"""R002.2 point-in-time volatility targeting diagnostic.

Applies the frozen SMA120 signal inside the existing point-in-time historical
subset portfolio and scales each active sleeve by recent realised volatility.

Primary pre-specified targets: 15%, 20%, 25%, 30% annualised volatility.
Estimator: 20-day realised volatility from daily close-to-close returns.
No leverage: scale = min(1, target_vol / RV20).
Signal and volatility estimate formed on day t, applied to day t+1 return.

This is a diagnostic branch; it does not modify frozen R002 SMA120 v1.0.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

LOOKBACK = 120
VOL_LOOKBACK = 20
DAYS_PER_YEAR = 365.25
TARGETS = [0.15, 0.20, 0.25, 0.30]


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
    avg_exposure: float
    calmar: float
    worst_year: float


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
        if int((g["volume"] > 0).sum()) < LOOKBACK:
            continue
        if len(g) < LOOKBACK:
            continue
        cleaned.append(g)

    if not cleaned:
        raise ValueError("No symbols survived cleaning")
    return pd.concat(cleaned, ignore_index=True)


def build_panels(df: pd.DataFrame):
    close = df.pivot(index="date", columns="symbol", values="close").sort_index()
    available = close.notna()
    history_count = available.cumsum()
    eligible = (history_count >= LOOKBACK) & available
    sma = close.rolling(LOOKBACK, min_periods=LOOKBACK).mean()
    signal = (close > sma) & eligible
    ret = close.pct_change(fill_method=None)
    rv20 = ret.rolling(VOL_LOOKBACK, min_periods=VOL_LOOKBACK).std() * math.sqrt(365.0)
    return close, available, eligible, signal, ret, rv20


def simulate(
    close: pd.DataFrame,
    available: pd.DataFrame,
    eligible: pd.DataFrame,
    signal: pd.DataFrame,
    ret: pd.DataFrame,
    rv20: pd.DataFrame,
    fee: float,
    delist_penalty: float,
    target_vol: float | None,
) -> tuple[Metrics, pd.Series]:
    symbols = close.columns
    dates = close.index
    prev_weights = pd.Series(0.0, index=symbols)
    equity = 1.0
    equity_values = []
    daily_returns = []
    exposures = []
    total_turnover = 0.0

    first_eligible = eligible.sum(axis=1) > 0
    if not first_eligible.any():
        raise ValueError("No eligible portfolio dates")
    first_signal_date = first_eligible[first_eligible].index.min()

    for i, date in enumerate(dates):
        if i == 0:
            equity_values.append(equity)
            daily_returns.append(0.0)
            exposures.append(0.0)
            continue

        prev_date = dates[i - 1]
        elig_prev = eligible.loc[prev_date]
        n = int(elig_prev.sum())

        if n > 0:
            sleeve = 1.0 / n
            desired = signal.loc[prev_date].astype(float) * sleeve
            if target_vol is not None:
                scale = (target_vol / rv20.loc[prev_date]).clip(upper=1.0)
                scale = scale.replace([np.inf, -np.inf], np.nan).fillna(0.0)
                desired = desired * scale
        else:
            desired = pd.Series(0.0, index=symbols)

        today_ret = ret.loc[date].fillna(0.0)
        portfolio_ret = float((desired * today_ret).sum())

        disappeared = elig_prev & (~available.loc[date])
        if delist_penalty > 0 and disappeared.any():
            portfolio_ret -= float(desired[disappeared].sum()) * delist_penalty

        desired = desired.copy()
        desired[~available.loc[date]] = 0.0

        turnover = float((desired - prev_weights).abs().sum())
        total_turnover += turnover
        portfolio_ret -= turnover * fee

        equity *= 1.0 + portfolio_ret
        prev_weights = desired
        equity_values.append(equity)
        daily_returns.append(portfolio_ret)
        exposures.append(float(desired.sum()))

    equity_series = pd.Series(equity_values, index=dates)
    return_series = pd.Series(daily_returns, index=dates)
    exposure_series = pd.Series(exposures, index=dates)

    start = first_signal_date + pd.Timedelta(days=1)
    equity_series = equity_series[equity_series.index >= start]
    return_series = return_series[return_series.index >= start]
    exposure_series = exposure_series[exposure_series.index >= start]

    cg = cagr(equity_series)
    dd = max_drawdown(equity_series)
    annual = (1.0 + return_series).groupby(return_series.index.year).prod() - 1.0

    metrics = Metrics(
        start=equity_series.index[0].date().isoformat(),
        end=equity_series.index[-1].date().isoformat(),
        days=int(len(equity_series)),
        cagr=cg,
        max_dd=dd,
        annualized_vol=float(return_series.std() * math.sqrt(365.0)),
        ending_multiple=float(equity_series.iloc[-1]),
        turnover=total_turnover,
        avg_exposure=float(exposure_series.mean()),
        calmar=float(cg / abs(dd)) if dd < 0 else float("nan"),
        worst_year=float(annual.min()),
    )
    return metrics, return_series


def fmt(label: str, m: Metrics) -> str:
    return (
        f"{label:10s} CAGR={m.cagr:.2%} MaxDD={m.max_dd:.2%} "
        f"Vol={m.annualized_vol:.2%} Calmar={m.calmar:.2f} "
        f"AvgExp={m.avg_exposure:.2%} WorstYear={m.worst_year:.2%} "
        f"Ending={m.ending_multiple:.3f}x Turnover={m.turnover:.2f}"
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="r002_binance_historical_subset_daily.csv")
    p.add_argument("--fee", type=float, default=0.001,
                   help="Cost per absolute portfolio weight change. Default 10 bps.")
    p.add_argument("--delist-penalty", type=float, default=0.25,
                   help="Penalty on disappearing long sleeve. Default 25%%.")
    args = p.parse_args()

    raw = pd.read_csv(args.csv)
    clean = clean_input(raw)
    close, available, eligible, signal, ret, rv20 = build_panels(clean)

    print("Symbols after cleaning:", close.shape[1])
    print("Date range:", close.index.min().date(), "->", close.index.max().date())
    print("RV estimator:", VOL_LOOKBACK, "days")
    print("Fee:", f"{args.fee:.2%}")
    print("Delist penalty:", f"{args.delist_penalty:.0%}")
    print()

    base, _ = simulate(close, available, eligible, signal, ret, rv20,
                       args.fee, args.delist_penalty, None)
    print(fmt("SMA120", base))
    for target in TARGETS:
        m, _ = simulate(close, available, eligible, signal, ret, rv20,
                        args.fee, args.delist_penalty, target)
        print(fmt(f"VT{target:.0%}", m))


if __name__ == "__main__":
    main()
