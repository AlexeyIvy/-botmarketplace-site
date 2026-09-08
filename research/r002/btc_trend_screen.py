"""R002 BTC Trend Following coarse screening.

Research-only. Uses daily BTCUSD close data. Signals are formed from information
available at the prior daily close and applied to the next close-to-close return,
so there is no same-day close look-ahead.

The screen intentionally evaluates a tiny, pre-specified family rather than
optimizing many parameters:
- close > SMA100
- close > SMA200
- 252-day absolute momentum > 0
- SMA50 > SMA200

A fixed transaction-cost sensitivity is applied on changes in exposure.
"""

from __future__ import annotations

import argparse
import math
import pandas as pd
import numpy as np


def cagr(equity: pd.Series) -> float:
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    return float(equity.iloc[-1] ** (1.0 / years) - 1.0)


def max_drawdown(equity: pd.Series) -> float:
    return float((equity / equity.cummax() - 1.0).min())


def evaluate(df: pd.DataFrame, raw_signal: pd.Series, valid: pd.Series,
             start: str, end: str, fee_per_exposure_change: float = 0.001) -> dict:
    signal = raw_signal.shift(1)
    usable = valid.shift(1).fillna(False).astype(bool)

    x = pd.DataFrame({
        "ret": df["ret"],
        "signal": signal,
        "usable": usable,
    })
    x = x[(x.index >= pd.Timestamp(start)) & (x.index <= pd.Timestamp(end))]
    x = x[x["usable"]].dropna(subset=["ret", "signal"])

    turnover = x["signal"].diff().abs().fillna(0.0)
    strategy_ret = x["signal"] * x["ret"] - turnover * fee_per_exposure_change
    equity = (1.0 + strategy_ret).cumprod()

    return {
        "start": x.index[0].date().isoformat(),
        "end": x.index[-1].date().isoformat(),
        "days": int(len(x)),
        "cagr": cagr(equity),
        "max_dd": max_drawdown(equity),
        "annualized_vol": float(strategy_ret.std() * math.sqrt(365.0)),
        "exposure": float(x["signal"].mean()),
        "exposure_changes": int((turnover > 0).sum()),
        "ending_multiple": float(equity.iloc[-1]),
    }


def evaluate_buy_hold(df: pd.DataFrame, start: str, end: str) -> dict:
    x = df.loc[pd.Timestamp(start):pd.Timestamp(end), "ret"].dropna()
    equity = (1.0 + x).cumprod()
    return {
        "start": x.index[0].date().isoformat(),
        "end": x.index[-1].date().isoformat(),
        "days": int(len(x)),
        "cagr": cagr(equity),
        "max_dd": max_drawdown(equity),
        "annualized_vol": float(x.std() * math.sqrt(365.0)),
        "ending_multiple": float(equity.iloc[-1]),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    p.add_argument("--fee", type=float, default=0.001,
                   help="Cost per absolute 0->1 or 1->0 exposure change. Default 10 bps.")
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    df["date"] = pd.to_datetime(df["date_utc"])
    df = df.set_index("date").sort_index()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["ret"] = df["close"].pct_change()

    df["sma50"] = df["close"].rolling(50).mean()
    df["sma100"] = df["close"].rolling(100).mean()
    df["sma200"] = df["close"].rolling(200).mean()
    df["mom252"] = df["close"] / df["close"].shift(252) - 1.0

    rules = {
        "SMA100": ((df["close"] > df["sma100"]).astype(float), df["sma100"].notna()),
        "SMA200": ((df["close"] > df["sma200"]).astype(float), df["sma200"].notna()),
        "MOM252": ((df["mom252"] > 0).astype(float), df["mom252"].notna()),
        "SMA50_GT_SMA200": ((df["sma50"] > df["sma200"]).astype(float),
                            df["sma50"].notna() & df["sma200"].notna()),
    }

    common_start = "2020-05-11"
    common_end = df.index.max().date().isoformat()
    periods = {
        "FULL_COMMON": (common_start, common_end),
        "EARLY": (common_start, "2022-12-31"),
        "LATE": ("2023-01-01", common_end),
    }

    for label, (start, end) in periods.items():
        print("\n===", label, start, "->", end, "===")
        print("BUY_HOLD", evaluate_buy_hold(df, start, end))
        for name, (signal, valid) in rules.items():
            print(name, evaluate(df, signal, valid, start, end, args.fee))


if __name__ == "__main__":
    main()
