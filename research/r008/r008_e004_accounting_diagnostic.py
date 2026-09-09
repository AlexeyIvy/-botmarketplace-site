"""R008-E004 accounting and event-diagnostic audit v0.1."""

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
PROTOCOL = "r008-e004-accounting-diagnostic-audit-protocol-v0.1"
SOURCE_URL = (
    "https://api.blockchain.info/charts/market-price"
    "?timespan=all&format=json&sampled=false"
)

BASE = 0.10
TRANCHE = 0.025
THRESH = (-0.20, -0.35, -0.50, -0.65)
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
    req = Request(SOURCE_URL, headers={"User-Agent": "botmarketplace-r008-e004/0.1"})
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
        pd.to_numeric(x["x"], errors="coerce"),
        unit="s",
        utc=True,
        errors="coerce",
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


def build_targets_and_breaches(price: pd.Series):
    idx = price.index
    peak = float(price.iloc[0])
    peak_date = idx[0]
    sticky = [False] * 4
    event_no = 0
    active_event = None
    state_rows = []
    event_rows = []

    for i, (date, raw) in enumerate(price.items()):
        p = float(raw)
        new_ath = (i == 0 or p > peak + EPS)

        if new_ath:
            if i > 0 and active_event is not None:
                active_event["reset_date"] = date
                active_event["status"] = "CLOSED"
                event_rows.append(active_event)
                active_event = None
            peak = p
            peak_date = date
            sticky = [False] * 4
            dd = 0.0
        else:
            dd = p / peak - 1.0
            newly = []
            for j, t in enumerate(THRESH):
                if (not sticky[j]) and dd <= t + EPS:
                    sticky[j] = True
                    newly.append(j)
            if newly and active_event is None:
                event_no += 1
                active_event = {
                    "event_id": event_no,
                    "prior_peak_date": peak_date,
                    "first_breach_date": date,
                    "reset_date": pd.NaT,
                    "status": "OPEN",
                    "max_drawdown": dd,
                    "max_drawdown_date": date,
                    **{f"breach_{pct}_date": pd.NaT for pct in LEVEL_PCT},
                }
            if active_event is not None:
                if dd < float(active_event["max_drawdown"]):
                    active_event["max_drawdown"] = dd
                    active_event["max_drawdown_date"] = date
                for j in newly:
                    key = f"breach_{LEVEL_PCT[j]}_date"
                    if pd.isna(active_event[key]):
                        active_event[key] = date

        v01_level = int(sum(sticky))
        v01_target = BASE + TRANCHE * v01_level
        v02_level = int(sum(dd <= t + EPS for t in THRESH))
        v02_target = BASE + TRANCHE * v02_level

        state_rows.append(
            {
                "date": date,
                "price": p,
                "running_peak_price": peak,
                "running_peak_date": peak_date,
                "drawdown": dd,
                "new_ath": bool(new_ath),
                "event_id": active_event["event_id"] if active_event else np.nan,
                "r008_v01_target": v01_target,
                "r008_v02_target": v02_target,
            }
        )

    if active_event is not None:
        active_event["status"] = "OPEN_CENSORED"
        event_rows.append(active_event)

    state = pd.DataFrame(state_rows).set_index("date")
    events = pd.DataFrame(event_rows)

    breach_rows = []
    if not events.empty:
        for _, e in events.iterrows():
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
    return state, events, breaches


def simulate_legacy(price: pd.Series, target: pd.Series, fee: float) -> pd.DataFrame:
    target = target.reindex(price.index).astype(float)
    r = price.pct_change(fill_method=None).fillna(0.0)
    held = target.shift(1).fillna(0.0)
    dturn = target.diff().abs()
    dturn.iloc[0] = abs(float(target.iloc[0]))
    turn = dturn.shift(1).fillna(0.0)
    gross = held * r
    cost = fee * turn
    net = gross - cost
    eq = (1.0 + net).cumprod()
    return pd.DataFrame(
        {
            "btc_return": r,
            "desired_target": target,
            "held_weight": held,
            "pretrade_weight": np.nan,
            "turnover": turn,
            "fee_cost": cost,
            "net_return": net,
            "equity": eq,
        },
        index=price.index,
    )


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


def simulate_transition_only(price: pd.Series, target: pd.Series, fee: float) -> pd.DataFrame:
    target = target.reindex(price.index).astype(float)
    idx = price.index
    out = []
    desired_prev = float(target.iloc[0])
    w = desired_prev
    init_turn = abs(w)
    eq = 1.0 - fee * init_turn
    out.append(
        {
            "btc_return": 0.0,
            "desired_target": desired_prev,
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
        do_trade = abs(desired - desired_prev) > EPS
        turn = abs(desired - pre) if do_trade else 0.0
        cost = fee * turn
        net = gross_factor - 1.0 - cost
        eq *= 1.0 + net
        w = desired if do_trade else pre
        desired_prev = desired
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


def metrics(name: str, model: str, fee: float, sim: pd.DataFrame,
            slice_name: str, start: pd.Timestamp, end: pd.Timestamp | None = None):
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
    q01 = float(r.quantile(0.01))
    q05 = float(r.quantile(0.05))
    cvar01 = float(r[r <= q01].mean())
    cvar05 = float(r[r <= q05].mean())
    return {
        "strategy": name,
        "accounting_model": model,
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
        "worst_calendar_quarter": float(qr.min()) if len(qr) else np.nan,
        "worst_month": float(mo.min()) if len(mo) else np.nan,
        "worst_rolling_12m": float(roll.min()) if len(roll) else np.nan,
        "longest_drawdown_days": longest_dd(eq),
        "average_realized_btc_weight": float(x["held_weight"].mean()),
        "max_realized_btc_weight": float(x["held_weight"].max()),
        "turnover": float(x["turnover"].sum()),
        "fee_drag_simple": float(x["fee_cost"].sum()),
        "var_1pct": q01,
        "cvar_1pct": cvar01,
        "var_5pct": q05,
        "cvar_5pct": cvar05,
    }


def slice_defs(last_date):
    return [
        ("PRIMARY_LONG", PRIMARY_START, None),
        ("PRE_2020_NEW", PRIMARY_START, PRE2020_END),
        ("REPLAY_2020", REPLAY_START, None),
        ("POST_2023", LATE_START, None),
    ]


def compound_window(sim: pd.DataFrame, start_pos: int, horizon: int):
    end_pos = start_pos + horizon
    if end_pos > len(sim):
        return None
    r = sim["net_return"].iloc[start_pos:end_pos]
    if len(r) != horizon:
        return None
    return float((1 + r).prod() - 1)


def fixed_horizon_rows(breaches: pd.DataFrame, sims: dict[str, pd.DataFrame],
                       idx: pd.DatetimeIndex):
    rows = []
    if breaches.empty:
        return pd.DataFrame()
    for _, b in breaches.iterrows():
        breach_date = pd.Timestamp(b["breach_date"])
        pos = idx.get_indexer([breach_date])[0]
        if pos < 0:
            continue
        start_pos = pos + 1
        for h in HORIZONS:
            vals = {}
            ok = True
            for name, sim in sims.items():
                v = compound_window(sim, start_pos, h)
                if v is None:
                    ok = False
                    break
                vals[name] = v
            if not ok:
                continue
            for strat in ("R008_V01_DAILY", "R008_V02_DAILY"):
                rows.append(
                    {
                        "event_id": int(b["event_id"]),
                        "status": b["status"],
                        "trigger_level": int(b["trigger_level"]),
                        "deepest_level": int(b["deepest_level"]),
                        "breach_date": breach_date.date().isoformat(),
                        "horizon_days": int(h),
                        "strategy": strat,
                        "strategy_return": vals[strat],
                        "static10_daily_return": vals["STATIC10_DAILY"],
                        "static15_daily_return": vals["STATIC15_DAILY"],
                        "static20_daily_return": vals["STATIC20_DAILY"],
                        "static15_monthly_return": vals["STATIC15_MONTHLY"],
                        "benefit_vs_static10_daily": vals[strat] - vals["STATIC10_DAILY"],
                        "benefit_vs_static15_daily": vals[strat] - vals["STATIC15_DAILY"],
                        "benefit_vs_static20_daily": vals[strat] - vals["STATIC20_DAILY"],
                        "benefit_vs_static15_monthly": vals[strat] - vals["STATIC15_MONTHLY"],
                    }
                )
    return pd.DataFrame(rows)


def summarize_fixed_horizon(x: pd.DataFrame):
    if x.empty:
        return pd.DataFrame()
    comps = [
        "benefit_vs_static10_daily",
        "benefit_vs_static15_daily",
        "benefit_vs_static20_daily",
        "benefit_vs_static15_monthly",
    ]
    rows = []
    for (strat, level, h), g in x.groupby(["strategy", "trigger_level", "horizon_days"]):
        row = {
            "strategy": strat,
            "trigger_level": int(level),
            "horizon_days": int(h),
            "count": len(g),
        }
        for c in comps:
            row[f"{c}_mean"] = float(g[c].mean())
            row[f"{c}_median"] = float(g[c].median())
            row[f"{c}_positive_fraction"] = float((g[c] > 0).mean())
        rows.append(row)
    return pd.DataFrame(rows)


def write_summary(path: Path, metrics_df: pd.DataFrame, fh_summary: pd.DataFrame, audit: dict):
    b = metrics_df[metrics_df["fee_bps"] == 10.0].copy()
    L = [
        "# R008-E004 Accounting & Event-Diagnostic Audit — Raw Output v0.1",
        "",
        "**Status:** methodology audit only; no automatic strategy promotion.",
        "",
        f"- Data gate: **{audit['status']}**",
        f"- Clean period: **{audit['clean_start']} -> {audit['clean_end']}**",
        "- Baseline fee: **10 bps**",
        "",
        "## Baseline key metrics",
        "",
        "| Strategy | Model | Slice | CAGR | Max DD | Calmar | Avg BTC | Turnover |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    keep = b[
        b["strategy"].isin(["R008_V01", "R008_V02", "STATIC10", "STATIC15", "STATIC20"])
        & b["accounting_model"].isin(
            ["SELF_FINANCING_DAILY_TARGET", "TRANSITION_ONLY", "STATIC_MONTHLY"]
        )
    ]
    for r in keep.itertuples(index=False):
        L.append(
            f"| {r.strategy} | {r.accounting_model} | {r.slice} | "
            f"{r.cagr:.2%} | {r.max_drawdown:.2%} | {r.calmar:.2f} | "
            f"{r.average_realized_btc_weight:.2%} | {r.turnover:.3f} |"
        )
    L += ["", "## Fixed-horizon diagnostics", ""]
    if fh_summary.empty:
        L.append("- No fixed-horizon rows available.")
    else:
        for strat in ("R008_V01_DAILY", "R008_V02_DAILY"):
            z = fh_summary[fh_summary["strategy"] == strat]
            if len(z):
                v = z[(z["trigger_level"] == 65) & (z["horizon_days"] == 365)]
                if len(v):
                    rr = v.iloc[0]
                    L.append(
                        f"- {strat} at -65% trigger / 365d: "
                        f"Benefit15 daily mean {rr['benefit_vs_static15_daily_mean']:.2%}; "
                        f"Benefit20 daily mean {rr['benefit_vs_static20_daily_mean']:.2%}; "
                        f"count {int(rr['count'])}."
                    )
    L += [
        "",
        "## Important",
        "",
        "E004 audits accounting and event-window interpretation on already inspected history. "
        "It cannot create historical PASS and does not change any R008 strategy rule.",
        "",
    ]
    path.write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir")
    a = ap.parse_args()
    out = (
        Path(a.outdir).expanduser().resolve()
        if a.outdir
        else Path.cwd() / f"R008_E004_RUN_{datetime.now():%Y-%m-%d_%H-%M-%S}"
    )
    out.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("R008-E004 ACCOUNTING & EVENT-DIAGNOSTIC AUDIT v0.1")
    print("=" * 72)

    raw, obj = download_source()
    clean, dup = clean_source(obj)
    raw_path = out / "r008_e004_blockchain_market_price_raw.json"
    raw_path.write_bytes(raw)
    price_path = out / "r008_e004_price_clean.csv"
    clean.to_csv(price_path, index=False)

    audit = audit_source(obj, clean, dup)
    audit["raw_sha256"] = sha256_bytes(raw)
    audit["clean_csv_sha256"] = sha256_file(price_path)
    (out / "r008_e004_data_audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if audit["status"] != "PASS":
        raise RuntimeError("DATA_REDESIGN: source gate failed")

    price = clean.set_index("date")["price"]
    state, events, breaches = build_targets_and_breaches(price)
    state.to_csv(out / "r008_e004_state_targets.csv")
    events.to_csv(out / "r008_e004_crisis_events_raw.csv", index=False)
    breaches.to_csv(out / "r008_e004_breaches.csv", index=False)

    static_targets = {
        "STATIC10": pd.Series(0.10, index=price.index),
        "STATIC15": pd.Series(0.15, index=price.index),
        "STATIC20": pd.Series(0.20, index=price.index),
    }
    dyn_targets = {
        "R008_V01": state["r008_v01_target"],
        "R008_V02": state["r008_v02_target"],
    }

    rows = []
    sims_baseline = {}
    for fee in FEES:
        for name, target in {**dyn_targets, **static_targets}.items():
            sim = simulate_legacy(price, target, fee)
            if fee == BASE_FEE:
                sims_baseline[f"{name}_LEGACY"] = sim
            for sl, st, en in slice_defs(price.index[-1]):
                r = metrics(name, "LEGACY_TARGET_WEIGHT", fee, sim, sl, st, en)
                if r:
                    rows.append(r)

        for name, target in {**dyn_targets, **static_targets}.items():
            sim = simulate_self_financing_daily(price, target, fee)
            if fee == BASE_FEE:
                sims_baseline[f"{name}_DAILY"] = sim
            for sl, st, en in slice_defs(price.index[-1]):
                r = metrics(name, "SELF_FINANCING_DAILY_TARGET", fee, sim, sl, st, en)
                if r:
                    rows.append(r)

        for name, target in dyn_targets.items():
            sim = simulate_transition_only(price, target, fee)
            if fee == BASE_FEE:
                sims_baseline[f"{name}_TRANSITION"] = sim
            for sl, st, en in slice_defs(price.index[-1]):
                r = metrics(name, "TRANSITION_ONLY", fee, sim, sl, st, en)
                if r:
                    rows.append(r)

        for name, w in (("STATIC10", 0.10), ("STATIC15", 0.15), ("STATIC20", 0.20)):
            sim = simulate_static_monthly(price, w, fee)
            if fee == BASE_FEE:
                sims_baseline[f"{name}_MONTHLY"] = sim
            for sl, st, en in slice_defs(price.index[-1]):
                r = metrics(name, "STATIC_MONTHLY", fee, sim, sl, st, en)
                if r:
                    rows.append(r)

    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv(out / "r008_e004_metrics.csv", index=False)

    fh_needed = {
        "R008_V01_DAILY": sims_baseline["R008_V01_DAILY"],
        "R008_V02_DAILY": sims_baseline["R008_V02_DAILY"],
        "STATIC10_DAILY": sims_baseline["STATIC10_DAILY"],
        "STATIC15_DAILY": sims_baseline["STATIC15_DAILY"],
        "STATIC20_DAILY": sims_baseline["STATIC20_DAILY"],
        "STATIC15_MONTHLY": sims_baseline["STATIC15_MONTHLY"],
    }
    fh = fixed_horizon_rows(breaches, fh_needed, price.index)
    fh.to_csv(out / "r008_e004_fixed_horizon_events.csv", index=False)
    fhs = summarize_fixed_horizon(fh)
    fhs.to_csv(out / "r008_e004_fixed_horizon_summary.csv", index=False)

    daily = state.copy()
    for key in (
        "R008_V01_DAILY",
        "R008_V02_DAILY",
        "R008_V01_TRANSITION",
        "R008_V02_TRANSITION",
        "STATIC15_DAILY",
        "STATIC15_MONTHLY",
    ):
        s = sims_baseline[key]
        daily[f"{key.lower()}_weight"] = s["held_weight"]
        daily[f"{key.lower()}_turnover"] = s["turnover"]
        daily[f"{key.lower()}_net_return"] = s["net_return"]
        daily[f"{key.lower()}_equity"] = s["equity"]
    daily.to_csv(out / "r008_e004_baseline_daily.csv")

    write_summary(out / "r008_e004_summary.md", metrics_df, fhs, audit)

    outputs = [
        "r008_e004_blockchain_market_price_raw.json",
        "r008_e004_price_clean.csv",
        "r008_e004_data_audit.json",
        "r008_e004_state_targets.csv",
        "r008_e004_crisis_events_raw.csv",
        "r008_e004_breaches.csv",
        "r008_e004_metrics.csv",
        "r008_e004_fixed_horizon_events.csv",
        "r008_e004_fixed_horizon_summary.csv",
        "r008_e004_baseline_daily.csv",
        "r008_e004_summary.md",
        "r008_e004_run_state.json",
    ]
    run = {
        "status": "PASS",
        "engine_version": VERSION,
        "protocol": PROTOCOL,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_freeze": {
            "base_weight": BASE,
            "opportunity_reserve": 0.10,
            "tranche_weight": TRANCHE,
            "thresholds": list(THRESH),
            "fee_grid": list(FEES),
            "fixed_horizons_days": list(HORIZONS),
            "static_monthly_frequency": "calendar_month_end",
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
        "crisis_events": len(events),
        "breach_rows": len(breaches),
        "outputs": outputs,
    }
    (out / "r008_e004_run_state.json").write_text(
        json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("FINISHED")
    print("Results:", out)


if __name__ == "__main__":
    main()
