from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

VERSION = "0.1"
EXPERIMENT = "SC001-E001"
PROTOCOL = "sc001-e001-pretest-freeze-v0.1"

DOWNLOAD = Path("/storage/emulated/0/Download")
R003_WS = DOWNLOAD / "R003_E002_WORKSPACE"
CACHE_DIR = R003_WS / "_cache"
CACHE_ZIP = R003_WS / "_cache_bundle.zip"
SNAPSHOT_JSON = R003_WS / "snapshot.json"
OUTDIR = DOWNLOAD / "SC001_E001_RESULTS"

FROZEN_START = pd.Timestamp("2020-01-01 00:00:00", tz="UTC")
FROZEN_END_OPEN = pd.Timestamp("2026-09-09 19:00:00", tz="UTC")
DEV_END = pd.Timestamp("2022-12-31 23:59:59.999999999", tz="UTC")
VAL_START = pd.Timestamp("2023-01-01 00:00:00", tz="UTC")
VAL_END = pd.Timestamp("2024-12-31 23:59:59.999999999", tz="UTC")
FINAL_START = pd.Timestamp("2025-01-01 00:00:00", tz="UTC")
HOURS_PER_YEAR = 365.25 * 24.0

K_PRIMARY = 2.00
COST_TRACKS = {
    "LOW": {"fee_side": 0.0005, "exec_side": 0.0001},
    "BASE": {"fee_side": 0.0005, "exec_side": 0.0003},
    "STRESS": {"fee_side": 0.0010, "exec_side": 0.0005},
}
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 1003


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def atomic_json(path: Path, obj) -> None:
    atomic_text(path, json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def source_identity() -> dict:
    out = {
        "experiment": EXPERIMENT,
        "protocol": PROTOCOL,
        "frozen_start": FROZEN_START.isoformat(),
        "frozen_end_open": FROZEN_END_OPEN.isoformat(),
        "cache_dir_exists": CACHE_DIR.exists(),
        "cache_zip_exists": CACHE_ZIP.exists(),
        "snapshot_json_exists": SNAPSHOT_JSON.exists(),
    }
    if SNAPSHOT_JSON.exists():
        raw = SNAPSHOT_JSON.read_bytes()
        out["snapshot_sha256"] = sha256_bytes(raw)
        try:
            out["snapshot"] = json.loads(raw.decode("utf-8"))
        except Exception:
            out["snapshot_parse_error"] = True
    if CACHE_ZIP.exists():
        out["cache_zip_sha256"] = sha256_bytes(CACHE_ZIP.read_bytes())
        out["cache_zip_size"] = CACHE_ZIP.stat().st_size
    return out


def _folder_pages(label: str):
    folder = CACHE_DIR / label
    return sorted(folder.glob("page_*.json.gz")) if folder.exists() else []


def _zip_members(label: str):
    if not CACHE_ZIP.exists():
        return []
    suffix = f"_cache/{label}/"
    with zipfile.ZipFile(CACHE_ZIP, "r") as zf:
        return sorted(
            n for n in zf.namelist()
            if suffix in n and n.endswith(".json.gz") and "/page_" in n
        )


def load_cached_json_pages(label: str):
    pages, hashes, mode = [], [], None
    folder_pages = _folder_pages(label)
    if folder_pages:
        mode = "folder"
        for p in folder_pages:
            raw = gzip.decompress(p.read_bytes())
            pages.append(json.loads(raw.decode("utf-8")))
            hashes.append(sha256_bytes(raw))
    else:
        members = _zip_members(label)
        if members:
            mode = "zip"
            with zipfile.ZipFile(CACHE_ZIP, "r") as zf:
                for name in members:
                    raw = gzip.decompress(zf.read(name))
                    pages.append(json.loads(raw.decode("utf-8")))
                    hashes.append(sha256_bytes(raw))
    if not pages:
        raise FileNotFoundError(
            f"No cached pages for {label}. Expected {CACHE_DIR / label} or {CACHE_ZIP}."
        )
    return pages, hashes, mode


def load_futures_ohlc():
    pages, hashes, mode = load_cached_json_pages("futures-contract")
    rows, raw_count = [], 0
    for page in pages:
        if not isinstance(page, list):
            raise ValueError("futures-contract cached page is not a list")
        for r in page:
            if not isinstance(r, list) or len(r) < 7:
                continue
            raw_count += 1
            try:
                rows.append({
                    "open_time": pd.to_datetime(int(r[0]), unit="ms", utc=True),
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "close_time": pd.to_datetime(int(r[6]), unit="ms", utc=True),
                })
            except Exception:
                continue
    if not rows:
        raise ValueError("No usable futures-contract rows")
    df = pd.DataFrame(rows).dropna().sort_values("open_time").drop_duplicates("open_time", keep="last").reset_index(drop=True)
    df = df[(df.open_time >= FROZEN_START) & (df.open_time <= FROZEN_END_OPEN)].copy()
    if df.empty:
        raise ValueError("No futures rows inside frozen E001 window")
    if (df[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("Non-positive futures OHLC found")
    return df, {
        "source_mode": mode,
        "page_hashes": hashes,
        "raw_rows_scanned": raw_count,
        "retained_rows": int(len(df)),
        "start": df.open_time.iloc[0].isoformat(),
        "end": df.open_time.iloc[-1].isoformat(),
    }


def load_funding():
    pages, hashes, mode = load_cached_json_pages("funding")
    rows, raw_count = [], 0
    for page in pages:
        if not isinstance(page, list):
            raise ValueError("funding cached page is not a list")
        for r in page:
            if not isinstance(r, dict) or "fundingTime" not in r or "fundingRate" not in r:
                continue
            raw_count += 1
            try:
                ts = pd.to_datetime(int(r["fundingTime"]), unit="ms", utc=True)
                rate = float(r["fundingRate"])
                mp = r.get("markPrice", "")
                mark = float(mp) if str(mp).strip() not in ("", "None", "nan") else np.nan
                rows.append({"funding_time": ts, "funding_rate": rate, "mark_price": mark})
            except Exception:
                continue
    if not rows:
        raise ValueError("No usable funding rows")
    df = pd.DataFrame(rows).dropna(subset=["funding_time", "funding_rate"]).sort_values("funding_time").drop_duplicates("funding_time", keep="last").reset_index(drop=True)
    end_close = FROZEN_END_OPEN + pd.Timedelta(hours=1)
    df = df[(df.funding_time >= FROZEN_START) & (df.funding_time <= end_close)].copy()
    return df, {
        "source_mode": mode,
        "page_hashes": hashes,
        "raw_rows_scanned": raw_count,
        "retained_rows": int(len(df)),
        "start": df.funding_time.iloc[0].isoformat() if len(df) else None,
        "end": df.funding_time.iloc[-1].isoformat() if len(df) else None,
    }


def audit_bars(df: pd.DataFrame) -> dict:
    gaps = df.open_time.diff().dropna() / pd.Timedelta(hours=1)
    expected = int(round((df.open_time.iloc[-1] - df.open_time.iloc[0]) / pd.Timedelta(hours=1))) + 1
    return {
        "rows": int(len(df)),
        "expected_rows": expected,
        "coverage": float(len(df) / expected),
        "duplicates_after_dedup": int(df.open_time.duplicated().sum()),
        "monotonic": bool(df.open_time.is_monotonic_increasing),
        "max_gap_hours": float(gaps.max()) if len(gaps) else 0.0,
        "non_1h_gap_count": int((gaps != 1.0).sum()),
        "close_after_open": bool((df.close_time > df.open_time).all()),
        "start_exact": bool(df.open_time.iloc[0] == FROZEN_START),
        "end_exact": bool(df.open_time.iloc[-1] == FROZEN_END_OPEN),
    }


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    z = df.copy()
    z["r"] = z.close.pct_change(fill_method=None)
    z["sigma24"] = z.r.shift(1).rolling(24, min_periods=24).std(ddof=1)
    prior_close = z.close.shift(1)
    z["ret90_prior"] = prior_close / z.close.shift(2161) - 1.0
    z["rv30_prior"] = z.r.shift(1).rolling(720, min_periods=720).std(ddof=1) * math.sqrt(HOURS_PER_YEAR)
    z["high90_prior"] = z.close.shift(1).rolling(2160, min_periods=2160).max()
    z["dd90_prior"] = prior_close / z.high90_prior - 1.0
    z["directional_regime"] = np.select([z.ret90_prior > 0.20, z.ret90_prior < -0.20], ["BULL", "BEAR"], default="SIDEWAYS")
    z["vol_regime"] = np.select([z.rv30_prior < 0.40, z.rv30_prior > 0.80], ["LOW_VOL", "HIGH_VOL"], default="MID_VOL")
    z["crisis_regime"] = np.where(z.dd90_prior <= -0.20, "CRISIS", "NON_CRISIS")
    return z


def split_name(ts: pd.Timestamp) -> str:
    if ts <= DEV_END:
        return "DEVELOPMENT"
    if VAL_START <= ts <= VAL_END:
        return "VALIDATION"
    if ts >= FINAL_START:
        return "FINAL"
    return "OTHER"


def funding_for_trade(funding, entry_time, exit_time, side, entry_price):
    x = funding[(funding.funding_time > entry_time) & (funding.funding_time <= exit_time)]
    total, missing_mark = 0.0, 0
    for row in x.itertuples(index=False):
        ratio = 1.0
        if np.isfinite(row.mark_price) and row.mark_price > 0 and entry_price > 0:
            ratio = float(row.mark_price / entry_price)
        else:
            missing_mark += 1
        total += -side * float(row.funding_rate) * ratio
    return float(total), int(len(x)), int(missing_mark)


def generate_trades(df, funding, k, delay_hours=0):
    z = add_features(df)
    by_time = {t: i for i, t in enumerate(z.open_time)}
    trades, skipped_gap, signals, same_bar = [], 0, 0, 0
    for _, row in z.iterrows():
        r, s = row.r, row.sigma24
        if not np.isfinite(r) or not np.isfinite(s) or s <= 0:
            continue
        side = 1 if r <= -k * s else -1 if r >= k * s else 0
        if side == 0:
            continue
        signals += 1
        entry_time = row.open_time + pd.Timedelta(hours=1 + delay_hours)
        j = by_time.get(entry_time)
        if j is None:
            skipped_gap += 1
            continue
        erow = z.iloc[j]
        if entry_time <= row.open_time:
            same_bar += 1
            continue
        entry_price, exit_price = float(erow.open), float(erow.close)
        gross = side * (exit_price / entry_price - 1.0)
        fund_ret, fund_events, missing_mark = funding_for_trade(funding, entry_time, erow.close_time, side, entry_price)
        trades.append({
            "signal_open_time": row.open_time,
            "signal_close_time": row.close_time,
            "entry_time": entry_time,
            "exit_time": erow.close_time,
            "side": "LONG" if side == 1 else "SHORT",
            "side_num": side,
            "shock_return": float(r),
            "sigma24": float(s),
            "zscore_abs": float(abs(r / s)),
            "entry_open": entry_price,
            "exit_close": exit_price,
            "gross_return": float(gross),
            "funding_return": fund_ret,
            "funding_events": fund_events,
            "funding_events_missing_mark": missing_mark,
            "directional_regime": row.directional_regime,
            "vol_regime": row.vol_regime,
            "crisis_regime": row.crisis_regime,
            "split": split_name(entry_time),
            "year": int(entry_time.year),
        })
    t = pd.DataFrame(trades)
    return t, {"k": k, "delay_hours": delay_hours, "signals": signals, "executed": int(len(t)), "skipped_gap": skipped_gap, "same_bar_violations": same_bar}


def apply_costs(trades, track):
    c = COST_TRACKS[track]
    x = trades.copy()
    x["cost_track"] = track
    x["fee_drag"] = 2.0 * c["fee_side"]
    x["execution_proxy_drag"] = 2.0 * c["exec_side"]
    x["net_return"] = x.gross_return + x.funding_return - x.fee_drag - x.execution_proxy_drag
    return x


def longest_losing_streak(vals):
    cur = best = 0
    for v in vals:
        if v < 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return int(best)


def max_drawdown(vals):
    nav = np.r_[1.0, np.cumprod(1.0 + np.asarray(vals, dtype=float))]
    peak = np.maximum.accumulate(nav)
    return float((nav / peak - 1.0).min())


def subset_metrics(x, a, b):
    n = int(len(x))
    days = max((b - a).total_seconds() / 86400.0, 1.0 / 24.0)
    years = days / 365.25
    if n:
        net, gross = x.net_return.to_numpy(float), x.gross_return.to_numpy(float)
        ending = float(np.prod(1.0 + net))
        total = ending - 1.0
        cagr = float(ending ** (1.0 / years) - 1.0) if ending > 0 else np.nan
        mdd = max_drawdown(net)
        calmar = cagr / abs(mdd) if np.isfinite(cagr) and mdd < 0 else np.nan
        wins, losses = net[net > 0], net[net < 0]
        pf = float(wins.sum() / abs(losses.sum())) if len(losses) and abs(losses.sum()) > 0 else np.inf if len(wins) else np.nan
        q = [float(np.quantile(net, v)) for v in (0.05, 0.25, 0.50, 0.75, 0.95)]
    else:
        net = gross = np.array([])
        ending, total, cagr, mdd, calmar, pf = 1.0, 0.0, 0.0, 0.0, np.nan, np.nan
        q = [np.nan] * 5
    total_hours = max(int(round(days * 24.0)), 1)
    hourly = np.zeros(total_hours)
    for row in x.itertuples(index=False):
        idx = int((pd.Timestamp(row.entry_time) - a) / pd.Timedelta(hours=1))
        if 0 <= idx < total_hours:
            hourly[idx] += float(row.net_return)
    mu = float(hourly.mean())
    sd = float(hourly.std(ddof=1)) if len(hourly) > 1 else np.nan
    downside = hourly[hourly < 0]
    dsd = float(downside.std(ddof=1)) if len(downside) > 1 else np.nan
    sharpe = mu / sd * math.sqrt(HOURS_PER_YEAR) if np.isfinite(sd) and sd > 0 else np.nan
    sortino = mu / dsd * math.sqrt(HOURS_PER_YEAR) if np.isfinite(dsd) and dsd > 0 else np.nan
    return {
        "trade_count": n,
        "total_return": total,
        "ending_multiple": ending,
        "annualized_return": cagr,
        "max_drawdown": mdd,
        "calmar": calmar,
        "sharpe_hourly_zero_filled": sharpe,
        "sortino_hourly_zero_filled": sortino,
        "profit_factor": pf,
        "win_rate": float((net > 0).mean()) if n else np.nan,
        "avg_gross_trade": float(gross.mean()) if n else np.nan,
        "median_gross_trade": float(np.median(gross)) if n else np.nan,
        "avg_net_trade": float(net.mean()) if n else np.nan,
        "median_net_trade": float(np.median(net)) if n else np.nan,
        "q05_net": q[0], "q25_net": q[1], "q50_net": q[2], "q75_net": q[3], "q95_net": q[4],
        "trades_per_day": n / days,
        "turnover_nav_units": 2.0 * n,
        "fee_drag_sum": float(x.fee_drag.sum()) if n else 0.0,
        "execution_proxy_drag_sum": float(x.execution_proxy_drag.sum()) if n else 0.0,
        "funding_contribution_sum": float(x.funding_return.sum()) if n else 0.0,
        "longest_losing_streak": longest_losing_streak(net) if n else 0,
        "exposure": n / total_hours,
        "capital_utilization": n / total_hours,
        "long_trades": int((x.side == "LONG").sum()) if n else 0,
        "short_trades": int((x.side == "SHORT").sum()) if n else 0,
    }


def period_bounds(name):
    end = FROZEN_END_OPEN + pd.Timedelta(hours=1)
    if name == "FULL": return FROZEN_START, end
    if name == "DEVELOPMENT": return FROZEN_START, pd.Timestamp("2023-01-01", tz="UTC")
    if name == "VALIDATION": return VAL_START, pd.Timestamp("2025-01-01", tz="UTC")
    if name == "FINAL": return FINAL_START, end
    if name == "OOS": return VAL_START, end
    raise ValueError(name)


def metrics_table(trades, variant, k, delay):
    rows = []
    for track in COST_TRACKS:
        x = apply_costs(trades, track)
        for pname in ("FULL", "DEVELOPMENT", "VALIDATION", "FINAL", "OOS"):
            a, b = period_bounds(pname)
            g = x[(x.entry_time >= a) & (x.entry_time < b)].copy()
            rows.append({"variant": variant, "k": k, "delay_hours": delay, "cost_track": track, "period": pname, **subset_metrics(g, a, b)})
        for year in range(2020, 2027):
            a = pd.Timestamp(f"{year}-01-01", tz="UTC")
            b = pd.Timestamp(f"{year+1}-01-01", tz="UTC") if year < 2026 else FROZEN_END_OPEN + pd.Timedelta(hours=1)
            g = x[(x.entry_time >= a) & (x.entry_time < b)].copy()
            rows.append({"variant": variant, "k": k, "delay_hours": delay, "cost_track": track, "period": f"YEAR_{year}", **subset_metrics(g, a, b)})
    return pd.DataFrame(rows)


def regime_table(trades):
    x = apply_costs(trades, "BASE")
    x = x[x.entry_time >= VAL_START].copy()
    out = []
    for col in ("directional_regime", "vol_regime", "crisis_regime"):
        for label, g in x.groupby(col, dropna=False):
            losses = g.loc[g.net_return < 0, "net_return"].sum()
            pf = float(g.loc[g.net_return > 0, "net_return"].sum() / abs(losses)) if losses < 0 else np.inf
            out.append({"regime_type": col, "regime": str(label), "trade_count": int(len(g)), "net_pnl_sum": float(g.net_return.sum()), "avg_net_trade": float(g.net_return.mean()), "profit_factor": pf, "win_rate": float((g.net_return > 0).mean())})
    return pd.DataFrame(out)


def block_bootstrap_oos(trades):
    x = apply_costs(trades, "BASE")
    x = x[x.entry_time >= VAL_START].copy()
    start = VAL_START.normalize()
    end = (FROZEN_END_OPEN + pd.Timedelta(hours=1)).normalize()
    days = pd.date_range(start, end, freq="D", tz="UTC")
    week_starts = pd.Series(days - pd.to_timedelta(days.weekday, unit="D")).drop_duplicates().sort_values().tolist()
    x["week_start"] = x.entry_time.dt.normalize() - pd.to_timedelta(x.entry_time.dt.weekday, unit="D")
    agg = x.groupby("week_start").net_return.agg(["sum", "count"])
    sums = np.array([float(agg.loc[w, "sum"]) if w in agg.index else 0.0 for w in week_starts])
    counts = np.array([int(agg.loc[w, "count"]) if w in agg.index else 0 for w in week_starts])
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    vals, discarded, n = [], 0, len(week_starts)
    for _ in range(BOOTSTRAP_REPS):
        idx = rng.integers(0, n, size=n)
        c = counts[idx].sum()
        if c <= 0:
            discarded += 1
            continue
        vals.append(float(sums[idx].sum() / c))
    arr = np.asarray(vals)
    return {
        "status": "PASS" if len(arr) else "NO_VALID_DRAWS",
        "weeks": n,
        "replications_requested": BOOTSTRAP_REPS,
        "replications_used": int(len(arr)),
        "discarded_zero_trade_draws": discarded,
        "seed": BOOTSTRAP_SEED,
        "point_estimate_avg_net_trade": float(x.net_return.mean()) if len(x) else np.nan,
        "ci95_lower": float(np.quantile(arr, 0.025)) if len(arr) else np.nan,
        "ci95_upper": float(np.quantile(arr, 0.975)) if len(arr) else np.nan,
    }


def missed_variant(trades, frac, seed):
    rng = np.random.default_rng(seed)
    return trades.loc[rng.random(len(trades)) >= frac].copy().reset_index(drop=True)


def gate_eval(metrics, bootstrap, meta, audit):
    def row(variant, k, delay, track, period):
        m = metrics[(metrics.variant == variant) & np.isclose(metrics.k, k) & (metrics.delay_hours == delay) & (metrics.cost_track == track) & (metrics.period == period)]
        if len(m) != 1:
            raise KeyError((variant, k, delay, track, period, len(m)))
        return m.iloc[0]
    base_val = row("PRIMARY", 2.0, 0, "BASE", "VALIDATION")
    base_final = row("PRIMARY", 2.0, 0, "BASE", "FINAL")
    base_oos = row("PRIMARY", 2.0, 0, "BASE", "OOS")
    stress_oos = row("PRIMARY", 2.0, 0, "STRESS", "OOS")
    stress_final = row("PRIMARY", 2.0, 0, "STRESS", "FINAL")
    delayed = row("LATENCY_1H", 2.0, 1, "BASE", "OOS")
    k175 = row("K_1.75", 1.75, 0, "BASE", "OOS")
    k225 = row("K_2.25", 2.25, 0, "BASE", "OOS")
    miss10 = row("MISS_10", 2.0, 0, "BASE", "OOS")
    miss25 = row("MISS_25", 2.0, 0, "BASE", "OOS")
    yrs = [row("PRIMARY", 2.0, 0, "BASE", f"YEAR_{y}") for y in (2023, 2024, 2025)]
    pos = [r for r in yrs if r.total_return > 0]
    pos_sum = sum(float(r.total_return) for r in pos)
    largest_share = max([float(r.total_return) for r in pos], default=0.0) / pos_sum if pos_sum > 0 else np.nan
    gates = {
        "D_data_integrity": bool(audit["duplicates_after_dedup"] == 0 and audit["monotonic"] and audit["close_after_open"] and audit["start_exact"] and audit["end_exact"] and meta["primary"]["same_bar_violations"] == 0),
        "N_net_edge": bool(base_val.avg_net_trade >= 0.0005 and base_final.avg_net_trade >= 0.0005),
        "C_cost_robustness": bool(stress_oos.avg_net_trade > 0 and stress_final.avg_net_trade > 0),
        "S_bootstrap": bool(bootstrap.get("ci95_lower", -np.inf) > 0),
        "PF_trade_quality": bool(base_oos.profit_factor >= 1.10 and base_oos.trade_count >= 100 and base_final.trade_count >= 30),
        "L_latency": bool(delayed.avg_net_trade > 0),
        "P_parameter_neighborhood": bool(k175.avg_net_trade > 0 and k225.avg_net_trade > 0),
        "M_missed_trade": bool(miss10.avg_net_trade > 0 and miss25.avg_net_trade > 0),
        "Y_temporal_breadth": bool(len(pos) >= 2 and np.isfinite(largest_share) and largest_share <= 0.60),
    }
    if all(gates.values()):
        verdict = "PROMISING_SCREEN"
    else:
        hard_fail = (
            not gates["D_data_integrity"]
            or base_oos.avg_net_trade <= 0
            or base_final.avg_net_trade <= 0
            or stress_oos.avg_net_trade <= 0
            or (bootstrap.get("ci95_lower", -np.inf) <= 0 and base_oos.avg_net_trade < 0.0005)
        )
        verdict = "FAIL" if hard_fail else "WEAK"
    details = {
        "gates": gates,
        "completed_oos_positive_years": len(pos),
        "largest_positive_completed_year_share": largest_share,
        "base_validation_avg_net_trade": float(base_val.avg_net_trade),
        "base_final_avg_net_trade": float(base_final.avg_net_trade),
        "base_oos_avg_net_trade": float(base_oos.avg_net_trade),
        "base_oos_profit_factor": float(base_oos.profit_factor),
        "base_oos_trade_count": int(base_oos.trade_count),
        "base_final_trade_count": int(base_final.trade_count),
        "stress_oos_avg_net_trade": float(stress_oos.avg_net_trade),
        "stress_final_avg_net_trade": float(stress_final.avg_net_trade),
        "latency_oos_avg_net_trade": float(delayed.avg_net_trade),
        "k175_oos_avg_net_trade": float(k175.avg_net_trade),
        "k225_oos_avg_net_trade": float(k225.avg_net_trade),
        "miss10_oos_avg_net_trade": float(miss10.avg_net_trade),
        "miss25_oos_avg_net_trade": float(miss25.avg_net_trade),
        "bootstrap_ci95_lower": bootstrap.get("ci95_lower"),
        "bootstrap_ci95_upper": bootstrap.get("ci95_upper"),
    }
    return details, verdict


def write_summary(verdict, gd, audit, metrics, bootstrap, source_meta):
    def pick(track, period):
        return metrics[(metrics.variant == "PRIMARY") & np.isclose(metrics.k, 2.0) & (metrics.delay_hours == 0) & (metrics.cost_track == track) & (metrics.period == period)].iloc[0]
    lines = [
        "# SC001-E001 Extreme-Move Mean-Reversion — Results v0.1",
        "",
        f"**Verdict:** `{verdict}`  ",
        "**Classification:** short-horizon intraday research; NOT true scalping  ",
        f"**Protocol:** `{PROTOCOL}`  ",
        "**No real-money authorization.**",
        "",
        "## Data",
        f"- Bars: {audit['rows']:,} / expected {audit['expected_rows']:,}",
        f"- Coverage: {audit['coverage']:.6%}",
        f"- Max gap: {audit['max_gap_hours']:.1f}h",
        f"- Source mode: {source_meta['futures']['source_mode']}",
        f"- Frozen window: {FROZEN_START} -> {FROZEN_END_OPEN}",
        "",
        "## Mandatory gates",
    ]
    for k, v in gd["gates"].items():
        lines.append(f"- {k}: **{'PASS' if v else 'FAIL'}**")
    lines += ["", "## Key metrics"]
    for period in ("DEVELOPMENT", "VALIDATION", "FINAL", "OOS"):
        b, s = pick("BASE", period), pick("STRESS", period)
        lines.append(f"- {period}: BASE avg net/trade {b.avg_net_trade*10000:.2f} bps, PF {b.profit_factor:.3f}, trades {int(b.trade_count)}, total {b.total_return:.2%}; STRESS avg net/trade {s.avg_net_trade*10000:.2f} bps")
    lines += [
        "",
        "## Bootstrap",
        f"- OOS BASE mean net/trade: {bootstrap.get('point_estimate_avg_net_trade', np.nan)*10000:.2f} bps",
        f"- 95% week-block CI: [{bootstrap.get('ci95_lower', np.nan)*10000:.2f}, {bootstrap.get('ci95_upper', np.nan)*10000:.2f}] bps",
        "",
        "## Interpretation boundary",
        "Historical evidence only. This cannot modify R009/R003/R010/S002 and cannot authorize live trading.",
        "If E001 is FAIL/WEAK, do not rescue it with new filters. A distinct hypothesis must receive a new experiment ID.",
    ]
    atomic_text(OUTDIR / "sc001_e001_summary.md", "\n".join(lines) + "\n")


def self_test():
    idx = pd.date_range("2024-01-01", periods=40, freq="1h", tz="UTC")
    px = np.full(40, 100.0); px[25] = 90.0; px[26] = 91.0
    d = pd.DataFrame({
        "open_time": idx,
        "open": np.r_[100.0, px[:-1]],
        "high": np.maximum(np.r_[100.0, px[:-1]], px) * 1.001,
        "low": np.minimum(np.r_[100.0, px[:-1]], px) * 0.999,
        "close": px,
        "close_time": idx + pd.Timedelta(hours=1) - pd.Timedelta(milliseconds=1),
    })
    f = pd.DataFrame(columns=["funding_time", "funding_rate", "mark_price"])
    t, meta = generate_trades(d, f, 2.0, 0)
    if meta["same_bar_violations"] != 0 or len(t) == 0 or not (t.entry_time > t.signal_open_time).all():
        raise AssertionError("causality self-test failed")


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    self_test()
    print("=" * 78)
    print("SC001-E001 BTCUSDT 1H EXTREME-MOVE MEAN-REVERSION — FROZEN TEST v0.1")
    print("Short-horizon intraday research; NOT true scalping")
    print("No tuning / no live trading")
    print("=" * 78)

    sid = source_identity()
    bars, fut_meta = load_futures_ohlc()
    funding, fund_meta = load_funding()
    audit = audit_bars(bars)
    source_meta = {"futures": fut_meta, "funding": fund_meta}
    atomic_json(OUTDIR / "sc001_e001_source_identity.json", sid)
    atomic_json(OUTDIR / "sc001_e001_data_audit.json", {"bars": audit, "sources": source_meta})

    print(f"Bars retained: {len(bars):,}")
    print(f"Coverage: {audit['coverage']:.6%}")
    print(f"Funding rows: {len(funding):,}")
    print(f"Source mode: {fut_meta['source_mode']}")

    if not (audit["duplicates_after_dedup"] == 0 and audit["monotonic"] and audit["close_after_open"] and audit["start_exact"] and audit["end_exact"]):
        state = {"status": "FAIL", "reason": "DATA_INTEGRITY_GATE_FAILED_BEFORE_PNL", "audit": audit, "source_identity": sid}
        atomic_json(OUTDIR / "sc001_e001_run_state.json", state)
        print(json.dumps(state, indent=2, default=str))
        return

    primary, pmeta = generate_trades(bars, funding, 2.0, 0)
    latency, lmeta = generate_trades(bars, funding, 2.0, 1)
    k175, k175meta = generate_trades(bars, funding, 1.75, 0)
    k225, k225meta = generate_trades(bars, funding, 2.25, 0)
    miss10 = missed_variant(primary, 0.10, 1001)
    miss25 = missed_variant(primary, 0.25, 1002)
    meta = {
        "primary": pmeta,
        "latency": lmeta,
        "k175": k175meta,
        "k225": k225meta,
        "miss10_executed": int(len(miss10)),
        "miss25_executed": int(len(miss25)),
    }

    metrics = pd.concat([
        metrics_table(primary, "PRIMARY", 2.0, 0),
        metrics_table(latency, "LATENCY_1H", 2.0, 1),
        metrics_table(k175, "K_1.75", 1.75, 0),
        metrics_table(k225, "K_2.25", 2.25, 0),
        metrics_table(miss10, "MISS_10", 2.0, 0),
        metrics_table(miss25, "MISS_25", 2.0, 0),
    ], ignore_index=True)
    bootstrap = block_bootstrap_oos(primary)
    regimes = regime_table(primary)
    gd, verdict = gate_eval(metrics, bootstrap, meta, audit)

    apply_costs(primary, "BASE").to_csv(OUTDIR / "sc001_e001_primary_trades_base.csv", index=False)
    metrics.to_csv(OUTDIR / "sc001_e001_metrics.csv", index=False)
    regimes.to_csv(OUTDIR / "sc001_e001_regimes.csv", index=False)
    atomic_json(OUTDIR / "sc001_e001_bootstrap.json", bootstrap)
    write_summary(verdict, gd, audit, metrics, bootstrap, source_meta)

    state = {
        "status": "PASS" if verdict == "PROMISING_SCREEN" else "COMPLETE",
        "experiment": EXPERIMENT,
        "version": VERSION,
        "protocol": PROTOCOL,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "classification": "SHORT_HORIZON_INTRADAY_NOT_TRUE_SCALPING",
        "source_identity": sid,
        "source_meta": source_meta,
        "data_audit": audit,
        "variant_meta": meta,
        "bootstrap": bootstrap,
        "gate_details": gd,
        "outputs": [
            "sc001_e001_source_identity.json",
            "sc001_e001_data_audit.json",
            "sc001_e001_primary_trades_base.csv",
            "sc001_e001_metrics.csv",
            "sc001_e001_regimes.csv",
            "sc001_e001_bootstrap.json",
            "sc001_e001_summary.md",
            "sc001_e001_run_state.json",
        ],
    }
    atomic_json(OUTDIR / "sc001_e001_run_state.json", state)

    print("\n" + "=" * 78)
    print("SC001-E001 COMPLETE")
    print("=" * 78)
    print("Verdict:", verdict)
    for k, v in gd["gates"].items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    print(f"OOS BASE avg net/trade: {gd['base_oos_avg_net_trade']*10000:.2f} bps")
    print(f"FINAL BASE avg net/trade: {gd['base_final_avg_net_trade']*10000:.2f} bps")
    print(f"OOS STRESS avg net/trade: {gd['stress_oos_avg_net_trade']*10000:.2f} bps")
    print(f"OOS BASE PF: {gd['base_oos_profit_factor']:.3f}")
    print(f"OOS trades: {gd['base_oos_trade_count']}")
    print("Bootstrap 95% CI (bps):", f"[{bootstrap.get('ci95_lower', np.nan)*10000:.2f}, {bootstrap.get('ci95_upper', np.nan)*10000:.2f}]")
    print("Results:", OUTDIR)
    print("\nUpload these 3 files to ChatGPT:")
    print("1) sc001_e001_run_state.json")
    print("2) sc001_e001_summary.md")
    print("3) sc001_e001_metrics.csv")


if __name__ == "__main__":
    main()
