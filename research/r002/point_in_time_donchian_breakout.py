"""R002 independent trend-following confirmation via Donchian breakouts.

This test is deliberately separate from SMA120. It asks whether a different
trend definition reproduces the same broad behavior in the same point-in-time
historical subset.

Pre-specified family:
- 50-day breakout / 25-day exit
- 100-day breakout / 50-day exit (central candidate)
- 200-day breakout / 100-day exit

Rules:
- Daily OHLCV only.
- Common 200-day eligibility warmup for all variants and the SMA120 comparator.
- Breakout on day t uses only prior highs/lows (channels shifted by one day).
- Signal formed on t is applied to return on t+1.
- Equal sleeve per currently eligible symbol; inactive sleeves stay in cash.
- Dead post-delisting archive tails are trimmed after last positive-volume day.
- 10 bps baseline transaction cost per absolute weight change.
- 25% baseline delisting penalty on any long sleeve that disappears next day.
- No leverage, cash return = 0.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

COMMON_WARMUP = 200
DAYS_PER_YEAR = 365.25


@dataclass
class Metrics:
    start: str
    end: str
    cagr: float
    max_dd: float
    annualized_vol: float
    calmar: float
    ending_multiple: float
    turnover: float


def clean_input(df: pd.DataFrame) -> pd.DataFrame:
    required = {"symbol", "date_utc", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    x = df.copy()
    x["date"] = pd.to_datetime(x["date_utc"], errors="coerce")
    for c in ["high", "low", "close", "volume"]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.dropna(subset=["symbol", "date", "high", "low", "close", "volume"])
    x = x[(x["high"] > 0) & (x["low"] > 0) & (x["close"] > 0)]

    cleaned = []
    for symbol, g in x.groupby("symbol", sort=True):
        g = g.sort_values("date").drop_duplicates("date", keep="last")
        positive = g[g["volume"] > 0]
        if positive.empty:
            continue
        last_live = positive["date"].max()
        g = g[g["date"] <= last_live].copy()
        if int((g["volume"] > 0).sum()) < COMMON_WARMUP:
            continue
        if len(g) < COMMON_WARMUP:
            continue
        cleaned.append(g)

    if not cleaned:
        raise ValueError("No symbols survived cleaning")
    return pd.concat(cleaned, ignore_index=True)


def build_panels(df: pd.DataFrame):
    close = df.pivot(index="date", columns="symbol", values="close").sort_index()
    high = df.pivot(index="date", columns="symbol", values="high").reindex(close.index)
    low = df.pivot(index="date", columns="symbol", values="low").reindex(close.index)
    available = close.notna()
    history_count = available.cumsum()
    eligible = (history_count >= COMMON_WARMUP) & available
    ret = close.pct_change(fill_method=None)
    sma120 = close.rolling(120, min_periods=120).mean()
    sma_signal = (close > sma120) & eligible
    return close, high, low, available, eligible, ret, sma_signal


def donchian_signal(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    eligible: pd.DataFrame,
    entry_lookback: int,
    exit_lookback: int,
) -> pd.DataFrame:
    # Shift by one full day: today's signal never sees today's high/low in the channel.
    upper = high.shift(1).rolling(entry_lookback, min_periods=entry_lookback).max()
    lower = low.shift(1).rolling(exit_lookback, min_periods=exit_lookback).min()
    signal = pd.DataFrame(False, index=close.index, columns=close.columns)

    for symbol in close.columns:
        state = False
        values = []
        for date in close.index:
            if not bool(eligible.at[date, symbol]) or pd.isna(close.at[date, symbol]):
                state = False
            else:
                c = close.at[date, symbol]
                u = upper.at[date, symbol]
                l = lower.at[date, symbol]
                if pd.notna(u) and c > u:
                    state = True
                elif pd.notna(l) and c < l:
                    state = False
            values.append(state)
        signal[symbol] = values
    return signal


def daily_portfolio_returns(
    close: pd.DataFrame,
    available: pd.DataFrame,
    eligible: pd.DataFrame,
    ret: pd.DataFrame,
    signal: pd.DataFrame | None,
    fee: float,
    delist_penalty: float,
) -> tuple[pd.Series, pd.Series]:
    symbols = close.columns
    dates = close.index
    prev_weights = pd.Series(0.0, index=symbols)
    returns = []
    turnovers = []

    for i, date in enumerate(dates):
        if i == 0:
            returns.append(0.0)
            turnovers.append(0.0)
            continue

        prev_date = dates[i - 1]
        elig_prev = eligible.loc[prev_date]
        n = int(elig_prev.sum())

        if n > 0:
            sleeve = 1.0 / n
            if signal is None:
                desired = elig_prev.astype(float) * sleeve
            else:
                desired = signal.loc[prev_date].astype(float) * sleeve
        else:
            desired = pd.Series(0.0, index=symbols)

        portfolio_ret = float((desired * ret.loc[date].fillna(0.0)).sum())

        disappeared = elig_prev & (~available.loc[date])
        if delist_penalty > 0 and disappeared.any():
            portfolio_ret -= float(desired[disappeared].sum()) * delist_penalty

        desired = desired.copy()
        desired[~available.loc[date]] = 0.0
        turnover = float((desired - prev_weights).abs().sum())
        portfolio_ret -= turnover * fee

        prev_weights = desired
        returns.append(portfolio_ret)
        turnovers.append(turnover)

    return pd.Series(returns, index=dates), pd.Series(turnovers, index=dates)


def metrics(r: pd.Series, turnover: pd.Series, start: str) -> Metrics:
    r = r[r.index >= pd.Timestamp(start)]
    turnover = turnover.loc[r.index]
    equity = (1.0 + r).cumprod()
    years = (equity.index[-1] - equity.index[0]).days / DAYS_PER_YEAR
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0)
    max_dd = float((equity / equity.cummax() - 1.0).min())
    vol = float(r.std() * math.sqrt(365.0))
    calmar = cagr / abs(max_dd) if max_dd < 0 else np.nan
    return Metrics(
        start=equity.index[0].date().isoformat(),
        end=equity.index[-1].date().isoformat(),
        cagr=cagr,
        max_dd=max_dd,
        annualized_vol=vol,
        calmar=float(calmar),
        ending_multiple=float(equity.iloc[-1]),
        turnover=float(turnover.sum()),
    )


def fmt(m: Metrics) -> str:
    return (
        f"{m.start} -> {m.end} CAGR={m.cagr:.2%} MaxDD={m.max_dd:.2%} "
        f"Vol={m.annualized_vol:.2%} Calmar={m.calmar:.2f} "
        f"Ending={m.ending_multiple:.3f}x Turnover={m.turnover:.2f}"
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="r002_binance_historical_subset_daily.csv")
    args = p.parse_args()

    raw = pd.read_csv(args.csv)
    clean = clean_input(raw)
    close, high, low, available, eligible, ret, sma120 = build_panels(clean)

    variants = {
        "DON50_25": donchian_signal(high, low, close, eligible, 50, 25),
        "DON100_50": donchian_signal(high, low, close, eligible, 100, 50),
        "DON200_100": donchian_signal(high, low, close, eligible, 200, 100),
        "SMA120": sma120,
    }

    first_date = (eligible.sum(axis=1) > 0)
    start = (first_date[first_date].index.min() + pd.Timedelta(days=1)).date().isoformat()

    print("Symbols after cleaning:", close.shape[1])
    print("Common warmup:", COMMON_WARMUP)
    print("Evaluation start:", start)
    print()

    print("=== BASELINE: fee=10bps, delist penalty=25% ===")
    for name, sig in variants.items():
        r, t = daily_portfolio_returns(close, available, eligible, ret, sig, 0.001, 0.25)
        print(name, fmt(metrics(r, t, start)))
    r, t = daily_portfolio_returns(close, available, eligible, ret, None, 0.001, 0.25)
    print("BUY_HOLD", fmt(metrics(r, t, start)))

    print("\n=== LATE PERIOD FROM 2023-01-01 ===")
    for name, sig in variants.items():
        r, t = daily_portfolio_returns(close, available, eligible, ret, sig, 0.001, 0.25)
        print(name, fmt(metrics(r, t, "2023-01-01")))

    print("\n=== COST STRESS: DON100_50 vs SMA120, delist penalty=25% ===")
    for fee in [0.0005, 0.0010, 0.0025, 0.0050]:
        for name, sig in [("DON100_50", variants["DON100_50"]), ("SMA120", sma120)]:
            r, t = daily_portfolio_returns(close, available, eligible, ret, sig, fee, 0.25)
            print(f"fee={fee:.2%} {name}", fmt(metrics(r, t, start)))
        print()


if __name__ == "__main__":
    main()
