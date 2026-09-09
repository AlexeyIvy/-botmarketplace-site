"""R003-E002 self-financing BTC cash-and-carry implementation study v0.1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

VERSION = "0.1"
PROTOCOL = "r003-e002-self-financing-cash-carry-protocol-v0.1"
SYMBOL = "BTCUSDT"

SPOT_URL = "https://data-api.binance.vision/api/v3/klines"
FUT_URL = "https://fapi.binance.com/fapi/v1/klines"
MARK_URL = "https://fapi.binance.com/fapi/v1/markPriceKlines"
FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"

DOWNLOAD_START = pd.Timestamp("2019-09-01", tz="UTC")
FULL_FLOOR = pd.Timestamp("2019-10-01", tz="UTC")
PRIMARY_START = pd.Timestamp("2020-01-01", tz="UTC")
PRE2023_END = pd.Timestamp("2022-12-31 23:59:59.999", tz="UTC")
POST2023_START = pd.Timestamp("2023-01-01", tz="UTC")

FEES = (0.0005, 0.0010, 0.0025)
BASE_FEE = 0.0010
FUNDING_TREATMENTS = ("REALIZED_FUNDING", "ZERO_FUNDING", "ADVERSE_FUNDING")
MIN_COVERAGE = 0.995
MAX_GAP_HOURS = 6.0
LOW_HEADROOM = 0.10
HURDLES = (0.0, 0.025, 0.05)
HOURS_PER_YEAR = 365.25 * 24.0
EPS = 1e-12


def get_json(url: str, params: dict):
    req = Request(
        url + "?" + urlencode(params),
        headers={"User-Agent": "botmarketplace-r003-e002/0.1"},
    )
    with urlopen(req, timeout=90) as r:
        raw = r.read()
    return raw, json.loads(raw.decode("utf-8"))


def fetch_klines(url: str, interval: str, limit: int, label: str):
    start = int(DOWNLOAD_START.timestamp() * 1000)
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    rows = []
    hashes = []
    last_open = None
    while True:
        raw, obj = get_json(
            url,
            {
                "symbol": SYMBOL,
                "interval": interval,
                "startTime": start,
                "limit": limit,
            },
        )
        hashes.append(hashlib.sha256(raw).hexdigest())
        if not isinstance(obj, list):
            raise RuntimeError(f"{label} source error: {obj}")
        if not obj:
            break
        valid = [r for r in obj if isinstance(r, list) and len(r) >= 7 and int(r[6]) < now_ms]
        rows.extend(valid)
        cur = int(obj[-1][0])
        if last_open is not None and cur <= last_open:
            raise RuntimeError(f"{label} pagination stalled")
        last_open = cur
        start = cur + 1
        if len(obj) < limit:
            break

    if not rows:
        raise RuntimeError(f"No closed {label} klines returned")

    x = pd.DataFrame(rows)
    out = pd.DataFrame(
        {
            "open_time": pd.to_datetime(pd.to_numeric(x.iloc[:, 0]), unit="ms", utc=True),
            "open": pd.to_numeric(x.iloc[:, 1], errors="coerce"),
            "high": pd.to_numeric(x.iloc[:, 2], errors="coerce"),
            "low": pd.to_numeric(x.iloc[:, 3], errors="coerce"),
            "close": pd.to_numeric(x.iloc[:, 4], errors="coerce"),
            "close_time": pd.to_datetime(pd.to_numeric(x.iloc[:, 6]), unit="ms", utc=True),
        }
    )
    out = (
        out.dropna()
        .sort_values("open_time")
        .drop_duplicates("open_time", keep="last")
        .reset_index(drop=True)
    )
    if (out[["open", "high", "low", "close"]] <= 0).any().any():
        raise RuntimeError(f"{label} contains non-positive retained prices")
    return out, hashes, len(rows)


def fetch_funding():
    start = int(DOWNLOAD_START.timestamp() * 1000)
    rows = []
    hashes = []
    last = None
    while True:
        raw, obj = get_json(
            FUNDING_URL,
            {"symbol": SYMBOL, "startTime": start, "limit": 1000},
        )
        hashes.append(hashlib.sha256(raw).hexdigest())
        if not isinstance(obj, list):
            raise RuntimeError(f"Funding source error: {obj}")
        if not obj:
            break
        rows.extend(obj)
        cur = int(obj[-1]["fundingTime"])
        if last is not None and cur <= last:
            raise RuntimeError("Funding pagination stalled")
        last = cur
        start = cur + 1
        if len(obj) < 1000:
            break

    if not rows:
        raise RuntimeError("No funding history returned")

    x = pd.DataFrame(rows)
    x["funding_time"] = pd.to_datetime(
        pd.to_numeric(x["fundingTime"], errors="coerce"),
        unit="ms",
        utc=True,
    )
    x["funding_rate"] = pd.to_numeric(x["fundingRate"], errors="coerce")
    x["published_mark_price"] = (
        pd.to_numeric(x["markPrice"], errors="coerce") if "markPrice" in x else np.nan
    )
    x["rate_type"] = x["rateType"].astype(str) if "rateType" in x else ""
    x = (
        x.dropna(subset=["funding_time", "funding_rate"])
        .sort_values("funding_time")
        .drop_duplicates("funding_time", keep="last")
        [["funding_time", "funding_rate", "published_mark_price", "rate_type"]]
        .reset_index(drop=True)
    )
    return x, hashes, len(rows)


def source_stats(df: pd.DataFrame, label: str):
    z = df[df["open_time"] >= PRIMARY_START].copy()
    if z.empty:
        return {
            "label": label,
            "rows_primary": 0,
            "coverage": 0.0,
            "max_gap_hours": np.nan,
        }
    gaps = z["open_time"].diff().dt.total_seconds().div(3600).dropna()
    start = z["open_time"].iloc[0]
    end = z["open_time"].iloc[-1]
    expected = int(round((end - start).total_seconds() / 3600.0)) + 1
    return {
        "label": label,
        "rows_total": int(len(df)),
        "rows_primary": int(len(z)),
        "start": df["open_time"].iloc[0].isoformat(),
        "end": df["open_time"].iloc[-1].isoformat(),
        "primary_start_actual": start.isoformat(),
        "primary_end_actual": end.isoformat(),
        "expected_primary_hours": int(expected),
        "coverage": float(len(z) / expected) if expected > 0 else 0.0,
        "max_gap_hours": float(gaps.max()) if len(gaps) else 0.0,
    }


def build_common(spot, fut, mark):
    s = spot.rename(
        columns={
            "open": "spot_open",
            "high": "spot_high",
            "low": "spot_low",
            "close": "spot_close",
            "close_time": "spot_close_time",
        }
    )
    f = fut.rename(
        columns={
            "open": "fut_open",
            "high": "fut_high",
            "low": "fut_low",
            "close": "fut_close",
            "close_time": "fut_close_time",
        }
    )
    m = mark.rename(
        columns={
            "open": "mark_open",
            "high": "mark_high",
            "low": "mark_low",
            "close": "mark_close",
            "close_time": "mark_close_time",
        }
    )

    common = s.merge(
        f[["open_time", "fut_open", "fut_high", "fut_low", "fut_close", "fut_close_time"]],
        on="open_time",
        how="inner",
    ).merge(
        m[["open_time", "mark_open", "mark_high", "mark_low", "mark_close", "mark_close_time"]],
        on="open_time",
        how="inner",
    )
    common = common.sort_values("open_time").drop_duplicates("open_time", keep="last").reset_index(drop=True)
    common["close_time"] = common[["spot_close_time", "fut_close_time", "mark_close_time"]].min(axis=1)
    common["mark_basis"] = common["mark_close"] / common["spot_close"] - 1.0
    common["contract_basis"] = common["fut_close"] / common["spot_close"] - 1.0
    return common


def align_funding(funding: pd.DataFrame, common: pd.DataFrame):
    base = common[["open_time", "close_time", "mark_close"]].sort_values("close_time")
    x = pd.merge_asof(
        funding.sort_values("funding_time"),
        base,
        left_on="funding_time",
        right_on="close_time",
        direction="backward",
        allow_exact_matches=True,
    )
    x["funding_mark"] = x["published_mark_price"]
    bad = x["funding_mark"].isna() | (x["funding_mark"] <= 0)
    x.loc[bad, "funding_mark"] = x.loc[bad, "mark_close"]
    x = x.dropna(subset=["open_time", "funding_mark"])
    return x.reset_index(drop=True)


def audit_data(spot, fut, mark, common, funding, funding_aligned, hashes, raw_counts):
    stats = {
        "spot": source_stats(spot, "spot"),
        "futures_contract": source_stats(fut, "futures_contract"),
        "futures_mark": source_stats(mark, "futures_mark"),
    }
    cp = common[common["open_time"] >= PRIMARY_START].copy()
    if cp.empty:
        common_coverage = 0.0
        common_max_gap = np.nan
        common_expected = 0
    else:
        gaps = cp["open_time"].diff().dt.total_seconds().div(3600).dropna()
        cstart = cp["open_time"].iloc[0]
        cend = cp["open_time"].iloc[-1]
        common_expected = int(round((cend - cstart).total_seconds() / 3600.0)) + 1
        common_coverage = len(cp) / common_expected
        common_max_gap = float(gaps.max()) if len(gaps) else 0.0

    funding_gaps = funding["funding_time"].diff().dt.total_seconds().div(3600).dropna()
    pass_sources = all(
        s["coverage"] >= MIN_COVERAGE
        and (np.isnan(s["max_gap_hours"]) or s["max_gap_hours"] <= MAX_GAP_HOURS)
        for s in stats.values()
    )
    passed = (
        pass_sources
        and common_coverage >= MIN_COVERAGE
        and (np.isnan(common_max_gap) or common_max_gap <= MAX_GAP_HOURS)
        and len(funding_aligned) >= 1000
    )
    return {
        "status": "PASS" if passed else "DATA_REDESIGN",
        "symbol": SYMBOL,
        "sources": {
            "spot": SPOT_URL,
            "futures_contract": FUT_URL,
            "futures_mark": MARK_URL,
            "funding": FUNDING_URL,
        },
        "raw_counts": raw_counts,
        "page_sha256": hashes,
        "source_stats": stats,
        "common_rows": int(len(common)),
        "common_primary_rows": int(len(cp)),
        "common_primary_expected_hours": int(common_expected),
        "common_primary_coverage": float(common_coverage),
        "common_primary_max_gap_hours": common_max_gap,
        "funding_rows_clean": int(len(funding)),
        "funding_rows_aligned": int(len(funding_aligned)),
        "funding_unaligned": int(len(funding) - len(funding_aligned)),
        "funding_start": funding["funding_time"].iloc[0].isoformat(),
        "funding_end": funding["funding_time"].iloc[-1].isoformat(),
        "funding_max_gap_hours": float(funding_gaps.max()) if len(funding_gaps) else 0.0,
        "gate_min_coverage": MIN_COVERAGE,
        "gate_max_gap_hours": MAX_GAP_HOURS,
    }


def transform_rate(rate: float, treatment: str):
    if treatment == "REALIZED_FUNDING":
        return rate
    if treatment == "ZERO_FUNDING":
        return 0.0
    if treatment == "ADVERSE_FUNDING":
        return rate * 0.5 if rate >= 0 else rate * 2.0
    raise ValueError(treatment)


def max_drawdown(nav: pd.Series):
    s = pd.concat([pd.Series([1.0]), nav.reset_index(drop=True)], ignore_index=True)
    peak = s.cummax()
    dd = s / peak - 1.0
    return float(dd.min())


def longest_dd_hours(nav: pd.Series):
    vals = np.r_[1.0, nav.to_numpy(dtype=float)]
    peak = np.maximum.accumulate(vals)
    under = vals < peak - 1e-15
    cur = best = 0
    for flag in under:
        if flag:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return int(max(0, best - 1))


def rolling_return(net_r: pd.Series, hours: int):
    if len(net_r) < hours:
        return np.nan
    x = (1.0 + net_r).rolling(hours).apply(np.prod, raw=True) - 1.0
    return float(x.min()) if len(x.dropna()) else np.nan


def simulate(df: pd.DataFrame, funding_aligned: pd.DataFrame, fee: float, treatment: str):
    if len(df) < 48:
        raise ValueError("Slice too short")

    z = df.copy().reset_index(drop=True)
    start_t = z["open_time"].iloc[0]
    end_close = z["close_time"].iloc[-1]
    fa = funding_aligned[
        (funding_aligned["open_time"] >= start_t)
        & (funding_aligned["close_time"] <= end_close)
    ].copy()

    funding_map = {}
    for row in fa.itertuples(index=False):
        funding_map.setdefault(row.open_time, []).append(
            (float(row.funding_rate), float(row.funding_mark))
        )

    n = len(z)
    month = z["open_time"].dt.to_period("M")
    is_month_end = np.zeros(n, dtype=bool)
    if n > 1:
        is_month_end[:-1] = month.iloc[:-1].to_numpy() != month.iloc[1:].to_numpy()

    spot0 = float(z.loc[0, "spot_close"])
    mark0 = float(z.loc[0, "mark_close"])
    q = 0.5 / spot0
    spot_notional0 = q * spot0
    perp_notional0 = q * mark0
    init_fee = fee * (spot_notional0 + perp_notional0)
    futures_cash = 0.5 - init_fee

    cum_funding = 0.0
    cum_pair = 0.0
    cum_fee = init_fee
    spot_turn = spot_notional0
    perp_turn = perp_notional0
    low_headroom_hours = 0
    hard_margin_failure = futures_cash <= 0
    min_close_ratio = np.inf
    min_intrahour_ratio = np.inf

    rows = []
    nav0 = q * spot0 + futures_cash
    close_ratio0 = futures_cash / max(q * mark0, EPS)
    min_close_ratio = min(min_close_ratio, close_ratio0)

    rows.append(
        {
            "open_time": z.loc[0, "open_time"],
            "close_time": z.loc[0, "close_time"],
            "spot_close": spot0,
            "mark_close": mark0,
            "fut_close": float(z.loc[0, "fut_close"]),
            "q_btc": q,
            "spot_value": q * spot0,
            "futures_cash": futures_cash,
            "nav": nav0,
            "pair_pnl": 0.0,
            "funding_cash": 0.0,
            "execution_fee": init_fee,
            "close_collateral_ratio": close_ratio0,
            "intrahour_collateral_ratio": close_ratio0,
            "rebalanced": True,
            "terminal_exit": False,
        }
    )

    prev_spot = spot0
    prev_mark = mark0

    for i in range(1, n):
        spot = float(z.loc[i, "spot_close"])
        mark = float(z.loc[i, "mark_close"])
        mark_high = float(z.loc[i, "mark_high"])

        cash_before = futures_cash
        intrahour_cash = cash_before - q * (mark_high - prev_mark)
        intrahour_ratio = intrahour_cash / max(q * mark_high, EPS)
        min_intrahour_ratio = min(min_intrahour_ratio, intrahour_ratio)
        if intrahour_ratio < LOW_HEADROOM:
            low_headroom_hours += 1
        if intrahour_cash <= 0:
            hard_margin_failure = True

        spot_pnl = q * (spot - prev_spot)
        fut_pnl = -q * (mark - prev_mark)
        pair_pnl = spot_pnl + fut_pnl
        futures_cash += fut_pnl
        cum_pair += pair_pnl

        reb_fee = 0.0
        rebalanced = False
        if is_month_end[i] and i < n - 1:
            nav_pre = q * spot + futures_cash
            if nav_pre <= 0:
                hard_margin_failure = True
            else:
                q_target = (0.5 * nav_pre) / spot
                dq = q_target - q
                futures_cash -= dq * spot
                spot_trade = abs(dq) * spot
                perp_trade = abs(dq) * mark
                reb_fee = fee * (spot_trade + perp_trade)
                futures_cash -= reb_fee
                cum_fee += reb_fee
                spot_turn += spot_trade
                perp_turn += perp_trade
                q = q_target
                rebalanced = True

        funding_cash = 0.0
        for rate, fmark in funding_map.get(z.loc[i, "open_time"], []):
            rr = transform_rate(rate, treatment)
            funding_cash += rr * q * fmark
        futures_cash += funding_cash
        cum_funding += funding_cash

        close_ratio = futures_cash / max(q * mark, EPS)
        min_close_ratio = min(min_close_ratio, close_ratio)
        if close_ratio < LOW_HEADROOM:
            low_headroom_hours += 1
        if futures_cash <= 0:
            hard_margin_failure = True

        nav = q * spot + futures_cash
        rows.append(
            {
                "open_time": z.loc[i, "open_time"],
                "close_time": z.loc[i, "close_time"],
                "spot_close": spot,
                "mark_close": mark,
                "fut_close": float(z.loc[i, "fut_close"]),
                "q_btc": q,
                "spot_value": q * spot,
                "futures_cash": futures_cash,
                "nav": nav,
                "pair_pnl": pair_pnl,
                "funding_cash": funding_cash,
                "execution_fee": reb_fee,
                "close_collateral_ratio": close_ratio,
                "intrahour_collateral_ratio": intrahour_ratio,
                "rebalanced": rebalanced,
                "terminal_exit": False,
            }
        )
        prev_spot = spot
        prev_mark = mark

    last = rows[-1]
    exit_fee = fee * (abs(last["q_btc"]) * last["spot_close"] + abs(last["q_btc"]) * last["mark_close"])
    last["execution_fee"] += exit_fee
    last["nav"] -= exit_fee
    last["futures_cash"] -= exit_fee
    last["terminal_exit"] = True
    cum_fee += exit_fee
    spot_turn += abs(last["q_btc"]) * last["spot_close"]
    perp_turn += abs(last["q_btc"]) * last["mark_close"]

    path = pd.DataFrame(rows)
    path["net_return"] = path["nav"].pct_change(fill_method=None)
    path.loc[0, "net_return"] = path.loc[0, "nav"] - 1.0

    years = max((path["close_time"].iloc[-1] - path["close_time"].iloc[0]).total_seconds() / (365.25 * 86400.0), 1.0 / 365.25)
    ending = float(path["nav"].iloc[-1])
    cagr = float(ending ** (1.0 / years) - 1.0) if ending > 0 else -1.0
    vol = float(path["net_return"].iloc[1:].std(ddof=0) * math.sqrt(HOURS_PER_YEAR))
    mdd = max_drawdown(path["nav"])
    calmar = cagr / abs(mdd) if mdd < -EPS else np.nan

    return path, {
        "ending_multiple": ending,
        "cagr": cagr,
        "annualized_vol": vol,
        "max_drawdown": mdd,
        "calmar": calmar,
        "worst_7d_return": rolling_return(path["net_return"].fillna(0.0), 24 * 7),
        "worst_30d_return": rolling_return(path["net_return"].fillna(0.0), 24 * 30),
        "longest_drawdown_hours": longest_dd_hours(path["nav"]),
        "total_funding_contribution": float(cum_funding),
        "total_pair_price_basis_pnl": float(cum_pair),
        "total_execution_cost": float(cum_fee),
        "spot_turnover": float(spot_turn),
        "perp_turnover": float(perp_turn),
        "total_turnover": float(spot_turn + perp_turn),
        "min_close_collateral_ratio": float(min_close_ratio),
        "min_intrahour_collateral_ratio": float(min_intrahour_ratio if np.isfinite(min_intrahour_ratio) else close_ratio0),
        "low_headroom_hours": int(low_headroom_hours),
        "hard_margin_failure": bool(hard_margin_failure),
        "funding_events_used": int(len(fa)),
    }


def slice_df(common: pd.DataFrame, name: str):
    if name == "FULL_AVAILABLE":
        x = common[common["open_time"] >= FULL_FLOOR]
    elif name == "PRIMARY_2020":
        x = common[common["open_time"] >= PRIMARY_START]
    elif name == "PRE_2023":
        x = common[(common["open_time"] >= PRIMARY_START) & (common["open_time"] <= PRE2023_END)]
    elif name == "POST_2023":
        x = common[common["open_time"] >= POST2023_START]
    else:
        raise ValueError(name)
    return x.copy().reset_index(drop=True)


def basis_metrics(common: pd.DataFrame, name: str):
    x = slice_df(common, name)
    mb = x["mark_basis"]
    cb = x["contract_basis"]
    widen24 = mb - mb.shift(24)
    return {
        "slice": name,
        "observations": int(len(x)),
        "start": x["open_time"].iloc[0].isoformat(),
        "end": x["open_time"].iloc[-1].isoformat(),
        "mark_basis_mean": float(mb.mean()),
        "mark_basis_median": float(mb.median()),
        "mark_basis_p01": float(mb.quantile(0.01)),
        "mark_basis_p99": float(mb.quantile(0.99)),
        "mark_basis_max_abs": float(mb.abs().max()),
        "contract_basis_mean": float(cb.mean()),
        "contract_basis_median": float(cb.median()),
        "contract_basis_p01": float(cb.quantile(0.01)),
        "contract_basis_p99": float(cb.quantile(0.99)),
        "contract_basis_max_abs": float(cb.abs().max()),
        "worst_24h_mark_basis_widening_against_short": float(widen24.max()),
    }


def yearly_from_path(path: pd.DataFrame):
    p = path.copy()
    p["year"] = p["close_time"].dt.year
    out = []
    for year, g in p.groupby("year"):
        first_idx = g.index[0]
        prev_nav = 1.0 if first_idx == 0 else float(p.loc[first_idx - 1, "nav"])
        end_nav = float(g["nav"].iloc[-1])
        ret = end_nav / prev_nav - 1.0 if prev_nav > 0 else np.nan
        out.append(
            {
                "year": int(year),
                "return": float(ret),
                "funding_contribution_cash": float(g["funding_cash"].sum()),
                "pair_price_basis_pnl": float(g["pair_pnl"].sum()),
                "execution_cost": float(g["execution_fee"].sum()),
                "min_intrahour_collateral_ratio": float(g["intrahour_collateral_ratio"].min()),
            }
        )
    return pd.DataFrame(out)


def completed_year_concentration(yearly: pd.DataFrame):
    current = datetime.now(timezone.utc).year
    y = yearly[(yearly["year"] >= 2020) & (yearly["year"] < current)].copy()
    if y.empty:
        return False, np.nan, 0
    majority = bool((y["return"] > 0).mean() > 0.5)
    pos = y[y["return"] > 0]["return"]
    share = float(pos.max() / pos.sum()) if len(pos) and pos.sum() > 0 else np.nan
    return majority, share, int(len(y))


def self_test():
    idx = pd.date_range("2024-01-01", periods=24 * 40, freq="1h", tz="UTC")
    close_time = idx + pd.Timedelta(hours=1) - pd.Timedelta(milliseconds=1)
    common = pd.DataFrame(
        {
            "open_time": idx,
            "close_time": close_time,
            "spot_close": 100.0,
            "fut_close": 100.0,
            "mark_close": 100.0,
            "mark_high": 100.0,
            "mark_basis": 0.0,
            "contract_basis": 0.0,
        }
    )
    frows = []
    for t in pd.date_range("2024-01-02", "2024-02-09 16:00", freq="8h", tz="UTC"):
        prior = common[common["close_time"] <= t].iloc[-1]
        frows.append(
            {
                "funding_time": t,
                "funding_rate": 0.0001,
                "published_mark_price": 100.0,
                "rate_type": "Regular",
                "open_time": prior["open_time"],
                "close_time": prior["close_time"],
                "mark_close": 100.0,
                "funding_mark": 100.0,
            }
        )
    fa = pd.DataFrame(frows)
    path, met = simulate(common, fa, 0.0, "REALIZED_FUNDING")
    if met["ending_multiple"] <= 1.0 or met["total_funding_contribution"] <= 0:
        raise AssertionError("Synthetic funding self-test failed")
    if abs(met["total_pair_price_basis_pnl"]) > 1e-12:
        raise AssertionError("Synthetic flat-basis self-test failed")
    if met["hard_margin_failure"]:
        raise AssertionError("Synthetic margin self-test failed")


def run(outdir: Path):
    self_test()

    spot, spot_hash, spot_raw = fetch_klines(SPOT_URL, "1h", 1000, "spot")
    fut, fut_hash, fut_raw = fetch_klines(FUT_URL, "1h", 1500, "futures-contract")
    mark, mark_hash, mark_raw = fetch_klines(MARK_URL, "1h", 1500, "futures-mark")
    funding, funding_hash, funding_raw = fetch_funding()

    common = build_common(spot, fut, mark)
    funding_aligned = align_funding(funding, common)

    hashes = {
        "spot_pages": spot_hash,
        "futures_contract_pages": fut_hash,
        "futures_mark_pages": mark_hash,
        "funding_pages": funding_hash,
    }
    raw_counts = {
        "spot_kline_rows_downloaded": int(spot_raw),
        "futures_contract_rows_downloaded": int(fut_raw),
        "futures_mark_rows_downloaded": int(mark_raw),
        "funding_rows_downloaded": int(funding_raw),
    }
    audit = audit_data(spot, fut, mark, common, funding, funding_aligned, hashes, raw_counts)
    (outdir / "r003_e002_source_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if audit["status"] != "PASS":
        state = {
            "status": "DATA_REDESIGN",
            "engine_version": VERSION,
            "protocol": PROTOCOL,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_audit": audit,
        }
        (outdir / "r003_e002_run_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
        print(json.dumps(state, indent=2))
        return

    clean_cols = [
        "open_time",
        "close_time",
        "spot_close",
        "fut_close",
        "mark_close",
        "mark_high",
        "mark_basis",
        "contract_basis",
    ]
    common[clean_cols].to_csv(outdir / "r003_e002_hourly_clean.csv", index=False)

    basis = pd.DataFrame(
        [basis_metrics(common, s) for s in ("FULL_AVAILABLE", "PRIMARY_2020", "PRE_2023", "POST_2023")]
    )
    basis.to_csv(outdir / "r003_e002_basis_diagnostics.csv", index=False)

    metric_rows = []
    baseline_path = None
    baseline_yearly = None
    margin_rows = []

    for s in ("FULL_AVAILABLE", "PRIMARY_2020", "PRE_2023", "POST_2023"):
        sdf = slice_df(common, s)
        for fee in FEES:
            for treatment in FUNDING_TREATMENTS:
                path, met = simulate(sdf, funding_aligned, fee, treatment)
                row = {
                    "slice": s,
                    "fee_bps_per_leg": fee * 10000.0,
                    "funding_treatment": treatment,
                    **met,
                }
                for h in HURDLES:
                    row[f"excess_cagr_vs_{h:.3f}_hurdle"] = met["cagr"] - h
                metric_rows.append(row)

                if s == "PRIMARY_2020" and abs(fee - BASE_FEE) < EPS and treatment == "REALIZED_FUNDING":
                    baseline_path = path.copy()
                    baseline_yearly = yearly_from_path(path)
                if abs(fee - BASE_FEE) < EPS and treatment == "REALIZED_FUNDING":
                    margin_rows.append(
                        {
                            "slice": s,
                            "min_close_collateral_ratio": met["min_close_collateral_ratio"],
                            "min_intrahour_collateral_ratio": met["min_intrahour_collateral_ratio"],
                            "low_headroom_hours": met["low_headroom_hours"],
                            "hard_margin_failure": met["hard_margin_failure"],
                        }
                    )

    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(outdir / "r003_e002_metrics.csv", index=False)
    pd.DataFrame(margin_rows).to_csv(outdir / "r003_e002_margin_diagnostics.csv", index=False)

    if baseline_path is None or baseline_yearly is None:
        raise RuntimeError("Baseline path missing")
    baseline_path.to_csv(outdir / "r003_e002_primary_hourly_nav.csv", index=False)
    baseline_yearly.to_csv(outdir / "r003_e002_yearly.csv", index=False)

    key = metrics_df.set_index(["slice", "fee_bps_per_leg", "funding_treatment"])
    def km(slice_name, fee_bps=10.0, treatment="REALIZED_FUNDING"):
        return key.loc[(slice_name, fee_bps, treatment)]

    primary = km("PRIMARY_2020")
    pre = km("PRE_2023")
    post = km("POST_2023")
    primary25 = km("PRIMARY_2020", 25.0)
    post25 = km("POST_2023", 25.0)
    adverse = km("PRIMARY_2020", 10.0, "ADVERSE_FUNDING")
    zero = km("PRIMARY_2020", 10.0, "ZERO_FUNDING")

    majority_years, largest_year_share, completed_years = completed_year_concentration(baseline_yearly)
    capital_eff = (
        "STRONG" if post["cagr"] >= 0.05
        else "MARGINAL" if post["cagr"] >= 0.025
        else "WEAK"
    )

    checks = {
        "positive_primary_pre_post": bool(primary["cagr"] > 0 and pre["cagr"] > 0 and post["cagr"] > 0),
        "post2023_cagr_ge_2_5pct": bool(post["cagr"] >= 0.025),
        "primary_maxdd_lt_10pct": bool(primary["max_drawdown"] > -0.10),
        "no_hard_margin_failure": bool(not primary["hard_margin_failure"]),
        "intrahour_margin_ratio_ge_10pct": bool(primary["min_intrahour_collateral_ratio"] >= LOW_HEADROOM),
        "fee25_positive_primary_post": bool(primary25["cagr"] > 0 and post25["cagr"] > 0),
        "adverse_funding_primary_positive": bool(adverse["cagr"] > 0),
        "realized_beats_zero_by_1pp": bool(primary["cagr"] >= zero["cagr"] + 0.01),
        "completed_years_majority_positive": bool(majority_years),
        "largest_positive_year_share_lt_50pct": bool(np.isnan(largest_year_share) or largest_year_share < 0.50),
    }

    if primary["cagr"] <= 0 or post["cagr"] <= 0 or bool(primary["hard_margin_failure"]):
        decision = "IMPLEMENTATION_FAIL"
    elif all(checks.values()):
        decision = "IMPLEMENTATION_PROMISING"
    else:
        decision = "IMPLEMENTATION_MIXED"

    state = {
        "status": "PASS",
        "engine_version": VERSION,
        "protocol": PROTOCOL,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_status": "HISTORICAL_IMPLEMENTATION_STUDY_NOT_OOS_PASS",
        "research_freeze": {
            "symbol": SYMBOL,
            "capital_split_spot": 0.50,
            "capital_split_futures_collateral": 0.50,
            "equal_btc_quantity": True,
            "rebalance": "UTC_CALENDAR_MONTH_END",
            "fee_bps_per_leg": [5, 10, 25],
            "funding_treatments": list(FUNDING_TREATMENTS),
            "low_headroom_ratio": LOW_HEADROOM,
            "capital_hurdles": list(HURDLES),
        },
        "source_audit": audit,
        "decision": decision,
        "capital_efficiency_post2023": capital_eff,
        "checks": checks,
        "completed_calendar_years": completed_years,
        "largest_positive_year_share": largest_year_share,
        "baseline_primary": {
            "cagr": float(primary["cagr"]),
            "max_drawdown": float(primary["max_drawdown"]),
            "ending_multiple": float(primary["ending_multiple"]),
            "min_intrahour_collateral_ratio": float(primary["min_intrahour_collateral_ratio"]),
            "total_funding_contribution": float(primary["total_funding_contribution"]),
            "total_pair_price_basis_pnl": float(primary["total_pair_price_basis_pnl"]),
            "total_execution_cost": float(primary["total_execution_cost"]),
        },
        "baseline_post2023": {
            "cagr": float(post["cagr"]),
            "max_drawdown": float(post["max_drawdown"]),
            "ending_multiple": float(post["ending_multiple"]),
        },
        "outputs": [
            "r003_e002_source_audit.json",
            "r003_e002_hourly_clean.csv",
            "r003_e002_basis_diagnostics.csv",
            "r003_e002_metrics.csv",
            "r003_e002_margin_diagnostics.csv",
            "r003_e002_primary_hourly_nav.csv",
            "r003_e002_yearly.csv",
            "r003_e002_summary.md",
            "r003_e002_run_state.json",
        ],
    }
    (outdir / "r003_e002_run_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    def pct(x):
        return f"{float(x):.2%}"

    md = "# R003-E002 Self-Financing BTC Cash-and-Carry — Raw Output v0.1\n\n"
    md += "**Status:** historical implementation study only; not production/OOS PASS.\n\n"
    md += f"- Data gate: **{audit['status']}**\n"
    md += f"- Decision: **{decision}**\n"
    md += f"- POST_2023 capital efficiency: **{capital_eff}**\n"
    md += "- Canonical portfolio: **50% BTC spot + 50% USDT futures collateral, equal-BTC short perpetual, month-end rebalance**\n"
    md += "- Baseline all-in execution cost: **10 bps per traded notional per leg**\n\n"
    md += "| Slice | CAGR | Max DD | Ending | Funding cash | Pair/basis P&L | Exec cost | Min intrahour collateral |\n"
    md += "|---|---:|---:|---:|---:|---:|---:|---:|\n"
    for s in ("PRIMARY_2020", "PRE_2023", "POST_2023"):
        r = km(s)
        md += (
            f"| {s} | {pct(r['cagr'])} | {pct(r['max_drawdown'])} | {float(r['ending_multiple']):.3f}x "
            f"| {float(r['total_funding_contribution']):.4f} | {float(r['total_pair_price_basis_pnl']):.4f} "
            f"| {float(r['total_execution_cost']):.4f} | {pct(r['min_intrahour_collateral_ratio'])} |\n"
        )
    md += "\n## Stress\n\n"
    md += f"- PRIMARY_2020 CAGR at 25 bps/leg: **{pct(primary25['cagr'])}**\n"
    md += f"- POST_2023 CAGR at 25 bps/leg: **{pct(post25['cagr'])}**\n"
    md += f"- PRIMARY_2020 adverse-funding CAGR: **{pct(adverse['cagr'])}**\n"
    md += f"- PRIMARY_2020 zero-funding CAGR: **{pct(zero['cagr'])}**\n"
    md += "\nThis is a fully funded research implementation, not a claim that exchange/custody/stablecoin risk is removed.\n"
    (outdir / "r003_e002_summary.md").write_text(md, encoding="utf-8")
    print(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    try:
        run(args.outdir)
    except Exception as e:
        state = {
            "status": "SOURCE_OR_ENGINE_ERROR",
            "engine_version": VERSION,
            "protocol": PROTOCOL,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "error_type": type(e).__name__,
            "error": str(e),
        }
        (args.outdir / "r003_e002_run_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
