"""R002 wide-universe point-in-time finalist validation engine v0.1.

Frozen finalists only:
- SMA120: long when close > SMA120.
- Donchian 100/50: enter above prior 100-observed-bar high, exit below
  prior 50-observed-bar low.

Research contract:
- Full archive-defined Binance USD-M universe as supplied in the input CSV.
- No future-lifetime/current-survivor filter for strategy eligibility.
- Common 200 observed-bar warmup.
- Signal at close t is applied to the next calendar-day portfolio return; for
  instruments with internal non-trading gaps, the signal is carried and the
  next observed close-to-close return is booked when it arrives.
- Equal sleeve across all currently eligible instruments; signal-off sleeves
  remain cash.
- Point-in-time passive equal-sleeve comparator under identical eligibility.
- Cost grid: 5/10/25/50 bps.
- Disappearance penalty grid: 0/25/50/100%.
- Baseline: 10 bps + 25% disappearance penalty.
- No parameter tuning or extra indicators.

The engine writes reproducible CSV/JSON/Markdown outputs, including late-period,
breadth, yearly-return and concentration diagnostics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

VERSION = "0.1"
COMMON_WARMUP = 200
SMA_LOOKBACK = 120
DON_ENTRY = 100
DON_EXIT = 50
DAYS_PER_YEAR = 365.25
VOL_DAYS_PER_YEAR = 365.0
EXPECTED_SYMBOLS = 864
EXPECTED_ROWS = 637_705
BASELINE_FEE = 0.0010
BASELINE_PENALTY = 0.25
FEE_GRID = (0.0005, 0.0010, 0.0025, 0.0050)
PENALTY_GRID = (0.0, 0.25, 0.50, 1.00)
LATE_START = pd.Timestamp("2023-01-01")


@dataclass
class MetricRow:
    strategy: str
    slice: str
    fee_bps: float
    disappearance_penalty: float
    start: str
    end: str
    days: int
    cagr: float
    max_drawdown: float
    annualized_vol: float
    calmar: float
    ending_multiple: float
    turnover: float
    average_gross_exposure: float
    average_cash_fraction: float
    worst_calendar_year: float
    worst_calendar_year_label: str
    worst_calendar_quarter: float
    worst_calendar_quarter_label: str
    worst_month: float
    worst_month_label: str
    worst_rolling_12m: float
    longest_drawdown_days: int
    average_eligible_assets: float
    median_eligible_assets: float
    average_active_assets: float
    median_active_assets: float


@dataclass
class Precomputed:
    name: str
    gross_return: pd.Series
    disappearance_exposure: pd.Series
    turnover: pd.Series
    gross_exposure: pd.Series
    active_count: pd.Series


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def pct(x: float) -> str:
    return "nan" if pd.isna(x) else f"{x:.2%}"


def load_and_validate(path: Path, strict_known_invariants: bool) -> tuple[pd.DataFrame, dict]:
    usecols = [
        "symbol", "date_utc", "open", "high", "low", "close", "volume",
        "source_month",
    ]
    df = pd.read_csv(path, usecols=usecols, low_memory=False)

    raw_rows = len(df)
    raw_symbols = int(df["symbol"].nunique(dropna=True))

    if strict_known_invariants:
        if raw_rows != EXPECTED_ROWS:
            raise ValueError(f"Expected {EXPECTED_ROWS} rows, found {raw_rows}")
        if raw_symbols != EXPECTED_SYMBOLS:
            raise ValueError(f"Expected {EXPECTED_SYMBOLS} symbols, found {raw_symbols}")

    df["date"] = pd.to_datetime(df["date_utc"], errors="coerce")
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    core = ["symbol", "date", "open", "high", "low", "close", "volume"]
    missing_core = int(df[core].isna().any(axis=1).sum())
    duplicate_symbol_date = int(df.duplicated(["symbol", "date"]).sum())
    nonpositive_prices = int(
        ((df[["open", "high", "low", "close"]] <= 0).any(axis=1)).sum()
    )
    negative_volume = int((df["volume"] < 0).sum())
    invalid_ohlc = int(
        (
            (df["high"] < df[["open", "close", "low"]].max(axis=1))
            | (df["low"] > df[["open", "close", "high"]].min(axis=1))
        ).sum()
    )

    if missing_core:
        raise ValueError(f"Core OHLCV/date corruption: {missing_core} rows")
    if duplicate_symbol_date:
        raise ValueError(f"Duplicate symbol+date rows: {duplicate_symbol_date}")
    if nonpositive_prices:
        raise ValueError(f"Non-positive OHLC rows: {nonpositive_prices}")
    if negative_volume:
        raise ValueError(f"Negative-volume rows: {negative_volume}")
    if invalid_ohlc:
        raise ValueError(f"Invalid OHLC relationships: {invalid_ohlc}")

    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    meta = {
        "raw_rows": raw_rows,
        "raw_symbols": raw_symbols,
        "raw_start": df["date"].min().date().isoformat(),
        "raw_end": df["date"].max().date().isoformat(),
        "duplicate_symbol_date": duplicate_symbol_date,
        "missing_core_rows": missing_core,
        "nonpositive_price_rows": nonpositive_prices,
        "negative_volume_rows": negative_volume,
        "invalid_ohlc_rows": invalid_ohlc,
    }
    return df, meta


def prepare_long(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Trim dead tails and compute observed-bar signals without future filters."""
    latest_source_month = str(df["source_month"].dropna().astype(str).max())
    global_end = df["date"].max()

    chunks: list[pd.DataFrame] = []
    meta_rows: list[dict] = []

    for symbol, g0 in df.groupby("symbol", sort=True):
        g = g0.sort_values("date").drop_duplicates("date", keep="last").copy()
        positive = g[g["volume"] > 0]
        if positive.empty:
            meta_rows.append({
                "symbol": symbol,
                "first_date": g["date"].min(),
                "last_live_date": pd.NaT,
                "alive_end_date": pd.NaT,
                "observed_bars_after_trim": 0,
                "positive_volume_bars": 0,
                "eligibility_date": pd.NaT,
                "latest_source_month": str(g["source_month"].astype(str).max()),
                "archive_survivor": False,
            })
            continue

        last_live = positive["date"].max()
        g = g[g["date"] <= last_live].copy()
        if g.empty:
            continue

        source_latest = str(g["source_month"].dropna().astype(str).max())
        archive_survivor = source_latest == latest_source_month

        # Right-censor latest archive-month instruments at the dataset boundary:
        # absence of a later archive cannot be treated as a known disappearance.
        # This affects only the terminal disappearance event, not the 200-bar
        # eligibility clock or any signal calculation.
        alive_end = global_end if archive_survivor else last_live

        g["obs_n"] = np.arange(1, len(g) + 1, dtype=np.int32)
        g["eligible_obs"] = g["obs_n"] >= COMMON_WARMUP
        g["ret_obs"] = g["close"].pct_change(fill_method=None).fillna(0.0)

        sma = g["close"].rolling(SMA_LOOKBACK, min_periods=SMA_LOOKBACK).mean()
        g["sma_signal_obs"] = (g["close"] > sma) & g["eligible_obs"]

        upper = (
            g["high"].shift(1).rolling(DON_ENTRY, min_periods=DON_ENTRY).max()
        )
        lower = (
            g["low"].shift(1).rolling(DON_EXIT, min_periods=DON_EXIT).min()
        )
        state = False
        don_values: list[bool] = []
        for eligible_now, c, u, l in zip(
            g["eligible_obs"].to_numpy(),
            g["close"].to_numpy(),
            upper.to_numpy(),
            lower.to_numpy(),
        ):
            if not bool(eligible_now):
                state = False
            else:
                if not np.isnan(u) and c > u:
                    state = True
                elif not np.isnan(l) and c < l:
                    state = False
            don_values.append(state)
        g["don_signal_obs"] = np.asarray(don_values, dtype=bool)

        eligibility_date = (
            g.loc[g["obs_n"] == COMMON_WARMUP, "date"].iloc[0]
            if len(g) >= COMMON_WARMUP
            else pd.NaT
        )

        meta_rows.append({
            "symbol": symbol,
            "first_date": g["date"].min(),
            "last_live_date": last_live,
            "alive_end_date": alive_end,
            "observed_bars_after_trim": int(len(g)),
            "positive_volume_bars": int((g["volume"] > 0).sum()),
            "eligibility_date": eligibility_date,
            "latest_source_month": source_latest,
            "archive_survivor": bool(archive_survivor),
        })
        chunks.append(g)

    if not chunks:
        raise ValueError("No usable symbols after dead-tail trimming")

    out = pd.concat(chunks, ignore_index=True)
    meta = pd.DataFrame(meta_rows).sort_values("symbol").reset_index(drop=True)
    return out, meta


def build_panels(long_df: pd.DataFrame, symbol_meta: pd.DataFrame):
    symbols = symbol_meta["symbol"].tolist()
    start = long_df["date"].min()
    end = long_df["date"].max()
    calendar = pd.date_range(start, end, freq="D")

    ret = (
        long_df.pivot(index="date", columns="symbol", values="ret_obs")
        .reindex(index=calendar, columns=symbols)
        .fillna(0.0)
        .astype("float64")
    )

    sma_obs = (
        long_df.pivot(index="date", columns="symbol", values="sma_signal_obs")
        .reindex(index=calendar, columns=symbols)
    )
    don_obs = (
        long_df.pivot(index="date", columns="symbol", values="don_signal_obs")
        .reindex(index=calendar, columns=symbols)
    )

    eligible = pd.DataFrame(False, index=calendar, columns=symbols, dtype=bool)
    alive = pd.DataFrame(False, index=calendar, columns=symbols, dtype=bool)

    for row in symbol_meta.itertuples(index=False):
        if pd.notna(row.first_date) and pd.notna(row.alive_end_date):
            alive.loc[row.first_date:row.alive_end_date, row.symbol] = True
        if pd.notna(row.eligibility_date) and pd.notna(row.alive_end_date):
            eligible.loc[row.eligibility_date:row.alive_end_date, row.symbol] = True

    # Signals are only recomputed on observed bars. Between observations, carry
    # the last known close-state while the contract remains eligible/alive.
    sma_signal = sma_obs.astype("float32").ffill().fillna(0.0).astype(bool) & eligible
    don_signal = don_obs.astype("float32").ffill().fillna(0.0).astype(bool) & eligible

    return calendar, ret, alive, eligible, sma_signal, don_signal


def precompute_strategy(
    name: str,
    ret: pd.DataFrame,
    alive: pd.DataFrame,
    eligible: pd.DataFrame,
    signal: pd.DataFrame | None,
) -> Precomputed:
    # Keep only daily aggregates after this function. The full 864-symbol test
    # can otherwise retain several hundred MB of duplicate weight matrices on
    # Android/Pydroid. Temporary arrays here are released before the next
    # strategy is precomputed.
    n = eligible.sum(axis=1).to_numpy(dtype=np.float64)
    numerator = (eligible if signal is None else signal).to_numpy(dtype=np.float32)
    target = np.zeros_like(numerator, dtype=np.float32)
    valid = n > 0
    target[valid] = numerator[valid] / n[valid, None]

    held = np.zeros_like(target, dtype=np.float32)
    held[1:] = target[:-1]
    alive_np = alive.to_numpy(dtype=bool)
    ret_np = ret.to_numpy(dtype=np.float64)
    executable = held * alive_np
    prev_exec = np.zeros_like(executable, dtype=np.float32)
    prev_exec[1:] = executable[:-1]

    gross_return = np.sum(held * ret_np, axis=1, dtype=np.float64)
    disappearance_exposure = np.sum(held * (~alive_np), axis=1, dtype=np.float64)
    turnover = np.sum(np.abs(executable - prev_exec), axis=1, dtype=np.float64)
    gross_exposure = np.sum(executable, axis=1, dtype=np.float64)
    active_count = (eligible if signal is None else signal).sum(axis=1).to_numpy(dtype=np.int32)

    idx = ret.index
    return Precomputed(
        name=name,
        gross_return=pd.Series(gross_return, index=idx),
        disappearance_exposure=pd.Series(disappearance_exposure, index=idx),
        turnover=pd.Series(turnover, index=idx),
        gross_exposure=pd.Series(gross_exposure, index=idx),
        active_count=pd.Series(active_count, index=idx),
    )


def first_evaluation_date(eligible: pd.DataFrame) -> pd.Timestamp:
    has = eligible.sum(axis=1) > 0
    if not has.any():
        raise ValueError("No symbol reaches the common 200-bar warmup")
    first_eligible = has[has].index[0]
    pos = eligible.index.get_loc(first_eligible)
    if pos + 1 >= len(eligible.index):
        raise ValueError("No next day after first eligibility date")
    return eligible.index[pos + 1]


def period_compound(r: pd.Series, keys: Iterable) -> pd.Series:
    return r.groupby(list(keys)).apply(lambda x: float((1.0 + x).prod() - 1.0))


def longest_drawdown_days(equity: pd.Series) -> int:
    peak = -np.inf
    dd_start = None
    longest = 0
    for date, value in equity.items():
        if value >= peak * (1.0 - 1e-12):
            if dd_start is not None:
                longest = max(longest, int((date - dd_start).days))
                dd_start = None
            peak = max(peak, float(value))
        else:
            if dd_start is None:
                dd_start = date
            longest = max(longest, int((date - dd_start).days))
    return longest


def metric_row(
    pre: Precomputed,
    eligible_count: pd.Series,
    fee: float,
    penalty: float,
    slice_name: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> MetricRow:
    idx = pre.gross_return.index
    mask = (idx >= start) & (idx <= end)
    r = (
        pre.gross_return.loc[mask]
        - penalty * pre.disappearance_exposure.loc[mask]
        - fee * pre.turnover.loc[mask]
    )
    turnover = pre.turnover.loc[mask]
    gross_exposure = pre.gross_exposure.loc[mask]
    active = pre.active_count.loc[mask]
    elig = eligible_count.loc[mask]

    if r.empty:
        raise ValueError(f"Empty metric slice: {slice_name}")
    if (1.0 + r <= 0).any():
        first_bad = r[(1.0 + r) <= 0].index[0]
        raise ValueError(
            f"{pre.name} fee={fee} penalty={penalty}: portfolio return <= -100% on {first_bad.date()}"
        )

    equity = (1.0 + r).cumprod()
    years = (equity.index[-1] - equity.index[0]).days / DAYS_PER_YEAR
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 else np.nan
    dd = equity / equity.cummax() - 1.0
    max_dd = float(dd.min())
    vol = float(r.std(ddof=1) * math.sqrt(VOL_DAYS_PER_YEAR))
    calmar = cagr / abs(max_dd) if max_dd < 0 else np.nan

    yearly = period_compound(r, [r.index.year])
    qlabels = pd.Index([f"{d.year}-Q{d.quarter}" for d in r.index])
    quarterly = period_compound(r, [qlabels])
    mlabels = pd.Index([f"{d.year}-{d.month:02d}" for d in r.index])
    monthly = period_compound(r, [mlabels])
    rolling = equity / equity.shift(365) - 1.0

    wy_label = str(yearly.idxmin()) if len(yearly) else ""
    wq_label = str(quarterly.idxmin()) if len(quarterly) else ""
    wm_label = str(monthly.idxmin()) if len(monthly) else ""

    return MetricRow(
        strategy=pre.name,
        slice=slice_name,
        fee_bps=fee * 10000.0,
        disappearance_penalty=penalty,
        start=equity.index[0].date().isoformat(),
        end=equity.index[-1].date().isoformat(),
        days=int(len(equity)),
        cagr=cagr,
        max_drawdown=max_dd,
        annualized_vol=vol,
        calmar=float(calmar),
        ending_multiple=float(equity.iloc[-1]),
        turnover=float(turnover.sum()),
        average_gross_exposure=float(gross_exposure.mean()),
        average_cash_fraction=float((1.0 - gross_exposure).mean()),
        worst_calendar_year=float(yearly.min()) if len(yearly) else np.nan,
        worst_calendar_year_label=wy_label,
        worst_calendar_quarter=float(quarterly.min()) if len(quarterly) else np.nan,
        worst_calendar_quarter_label=wq_label,
        worst_month=float(monthly.min()) if len(monthly) else np.nan,
        worst_month_label=wm_label,
        worst_rolling_12m=float(rolling.min()) if rolling.notna().any() else np.nan,
        longest_drawdown_days=longest_drawdown_days(equity),
        average_eligible_assets=float(elig.mean()),
        median_eligible_assets=float(elig.median()),
        average_active_assets=float(active.mean()),
        median_active_assets=float(active.median()),
    )


def yearly_returns(pre: Precomputed, fee: float, penalty: float, start: pd.Timestamp) -> pd.DataFrame:
    r = (
        pre.gross_return - penalty * pre.disappearance_exposure - fee * pre.turnover
    )
    r = r[r.index >= start]
    rows = []
    for year, g in r.groupby(r.index.year):
        rows.append({
            "strategy": pre.name,
            "fee_bps": fee * 10000.0,
            "disappearance_penalty": penalty,
            "year": int(year),
            "return": float((1.0 + g).prod() - 1.0),
            "days": int(len(g)),
            "start": g.index.min().date().isoformat(),
            "end": g.index.max().date().isoformat(),
        })
    return pd.DataFrame(rows)


def contribution_table(
    pre: Precomputed,
    symbol_meta: pd.DataFrame,
    ret: pd.DataFrame,
    alive: pd.DataFrame,
    eligible: pd.DataFrame,
    signal: pd.DataFrame | None,
    fee: float,
    penalty: float,
    start: pd.Timestamp,
) -> pd.DataFrame:
    idx = pre.gross_return.index
    mask = idx >= start
    net_r = (
        pre.gross_return.loc[mask]
        - penalty * pre.disappearance_exposure.loc[mask]
        - fee * pre.turnover.loc[mask]
    )
    if (1.0 + net_r <= 0).any():
        raise ValueError(f"Cannot compute contributions for ruined {pre.name} path")
    equity = (1.0 + net_r).cumprod()
    equity_before = equity.shift(1, fill_value=1.0).to_numpy(dtype=np.float64)

    n = eligible.sum(axis=1).to_numpy(dtype=np.float64)
    numerator = (eligible if signal is None else signal).to_numpy(dtype=np.float32)
    target = np.zeros_like(numerator, dtype=np.float32)
    valid = n > 0
    target[valid] = numerator[valid] / n[valid, None]
    held = np.zeros_like(target, dtype=np.float32)
    held[1:] = target[:-1]
    alive_np = alive.to_numpy(dtype=bool)
    executable = held * alive_np
    prev_exec = np.zeros_like(executable, dtype=np.float32)
    prev_exec[1:] = executable[:-1]

    mask_np = np.asarray(mask, dtype=bool)
    held_s = held[mask_np]
    alive_s = alive_np[mask_np]
    ret_s = ret.to_numpy(dtype=np.float64)[mask_np]
    exec_s = executable[mask_np]
    prev_exec_s = prev_exec[mask_np]

    gross = np.sum(
        (held_s * ret_s) * equity_before[:, None], axis=0, dtype=np.float64
    )
    dis_drag = np.sum(
        (held_s * (~alive_s)) * (equity_before * penalty)[:, None],
        axis=0, dtype=np.float64,
    )
    fee_drag = np.sum(
        np.abs(exec_s - prev_exec_s) * (equity_before * fee)[:, None],
        axis=0, dtype=np.float64,
    )
    net = gross - dis_drag - fee_drag

    m = symbol_meta.set_index("symbol")
    out = pd.DataFrame({
        "symbol": ret.columns,
        "strategy": pre.name,
        "gross_wealth_contribution": gross,
        "disappearance_wealth_drag": dis_drag,
        "fee_wealth_drag": fee_drag,
        "net_wealth_contribution": net,
    }).set_index("symbol")
    out = out.join(
        m[[
            "archive_survivor", "latest_source_month", "first_date", "last_live_date",
            "observed_bars_after_trim", "positive_volume_bars", "eligibility_date",
        ]],
        how="left",
    ).reset_index()
    positive_total = float(out["net_wealth_contribution"].clip(lower=0).sum())
    out["share_of_positive_gains"] = np.where(
        out["net_wealth_contribution"] > 0,
        out["net_wealth_contribution"] / positive_total if positive_total > 0 else np.nan,
        0.0,
    )
    return out.sort_values("net_wealth_contribution", ascending=False).reset_index(drop=True)


def concentration_summary(contrib: pd.DataFrame, ending_multiple: float) -> dict:
    c = contrib.sort_values("net_wealth_contribution", ascending=False)
    positive_total = float(c["net_wealth_contribution"].clip(lower=0).sum())
    top5_gain = float(c.head(5)["net_wealth_contribution"].clip(lower=0).sum())
    net_pnl = ending_multiple - 1.0
    survivor = c.groupby("archive_survivor")["net_wealth_contribution"].sum().to_dict()
    return {
        "strategy": str(c["strategy"].iloc[0]),
        "top_contributor": str(c.iloc[0]["symbol"]),
        "top_contribution": float(c.iloc[0]["net_wealth_contribution"]),
        "top5_symbols": ",".join(c.head(5)["symbol"].astype(str)),
        "top5_share_of_positive_gains": top5_gain / positive_total if positive_total > 0 else np.nan,
        "top5_share_of_net_pnl": top5_gain / net_pnl if net_pnl > 0 else np.nan,
        "bottom5_symbols": ",".join(c.tail(5)["symbol"].astype(str)),
        "positive_asset_gain_total": positive_total,
        "net_portfolio_pnl": net_pnl,
        "archive_survivor_net_contribution": float(survivor.get(True, 0.0)),
        "historical_non_survivor_net_contribution": float(survivor.get(False, 0.0)),
    }


def make_precomputed_subset(
    name: str,
    excluded: set[str],
    ret: pd.DataFrame,
    alive: pd.DataFrame,
    eligible: pd.DataFrame,
    signal: pd.DataFrame | None,
) -> Precomputed:
    cols = [c for c in ret.columns if c not in excluded]
    sig = None if signal is None else signal[cols]
    return precompute_strategy(name, ret[cols], alive[cols], eligible[cols], sig)


def write_markdown_summary(
    out_path: Path,
    metrics_df: pd.DataFrame,
    concentration_df: pd.DataFrame,
    invariants: dict,
    eval_start: pd.Timestamp,
) -> None:
    base = metrics_df[
        (metrics_df["fee_bps"] == 10.0)
        & (metrics_df["disappearance_penalty"] == 0.25)
    ].copy()
    lines = [
        "# R002 Wide-Universe PTI Validation — Engine Output v0.1",
        "",
        "**Research status:** raw engine output; PASS/FAIL/REDESIGN must be decided after review.",
        "",
        f"- Evaluation start: `{eval_start.date().isoformat()}`",
        f"- Raw symbols: **{invariants['raw_symbols']}**",
        f"- Raw rows: **{invariants['raw_rows']}**",
        f"- Common observed-bar warmup: **{COMMON_WARMUP}**",
        f"- Baseline: **10 bps + 25% disappearance penalty**",
        "",
        "## Baseline metrics",
        "",
        "| Strategy | Slice | CAGR | Max DD | Vol | Calmar | Ending | Turnover | Avg exposure | Worst 12m |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in base.itertuples(index=False):
        lines.append(
            f"| {row.strategy} | {row.slice} | {pct(row.cagr)} | {pct(row.max_drawdown)} | "
            f"{pct(row.annualized_vol)} | {row.calmar:.2f} | {row.ending_multiple:.3f}x | "
            f"{row.turnover:.2f} | {pct(row.average_gross_exposure)} | {pct(row.worst_rolling_12m)} |"
        )
    lines += ["", "## Concentration baseline", ""]
    for row in concentration_df.itertuples(index=False):
        lines.append(
            f"- **{row.strategy}:** top-5 share of positive gains {pct(row.top5_share_of_positive_gains)}; "
            f"top contributor `{row.top_contributor}`; survivor net contribution "
            f"{row.archive_survivor_net_contribution:.4f}; historical/non-survivor net contribution "
            f"{row.historical_non_survivor_net_contribution:.4f}."
        )
    lines += [
        "",
        "## Important",
        "",
        "This file intentionally does not auto-promote a finalist. Review the full stress grid, late period, yearly returns and concentration diagnostics before assigning PASS / FAIL / REDESIGN.",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def maybe_validate_state(csv_path: Path, state_path: Path | None) -> dict:
    if state_path is None:
        candidate = csv_path.with_name("r002_binance_full_universe_state.json")
        state_path = candidate if candidate.exists() else None
    if state_path is None or not state_path.exists():
        return {"state_file": None, "state_validation": "not_provided"}
    state = json.loads(state_path.read_text(encoding="utf-8"))
    combined_rows = state.get("combined_rows")
    combined_symbols = state.get("combined_symbols")
    if combined_rows is not None and int(combined_rows) != EXPECTED_ROWS:
        raise ValueError(f"State combined_rows={combined_rows}, expected {EXPECTED_ROWS}")
    if combined_symbols is not None and int(combined_symbols) != EXPECTED_SYMBOLS:
        raise ValueError(f"State combined_symbols={combined_symbols}, expected {EXPECTED_SYMBOLS}")
    return {
        "state_file": str(state_path),
        "state_validation": "PASS",
        "state_version": state.get("version"),
        "state_combined_rows": combined_rows,
        "state_combined_symbols": combined_symbols,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv", help="Path to r002_binance_full_universe_daily.csv")
    p.add_argument("--state", help="Optional r002_binance_full_universe_state.json")
    p.add_argument(
        "--outdir",
        help="Output directory. Default: sibling r002_wide_universe_results_v0_1",
    )
    p.add_argument(
        "--skip-known-invariants",
        action="store_true",
        help="Skip exact 864-symbol / 637705-row assertion; integrity checks still run.",
    )
    args = p.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)
    state_path = Path(args.state).expanduser().resolve() if args.state else None
    outdir = (
        Path(args.outdir).expanduser().resolve()
        if args.outdir
        else csv_path.parent / "r002_wide_universe_results_v0_1"
    )
    outdir.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("R002 WIDE-UNIVERSE POINT-IN-TIME FINALIST ENGINE v0.1")
    print("Frozen: SMA120 vs Donchian100/50 vs PTI passive")
    print("No tuning; common 200 observed-bar warmup")
    print("=" * 78)
    print("Input:", csv_path)
    print("Output:", outdir)
    print()

    print("[1/8] Validating dataset...")
    raw, invariants = load_and_validate(csv_path, not args.skip_known_invariants)
    state_info = maybe_validate_state(csv_path, state_path)
    print("      PASS:", invariants["raw_symbols"], "symbols,", invariants["raw_rows"], "rows")

    print("[2/8] Trimming dead tails and computing observed-bar signals...")
    long_df, symbol_meta = prepare_long(raw)
    del raw
    eligible_ever = int(symbol_meta["eligibility_date"].notna().sum())
    print("      Symbols retained after dead-tail cleaning:", symbol_meta.shape[0])
    print("      Symbols reaching 200 observed bars:", eligible_ever)

    print("[3/8] Building daily PTI panels...")
    calendar, ret, alive, eligible, sma_signal, don_signal = build_panels(long_df, symbol_meta)
    del long_df
    eval_start = first_evaluation_date(eligible)
    eval_end = calendar[-1]
    eligible_count = eligible.sum(axis=1).astype(int)
    print("      Evaluation:", eval_start.date(), "->", eval_end.date())

    print("[4/8] Precomputing portfolio mechanics...")
    strategies = {
        "SMA120": precompute_strategy("SMA120", ret, alive, eligible, sma_signal),
        "DON100_50": precompute_strategy("DON100_50", ret, alive, eligible, don_signal),
        "PASSIVE": precompute_strategy("PASSIVE", ret, alive, eligible, None),
    }

    print("[5/8] Running full 4x4 stress grid and late-period slice...")
    metric_rows: list[dict] = []
    yearly_frames: list[pd.DataFrame] = []
    for fee in FEE_GRID:
        for penalty in PENALTY_GRID:
            for pre in strategies.values():
                full = metric_row(pre, eligible_count, fee, penalty, "FULL", eval_start, eval_end)
                late_start = max(LATE_START, eval_start)
                late = metric_row(pre, eligible_count, fee, penalty, "POST_2023", late_start, eval_end)
                metric_rows.extend([asdict(full), asdict(late)])
                yearly_frames.append(yearly_returns(pre, fee, penalty, eval_start))
    metrics_df = pd.DataFrame(metric_rows)
    yearly_df = pd.concat(yearly_frames, ignore_index=True).drop_duplicates()

    print("[6/8] Building breadth/equity diagnostics...")
    breadth = pd.DataFrame(index=calendar)
    breadth.index.name = "date"
    breadth["eligible_assets"] = eligible_count
    breadth["sma_active_assets"] = sma_signal.sum(axis=1).astype(int)
    breadth["don_active_assets"] = don_signal.sum(axis=1).astype(int)
    denom = eligible_count.replace(0, np.nan).astype(float)
    breadth["sma_target_exposure"] = (breadth["sma_active_assets"] / denom).fillna(0.0)
    breadth["don_target_exposure"] = (breadth["don_active_assets"] / denom).fillna(0.0)
    breadth["passive_target_exposure"] = (eligible_count > 0).astype(float)
    breadth = breadth[breadth.index >= eval_start]

    baseline_equity = pd.DataFrame(index=calendar)
    baseline_equity.index.name = "date"
    for name, pre in strategies.items():
        r = pre.gross_return - BASELINE_PENALTY * pre.disappearance_exposure - BASELINE_FEE * pre.turnover
        eq = (1.0 + r[r.index >= eval_start]).cumprod()
        baseline_equity.loc[eq.index, name] = eq
    baseline_equity = baseline_equity[baseline_equity.index >= eval_start]

    print("[7/8] Computing baseline concentration and ex-post exclusion diagnostics...")
    contrib_frames = []
    concentration_rows = []
    exclusion_rows = []
    for name in ["SMA120", "DON100_50"]:
        pre = strategies[name]
        signal = sma_signal if name == "SMA120" else don_signal
        contrib = contribution_table(
            pre, symbol_meta, ret, alive, eligible, signal,
            BASELINE_FEE, BASELINE_PENALTY, eval_start,
        )
        contrib_frames.append(contrib)
        base_metric = metric_row(pre, eligible_count, BASELINE_FEE, BASELINE_PENALTY, "FULL", eval_start, eval_end)
        summary = concentration_summary(contrib, base_metric.ending_multiple)

        top1 = {str(contrib.iloc[0]["symbol"])}
        top5 = set(contrib.head(5)["symbol"].astype(str))
        for label, excluded in [("EX_TOP1", top1), ("EX_TOP5", top5)]:
            ex_pre = make_precomputed_subset(
                f"{name}_{label}", excluded, ret, alive, eligible, signal
            )
            ex_elig = eligible[[c for c in eligible.columns if c not in excluded]].sum(axis=1).astype(int)
            ex_metric = metric_row(
                ex_pre, ex_elig, BASELINE_FEE, BASELINE_PENALTY,
                "FULL", eval_start, eval_end,
            )
            exclusion_rows.append({
                "strategy": name,
                "diagnostic": label,
                "excluded_symbols": ",".join(sorted(excluded)),
                "cagr": ex_metric.cagr,
                "max_drawdown": ex_metric.max_drawdown,
                "ending_multiple": ex_metric.ending_multiple,
                "turnover": ex_metric.turnover,
            })
            summary[f"{label.lower()}_cagr"] = ex_metric.cagr
            summary[f"{label.lower()}_max_drawdown"] = ex_metric.max_drawdown
            summary[f"{label.lower()}_ending_multiple"] = ex_metric.ending_multiple
        concentration_rows.append(summary)

    contributions_df = pd.concat(contrib_frames, ignore_index=True)
    concentration_df = pd.DataFrame(concentration_rows)
    exclusion_df = pd.DataFrame(exclusion_rows)

    print("[8/8] Writing outputs...")
    metrics_df.to_csv(outdir / "r002_wide_universe_metrics.csv", index=False)
    yearly_df.to_csv(outdir / "r002_wide_universe_yearly_returns.csv", index=False)
    breadth.to_csv(outdir / "r002_wide_universe_breadth.csv")
    baseline_equity.to_csv(outdir / "r002_wide_universe_baseline_equity.csv")
    contributions_df.to_csv(outdir / "r002_wide_universe_contributions_baseline.csv", index=False)
    concentration_df.to_csv(outdir / "r002_wide_universe_concentration_summary.csv", index=False)
    exclusion_df.to_csv(outdir / "r002_wide_universe_exclusion_diagnostics.csv", index=False)
    symbol_meta.to_csv(outdir / "r002_wide_universe_symbol_meta.csv", index=False)

    run_state = {
        "engine_version": VERSION,
        "research_freeze": {
            "common_warmup_observed_bars": COMMON_WARMUP,
            "sma_lookback": SMA_LOOKBACK,
            "donchian_entry": DON_ENTRY,
            "donchian_exit": DON_EXIT,
            "fee_grid": list(FEE_GRID),
            "disappearance_penalty_grid": list(PENALTY_GRID),
            "baseline_fee": BASELINE_FEE,
            "baseline_disappearance_penalty": BASELINE_PENALTY,
            "late_start": LATE_START.date().isoformat(),
        },
        "input": {
            "csv": str(csv_path),
            "csv_sha256": sha256_file(csv_path),
            **state_info,
        },
        "validation": invariants,
        "cleaning": {
            "symbols_in_symbol_meta": int(len(symbol_meta)),
            "symbols_ever_eligible": eligible_ever,
            "evaluation_start": eval_start.date().isoformat(),
            "evaluation_end": eval_end.date().isoformat(),
            "latest_source_month": str(symbol_meta["latest_source_month"].max()),
            "archive_survivors": int(symbol_meta["archive_survivor"].sum()),
        },
        "outputs": [
            "r002_wide_universe_metrics.csv",
            "r002_wide_universe_yearly_returns.csv",
            "r002_wide_universe_breadth.csv",
            "r002_wide_universe_baseline_equity.csv",
            "r002_wide_universe_contributions_baseline.csv",
            "r002_wide_universe_concentration_summary.csv",
            "r002_wide_universe_exclusion_diagnostics.csv",
            "r002_wide_universe_symbol_meta.csv",
            "r002_wide_universe_run_state.json",
            "r002_wide_universe_summary.md",
        ],
    }
    (outdir / "r002_wide_universe_run_state.json").write_text(
        json.dumps(run_state, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    write_markdown_summary(
        outdir / "r002_wide_universe_summary.md",
        metrics_df,
        concentration_df,
        invariants,
        eval_start,
    )

    print()
    print("=" * 78)
    print("BASELINE 10 bps + 25% disappearance penalty")
    print("=" * 78)
    baseline = metrics_df[
        (metrics_df["fee_bps"] == 10.0)
        & (metrics_df["disappearance_penalty"] == 0.25)
    ]
    for row in baseline.itertuples(index=False):
        print(
            f"{row.strategy:10s} {row.slice:9s} "
            f"CAGR={row.cagr:8.2%} MaxDD={row.max_drawdown:8.2%} "
            f"Vol={row.annualized_vol:8.2%} Calmar={row.calmar:6.2f} "
            f"Ending={row.ending_multiple:8.3f}x Turnover={row.turnover:8.2f}"
        )
    print()
    print("Concentration:")
    for row in concentration_df.itertuples(index=False):
        print(
            f"{row.strategy}: top5 positive-gain share={row.top5_share_of_positive_gains:.2%}; "
            f"top={row.top_contributor}; ex-top1 CAGR={row.ex_top1_cagr:.2%}; "
            f"ex-top5 CAGR={row.ex_top5_cagr:.2%}"
        )
    print()
    print("RESULT FILES:", outdir)
    print("Upload at minimum:")
    print("  r002_wide_universe_summary.md")
    print("  r002_wide_universe_metrics.csv")
    print("  r002_wide_universe_concentration_summary.csv")
    print("  r002_wide_universe_contributions_baseline.csv")
    print("  r002_wide_universe_breadth.csv")
    print("  r002_wide_universe_run_state.json")


if __name__ == "__main__":
    main()
