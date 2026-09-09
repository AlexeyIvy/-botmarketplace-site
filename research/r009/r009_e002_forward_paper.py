"""R009-E002 frozen forward paper tracker v0.1.

Uses only fully closed Binance Spot BTCUSDT 1d bars. Historical bars before
inception initialize SMA/crisis state only; forward P&L begins from the fixed
2026-09-10 UTC inception defined in the protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

VERSION = "0.1"
PROTOCOL = "r009-e002-forward-paper-protocol-v0.1"

BASE_URL = "https://data-api.binance.vision"
KLINES_PATH = "/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1d"
HISTORY_START_MS = int(pd.Timestamp("2017-07-01", tz="UTC").timestamp() * 1000)
DAY_MS = 86_400_000
LIMIT = 1000

SMA_LOOKBACK = 120
TREND_WEIGHT = 0.10
CRISIS_TRANCHE = 0.025
CRISIS_THRESH = (-0.20, -0.35, -0.50, -0.65)
FEES = (0.0005, 0.0010, 0.0025, 0.0050)
BASELINE_FEE = 0.0010
CASH_RETURN = 0.0
EPS = 1e-12
DAYS_PER_YEAR = 365.25

SIGNAL_BAR_DATE = pd.Timestamp("2026-09-09")
FORWARD_INCEPTION = pd.Timestamp("2026-09-10")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_json(url: str):
    req = Request(url, headers={"User-Agent": "botmarketplace-r009-e002-forward/0.1"})
    with urlopen(req, timeout=60) as resp:
        raw = resp.read()
    return raw, json.loads(raw.decode("utf-8"))


def fetch_all_closed_klines() -> tuple[pd.DataFrame, list[str]]:
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start = HISTORY_START_MS
    rows = []
    page_hashes: list[str] = []

    while True:
        qs = urlencode(
            {
                "symbol": SYMBOL,
                "interval": INTERVAL,
                "startTime": start,
                "limit": LIMIT,
            }
        )
        raw, obj = fetch_json(BASE_URL + KLINES_PATH + "?" + qs)
        page_hashes.append(sha256_bytes(raw))

        if not isinstance(obj, list):
            raise ValueError(f"Unexpected Binance response: {obj}")
        if not obj:
            break

        rows.extend(obj)
        last_open = int(obj[-1][0])
        next_start = last_open + DAY_MS
        if len(obj) < LIMIT or next_start >= now_ms:
            break
        if next_start <= start:
            raise RuntimeError("Kline pagination did not advance")
        start = next_start

    if not rows:
        raise ValueError("No Binance BTCUSDT daily klines returned")

    parsed = []
    for r in rows:
        if not isinstance(r, list) or len(r) < 7:
            continue
        parsed.append(
            {
                "open_time_ms": int(r[0]),
                "date": pd.to_datetime(int(r[0]), unit="ms", utc=True).tz_convert(None).normalize(),
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
                "close_time_ms": int(r[6]),
            }
        )

    x = pd.DataFrame(parsed)
    x = x[x["close_time_ms"] < now_ms].copy()
    x = x.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    if x.empty:
        raise ValueError("No fully closed Binance daily bars available")
    if (x["close"] <= 0).any():
        raise ValueError("Non-positive close in Binance data")
    return x, page_hashes


def audit_source(x: pd.DataFrame, page_hashes: list[str]) -> dict:
    gaps = x["date"].diff().dt.days.dropna()
    return {
        "status": "PASS" if len(x) >= SMA_LOOKBACK and (int(gaps.max()) if len(gaps) else 1) <= 3 else "DATA_REDESIGN",
        "source_base": BASE_URL,
        "endpoint": KLINES_PATH,
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "closed_rows": int(len(x)),
        "start": x["date"].iloc[0].date().isoformat(),
        "end": x["date"].iloc[-1].date().isoformat(),
        "duplicate_dates": int(x["date"].duplicated().sum()),
        "max_gap_days": int(gaps.max()) if len(gaps) else 0,
        "missing_calendar_days": int((gaps[gaps > 1] - 1).sum()) if len(gaps) else 0,
        "page_sha256": page_hashes,
    }


def build_state(x: pd.DataFrame) -> pd.DataFrame:
    s = x[["date", "close"]].copy().set_index("date")
    s["sma120"] = s["close"].rolling(SMA_LOOKBACK, min_periods=SMA_LOOKBACK).mean()
    s["trend_on"] = (s["close"] > s["sma120"]) & s["sma120"].notna()
    s["trend_target"] = np.where(s["trend_on"], TREND_WEIGHT, 0.0)

    peak = float(s["close"].iloc[0])
    sticky = [False] * 4
    crisis_targets = []
    drawdowns = []
    levels = []
    new_aths = []

    for i, p0 in enumerate(s["close"].astype(float)):
        p = float(p0)
        new_ath = (i == 0 or p > peak + EPS)
        if new_ath:
            peak = p
            sticky = [False] * 4
            dd = 0.0
        else:
            dd = p / peak - 1.0
            for j, threshold in enumerate(CRISIS_THRESH):
                if (not sticky[j]) and dd <= threshold + EPS:
                    sticky[j] = True
        level = int(sum(sticky))
        drawdowns.append(dd)
        levels.append(level)
        crisis_targets.append(CRISIS_TRANCHE * level)
        new_aths.append(bool(new_ath))

    s["drawdown"] = drawdowns
    s["crisis_level"] = levels
    s["crisis_target"] = crisis_targets
    s["combined_target"] = s["trend_target"] + s["crisis_target"]
    s["new_ath"] = new_aths
    return s


def target_map(state: pd.DataFrame) -> dict[str, pd.Series]:
    idx = state.index
    return {
        "R009_COMBINED_DAILY": state["combined_target"].astype(float),
        "TREND10_DAILY": state["trend_target"].astype(float),
        "CRISIS10_DAILY": state["crisis_target"].astype(float),
        "STATIC10_DAILY": pd.Series(0.10, index=idx),
        "STATIC15_DAILY": pd.Series(0.15, index=idx),
        "STATIC20_DAILY": pd.Series(0.20, index=idx),
    }


def simulate_daily_forward(close: pd.Series, target: pd.Series, fee: float) -> pd.DataFrame:
    if SIGNAL_BAR_DATE not in close.index:
        return pd.DataFrame()

    dates = close.index
    signal_pos = dates.get_loc(SIGNAL_BAR_DATE)
    if isinstance(signal_pos, slice) or not isinstance(signal_pos, (int, np.integer)):
        raise ValueError("Unexpected signal date index")

    initial_target = float(target.loc[SIGNAL_BAR_DATE])
    equity = 1.0 - fee * abs(initial_target)
    w = initial_target
    rows = [
        {
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
        }
    ]

    for i in range(signal_pos + 1, len(dates)):
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
        rows.append(
            {
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
            }
        )

    return pd.DataFrame(rows).set_index("date")


def simulate_static15_monthly_forward(close: pd.Series, fee: float) -> pd.DataFrame:
    if SIGNAL_BAR_DATE not in close.index:
        return pd.DataFrame()
    dates = close.index
    signal_pos = dates.get_loc(SIGNAL_BAR_DATE)
    weight = 0.15
    equity = 1.0 - fee * weight
    w = weight
    rows = [
        {
            "date": SIGNAL_BAR_DATE,
            "record_type": "INCEPTION_ALLOCATION",
            "btc_return": 0.0,
            "desired_target": weight,
            "held_weight": 0.0,
            "pretrade_weight": 0.0,
            "turnover": weight,
            "fee_cost": fee * weight,
            "net_return": -fee * weight,
            "equity": equity,
        }
    ]

    for i in range(signal_pos + 1, len(dates)):
        date = dates[i]
        if date < FORWARD_INCEPTION:
            continue
        r = float(close.iloc[i] / close.iloc[i - 1] - 1.0)
        held = w
        gross_factor = 1.0 + held * r
        pre = held * (1.0 + r) / gross_factor if gross_factor > 0 else 0.0
        month_end = (date + pd.Timedelta(days=1)).month != date.month
        turn = abs(weight - pre) if month_end else 0.0
        cost = fee * turn
        net = gross_factor - 1.0 - cost
        equity *= 1.0 + net
        w = weight if month_end else pre
        rows.append(
            {
                "date": date,
                "record_type": "FORWARD_DAY",
                "btc_return": r,
                "desired_target": weight,
                "held_weight": held,
                "pretrade_weight": pre,
                "turnover": turn,
                "fee_cost": cost,
                "net_return": net,
                "equity": equity,
            }
        )

    return pd.DataFrame(rows).set_index("date")


def calc_metrics(name: str, fee: float, sim: pd.DataFrame) -> dict:
    if sim.empty:
        return {
            "strategy": name,
            "fee_bps": fee * 10000,
            "realized_forward_days": 0,
        }
    x = sim[sim["record_type"] == "FORWARD_DAY"].copy()
    if x.empty:
        return {
            "strategy": name,
            "fee_bps": fee * 10000,
            "realized_forward_days": 0,
            "ending_equity_including_inception_cost": float(sim["equity"].iloc[-1]),
            "turnover_including_inception": float(sim["turnover"].sum()),
            "fee_drag_simple": float(sim["fee_cost"].sum()),
        }

    r = x["net_return"]
    eq0 = float(sim["equity"].iloc[0])
    eq = sim.loc[x.index, "equity"] / eq0
    dd = float((eq / eq.cummax() - 1.0).min())
    n = len(x)
    years = n / DAYS_PER_YEAR
    cagr = float(eq.iloc[-1] ** (1.0 / years) - 1.0) if n >= 30 and eq.iloc[-1] > 0 else np.nan
    vol = float(r.std(ddof=1) * math.sqrt(365.0)) if n >= 2 else np.nan
    return {
        "strategy": name,
        "fee_bps": fee * 10000,
        "realized_forward_days": n,
        "first_forward_date": x.index[0].date().isoformat(),
        "last_forward_date": x.index[-1].date().isoformat(),
        "ending_multiple_after_inception_allocation": float(eq.iloc[-1]),
        "cagr_if_30plus_days": cagr,
        "annualized_vol": vol,
        "max_drawdown": dd,
        "calmar_if_available": cagr / abs(dd) if pd.notna(cagr) and dd < 0 else np.nan,
        "average_btc_exposure": float(x["held_weight"].mean()),
        "max_btc_exposure": float(x["held_weight"].max()),
        "turnover_including_inception": float(sim["turnover"].sum()),
        "fee_drag_simple": float(sim["fee_cost"].sum()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args()
    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    bars, hashes = fetch_all_closed_klines()
    audit = audit_source(bars, hashes)
    state = build_state(bars)
    close = state["close"]

    bars.to_csv(outdir / "r009_e002_source_closed_bars.csv", index=False)
    state.reset_index().to_csv(outdir / "r009_e002_state_history.csv", index=False)
    (outdir / "r009_e002_source_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )

    if audit["status"] != "PASS":
        raise RuntimeError(f"DATA_REDESIGN: {audit}")

    signal_ready = SIGNAL_BAR_DATE in state.index
    latest = state.iloc[-1]

    all_sims: dict[tuple[str, float], pd.DataFrame] = {}
    metrics_rows = []
    targets = target_map(state)
    for fee in FEES:
        for name, target in targets.items():
            sim = simulate_daily_forward(close, target, fee)
            all_sims[(name, fee)] = sim
            metrics_rows.append(calc_metrics(name, fee, sim))
        sm = simulate_static15_monthly_forward(close, fee)
        all_sims[("STATIC15_MONTHLY", fee)] = sm
        metrics_rows.append(calc_metrics("STATIC15_MONTHLY", fee, sm))

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df.to_csv(outdir / "r009_e002_forward_metrics.csv", index=False)

    # Baseline forward history in wide audit-friendly form.
    base_names = list(targets.keys()) + ["STATIC15_MONTHLY"]
    wide = None
    for name in base_names:
        sim = all_sims[(name, BASELINE_FEE)]
        if sim.empty:
            continue
        z = sim.reset_index()[
            ["date", "record_type", "desired_target", "held_weight", "pretrade_weight", "turnover", "fee_cost", "net_return", "equity"]
        ].copy()
        z = z.rename(
            columns={
                c: f"{name.lower()}_{c}" for c in z.columns if c not in ("date", "record_type")
            }
        )
        if wide is None:
            wide = z
        else:
            wide = wide.merge(z.drop(columns=["record_type"]), on="date", how="outer")
    if wide is None:
        wide = pd.DataFrame(columns=["date"])
    wide.to_csv(outdir / "r009_e002_forward_daily.csv", index=False)

    # Baseline trade log.
    trades = []
    for name in base_names:
        sim = all_sims[(name, BASELINE_FEE)]
        if sim.empty:
            continue
        for date, row in sim.iterrows():
            if float(row["turnover"]) > EPS:
                trades.append(
                    {
                        "date": date.date().isoformat(),
                        "strategy": name,
                        "record_type": row["record_type"],
                        "pretrade_weight": float(row["pretrade_weight"]),
                        "desired_target": float(row["desired_target"]),
                        "turnover": float(row["turnover"]),
                        "fee_cost": float(row["fee_cost"]),
                    }
                )
    pd.DataFrame(trades).to_csv(outdir / "r009_e002_forward_trades.csv", index=False)

    state_obj = {
        "status": "PASS" if signal_ready else "WAITING_FOR_2026_09_09_CLOSE",
        "engine_version": VERSION,
        "protocol": PROTOCOL,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixed_forward_inception_utc": "2026-09-10T00:00:00+00:00",
        "signal_bar_date": SIGNAL_BAR_DATE.date().isoformat(),
        "latest_fully_closed_bar": state.index[-1].date().isoformat(),
        "latest_close": float(latest["close"]),
        "latest_sma120": None if pd.isna(latest["sma120"]) else float(latest["sma120"]),
        "latest_trend_on": bool(latest["trend_on"]),
        "latest_trend_target": float(latest["trend_target"]),
        "latest_drawdown": float(latest["drawdown"]),
        "latest_crisis_level": int(latest["crisis_level"]),
        "latest_crisis_target": float(latest["crisis_target"]),
        "latest_combined_target": float(latest["combined_target"]),
        "realized_forward_days": int(
            max(
                [
                    len(sim[sim["record_type"] == "FORWARD_DAY"])
                    for sim in all_sims.values()
                    if not sim.empty
                ]
                or [0]
            )
        ),
        "source_audit": audit,
        "freeze": {
            "sma_lookback": SMA_LOOKBACK,
            "trend_weight": TREND_WEIGHT,
            "crisis_tranche": CRISIS_TRANCHE,
            "crisis_thresholds": CRISIS_THRESH,
            "crisis_reset": "sticky_until_new_closing_ath",
            "baseline_fee": BASELINE_FEE,
            "fee_grid": FEES,
            "cash_return": CASH_RETURN,
        },
    }
    (outdir / "r009_e002_forward_state.json").write_text(
        json.dumps(state_obj, indent=2), encoding="utf-8"
    )

    baseline_metrics = metrics_df[metrics_df["fee_bps"] == BASELINE_FEE * 10000]
    lines = [
        "# R009-E002 Forward Paper Snapshot",
        "",
        f"Generated UTC: {state_obj['generated_at_utc']}",
        f"Status: **{state_obj['status']}**",
        f"Latest fully closed Binance BTCUSDT day: **{state_obj['latest_fully_closed_bar']}**",
        f"Fixed forward inception: **{state_obj['fixed_forward_inception_utc']}**",
        f"Realized forward days: **{state_obj['realized_forward_days']}**",
        "",
        "## Current frozen state",
        f"- close: {state_obj['latest_close']:.2f}",
        f"- SMA120: {state_obj['latest_sma120'] if state_obj['latest_sma120'] is not None else 'NA'}",
        f"- trend ON: {state_obj['latest_trend_on']}",
        f"- trend target: {state_obj['latest_trend_target']:.1%}",
        f"- drawdown: {state_obj['latest_drawdown']:.2%}",
        f"- crisis target: {state_obj['latest_crisis_target']:.1%}",
        f"- combined target: {state_obj['latest_combined_target']:.1%}",
        "",
        "## Baseline 10 bps metrics",
        "",
    ]
    if not baseline_metrics.empty:
        lines.append(baseline_metrics.to_markdown(index=False))
    lines += [
        "",
        "This is a forward paper record. Historical bars before inception initialize state only and do not contribute forward P&L.",
    ]
    (outdir / "r009_e002_forward_summary.md").write_text("\n".join(lines), encoding="utf-8")

    print("R009-E002 forward tracker complete")
    print("Status:", state_obj["status"])
    print("Latest closed bar:", state_obj["latest_fully_closed_bar"])
    print("Realized forward days:", state_obj["realized_forward_days"])
    print("Combined target:", f"{state_obj['latest_combined_target']:.1%}")
    print("Outputs:", outdir)


if __name__ == "__main__":
    main()
