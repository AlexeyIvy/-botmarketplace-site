"""R002 point-in-time portfolio diagnostic for the frozen historical subset.

Purpose
-------
Evaluate frozen SMA120 inside a portfolio that only uses information available
at each historical date. This is not a full-market universe backtest; it is a
point-in-time test inside the pre-specified 29-symbol survivorship subset.

Key rules
---------
- Daily close data only.
- A symbol becomes eligible only after 120 observed daily closes.
- Signal = close > SMA120, formed on day t and applied to day t+1 return.
- No knowledge of future delisting is used in signal formation.
- Histories are trimmed after the last day with positive volume to remove dead
  post-delisting archive tails.
- Equal-sleeve portfolio: each currently eligible symbol gets 1/N capital slot;
  if its SMA120 signal is off, that slot stays in cash.
- Transaction costs are charged on absolute target-weight changes.
- Missing next-day data after an eligible day is treated as disappearance; a
  configurable delisting penalty can be charged to any long sleeve.
- Cash return = 0 for this diagnostic.

The script also evaluates a point-in-time equal-weight buy-and-hold comparator.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

LOOKBACK = 120
DAYS_PER_YEAR = 365.25


@dataclass
class Metrics:
    start: str
    end: str
    days: int
    cagr: float
    max_dd: float
    annualized_vol: float
    ending_multiple: float
    turnover: float


def cagr(equity: pd.Series) -> float:
    years = (equity.index[-1] - equity.index[0]).days / DAYS_PER_YEAR
    return float(equity.iloc[-1] ** (1.0 / years) - 1.0)


def max_drawdown(equity: pd.Series) -> float:
    return float((equity / equity.cummax() - 1.0).min())


def clean_input(df: pd.DataFrame) -> pd.DataFrame:
    required = {"symbol", "date_utc", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    x = df.copy()
    x["date"] = pd.to_datetime(x["date_utc"], errors="coerce")
    x["close"] = pd.to_numeric(x["close"], errors="coerce")
    x["volume"] = pd.to_numeric(x["volume"], errors="coerce")
    x = x.dropna(subset=["symbol", "date", "close", "volume"])
    x = x[x["close"] > 0]

    cleaned = []
    for symbol, g in x.groupby("symbol", sort=True):
        g = g.sort_values("date").drop_duplicates("date", keep="last")
        positive = g[g["volume"] > 0]
        if positive.empty:
            continue
        last_live = positive["date"].max()
        g = g[g["date"] <= last_live].copy()

        # Require at least LOOKBACK genuinely traded days. This removes archive
        # artefacts such as BTCST/COCOS dead tails from entering the portfolio.
        if int((g["volume"] > 0).sum()) < LOOKBACK:
            continue
        if len(g) < LOOKBACK:
            continue
        cleaned.append(g)

    if not cleaned:
        raise ValueError("No symbols survived cleaning")

    return pd.concat(cleaned, ignore_index=True)


def build_panels(df: pd.DataFrame):
    close = (
        df.pivot(index="date", columns="symbol", values="close")
        .sort_index()
    )
    available = close.notna()
    history_count = available.cumsum()
    eligible = (history_count >= LOOKBACK) & available
    sma = close.rolling(LOOKBACK, min_periods=LOOKBACK).mean()
    signal = (close > sma) & eligible
    ret = close.pct_change(fill_method=None)
    return close, available, eligible, signal, ret


def simulate(
    close: pd.DataFrame,
    available: pd.DataFrame,
    eligible: pd.DataFrame,
    signal: pd.DataFrame,
    ret: pd.DataFrame,
    fee: float,
    delist_penalty: float,
    use_signal: bool,
) -> Metrics:
    symbols = close.columns
    dates = close.index
    prev_weights = pd.Series(0.0, index=symbols)
    equity = 1.0
    equity_values = []
    daily_returns = []
    total_turnover = 0.0

    first_eligible = eligible.sum(axis=1) > 0
    if not first_eligible.any():
        raise ValueError("No eligible portfolio dates")
    first_signal_date = first_eligible[first_eligible].index.min()

    for i, date in enumerate(dates):
        if i == 0:
            equity_values.append(equity)
            daily_returns.append(0.0)
            continue

        prev_date = dates[i - 1]
        elig_prev = eligible.loc[prev_date]
        n = int(elig_prev.sum())

        if n > 0:
            sleeve = 1.0 / n
            if use_signal:
                desired = signal.loc[prev_date].astype(float) * sleeve
            else:
                desired = elig_prev.astype(float) * sleeve
        else:
            desired = pd.Series(0.0, index=symbols)

        today_ret = ret.loc[date].fillna(0.0)
        portfolio_ret = float((desired * today_ret).sum())

        disappeared = elig_prev & (~available.loc[date])
        if delist_penalty > 0 and disappeared.any():
            portfolio_ret -= float(desired[disappeared].sum()) * delist_penalty

        # Cannot keep holding an instrument with no current row.
        desired = desired.copy()
        desired[~available.loc[date]] = 0.0

        turnover = float((desired - prev_weights).abs().sum())
        total_turnover += turnover
        portfolio_ret -= turnover * fee

        equity *= 1.0 + portfolio_ret
        prev_weights = desired
        equity_values.append(equity)
        daily_returns.append(portfolio_ret)

    equity_series = pd.Series(equity_values, index=dates)
    return_series = pd.Series(daily_returns, index=dates)

    start = first_signal_date + pd.Timedelta(days=1)
    equity_series = equity_series[equity_series.index >= start]
    return_series = return_series[return_series.index >= start]

    return Metrics(
        start=equity_series.index[0].date().isoformat(),
        end=equity_series.index[-1].date().isoformat(),
        days=int(len(equity_series)),
        cagr=cagr(equity_series),
        max_dd=max_drawdown(equity_series),
        annualized_vol=float(return_series.std() * math.sqrt(365.0)),
        ending_multiple=float(equity_series.iloc[-1]),
        turnover=total_turnover,
    )


def fmt(m: Metrics) -> str:
    return (
        f"start={m.start} end={m.end} days={m.days} "
        f"CAGR={m.cagr:.2%} MaxDD={m.max_dd:.2%} "
        f"Vol={m.annualized_vol:.2%} Ending={m.ending_multiple:.3f}x "
        f"Turnover={m.turnover:.2f}"
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="r002_binance_historical_subset_daily.csv")
    p.add_argument("--fee", type=float, default=0.001,
                   help="Cost per absolute portfolio weight change. Default 10 bps.")
    args = p.parse_args()

    raw = pd.read_csv(args.csv)
    clean = clean_input(raw)
    close, available, eligible, signal, ret = build_panels(clean)

    print("Symbols after cleaning:", close.shape[1])
    print("Date range:", close.index.min().date(), "->", close.index.max().date())
    print()

    for penalty in [0.0, 0.10, 0.25, 0.50, 1.00]:
        print(f"=== DELIST PENALTY {penalty:.0%} ===")
        sma = simulate(close, available, eligible, signal, ret, args.fee, penalty, True)
        bh = simulate(close, available, eligible, signal, ret, args.fee, penalty, False)
        print("SMA120     ", fmt(sma))
        print("BUY_HOLD   ", fmt(bh))
        print()

    print("=== COST STRESS, DELIST PENALTY 25% ===")
    for fee in [0.0005, 0.0010, 0.0025, 0.0050]:
        sma = simulate(close, available, eligible, signal, ret, fee, 0.25, True)
        print(f"fee={fee:.2%}", fmt(sma))


if __name__ == "__main__":
    main()
