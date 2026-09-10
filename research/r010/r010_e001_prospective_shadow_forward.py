"""R010-E001 prospective shadow-forward tracker v0.1.

No historical R010 P&L is produced. Pre-inception BTC history is used only to
initialize SMA120, closing ATH, and armed drawdown tranches. Forward P&L begins
from the fixed 2026-09-11 UTC inception frozen in the protocol.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

VERSION = "0.1"
PROTOCOL = "r010-e001-prospective-shadow-forward-protocol-v0.1"

BASE_URL = "https://data-api.binance.vision"
KLINES_PATH = "/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1d"
START_MS = int(pd.Timestamp("2017-07-01", tz="UTC").timestamp() * 1000)
DAY_MS = 86_400_000
LIMIT = 1000

SMA_LOOKBACK = 120
TREND_WEIGHT = 0.10
RECOVERY_TRANCHE = 0.025
ARM_THRESHOLDS = (-0.20, -0.35, -0.50, -0.65)
FEES = (0.0005, 0.0010, 0.0025, 0.0050)
BASELINE_FEE = 0.0010
CASH_RETURN = 0.0
EPS = 1e-12
DAYS_PER_YEAR = 365.25

SIGNAL_BAR_DATE = pd.Timestamp("2026-09-10")
FORWARD_INCEPTION = pd.Timestamp("2026-09-11")


def fetch_json(url: str):
    req = Request(url, headers={"User-Agent": "botmarketplace-r010-e001-forward/0.1"})
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all_closed_klines() -> pd.DataFrame:
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start = START_MS
    rows = []
    while True:
        qs = urlencode({
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "startTime": start,
            "limit": LIMIT,
        })
        obj = fetch_json(BASE_URL + KLINES_PATH + "?" + qs)
        if not isinstance(obj, list):
            raise RuntimeError(f"Unexpected Binance response: {obj}")
        if not obj:
            break
        rows.extend(obj)
        last_open = int(obj[-1][0])
        nxt = last_open + DAY_MS
        if len(obj) < LIMIT or nxt >= now_ms:
            break
        if nxt <= start:
            raise RuntimeError("Kline pagination stalled")
        start = nxt

    parsed = []
    for r in rows:
        if not isinstance(r, list) or len(r) < 7:
            continue
        close_ms = int(r[6])
        if close_ms >= now_ms:
            continue
        parsed.append({
            "open_time_ms": int(r[0]),
            "date": pd.to_datetime(int(r[0]), unit="ms", utc=True).tz_convert(None).normalize(),
            "close": float(r[4]),
            "close_time_ms": close_ms,
        })
    if not parsed:
        raise RuntimeError("No fully closed Binance BTCUSDT daily bars")
    x = pd.DataFrame(parsed).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    if (x["close"] <= 0).any():
        raise RuntimeError("Non-positive BTCUSDT close retained")
    return x


def audit_source(x: pd.DataFrame) -> dict:
    gaps = x["date"].diff().dt.days.dropna()
    max_gap = int(gaps.max()) if len(gaps) else 0
    missing = int((gaps[gaps > 1] - 1).sum()) if len(gaps) else 0
    passed = len(x) >= SMA_LOOKBACK and max_gap <= 1
    return {
        "status": "PASS" if passed else "DATA_ISSUE_DO_NOT_INTERPRET",
        "source_base": BASE_URL,
        "endpoint": KLINES_PATH,
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "closed_rows": int(len(x)),
        "start": x["date"].iloc[0].date().isoformat(),
        "end": x["date"].iloc[-1].date().isoformat(),
        "duplicate_dates": int(x["date"].duplicated().sum()),
        "max_gap_days": max_gap,
        "missing_calendar_days": missing,
    }


def build_state(x: pd.DataFrame) -> pd.DataFrame:
    s = x[["date", "close"]].copy().set_index("date")
    s["sma120"] = s["close"].rolling(SMA_LOOKBACK, min_periods=SMA_LOOKBACK).mean()
    s["trend_on"] = (s["close"] > s["sma120"]) & s["sma120"].notna()

    peak = float(s["close"].iloc[0])
    armed = [False] * 4
    rows = []
    prev_trend = False
    prev_recovery = 0.0

    for i, (date, raw) in enumerate(s["close"].astype(float).items()):
        p = float(raw)
        new_ath = (i == 0 or p > peak + EPS)
        newly_armed = []
        reset_event = False

        if new_ath:
            if i > 0 and any(armed):
                reset_event = True
            peak = p
            armed = [False] * 4
            dd = 0.0
        else:
            dd = p / peak - 1.0
            for j, th in enumerate(ARM_THRESHOLDS):
                if (not armed[j]) and dd <= th + EPS:
                    armed[j] = True
                    newly_armed.append(j)

        armed_count = int(sum(armed))
        armed_weight = armed_count * RECOVERY_TRANCHE
        trend_on = bool(s.at[date, "trend_on"])
        trend_target = TREND_WEIGHT if trend_on else 0.0
        recovery_target = armed_weight if trend_on else 0.0
        r010_target = trend_target + recovery_target
        r009_crisis_target = armed_weight
        r009_target = trend_target + r009_crisis_target

        trend_turn_on = bool(i > 0 and trend_on and not prev_trend)
        trend_turn_off = bool(i > 0 and (not trend_on) and prev_trend)
        recovery_activation = bool(i > 0 and recovery_target > prev_recovery + EPS)
        recovery_deactivation = bool(i > 0 and recovery_target + EPS < prev_recovery)

        rows.append({
            "date": date,
            "close": p,
            "sma120": float(s.at[date, "sma120"]) if pd.notna(s.at[date, "sma120"]) else np.nan,
            "trend_on": trend_on,
            "trend_target": trend_target,
            "running_peak": peak,
            "drawdown": dd,
            "armed_count": armed_count,
            "armed_weight": armed_weight,
            "newly_armed_count": len(newly_armed),
            "newly_armed_levels": ",".join(str(int(abs(ARM_THRESHOLDS[j]) * 100)) for j in newly_armed),
            "new_ath": bool(new_ath),
            "reset_event": reset_event,
            "trend_turn_on": trend_turn_on,
            "trend_turn_off": trend_turn_off,
            "recovery_target": recovery_target,
            "recovery_activation_event": recovery_activation,
            "recovery_deactivation_event": recovery_deactivation,
            "r010_combined_target": r010_target,
            "r009_crisis_target": r009_crisis_target,
            "r009_combined_target": r009_target,
            "armed_while_trend_off": bool(armed_count > 0 and not trend_on),
        })

        prev_trend = trend_on
        prev_recovery = recovery_target

    return pd.DataFrame(rows).set_index("date")


def target_map(state: pd.DataFrame) -> dict[str, pd.Series]:
    idx = state.index
    return {
        "R010_COMBINED_DAILY": state["r010_combined_target"].astype(float),
        "RECOVERY10_DAILY": state["recovery_target"].astype(float),
        "R009_COMBINED_DAILY": state["r009_combined_target"].astype(float),
        "TREND10_DAILY": state["trend_target"].astype(float),
        "STATIC10_DAILY": pd.Series(0.10, index=idx),
        "STATIC15_DAILY": pd.Series(0.15, index=idx),
        "STATIC20_DAILY": pd.Series(0.20, index=idx),
    }


def simulate_forward(close: pd.Series, target: pd.Series, fee: float) -> pd.DataFrame:
    if SIGNAL_BAR_DATE not in close.index:
        return pd.DataFrame()
    dates = close.index
    pos = dates.get_loc(SIGNAL_BAR_DATE)
    if not isinstance(pos, (int, np.integer)):
        raise RuntimeError("Unexpected signal-date index")

    initial_target = float(target.loc[SIGNAL_BAR_DATE])
    equity = 1.0 - fee * abs(initial_target)
    w = initial_target
    rows = [{
        "date": SIGNAL_BAR_DATE,
        "record_type": "INCEPTION_ALLOCATION",
        "btc_return": 0.0,
        "desired_target": initial_target,
        "held_weight": 0.0,
        "pretrade_weight": 0.0,
        "turnover": abs(initial_target),
        "fee_cost": fee * abs(initial_target),
        "net_return": -fee * abs(initial_target),
        "equity": equity,
    }]

    for i in range(pos + 1, len(dates)):
        date = dates[i]
        if date < FORWARD_INCEPTION:
            continue
        r = float(close.iloc[i] / close.iloc[i - 1] - 1.0)
        held = w
        gross_factor = 1.0 + held * r
        pre = held * (1.0 + r) / gross_factor if gross_factor > 0 else 0.0
        desired = float(target.iloc[i])
        turn = abs(desired - pre)
        cost = fee * turn
        net = gross_factor - 1.0 - cost
        equity *= 1.0 + net
        w = desired
        rows.append({
            "date": date,
            "record_type": "FORWARD_DAY",
            "btc_return": r,
            "desired_target": desired,
            "held_weight": held,
            "pretrade_weight": pre,
            "turnover": turn,
            "fee_cost": cost,
            "net_return": net,
            "equity": equity,
        })
    return pd.DataFrame(rows).set_index("date")


def calc_metrics(name: str, fee: float, sim: pd.DataFrame) -> dict:
    if sim.empty:
        return {"strategy": name, "fee_bps": fee * 10000, "realized_forward_days": 0}
    x = sim[sim["record_type"] == "FORWARD_DAY"].copy()
    base = {
        "strategy": name,
        "fee_bps": fee * 10000,
        "realized_forward_days": int(len(x)),
        "ending_equity_including_inception_cost": float(sim["equity"].iloc[-1]),
        "turnover_including_inception": float(sim["turnover"].sum()),
        "fee_drag_simple": float(sim["fee_cost"].sum()),
    }
    if x.empty:
        return base

    eq0 = float(sim["equity"].iloc[0])
    eq = sim.loc[x.index, "equity"] / eq0
    r = x["net_return"]
    n = len(x)
    years = n / DAYS_PER_YEAR
    cagr = float(eq.iloc[-1] ** (1.0 / years) - 1.0) if n >= 30 and eq.iloc[-1] > 0 else np.nan
    vol = float(r.std(ddof=1) * math.sqrt(365.0)) if n >= 2 else np.nan
    dd = float((eq / eq.cummax() - 1.0).min())
    base.update({
        "first_forward_date": x.index[0].date().isoformat(),
        "last_forward_date": x.index[-1].date().isoformat(),
        "ending_multiple_after_inception_allocation": float(eq.iloc[-1]),
        "cagr_if_30plus_days": cagr,
        "annualized_vol": vol,
        "max_drawdown": dd,
        "calmar_if_available": cagr / abs(dd) if pd.notna(cagr) and dd < 0 else np.nan,
        "average_btc_exposure": float(x["held_weight"].mean()),
        "max_btc_exposure": float(x["held_weight"].max()),
    })
    return base


def compact_event_table(state: pd.DataFrame) -> pd.DataFrame:
    x = state[state.index >= SIGNAL_BAR_DATE].copy()
    if x.empty:
        return pd.DataFrame(columns=[
            "date", "event_type", "close", "drawdown", "trend_on", "armed_count", "recovery_target", "r010_combined_target"
        ])
    rows = []
    for date, r in x.iterrows():
        events = []
        if int(r["newly_armed_count"]) > 0:
            events.append("ARM_" + str(r["newly_armed_levels"]))
        if bool(r["trend_turn_on"]):
            events.append("TREND_ON")
        if bool(r["trend_turn_off"]):
            events.append("TREND_OFF")
        if bool(r["recovery_activation_event"]):
            events.append("RECOVERY_ACTIVATE")
        if bool(r["recovery_deactivation_event"]):
            events.append("RECOVERY_DEACTIVATE")
        if bool(r["reset_event"]):
            events.append("ATH_RESET")
        for ev in events:
            rows.append({
                "date": date,
                "event_type": ev,
                "close": float(r["close"]),
                "drawdown": float(r["drawdown"]),
                "trend_on": bool(r["trend_on"]),
                "armed_count": int(r["armed_count"]),
                "recovery_target": float(r["recovery_target"]),
                "r010_combined_target": float(r["r010_combined_target"]),
            })
    return pd.DataFrame(rows)


def write_waiting(outdir: Path, audit: dict, state: pd.DataFrame) -> None:
    latest = state.iloc[-1]
    run_state = {
        "status": "WAITING_FOR_SIGNAL_BAR_CLOSE",
        "engine_version": VERSION,
        "protocol": PROTOCOL,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixed_forward_inception_utc": "2026-09-11T00:00:00+00:00",
        "required_signal_bar_date": "2026-09-10",
        "latest_fully_closed_bar": state.index[-1].date().isoformat(),
        "reason": "The frozen 2026-09-10 UTC signal bar is not yet fully closed.",
        "source_audit": audit,
        "latest_state_for_warmup_only": {
            "close": float(latest["close"]),
            "trend_on": bool(latest["trend_on"]),
            "armed_count": int(latest["armed_count"]),
        },
    }
    (outdir / "r010_e001_run_state.json").write_text(json.dumps(run_state, indent=2), encoding="utf-8")
    md = (
        "# R010-E001 Prospective Shadow Forward\n\n"
        "**Status:** WAITING_FOR_SIGNAL_BAR_CLOSE\n\n"
        "The fixed 2026-09-10 UTC signal bar is not yet fully closed. "
        "Forward inception remains 2026-09-11 00:00 UTC and will not move.\n"
    )
    (outdir / "r010_e001_summary.md").write_text(md, encoding="utf-8")
    print(md)


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    bars = fetch_all_closed_klines()
    audit = audit_source(bars)
    state = build_state(bars)

    (outdir / "r010_e001_source_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    state.reset_index().to_csv(outdir / "r010_e001_state_history.csv", index=False)

    if audit["status"] != "PASS":
        raise RuntimeError(f"Source audit failed: {audit}")

    if SIGNAL_BAR_DATE not in state.index:
        pd.DataFrame().to_csv(outdir / "r010_e001_forward_daily.csv", index=False)
        pd.DataFrame().to_csv(outdir / "r010_e001_forward_metrics.csv", index=False)
        compact_event_table(state).to_csv(outdir / "r010_e001_state_events.csv", index=False)
        write_waiting(outdir, audit, state)
        return

    targets = target_map(state)
    close = state["close"].astype(float)
    all_sims = {}
    metrics_rows = []
    for fee in FEES:
        for name, target in targets.items():
            sim = simulate_forward(close, target, fee)
            all_sims[(name, fee)] = sim
            metrics_rows.append(calc_metrics(name, fee, sim))

    metrics = pd.DataFrame(metrics_rows)
    metrics.to_csv(outdir / "r010_e001_forward_metrics.csv", index=False)

    wide = None
    for name in targets:
        sim = all_sims[(name, BASELINE_FEE)].copy()
        if sim.empty:
            continue
        z = sim[["record_type", "desired_target", "held_weight", "pretrade_weight", "turnover", "fee_cost", "net_return", "equity"]].copy()
        z = z.add_prefix(name + "__")
        wide = z if wide is None else wide.join(z, how="outer")
    if wide is None:
        wide = pd.DataFrame()
    wide.reset_index().to_csv(outdir / "r010_e001_forward_daily.csv", index=False)

    events = compact_event_table(state)
    events.to_csv(outdir / "r010_e001_state_events.csv", index=False)

    prospective = state[state.index >= SIGNAL_BAR_DATE].copy()
    r010_sim = all_sims[("R010_COMBINED_DAILY", BASELINE_FEE)]
    realized_days = int((r010_sim["record_type"] == "FORWARD_DAY").sum()) if not r010_sim.empty else 0
    new_arms = int(prospective["newly_armed_count"].sum()) if len(prospective) else 0
    activation_events = int(prospective["recovery_activation_event"].sum()) if len(prospective) else 0
    deactivation_events = int(prospective["recovery_deactivation_event"].sum()) if len(prospective) else 0
    reset_events = int(prospective["reset_event"].sum()) if len(prospective) else 0
    armed_trend_off_days = int(prospective["armed_while_trend_off"].sum()) if len(prospective) else 0

    calendar_mature = realized_days >= 365
    mechanism_ready = new_arms >= 1 and activation_events >= 1
    if calendar_mature and mechanism_ready:
        evidence_status = "MATURE_FORWARD_SAMPLE_REQUIRES_FORMAL_REVIEW"
    elif calendar_mature:
        evidence_status = "365D_REACHED_WAITING_FOR_MECHANISM_EVENT"
    else:
        evidence_status = "FORWARD_EVIDENCE_ACCUMULATING"

    latest = state.iloc[-1]
    signal = state.loc[SIGNAL_BAR_DATE]
    run_state = {
        "status": "PASS",
        "engine_version": VERSION,
        "protocol": PROTOCOL,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_status": evidence_status,
        "fixed_forward_inception_utc": "2026-09-11T00:00:00+00:00",
        "signal_bar_date": "2026-09-10",
        "latest_fully_closed_bar": state.index[-1].date().isoformat(),
        "realized_forward_days": realized_days,
        "signal_state": {
            "close": float(signal["close"]),
            "sma120": float(signal["sma120"]) if pd.notna(signal["sma120"]) else None,
            "trend_on": bool(signal["trend_on"]),
            "armed_count": int(signal["armed_count"]),
            "armed_weight": float(signal["armed_weight"]),
            "recovery_target": float(signal["recovery_target"]),
            "r010_combined_target": float(signal["r010_combined_target"]),
            "r009_combined_target": float(signal["r009_combined_target"]),
        },
        "latest_state": {
            "close": float(latest["close"]),
            "sma120": float(latest["sma120"]) if pd.notna(latest["sma120"]) else None,
            "trend_on": bool(latest["trend_on"]),
            "drawdown": float(latest["drawdown"]),
            "armed_count": int(latest["armed_count"]),
            "recovery_target": float(latest["recovery_target"]),
            "r010_combined_target": float(latest["r010_combined_target"]),
        },
        "prospective_mechanism_counts_from_signal_bar": {
            "newly_armed_tranches": new_arms,
            "recovery_activation_events": activation_events,
            "recovery_deactivation_events": deactivation_events,
            "ath_reset_events": reset_events,
            "armed_while_trend_off_days": armed_trend_off_days,
            "mechanism_event_ready": mechanism_ready,
        },
        "freeze": {
            "sma_lookback": SMA_LOOKBACK,
            "trend_weight": TREND_WEIGHT,
            "recovery_tranche": RECOVERY_TRANCHE,
            "arming_thresholds": list(ARM_THRESHOLDS),
            "recovery_deployment": "armed_weight_only_when_trend_on",
            "arming_reset": "new_closing_ath_only",
            "fee_grid": list(FEES),
            "baseline_fee": BASELINE_FEE,
            "cash_return": CASH_RETURN,
        },
        "source_audit": audit,
        "outputs": [
            "r010_e001_run_state.json",
            "r010_e001_source_audit.json",
            "r010_e001_state_history.csv",
            "r010_e001_forward_daily.csv",
            "r010_e001_forward_metrics.csv",
            "r010_e001_state_events.csv",
            "r010_e001_summary.md",
        ],
    }
    (outdir / "r010_e001_run_state.json").write_text(json.dumps(run_state, indent=2), encoding="utf-8")

    base = metrics[metrics["fee_bps"] == 10.0].copy()
    lines = [
        "# R010-E001 Prospective Shadow Forward — Current Snapshot",
        "",
        f"**Evidence status:** {evidence_status}",
        "",
        f"- Fixed forward inception: **2026-09-11T00:00:00+00:00**",
        f"- Signal bar: **2026-09-10**",
        f"- Latest fully closed BTCUSDT day: **{state.index[-1].date().isoformat()}**",
        f"- Realized forward days: **{realized_days}**",
        f"- Signal trend ON: **{bool(signal['trend_on'])}**",
        f"- Signal armed tranches: **{int(signal['armed_count'])}**",
        f"- Signal recovery target: **{float(signal['recovery_target']):.1%}**",
        f"- Signal R010 combined target: **{float(signal['r010_combined_target']):.1%}**",
        f"- Prospective newly armed tranches: **{new_arms}**",
        f"- Prospective recovery activation events: **{activation_events}**",
        "",
        "## Baseline 10 bps",
        "",
        "| Strategy | Forward days | Equity incl. inception cost | Turnover incl. inception | Fee drag |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in base.iterrows():
        eq = r.get("ending_equity_including_inception_cost", np.nan)
        turn = r.get("turnover_including_inception", np.nan)
        drag = r.get("fee_drag_simple", np.nan)
        lines.append(
            f"| {r['strategy']} | {int(r['realized_forward_days'])} | "
            f"{eq:.9f} | {turn:.6f} | {drag:.6f} |"
        )
    lines.extend([
        "",
        "This is a prospective shadow-forward record. Pre-inception BTC history initializes state only and contributes no R010 forward P&L.",
        "R009-E002 remains a separate frozen forward record and is not changed by this experiment.",
    ])
    md = "\n".join(lines) + "\n"
    (outdir / "r010_e001_summary.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args()
    main(args.outdir)
