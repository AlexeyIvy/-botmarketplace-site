"""R002 frozen SMA120 forward-validation tracker.

Reads daily BTC data, ignores the current incomplete UTC candle, computes the
frozen SMA120 signal from fully closed candles only, and reports historical
context plus post-freeze forward observations without changing parameters.

Research-only. This script does not place trades.
"""

from __future__ import annotations

import argparse
import math
from datetime import datetime, timezone
import pandas as pd

FREEZE_DATE = pd.Timestamp("2026-09-08")
LOOKBACK = 120
FEE = 0.001


def latest_closed_utc_date() -> pd.Timestamp:
    now = datetime.now(timezone.utc)
    today = pd.Timestamp(now.date())
    return today - pd.Timedelta(days=1)


def cagr(equity: pd.Series) -> float | None:
    if len(equity) < 2:
        return None
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    if years <= 0:
        return None
    return float(equity.iloc[-1] ** (1.0 / years) - 1.0)


def max_dd(equity: pd.Series) -> float | None:
    if equity.empty:
        return None
    return float((equity / equity.cummax() - 1.0).min())


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date_utc"])
    df = df.set_index("date").sort_index()
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[~df.index.duplicated(keep="last")]
    df = df.loc[:latest_closed_utc_date()].copy()
    df["ret"] = df["close"].pct_change()
    df["sma120"] = df["close"].rolling(LOOKBACK).mean()
    df["raw_signal"] = (df["close"] > df["sma120"]).astype(float)
    # Signal formed at close t applies to return on t+1.
    df["position"] = df["raw_signal"].shift(1)
    return df


def evaluate(x: pd.DataFrame) -> dict:
    x = x.dropna(subset=["ret", "position"]).copy()
    if x.empty:
        return {"days": 0}
    turnover = x["position"].diff().abs().fillna(0.0)
    strategy_ret = x["position"] * x["ret"] - turnover * FEE
    equity = (1.0 + strategy_ret).cumprod()
    bh = (1.0 + x["ret"]).cumprod()
    return {
        "days": int(len(x)),
        "start": x.index[0].date().isoformat(),
        "end": x.index[-1].date().isoformat(),
        "strategy_return": float(equity.iloc[-1] - 1.0),
        "strategy_cagr": cagr(equity),
        "strategy_max_dd": max_dd(equity),
        "buy_hold_return": float(bh.iloc[-1] - 1.0),
        "buy_hold_cagr": cagr(bh),
        "buy_hold_max_dd": max_dd(bh),
        "exposure": float(x["position"].mean()),
        "exposure_changes": int((turnover > 0).sum()),
        "cost_drag": float((turnover * FEE).sum()),
        "annualized_vol": float(strategy_ret.std() * math.sqrt(365.0)) if len(x) > 1 else None,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="Daily Bybit BTC CSV")
    args = p.parse_args()

    df = load_data(args.csv)
    if df.empty:
        raise SystemExit("No fully closed daily candles found")

    last = df.iloc[-1]
    last_date = df.index[-1]
    print("R002 SMA120 FROZEN FORWARD TRACKER")
    print("Freeze date:", FREEZE_DATE.date())
    print("Latest fully closed UTC candle:", last_date.date())
    print("Close:", round(float(last["close"]), 2))
    print("SMA120:", round(float(last["sma120"]), 2) if pd.notna(last["sma120"]) else None)
    print("Signal for next UTC day:", "LONG BTC" if last["raw_signal"] == 1.0 else "CASH")

    hist = df[df.index < FREEZE_DATE]
    fwd = df[df.index > FREEZE_DATE]

    print("\nHistorical/development context:")
    print(evaluate(hist))

    print("\nForward observations after freeze:")
    print(evaluate(fwd))

    if fwd.empty:
        print("No legitimate post-freeze closed candles yet. Forward clock has started, but there is nothing to score.")


if __name__ == "__main__":
    main()
