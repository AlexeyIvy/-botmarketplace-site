"""R002 BTC Trend Following robustness screen.

Research-only. Evaluates a small pre-specified neighborhood around the coarse
screen rather than optimizing a large parameter grid.

Checks:
- SMA plateau: 80, 90, 100, 110, 120, 130, 140, 150 days.
- Momentum plateau: 189, 252, 315 days (roughly 9/12/15 months).
- Transaction-cost stress: 5/10/25/50 bps per 0<->1 exposure change.
- Next-day-open execution (signal formed at close t, exposure from open t+1).
- Chronological early/late split. The late period is validation, not pristine
  OOS, because it has already been inspected in prior research.

No leverage, no shorting, no cash yield. Daily BTCUSD Bybit inverse perpetual
OHLC is used as the market proxy.
"""

from __future__ import annotations

import argparse
import math
import pandas as pd


def cagr(equity: pd.Series) -> float:
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    return float(equity.iloc[-1] ** (1.0 / years) - 1.0)


def max_drawdown(equity: pd.Series) -> float:
    return float((equity / equity.cummax() - 1.0).min())


def evaluate(
    df: pd.DataFrame,
    raw_signal: pd.Series,
    valid: pd.Series,
    start: str,
    end: str,
    fee: float,
    execution: str = "close",
) -> dict:
    if execution == "close":
        # Signal observed at close t-1, applied to close(t-1)->close(t).
        ret = df["close_ret"]
        signal = raw_signal.shift(1)
        usable = valid.shift(1).fillna(False).astype(bool)
    elif execution == "next_open":
        # Signal observed at close t-2, trade at open t-1, hold open(t-1)->open(t).
        # This is the correct alignment for next-day-open execution.
        ret = df["open_ret"]
        signal = raw_signal.shift(2)
        usable = valid.shift(2).fillna(False).astype(bool)
    else:
        raise ValueError("execution must be 'close' or 'next_open'")

    x = pd.DataFrame({"ret": ret, "signal": signal, "usable": usable})
    x = x.loc[pd.Timestamp(start):pd.Timestamp(end)]
    x = x[x["usable"]].dropna(subset=["ret", "signal"])

    turnover = x["signal"].diff().abs().fillna(0.0)
    strategy_ret = x["signal"] * x["ret"] - turnover * fee
    equity = (1.0 + strategy_ret).cumprod()
    dd = max_drawdown(equity)
    g = cagr(equity)

    return {
        "start": x.index[0].date().isoformat(),
        "end": x.index[-1].date().isoformat(),
        "days": int(len(x)),
        "cagr": g,
        "max_dd": dd,
        "calmar": g / abs(dd) if dd < 0 else float("nan"),
        "annualized_vol": float(strategy_ret.std() * math.sqrt(365.0)),
        "exposure": float(x["signal"].mean()),
        "exposure_changes": int((turnover > 0).sum()),
        "ending_multiple": float(equity.iloc[-1]),
    }


def evaluate_buy_hold(df: pd.DataFrame, start: str, end: str) -> dict:
    r = df.loc[pd.Timestamp(start):pd.Timestamp(end), "close_ret"].dropna()
    equity = (1.0 + r).cumprod()
    dd = max_drawdown(equity)
    g = cagr(equity)
    return {
        "cagr": g,
        "max_dd": dd,
        "calmar": g / abs(dd),
        "ending_multiple": float(equity.iloc[-1]),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    df["date"] = pd.to_datetime(df["date_utc"])
    df = df.set_index("date").sort_index()
    for col in ("open", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["close_ret"] = df["close"].pct_change()
    df["open_ret"] = df["open"].pct_change()

    sma_windows = [80, 90, 100, 110, 120, 130, 140, 150]
    mom_windows = [189, 252, 315]

    rules = {}
    for n in sma_windows:
        sma = df["close"].rolling(n).mean()
        rules[f"SMA{n}"] = ((df["close"] > sma).astype(float), sma.notna())
    for n in mom_windows:
        mom = df["close"] / df["close"].shift(n) - 1.0
        rules[f"MOM{n}"] = ((mom > 0).astype(float), mom.notna())

    # Common start makes all 315-day momentum observations available.
    common_start = "2020-07-12"
    common_end = df.index.max().date().isoformat()
    early = (common_start, "2022-12-31")
    late = ("2023-01-01", common_end)

    print("=== BUY & HOLD ===")
    print("FULL", evaluate_buy_hold(df, common_start, common_end))
    print("EARLY", evaluate_buy_hold(df, *early))
    print("LATE", evaluate_buy_hold(df, *late))

    print("\n=== 10 BPS, CLOSE EXECUTION, CHRONOLOGICAL SPLIT ===")
    for name, (signal, valid) in rules.items():
        print(name)
        print("  FULL ", evaluate(df, signal, valid, common_start, common_end, 0.001))
        print("  EARLY", evaluate(df, signal, valid, *early, 0.001))
        print("  LATE ", evaluate(df, signal, valid, *late, 0.001))

    print("\n=== COST STRESS, FULL PERIOD ===")
    for name, (signal, valid) in rules.items():
        for bps in (5, 10, 25, 50):
            result = evaluate(df, signal, valid, common_start, common_end, bps / 10000.0)
            print(name, bps, result)

    print("\n=== NEXT-DAY-OPEN EXECUTION, 10 BPS ===")
    for name, (signal, valid) in rules.items():
        result = evaluate(
            df, signal, valid, common_start, common_end, 0.001, execution="next_open"
        )
        print(name, result)


if __name__ == "__main__":
    main()
