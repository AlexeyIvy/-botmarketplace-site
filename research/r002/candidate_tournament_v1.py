"""R002 unified candidate tournament on the point-in-time historical subset.

Compares the pre-specified candidates on one common 200-day warmup and the same
portfolio/execution assumptions:
- frozen SMA120
- SMA120 + ADX14 > 20 (R002.1)
- Donchian 100/50 (independent trend challenger)
- SMA120 + RV20 volatility targeting at 30% (R002.2 reference)

Baseline assumptions:
- signal on t, return on t+1
- equal sleeve per currently eligible symbol
- cash return 0
- 10 bps cost per absolute weight change
- 25% penalty on a disappearing long sleeve
- dead post-delisting archive tails trimmed after the last positive-volume day
- no leverage

The script reports full-period, late-period, transaction-cost stress, and
Delisting-penalty stress. It does not tune parameters.
"""

from __future__ import annotations

import argparse
import math
import numpy as np
import pandas as pd

WARMUP = 200
SMA_N = 120
ADX_N = 14
ADX_THRESHOLD = 20
VOL_LOOKBACK = 20
VT_TARGET = 0.30
DAYS_PER_YEAR = 365.25


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
        g = g[g["date"] <= positive["date"].max()].copy()
        if int((g["volume"] > 0).sum()) < WARMUP or len(g) < WARMUP:
            continue
        cleaned.append(g)
    if not cleaned:
        raise ValueError("No symbols survived cleaning")
    return pd.concat(cleaned, ignore_index=True)


def adx14_panel(df: pd.DataFrame, dates: pd.Index, symbols: pd.Index) -> pd.DataFrame:
    out = pd.DataFrame(index=dates, columns=symbols, dtype=float)
    for symbol, g in df.groupby("symbol"):
        g = g.sort_values("date").set_index("date")
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
        adx = dx.ewm(alpha=1 / ADX_N, adjust=False, min_periods=ADX_N).mean()
        out.loc[adx.index, symbol] = adx.values
    return out


def donchian_signal(high, low, close, eligible, entry=100, exit_=50):
    upper = high.shift(1).rolling(entry, min_periods=entry).max()
    lower = low.shift(1).rolling(exit_, min_periods=exit_).min()
    signal = pd.DataFrame(False, index=close.index, columns=close.columns)
    for symbol in close.columns:
        state = False
        vals = []
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
            vals.append(state)
        signal[symbol] = vals
    return signal


def build(df: pd.DataFrame):
    close = df.pivot(index="date", columns="symbol", values="close").sort_index()
    high = df.pivot(index="date", columns="symbol", values="high").reindex(close.index)
    low = df.pivot(index="date", columns="symbol", values="low").reindex(close.index)
    available = close.notna()
    eligible = (available.cumsum() >= WARMUP) & available
    ret = close.pct_change(fill_method=None)
    sma = close.rolling(SMA_N, min_periods=SMA_N).mean()
    sma_sig = (close > sma) & eligible
    adx = adx14_panel(df, close.index, close.columns)
    adx_sig = (close > sma) & (adx > ADX_THRESHOLD) & eligible
    don_sig = donchian_signal(high, low, close, eligible)
    rv20 = ret.rolling(VOL_LOOKBACK, min_periods=VOL_LOOKBACK).std() * math.sqrt(365.0)
    vt_scale = (VT_TARGET / rv20).clip(upper=1.0)
    return close, available, eligible, ret, {
        "SMA120": (sma_sig, None),
        "SMA120_ADX20": (adx_sig, None),
        "DON100_50": (don_sig, None),
        "SMA120_VT30": (sma_sig, vt_scale),
    }


def simulate(close, available, eligible, ret, signal, scale, fee, delist_penalty):
    symbols = close.columns
    dates = close.index
    prev = pd.Series(0.0, index=symbols)
    rows = []
    for i, date in enumerate(dates):
        if i == 0:
            rows.append((date, 0.0, 0.0, 0.0))
            continue
        prev_date = dates[i - 1]
        elig = eligible.loc[prev_date]
        n = int(elig.sum())
        if n > 0:
            desired = signal.loc[prev_date].astype(float) / n
            if scale is not None:
                sc = scale.loc[prev_date].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(0.0, 1.0)
                desired = desired * sc
        else:
            desired = pd.Series(0.0, index=symbols)

        pr = float((desired * ret.loc[date].fillna(0.0)).sum())
        disappeared = elig & (~available.loc[date])
        if delist_penalty > 0 and disappeared.any():
            pr -= float(desired[disappeared].sum()) * delist_penalty
        desired = desired.copy()
        desired[~available.loc[date]] = 0.0
        turnover = float((desired - prev).abs().sum())
        pr -= turnover * fee
        prev = desired
        rows.append((date, pr, turnover, float(desired.sum())))
    return pd.DataFrame(rows, columns=["date", "ret", "turnover", "exposure"]).set_index("date")


def metrics(res: pd.DataFrame, common_start: pd.Timestamp, start: str | None = None) -> dict:
    st = common_start if start is None else max(common_start, pd.Timestamp(start))
    z = res[res.index >= st]
    eq = (1 + z["ret"]).cumprod()
    years = (eq.index[-1] - eq.index[0]).days / DAYS_PER_YEAR
    cagr = float(eq.iloc[-1] ** (1 / years) - 1)
    dd = float((eq / eq.cummax() - 1).min())
    vol = float(z["ret"].std() * math.sqrt(365.0))
    annual = (1 + z["ret"]).groupby(z.index.year).prod() - 1
    sharpe = float(z["ret"].mean() / z["ret"].std() * math.sqrt(365.0)) if z["ret"].std() > 0 else np.nan
    return {
        "start": eq.index[0].date().isoformat(),
        "end": eq.index[-1].date().isoformat(),
        "cagr": cagr,
        "max_dd": dd,
        "vol": vol,
        "calmar": cagr / abs(dd) if dd < 0 else np.nan,
        "sharpe": sharpe,
        "worst_year": float(annual.min()),
        "turnover": float(z["turnover"].sum()),
        "avg_exposure": float(z["exposure"].mean()),
        "ending_multiple": float(eq.iloc[-1]),
    }


def fmt(name, m):
    return (f"{name:13s} CAGR={m['cagr']:.2%} MaxDD={m['max_dd']:.2%} "
            f"Vol={m['vol']:.2%} Calmar={m['calmar']:.2f} Sharpe={m['sharpe']:.2f} "
            f"WorstYear={m['worst_year']:.2%} Turnover={m['turnover']:.2f} "
            f"AvgExp={m['avg_exposure']:.2%} Ending={m['ending_multiple']:.3f}x")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    args = p.parse_args()
    df = clean_input(pd.read_csv(args.csv))
    close, available, eligible, ret, candidates = build(df)
    first = eligible.sum(axis=1) > 0
    common_start = first[first].index.min() + pd.Timedelta(days=1)

    print("Symbols:", close.shape[1])
    print("Common start:", common_start.date())
    print("Baseline fee=10bps, delist penalty=25%")
    print("\n=== FULL PERIOD ===")
    for name, (sig, scale) in candidates.items():
        r = simulate(close, available, eligible, ret, sig, scale, 0.001, 0.25)
        print(fmt(name, metrics(r, common_start)))

    print("\n=== LATE PERIOD FROM 2023-01-01 ===")
    for name, (sig, scale) in candidates.items():
        r = simulate(close, available, eligible, ret, sig, scale, 0.001, 0.25)
        print(fmt(name, metrics(r, common_start, "2023-01-01")))

    print("\n=== COST STRESS (delist penalty 25%) ===")
    for fee in [0.0005, 0.0010, 0.0025, 0.0050]:
        print(f"fee={fee:.2%}")
        for name, (sig, scale) in candidates.items():
            r = simulate(close, available, eligible, ret, sig, scale, fee, 0.25)
            print(fmt(name, metrics(r, common_start)))

    print("\n=== DELIST PENALTY STRESS (fee 10bps) ===")
    for penalty in [0.0, 0.25, 0.50, 1.00]:
        print(f"penalty={penalty:.0%}")
        for name, (sig, scale) in candidates.items():
            r = simulate(close, available, eligible, ret, sig, scale, 0.001, penalty)
            print(fmt(name, metrics(r, common_start)))


if __name__ == "__main__":
    main()
