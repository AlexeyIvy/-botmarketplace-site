"""R002 cross-asset validation for frozen SMA120 rule.

Applies the same long/cash SMA120 rule to a fixed panel of Bybit linear USDT
perpetuals without per-asset tuning. Signals are formed from a fully closed daily
bar and applied to the following close-to-close return. Transaction costs are
charged on changes in exposure.

Research-only. This panel is survivorship-biased because it uses large current
assets; it is a cross-market robustness test, not a point-in-time universe test.
"""

from __future__ import annotations

import argparse
import math
import pandas as pd

LOOKBACK = 120
DEFAULT_FEE = 0.001
COMMON_START = "2022-02-12"
LATE_START = "2023-01-01"


def cagr(ret: pd.Series) -> float:
    ret = ret.dropna()
    eq = (1.0 + ret).cumprod()
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    return float(eq.iloc[-1] ** (1.0 / years) - 1.0)


def max_dd(ret: pd.Series) -> float:
    eq = (1.0 + ret.dropna()).cumprod()
    return float((eq / eq.cummax() - 1.0).min())


def ann_vol(ret: pd.Series) -> float:
    return float(ret.dropna().std() * math.sqrt(365.0))


def prepare(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_index().copy()
    g["ret"] = g["close"].pct_change()
    g["sma120"] = g["close"].rolling(LOOKBACK).mean()
    g["raw_signal"] = (g["close"] > g["sma120"]).astype(float)
    g["signal"] = g["raw_signal"].shift(1)
    g["usable"] = g["sma120"].notna().shift(1).fillna(False).astype(bool)
    return g


def strategy_returns(g: pd.DataFrame, fee: float, start: str | None = None) -> pd.Series:
    x = g[g["usable"]].dropna(subset=["ret", "signal"]).copy()
    if start:
        x = x[x.index >= pd.Timestamp(start)]
    turnover = x["signal"].diff().abs()
    if len(x):
        turnover.iloc[0] = abs(x["signal"].iloc[0])
    turnover = turnover.fillna(0.0)
    return x["signal"] * x["ret"] - turnover * fee


def buy_hold_returns(g: pd.DataFrame, start: str | None = None) -> pd.Series:
    r = g["ret"].dropna().copy()
    if start:
        r = r[r.index >= pd.Timestamp(start)]
    return r


def summarize(ret: pd.Series) -> dict:
    ret = ret.dropna()
    return {
        "start": ret.index[0].date().isoformat(),
        "end": ret.index[-1].date().isoformat(),
        "cagr": cagr(ret),
        "max_dd": max_dd(ret),
        "ann_vol": ann_vol(ret),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    p.add_argument("--fee", type=float, default=DEFAULT_FEE)
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    df["date"] = pd.to_datetime(df["date_utc"])
    for c in ["open", "high", "low", "close", "volume", "turnover"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    prepared = {
        sym: prepare(g.set_index("date"))
        for sym, g in df.groupby("symbol")
    }

    print("=== PER-ASSET MAX AVAILABLE HISTORY ===")
    for sym, g in sorted(prepared.items()):
        sr = strategy_returns(g, args.fee)
        bh = buy_hold_returns(g, sr.index[0].date().isoformat())
        print(sym, "SMA120", summarize(sr), "BUY_HOLD", summarize(bh))

    print("\n=== COMMON PERIOD ===")
    strategy_panel = {}
    bh_panel = {}
    for sym, g in sorted(prepared.items()):
        sr = strategy_returns(g, args.fee, COMMON_START)
        bh = buy_hold_returns(g, COMMON_START)
        strategy_panel[sym] = sr
        bh_panel[sym] = bh
        print(sym, "SMA120", summarize(sr), "BUY_HOLD", summarize(bh))

    s = pd.concat(strategy_panel, axis=1).dropna().mean(axis=1)
    b = pd.concat(bh_panel, axis=1).dropna().mean(axis=1)
    print("COMMON_EQUAL_WEIGHT_SMA120", summarize(s))
    print("COMMON_EQUAL_WEIGHT_BUY_HOLD", summarize(b))

    print("\n=== LATE PERIOD 2023+ ===")
    late_s = {}
    late_b = {}
    for sym, g in sorted(prepared.items()):
        late_s[sym] = strategy_returns(g, args.fee, LATE_START)
        late_b[sym] = buy_hold_returns(g, LATE_START)
    s2 = pd.concat(late_s, axis=1).dropna().mean(axis=1)
    b2 = pd.concat(late_b, axis=1).dropna().mean(axis=1)
    print("LATE_EQUAL_WEIGHT_SMA120", summarize(s2))
    print("LATE_EQUAL_WEIGHT_BUY_HOLD", summarize(b2))

    print("\n=== COMMON PERIOD COST STRESS ===")
    for fee in [0.0005, 0.0010, 0.0025, 0.0050]:
        panel = {
            sym: strategy_returns(g, fee, COMMON_START)
            for sym, g in sorted(prepared.items())
        }
        r = pd.concat(panel, axis=1).dropna().mean(axis=1)
        print("fee", fee, summarize(r))


if __name__ == "__main__":
    main()
