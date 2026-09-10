"""R003-X001 Bybit BTCUSDT funding structural replication v0.1."""
from __future__ import annotations
import argparse, json, math, os, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import numpy as np
import pandas as pd

VERSION="0.1"
PROTOCOL="r003-bybit-x001-structural-replication-protocol-v0.1"
BASE="https://api.bybit.com"
SYMBOL="BTCUSDT"; CATEGORY="linear"
INSTRUMENT=BASE+"/v5/market/instruments-info"
FUNDING=BASE+"/v5/market/funding/history"
INDEX=BASE+"/v5/market/index-price-kline"


def atomic_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf-8"); os.replace(tmp,path)


def get_json(url,params,retries=5):
    for i in range(retries):
        try:
            req=Request(url+"?"+urlencode(params),headers={"User-Agent":"botmarketplace-r003-x001/0.1"})
            with urlopen(req,timeout=60) as r: obj=json.loads(r.read().decode("utf-8"))
            if int(obj.get("retCode",-1))!=0: raise RuntimeError(f"Bybit {obj.get('retCode')}: {obj.get('retMsg')}")
            return obj
        except Exception:
            if i+1==retries: raise
            time.sleep(min(2**i,8))


def snapshot(work):
    p=work/"snapshot.json"
    if p.exists():
        x=json.loads(p.read_text(encoding="utf-8"))
        if x.get("protocol")!=PROTOCOL: raise RuntimeError("Workspace protocol mismatch")
        return x
    now=datetime.now(timezone.utc); x={"protocol":PROTOCOL,"created_at_utc":now.isoformat(),"cutoff_ms":int(now.timestamp()*1000)}
    atomic_json(p,x); return x


def instrument_info(work):
    p=work/"instrument_info.json"
    if p.exists(): obj=json.loads(p.read_text(encoding="utf-8"))
    else:
        obj=get_json(INSTRUMENT,{"category":CATEGORY,"symbol":SYMBOL}); atomic_json(p,obj)
    rows=obj.get("result",{}).get("list",[]); rows=[r for r in rows if r.get("symbol")==SYMBOL]
    if not rows: raise RuntimeError("BTCUSDT instrument metadata missing")
    return rows[0]


def load_pages(path):
    if not path.exists(): return []
    out=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip(): out.append(json.loads(line))
    return out


def append_page(path,page):
    path.parent.mkdir(parents=True,exist_ok=True)
    with open(path,"a",encoding="utf-8") as f: f.write(json.dumps(page,separators=(",",":"))+"\n"); f.flush(); os.fsync(f.fileno())


def fetch_funding(work,cutoff,launch):
    cp=work/"_checkpoint_funding.jsonl"; pages=load_pages(cp); rows=[]; end=cutoff
    for p in pages:
        rows+=p
        if p: end=min(int(r["fundingRateTimestamp"]) for r in p)-1
    if pages: print(f"funding: resumed {len(pages)} pages")
    done=bool(pages and (not pages[-1] or len(pages[-1])<200 or min(int(r["fundingRateTimestamp"]) for r in pages[-1])<=launch))
    while not done:
        obj=get_json(FUNDING,{"category":CATEGORY,"symbol":SYMBOL,"endTime":end,"limit":200})
        page=obj.get("result",{}).get("list",[]); append_page(cp,page); pages.append(page); rows+=page
        print(f"funding: page {len(pages)}, raw rows {len(rows):,}")
        if not page: done=True
        else:
            oldest=min(int(r["fundingRateTimestamp"]) for r in page); end=oldest-1
            done=len(page)<200 or oldest<=launch
    x=pd.DataFrame(rows)
    x["funding_time"]=pd.to_datetime(pd.to_numeric(x["fundingRateTimestamp"],errors="coerce"),unit="ms",utc=True)
    x["funding_rate"]=pd.to_numeric(x["fundingRate"],errors="coerce")
    x=x.dropna(subset=["funding_time","funding_rate"]).sort_values("funding_time").drop_duplicates("funding_time",keep="last")
    lo=pd.to_datetime(launch,unit="ms",utc=True); hi=pd.to_datetime(cutoff,unit="ms",utc=True)
    return x[(x.funding_time>=lo)&(x.funding_time<=hi)][["funding_time","funding_rate"]].reset_index(drop=True),len(rows),len(pages)


def fetch_index(work,cutoff,launch):
    cp=work/"_checkpoint_index.jsonl"; pages=load_pages(cp); rows=[]; end=cutoff
    for p in pages:
        rows+=p
        if p: end=min(int(r[0]) for r in p)-1
    if pages: print(f"index: resumed {len(pages)} pages")
    done=bool(pages and (not pages[-1] or len(pages[-1])<1000 or min(int(r[0]) for r in pages[-1])<=launch))
    while not done:
        obj=get_json(INDEX,{"category":CATEGORY,"symbol":SYMBOL,"interval":"D","end":end,"limit":1000})
        page=obj.get("result",{}).get("list",[]); append_page(cp,page); pages.append(page); rows+=page
        print(f"index: page {len(pages)}, raw rows {len(rows):,}")
        if not page: done=True
        else:
            oldest=min(int(r[0]) for r in page); end=oldest-1
            done=len(page)<1000 or oldest<=launch
    x=pd.DataFrame(rows)
    z=pd.DataFrame({"open_time":pd.to_datetime(pd.to_numeric(x.iloc[:,0]),unit="ms",utc=True),"open":pd.to_numeric(x.iloc[:,1],errors="coerce"),"high":pd.to_numeric(x.iloc[:,2],errors="coerce"),"low":pd.to_numeric(x.iloc[:,3],errors="coerce"),"close":pd.to_numeric(x.iloc[:,4],errors="coerce")}).dropna()
    z["close_time"]=z.open_time+pd.Timedelta(days=1)-pd.Timedelta(milliseconds=1)
    lo=pd.to_datetime(launch,unit="ms",utc=True).floor("D"); hi=pd.to_datetime(cutoff,unit="ms",utc=True)
    z=z[(z.open_time>=lo)&(z.close_time<hi)].sort_values("open_time").drop_duplicates("open_time",keep="last").reset_index(drop=True)
    if (z[["open","high","low","close"]]<=0).any().any(): raise RuntimeError("Non-positive index price")
    z["running_ath"]=z.close.cummax(); z["drawdown"]=z.close/z.running_ath-1
    return z,len(rows),len(pages)


def merge_state(f,idx):
    return pd.merge_asof(f.sort_values("funding_time"),idx[["close_time","close","running_ath","drawdown"]].sort_values("close_time"),left_on="funding_time",right_on="close_time",direction="backward",allow_exact_matches=True)


def first_full_year(launch,first):
    a=max(launch,first)
    return int(a.year if (a.month,a.day,a.hour,a.minute,a.second,a.microsecond)==(1,1,0,0,0,0) else a.year+1)


def daily_rates(x): return x.set_index("funding_time").funding_rate.sort_index().resample("1D").sum().fillna(0.0)


def neg_streak(s):
    best=cur=0
    for v in s:
        cur=cur+1 if v<0 else 0; best=max(best,cur)
    return int(best)


def metric(name,x,start=None,end=None):
    g=x.copy()
    if start is not None: g=g[g.funding_time>=start]
    if end is not None: g=g[g.funding_time<=end]
    if g.empty: return {"slice":name,"observations":0,"short_funding_simple_sum":np.nan,"short_funding_compounded":np.nan,"positive_fraction":np.nan,"median_365d_sum":np.nan,"positive_365d_share":np.nan,"latest_365d_sum":np.nan,"worst_30d_sum":np.nan}
    d=daily_rates(g); r7=d.rolling(7).sum().dropna(); r30=d.rolling(30).sum().dropna(); r90=d.rolling(90).sum().dropna(); r365=d.rolling(365).sum().dropna()
    return {"slice":name,"start":g.funding_time.iloc[0].isoformat(),"end":g.funding_time.iloc[-1].isoformat(),"observations":len(g),"short_funding_simple_sum":float(g.funding_rate.sum()),"short_funding_compounded":float((1+g.funding_rate).prod()-1),"mean_funding_rate":float(g.funding_rate.mean()),"median_funding_rate":float(g.funding_rate.median()),"positive_fraction":float((g.funding_rate>0).mean()),"negative_fraction":float((g.funding_rate<0).mean()),"zero_fraction":float((g.funding_rate==0).mean()),"worst_single_funding":float(g.funding_rate.min()),"best_single_funding":float(g.funding_rate.max()),"longest_negative_event_streak":neg_streak(g.funding_rate),"worst_7d_sum":float(r7.min()) if len(r7) else np.nan,"worst_30d_sum":float(r30.min()) if len(r30) else np.nan,"worst_90d_sum":float(r90.min()) if len(r90) else np.nan,"median_365d_sum":float(r365.median()) if len(r365) else np.nan,"positive_365d_share":float((r365>0).mean()) if len(r365) else np.nan,"worst_365d_sum":float(r365.min()) if len(r365) else np.nan,"best_365d_sum":float(r365.max()) if len(r365) else np.nan,"latest_365d_sum":float(r365.iloc[-1]) if len(r365) else np.nan}


def yearly(x):
    z=x.copy(); z["year"]=z.funding_time.dt.year; out=[]
    for y,g in z.groupby("year"):
        out.append({"year":int(y),"observations":len(g),"short_funding_simple_sum":float(g.funding_rate.sum()),"short_funding_compounded":float((1+g.funding_rate).prod()-1),"positive_fraction":float((g.funding_rate>0).mean()),"negative_fraction":float((g.funding_rate<0).mean()),"mean_rate":float(g.funding_rate.mean()),"median_rate":float(g.funding_rate.median())})
    return pd.DataFrame(out)


def bucket(dd):
    if pd.isna(dd): return "NO_INDEX_STATE"
    if dd>-0.10:return "DD_0_TO_10"
    if dd>-0.20:return "DD_10_TO_20"
    if dd>-0.35:return "DD_20_TO_35"
    if dd>-0.50:return "DD_35_TO_50"
    return "DD_50_PLUS"


def bucket_table(x):
    z=x.copy(); z["drawdown_bucket"]=z.drawdown.map(bucket); out=[]
    for b,g in z.groupby("drawdown_bucket",sort=False): out.append({"drawdown_bucket":b,"observations":len(g),"short_funding_simple_sum":float(g.funding_rate.sum()),"mean_rate":float(g.funding_rate.mean()),"median_rate":float(g.funding_rate.median()),"positive_fraction":float((g.funding_rate>0).mean()),"negative_fraction":float((g.funding_rate<0).mean())})
    return pd.DataFrame(out)


def source_audit(info,f,idx,cutoff,raw_f,pages_f,raw_i,pages_i):
    launch=int(info.get("launchTime") or 0); interval=int(float(info.get("fundingInterval") or 0)); gaps=f.funding_time.diff().dt.total_seconds().div(3600).dropna(); ig=idx.open_time.diff().dt.total_seconds().div(86400).dropna()
    exp=(idx.open_time.iloc[-1].normalize()-idx.open_time.iloc[0].normalize()).days+1 if len(idx) else 0; cov=len(idx)/exp if exp else 0
    age=(pd.to_datetime(cutoff,unit="ms",utc=True)-f.funding_time.iloc[-1]).total_seconds()/3600 if len(f) else math.inf
    start_ok=bool(len(f) and len(idx) and idx.open_time.iloc[0]<=f.funding_time.iloc[0].normalize()+pd.Timedelta(days=2))
    documented=interval/60 if interval else np.nan; match=float(((gaps-documented).abs()<=5/60).mean()) if len(gaps) and np.isfinite(documented) else np.nan
    checks={"instrument_metadata_ok":bool(info.get("symbol")==SYMBOL and info.get("contractType")=="LinearPerpetual" and launch>0),"funding_observations_ge_1000":bool(len(f)>=1000),"funding_timestamps_strict_after_dedup":bool(f.funding_time.is_monotonic_increasing and not f.funding_time.duplicated().any()),"latest_funding_within_24h_cutoff":bool(age<=24),"index_starts_by_first_funding_plus_2d":start_ok,"index_daily_coverage_ge_99pct":bool(cov>=0.99),"index_max_gap_le_3d":bool((float(ig.max()) if len(ig) else 0)<=3),"index_prices_positive":bool(len(idx) and (idx.close>0).all())}
    return {"status":"PASS" if all(checks.values()) else "DATA_REDESIGN","checks":checks,"instrument":{"symbol":info.get("symbol"),"contractType":info.get("contractType"),"status":info.get("status"),"launchTime":info.get("launchTime"),"launchTimeUtc":pd.to_datetime(launch,unit="ms",utc=True).isoformat() if launch else None,"fundingIntervalMinutes":interval,"settleCoin":info.get("settleCoin")},"snapshot_cutoff_utc":pd.to_datetime(cutoff,unit="ms",utc=True).isoformat(),"funding":{"rows_clean":len(f),"raw_rows":raw_f,"pages":pages_f,"start":f.funding_time.iloc[0].isoformat() if len(f) else None,"end":f.funding_time.iloc[-1].isoformat() if len(f) else None,"latest_age_hours":age,"median_gap_hours":float(gaps.median()) if len(gaps) else np.nan,"max_gap_hours":float(gaps.max()) if len(gaps) else np.nan,"documented_interval_hours_current":documented,"gap_fraction_within_5min_of_documented_interval":match},"index_daily":{"rows_clean":len(idx),"raw_rows":raw_i,"pages":pages_i,"start":idx.open_time.iloc[0].isoformat() if len(idx) else None,"end":idx.open_time.iloc[-1].isoformat() if len(idx) else None,"coverage":cov,"max_gap_days":float(ig.max()) if len(ig) else 0},"sources":{"instrument":INSTRUMENT,"funding":FUNDING,"index_daily":INDEX}}


def decide(m,y,b,first_full,current_year):
    mm=m.set_index("slice"); full=mm.loc["FULL_AVAILABLE"]; primary=mm.loc["PRIMARY_FULL_YEARS"]; pre=mm.loc["PRE_2023"]; post=mm.loc["POST_2023"]
    cy=y[(y.year>=first_full)&(y.year<current_year)]; majority=bool((cy.short_funding_simple_sum>0).mean()>0.5) if len(cy) else False; pos=cy[cy.short_funding_simple_sum>0].short_funding_simple_sum; conc=float(pos.max()/pos.sum()) if len(pos) and pos.sum()>0 else np.nan
    checks={"full_available_sum_positive":bool(full.short_funding_simple_sum>0),"primary_full_years_sum_positive":bool(primary.short_funding_simple_sum>0),"pre_2023_positive_if_available":bool(pre.observations==0 or pre.short_funding_simple_sum>0),"post_2023_sum_positive":bool(post.short_funding_simple_sum>0),"majority_completed_full_years_positive":majority,"median_365d_positive":bool(full.median_365d_sum>0),"positive_365d_share_gt_50pct":bool(full.positive_365d_share>0.5),"largest_positive_completed_year_share_lt_50pct":bool(np.isnan(conc) or conc<0.5)}
    carry="STRUCTURAL_SIGNAL_PRESENT" if all(checks.values()) else ("STRUCTURAL_SIGNAL_ABSENT" if not checks["full_available_sum_positive"] else "STRUCTURAL_SIGNAL_MIXED")
    deep=b[b.drawdown_bucket.isin(["DD_35_TO_50","DD_50_PLUS"])]
    if deep.empty: crisis="INSUFFICIENT_DEEP_DRAWDOWN_DATA"; dm=dmed=dpos=np.nan
    else:
        n=deep.observations.sum(); dm=float((deep.mean_rate*deep.observations).sum()/n); dmed=float(deep.median_rate.median()); dpos=float((deep.positive_fraction*deep.observations).sum()/n); crisis="CRISIS_FINANCING_COMPATIBLE" if dm>=0 and dmed>=0 else ("CRISIS_FINANCING_PROCYCLICAL_RISK" if dm<0 and dmed<0 else "CRISIS_FINANCING_MIXED")
    return {"carry_conclusion":carry,"checks":checks,"first_full_calendar_year":first_full,"completed_full_calendar_years":len(cy),"largest_positive_completed_year_share":conc,"crisis_financing_conclusion":crisis,"deep_drawdown_weighted_mean_rate":dm,"deep_drawdown_median_bucket_rate":dmed,"deep_drawdown_positive_fraction":dpos}


def run(work):
    work.mkdir(parents=True,exist_ok=True); out=work/"results"; out.mkdir(parents=True,exist_ok=True); snap=snapshot(work); cutoff=int(snap["cutoff_ms"]); info=instrument_info(work); launch=int(info.get("launchTime") or 0)
    f,raw_f,pages_f=fetch_funding(work,cutoff,launch); idx,raw_i,pages_i=fetch_index(work,cutoff,launch); audit=source_audit(info,f,idx,cutoff,raw_f,pages_f,raw_i,pages_i); atomic_json(out/"r003_x001_bybit_source_audit.json",audit)
    if audit["status"]!="PASS":
        state={"status":"DATA_REDESIGN","engine_version":VERSION,"protocol":PROTOCOL,"created_at_utc":datetime.now(timezone.utc).isoformat(),"source_audit":audit}; atomic_json(out/"r003_x001_bybit_run_state.json",state); print(json.dumps(state,indent=2)); return
    x=merge_state(f,idx); ff=first_full_year(pd.to_datetime(launch,unit="ms",utc=True),f.funding_time.iloc[0]); current=pd.to_datetime(cutoff,unit="ms",utc=True).year; primary=pd.Timestamp(f"{ff}-01-01",tz="UTC"); pre_end=pd.Timestamp("2022-12-31 23:59:59.999999",tz="UTC"); post=pd.Timestamp("2023-01-01",tz="UTC")
    m=pd.DataFrame([metric("FULL_AVAILABLE",x),metric("PRIMARY_FULL_YEARS",x,primary),metric("PRE_2023",x,primary,pre_end),metric("POST_2023",x,post)]); y=yearly(x); b=bucket_table(x); d=decide(m,y,b,ff,current)
    x.to_csv(out/"r003_x001_bybit_funding_clean.csv",index=False); idx.to_csv(out/"r003_x001_bybit_index_daily.csv",index=False); m.to_csv(out/"r003_x001_bybit_metrics.csv",index=False); y.to_csv(out/"r003_x001_bybit_yearly.csv",index=False); b.to_csv(out/"r003_x001_bybit_drawdown_buckets.csv",index=False)
    state={"status":"PASS","engine_version":VERSION,"protocol":PROTOCOL,"created_at_utc":datetime.now(timezone.utc).isoformat(),"evidence_status":"INDEPENDENT_VENUE_STRUCTURAL_REPLICATION_ONLY_NOT_STRATEGY_PASS","venue":"Bybit","symbol":SYMBOL,"snapshot_cutoff_utc":audit["snapshot_cutoff_utc"],"first_full_calendar_year":ff,"funding_rows_clean":len(f),"funding_rows_without_causal_index_state":int(x.drawdown.isna().sum()),"decision":d,"outputs":["r003_x001_bybit_run_state.json","r003_x001_bybit_source_audit.json","r003_x001_bybit_funding_clean.csv","r003_x001_bybit_index_daily.csv","r003_x001_bybit_metrics.csv","r003_x001_bybit_yearly.csv","r003_x001_bybit_drawdown_buckets.csv","r003_x001_bybit_summary.md"]}; atomic_json(out/"r003_x001_bybit_run_state.json",state)
    mm=m.set_index("slice"); pct=lambda v:"n/a" if pd.isna(v) else f"{float(v):.2%}"; md="# R003-X001 Bybit Funding-Premium Structural Replication — Raw Output v0.1\n\n**Status:** independent-venue structural replication only; not an executable strategy PASS.\n\n"; md+=f"- Data gate: **{audit['status']}**\n- Bybit BTCUSDT launch: **{audit['instrument']['launchTimeUtc']}**\n- Funding observations: **{len(f):,}**\n- First full calendar year: **{ff}**\n- Carry conclusion: **{d['carry_conclusion']}**\n- Crisis-financing conclusion: **{d['crisis_financing_conclusion']}**\n\n| Slice | Simple sum | Compounded* | Positive | Median 365d | Positive 365d | Latest 365d | Worst 30d |\n|---|---:|---:|---:|---:|---:|---:|---:|\n"
    for s in ["FULL_AVAILABLE","PRIMARY_FULL_YEARS","PRE_2023","POST_2023"]:
        r=mm.loc[s]; md+=f"| {s} | {pct(r.short_funding_simple_sum)} | {pct(r.short_funding_compounded)} | {pct(r.positive_fraction)} | {pct(r.median_365d_sum)} | {pct(r.positive_365d_share)} | {pct(r.latest_365d_sum)} | {pct(r.worst_30d_sum)} |\n"
    md+="\n*Compounded funding is descriptive only. X001 excludes basis P&L, two-leg costs, margin/liquidation mechanics, slippage and counterparty risk. If the structural gate is present, only then freeze Bybit X002 implementation replication.\n"; (out/"r003_x001_bybit_summary.md").write_text(md,encoding="utf-8"); print(md)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--workspace",type=Path,required=True); a=ap.parse_args()
    try: run(a.workspace)
    except Exception as e:
        out=a.workspace/"results"; out.mkdir(parents=True,exist_ok=True); atomic_json(out/"r003_x001_bybit_run_state.json",{"status":"SOURCE_OR_ENGINE_ERROR","engine_version":VERSION,"protocol":PROTOCOL,"created_at_utc":datetime.now(timezone.utc).isoformat(),"error_type":type(e).__name__,"error":str(e)}); raise

if __name__=="__main__": main()
