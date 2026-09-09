"""R003-E001 BTCUSDT funding-premium structural audit v0.1."""
from __future__ import annotations

import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

VERSION="0.1"
PROTOCOL="r003-e001-funding-premium-structural-audit-protocol-v0.1"
SYMBOL="BTCUSDT"
FUNDING_URL="https://fapi.binance.com/fapi/v1/fundingRate"
SPOT_URL="https://data-api.binance.vision/api/v3/klines"
START=pd.Timestamp("2019-10-01", tz="UTC")
PRIMARY=pd.Timestamp("2020-01-01")
POST2023=pd.Timestamp("2023-01-01")


def get_json(url, params):
    req=Request(url+"?"+urlencode(params), headers={"User-Agent":"botmarketplace-r003-e001/0.1"})
    with urlopen(req, timeout=60) as r: raw=r.read()
    return raw, json.loads(raw.decode("utf-8"))


def fetch_funding():
    start=int(START.timestamp()*1000); rows=[]; hashes=[]; last=None
    while True:
        raw,obj=get_json(FUNDING_URL,{"symbol":SYMBOL,"startTime":start,"limit":1000})
        hashes.append(hashlib.sha256(raw).hexdigest())
        if not isinstance(obj,list): raise RuntimeError(f"Funding source error: {obj}")
        if not obj: break
        rows.extend(obj); cur=int(obj[-1]["fundingTime"])
        if last is not None and cur<=last: raise RuntimeError("Funding pagination stalled")
        last=cur; start=cur+1
        if len(obj)<1000: break
    if not rows: raise RuntimeError("No funding history returned")
    x=pd.DataFrame(rows)
    x["funding_time"]=pd.to_datetime(pd.to_numeric(x["fundingTime"],errors="coerce"),unit="ms",utc=True)
    x["funding_rate"]=pd.to_numeric(x["fundingRate"],errors="coerce")
    x["mark_price"]=pd.to_numeric(x["markPrice"],errors="coerce") if "markPrice" in x else np.nan
    x["rate_type"]=x["rateType"].astype(str) if "rateType" in x else ""
    x=x.dropna(subset=["funding_time","funding_rate"]).sort_values("funding_time").drop_duplicates("funding_time",keep="last")
    return rows,hashes,x[["funding_time","funding_rate","mark_price","rate_type"]].reset_index(drop=True)


def fetch_spot():
    start=int(START.timestamp()*1000); now=int(datetime.now(timezone.utc).timestamp()*1000); rows=[]; last=None
    while True:
        _,obj=get_json(SPOT_URL,{"symbol":SYMBOL,"interval":"1d","startTime":start,"limit":1000})
        if not isinstance(obj,list): raise RuntimeError(f"Spot source error: {obj}")
        if not obj: break
        rows += [r for r in obj if len(r)>=7 and int(r[6])<now]
        cur=int(obj[-1][0])
        if last is not None and cur<=last: raise RuntimeError("Spot pagination stalled")
        last=cur; start=cur+1
        if len(obj)<1000: break
    if not rows: raise RuntimeError("No closed spot bars returned")
    x=pd.DataFrame(rows)
    z=pd.DataFrame({
        "open_time":pd.to_datetime(pd.to_numeric(x.iloc[:,0]),unit="ms",utc=True),
        "close":pd.to_numeric(x.iloc[:,4],errors="coerce"),
        "close_time":pd.to_datetime(pd.to_numeric(x.iloc[:,6]),unit="ms",utc=True),
    }).dropna().sort_values("open_time").drop_duplicates("open_time",keep="last")
    z["running_ath"]=z["close"].cummax(); z["drawdown"]=z["close"]/z["running_ath"]-1
    return z.reset_index(drop=True)


def merge_state(f,spot):
    return pd.merge_asof(f.sort_values("funding_time"),spot[["close_time","close","running_ath","drawdown"]].sort_values("close_time"),left_on="funding_time",right_on="close_time",direction="backward",allow_exact_matches=True)


def daily_rates(x): return x.set_index("funding_time")["funding_rate"].sort_index().resample("1D").sum().fillna(0.0)


def neg_streak(s):
    best=cur=0
    for v in s:
        cur=cur+1 if v<0 else 0; best=max(best,cur)
    return int(best)


def metrics(name,x,start,end=None):
    t=x["funding_time"].dt.tz_convert(None); m=t>=start
    if end is not None: m &= t<=end
    g=x[m].copy(); d=daily_rates(g)
    r7=d.rolling(7).sum().dropna(); r30=d.rolling(30).sum().dropna(); r90=d.rolling(90).sum().dropna(); r365=d.rolling(365).sum().dropna()
    return {
        "slice":name,"start":g["funding_time"].iloc[0].date().isoformat(),"end":g["funding_time"].iloc[-1].date().isoformat(),"observations":len(g),
        "short_funding_simple_sum":float(g.funding_rate.sum()),"short_funding_compounded":float((1+g.funding_rate).prod()-1),
        "mean_funding_rate":float(g.funding_rate.mean()),"median_funding_rate":float(g.funding_rate.median()),
        "positive_fraction":float((g.funding_rate>0).mean()),"negative_fraction":float((g.funding_rate<0).mean()),"zero_fraction":float((g.funding_rate==0).mean()),
        "worst_single_funding":float(g.funding_rate.min()),"best_single_funding":float(g.funding_rate.max()),"longest_negative_event_streak":neg_streak(g.funding_rate),
        "worst_7d_sum":float(r7.min()),"worst_30d_sum":float(r30.min()),"worst_90d_sum":float(r90.min()),
        "median_365d_sum":float(r365.median()),"positive_365d_share":float((r365>0).mean()),"worst_365d_sum":float(r365.min()),"best_365d_sum":float(r365.max()),
    }


def yearly(x):
    z=x.copy(); z["year"]=z.funding_time.dt.year; out=[]
    for y,g in z.groupby("year"):
        out.append({"year":int(y),"observations":len(g),"short_funding_simple_sum":float(g.funding_rate.sum()),"short_funding_compounded":float((1+g.funding_rate).prod()-1),"positive_fraction":float((g.funding_rate>0).mean()),"mean_rate":float(g.funding_rate.mean()),"median_rate":float(g.funding_rate.median())})
    return pd.DataFrame(out)


def bucket(dd):
    if pd.isna(dd): return "NO_SPOT_STATE"
    if dd>-0.10:return "DD_0_TO_10"
    if dd>-0.20:return "DD_10_TO_20"
    if dd>-0.35:return "DD_20_TO_35"
    if dd>-0.50:return "DD_35_TO_50"
    return "DD_50_PLUS"


def buckets(x):
    z=x.copy(); z["drawdown_bucket"]=z.drawdown.map(bucket); out=[]
    for b,g in z.groupby("drawdown_bucket",sort=False):
        out.append({"drawdown_bucket":b,"observations":len(g),"short_funding_simple_sum":float(g.funding_rate.sum()),"mean_rate":float(g.funding_rate.mean()),"median_rate":float(g.funding_rate.median()),"positive_fraction":float((g.funding_rate>0).mean()),"negative_fraction":float((g.funding_rate<0).mean())})
    return pd.DataFrame(out)


def decide(m,y,b):
    mm=m.set_index("slice"); full=mm.loc["FULL_AVAILABLE"]; pre=mm.loc["PRE_2023"]; post=mm.loc["POST_2023"]
    current=datetime.now(timezone.utc).year; cy=y[(y.year>=2020)&(y.year<current)]
    maj=bool((cy.short_funding_simple_sum>0).mean()>0.5) if len(cy) else False
    py=cy[cy.short_funding_simple_sum>0].short_funding_simple_sum; conc=float(py.max()/py.sum()) if len(py) and py.sum()>0 else np.nan
    checks=[full.short_funding_simple_sum>0,pre.short_funding_simple_sum>0,post.short_funding_simple_sum>0,maj,full.median_365d_sum>0,full.positive_365d_share>0.5,np.isnan(conc) or conc<0.5]
    carry="STRUCTURAL_SIGNAL_PRESENT" if all(checks) else ("STRUCTURAL_SIGNAL_ABSENT" if full.short_funding_simple_sum<=0 else "STRUCTURAL_SIGNAL_MIXED")
    deep=b[b.drawdown_bucket.isin(["DD_35_TO_50","DD_50_PLUS"])]
    if deep.empty: crisis="INSUFFICIENT_DEEP_DRAWDOWN_DATA"; dm=dmed=dpos=np.nan
    else:
        n=deep.observations.sum(); dm=float((deep.mean_rate*deep.observations).sum()/n); dpos=float((deep.positive_fraction*deep.observations).sum()/n); dmed=float(deep.median_rate.median())
        crisis="CRISIS_FINANCING_COMPATIBLE" if dm>=0 and dmed>=0 else ("CRISIS_FINANCING_PROCYCLICAL_RISK" if dm<0 and dmed<0 else "CRISIS_FINANCING_MIXED")
    return {"carry_conclusion":carry,"completed_calendar_years":int(len(cy)),"majority_completed_years_positive":maj,"largest_positive_year_share":conc,"crisis_financing_conclusion":crisis,"deep_drawdown_weighted_mean_rate":dm,"deep_drawdown_median_bucket_rate":dmed,"deep_drawdown_positive_fraction":dpos}


def run(out):
    raw,hashes,f=fetch_funding(); spot=fetch_spot(); x=merge_state(f,spot)
    (out/"r003_e001_funding_raw.json").write_text(json.dumps({"source_url":FUNDING_URL,"symbol":SYMBOL,"pages_sha256":hashes,"rows":raw},ensure_ascii=False),encoding="utf-8")
    x.to_csv(out/"r003_e001_funding_clean.csv",index=False); spot.to_csv(out/"r003_e001_spot_daily.csv",index=False)
    m=pd.DataFrame([metrics("FULL_AVAILABLE",x,pd.Timestamp("1900-01-01")),metrics("PRIMARY_2020",x,PRIMARY),metrics("PRE_2023",x,PRIMARY,pd.Timestamp("2022-12-31 23:59:59")),metrics("POST_2023",x,POST2023)])
    y=yearly(x); b=buckets(x); d=decide(m,y,b)
    m.to_csv(out/"r003_e001_metrics.csv",index=False); y.to_csv(out/"r003_e001_yearly.csv",index=False); b.to_csv(out/"r003_e001_drawdown_buckets.csv",index=False)
    gaps=f.funding_time.diff().dt.total_seconds().div(3600).dropna().round(6).value_counts().sort_index()
    state={"status":"PASS","engine_version":VERSION,"protocol":PROTOCOL,"created_at_utc":datetime.now(timezone.utc).isoformat(),"evidence_status":"STRUCTURAL_PREMIUM_AUDIT_ONLY_NOT_STRATEGY_PASS","funding_source":FUNDING_URL,"spot_source":SPOT_URL,"symbol":SYMBOL,"funding_rows_raw":len(raw),"funding_rows_clean":len(f),"funding_start":f.funding_time.iloc[0].isoformat(),"funding_end":f.funding_time.iloc[-1].isoformat(),"funding_interval_hours_distribution":{str(k):int(v) for k,v in gaps.items()},"spot_rows":len(spot),"spot_start":spot.open_time.iloc[0].isoformat(),"spot_end":spot.open_time.iloc[-1].isoformat(),"spot_max_gap_days":int(spot.open_time.diff().dt.days.dropna().max()),"funding_rows_without_causal_spot_state":int(x.drawdown.isna().sum()),"decision":d}
    (out/"r003_e001_run_state.json").write_text(json.dumps(state,indent=2),encoding="utf-8")
    mm=m.set_index("slice")
    md="# R003-E001 Funding-Premium Structural Audit — Raw Output v0.1\n\n**Status:** structural premium audit only; not a strategy PASS.\n\n"
    md+=f"- Funding period: **{f.funding_time.iloc[0].date()} -> {f.funding_time.iloc[-1].date()}**\n- Funding observations: **{len(f):,}**\n- Carry conclusion: **{d['carry_conclusion']}**\n- Crisis-financing conclusion: **{d['crisis_financing_conclusion']}**\n\n"
    md+="| Slice | Simple sum | Compounded | Positive funding | Median rolling 365d | Positive 365d share | Worst 30d |\n|---|---:|---:|---:|---:|---:|---:|\n"
    for s in ["FULL_AVAILABLE","PRIMARY_2020","PRE_2023","POST_2023"]:
        r=mm.loc[s]; md+=f"| {s} | {r.short_funding_simple_sum:.2%} | {r.short_funding_compounded:.2%} | {r.positive_fraction:.1%} | {r.median_365d_sum:.2%} | {r.positive_365d_share:.1%} | {r.worst_30d_sum:.2%} |\n"
    md+="\nThis measures the realized funding premium paid to a normalized perpetual short. It is **not** an executable long-spot/short-perpetual return: basis P&L, margin/liquidation mechanics, legging, spreads, slippage, collateral transfers and counterparty risk are intentionally deferred.\n"
    (out/"r003_e001_summary.md").write_text(md,encoding="utf-8"); print(md)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--outdir",type=Path,required=True); a=ap.parse_args(); a.outdir.mkdir(parents=True,exist_ok=True)
    try: run(a.outdir)
    except Exception as e:
        state={"status":"SOURCE_OR_ENGINE_ERROR","engine_version":VERSION,"protocol":PROTOCOL,"created_at_utc":datetime.now(timezone.utc).isoformat(),"error_type":type(e).__name__,"error":str(e)}
        (a.outdir/"r003_e001_run_state.json").write_text(json.dumps(state,indent=2),encoding="utf-8"); raise

if __name__=="__main__": main()
