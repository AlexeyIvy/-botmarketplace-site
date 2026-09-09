"""R002.1 cross-asset validation: frozen SMA120 with optional ADX14 filter.

Research-only. Uses the same fixed SMA120 baseline on every asset and tests only
three coarse ADX thresholds (15, 20, 25). No per-asset tuning.
Signals are formed on the prior fully closed daily candle and applied to the
next close-to-close return. Transaction cost is charged on exposure changes.
"""

from __future__ import annotations

import argparse
import math
import numpy as np
import pandas as pd

FEE = 0.001
ADX_N = 14
SMA_N = 120
THRESHOLDS = [None, 15, 20, 25]
COMMON_START = "2022-02-12"
LATE_START = "2023-01-01"


def enrich(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_values("date").copy()
    h, l, c = g["high"], g["low"], g["close"]
    up = h.diff()
    down = -l.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=g.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=g.index)
    tr = pd.concat([(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / ADX_N, adjust=False, min_periods=ADX_N).mean()
    plus_sm = plus_dm.ewm(alpha=1 / ADX_N, adjust=False, min_periods=ADX_N).mean()
    minus_sm = minus_dm.ewm(alpha=1 / ADX_N, adjust=False, min_periods=ADX_N).mean()
    plus_di = 100 * plus_sm / atr
    minus_di = 100 * minus_sm / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    g["adx14"] = dx.ewm(alpha=1 / ADX_N, adjust=False, min_periods=ADX_N).mean()
    g["sma120"] = c.rolling(SMA_N, min_periods=SMA_N).mean()
    g["ret"] = c.pct_change()
    return g


def metrics(g: pd.DataFrame, threshold: int | None, start: str, fee: float) -> dict:
    raw = g["close"] > g["sma120"]
    valid = g["sma120"].notna()
    if threshold is not None:
        raw = raw & (g["adx14"] > threshold)
        valid = valid & g["adx14"].notna()

    signal = raw.astype(float).shift(1)
    usable = valid.shift(1).fillna(False).astype(bool)
    x = pd.DataFrame({"date": g["date"], "ret": g["ret"], "signal": signal})
    x = x[usable & (x["date"] >= pd.Timestamp(start))].dropna()

    turnover = x["signal"].diff().abs().fillna(0.0)
    r = x["signal"] * x["ret"] - turnover * fee
    eq = (1.0 + r).cumprod()
    years = (x["date"].iloc[-1] - x["date"].iloc[0]).days / 365.25
    return {
        "cagr": float(eq.iloc[-1] ** (1.0 / years) - 1.0),
        "max_dd": float((eq / eq.cummax() - 1.0).min()),
        "annualized_vol": float(r.std() * math.sqrt(365.0)),
        "exposure": float(x["signal"].mean()),
        "changes": int((turnover > 0).sum()),
        "ending_multiple": float(eq.iloc[-1]),
        "start": x["date"].iloc[0].date().isoformat(),
        "end": x["date"].iloc[-1].date().isoformat(),
    }


def portfolio(enriched: dict[str, pd.DataFrame], threshold: int | None, start: str, fee: float) -> dict:
    cols = []
    for symbol, g in enriched.items():
        raw = g["close"] > g["sma120"]
        valid = g["sma120"].notna()
        if threshold is not None:
            raw = raw & (g["adx14"] > threshold)
            valid = valid & g["adx14"].notna()
        signal = raw.astype(float).shift(1)
        usable = valid.shift(1).fillna(False).astype(bool)
        x = pd.DataFrame({"date": g["date"], "ret": g["ret"], "signal": signal})
        x = x[usable & (x["date"] >= pd.Timestamp(start))].dropna()
        turnover = x["signal"].diff().abs().fillna(0.0)
        x[symbol] = x["signal"] * x["ret"] - turnover * fee
        cols.append(x.set_index("date")[[symbol]])

    panel = pd.concat(cols, axis=1, join="inner")
    r = panel.mean(axis=1)
    eq = (1.0 + r).cumprod()
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    return {
        "cagr": float(eq.iloc[-1] ** (1.0 / years) - 1.0),
        "max_dd": float((eq / eq.cummax() - 1.0).min()),
        "annualized_vol": float(r.std() * math.sqrt(365.0)),
        "ending_multiple": float(eq.iloc[-1]),
        "start": eq.index[0].date().isoformat(),
        "end": eq.index[-1].date().isoformat(),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    p.add_argument("--fee", type=float, default=FEE)
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    df["date"] = pd.to_datetime(df["date_utc"])
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    enriched = {s: enrich(g) for s, g in df.groupby("symbol")}

    for start_label, start in [("COMMON", COMMON_START), ("LATE", LATE_START)]:
        print(f"\n=== {start_label} from {start} ===")
        for symbol, g in enriched.items():
            print("\n", symbol)
            for th in THRESHOLDS:
                name = "SMA120" if th is None else f"SMA120_ADX_GT_{th}"
                print(name, metrics(g, th, start, args.fee))

        print("\nPORTFOLIO")
        for th in THRESHOLDS:
            name = "SMA120" if th is None else f"SMA120_ADX_GT_{th}"
            print(name, portfolio(enriched, th, start, args.fee))


if __name__ == "__main__":
    main()
