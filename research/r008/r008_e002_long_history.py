"""R008-E002 independent long-history validation engine v0.1."""

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
PROTOCOL = "r008-e002-long-history-validation-protocol-v0.1"

SOURCE_URL = (
    "https://api.blockchain.info/charts/market-price"
    "?timespan=all&format=json&sampled=false"
)

BASE = 0.10
TRANCHE = 0.025
THRESH = (-0.20, -0.35, -0.50, -0.65)
FEES = (0.0005, 0.0010, 0.0025, 0.0050)
BASE_FEE = 0.0010
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
    req = Request(
        SOURCE_URL,
        headers={"User-Agent": "botmarketplace-r008-e002/0.1"},
    )
    with urlopen(req, timeout=90) as resp:
        raw = resp.read()
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict) or "values" not in obj:
        raise ValueError("Unexpected Blockchain.com response schema")
    if not isinstance(obj["values"], list) or not obj["values"]:
        raise ValueError("Blockchain.com response has no values")
    return raw, obj


def clean_source(obj: dict) -> pd.DataFrame:
    rows = []
    for item in obj["values"]:
        if not isinstance(item, dict):
            continue
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
    x = x.drop_duplicates("date", keep="last")
    x = x[["date", "price"]].reset_index(drop=True)

    if len(x) < 1000:
        raise ValueError(f"Long-history source unexpectedly short: {len(x)} rows")
    return x


def audit_source(raw_obj: dict, clean: pd.DataFrame) -> dict:
    raw_values = raw_obj.get("values", [])
    dates = clean["date"]
    gaps = dates.diff().dt.days.dropna()
    primary = clean[clean["date"] >= PRIMARY_START].copy()
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
        "raw_values": len(raw_values),
        "clean_rows": len(clean),
        "clean_start": clean["date"].iloc[0].date().isoformat(),
        "clean_end": clean["date"].iloc[-1].date().isoformat(),
        "duplicate_clean_dates": int(clean["date"].duplicated().sum()),
        "nonpositive_or_unparseable_removed": int(len(raw_values) - len(clean)),
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


def next_date(idx: pd.DatetimeIndex, date: pd.Timestamp):
    pos = idx.searchsorted(date, side="right")
    return None if pos >= len(idx) else idx[pos]


def build_state(price: pd.Series):
    idx = price.index
    peak = float(price.iloc[0])
    peak_date = idx[0]
    triggered = [False] * 4
    active = None
    event_no = 1
    states = []
    done = []

    for i, (date, raw) in enumerate(price.items()):
        p = float(raw)
        new_ath = (i == 0 or p > peak + EPS)

        if new_ath:
            if i > 0 and active is not None:
                active["reset_date"] = date
                active["status"] = "CLOSED"
                done.append(active)
                active = None
            peak = p
            peak_date = date
            triggered = [False] * 4
            dd = 0.0
        else:
            dd = p / peak - 1.0
            crossed = []
            for j, threshold in enumerate(THRESH):
                if (not triggered[j]) and dd <= threshold + EPS:
                    triggered[j] = True
                    crossed.append(j)

            if crossed:
                if active is None:
                    active = {
                        "event_id": event_no,
                        "prior_peak_date": peak_date,
                        "prior_peak_price": peak,
                        "first_breach_date": date,
                        "reset_date": pd.NaT,
                        "status": "OPEN",
                        "max_drawdown": dd,
                        "max_drawdown_date": date,
                        "breach_20_date": pd.NaT,
                        "breach_35_date": pd.NaT,
                        "breach_50_date": pd.NaT,
                        "breach_65_date": pd.NaT,
                    }
                    event_no += 1

                for j in crossed:
                    key = f"breach_{(20, 35, 50, 65)[j]}_date"
                    if pd.isna(active[key]):
                        active[key] = date

            if active is not None and dd < float(active["max_drawdown"]):
                active["max_drawdown"] = dd
                active["max_drawdown_date"] = date

        level = sum(triggered)
        target = BASE + TRANCHE * level
        states.append(
            {
                "date": date,
                "price": p,
                "running_peak_price": peak,
                "running_peak_date": peak_date,
                "drawdown": dd,
                "active_tranches": level,
                "target_btc_weight": target,
                "event_id": active["event_id"] if active else np.nan,
                "new_ath": bool(new_ath),
            }
        )

    if active is not None:
        active["status"] = "OPEN_CENSORED"
        done.append(active)

    state = pd.DataFrame(states).set_index("date")
    events = pd.DataFrame(done)
    return state, events


def simulate(price: pd.Series, target: pd.Series, fee: float) -> pd.DataFrame:
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
            "target_weight": target,
            "held_weight": held,
            "turnover": turn,
            "gross_return": gross,
            "fee_cost": cost,
            "net_return": net,
            "equity": eq,
        },
        index=price.index,
    )


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


def period_return(r: pd.Series, freq: str) -> pd.Series:
    return (1 + r).groupby(r.index.to_period(freq)).prod() - 1


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
    }


def event_period(first_breach_date: pd.Timestamp) -> str:
    if first_breach_date < PRIMARY_START:
        return "BEFORE_PRIMARY"
    if first_breach_date <= PRE2020_END:
        return "PRE_2020_NEW"
    return "REPLAY_2020"


def event_diag(events: pd.DataFrame, sims: dict[str, pd.DataFrame],
               state: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()

    idx = state.index
    rows = []
    for _, e in events.iterrows():
        breach = pd.Timestamp(e["first_breach_date"])
        reset = pd.Timestamp(e["reset_date"]) if pd.notna(e["reset_date"]) else None
        start = next_date(idx, breach)
        if start is None:
            continue
        end = next_date(idx, reset) if reset is not None else idx[-1]
        if end is None:
            end = idx[-1]

        deepest = sum(pd.notna(e[f"breach_{p}_date"]) for p in (20, 35, 50, 65))
        row = {
            "event_id": int(e["event_id"]),
            "period_group": event_period(breach),
            "status": e["status"],
            "prior_peak_date": pd.Timestamp(e["prior_peak_date"]).date().isoformat(),
            "first_breach_date": breach.date().isoformat(),
            "start_execution_date": start.date().isoformat(),
            "reset_date": reset.date().isoformat() if reset is not None else "",
            "end_execution_date": end.date().isoformat(),
            "max_drawdown": float(e["max_drawdown"]),
            "max_drawdown_date": pd.Timestamp(e["max_drawdown_date"]).date().isoformat(),
            "deepest_level": int(deepest),
            "deployed_tranches": int(deepest),
        }

        for p in (20, 35, 50, 65):
            v = e[f"breach_{p}_date"]
            row[f"breach_{p}_date"] = (
                pd.Timestamp(v).date().isoformat() if pd.notna(v) else ""
            )

        for name in ("R008", "STATIC10", "STATIC15", "STATIC20"):
            rr = sims[name].loc[start:end, "net_return"]
            row[f"{name.lower()}_event_return"] = float((1 + rr).prod() - 1)

        row["benefit_vs_static10"] = row["r008_event_return"] - row["static10_event_return"]
        row["benefit_vs_static15"] = row["r008_event_return"] - row["static15_event_return"]
        row["benefit_vs_static20"] = row["r008_event_return"] - row["static20_event_return"]
        rows.append(row)

    return pd.DataFrame(rows)


def severity_summary(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()

    closed = events[events["status"] == "CLOSED"].copy()
    rows = []
    for period_name in ("ALL", "PRE_2020_NEW", "REPLAY_2020"):
        x = closed if period_name == "ALL" else closed[closed["period_group"] == period_name]
        for level in (1, 2, 3, 4):
            y = x[x["deepest_level"] == level]
            if y.empty:
                continue
            row = {
                "period_group": period_name,
                "deepest_level": level,
                "closed_events": len(y),
            }
            for col, short in (
                ("benefit_vs_static10", "benefit10"),
                ("benefit_vs_static15", "benefit15"),
                ("benefit_vs_static20", "benefit20"),
            ):
                vals = y[col].astype(float)
                pos = vals[vals > 0]
                row[f"{short}_mean"] = float(vals.mean())
                row[f"{short}_median"] = float(vals.median())
                row[f"{short}_positive_fraction"] = float((vals > 0).mean())
                row[f"{short}_largest_positive_share"] = (
                    float(pos.max() / pos.sum()) if len(pos) else np.nan
                )
            rows.append(row)
    return pd.DataFrame(rows)


def self_test():
    idx = pd.date_range("2010-01-01", periods=12)
    p = pd.Series(
        [100, 110, 105, 88, 80, 70, 50, 35, 55, 90, 111, 100],
        index=idx,
        dtype=float,
    )
    state, events = build_state(p)
    expected = [.10, .10, .10, .125, .125, .15, .175, .20, .20, .20, .10, .10]
    if state["target_btc_weight"].round(6).tolist() != expected:
        raise AssertionError("state self-test failed")
    if len(events) != 1 or events.iloc[0]["status"] != "CLOSED":
        raise AssertionError("event self-test failed")


def write_summary(path: Path, metrics_df: pd.DataFrame, events: pd.DataFrame,
                  severity: pd.DataFrame, state: pd.DataFrame, audit: dict):
    base = metrics_df[metrics_df["fee_bps"] == 10.0].copy()
    order = ["PRIMARY_LONG", "PRE_2020_NEW", "REPLAY_2020", "POST_2023", "FULL_AVAILABLE"]
    base["slice_order"] = base["slice"].map({k: i for i, k in enumerate(order)})
    base = base.sort_values(["slice_order", "strategy"])

    lines = [
        "# R008-E002 Long-History Independent Validation — Engine Output v0.1",
        "",
        "**Status:** raw validation output; no automatic PASS/FAIL.",
        "",
        "- Source: Blockchain.com market-price reference series",
        f"- Clean rows: **{audit['clean_rows']}**",
        f"- Period: **{audit['clean_start']} -> {audit['clean_end']}**",
        f"- Data gate: **{audit['status']}**",
        "- Frozen architecture: **10% BTC base + four 2.5% crisis tranches at -20/-35/-50/-65%**",
        "- Reset: **new daily-reference-price all-time high**",
        "- Baseline cost: **10 bps**",
        "",
        "## Baseline metrics",
        "",
        "| Strategy | Slice | CAGR | Max DD | Calmar | Ending | Avg BTC | Turnover |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in base.itertuples(index=False):
        lines.append(
            f"| {r.strategy} | {r.slice} | {r.cagr:.2%} | {r.max_drawdown:.2%} | "
            f"{r.calmar:.2f} | {r.ending_multiple:.3f}x | "
            f"{r.average_btc_exposure:.2%} | {r.turnover:.3f} |"
        )

    lines += ["", "## Crisis events", ""]
    if events.empty:
        lines.append("- No crisis events detected.")
    else:
        closed = int((events["status"] == "CLOSED").sum())
        open_n = int((events["status"] != "CLOSED").sum())
        lines.append(f"- Total mechanically detected events: **{len(events)}**")
        lines.append(f"- Closed: **{closed}**; open/censored: **{open_n}**")
        pre = events[events["period_group"] == "PRE_2020_NEW"]
        lines.append(f"- PRE_2020_NEW events: **{len(pre)}**")

    lines += ["", "## Dry-powder utilization", ""]
    for weight, share in state["target_btc_weight"].value_counts(normalize=True).sort_index().items():
        lines.append(f"- Target BTC {weight:.1%}: **{share:.1%}** of all source observations")

    lines += [
        "",
        "## Important",
        "",
        "This file is raw engine output. The formal HISTORICAL PASS / REDESIGN / FAIL decision must be made against the frozen E002 protocol after reviewing PRE_2020_NEW, PRIMARY_LONG, severity, event concentration, and cost stress.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir")
    args = ap.parse_args()
    out = (
        Path(args.outdir).expanduser().resolve()
        if args.outdir
        else Path.cwd() / f"R008_E002_RUN_{datetime.now():%Y-%m-%d_%H-%M-%S}"
    )
    out.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("R008-E002 LONG-HISTORY INDEPENDENT VALIDATION v0.1")
    print("=" * 72)

    print("[1/9] Synthetic state-machine self-test...")
    self_test()
    print("      PASS")

    print("[2/9] Downloading Blockchain.com market-price history...")
    raw, obj = download_source()
    raw_path = out / "r008_e002_blockchain_market_price_raw.json"
    raw_path.write_bytes(raw)
    print("      raw bytes:", len(raw))

    print("[3/9] Cleaning + data audit...")
    clean = clean_source(obj)
    clean_path = out / "r008_e002_price_clean.csv"
    clean.to_csv(clean_path, index=False)
    audit = audit_source(obj, clean)
    audit["raw_sha256"] = sha256_bytes(raw)
    audit["clean_csv_sha256"] = sha256_file(clean_path)
    (out / "r008_e002_data_audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("      ", audit["clean_rows"], "rows", audit["clean_start"], "->", audit["clean_end"])
    print("      data gate:", audit["status"])

    if audit["status"] != "PASS":
        run = {
            "status": "DATA_REDESIGN",
            "engine_version": VERSION,
            "protocol": PROTOCOL,
            "source_url": SOURCE_URL,
            "data_audit": audit,
        }
        (out / "r008_e002_run_state.json").write_text(
            json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("DATA GATE FAILED. No strategy P&L calculated.")
        print("Results:", out)
        return

    price = clean.set_index("date")["price"].astype(float)

    print("[4/9] Building full-history path state...")
    state, raw_events = build_state(price)
    print("      crisis episodes:", len(raw_events))

    targets = {
        "R008": state["target_btc_weight"],
        "CASH": pd.Series(0.0, index=price.index),
        "STATIC10": pd.Series(0.10, index=price.index),
        "STATIC15": pd.Series(0.15, index=price.index),
        "STATIC20": pd.Series(0.20, index=price.index),
        "BTC100": pd.Series(1.0, index=price.index),
    }

    slices = [
        ("FULL_AVAILABLE", price.index[0], None),
        ("PRIMARY_LONG", max(PRIMARY_START, price.index[0]), None),
        ("PRE_2020_NEW", max(PRIMARY_START, price.index[0]), min(PRE2020_END, price.index[-1])),
        ("REPLAY_2020", max(REPLAY_START, price.index[0]), None),
        ("POST_2023", max(LATE_START, price.index[0]), None),
    ]

    print("[5/9] Running fee grid and evaluation slices...")
    rows = []
    sims_by_fee = {}
    for fee in FEES:
        sims = {name: simulate(price, target, fee) for name, target in targets.items()}
        sims_by_fee[fee] = sims
        for name, sim in sims.items():
            for slice_name, start, end in slices:
                row = metrics(name, fee, sim, slice_name, start, end)
                if row is not None:
                    rows.append(row)
    metrics_df = pd.DataFrame(rows)

    print("[6/9] Yearly returns...")
    yearly_rows = []
    for fee, sims in sims_by_fee.items():
        for name, sim in sims.items():
            for slice_name, start, end in (
                ("PRIMARY_LONG", max(PRIMARY_START, price.index[0]), None),
                ("PRE_2020_NEW", max(PRIMARY_START, price.index[0]), min(PRE2020_END, price.index[-1])),
            ):
                x = sim[sim.index >= start]
                if end is not None:
                    x = x[x.index <= end]
                if x.empty:
                    continue
                yr = period_return(x["net_return"], "Y")
                for period, val in yr.items():
                    yearly_rows.append(
                        {
                            "strategy": name,
                            "fee_bps": fee * 10000,
                            "slice": slice_name,
                            "year": int(period.year),
                            "return": float(val),
                        }
                    )
    yearly = pd.DataFrame(yearly_rows)

    print("[7/9] Crisis + severity diagnostics...")
    base = sims_by_fee[BASE_FEE]
    events = event_diag(raw_events, base, state)
    severity = severity_summary(events)

    print("[8/9] Writing outputs...")
    daily = state.copy()
    daily["btc_return"] = base["R008"]["btc_return"]
    for name in ("R008", "STATIC10", "STATIC15", "STATIC20", "BTC100", "CASH"):
        sim = base[name]
        daily[f"{name.lower()}_held_weight"] = sim["held_weight"]
        daily[f"{name.lower()}_net_return"] = sim["net_return"]
        daily[f"{name.lower()}_equity"] = sim["equity"]

    metrics_df.to_csv(out / "r008_e002_metrics.csv", index=False)
    yearly.to_csv(out / "r008_e002_yearly_returns.csv", index=False)
    state.to_csv(out / "r008_e002_state_daily.csv")
    raw_events.to_csv(out / "r008_e002_crisis_events_raw.csv", index=False)
    events.to_csv(out / "r008_e002_crisis_event_diagnostics.csv", index=False)
    severity.to_csv(out / "r008_e002_severity_summary.csv", index=False)
    daily.to_csv(out / "r008_e002_baseline_daily.csv")

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
            "reset": "new_reference_price_all_time_high",
            "fee_grid": list(FEES),
            "primary_start": PRIMARY_START.date().isoformat(),
            "pre2020_end": PRE2020_END.date().isoformat(),
            "replay_start": REPLAY_START.date().isoformat(),
            "late_start": LATE_START.date().isoformat(),
            "cash_return": 0.0,
            "static15_prospectively_frozen": True,
        },
        "source": {
            "url": SOURCE_URL,
            "raw_sha256": audit["raw_sha256"],
            "clean_csv_sha256": audit["clean_csv_sha256"],
            "clean_rows": audit["clean_rows"],
            "start": audit["clean_start"],
            "end": audit["clean_end"],
        },
        "data_gate": audit,
        "crisis_events": len(raw_events),
        "outputs": [
            "r008_e002_blockchain_market_price_raw.json",
            "r008_e002_price_clean.csv",
            "r008_e002_data_audit.json",
            "r008_e002_metrics.csv",
            "r008_e002_yearly_returns.csv",
            "r008_e002_state_daily.csv",
            "r008_e002_crisis_events_raw.csv",
            "r008_e002_crisis_event_diagnostics.csv",
            "r008_e002_severity_summary.csv",
            "r008_e002_baseline_daily.csv",
            "r008_e002_summary.md",
            "r008_e002_run_state.json",
        ],
    }
    (out / "r008_e002_run_state.json").write_text(
        json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_summary(
        out / "r008_e002_summary.md",
        metrics_df,
        events,
        severity,
        state,
        audit,
    )

    print("[9/9] FINISHED")
    print("Results:", out)


if __name__ == "__main__":
    main()
