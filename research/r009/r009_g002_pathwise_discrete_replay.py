"""R009-G002 pathwise discrete execution replay v0.1.

Implementation-fidelity diagnostic only. R009 signals are frozen; current Binance
order filters are frozen from R009-G001 and applied counterfactually across the
historical replay.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

VERSION = "0.1"
PROTOCOL = "r009-g002-pathwise-discrete-replay-protocol-v0.1"

BASE_URL = "https://data-api.binance.vision"
KLINES = "/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1d"
DAY_MS = 86_400_000
START_MS = int(pd.Timestamp("2017-07-01", tz="UTC").timestamp() * 1000)
PRIMARY_START = pd.Timestamp("2018-01-01")

SMA_LOOKBACK = 120
TREND_WEIGHT = 0.10
CRISIS_TRANCHE = 0.025
CRISIS_THRESH = (-0.20, -0.35, -0.50, -0.65)
EPS = 1e-12

# Frozen from R009-G001 snapshot on 2026-09-10.
STEP = Decimal("0.00001000")
MIN_QTY = Decimal("0.00001000")
MIN_NOTIONAL = Decimal("5.00000000")

CAPITALS = (200, 250, 500, 1000, 5000, 10000)
FEES = (0.0005, 0.0010, 0.0025, 0.0050)
BASELINE_FEE = 0.0010


def d(x) -> Decimal:
    return Decimal(str(x))


def floor_step(x: Decimal, step: Decimal = STEP) -> Decimal:
    if step <= 0:
        return x
    return (x / step).to_integral_value(rounding=ROUND_DOWN) * step


def get_json(url: str):
    req = Request(url, headers={"User-Agent": "botmarketplace-r009-g002/0.1"})
    with urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_closed_daily() -> pd.DataFrame:
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start = START_MS
    rows = []
    while True:
        qs = urlencode({"symbol": SYMBOL, "interval": INTERVAL, "startTime": start, "limit": 1000})
        obj = get_json(BASE_URL + KLINES + "?" + qs)
        if not isinstance(obj, list):
            raise RuntimeError(f"Unexpected Binance response: {obj}")
        if not obj:
            break
        rows.extend(obj)
        last_open = int(obj[-1][0])
        nxt = last_open + DAY_MS
        if len(obj) < 1000 or nxt >= now_ms:
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
            "date": pd.to_datetime(int(r[0]), unit="ms", utc=True).tz_convert(None).normalize(),
            "close": float(r[4]),
            "open_time_ms": int(r[0]),
            "close_time_ms": close_ms,
        })
    x = pd.DataFrame(parsed).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    if x.empty or (x["close"] <= 0).any():
        raise RuntimeError("No valid closed Binance daily bars")
    return x


def audit_source(x: pd.DataFrame) -> dict:
    gaps = x["date"].diff().dt.days.dropna()
    p = x[x["date"] >= PRIMARY_START]
    pg = p["date"].diff().dt.days.dropna()
    status = "PASS"
    if len(p) < 1000 or (len(pg) and int(pg.max()) > 1):
        status = "DATA_OR_ACCOUNTING_REDESIGN"
    return {
        "status": status,
        "source_base": BASE_URL,
        "endpoint": KLINES,
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "closed_rows": int(len(x)),
        "start": x["date"].iloc[0].date().isoformat(),
        "end": x["date"].iloc[-1].date().isoformat(),
        "primary_start": PRIMARY_START.date().isoformat(),
        "primary_rows": int(len(p)),
        "duplicate_dates": int(x["date"].duplicated().sum()),
        "max_gap_days_all": int(gaps.max()) if len(gaps) else 0,
        "max_gap_days_primary": int(pg.max()) if len(pg) else 0,
        "missing_days_primary": int((pg[pg > 1] - 1).sum()) if len(pg) else 0,
        "frozen_execution_rules": {
            "step_btc": str(STEP),
            "min_qty_btc": str(MIN_QTY),
            "min_notional_usdt": str(MIN_NOTIONAL),
            "source": "R009-G001 snapshot 2026-09-10",
        },
    }


def build_state(x: pd.DataFrame) -> pd.DataFrame:
    s = x[["date", "close"]].copy().set_index("date")
    s["sma120"] = s["close"].rolling(SMA_LOOKBACK, min_periods=SMA_LOOKBACK).mean()
    s["trend_on"] = (s["close"] > s["sma120"]) & s["sma120"].notna()
    s["trend_target"] = np.where(s["trend_on"], TREND_WEIGHT, 0.0)

    peak = float(s["close"].iloc[0])
    sticky = [False] * 4
    dds, levels, crisis, aths = [], [], [], []
    for i, raw in enumerate(s["close"].astype(float)):
        p = float(raw)
        new_ath = (i == 0 or p > peak + EPS)
        if new_ath:
            peak = p
            sticky = [False] * 4
            dd = 0.0
        else:
            dd = p / peak - 1.0
            for j, th in enumerate(CRISIS_THRESH):
                if not sticky[j] and dd <= th + EPS:
                    sticky[j] = True
        level = int(sum(sticky))
        dds.append(dd)
        levels.append(level)
        crisis.append(level * CRISIS_TRANCHE)
        aths.append(bool(new_ath))

    s["drawdown"] = dds
    s["crisis_level"] = levels
    s["crisis_target"] = crisis
    s["combined_target"] = s["trend_target"] + s["crisis_target"]
    s["new_ath"] = aths
    return s


def continuous_reference(price: pd.Series, target: pd.Series, fee: float) -> pd.DataFrame:
    idx = price.index
    w = float(target.iloc[0])
    eq = 1.0 - fee * abs(w)
    rows = [{
        "date": idx[0], "equity": eq, "desired_target": w,
        "pretrade_weight": 0.0, "turnover": abs(w), "fee_cost": fee * abs(w),
    }]
    for i in range(1, len(idx)):
        r = float(price.iloc[i] / price.iloc[i-1] - 1.0)
        gross = 1.0 + w * r
        pre = w * (1.0 + r) / gross if gross > 0 else 0.0
        desired = float(target.iloc[i])
        turn = abs(desired - pre)
        cost = fee * turn
        eq *= gross - cost
        w = desired
        rows.append({
            "date": idx[i], "equity": eq, "desired_target": desired,
            "pretrade_weight": pre, "turnover": turn, "fee_cost": cost,
        })
    return pd.DataFrame(rows).set_index("date")


def discrete_replay(price: pd.Series, target: pd.Series, capital: float, fee: float) -> pd.DataFrame:
    cash = d(capital)
    q = Decimal("0")
    rows = []

    for date, px_raw, target_raw in zip(price.index, price.to_numpy(), target.to_numpy()):
        px = d(px_raw)
        pre_nav = cash + q * px
        if pre_nav <= 0:
            raise RuntimeError(f"Non-positive NAV at {date} capital={capital} fee={fee}")

        desired_w = d(target_raw)
        desired_q = Decimal("0") if desired_w <= 0 else floor_step(desired_w * pre_nav / px)
        old_q = q
        delta_q = desired_q - old_q
        desired_trade_notional = abs(delta_q) * px
        attempted = abs(delta_q) > Decimal("0")
        executable = attempted and abs(delta_q) >= MIN_QTY and desired_trade_notional >= MIN_NOTIONAL
        skipped = attempted and not executable

        execution_fee = Decimal("0")
        executed_notional = Decimal("0")
        if executable:
            executed_notional = desired_trade_notional
            execution_fee = d(fee) * executed_notional
            cash = cash - delta_q * px - execution_fee
            q = desired_q

        post_nav = cash + q * px
        actual_w = (q * px / post_nav) if post_nav > 0 else Decimal("0")
        err_pp = abs(actual_w - desired_w) * Decimal("100")
        dust_exit_blocked = bool(desired_w == 0 and q > 0)

        rows.append({
            "date": date,
            "close": float(px),
            "desired_target": float(desired_w),
            "pretrade_nav_usd": float(pre_nav),
            "desired_rounded_qty_btc": float(desired_q),
            "pretrade_qty_btc": float(old_q),
            "delta_qty_requested_btc": float(delta_q),
            "desired_trade_notional_usd": float(desired_trade_notional),
            "order_attempted": bool(attempted),
            "order_executed": bool(executable),
            "order_skipped": bool(skipped),
            "executed_notional_usd": float(executed_notional),
            "execution_fee_usd": float(execution_fee),
            "posttrade_qty_btc": float(q),
            "cash_usd": float(cash),
            "posttrade_nav_usd": float(post_nav),
            "actual_weight": float(actual_w),
            "absolute_target_error_pp": float(err_pp),
            "dust_exit_blocked": dust_exit_blocked,
            "negative_cash": bool(cash < 0),
        })
    return pd.DataFrame(rows).set_index("date")


def max_drawdown_from_nav(nav: pd.Series, initial: float) -> float:
    s = pd.concat([pd.Series([float(initial)]), nav.reset_index(drop=True)], ignore_index=True)
    return float((s / s.cummax() - 1.0).min())


def summarize(capital: float, fee: float, disc: pd.DataFrame, cont: pd.DataFrame) -> dict:
    disc_mult = float(disc["posttrade_nav_usd"].iloc[-1] / capital)
    cont_mult = float(cont["equity"].iloc[-1])
    attempts = int(disc["order_attempted"].sum())
    executed = int(disc["order_executed"].sum())
    skipped = int(disc["order_skipped"].sum())
    dust = disc[disc["dust_exit_blocked"]]
    return {
        "capital_usd": capital,
        "fee_bps": fee * 10000,
        "observations": int(len(disc)),
        "discrete_ending_multiple": disc_mult,
        "continuous_ending_multiple": cont_mult,
        "ending_multiple_difference": disc_mult - cont_mult,
        "discrete_max_drawdown": max_drawdown_from_nav(disc["posttrade_nav_usd"], capital),
        "continuous_max_drawdown": max_drawdown_from_nav(cont["equity"], 1.0),
        "avg_abs_target_error_pp": float(disc["absolute_target_error_pp"].mean()),
        "p95_abs_target_error_pp": float(disc["absolute_target_error_pp"].quantile(0.95)),
        "max_abs_target_error_pp": float(disc["absolute_target_error_pp"].max()),
        "desired_trade_attempts": attempts,
        "executed_orders": executed,
        "skipped_orders": skipped,
        "skipped_order_share": float(skipped / attempts) if attempts else 0.0,
        "skipped_desired_notional_sum_usd": float(disc.loc[disc["order_skipped"], "desired_trade_notional_usd"].sum()),
        "executed_turnover_notional_usd": float(disc["executed_notional_usd"].sum()),
        "execution_fee_drag_usd": float(disc["execution_fee_usd"].sum()),
        "dust_exit_blocked_days": int(len(dust)),
        "max_dust_weight_pp": float(dust["actual_weight"].max() * 100) if len(dust) else 0.0,
        "negative_cash_days": int(disc["negative_cash"].sum()),
    }


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    bars = fetch_closed_daily()
    audit = audit_source(bars)
    (outdir / "r009_g002_source_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if audit["status"] != "PASS":
        raise RuntimeError(f"Source gate failed: {audit}")

    state = build_state(bars)
    p = state[state.index >= PRIMARY_START].copy()
    p = p[p["sma120"].notna()].copy()
    if len(p) < 1000:
        raise RuntimeError("Primary replay unexpectedly short")
    price = p["close"].astype(float)
    target = p["combined_target"].astype(float)

    metrics = []
    baseline_daily = []
    for fee in FEES:
        cont = continuous_reference(price, target, fee)
        for capital in CAPITALS:
            disc = discrete_replay(price, target, capital, fee)
            metrics.append(summarize(capital, fee, disc, cont))
            if abs(fee - BASELINE_FEE) < 1e-15:
                z = disc.reset_index()
                z.insert(1, "capital_usd", capital)
                z["continuous_equity"] = cont["equity"].to_numpy()
                z["continuous_desired_target"] = cont["desired_target"].to_numpy()
                baseline_daily.append(z)

    m = pd.DataFrame(metrics)
    m.to_csv(outdir / "r009_g002_metrics.csv", index=False)
    pd.concat(baseline_daily, ignore_index=True).to_csv(
        outdir / "r009_g002_daily_baseline_10bps.csv", index=False
    )

    b = m[m["fee_bps"] == 10.0].sort_values("capital_usd")
    hard_error = bool((m["negative_cash_days"] > 0).any())
    status = "DATA_OR_ACCOUNTING_REDESIGN" if hard_error else "DISCRETE_IMPLEMENTATION_ENVELOPE_ESTABLISHED"

    run_state = {
        "status": status,
        "evidence_status": "IMPLEMENTATION_FIDELITY_ONLY_NOT_STRATEGY_PASS",
        "engine_version": VERSION,
        "protocol": PROTOCOL,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "primary_start": p.index[0].date().isoformat(),
        "primary_end": p.index[-1].date().isoformat(),
        "observations": int(len(p)),
        "capital_tiers_usd": list(CAPITALS),
        "fee_grid": list(FEES),
        "frozen_execution_rules": {
            "step_btc": str(STEP),
            "min_qty_btc": str(MIN_QTY),
            "min_notional_usdt": str(MIN_NOTIONAL),
        },
        "baseline_10bps": b.to_dict(orient="records"),
        "hard_accounting_error_negative_cash": hard_error,
        "important_limitation": (
            "Historical Binance filter changes, spread/slippage and market impact are not reconstructed. "
            "G002 measures discrete tracking under the single G001 current-rule snapshot only."
        ),
        "outputs": [
            "r009_g002_run_state.json",
            "r009_g002_source_audit.json",
            "r009_g002_metrics.csv",
            "r009_g002_daily_baseline_10bps.csv",
            "r009_g002_summary.md",
        ],
    }
    (outdir / "r009_g002_run_state.json").write_text(
        json.dumps(run_state, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# R009-G002 Pathwise Discrete Replay v0.1",
        "",
        f"- Status: **{status}**",
        f"- Primary replay: **{p.index[0].date()} -> {p.index[-1].date()}**",
        f"- Observations: **{len(p)}**",
        "- Purpose: implementation tracking fidelity only; not strategy validation.",
        "",
        "## Baseline 10 bps",
        "",
        "| Capital | Ending delta vs continuous | Avg target error (pp) | P95 error (pp) | Skipped share | Dust-exit days |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for r in b.itertuples(index=False):
        lines.append(
            f"| ${r.capital_usd:,.0f} | {r.ending_multiple_difference:+.6f} | "
            f"{r.avg_abs_target_error_pp:.4f} | {r.p95_abs_target_error_pp:.4f} | "
            f"{r.skipped_order_share:.2%} | {r.dust_exit_blocked_days} |"
        )
    lines += [
        "",
        "Interpretation must focus on implementation distortion, not on whether historical R009 P&L looks attractive.",
        "No account tier may be selected by maximizing historical return.",
    ]
    (outdir / "r009_g002_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args()
    main(args.outdir)
