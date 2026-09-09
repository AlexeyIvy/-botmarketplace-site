"""R002 finalist robustness + diversification + simple ensemble test.

Finalists:
- frozen SMA120
- challenger Donchian 100/50

Pre-specified ensembles:
- 50/50 capital blend
- AND: long only when both are long
- OR: long when either is long

The script uses the same point-in-time historical subset conventions as prior
R002 work: 200-day common warmup, next-day application, dead-tail trimming,
10 bps base cost, and 25% delisting penalty. It also reports late-period,
survivor/non-survivor subgroup, cost, and delisting stress diagnostics.
"""

from __future__ import annotations

import argparse
import json
import math
import numpy as np
import pandas as pd

WARMUP = 200
DAYS_PER_YEAR = 365.25


def clean_input(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["date"] = pd.to_datetime(x["date_utc"], errors="coerce")
    for c in ["high", "low", "close", "volume"]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.dropna(subset=["symbol", "date", "high", "low", "close", "volume"])
    x = x[(x["high"] > 0) & (x["low"] > 0) & (x["close"] > 0)]

    out = []
    for symbol, g in x.groupby("symbol", sort=True):
        g = g.sort_values("date").drop_duplicates("date", keep="last")
        live = g[g["volume"] > 0]
        if live.empty:
            continue
        g = g[g["date"] <= live["date"].max()].copy()
        if int((g["volume"] > 0).sum()) >= WARMUP and len(g) >= WARMUP:
            out.append(g)
    if not out:
        raise ValueError("No symbols survive cleaning")
    return pd.concat(out, ignore_index=True)


def panels(df: pd.DataFrame):
    close = df.pivot(index="date", columns="symbol", values="close").sort_index()
    high = df.pivot(index="date", columns="symbol", values="high").reindex(close.index)
    low = df.pivot(index="date", columns="symbol", values="low").reindex(close.index)
    available = close.notna()
    eligible = (available.cumsum() >= WARMUP) & available
    ret = close.pct_change(fill_method=None)
    sma = close.rolling(120, min_periods=120).mean()
    sma_sig = (close > sma) & eligible

    upper = high.shift(1).rolling(100, min_periods=100).max()
    lower = low.shift(1).rolling(50, min_periods=50).min()
    don = pd.DataFrame(False, index=close.index, columns=close.columns)
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
        don[symbol] = vals
    return close, available, eligible, ret, sma_sig, don


def simulate(close, available, eligible, ret, signal_fraction,
             fee=0.001, delist_penalty=0.25, symbols=None):
    syms = list(close.columns if symbols is None else [s for s in close.columns if s in symbols])
    elig = eligible[syms]
    n = elig.sum(axis=1).replace(0, np.nan)
    desired = signal_fraction[syms].astype(float).mul(1.0 / n, axis=0).fillna(0.0)
    weights = desired.shift(1).fillna(0.0)

    r = (weights * ret[syms].fillna(0.0)).sum(axis=1)
    prev_elig = elig.shift(1).fillna(False).astype(bool)
    disappeared = prev_elig & (~available[syms])
    if delist_penalty:
        r -= weights.where(disappeared, 0.0).sum(axis=1) * delist_penalty

    weights_post = weights.where(available[syms], 0.0)
    turnover = weights_post.diff().abs().sum(axis=1)
    turnover.iloc[0] = weights_post.iloc[0].abs().sum()
    r -= turnover * fee
    exposure = weights_post.sum(axis=1)
    return r, turnover, exposure


def metrics(r, turnover, exposure, start):
    r = r.loc[pd.Timestamp(start):]
    turnover = turnover.loc[r.index]
    exposure = exposure.loc[r.index]
    equity = (1 + r).cumprod()
    years = (equity.index[-1] - equity.index[0]).days / DAYS_PER_YEAR
    cagr = float(equity.iloc[-1] ** (1 / years) - 1)
    dd = equity / equity.cummax() - 1
    annual = (1 + r).groupby(r.index.year).prod() - 1
    rolling_12m = (1 + r).rolling(365, min_periods=365).apply(np.prod, raw=True) - 1
    quarter = (1 + r).groupby([r.index.year, r.index.quarter]).prod() - 1
    month = (1 + r).groupby([r.index.year, r.index.month]).prod() - 1
    underwater = (equity < equity.cummax()).astype(int)
    runs = underwater.groupby((underwater != underwater.shift()).cumsum()).cumsum()
    return {
        "cagr": cagr,
        "max_dd": float(dd.min()),
        "vol": float(r.std() * math.sqrt(365.0)),
        "calmar": float(cagr / abs(dd.min())) if dd.min() < 0 else np.nan,
        "worst_year": float(annual.min()),
        "worst_12m": float(rolling_12m.min()),
        "worst_quarter": float(quarter.min()),
        "worst_month": float(month.min()),
        "turnover": float(turnover.sum()),
        "avg_exposure": float(exposure.mean()),
        "ending_multiple": float(equity.iloc[-1]),
        "max_underwater_days": int(runs.max()),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    p.add_argument("--state-json", default=None,
                   help="Optional subset state JSON with historical_symbols/control_symbols")
    args = p.parse_args()

    clean = clean_input(pd.read_csv(args.csv))
    close, available, eligible, ret, sma, don = panels(clean)
    first = eligible.sum(axis=1) > 0
    start = (first[first].index.min() + pd.Timedelta(days=1)).date().isoformat()

    variants = {
        "SMA120": sma.astype(float),
        "DON100_50": don.astype(float),
        "BLEND50": 0.5 * sma.astype(float) + 0.5 * don.astype(float),
        "AND": (sma & don).astype(float),
        "OR": (sma | don).astype(float),
    }

    mask = eligible
    total = mask.sum().sum()
    print("=== SIGNAL DIVERSIFICATION ===")
    print("daily strategy return correlation:", end=" ")
    rs = simulate(close, available, eligible, ret, variants["SMA120"])[0]
    rd = simulate(close, available, eligible, ret, variants["DON100_50"])[0]
    print(f"{pd.concat([rs, rd], axis=1).loc[start:].corr().iloc[0,1]:.4f}")
    print("both long:", f"{(((sma & don) & mask).sum().sum() / total):.2%}")
    print("both cash:", f"{((((~sma) & (~don)) & mask).sum().sum() / total):.2%}")
    print("SMA only:", f"{(((sma & (~don)) & mask).sum().sum() / total):.2%}")
    print("Donchian only:", f"{((((~sma) & don) & mask).sum().sum() / total):.2%}")

    print("\n=== BASE: 10bps cost, 25% delist penalty ===")
    for name, sf in variants.items():
        r, t, e = simulate(close, available, eligible, ret, sf)
        print(name, metrics(r, t, e, start))

    print("\n=== LATE: from 2023-01-01 ===")
    for name, sf in variants.items():
        r, t, e = simulate(close, available, eligible, ret, sf)
        print(name, metrics(r, t, e, "2023-01-01"))

    print("\n=== COST STRESS ===")
    for fee in [0.0005, 0.0010, 0.0025, 0.0050]:
        print("fee", fee)
        for name, sf in variants.items():
            r, t, e = simulate(close, available, eligible, ret, sf, fee=fee)
            print(name, metrics(r, t, e, start)["cagr"])

    print("\n=== DELIST STRESS ===")
    for penalty in [0.0, 0.10, 0.25, 0.50, 1.00]:
        print("penalty", penalty)
        for name, sf in variants.items():
            r, t, e = simulate(close, available, eligible, ret, sf,
                               delist_penalty=penalty)
            print(name, metrics(r, t, e, start)["cagr"])

    if args.state_json:
        state = json.load(open(args.state_json, "r", encoding="utf-8"))
        groups = {
            "controls": set(state["control_symbols"]),
            "historical_non_survivors": set(state["historical_symbols"]),
        }
        print("\n=== SUBGROUP STRESS ===")
        for group_name, symbols in groups.items():
            print(group_name)
            for name, sf in variants.items():
                r, t, e = simulate(close, available, eligible, ret, sf, symbols=symbols)
                print(name, metrics(r, t, e, start))


if __name__ == "__main__":
    main()
