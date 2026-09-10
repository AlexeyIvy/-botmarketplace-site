"""R003-E003 forward paper tracker v0.2."""
from __future__ import annotations

import argparse
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

VERSION = "0.2"
PROTOCOL = "r003-e003-forward-paper-protocol-v0.1"
SYMBOL = "BTCUSDT"

INCEPTION = pd.Timestamp("2026-09-10 12:00:00", tz="UTC")
TREASURY_HURDLE = 0.0390
COMPENSATION_HURDLE = 0.0590

SPOT_URL = "https://data-api.binance.vision/api/v3/klines"
FUT_URL = "https://fapi.binance.com/fapi/v1/klines"
MARK_URL = "https://fapi.binance.com/fapi/v1/markPriceKlines"
FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
TREASURY_CSV_TEMPLATE = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?_format=csv&field_tdr_date_value={year}&page=&type=daily_treasury_bill_rates"

FEES = (0.0005, 0.0010, 0.0025)
BASE_FEE = 0.0010
FUNDING_TREATMENTS = ("REALIZED_FUNDING", "ZERO_FUNDING", "ADVERSE_FUNDING")
LOW_HEADROOM = 0.10
MIN_COVERAGE = 0.995
MAX_GAP_HOURS = 6.0
EPS = 1e-12
HOURS_PER_YEAR = 365.25 * 24.0


def get_json(url: str, params: dict):
    req = Request(
        url + "?" + urlencode(params),
        headers={"User-Agent": "botmarketplace-r003-e003-forward/0.2"},
    )
    with urlopen(req, timeout=90) as r:
        raw = r.read()
    return json.loads(raw.decode("utf-8"))


def fetch_klines(url: str, limit: int, label: str):
    start = int(INCEPTION.timestamp() * 1000)
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    rows = []
    last_open = None
    while True:
        obj = get_json(url, {"symbol": SYMBOL, "interval": "1h", "startTime": start, "limit": limit})
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
        return pd.DataFrame()
    x = pd.DataFrame(rows)
    out = pd.DataFrame({
        "open_time": pd.to_datetime(pd.to_numeric(x.iloc[:, 0]), unit="ms", utc=True),
        "open": pd.to_numeric(x.iloc[:, 1], errors="coerce"),
        "high": pd.to_numeric(x.iloc[:, 2], errors="coerce"),
        "low": pd.to_numeric(x.iloc[:, 3], errors="coerce"),
        "close": pd.to_numeric(x.iloc[:, 4], errors="coerce"),
        "close_time": pd.to_datetime(pd.to_numeric(x.iloc[:, 6]), unit="ms", utc=True),
    })
    out = out.dropna().sort_values("open_time").drop_duplicates("open_time", keep="last").reset_index(drop=True)
    if len(out) and (out[["open", "high", "low", "close"]] <= 0).any().any():
        raise RuntimeError(f"{label} contains non-positive retained prices")
    return out


def fetch_funding():
    start = int(INCEPTION.timestamp() * 1000)
    rows = []
    last = None
    while True:
        obj = get_json(FUNDING_URL, {"symbol": SYMBOL, "startTime": start, "limit": 1000})
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
        return pd.DataFrame(columns=["funding_time", "funding_rate", "published_mark_price", "rate_type"])
    x = pd.DataFrame(rows)
    x["funding_time"] = pd.to_datetime(pd.to_numeric(x["fundingTime"], errors="coerce"), unit="ms", utc=True)
    x["funding_rate"] = pd.to_numeric(x["fundingRate"], errors="coerce")
    x["published_mark_price"] = pd.to_numeric(x["markPrice"], errors="coerce") if "markPrice" in x else np.nan
    x["rate_type"] = x["rateType"].astype(str) if "rateType" in x else ""
    return x.dropna(subset=["funding_time", "funding_rate"]).sort_values("funding_time").drop_duplicates("funding_time", keep="last")[["funding_time", "funding_rate", "published_mark_price", "rate_type"]].reset_index(drop=True)


def build_common(spot, fut, mark):
    if spot.empty or fut.empty or mark.empty:
        return pd.DataFrame()
    s = spot.rename(columns={"open": "spot_open", "high": "spot_high", "low": "spot_low", "close": "spot_close", "close_time": "spot_close_time"})
    f = fut.rename(columns={"open": "fut_open", "high": "fut_high", "low": "fut_low", "close": "fut_close", "close_time": "fut_close_time"})
    m = mark.rename(columns={"open": "mark_open", "high": "mark_high", "low": "mark_low", "close": "mark_close", "close_time": "mark_close_time"})
    common = s.merge(f[["open_time", "fut_open", "fut_high", "fut_low", "fut_close", "fut_close_time"]], on="open_time", how="inner").merge(m[["open_time", "mark_open", "mark_high", "mark_low", "mark_close", "mark_close_time"]], on="open_time", how="inner")
    common = common[common["open_time"] >= INCEPTION].sort_values("open_time").drop_duplicates("open_time", keep="last").reset_index(drop=True)
    if common.empty:
        return common
    common["close_time"] = common[["spot_close_time", "fut_close_time", "mark_close_time"]].min(axis=1)
    common["mark_basis"] = common["mark_close"] / common["spot_close"] - 1.0
    common["contract_basis"] = common["fut_close"] / common["spot_close"] - 1.0
    return common


def align_funding(funding, common):
    if funding.empty or common.empty:
        return pd.DataFrame(columns=["funding_time", "funding_rate", "published_mark_price", "rate_type", "open_time", "close_time", "mark_close", "funding_mark"])
    base = common[["open_time", "close_time", "mark_close"]].sort_values("close_time")
    x = pd.merge_asof(funding.sort_values("funding_time"), base, left_on="funding_time", right_on="close_time", direction="backward", allow_exact_matches=True)
    x["funding_mark"] = x["published_mark_price"]
    bad = x["funding_mark"].isna() | (x["funding_mark"] <= 0)
    x.loc[bad, "funding_mark"] = x.loc[bad, "mark_close"]
    return x.dropna(subset=["open_time", "funding_mark"]).reset_index(drop=True)


def source_stats(df, label):
    if df.empty:
        return {"label": label, "rows": 0, "coverage": 0.0, "max_gap_hours": None}
    gaps = df["open_time"].diff().dt.total_seconds().div(3600).dropna()
    start = df["open_time"].iloc[0]
    end = df["open_time"].iloc[-1]
    expected = int(round((end - start).total_seconds() / 3600.0)) + 1
    return {"label": label, "rows": int(len(df)), "start": start.isoformat(), "end": end.isoformat(), "expected_hours": int(expected), "coverage": float(len(df) / expected) if expected > 0 else 0.0, "max_gap_hours": float(gaps.max()) if len(gaps) else 0.0}


def audit_data(spot, fut, mark, common, funding, funding_aligned):
    stats = {"spot": source_stats(spot, "spot"), "futures_contract": source_stats(fut, "futures_contract"), "futures_mark": source_stats(mark, "futures_mark")}
    if common.empty:
        common_coverage, common_gap, common_expected = 0.0, None, 0
    else:
        gaps = common["open_time"].diff().dt.total_seconds().div(3600).dropna()
        expected = int(round((common["open_time"].iloc[-1] - common["open_time"].iloc[0]).total_seconds() / 3600.0)) + 1
        common_expected = expected
        common_coverage = float(len(common) / expected) if expected > 0 else 0.0
        common_gap = float(gaps.max()) if len(gaps) else 0.0
    if len(common) < 24:
        status = "EARLY_FORWARD_SAMPLE"
    else:
        source_ok = all(s["coverage"] >= MIN_COVERAGE and (s["max_gap_hours"] is None or s["max_gap_hours"] <= MAX_GAP_HOURS) for s in stats.values())
        common_ok = common_coverage >= MIN_COVERAGE and (common_gap is None or common_gap <= MAX_GAP_HOURS)
        status = "PASS" if source_ok and common_ok else "DATA_ISSUE_DO_NOT_INTERPRET"
    return {"status": status, "symbol": SYMBOL, "fixed_inception_boundary": INCEPTION.isoformat(), "source_stats": stats, "common_rows": int(len(common)), "common_expected_hours": int(common_expected), "common_coverage": float(common_coverage), "common_max_gap_hours": common_gap, "funding_rows_downloaded": int(len(funding)), "funding_rows_aligned": int(len(funding_aligned)), "sources": {"spot": SPOT_URL, "futures_contract": FUT_URL, "futures_mark": MARK_URL, "funding": FUNDING_URL}}


def fetch_treasury_13w():
    frames = []
    current_year = datetime.now(timezone.utc).year
    for year in range(INCEPTION.year, current_year + 1):
        url = TREASURY_CSV_TEMPLATE.format(year=year)
        req = Request(url, headers={"User-Agent": "botmarketplace-r003-e003-forward/0.2"})
        with urlopen(req, timeout=60) as r:
            raw = r.read()
        df = pd.read_csv(io.StringIO(raw.decode("utf-8-sig")))
        cols = [str(c).strip() for c in df.columns]
        df.columns = cols
        date_col = next((c for c in cols if c.strip().lower() == "date"), None)
        rate_col = next((c for c in cols if "13 WEEKS" in c.upper() and "COUPON EQUIVALENT" in c.upper()), None)
        if date_col is None or rate_col is None:
            raise RuntimeError(f"Treasury CSV schema changed; columns={cols}")
        z = pd.DataFrame({"quote_date": pd.to_datetime(df[date_col], errors="coerce"), "rate_pct": pd.to_numeric(df[rate_col], errors="coerce")}).dropna()
        if z.empty:
            continue
        z["quote_date"] = z["quote_date"].dt.tz_localize("UTC")
        z["effective_time"] = z["quote_date"] + pd.Timedelta(days=1)
        frames.append(z)
    if not frames:
        raise RuntimeError("No Treasury 13-week bill data returned")
    return pd.concat(frames, ignore_index=True).sort_values("quote_date").drop_duplicates("quote_date", keep="last").reset_index(drop=True)


def build_dynamic_safe_reference(path, treasury):
    p = path[["close_time"]].copy().sort_values("close_time").reset_index(drop=True)
    t = treasury[["quote_date", "effective_time", "rate_pct"]].copy().sort_values("effective_time")
    m = pd.merge_asof(p, t, left_on="close_time", right_on="effective_time", direction="backward", allow_exact_matches=True)
    if m["rate_pct"].isna().iloc[0]:
        raise RuntimeError("No causally available Treasury 13-week quote at forward establishment")
    m["rate_pct"] = m["rate_pct"].ffill()
    m["quote_date"] = m["quote_date"].ffill()
    nav = np.ones(len(m), dtype=float)
    for i in range(1, len(m)):
        dt_hours = (m.loc[i, "close_time"] - m.loc[i - 1, "close_time"]).total_seconds() / 3600.0
        annual_rate = float(m.loc[i - 1, "rate_pct"]) / 100.0
        nav[i] = nav[i - 1] * (1.0 + annual_rate) ** (dt_hours / HOURS_PER_YEAR)
    m["safe_nav_dynamic_13w"] = nav
    m["annual_rate"] = m["rate_pct"] / 100.0
    m["date"] = m["close_time"].dt.date.astype(str)
    daily = m.groupby("date", as_index=False).tail(1)[["date", "close_time", "quote_date", "annual_rate", "safe_nav_dynamic_13w"]].reset_index(drop=True)
    return m, daily


def transform_rate(rate, treatment):
    if treatment == "REALIZED_FUNDING": return rate
    if treatment == "ZERO_FUNDING": return 0.0
    if treatment == "ADVERSE_FUNDING": return rate * 0.5 if rate >= 0 else rate * 2.0
    raise ValueError(treatment)


def max_drawdown(nav):
    s = pd.concat([pd.Series([1.0]), nav.reset_index(drop=True)], ignore_index=True)
    return float((s / s.cummax() - 1.0).min())


def simulate(common, funding_aligned, fee, treatment):
    z = common.copy().reset_index(drop=True)
    if len(z) < 2:
        raise ValueError("Need at least two closed common hourly bars")
    init_close = z.loc[0, "close_time"]
    fa = funding_aligned[(funding_aligned["funding_time"] > init_close) & (funding_aligned["close_time"] <= z["close_time"].iloc[-1])].copy()
    funding_map = {}
    for row in fa.itertuples(index=False):
        funding_map.setdefault(row.open_time, []).append((float(row.funding_rate), float(row.funding_mark), row.funding_time))
    n = len(z)
    month = z["open_time"].dt.to_period("M")
    is_month_end = np.zeros(n, dtype=bool)
    if n > 1:
        is_month_end[:-1] = month.iloc[:-1].to_numpy() != month.iloc[1:].to_numpy()
    spot0 = float(z.loc[0, "spot_close"])
    mark0 = float(z.loc[0, "mark_close"])
    q = 0.5 / spot0
    init_fee = fee * (q * spot0 + q * mark0)
    futures_cash = 0.5 - init_fee
    cum_funding = cum_pair = 0.0
    cum_fee_realized = init_fee
    spot_turn, perp_turn = q * spot0, q * mark0
    hard_margin_failure = futures_cash <= 0
    low_headroom_hours = 0
    min_close_ratio = futures_cash / max(q * mark0, EPS)
    min_intrahour_ratio = min_close_ratio
    rows = [{"open_time": z.loc[0, "open_time"], "close_time": z.loc[0, "close_time"], "spot_close": spot0, "mark_close": mark0, "fut_close": float(z.loc[0, "fut_close"]), "q_btc": q, "spot_value": q * spot0, "futures_cash": futures_cash, "nav_going_concern": q * spot0 + futures_cash, "pair_pnl": 0.0, "funding_cash": 0.0, "execution_fee": init_fee, "close_collateral_ratio": min_close_ratio, "intrahour_collateral_ratio": min_close_ratio, "rebalanced": True}]
    prev_spot, prev_mark = spot0, mark0
    for i in range(1, n):
        spot, mark, mark_high = float(z.loc[i, "spot_close"]), float(z.loc[i, "mark_close"]), float(z.loc[i, "mark_high"])
        intrahour_cash = futures_cash - q * (mark_high - prev_mark)
        intrahour_ratio = intrahour_cash / max(q * mark_high, EPS)
        min_intrahour_ratio = min(min_intrahour_ratio, intrahour_ratio)
        if intrahour_ratio < LOW_HEADROOM: low_headroom_hours += 1
        if intrahour_cash <= 0: hard_margin_failure = True
        pair_pnl = q * (spot - prev_spot) - q * (mark - prev_mark)
        futures_cash += -q * (mark - prev_mark)
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
                spot_trade, perp_trade = abs(dq) * spot, abs(dq) * mark
                reb_fee = fee * (spot_trade + perp_trade)
                futures_cash -= reb_fee
                cum_fee_realized += reb_fee
                spot_turn += spot_trade
                perp_turn += perp_trade
                q = q_target
                rebalanced = True
        funding_cash = 0.0
        for rate, fmark, _ in funding_map.get(z.loc[i, "open_time"], []):
            funding_cash += transform_rate(rate, treatment) * q * fmark
        futures_cash += funding_cash
        cum_funding += funding_cash
        close_ratio = futures_cash / max(q * mark, EPS)
        min_close_ratio = min(min_close_ratio, close_ratio)
        if close_ratio < LOW_HEADROOM: low_headroom_hours += 1
        if futures_cash <= 0: hard_margin_failure = True
        nav = q * spot + futures_cash
        rows.append({"open_time": z.loc[i, "open_time"], "close_time": z.loc[i, "close_time"], "spot_close": spot, "mark_close": mark, "fut_close": float(z.loc[i, "fut_close"]), "q_btc": q, "spot_value": q * spot, "futures_cash": futures_cash, "nav_going_concern": nav, "pair_pnl": pair_pnl, "funding_cash": funding_cash, "execution_fee": reb_fee, "close_collateral_ratio": close_ratio, "intrahour_collateral_ratio": intrahour_ratio, "rebalanced": rebalanced})
        prev_spot, prev_mark = spot, mark
    path = pd.DataFrame(rows)
    last = path.iloc[-1]
    exit_fee = fee * (abs(float(last["q_btc"])) * float(last["spot_close"]) + abs(float(last["q_btc"])) * float(last["mark_close"]))
    ending_gc = float(last["nav_going_concern"])
    ending_liq = ending_gc - exit_fee
    elapsed_years = max((path["close_time"].iloc[-1] - path["close_time"].iloc[0]).total_seconds() / (365.25 * 86400.0), 1.0 / HOURS_PER_YEAR)
    elapsed_days = elapsed_years * 365.25
    cagr = float(ending_liq ** (1.0 / elapsed_years) - 1.0) if ending_liq > 0 and elapsed_days >= 30 else np.nan
    path["net_return_gc"] = path["nav_going_concern"].pct_change(fill_method=None)
    path.loc[0, "net_return_gc"] = path.loc[0, "nav_going_concern"] - 1.0
    vol = float(path["net_return_gc"].iloc[1:].std(ddof=0) * math.sqrt(HOURS_PER_YEAR)) if len(path) >= 24 * 30 else np.nan
    mdd = max_drawdown(path["nav_going_concern"])
    calmar = cagr / abs(mdd) if pd.notna(cagr) and mdd < -EPS else np.nan
    hurdle_cum = (1.0 + TREASURY_HURDLE) ** elapsed_years - 1.0
    comp_cum = (1.0 + COMPENSATION_HURDLE) ** elapsed_years - 1.0
    strat_cum_liq = ending_liq - 1.0
    return path, {"elapsed_days": float(elapsed_days), "ending_multiple_going_concern": ending_gc, "ending_multiple_liquidation_adjusted": ending_liq, "cumulative_return_liquidation_adjusted": strat_cum_liq, "annualized_return_if_30d_plus": cagr, "annualized_vol_if_30d_plus": vol, "max_drawdown_going_concern": mdd, "calmar_if_30d_plus": calmar, "total_funding_contribution": float(cum_funding), "total_pair_price_basis_pnl": float(cum_pair), "realized_execution_cost": float(cum_fee_realized), "hypothetical_terminal_exit_cost": float(exit_fee), "total_cost_including_hypothetical_exit": float(cum_fee_realized + exit_fee), "spot_turnover_including_hypothetical_exit": float(spot_turn + abs(float(last["q_btc"])) * float(last["spot_close"])), "perp_turnover_including_hypothetical_exit": float(perp_turn + abs(float(last["q_btc"])) * float(last["mark_close"])), "min_close_collateral_ratio": float(min_close_ratio), "min_intrahour_collateral_ratio": float(min_intrahour_ratio), "low_headroom_count_proxy": int(low_headroom_hours), "hard_margin_failure": bool(hard_margin_failure), "funding_events_used": int(len(fa)), "month_end_rebalances_completed": int(max(0, path["rebalanced"].sum() - 1)), "treasury_hurdle_annual": TREASURY_HURDLE, "compensation_hurdle_annual": COMPENSATION_HURDLE, "treasury_hurdle_cumulative_same_elapsed_time": float(hurdle_cum), "compensation_hurdle_cumulative_same_elapsed_time": float(comp_cum), "excess_cumulative_vs_treasury": float(strat_cum_liq - hurdle_cum), "excess_cumulative_vs_compensation_floor": float(strat_cum_liq - comp_cum)}


def monthly_from_path(path):
    p = path.copy()
    p["month"] = p["close_time"].dt.to_period("M").astype(str)
    out, prev_nav = [], 1.0
    for month, g in p.groupby("month", sort=True):
        end_nav = float(g["nav_going_concern"].iloc[-1])
        ret = end_nav / prev_nav - 1.0 if prev_nav > 0 else np.nan
        out.append({"month": month, "return_going_concern": float(ret), "funding_cash": float(g["funding_cash"].sum()), "pair_pnl": float(g["pair_pnl"].sum()), "execution_fee": float(g["execution_fee"].sum()), "min_intrahour_collateral_ratio": float(g["intrahour_collateral_ratio"].min())})
        prev_nav = end_nav
    return pd.DataFrame(out)


def write_waiting(outdir, reason, audit=None):
    state = {"status": "WAITING_FOR_FORWARD_DATA", "engine_version": VERSION, "protocol": PROTOCOL, "fixed_inception_boundary": INCEPTION.isoformat(), "reason": reason, "created_at_utc": datetime.now(timezone.utc).isoformat()}
    if audit is not None: state["source_audit"] = audit
    (outdir / "r003_e003_run_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    (outdir / "r003_e003_summary.md").write_text("# R003-E003 Forward Paper\n\n**Status:** WAITING_FOR_FORWARD_DATA\n\nReason: " + reason + "\n", encoding="utf-8")
    print(json.dumps(state, indent=2))


def run(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    now = pd.Timestamp(datetime.now(timezone.utc))
    if now <= INCEPTION + pd.Timedelta(hours=1):
        write_waiting(outdir, "The first common 1h bar after the frozen inception boundary is not yet fully closed.")
        return
    spot = fetch_klines(SPOT_URL, 1000, "spot")
    fut = fetch_klines(FUT_URL, 1500, "futures-contract")
    mark = fetch_klines(MARK_URL, 1500, "futures-mark")
    funding = fetch_funding()
    common = build_common(spot, fut, mark)
    funding_aligned = align_funding(funding, common)
    audit = audit_data(spot, fut, mark, common, funding, funding_aligned)
    (outdir / "r003_e003_source_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if len(common) < 2:
        write_waiting(outdir, "Fewer than two fully closed common hourly bars are available.", audit)
        return
    if audit["status"] == "DATA_ISSUE_DO_NOT_INTERPRET":
        state = {"status": "DATA_ISSUE_DO_NOT_INTERPRET", "engine_version": VERSION, "protocol": PROTOCOL, "created_at_utc": datetime.now(timezone.utc).isoformat(), "fixed_inception_boundary": INCEPTION.isoformat(), "source_audit": audit}
        (outdir / "r003_e003_run_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
        return
    metric_rows, baseline_path, baseline_met = [], None, None
    for fee in FEES:
        for treatment in FUNDING_TREATMENTS:
            path, met = simulate(common, funding_aligned, fee, treatment)
            metric_rows.append({"fee_bps_per_leg": fee * 10000.0, "funding_treatment": treatment, **met})
            if abs(fee - BASE_FEE) < EPS and treatment == "REALIZED_FUNDING":
                baseline_path, baseline_met = path.copy(), met.copy()
    metrics = pd.DataFrame(metric_rows)
    assert baseline_path is not None and baseline_met is not None
    baseline_path.to_csv(outdir / "r003_e003_forward_hourly_nav.csv", index=False)
    treasury_status, treasury_error, treasury_latest_quote = "PASS", None, None
    dynamic_safe_cumulative = dynamic_safe_excess = np.nan
    try:
        treasury = fetch_treasury_13w()
        safe_hourly, safe_daily = build_dynamic_safe_reference(baseline_path, treasury)
        safe_daily.to_csv(outdir / "r003_e003_safe_hurdle_daily.csv", index=False)
        treasury_latest_quote = treasury["quote_date"].iloc[-1].isoformat()
        dynamic_safe_cumulative = float(safe_hourly["safe_nav_dynamic_13w"].iloc[-1] - 1.0)
        dynamic_safe_excess = float(baseline_met["cumulative_return_liquidation_adjusted"] - dynamic_safe_cumulative)
    except Exception as exc:
        treasury_status = "SAFE_HURDLE_SOURCE_INCOMPLETE"
        treasury_error = f"{type(exc).__name__}: {exc}"
        pd.DataFrame(columns=["date", "close_time", "quote_date", "annual_rate", "safe_nav_dynamic_13w"]).to_csv(outdir / "r003_e003_safe_hurdle_daily.csv", index=False)
    metrics["dynamic_treasury_status"] = treasury_status
    metrics["dynamic_treasury_cumulative"] = dynamic_safe_cumulative
    metrics["excess_cumulative_vs_dynamic_treasury"] = metrics["cumulative_return_liquidation_adjusted"] - dynamic_safe_cumulative if pd.notna(dynamic_safe_cumulative) else np.nan
    metrics.to_csv(outdir / "r003_e003_metrics.csv", index=False)
    pd.DataFrame([{"min_close_collateral_ratio": baseline_met["min_close_collateral_ratio"], "min_intrahour_collateral_ratio": baseline_met["min_intrahour_collateral_ratio"], "low_headroom_count_proxy": baseline_met["low_headroom_count_proxy"], "hard_margin_failure": baseline_met["hard_margin_failure"]}]).to_csv(outdir / "r003_e003_margin.csv", index=False)
    init_close = baseline_path["close_time"].iloc[0]
    fe = funding_aligned[(funding_aligned["funding_time"] > init_close) & (funding_aligned["close_time"] <= baseline_path["close_time"].iloc[-1])].copy()
    fe.to_csv(outdir / "r003_e003_funding_events.csv", index=False)
    monthly_from_path(baseline_path).to_csv(outdir / "r003_e003_monthly.csv", index=False)
    elapsed, funding_n, rebal_n = baseline_met["elapsed_days"], baseline_met["funding_events_used"], baseline_met["month_end_rebalances_completed"]
    mature = elapsed >= 365.0 and funding_n >= 1000 and rebal_n >= 10
    evidence_status = "MATURE_FORWARD_SAMPLE_REQUIRES_FORMAL_REVIEW" if mature else "FORWARD_EVIDENCE_ACCUMULATING"
    state = {"status": "PASS", "engine_version": VERSION, "protocol": PROTOCOL, "created_at_utc": datetime.now(timezone.utc).isoformat(), "evidence_status": evidence_status, "fixed_inception_boundary": INCEPTION.isoformat(), "initial_establishment_close": baseline_path["close_time"].iloc[0].isoformat(), "latest_forward_close": baseline_path["close_time"].iloc[-1].isoformat(), "safe_hurdles": {"treasury_13w_inception_annual": TREASURY_HURDLE, "treasury_plus_2pp_annual": COMPENSATION_HURDLE, "dynamic_treasury_status": treasury_status, "dynamic_treasury_latest_quote": treasury_latest_quote, "dynamic_treasury_cumulative": None if pd.isna(dynamic_safe_cumulative) else float(dynamic_safe_cumulative), "excess_cumulative_vs_dynamic_treasury": None if pd.isna(dynamic_safe_excess) else float(dynamic_safe_excess), "dynamic_treasury_error": treasury_error}, "evidence_thresholds": {"min_calendar_days": 365, "min_funding_events": 1000, "min_month_end_rebalances": 10}, "progress": {"elapsed_days": elapsed, "funding_events": funding_n, "month_end_rebalances": rebal_n, "mature": mature}, "baseline": baseline_met, "source_audit": audit, "outputs": ["r003_e003_run_state.json", "r003_e003_source_audit.json", "r003_e003_forward_hourly_nav.csv", "r003_e003_metrics.csv", "r003_e003_margin.csv", "r003_e003_funding_events.csv", "r003_e003_monthly.csv", "r003_e003_safe_hurdle_daily.csv", "r003_e003_summary.md"]}
    (outdir / "r003_e003_run_state.json").write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    def pct(v): return "n/a" if pd.isna(v) else f"{float(v):.2%}"
    md = "# R003-E003 Forward Paper — Current Snapshot\n\n"
    md += f"**Evidence status:** {evidence_status}\n\n"
    md += f"- Fixed inception boundary: **{INCEPTION.isoformat()}**\n"
    md += f"- Initial establishment close: **{baseline_path['close_time'].iloc[0]}**\n"
    md += f"- Latest forward close: **{baseline_path['close_time'].iloc[-1]}**\n"
    md += f"- Elapsed forward days: **{elapsed:.1f}**\n"
    md += f"- Realized funding events used: **{funding_n}**\n"
    md += f"- Completed month-end rebalances: **{rebal_n}**\n"
    md += f"- Liquidation-adjusted cumulative return: **{pct(baseline_met['cumulative_return_liquidation_adjusted'])}**\n"
    md += f"- Annualized return (only shown after 30d): **{pct(baseline_met['annualized_return_if_30d_plus'])}**\n"
    md += f"- Max DD, going-concern NAV: **{pct(baseline_met['max_drawdown_going_concern'])}**\n"
    md += f"- Min intrahour collateral ratio: **{pct(baseline_met['min_intrahour_collateral_ratio'])}**\n"
    md += f"- Funding contribution: **{baseline_met['total_funding_contribution']:.6f} NAV**\n"
    md += f"- Pair/basis P&L: **{baseline_met['total_pair_price_basis_pnl']:.6f} NAV**\n"
    md += f"- Treasury inception hurdle: **{TREASURY_HURDLE:.2%} annual**\n"
    md += f"- Treasury+2pp compensation floor: **{COMPENSATION_HURDLE:.2%} annual**\n"
    md += f"- Dynamic Treasury benchmark status: **{treasury_status}**\n"
    if pd.notna(dynamic_safe_cumulative):
        md += f"- Dynamic Treasury cumulative return over same forward time: **{dynamic_safe_cumulative:.4%}**\n"
        md += f"- R003 excess cumulative vs dynamic Treasury: **{dynamic_safe_excess:.4%}**\n"
    elif treasury_error:
        md += f"- Dynamic Treasury error: `{treasury_error}`\n"
    md += "\nNo terminal strategy conclusion is allowed before the frozen evidence thresholds are met.\n"
    (outdir / "r003_e003_summary.md").write_text(md, encoding="utf-8")
    print(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args()
    try:
        run(args.outdir)
    except Exception as exc:
        args.outdir.mkdir(parents=True, exist_ok=True)
        state = {"status": "SOURCE_OR_ENGINE_ERROR", "engine_version": VERSION, "protocol": PROTOCOL, "created_at_utc": datetime.now(timezone.utc).isoformat(), "error_type": type(exc).__name__, "error": str(exc)}
        (args.outdir / "r003_e003_run_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
