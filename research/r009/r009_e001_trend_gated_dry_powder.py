"""R009-E001 trend-gated dry-powder barbell mechanism screen v0.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

VERSION = "0.1"
PROTOCOL = "r009-e001-trend-gated-dry-powder-protocol-v0.1"
SOURCE_URL = (
    "https://api.blockchain.info/charts/market-price"
    "?timespan=all&format=json&sampled=false"
)

SMA_LOOKBACK = 120
TREND_WEIGHT = 0.10
CRISIS_TRANCHE = 0.025
CRISIS_THRESH = (-0.20, -0.35, -0.50, -0.65)
LEVEL_PCT = (20, 35, 50, 65)
FEES = (0.0005, 0.0010, 0.0025, 0.0050)
BASE_FEE = 0.0010
HORIZONS = (7, 30, 90, 180, 365)
DAYS_PER_YEAR = 365.25
EPS = 1e-12

PRIMARY_START = pd.Timestamp("2013-01-01")
PRE2020_END = pd.Timestamp("2019-12-31")
REPLAY_START = pd.Timestamp("2020-01-01")
LATE_START = pd.Timestamp("2023-01-01")
MIN_ONE_DAY_GAP_SHARE = 0.98
MAX_ALLOWED_GAP_DAYS = 7


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_source() -> tuple[bytes, dict]:
    req = Request(SOURCE_URL, headers={"User-Agent": "botmarketplace-r009-e001/0.1"})
    with urlopen(req, timeout=90) as resp:
        raw = resp.read()
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict) or not isinstance(obj.get("values"), list) or not obj["values"]:
        raise ValueError("Unexpected Blockchain.com response schema")
    return raw, obj


def clean_source(obj: dict) -> tuple[pd.DataFrame, int]:
    rows = []
    for item in obj["values"]:
        if isinstance(item, dict):
            rows.append({"x": item.get("x"), "price": item.get("y")})
    x = pd.DataFrame(rows)
    if x.empty:
        raise ValueError("No parseable source rows")
    x["date"] = pd.to_datetime(
        pd.to_numeric(x["x"], errors="coerce"), unit="s", utc=True, errors="coerce"
    ).dt.tz_convert(None).dt.normalize()
    x["price"] = pd.to_numeric(x["price"], errors="coerce")
    x = x.dropna(subset=["date", "price"])
    x = x[x["price"] > 0].sort_values("date")
    dup = int(x["date"].duplicated().sum())
    x = x.drop_duplicates("date", keep="last")[["date", "price"]].reset_index(drop=True)
    if len(x) < 1000:
        raise ValueError(f"Long-history source unexpectedly short: {len(x)}")
    return x, dup


def audit_source(raw_obj: dict, clean: pd.DataFrame, dup_raw: int) -> dict:
    gaps = clean["date"].diff().dt.days.dropna()
    primary = clean[clean["date"] >= PRIMARY_START]
    pgaps = primary["date"].diff().dt.days.dropna()
    one_day_share = float((pgaps == 1).mean()) if len(pgaps) else 0.0
    max_gap = int(pgaps.max()) if len(pgaps) else 0
    long_gaps = int((pgaps > 1).sum()) if len(pgaps) else 0
    missing_days = int((pgaps[pgaps > 1] - 1).sum()) if len(pgaps) else 0
    passed = (
        len(primary) >= 1000
        and one_day_share >= MIN_ONE_DAY_GAP_SHARE
        and max_gap <= MAX_ALLOWED_GAP_DAYS
    )
    return {
        "status": "PASS" if passed else "DATA_REDESIGN",
        "source_url": SOURCE_URL,
        "source_name": raw_obj.get("name"),
        "source_unit": raw_obj.get("unit"),
        "source_period": raw_obj.get("period"),
        "raw_values": len(raw_obj.get("values", [])),
        "clean_rows": len(clean),
        "clean_start": clean["date"].iloc[0].date().isoformat(),
        "clean_end": clean["date"].iloc[-1].date().isoformat(),
        "duplicate_raw_dates_before_dedup": dup_raw,
        "all_history_max_gap_days": int(gaps.max()) if len(gaps) else 0,
        "primary_start": PRIMARY_START.date().isoformat(),
        "primary_rows": len(primary),
        "primary_one_day_gap_share": one_day_share,
        "primary_long_gap_events_gt1d": long_gaps,
        "primary_missing_calendar_days": missing_days,
        "primary_max_gap_days": max_gap,
        "gate_min_one_day_share": MIN_ONE_DAY_GAP_SHARE,
        "gate_max_gap_days": MAX_ALLOWED_GAP_DAYS,
    }


def build_state(price: pd.Series):
    idx = price.index
    sma = price.rolling(SMA_LOOKBACK, min_periods=SMA_LOOKBACK).mean()
    trend_on = (price > sma) & sma.notna()

    peak = float(price.iloc[0])
    peak_date = idx[0]
    sticky = [False] * 4
    event_no = 0
    active = None
    states = []
    events = []

    for i, (date, raw) in enumerate(price.items()):
        p = float(raw)
        new_ath = (i == 0 or p > peak + EPS)

        if new_ath:
            if i > 0 and active is not None:
                active["reset_date"] = date
                active["status"] = "CLOSED"
                events.append(active)
                active = None
            peak = p
            peak_date = date
            sticky = [False] * 4
            dd = 0.0
        else:
            dd = p / peak - 1.0
            newly = []
            for j, threshold in enumerate(CRISIS_THRESH):
                if (not sticky[j]) and dd <= threshold + EPS:
                    sticky[j] = True
                    newly.append(j)
            if newly and active is None:
                event_no += 1
                active = {
                    "event_id": event_no,
                    "prior_peak_date": peak_date,
                    "first_breach_date": date,
                    "reset_date": pd.NaT,
                    "status": "OPEN",
                    "max_drawdown": dd,
                    "max_drawdown_date": date,
                    **{f"breach_{pct}_date": pd.NaT for pct in LEVEL_PCT},
                }
            if active is not None:
                if dd < float(active["max_drawdown"]):
                    active["max_drawdown"] = dd
                    active["max_drawdown_date"] = date
                for j in newly:
                    key = f"breach_{LEVEL_PCT[j]}_date"
                    if pd.isna(active[key]):
                        active[key] = date

        crisis_level = int(sum(sticky))
        crisis_target = CRISIS_TRANCHE * crisis_level
        trend_target = TREND_WEIGHT if bool(trend_on.loc[date]) else 0.0
        combined_target = trend_target + crisis_target
        r008_v01_target = TREND_WEIGHT + crisis_target

        states.append(
            {
                "date": date,
                "price": p,
                "sma120": float(sma.loc[date]) if pd.notna(sma.loc[date]) else np.nan,
                "trend_on": bool(trend_on.loc[date]),
                "trend_target": trend_target,
                "running_peak_price": peak,
                "running_peak_date": peak_date,
                "drawdown": dd,
                "crisis_level": crisis_level,
                "crisis_target": crisis_target,
                "combined_target": combined_target,
                "r008_v01_target": r008_v01_target,
                "event_id": active["event_id"] if active else np.nan,
                "new_ath": bool(new_ath),
            }
        )

    if active is not None:
        active["status"] = "OPEN_CENSORED"
        events.append(active)

    state = pd.DataFrame(states).set_index("date")
    events_df = pd.DataFrame(events)

    breach_rows = []
    if not events_df.empty:
        for _, e in events_df.iterrows():
            deepest = sum(pd.notna(e[f"breach_{pct}_date"]) for pct in LEVEL_PCT)
            for pct in LEVEL_PCT:
                v = e[f"breach_{pct}_date"]
                if pd.notna(v):
                    breach_rows.append(
                        {
                            "event_id": int(e["event_id"]),
                            "status": e["status"],
                            "trigger_level": int(pct),
                            "breach_date": pd.Timestamp(v),
                            "deepest_level": int(deepest),
                            "max_drawdown": float(e["max_drawdown"]),
                        }
                    )
    breaches = pd.DataFrame(breach_rows)
    return state, events_df, breaches


def simulate_self_financing_daily(price: pd.Series, target: pd.Series, fee: float) -> pd.DataFrame:
    target = target.reindex(price.index).astype(float)
    idx = price.index
    out = []
    w = float(target.iloc[0])
    init_turn = abs(w)
    eq = 1.0 - fee * init_turn
    out.append(
        {
            "btc_return": 0.0,
            "desired_target": w,
            "held_weight": 0.0,
            "pretrade_weight": 0.0,
            "turnover": init_turn,
            "fee_cost": fee * init_turn,
            "net_return": -fee * init_turn,
            "equity": eq,
        }
    )
    for i in range(1, len(idx)):
        r = float(price.iloc[i] / price.iloc[i - 1] - 1.0)
        held = w
        gross_factor = 1.0 + held * r
        pre = held * (1.0 + r) / gross_factor if gross_factor > 0 else 0.0
        desired = float(target.iloc[i])
        turn = abs(desired - pre)
        cost = fee * turn
        net = gross_factor - 1.0 - cost
        eq *= 1.0 + net
        w = desired
        out.append(
            {
                "btc_return": r,
                "desired_target": desired,
                "held_weight": held,
                "pretrade_weight": pre,
                "turnover": turn,
                "fee_cost": cost,
                "net_return": net,
                "equity": eq,
            }
        )
    return pd.DataFrame(out, index=idx)


def simulate_static_monthly(price: pd.Series, weight: float, fee: float) -> pd.DataFrame:
    idx = price.index
    out = []
    w = float(weight)
    init_turn = abs(w)
    eq = 1.0 - fee * init_turn
    out.append(
        {
            "btc_return": 0.0,
            "desired_target": weight,
            "held_weight": 0.0,
            "pretrade_weight": 0.0,
            "turnover": init_turn,
            "fee_cost": fee * init_turn,
            "net_return": -fee * init_turn,
            "equity": eq,
        }
    )
    for i in range(1, len(idx)):
        r = float(price.iloc[i] / price.iloc[i - 1] - 1.0)
        held = w
        gross_factor = 1.0 + held * r
        pre = held * (1.0 + r) / gross_factor if gross_factor > 0 else 0.0
        is_month_end = (i == len(idx) - 1) or (idx[i + 1].month != idx[i].month)
        turn = abs(weight - pre) if is_month_end else 0.0
        cost = fee * turn
        net = gross_factor - 1.0 - cost
        eq *= 1.0 + net
        w = weight if is_month_end else pre
        out.append(
            {
                "btc_return": r,
                "desired_target": weight,
                "held_weight": held,
                "pretrade_weight": pre,
                "turnover": turn,
                "fee_cost": cost,
                "net_return": net,
                "equity": eq,
            }
        )
    return pd.DataFrame(out, index=idx)


def period_return(r: pd.Series, freq: str) -> pd.Series:
    return (1 + r).groupby(r.index.to_period(freq)).prod() - 1


def longest_dd(eq: pd.Series) -> int:
    peak = eq.cummax()
    under = eq < peak - 1e-15
    start = None
    best = 0
    for date, flag in under.items():
        if flag and start is None:
            start = date
        elif (not flag) and start is not None:
            best = max(best, (date - start).days)
            start = None
    if start is not None:
        best = max(best, (eq.index[-1] - start).days)
    return int(best)


def cvar(r: pd.Series, q: float) -> tuple[float, float]:
    if len(r) == 0:
        return np.nan, np.nan
    v = float(r.quantile(q))
    tail = r[r <= v]
    return v, float(tail.mean()) if len(tail) else np.nan


def metrics(name: str, fee: float, sim: pd.DataFrame, slice_name: str,
            start: pd.Timestamp, end: pd.Timestamp | None = None) -> dict | None:
    x = sim[sim.index >= start]
    if end is not None:
        x = x[x.index <= end]
    if len(x) < 2:
        return None
    r = x["net_return"]
    eq = (1 + r).cumprod()
    years = (eq.index[-1] - eq.index[0]).days / DAYS_PER_YEAR
    cagr = float(eq.iloc[-1] ** (1 / years) - 1) if years > 0 else np.nan
    dd = float((eq / eq.cummax() - 1).min())
    vol = float(r.std() * math.sqrt(365))
    yr = period_return(r, "Y")
    qr = period_return(r, "Q")
    mo = period_return(r, "M")
    roll = (eq / eq.shift(365) - 1).dropna()
    var1, cvar1 = cvar(r, 0.01)
    var5, cvar5 = cvar(r, 0.05)
    return {
        "strategy": name,
        "fee_bps": fee * 10000,
        "slice": slice_name,
        "start": eq.index[0].date().isoformat(),
        "end": eq.index[-1].date().isoformat(),
        "observations": len(eq),
        "cagr": cagr,
        "ending_multiple": float(eq.iloc[-1]),
        "annualized_vol": vol,
        "max_drawdown": dd,
        "calmar": cagr / abs(dd) if dd < 0 else np.nan,
        "worst_calendar_year": float(yr.min()) if len(yr) else np.nan,
        "worst_calendar_year_label": str(yr.idxmin()) if len(yr) else "",
        "worst_calendar_quarter": float(qr.min()) if len(qr) else np.nan,
        "worst_calendar_quarter_label": str(qr.idxmin()) if len(qr) else "",
        "worst_month": float(mo.min()) if len(mo) else np.nan,
        "worst_month_label": str(mo.idxmin()) if len(mo) else "",
        "worst_rolling_12m": float(roll.min()) if len(roll) else np.nan,
        "longest_drawdown_days": longest_dd(eq),
        "average_btc_exposure": float(x["held_weight"].mean()),
        "max_btc_exposure": float(x["held_weight"].max()),
        "turnover": float(x["turnover"].sum()),
        "fee_drag_simple": float(x["fee_cost"].sum()),
        "var_1pct": var1,
        "cvar_1pct": cvar1,
        "var_5pct": var5,
        "cvar_5pct": cvar5,
    }


def slice_defs(first_date: pd.Timestamp):
    return [
        ("FULL_AVAILABLE", first_date, None),
        ("PRIMARY_LONG", PRIMARY_START, None),
        ("PRE_2020", PRIMARY_START, PRE2020_END),
        ("REPLAY_2020", REPLAY_START, None),
        ("POST_2023", LATE_START, None),
    ]


def fixed_horizon_events(breaches: pd.DataFrame, sims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if breaches.empty:
        return pd.DataFrame()
    idx = next(iter(sims.values())).index
    rows = []
    for _, b in breaches.iterrows():
        breach = pd.Timestamp(b["breach_date"])
        pos = idx.searchsorted(breach, side="right")
        if pos >= len(idx):
            continue
        for h in HORIZONS:
            end_pos = pos + h - 1
            if end_pos >= len(idx):
                continue
            start = idx[pos]
            end = idx[end_pos]
            row = {
                "event_id": int(b["event_id"]),
                "status": b["status"],
                "trigger_level": int(b["trigger_level"]),
                "breach_date": breach.date().isoformat(),
                "deepest_level": int(b["deepest_level"]),
                "max_drawdown": float(b["max_drawdown"]),
                "horizon_days": int(h),
                "start_execution_date": start.date().isoformat(),
                "end_execution_date": end.date().isoformat(),
            }
            names = [
                "R009_COMBINED_DAILY", "CRISIS10_DAILY", "TREND10_DAILY",
                "STATIC15_DAILY", "STATIC20_DAILY", "STATIC15_MONTHLY",
            ]
            for name in names:
                rr = sims[name].loc[start:end, "net_return"]
                row[f"{name.lower()}_return"] = float((1 + rr).prod() - 1)
            c = row["r009_combined_daily_return"]
            cr = row["crisis10_daily_return"]
            for comp, key in [
                ("TREND10_DAILY", "trend10"),
                ("STATIC15_DAILY", "static15_daily"),
                ("STATIC20_DAILY", "static20_daily"),
                ("STATIC15_MONTHLY", "static15_monthly"),
            ]:
                row[f"combined_benefit_vs_{key}"] = c - row[f"{comp.lower()}_return"]
                row[f"crisis_benefit_vs_{key}"] = cr - row[f"{comp.lower()}_return"]
            rows.append(row)
    return pd.DataFrame(rows)


def fixed_horizon_summary(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    rows = []
    for subject in ("combined", "crisis"):
        benefit_cols = [
            f"{subject}_benefit_vs_trend10",
            f"{subject}_benefit_vs_static15_daily",
            f"{subject}_benefit_vs_static20_daily",
            f"{subject}_benefit_vs_static15_monthly",
        ]
        for (level, h), g in events.groupby(["trigger_level", "horizon_days"]):
            row = {
                "subject": subject.upper(),
                "trigger_level": int(level),
                "horizon_days": int(h),
                "count": len(g),
            }
            for col in benefit_cols:
                vals = g[col].dropna()
                suffix = col.replace(f"{subject}_benefit_vs_", "")
                row[f"benefit_vs_{suffix}_mean"] = float(vals.mean()) if len(vals) else np.nan
                row[f"benefit_vs_{suffix}_median"] = float(vals.median()) if len(vals) else np.nan
                row[f"benefit_vs_{suffix}_positive_fraction"] = float((vals > 0).mean()) if len(vals) else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def state_diagnostics(state: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp | None = None) -> dict:
    x = state[state.index >= start]
    if end is not None:
        x = x[x.index <= end]
    if x.empty:
        return {}
    joint = {
        "trend_on_crisis_inactive": float((x["trend_on"] & (x["crisis_target"] == 0)).mean()),
        "trend_off_crisis_inactive": float(((~x["trend_on"]) & (x["crisis_target"] == 0)).mean()),
        "trend_on_crisis_active": float((x["trend_on"] & (x["crisis_target"] > 0)).mean()),
        "trend_off_crisis_active": float(((~x["trend_on"]) & (x["crisis_target"] > 0)).mean()),
    }
    occupancy = {}
    for w in (0.0, 0.025, 0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20):
        occupancy[f"share_{w:.3f}"] = float(np.isclose(x["combined_target"], w).mean())
    return {
        "observations": len(x),
        "trend_on_fraction": float(x["trend_on"].mean()),
        "crisis_active_fraction": float((x["crisis_target"] > 0).mean()),
        "crisis_fully_deployed_fraction": float(np.isclose(x["crisis_target"], 0.10).mean()),
        "average_trend_target": float(x["trend_target"].mean()),
        "average_crisis_target": float(x["crisis_target"].mean()),
        "average_combined_target": float(x["combined_target"].mean()),
        "joint_state": joint,
        "combined_target_occupancy": occupancy,
    }


def count_transitions(s: pd.Series) -> int:
    return int((s.diff().abs() > EPS).sum())


def self_test() -> None:
    dates = pd.date_range("2020-01-01", periods=130, freq="D")
    vals = np.full(130, 100.0)
    vals[:120] = np.linspace(50, 100, 120)
    vals[120] = 80
    vals[121] = 65
    vals[122] = 50
    vals[123] = 35
    vals[124] = 40
    vals[125] = 70
    vals[126] = 101
    vals[127:] = 102
    price = pd.Series(vals, index=dates)
    state, _, _ = build_state(price)
    assert abs(float(state.iloc[123]["crisis_target"]) - 0.10) < 1e-12
    assert abs(float(state.iloc[126]["crisis_target"])) < 1e-12
    assert abs(float(state.iloc[126]["combined_target"]) - float(state.iloc[126]["trend_target"])) < 1e-12
    assert state["combined_target"].min() >= -EPS
    assert state["combined_target"].max() <= 0.20 + EPS


def write_summary(path: Path, audit: dict, metrics_df: pd.DataFrame, state: pd.DataFrame,
                  fh_summary: pd.DataFrame) -> None:
    b = metrics_df[np.isclose(metrics_df["fee_bps"], BASE_FEE * 10000)].copy()
    lines = [
        "# R009-E001 Trend-Gated Dry-Powder Barbell — Raw Output v0.1",
        "",
        "**Status:** in-sample mechanism screen only; no automatic promotion.",
        "",
        f"- Data gate: **{audit['status']}**",
        f"- Clean period: **{audit['clean_start']} -> {audit['clean_end']}**",
        "- Frozen trend: **SMA120, 10% sleeve when price > SMA120**",
        "- Frozen crisis reserve: **2.5% x4 at -20/-35/-50/-65%, sticky to new ATH**",
        "- Combined target: **TREND10 + CRISIS10, 0-20% BTC**",
        "- Baseline cost: **10 bps**",
        "",
        "## Baseline metrics",
        "",
        "| Strategy | Slice | CAGR | Max DD | Calmar | Avg BTC | Turnover |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    show_names = [
        "R009_COMBINED_DAILY", "TREND10_DAILY", "CRISIS10_DAILY", "R008_V01_DAILY",
        "STATIC10_DAILY", "STATIC15_DAILY", "STATIC20_DAILY",
        "STATIC15_MONTHLY", "STATIC20_MONTHLY",
    ]
    for name in show_names:
        for sl in ("PRIMARY_LONG", "PRE_2020", "REPLAY_2020", "POST_2023"):
            x = b[(b["strategy"] == name) & (b["slice"] == sl)]
            if x.empty:
                continue
            r = x.iloc[0]
            lines.append(
                f"| {name} | {sl} | {100*r['cagr']:.2f}% | {100*r['max_drawdown']:.2f}% | "
                f"{r['calmar']:.2f} | {100*r['average_btc_exposure']:.2f}% | {r['turnover']:.3f} |"
            )
    lines += ["", "## State diagnostics", ""]
    for label, start, end in [
        ("PRIMARY_LONG", PRIMARY_START, None),
        ("PRE_2020", PRIMARY_START, PRE2020_END),
        ("REPLAY_2020", REPLAY_START, None),
    ]:
        d = state_diagnostics(state, start, end)
        lines.append(
            f"- {label}: trend ON **{100*d['trend_on_fraction']:.1f}%**, crisis active **{100*d['crisis_active_fraction']:.1f}%**, "
            f"avg combined target **{100*d['average_combined_target']:.2f}%**."
        )
    lines += [
        "",
        "## Target transitions",
        "",
        f"- TREND10 target transitions: **{count_transitions(state['trend_target'])}**",
        f"- CRISIS10 target transitions: **{count_transitions(state['crisis_target'])}**",
        f"- R009 combined target transitions: **{count_transitions(state['combined_target'])}**",
    ]
    if not fh_summary.empty:
        x = fh_summary[(fh_summary["subject"] == "COMBINED") & (fh_summary["trigger_level"] == 65) & (fh_summary["horizon_days"] == 365)]
        if not x.empty:
            r = x.iloc[0]
            lines += [
                "",
                "## Fixed-horizon deep-shock diagnostic",
                "",
                f"- Combined at -65% / 365d: Benefit vs TREND10 mean **{100*r['benefit_vs_trend10_mean']:.2f}%**; "
                f"vs STATIC15 daily **{100*r['benefit_vs_static15_daily_mean']:.2f}%**; "
                f"vs STATIC20 daily **{100*r['benefit_vs_static20_daily_mean']:.2f}%**; count **{int(r['count'])}**.",
            ]
    lines += [
        "",
        "## Important",
        "",
        "R009-E001 uses history already inspected while designing R002/R008. Even a strong result can only be a PROMISING_SCREEN; it cannot receive independent historical PASS.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    self_test()
    print("R009-E001 self-test: PASS")

    raw, obj = download_source()
    clean, dup = clean_source(obj)
    audit = audit_source(obj, clean, dup)
    audit["raw_sha256"] = sha256_bytes(raw)

    clean_path = outdir / "r009_e001_price_clean.csv"
    clean.to_csv(clean_path, index=False)
    audit["clean_csv_sha256"] = sha256_file(clean_path)
    (outdir / "r009_e001_data_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    if audit["status"] != "PASS":
        raise RuntimeError("R009 E001 data gate failed: DATA_REDESIGN")

    price = clean.set_index("date")["price"].astype(float)
    state, events, breaches = build_state(price)
    state.to_csv(outdir / "r009_e001_state_daily.csv", index_label="date")

    dynamic_targets = {
        "TREND10_DAILY": state["trend_target"],
        "CRISIS10_DAILY": state["crisis_target"],
        "R009_COMBINED_DAILY": state["combined_target"],
        "R008_V01_DAILY": state["r008_v01_target"],
        "STATIC10_DAILY": pd.Series(0.10, index=price.index),
        "STATIC15_DAILY": pd.Series(0.15, index=price.index),
        "STATIC20_DAILY": pd.Series(0.20, index=price.index),
        "CASH": pd.Series(0.0, index=price.index),
        "BTC100": pd.Series(1.0, index=price.index),
    }

    all_metrics = []
    baseline_sims = {}
    for fee in FEES:
        sims = {name: simulate_self_financing_daily(price, target, fee) for name, target in dynamic_targets.items()}
        for w, label in [(0.10, "STATIC10_MONTHLY"), (0.15, "STATIC15_MONTHLY"), (0.20, "STATIC20_MONTHLY")]:
            sims[label] = simulate_static_monthly(price, w, fee)
        if abs(fee - BASE_FEE) < 1e-12:
            baseline_sims = sims
        for name, sim in sims.items():
            for sl, start, end in slice_defs(price.index[0]):
                m = metrics(name, fee, sim, sl, start, end)
                if m is not None:
                    all_metrics.append(m)

    metrics_df = pd.DataFrame(all_metrics)
    metrics_df.to_csv(outdir / "r009_e001_metrics.csv", index=False)

    yearly_rows = []
    for name, sim in baseline_sims.items():
        x = sim[sim.index >= PRIMARY_START]
        yr = period_return(x["net_return"], "Y")
        for period, value in yr.items():
            yearly_rows.append({"strategy": name, "year": int(period.year), "return": float(value)})
    pd.DataFrame(yearly_rows).to_csv(outdir / "r009_e001_yearly_returns.csv", index=False)

    fh_events = fixed_horizon_events(breaches, baseline_sims)
    fh_summary = fixed_horizon_summary(fh_events)
    fh_events.to_csv(outdir / "r009_e001_fixed_horizon_events.csv", index=False)
    fh_summary.to_csv(outdir / "r009_e001_fixed_horizon_summary.csv", index=False)

    baseline = pd.DataFrame(index=price.index)
    baseline["price"] = price
    baseline["sma120"] = state["sma120"]
    baseline["drawdown"] = state["drawdown"]
    baseline["trend_on"] = state["trend_on"]
    baseline["trend_target"] = state["trend_target"]
    baseline["crisis_target"] = state["crisis_target"]
    baseline["combined_target"] = state["combined_target"]
    for name in [
        "R009_COMBINED_DAILY", "TREND10_DAILY", "CRISIS10_DAILY", "R008_V01_DAILY",
        "STATIC10_DAILY", "STATIC15_DAILY", "STATIC20_DAILY", "STATIC15_MONTHLY",
    ]:
        baseline[f"{name.lower()}_equity"] = baseline_sims[name]["equity"]
    baseline.to_csv(outdir / "r009_e001_baseline_daily.csv", index_label="date")

    diag = {}
    for sl, start, end in slice_defs(price.index[0]):
        diag[sl] = state_diagnostics(state, start, end)

    run_state = {
        "status": "PASS",
        "engine_version": VERSION,
        "protocol": PROTOCOL,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_status": "IN_SAMPLE_MECHANISM_SCREEN_ONLY",
        "research_freeze": {
            "sma_lookback": SMA_LOOKBACK,
            "trend_weight": TREND_WEIGHT,
            "crisis_reserve": 0.10,
            "crisis_tranche": CRISIS_TRANCHE,
            "crisis_thresholds": list(CRISIS_THRESH),
            "crisis_reset": "sticky_until_new_ath",
            "combined_rule": "trend_target_plus_crisis_target",
            "accounting": "SELF_FINANCING_DAILY_TARGET",
            "fee_grid": list(FEES),
            "baseline_fee": BASE_FEE,
            "cash_return": 0.0,
        },
        "source": {
            "url": SOURCE_URL,
            "raw_sha256": audit["raw_sha256"],
            "clean_csv_sha256": audit["clean_csv_sha256"],
            "clean_rows": len(clean),
            "start": clean["date"].iloc[0].date().isoformat(),
            "end": clean["date"].iloc[-1].date().isoformat(),
        },
        "data_gate": audit,
        "crisis_events": int(len(events)),
        "breach_rows": int(len(breaches)),
        "trend_target_transitions": count_transitions(state["trend_target"]),
        "crisis_target_transitions": count_transitions(state["crisis_target"]),
        "combined_target_transitions": count_transitions(state["combined_target"]),
        "state_diagnostics": diag,
        "outputs": [
            "r009_e001_price_clean.csv",
            "r009_e001_data_audit.json",
            "r009_e001_state_daily.csv",
            "r009_e001_metrics.csv",
            "r009_e001_yearly_returns.csv",
            "r009_e001_fixed_horizon_events.csv",
            "r009_e001_fixed_horizon_summary.csv",
            "r009_e001_baseline_daily.csv",
            "r009_e001_summary.md",
            "r009_e001_run_state.json",
        ],
    }
    (outdir / "r009_e001_run_state.json").write_text(
        json.dumps(run_state, indent=2), encoding="utf-8"
    )
    write_summary(outdir / "r009_e001_summary.md", audit, metrics_df, state, fh_summary)

    print("R009-E001 complete")
    print("Output folder:", outdir)
    print("Files:")
    for p in sorted(outdir.iterdir()):
        print(" -", p.name)


if __name__ == "__main__":
    main()
