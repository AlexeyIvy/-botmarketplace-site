"""R002 survivorship-bias validation on Binance historical subset.

Key integrity rule: Binance monthly archives may contain long flat zero-volume
post-delisting tails. These are NOT economically tradable observations and must
not be treated as live market history. For each symbol we truncate the series at
the last day with positive base or quote volume before computing signals.

Strategies:
- frozen SMA120
- research variant SMA120 + ADX14 > 20

Signal is formed on a fully closed daily candle and applied to the next daily
return. Cost = 10 bps per 0<->1 exposure change, plus a final liquidation cost
if the strategy is long on the final tradable day.
"""

from __future__ import annotations

import argparse
import math
import pandas as pd
import numpy as np

HISTORICAL_SYMBOLS = {
    "SXPUSDT", "EOSUSDT", "BTCSTUSDT", "MATICUSDT", "HNTUSDT",
    "SRMUSDT", "TOMOUSDT", "BTSUSDT", "AUDIOUSDT", "ANTUSDT",
    "GALUSDT", "AERGOUSDT", "FOOTBALLUSDT", "YFIIUSDT",
    "BLUEBIRDUSDT", "RNDRUSDT", "AKROUSDT", "LUNAUSDT",
    "BZRXUSDT", "DODOUSDT", "COCOSUSDT", "FRONTUSDT",
}


def cagr(equity: pd.Series) -> float:
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    if years <= 0 or equity.iloc[-1] <= 0:
        return float("nan")
    return float(equity.iloc[-1] ** (1.0 / years) - 1.0)


def max_drawdown(equity: pd.Series) -> float:
    return float((equity / equity.cummax() - 1.0).min())


def adx_wilder(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    up = high.diff()
    down = -low.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    pdi = 100 * plus_dm.ewm(alpha=1 / n, adjust=False, min_periods=n).mean() / atr
    mdi = 100 * minus_dm.ewm(alpha=1 / n, adjust=False, min_periods=n).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    return dx.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def evaluate(df: pd.DataFrame, raw_signal: pd.Series, valid: pd.Series,
             fee: float) -> dict:
    signal = raw_signal.shift(1)
    usable = valid.shift(1).fillna(False).astype(bool)
    x = pd.DataFrame({"ret": df["ret"], "signal": signal, "usable": usable})
    x = x[x["usable"]].dropna(subset=["ret", "signal"])
    if len(x) < 2:
        raise ValueError("insufficient post-warmup observations")

    turnover = x["signal"].diff().abs().fillna(0.0)
    strategy_ret = x["signal"] * x["ret"] - turnover * fee
    # Conservative forced liquidation at the final tradable close.
    strategy_ret.iloc[-1] -= fee * x["signal"].iloc[-1]

    equity = (1.0 + strategy_ret).cumprod()
    bh_equity = (1.0 + x["ret"]).cumprod()

    return {
        "start": x.index[0].date().isoformat(),
        "end": x.index[-1].date().isoformat(),
        "days": int(len(x)),
        "cagr": cagr(equity),
        "max_dd": max_drawdown(equity),
        "ending_multiple": float(equity.iloc[-1]),
        "buy_hold_cagr": cagr(bh_equity),
        "buy_hold_max_dd": max_drawdown(bh_equity),
        "buy_hold_ending_multiple": float(bh_equity.iloc[-1]),
        "exposure": float(x["signal"].mean()),
        "switches": int((turnover > 0).sum()),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    p.add_argument("--fee", type=float, default=0.001)
    args = p.parse_args()

    raw = pd.read_csv(args.csv)
    raw["date"] = pd.to_datetime(raw["date_utc"])
    for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")

    results = []
    exclusions = []

    for symbol, g in raw.groupby("symbol"):
        g = g.sort_values("date").copy()
        tradable = g[(g["volume"].fillna(0) > 0) | (g["quote_volume"].fillna(0) > 0)]
        if tradable.empty:
            exclusions.append((symbol, "no positive-volume observations"))
            continue

        last_trade = tradable["date"].max()
        g = g[g["date"] <= last_trade].copy()
        if len(g) < 120:
            exclusions.append((symbol, f"only {len(g)} tradable daily rows"))
            continue

        g = g.set_index("date").sort_index()
        g["ret"] = g["close"].pct_change()
        g["sma120"] = g["close"].rolling(120).mean()
        g["adx14"] = adx_wilder(g)

        rules = {
            "SMA120": (
                (g["close"] > g["sma120"]).astype(float),
                g["sma120"].notna(),
            ),
            "SMA120_ADX20": (
                ((g["close"] > g["sma120"]) & (g["adx14"] > 20)).astype(float),
                g["sma120"].notna() & g["adx14"].notna(),
            ),
        }

        for name, (signal, valid) in rules.items():
            try:
                r = evaluate(g, signal, valid, args.fee)
            except ValueError as exc:
                exclusions.append((symbol, f"{name}: {exc}"))
                continue
            r.update({
                "symbol": symbol,
                "group": "historical" if symbol in HISTORICAL_SYMBOLS else "control",
                "strategy": name,
                "last_positive_volume_day": last_trade.date().isoformat(),
            })
            results.append(r)

    out = pd.DataFrame(results)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    for strategy in ["SMA120", "SMA120_ADX20"]:
        print(f"\n=== {strategy} ===")
        s = out[out["strategy"] == strategy].copy()
        s["cagr_improvement"] = s["cagr"] - s["buy_hold_cagr"]
        s["dd_improvement"] = s["max_dd"] - s["buy_hold_max_dd"]
        for group in ["historical", "control"]:
            z = s[s["group"] == group]
            if z.empty:
                continue
            both = ((z["cagr_improvement"] > 0) & (z["dd_improvement"] > 0)).sum()
            print({
                "group": group,
                "assets": len(z),
                "cagr_wins": int((z["cagr_improvement"] > 0).sum()),
                "drawdown_wins": int((z["dd_improvement"] > 0).sum()),
                "both_wins": int(both),
                "median_strategy_cagr": float(z["cagr"].median()),
                "median_buy_hold_cagr": float(z["buy_hold_cagr"].median()),
                "median_strategy_max_dd": float(z["max_dd"].median()),
                "median_buy_hold_max_dd": float(z["buy_hold_max_dd"].median()),
            })

    if exclusions:
        print("\n=== EXCLUSIONS ===")
        for item in exclusions:
            print(item)


if __name__ == "__main__":
    main()
