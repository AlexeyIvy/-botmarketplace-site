"""R003-X003 Bybit forward venue replication tracker v0.1."""
from __future__ import annotations

import argparse
import io
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import numpy as np
import pandas as pd

VERSION = "0.1"
PROTOCOL = "r003-x003-bybit-forward-venue-replication-protocol-v0.1"
SYMBOL = "BTCUSDT"
CATEGORY = "linear"
API = "https://api.bybit.com"

INCEPTION = pd.Timestamp("2026-09-10 16:00:00", tz="UTC")
TREASURY_HURDLE = 0.0390
COMPENSATION_HURDLE = 0.0590

KLINE = "/v5/market/kline"
MARK_KLINE = "/v5/market/mark-price-kline"
FUNDING = "/v5/market/funding/history"
INSTRUMENTS = "/v5/market/instruments-info"
TREASURY_CSV_TEMPLATE = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?_format=csv&field_tdr_date_value={year}&page=&type=daily_treasury_bill_rates"

FEES = (0.0005, 0.0010, 0.0025)
BASE_FEE = 0.0010
FUNDING_TREATMENTS = ("REALIZED_FUNDING", "ZERO_FUNDING", "ADVERSE_FUNDING")
LOW_HEADROOM = 0.10
MIN_COVERAGE = 0.995
MAX_GAP_HOURS = 6.0
EPS = 1e-12
HOUR_MS = 3_600_000
HOURS_PER_YEAR = 365.25 * 24.0


def get_json(path: str, params: dict, tries: int = 4):
    url = API + path + "?" + urlencode(params)
    last = None
    for attempt in range(tries):
        try:
            req = Request(url, headers={"User-Agent": "botmarketplace-r003-x003-bybit/0.1"})
            with urlopen(req, timeout=60) as r:
                raw = r.read()
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict):
                raise RuntimeError(f"Unexpected Bybit response type for {path}")
            if int(obj.get("retCode", -1)) != 0:
                raise RuntimeError(f"Bybit retCode={obj.get('retCode')} retMsg={obj.get('retMsg')}")
            return obj
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            last = exc
            if attempt + 1 >= tries:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise last


def get_instrument():
    obj = get_json(INSTRUMENTS, {"category": CATEGORY, "symbol": SYMBOL})
    rows = obj.get("result", {}).get("list", [])
    return rows[0] if rows else {}


def _fetch_hourly(path: str, category: str, label: str, has_volume: bool):
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    cursor = int(INCEPTION.timestamp() * 1000)
    rows = []
    while cursor < now_ms:
        end = min(now_ms - 1, cursor + 999 * HOUR_MS + (HOUR_MS - 1))
        params = {
            "category": category,
            "symbol": SYMBOL,
            "interval": "60",
            "start": cursor,
            "end": end,
            "limit": 1000,
        }
        obj = get_json(path, params)
        batch = obj.get("result", {}).get("list", [])
        rows.extend(batch)
        cursor = end + 1
        if not batch and cursor >= now_ms:
            break

    parsed = []
    for r in rows:
        if not isinstance(r, list) or len(r) < 5:
            continue
        ot = int(r[0])
        ct = ot + HOUR_MS - 1
        if ct >= now_ms:
            continue
        item = {
            "open_time": pd.to_datetime(ot, unit="ms", utc=True),
            "close_time": pd.to_datetime(ct, unit="ms", utc=True),
            "open": float(r[1]),
            "high": float(r[2]),
            "low": float(r[3]),
            "close": float(r[4]),
        }
        if has_volume and len(r) >= 6:
            item["volume"] = float(r[5])
        parsed.append(item)

    if not parsed:
        return pd.DataFrame()
    x = pd.DataFrame(parsed).sort_values("open_time").drop_duplicates("open_time", keep="last").reset_index(drop=True)
    if (x[["open", "high", "low", "close"]] <= 0).any().any():
        raise RuntimeError(f"{label} contains non-positive retained prices")
    return x


def fetch_spot():
    return _fetch_hourly(KLINE, "spot", "spot", True)


def fetch_contract():
    return _fetch_hourly(KLINE, CATEGORY, "linear-contract", True)


def fetch_mark():
    return _fetch_hourly(MARK_KLINE, CATEGORY, "mark-price", False)


def fetch_funding():
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    floor_ms = int(INCEPTION.timestamp() * 1000)
    end = now_ms
    out = []
    last_min = None
    while True:
        obj = get_json(FUNDING, {"category": CATEGORY, "symbol": SYMBOL, "endTime": end, "limit": 200})
        batch = obj.get("result", {}).get("list", [])
        if not batch:
            break
        parsed = []
        for r in batch:
            try:
                ts = int(r["fundingRateTimestamp"])
                rate = float(r["fundingRate"])
                parsed.append((ts, rate))
            except Exception:
                continue
        if not parsed:
            break
        out.extend(parsed)
        mn = min(ts for ts, _ in parsed)
        if mn <= floor_ms:
            break
        if last_min is not None and mn >= last_min:
            raise RuntimeError("Bybit funding pagination stalled")
        last_min = mn
        end = mn - 1
    if not out:
        return pd.DataFrame(columns=["funding_time", "funding_rate"])
    x = pd.DataFrame(out, columns=["funding_time_ms", "funding_rate"])
    x["funding_time"] = pd.to_datetime(x["funding_time_ms"], unit="ms", utc=True)
    x = x[(x["funding_time"] >= INCEPTION) & (x["funding_time_ms"] < now_ms)]
    return x.sort_values("funding_time").drop_duplicates("funding_time", keep="last")[["funding_time", "funding_rate"]].reset_index(drop=True)


def build_common(spot, fut, mark):
    if spot.empty or fut.empty or mark.empty:
        return pd.DataFrame()
    s = spot.rename(columns={"open":"spot_open","high":"spot_high","low":"spot_low","close":"spot_close","close_time":"spot_close_time"})
    f = fut.rename(columns={"open":"fut_open","high":"fut_high","low":"fut_low","close":"fut_close","close_time":"fut_close_time"})
    m = mark.rename(columns={"open":"mark_open","high":"mark_high","low":"mark_low","close":"mark_close","close_time":"mark_close_time"})
    common = s.merge(
        f[["open_time","fut_open","fut_high","fut_low","fut_close","fut_close_time"]],
        on="open_time", how="inner"
    ).merge(
        m[["open_time","mark_open","mark_high","mark_low","mark_close","mark_close_time"]],
        on="open_time", how="inner"
    )
    common = common[common["open_time"] >= INCEPTION].sort_values("open_time").drop_duplicates("open_time", keep="last").reset_index(drop=True)
    if common.empty:
        return common
    common["close_time"] = common[["spot_close_time","fut_close_time","mark_close_time"]].min(axis=1)
    common["mark_basis"] = common["mark_close"] / common["spot_close"] - 1.0
    common["contract_basis"] = common["fut_close"] / common["spot_close"] - 1.0
    return common


def align_funding(funding, common):
    cols = ["funding_time","funding_rate","open_time","close_time","funding_mark"]
    if funding.empty or common.empty:
        return pd.DataFrame(columns=cols)

    f = funding.copy().sort_values("funding_time").reset_index(drop=True)
    f["funding_time"] = f["funding_time"].astype("datetime64[ns, UTC]")

    app = common[["open_time","close_time"]].copy().sort_values("close_time")
    app["close_time"] = app["close_time"].astype("datetime64[ns, UTC]")
    x = pd.merge_asof(
        f, app,
        left_on="funding_time", right_on="close_time",
        direction="forward", allow_exact_matches=True
    )

    causal = common[["close_time","mark_close"]].copy().sort_values("close_time")
    causal["close_time"] = causal["close_time"].astype("datetime64[ns, UTC]")
    causal = causal.rename(columns={"close_time":"causal_close_time","mark_close":"funding_mark"})
    back = pd.merge_asof(
        f[["funding_time"]], causal,
        left_on="funding_time", right_on="causal_close_time",
        direction="backward", allow_exact_matches=True
    )
    x["funding_mark"] = back["funding_mark"].to_numpy()
    return x.dropna(subset=["open_time","close_time","funding_mark"])[cols].reset_index(drop=True)


def source_stats(df, label):
    if df.empty:
        return {"label":label,"rows":0,"coverage":0.0,"max_gap_hours":None}
    gaps = df["open_time"].diff().dt.total_seconds().div(3600).dropna()
    start, end = df["open_time"].iloc[0], df["open_time"].iloc[-1]
    expected = int(round((end-start).total_seconds()/3600.0)) + 1
    return {
        "label":label,
        "rows":int(len(df)),
        "start":start.isoformat(),
        "end":end.isoformat(),
        "expected_hours":expected,
        "coverage":float(len(df)/expected) if expected > 0 else 0.0,
        "max_gap_hours":float(gaps.max()) if len(gaps) else 0.0,
    }


def audit_data(spot, fut, mark, common, funding, aligned, instrument):
    stats = {
        "spot":source_stats(spot,"spot"),
        "linear_contract":source_stats(fut,"linear_contract"),
        "mark_price":source_stats(mark,"mark_price"),
    }
    if common.empty:
        cov, gap, expected = 0.0, None, 0
    else:
        gaps = common["open_time"].diff().dt.total_seconds().div(3600).dropna()
        expected = int(round((common["open_time"].iloc[-1]-common["open_time"].iloc[0]).total_seconds()/3600.0)) + 1
        cov = float(len(common)/expected) if expected > 0 else 0.0
        gap = float(gaps.max()) if len(gaps) else 0.0
    if len(common) < 24:
        status = "EARLY_FORWARD_SAMPLE"
    else:
        source_ok = all(s["coverage"] >= MIN_COVERAGE and (s["max_gap_hours"] is None or s["max_gap_hours"] <= MAX_GAP_HOURS) for s in stats.values())
        common_ok = cov >= MIN_COVERAGE and (gap is None or gap <= MAX_GAP_HOURS)
        status = "PASS" if source_ok and common_ok else "DATA_ISSUE_DO_NOT_INTERPRET"
    return {
        "status":status,
        "venue":"Bybit",
        "symbol":SYMBOL,
        "fixed_inception_boundary":INCEPTION.isoformat(),
        "source_stats":stats,
        "common_rows":int(len(common)),
        "common_expected_hours":expected,
        "common_coverage":cov,
        "common_max_gap_hours":gap,
        "funding_rows_downloaded":int(len(funding)),
        "funding_rows_aligned":int(len(aligned)),
        "instrument_metadata":{
            "contractType":instrument.get("contractType"),
            "launchTime":instrument.get("launchTime"),
            "fundingInterval_minutes":instrument.get("fundingInterval"),
            "status":instrument.get("status"),
        },
        "sources":{
            "base":API,
            "spot":KLINE,
            "linear_contract":KLINE,
            "mark_price":MARK_KLINE,
            "funding":FUNDING,
            "instrument_info":INSTRUMENTS,
        },
    }


def fetch_treasury_13w():
    frames = []
    current_year = datetime.now(timezone.utc).year
    for year in range(INCEPTION.year, current_year + 1):
        url = TREASURY_CSV_TEMPLATE.format(year=year)
        req = Request(url, headers={"User-Agent":"botmarketplace-r003-x003-bybit/0.1"})
        with urlopen(req, timeout=60) as r:
            raw = r.read()
        df = pd.read_csv(io.StringIO(raw.decode("utf-8-sig")))
        cols = [str(c).strip() for c in df.columns]
        df.columns = cols
        date_col = next((c for c in cols if c.lower()=="date"), None)
        rate_col = next((c for c in cols if "13 WEEKS" in c.upper() and "COUPON EQUIVALENT" in c.upper()), None)
        if date_col is None or rate_col is None:
            raise RuntimeError(f"Treasury CSV schema changed; columns={cols}")
        z = pd.DataFrame({
            "quote_date":pd.to_datetime(df[date_col], errors="coerce"),
            "rate_pct":pd.to_numeric(df[rate_col], errors="coerce"),
        }).dropna()
        if z.empty:
            continue
        z["quote_date"] = z["quote_date"].dt.tz_localize("UTC")
        z["effective_time"] = z["quote_date"] + pd.Timedelta(days=1)
        frames.append(z)
    if not frames:
        raise RuntimeError("No Treasury 13-week data returned")
    return pd.concat(frames, ignore_index=True).sort_values("quote_date").drop_duplicates("quote_date", keep="last").reset_index(drop=True)


def build_dynamic_safe_reference(path, treasury):
    p = path[["close_time"]].copy().sort_values("close_time").reset_index(drop=True)
    t = treasury[["quote_date","effective_time","rate_pct"]].copy().sort_values("effective_time")
    p["close_time"] = p["close_time"].astype("datetime64[ns, UTC]")
    t["effective_time"] = t["effective_time"].astype("datetime64[ns, UTC]")
    m = pd.merge_asof(p,t,left_on="close_time",right_on="effective_time",direction="backward",allow_exact_matches=True)
    if m["rate_pct"].isna().iloc[0]:
        raise RuntimeError("No causally available Treasury quote at Bybit establishment")
    m["rate_pct"] = m["rate_pct"].ffill()
    m["quote_date"] = m["quote_date"].ffill()
    nav = np.ones(len(m), dtype=float)
    for i in range(1,len(m)):
        dt_hours = (m.loc[i,"close_time"]-m.loc[i-1,"close_time"]).total_seconds()/3600.0
        annual = float(m.loc[i-1,"rate_pct"])/100.0
        nav[i] = nav[i-1]*(1+annual)**(dt_hours/HOURS_PER_YEAR)
    m["safe_nav_dynamic_13w"] = nav
    m["annual_rate"] = m["rate_pct"]/100.0
    m["date"] = m["close_time"].dt.date.astype(str)
    daily = m.groupby("date",as_index=False).tail(1)[["date","close_time","quote_date","annual_rate","safe_nav_dynamic_13w"]].reset_index(drop=True)
    return m,daily


def transform_rate(rate,treatment):
    if treatment=="REALIZED_FUNDING": return rate
    if treatment=="ZERO_FUNDING": return 0.0
    if treatment=="ADVERSE_FUNDING": return rate*0.5 if rate>=0 else rate*2.0
    raise ValueError(treatment)


def max_drawdown(nav):
    s = pd.concat([pd.Series([1.0]), nav.reset_index(drop=True)], ignore_index=True)
    return float((s/s.cummax()-1.0).min())


def simulate(common, aligned, fee, treatment):
    z = common.copy().reset_index(drop=True)
    if len(z) < 2:
        raise ValueError("Need at least two fully closed common Bybit hourly bars")
    init_close = z.loc[0,"close_time"]
    fa = aligned[(aligned["funding_time"] > init_close) & (aligned["funding_time"] <= z["close_time"].iloc[-1])].copy()
    fmap = {}
    for row in fa.itertuples(index=False):
        fmap.setdefault(row.open_time, []).append((float(row.funding_rate), float(row.funding_mark), row.funding_time))

    n = len(z)
    month = z["open_time"].dt.to_period("M")
    is_month_end = np.zeros(n,dtype=bool)
    if n>1:
        is_month_end[:-1] = month.iloc[:-1].to_numpy()!=month.iloc[1:].to_numpy()

    spot0 = float(z.loc[0,"spot_close"])
    mark0 = float(z.loc[0,"mark_close"])
    q = 0.5/spot0
    init_fee = fee*(q*spot0 + q*mark0)
    futures_cash = 0.5 - init_fee
    cum_funding = cum_pair = 0.0
    cum_fee = init_fee
    spot_turn = q*spot0
    perp_turn = q*mark0
    hard_margin_failure = futures_cash <= 0
    low_headroom = 0
    min_close_ratio = futures_cash/max(q*mark0,EPS)
    min_intrahour_ratio = min_close_ratio

    rows=[{
        "open_time":z.loc[0,"open_time"],"close_time":z.loc[0,"close_time"],
        "spot_close":spot0,"mark_close":mark0,"fut_close":float(z.loc[0,"fut_close"]),
        "q_btc":q,"spot_value":q*spot0,"futures_cash":futures_cash,
        "nav_going_concern":q*spot0+futures_cash,"pair_pnl":0.0,"funding_cash":0.0,
        "execution_fee":init_fee,"close_collateral_ratio":min_close_ratio,
        "intrahour_collateral_ratio":min_close_ratio,"rebalanced":True
    }]
    prev_spot, prev_mark = spot0, mark0

    for i in range(1,n):
        spot = float(z.loc[i,"spot_close"])
        mark = float(z.loc[i,"mark_close"])
        mark_high = float(z.loc[i,"mark_high"])

        intrahour_cash = futures_cash - q*(mark_high-prev_mark)
        intrahour_ratio = intrahour_cash/max(q*mark_high,EPS)
        min_intrahour_ratio = min(min_intrahour_ratio,intrahour_ratio)
        if intrahour_ratio < LOW_HEADROOM: low_headroom += 1
        if intrahour_cash <= 0: hard_margin_failure = True

        pair_pnl = q*(spot-prev_spot) - q*(mark-prev_mark)
        futures_cash += -q*(mark-prev_mark)
        cum_pair += pair_pnl

        reb_fee=0.0
        rebalanced=False
        if is_month_end[i] and i < n-1:
            nav_pre = q*spot + futures_cash
            if nav_pre <= 0:
                hard_margin_failure = True
            else:
                q_target = (0.5*nav_pre)/spot
                dq = q_target-q
                futures_cash -= dq*spot
                spot_trade = abs(dq)*spot
                perp_trade = abs(dq)*mark
                reb_fee = fee*(spot_trade+perp_trade)
                futures_cash -= reb_fee
                cum_fee += reb_fee
                spot_turn += spot_trade
                perp_turn += perp_trade
                q = q_target
                rebalanced=True

        funding_cash=0.0
        for rate,fmark,_ in fmap.get(z.loc[i,"open_time"],[]):
            funding_cash += transform_rate(rate,treatment)*q*fmark
        futures_cash += funding_cash
        cum_funding += funding_cash

        close_ratio = futures_cash/max(q*mark,EPS)
        min_close_ratio = min(min_close_ratio,close_ratio)
        if close_ratio < LOW_HEADROOM: low_headroom += 1
        if futures_cash <= 0: hard_margin_failure = True

        nav = q*spot + futures_cash
        rows.append({
            "open_time":z.loc[i,"open_time"],"close_time":z.loc[i,"close_time"],
            "spot_close":spot,"mark_close":mark,"fut_close":float(z.loc[i,"fut_close"]),
            "q_btc":q,"spot_value":q*spot,"futures_cash":futures_cash,
            "nav_going_concern":nav,"pair_pnl":pair_pnl,"funding_cash":funding_cash,
            "execution_fee":reb_fee,"close_collateral_ratio":close_ratio,
            "intrahour_collateral_ratio":intrahour_ratio,"rebalanced":rebalanced
        })
        prev_spot,prev_mark=spot,mark

    path=pd.DataFrame(rows)
    last=path.iloc[-1]
    exit_fee=fee*(abs(float(last["q_btc"]))*float(last["spot_close"]) + abs(float(last["q_btc"]))*float(last["mark_close"]))
    ending_gc=float(last["nav_going_concern"])
    ending_liq=ending_gc-exit_fee
    elapsed_years=max((path["close_time"].iloc[-1]-path["close_time"].iloc[0]).total_seconds()/(365.25*86400.0),1.0/HOURS_PER_YEAR)
    elapsed_days=elapsed_years*365.25
    cagr=float(ending_liq**(1.0/elapsed_years)-1.0) if ending_liq>0 and elapsed_days>=30 else np.nan
    path["net_return_gc"]=path["nav_going_concern"].pct_change(fill_method=None)
    path.loc[0,"net_return_gc"]=path.loc[0,"nav_going_concern"]-1.0
    vol=float(path["net_return_gc"].iloc[1:].std(ddof=0)*math.sqrt(HOURS_PER_YEAR)) if len(path)>=24*30 else np.nan
    mdd=max_drawdown(path["nav_going_concern"])
    calmar=cagr/abs(mdd) if pd.notna(cagr) and mdd<-EPS else np.nan
    hurdle=(1+TREASURY_HURDLE)**elapsed_years-1
    comp=(1+COMPENSATION_HURDLE)**elapsed_years-1
    strat=ending_liq-1.0

    met={
        "elapsed_days":float(elapsed_days),
        "ending_multiple_going_concern":ending_gc,
        "ending_multiple_liquidation_adjusted":ending_liq,
        "cumulative_return_liquidation_adjusted":strat,
        "annualized_return_if_30d_plus":cagr,
        "annualized_vol_if_30d_plus":vol,
        "max_drawdown_going_concern":mdd,
        "calmar_if_30d_plus":calmar,
        "total_funding_contribution":float(cum_funding),
        "total_pair_price_basis_pnl":float(cum_pair),
        "realized_execution_cost":float(cum_fee),
        "hypothetical_terminal_exit_cost":float(exit_fee),
        "total_cost_including_hypothetical_exit":float(cum_fee+exit_fee),
        "spot_turnover_including_hypothetical_exit":float(spot_turn+abs(float(last["q_btc"]))*float(last["spot_close"])),
        "perp_turnover_including_hypothetical_exit":float(perp_turn+abs(float(last["q_btc"]))*float(last["mark_close"])),
        "min_close_collateral_ratio":float(min_close_ratio),
        "min_intrahour_collateral_ratio":float(min_intrahour_ratio),
        "low_headroom_count_proxy":int(low_headroom),
        "hard_margin_failure":bool(hard_margin_failure),
        "funding_events_used":int(len(fa)),
        "month_end_rebalances_completed":int(max(0,path["rebalanced"].sum()-1)),
        "treasury_hurdle_annual":TREASURY_HURDLE,
        "compensation_hurdle_annual":COMPENSATION_HURDLE,
        "treasury_hurdle_cumulative_same_elapsed_time":float(hurdle),
        "compensation_hurdle_cumulative_same_elapsed_time":float(comp),
        "excess_cumulative_vs_treasury":float(strat-hurdle),
        "excess_cumulative_vs_compensation_floor":float(strat-comp),
    }
    return path,met


def monthly_from_path(path):
    p=path.copy()
    p["month"]=p["close_time"].dt.to_period("M").astype(str)
    out=[]
    prev=1.0
    for month,g in p.groupby("month",sort=True):
        end=float(g["nav_going_concern"].iloc[-1])
        ret=end/prev-1.0 if prev>0 else np.nan
        out.append({
            "month":month,
            "return_going_concern":float(ret),
            "funding_cash":float(g["funding_cash"].sum()),
            "pair_pnl":float(g["pair_pnl"].sum()),
            "execution_fee":float(g["execution_fee"].sum()),
            "min_intrahour_collateral_ratio":float(g["intrahour_collateral_ratio"].min()),
        })
        prev=end
    return pd.DataFrame(out)


def write_waiting(outdir,reason,audit=None):
    state={
        "status":"WAITING_FOR_FORWARD_DATA",
        "engine_version":VERSION,
        "protocol":PROTOCOL,
        "venue":"Bybit",
        "fixed_inception_boundary":INCEPTION.isoformat(),
        "reason":reason,
        "created_at_utc":datetime.now(timezone.utc).isoformat(),
    }
    if audit is not None: state["source_audit"]=audit
    (outdir/"r003_x003_bybit_run_state.json").write_text(json.dumps(state,indent=2),encoding="utf-8")
    (outdir/"r003_x003_bybit_summary.md").write_text("# R003-X003 Bybit Forward\n\n**Status:** WAITING_FOR_FORWARD_DATA\n\nReason: "+reason+"\n",encoding="utf-8")
    print(json.dumps(state,indent=2))


def run(outdir):
    outdir.mkdir(parents=True,exist_ok=True)
    now=pd.Timestamp(datetime.now(timezone.utc))
    if now <= INCEPTION + pd.Timedelta(hours=1):
        write_waiting(outdir,"The first Bybit 1h bar whose open is at/after the frozen boundary is not yet fully closed.")
        return

    instrument=get_instrument()
    spot=fetch_spot()
    fut=fetch_contract()
    mark=fetch_mark()
    funding=fetch_funding()
    common=build_common(spot,fut,mark)
    aligned=align_funding(funding,common)
    audit=audit_data(spot,fut,mark,common,funding,aligned,instrument)
    (outdir/"r003_x003_bybit_source_audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")

    if len(common)<2:
        write_waiting(outdir,"Fewer than two fully closed common Bybit hourly bars are available.",audit)
        return
    if audit["status"]=="DATA_ISSUE_DO_NOT_INTERPRET":
        state={
            "status":"DATA_ISSUE_DO_NOT_INTERPRET",
            "engine_version":VERSION,
            "protocol":PROTOCOL,
            "venue":"Bybit",
            "created_at_utc":datetime.now(timezone.utc).isoformat(),
            "fixed_inception_boundary":INCEPTION.isoformat(),
            "source_audit":audit,
        }
        (outdir/"r003_x003_bybit_run_state.json").write_text(json.dumps(state,indent=2),encoding="utf-8")
        return

    metric_rows=[]
    baseline_path=None
    baseline_met=None
    for fee in FEES:
        for treatment in FUNDING_TREATMENTS:
            path,met=simulate(common,aligned,fee,treatment)
            metric_rows.append({"fee_bps_per_leg":fee*10000.0,"funding_treatment":treatment,**met})
            if abs(fee-BASE_FEE)<EPS and treatment=="REALIZED_FUNDING":
                baseline_path,baseline_met=path.copy(),met.copy()

    assert baseline_path is not None and baseline_met is not None
    metrics=pd.DataFrame(metric_rows)
    baseline_path.to_csv(outdir/"r003_x003_bybit_forward_hourly_nav.csv",index=False)

    treasury_status="PASS"
    treasury_error=None
    treasury_latest_quote=None
    dynamic_safe=np.nan
    dynamic_excess=np.nan
    try:
        treasury=fetch_treasury_13w()
        safe_hourly,safe_daily=build_dynamic_safe_reference(baseline_path,treasury)
        safe_daily.to_csv(outdir/"r003_x003_bybit_safe_hurdle_daily.csv",index=False)
        treasury_latest_quote=treasury["quote_date"].iloc[-1].isoformat()
        dynamic_safe=float(safe_hourly["safe_nav_dynamic_13w"].iloc[-1]-1.0)
        dynamic_excess=float(baseline_met["cumulative_return_liquidation_adjusted"]-dynamic_safe)
    except Exception as exc:
        treasury_status="SAFE_HURDLE_SOURCE_INCOMPLETE"
        treasury_error=f"{type(exc).__name__}: {exc}"
        pd.DataFrame(columns=["date","close_time","quote_date","annual_rate","safe_nav_dynamic_13w"]).to_csv(outdir/"r003_x003_bybit_safe_hurdle_daily.csv",index=False)

    metrics["dynamic_treasury_status"]=treasury_status
    metrics["dynamic_treasury_cumulative"]=dynamic_safe
    metrics["excess_cumulative_vs_dynamic_treasury"]=metrics["cumulative_return_liquidation_adjusted"]-dynamic_safe if pd.notna(dynamic_safe) else np.nan
    metrics.to_csv(outdir/"r003_x003_bybit_metrics.csv",index=False)

    pd.DataFrame([{
        "min_close_collateral_ratio":baseline_met["min_close_collateral_ratio"],
        "min_intrahour_collateral_ratio":baseline_met["min_intrahour_collateral_ratio"],
        "low_headroom_count_proxy":baseline_met["low_headroom_count_proxy"],
        "hard_margin_failure":baseline_met["hard_margin_failure"],
    }]).to_csv(outdir/"r003_x003_bybit_margin.csv",index=False)

    init_close=baseline_path["close_time"].iloc[0]
    fe=aligned[(aligned["funding_time"]>init_close)&(aligned["funding_time"]<=baseline_path["close_time"].iloc[-1])].copy()
    fe.to_csv(outdir/"r003_x003_bybit_funding_events.csv",index=False)
    monthly_from_path(baseline_path).to_csv(outdir/"r003_x003_bybit_monthly.csv",index=False)

    elapsed=baseline_met["elapsed_days"]
    funding_n=baseline_met["funding_events_used"]
    rebal_n=baseline_met["month_end_rebalances_completed"]
    mature=elapsed>=365.0 and rebal_n>=10 and funding_n>=1000
    evidence_status="MATURE_FORWARD_SAMPLE_REQUIRES_FORMAL_REVIEW" if mature else "FORWARD_EVIDENCE_ACCUMULATING"

    state={
        "status":"PASS",
        "engine_version":VERSION,
        "protocol":PROTOCOL,
        "venue":"Bybit",
        "created_at_utc":datetime.now(timezone.utc).isoformat(),
        "evidence_status":evidence_status,
        "fixed_inception_boundary":INCEPTION.isoformat(),
        "initial_establishment_close":baseline_path["close_time"].iloc[0].isoformat(),
        "latest_forward_close":baseline_path["close_time"].iloc[-1].isoformat(),
        "safe_hurdles":{
            "treasury_13w_inception_annual":TREASURY_HURDLE,
            "treasury_plus_2pp_annual":COMPENSATION_HURDLE,
            "dynamic_treasury_status":treasury_status,
            "dynamic_treasury_latest_quote":treasury_latest_quote,
            "dynamic_treasury_cumulative":None if pd.isna(dynamic_safe) else float(dynamic_safe),
            "excess_cumulative_vs_dynamic_treasury":None if pd.isna(dynamic_excess) else float(dynamic_excess),
            "dynamic_treasury_error":treasury_error,
        },
        "evidence_thresholds":{
            "min_calendar_days":365,
            "min_funding_events_reference":1000,
            "min_month_end_rebalances":10,
        },
        "progress":{
            "elapsed_days":elapsed,
            "funding_events":funding_n,
            "month_end_rebalances":rebal_n,
            "mature":mature,
        },
        "baseline":baseline_met,
        "source_audit":audit,
        "outputs":[
            "r003_x003_bybit_run_state.json",
            "r003_x003_bybit_source_audit.json",
            "r003_x003_bybit_forward_hourly_nav.csv",
            "r003_x003_bybit_metrics.csv",
            "r003_x003_bybit_margin.csv",
            "r003_x003_bybit_funding_events.csv",
            "r003_x003_bybit_monthly.csv",
            "r003_x003_bybit_safe_hurdle_daily.csv",
            "r003_x003_bybit_summary.md",
        ],
    }
    (outdir/"r003_x003_bybit_run_state.json").write_text(json.dumps(state,indent=2,default=str),encoding="utf-8")

    def pct(v): return "n/a" if pd.isna(v) else f"{float(v):.2%}"
    md="# R003-X003 Bybit Forward — Current Snapshot\n\n"
    md+=f"**Evidence status:** {evidence_status}\n\n"
    md+=f"- Fixed inception boundary: **{INCEPTION.isoformat()}**\n"
    md+=f"- Initial establishment close: **{baseline_path['close_time'].iloc[0]}**\n"
    md+=f"- Latest forward close: **{baseline_path['close_time'].iloc[-1]}**\n"
    md+=f"- Elapsed forward days: **{elapsed:.1f}**\n"
    md+=f"- Realized funding events used: **{funding_n}**\n"
    md+=f"- Completed month-end rebalances: **{rebal_n}**\n"
    md+=f"- Liquidation-adjusted cumulative return: **{pct(baseline_met['cumulative_return_liquidation_adjusted'])}**\n"
    md+=f"- Annualized return (only shown after 30d): **{pct(baseline_met['annualized_return_if_30d_plus'])}**\n"
    md+=f"- Max DD, going-concern NAV: **{pct(baseline_met['max_drawdown_going_concern'])}**\n"
    md+=f"- Min intrahour collateral ratio: **{pct(baseline_met['min_intrahour_collateral_ratio'])}**\n"
    md+=f"- Funding contribution: **{baseline_met['total_funding_contribution']:.6f} NAV**\n"
    md+=f"- Pair/basis P&L: **{baseline_met['total_pair_price_basis_pnl']:.6f} NAV**\n"
    md+=f"- Dynamic Treasury benchmark: **{treasury_status}**\n"
    if pd.notna(dynamic_safe):
        md+=f"- Dynamic Treasury cumulative: **{dynamic_safe:.4%}**\n"
        md+=f"- Excess vs dynamic Treasury: **{dynamic_excess:.4%}**\n"
    md+="\nThis is a separate Bybit forward venue replication. It does not replace Binance R003-E003 or alter Bybit X001.\n"
    (outdir/"r003_x003_bybit_summary.md").write_text(md,encoding="utf-8")
    print(md)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--outdir",type=Path,required=True)
    args=ap.parse_args()
    try:
        run(args.outdir)
    except Exception as exc:
        args.outdir.mkdir(parents=True,exist_ok=True)
        state={
            "status":"SOURCE_OR_ENGINE_ERROR",
            "engine_version":VERSION,
            "protocol":PROTOCOL,
            "venue":"Bybit",
            "created_at_utc":datetime.now(timezone.utc).isoformat(),
            "fixed_inception_boundary":INCEPTION.isoformat(),
            "error_type":type(exc).__name__,
            "error":str(exc),
        }
        (args.outdir/"r003_x003_bybit_run_state.json").write_text(json.dumps(state,indent=2),encoding="utf-8")
        raise


if __name__=="__main__":
    main()
