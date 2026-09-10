"""R009-X002 fixed cross-asset breadth panel v0.1."""
from __future__ import annotations
import argparse, hashlib, json, math, os, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

VERSION="0.1"
PROTOCOL="r009-x002-cross-asset-breadth-panel-v0.1"
BASE="https://data-api.binance.vision"
PATH="/api/v3/klines"
INTERVAL="1d"
SYMBOLS=["BNBUSDT","LTCUSDT","XRPUSDT","ADAUSDT","SOLUSDT"]
SMA_LOOKBACK=120
TREND_WEIGHT=0.10
CRISIS_TRANCHE=0.025
CRISIS_THRESH=(-0.20,-0.35,-0.50,-0.65)
FEES=(0.0005,0.0010,0.0025,0.0050)
BASE_FEE=0.0010
DAYS_PER_YEAR=365.25
EPS=1e-12
MIN_ONE_DAY_GAP_SHARE=0.98
MAX_ALLOWED_GAP_DAYS=7

def atomic_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=str),encoding="utf-8")
    os.replace(tmp,path)

def get_json(url,params,retries=5):
    for i in range(retries):
        try:
            req=Request(url+"?"+urlencode(params),headers={"User-Agent":"botmarketplace-r009-x002/0.1"})
            with urlopen(req,timeout=60) as r:
                raw=r.read()
            obj=json.loads(raw.decode("utf-8"))
            if not isinstance(obj,list):
                raise RuntimeError(f"Unexpected response: {obj}")
            return raw,obj
        except Exception:
            if i+1==retries:
                raise
            time.sleep(min(2**i,8))

def snapshot(work):
    p=work/"snapshot.json"
    if p.exists():
        x=json.loads(p.read_text(encoding="utf-8"))
        if x.get("protocol")!=PROTOCOL:
            raise RuntimeError("Workspace protocol mismatch")
        return x
    now=datetime.now(timezone.utc)
    x={"protocol":PROTOCOL,"created_at_utc":now.isoformat(),"cutoff_ms":int(now.timestamp()*1000)}
    atomic_json(p,x)
    return x

def load_pages(path):
    if not path.exists():
        return []
    out=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out

def append_page(path,page,sha):
    path.parent.mkdir(parents=True,exist_ok=True)
    rec={"sha256":sha,"rows":page}
    with open(path,"a",encoding="utf-8") as f:
        f.write(json.dumps(rec,separators=(",",":"))+"\n")
        f.flush(); os.fsync(f.fileno())

def fetch_symbol(work,symbol,cutoff_ms):
    cp=work/"_cache"/f"{symbol}_pages.jsonl"
    pages=load_pages(cp)
    rows=[]; hashes=[]
    start=0
    for rec in pages:
        page=rec["rows"]; rows+=page; hashes.append(rec["sha256"])
        if page:
            start=max(start,int(page[-1][0])+1)
    done=bool(pages and (not pages[-1]["rows"] or len(pages[-1]["rows"])<1000 or int(pages[-1]["rows"][-1][0])>=cutoff_ms))
    if pages:
        print(f"{symbol}: resumed {len(pages)} cached pages")
    while not done:
        raw,page=get_json(BASE+PATH,{"symbol":symbol,"interval":INTERVAL,"startTime":start,"limit":1000})
        sha=hashlib.sha256(raw).hexdigest()
        append_page(cp,page,sha)
        rows+=page; hashes.append(sha)
        print(f"{symbol}: page {len(hashes)}, raw rows {len(rows):,}")
        if not page:
            done=True
        else:
            last=int(page[-1][0]); start=last+1
            done=len(page)<1000 or last>=cutoff_ms
    parsed=[]
    for r in rows:
        if not isinstance(r,list) or len(r)<7:
            continue
        if int(r[6])>=cutoff_ms:
            continue
        parsed.append({
            "date":pd.to_datetime(int(r[0]),unit="ms",utc=True).tz_convert(None).normalize(),
            "open":float(r[1]),"high":float(r[2]),"low":float(r[3]),"close":float(r[4]),
            "volume":float(r[5]),"close_time_ms":int(r[6])
        })
    x=pd.DataFrame(parsed)
    if x.empty:
        raise RuntimeError(f"{symbol}: no fully closed bars")
    dup=int(x["date"].duplicated().sum())
    x=x.sort_values("date").drop_duplicates("date",keep="last").reset_index(drop=True)
    if (x[["open","high","low","close"]]<=0).any().any():
        raise RuntimeError(f"{symbol}: non-positive price")
    return x,hashes,dup,len(rows)

def audit_source(symbol,x,hashes,dup,raw_rows):
    gaps=x["date"].diff().dt.days.dropna()
    one=float((gaps==1).mean()) if len(gaps) else 0.0
    maxgap=int(gaps.max()) if len(gaps) else 0
    missing=int((gaps[gaps>1]-1).sum()) if len(gaps) else 0
    ok=(len(x)>=1000 and one>=MIN_ONE_DAY_GAP_SHARE and maxgap<=MAX_ALLOWED_GAP_DAYS)
    first=x["date"].iloc[0]
    ff=int(first.year if (first.month,first.day)==(1,1) else first.year+1)
    return {
        "symbol":symbol,"status":"PASS" if ok else "DATA_REDESIGN","raw_rows":raw_rows,
        "clean_rows":len(x),"clean_start":x["date"].iloc[0].date().isoformat(),
        "clean_end":x["date"].iloc[-1].date().isoformat(),"first_full_calendar_year":ff,
        "duplicate_dates_before_dedup":dup,"one_day_gap_share":one,
        "max_gap_days":maxgap,"missing_days":missing,"page_sha256":";".join(hashes)
    }

def build_state(x):
    s=x[["date","close"]].copy().set_index("date")
    s["sma120"]=s["close"].rolling(SMA_LOOKBACK,min_periods=SMA_LOOKBACK).mean()
    s["trend_on"]=(s["close"]>s["sma120"]) & s["sma120"].notna()
    s["trend_target"]=np.where(s["trend_on"],TREND_WEIGHT,0.0)
    peak=float(s["close"].iloc[0]); sticky=[False]*4
    crisis=[]; dds=[]; levels=[]; events=[]; event_no=0; active=None
    for i,(date,p0) in enumerate(s["close"].items()):
        p=float(p0); new_ath=(i==0 or p>peak+EPS)
        if new_ath:
            if i>0 and active is not None:
                active["reset_date"]=date; active["status"]="CLOSED"; events.append(active); active=None
            peak=p; sticky=[False]*4; dd=0.0
        else:
            dd=p/peak-1.0; newly=[]
            for j,t in enumerate(CRISIS_THRESH):
                if (not sticky[j]) and dd<=t+EPS:
                    sticky[j]=True; newly.append(j)
            if newly and active is None:
                event_no+=1
                active={"event_id":event_no,"first_breach_date":date,"reset_date":pd.NaT,"status":"OPEN","max_drawdown":dd}
            if active is not None and dd<float(active["max_drawdown"]):
                active["max_drawdown"]=dd
        levels.append(sum(sticky)); crisis.append(CRISIS_TRANCHE*sum(sticky)); dds.append(dd)
    if active is not None:
        active["status"]="OPEN_CENSORED"; events.append(active)
    s["drawdown"]=dds; s["crisis_level"]=levels; s["crisis_target"]=crisis
    s["combined_target"]=s["trend_target"]+s["crisis_target"]
    s["permanent10_plus_crisis"]=TREND_WEIGHT+s["crisis_target"]
    return s,pd.DataFrame(events)

def simulate_daily(price,target,fee):
    idx=price.index; target=target.reindex(idx).astype(float)
    out=[]; w=float(target.iloc[0]); eq=1.0-fee*abs(w)
    out.append({"net_return":-fee*abs(w),"equity":eq,"held_weight":0.0,"desired_target":w,
                "turnover":abs(w),"fee_cost":fee*abs(w)})
    for i in range(1,len(idx)):
        r=float(price.iloc[i]/price.iloc[i-1]-1.0)
        held=w; gross=1.0+held*r
        pre=held*(1.0+r)/gross if gross>0 else 0.0
        desired=float(target.iloc[i]); turn=abs(desired-pre); cost=fee*turn
        net=gross-1.0-cost; eq*=1.0+net; w=desired
        out.append({"net_return":net,"equity":eq,"held_weight":held,"desired_target":desired,
                    "turnover":turn,"fee_cost":cost})
    return pd.DataFrame(out,index=idx)

def simulate_static_monthly(price,weight,fee):
    idx=price.index; out=[]; w=float(weight); eq=1.0-fee*abs(w)
    out.append({"net_return":-fee*abs(w),"equity":eq,"held_weight":0.0,"desired_target":weight,
                "turnover":abs(w),"fee_cost":fee*abs(w)})
    for i in range(1,len(idx)):
        r=float(price.iloc[i]/price.iloc[i-1]-1.0)
        held=w; gross=1.0+held*r
        pre=held*(1.0+r)/gross if gross>0 else 0.0
        is_me=(i==len(idx)-1) or (idx[i+1].month!=idx[i].month)
        turn=abs(weight-pre) if is_me else 0.0; cost=fee*turn
        net=gross-1.0-cost; eq*=1.0+net; w=weight if is_me else pre
        out.append({"net_return":net,"equity":eq,"held_weight":held,"desired_target":weight,
                    "turnover":turn,"fee_cost":cost})
    return pd.DataFrame(out,index=idx)

def metric(asset,strategy,fee,sim,slice_name,start,end=None):
    x=sim[sim.index>=start]
    if end is not None: x=x[x.index<=end]
    if len(x)<2: return None
    r=x["net_return"]; eq=(1+r).cumprod()
    years=(eq.index[-1]-eq.index[0]).days/DAYS_PER_YEAR
    cagr=float(eq.iloc[-1]**(1/years)-1) if years>0 else np.nan
    dd=float((eq/eq.cummax()-1).min())
    return {"asset":asset,"strategy":strategy,"fee_bps":fee*10000,"slice":slice_name,
            "start":eq.index[0].date().isoformat(),"end":eq.index[-1].date().isoformat(),
            "observations":len(eq),"cagr":cagr,"ending_multiple":float(eq.iloc[-1]),
            "max_drawdown":dd,"calmar":cagr/abs(dd) if dd<0 else np.nan,
            "avg_held_weight":float(x["held_weight"].mean()),"max_held_weight":float(x["held_weight"].max()),
            "turnover":float(x["turnover"].sum()),"fee_drag":float(x["fee_cost"].sum())}

def state_diag(asset,state,slice_name,start,end=None):
    x=state[state.index>=start]
    if end is not None: x=x[x.index<=end]
    if x.empty: return None
    return {"asset":asset,"slice":slice_name,"observations":len(x),
            "trend_on_fraction":float(x.trend_on.mean()),
            "crisis_active_fraction":float((x.crisis_level>0).mean()),
            "crisis_full_fraction":float((x.crisis_level==4).mean()),
            "avg_trend_target":float(x.trend_target.mean()),
            "avg_crisis_target":float(x.crisis_target.mean()),
            "avg_combined_target":float(x.combined_target.mean())}

def decide_asset(asset,m,pre_eligible):
    mm=m[(m.asset==asset)&(m.fee_bps==10)].set_index(["strategy","slice"])
    def g(strategy,slice_name,col):
        try: return float(mm.loc[(strategy,slice_name),col])
        except Exception: return np.nan
    pri="PRIMARY_FULL_YEARS"; rep="REPLAY_2020"; pre="PRE_2020"
    checks={
      "primary_combined_gt_static10": g("R009_COMBINED_DAILY",pri,"cagr")>g("STATIC10_DAILY",pri,"cagr"),
      "primary_combined_gt_trend10": g("R009_COMBINED_DAILY",pri,"cagr")>g("TREND10_DAILY",pri,"cagr"),
      "replay2020_combined_gt_static10": g("R009_COMBINED_DAILY",rep,"cagr")>g("STATIC10_DAILY",rep,"cagr"),
      "replay2020_combined_gt_trend10": g("R009_COMBINED_DAILY",rep,"cagr")>g("TREND10_DAILY",rep,"cagr"),
      "primary_not_pareto_dominated_static15_daily": not (
          g("STATIC15_DAILY",pri,"cagr")>=g("R009_COMBINED_DAILY",pri,"cagr") and
          abs(g("STATIC15_DAILY",pri,"max_drawdown"))<=abs(g("R009_COMBINED_DAILY",pri,"max_drawdown"))
      ),
      "primary_not_pareto_dominated_static15_monthly": not (
          g("STATIC15_MONTHLY",pri,"cagr")>=g("R009_COMBINED_DAILY",pri,"cagr") and
          abs(g("STATIC15_MONTHLY",pri,"max_drawdown"))<=abs(g("R009_COMBINED_DAILY",pri,"max_drawdown"))
      ),
      "primary_dd_better_than_static20_daily": abs(g("R009_COMBINED_DAILY",pri,"max_drawdown"))<abs(g("STATIC20_DAILY",pri,"max_drawdown")),
      "primary_dd_better_than_static20_monthly": abs(g("R009_COMBINED_DAILY",pri,"max_drawdown"))<abs(g("STATIC20_MONTHLY",pri,"max_drawdown")),
      "primary_dd_better_than_permanent10_crisis_ref": abs(g("R009_COMBINED_DAILY",pri,"max_drawdown"))<abs(g("PERMANENT10_PLUS_CRISIS10_REF",pri,"max_drawdown")),
      "primary_avg_target_lt_15pct": g("R009_COMBINED_DAILY",pri,"avg_held_weight")<0.15,
      "primary_crisis10_ending_gt_1": g("CRISIS10_DAILY",pri,"ending_multiple")>1.0,
    }
    if pre_eligible:
        checks["pre2020_combined_gt_static10"]=g("R009_COMBINED_DAILY",pre,"cagr")>g("STATIC10_DAILY",pre,"cagr")
        checks["pre2020_combined_gt_trend10"]=g("R009_COMBINED_DAILY",pre,"cagr")>g("TREND10_DAILY",pre,"cagr")
    mm50=m[(m.asset==asset)&(m.fee_bps==50)].set_index(["strategy","slice"])
    def g50(strategy,slice_name,col):
        try:return float(mm50.loc[(strategy,slice_name),col])
        except Exception:return np.nan
    checks["fee50_primary_combined_gt_static10"]=g50("R009_COMBINED_DAILY",pri,"cagr")>g50("STATIC10_DAILY",pri,"cagr")
    checks["fee50_primary_combined_gt_trend10"]=g50("R009_COMBINED_DAILY",pri,"cagr")>g50("TREND10_DAILY",pri,"cagr")
    checks["fee50_primary_not_pareto_dominated_static15_daily"]=not (
        g50("STATIC15_DAILY",pri,"cagr")>=g50("R009_COMBINED_DAILY",pri,"cagr") and
        abs(g50("STATIC15_DAILY",pri,"max_drawdown"))<=abs(g50("R009_COMBINED_DAILY",pri,"max_drawdown"))
    )
    hard={
      "primary_combined_cagr_positive":g("R009_COMBINED_DAILY",pri,"cagr")>0,
      "primary_combined_gt_static10":checks["primary_combined_gt_static10"],
      "primary_combined_gt_trend10":checks["primary_combined_gt_trend10"],
      "crisis10_ending_gt1":checks["primary_crisis10_ending_gt_1"],
      "avg_target_lt15":checks["primary_avg_target_lt_15pct"],
      "dd_better_than_static20_daily":checks["primary_dd_better_than_static20_daily"],
      "fee50_combined_cagr_positive":g50("R009_COMBINED_DAILY",pri,"cagr")>0,
    }
    if all(checks.values()): decision="SUPPORT"
    elif not all(hard.values()): decision="FAIL"
    else: decision="MIXED"
    return decision,checks,hard

def run(work):
    work.mkdir(parents=True,exist_ok=True); out=work/"results"; out.mkdir(parents=True,exist_ok=True)
    snap=snapshot(work); cutoff=int(snap["cutoff_ms"])
    audits=[]; metric_rows=[]; diag_rows=[]; event_rows=[]; state_rows=[]; decisions=[]
    for symbol in SYMBOLS:
        x,hashes,dup,raw_rows=fetch_symbol(work,symbol,cutoff)
        audit=audit_source(symbol,x,hashes,dup,raw_rows); audits.append(audit)
        if audit["status"]!="PASS": continue
        asset=symbol.replace("USDT","")
        state,events=build_state(x)
        state2=state.reset_index(); state2.insert(0,"asset",asset); state_rows.append(state2)
        if not events.empty:
            events=events.copy(); events.insert(0,"asset",asset); event_rows.append(events)
        price=state["close"]
        targets={
          "R009_COMBINED_DAILY":state["combined_target"],
          "TREND10_DAILY":state["trend_target"],
          "CRISIS10_DAILY":state["crisis_target"],
          "PERMANENT10_PLUS_CRISIS10_REF":state["permanent10_plus_crisis"],
          "STATIC10_DAILY":pd.Series(0.10,index=state.index),
          "STATIC15_DAILY":pd.Series(0.15,index=state.index),
          "STATIC20_DAILY":pd.Series(0.20,index=state.index),
        }
        ff=audit["first_full_calendar_year"]; primary=pd.Timestamp(f"{ff}-01-01")
        pre_end=pd.Timestamp("2019-12-31"); replay=pd.Timestamp("2020-01-01"); post=pd.Timestamp("2023-01-01")
        pre_count=int(((state.index>=primary)&(state.index<=pre_end)).sum())
        pre_eligible=pre_count>=365
        slices=[("PRIMARY_FULL_YEARS",primary,None),("REPLAY_2020",replay,None),("POST_2023",post,None)]
        if pre_eligible: slices.append(("PRE_2020",primary,pre_end))
        for fee in FEES:
            sims={k:simulate_daily(price,v,fee) for k,v in targets.items()}
            sims["STATIC10_MONTHLY"]=simulate_static_monthly(price,0.10,fee)
            sims["STATIC15_MONTHLY"]=simulate_static_monthly(price,0.15,fee)
            sims["STATIC20_MONTHLY"]=simulate_static_monthly(price,0.20,fee)
            for sname,start,end in slices:
                for name,sim in sims.items():
                    r=metric(asset,name,fee,sim,sname,start,end)
                    if r: metric_rows.append(r)
        for sname,start,end in slices:
            d=state_diag(asset,state,sname,start,end)
            if d: diag_rows.append(d)
        mtmp=pd.DataFrame(metric_rows)
        dec,checks,hard=decide_asset(asset,mtmp,pre_eligible)
        pri=mtmp[(mtmp.asset==asset)&(mtmp.fee_bps==10)&(mtmp.slice=="PRIMARY_FULL_YEARS")&
                  (mtmp.strategy=="R009_COMBINED_DAILY")].iloc[0]
        decisions.append({
            "asset":asset,"symbol":symbol,"decision":dec,"pre2020_eligible":pre_eligible,
            "primary_cagr":float(pri.cagr),"primary_max_drawdown":float(pri.max_drawdown),
            "primary_calmar":float(pri.calmar),"primary_avg_held_weight":float(pri.avg_held_weight),
            "checks_json":json.dumps(checks,sort_keys=True),"hard_checks_json":json.dumps(hard,sort_keys=True)
        })
    aud=pd.DataFrame(audits); met=pd.DataFrame(metric_rows); dia=pd.DataFrame(diag_rows)
    decdf=pd.DataFrame(decisions)
    support=int((decdf.decision=="SUPPORT").sum()) if len(decdf) else 0
    fail=int((decdf.decision=="FAIL").sum()) if len(decdf) else 0
    mixed=int((decdf.decision=="MIXED").sum()) if len(decdf) else 0
    if len(decdf)!=len(SYMBOLS) or (aud.status!="PASS").any():
        panel="DATA_REDESIGN"
    elif support>=4 and fail==0:
        panel="CROSS_ASSET_BREADTH_SUPPORT"
    elif fail>=3:
        panel="CROSS_ASSET_BREADTH_REJECTED"
    else:
        panel="CROSS_ASSET_BREADTH_MIXED"
    state_long=pd.concat(state_rows,ignore_index=True) if state_rows else pd.DataFrame()
    events_long=pd.concat(event_rows,ignore_index=True) if event_rows else pd.DataFrame()
    aud.to_csv(out/"r009_x002_source_audit.csv",index=False)
    decdf.to_csv(out/"r009_x002_asset_decisions.csv",index=False)
    met.to_csv(out/"r009_x002_metrics.csv",index=False)
    dia.to_csv(out/"r009_x002_state_diagnostics.csv",index=False)
    state_long.to_csv(out/"r009_x002_state_daily_long.csv",index=False)
    events_long.to_csv(out/"r009_x002_crisis_events.csv",index=False)
    state={
      "status":"PASS" if panel!="DATA_REDESIGN" else "DATA_REDESIGN",
      "engine_version":VERSION,"protocol":PROTOCOL,
      "created_at_utc":datetime.now(timezone.utc).isoformat(),
      "snapshot_cutoff_utc":pd.to_datetime(cutoff,unit="ms",utc=True).isoformat(),
      "symbols":SYMBOLS,"asset_count":len(decdf),"support_count":support,"mixed_count":mixed,"fail_count":fail,
      "panel_decision":panel,
      "evidence_status":"POST_ETH_FIXED_BREADTH_DIAGNOSTIC_NOT_INDEPENDENT_CONFIRMATION",
      "outputs":["r009_x002_run_state.json","r009_x002_source_audit.csv","r009_x002_asset_decisions.csv",
                 "r009_x002_metrics.csv","r009_x002_state_diagnostics.csv","r009_x002_state_daily_long.csv",
                 "r009_x002_crisis_events.csv","r009_x002_summary.md"]
    }
    atomic_json(out/"r009_x002_run_state.json",state)
    lines=["# R009-X002 Cross-Asset Breadth Panel — Raw Output v0.1","",
           f"- Panel decision: **{panel}**",f"- Assets: {', '.join([s.replace('USDT','') for s in SYMBOLS])}",
           f"- SUPPORT / MIXED / FAIL: **{support} / {mixed} / {fail}**","",
           "| Asset | Decision | CAGR | Max DD | Calmar | Avg risky weight |","|---|---|---:|---:|---:|---:|"]
    for r in decisions:
        lines.append(f"| {r['asset']} | {r['decision']} | {r['primary_cagr']:.2%} | {r['primary_max_drawdown']:.2%} | {r['primary_calmar']:.2f} | {r['primary_avg_held_weight']:.2%} |")
    lines+=["","This is a fixed breadth diagnostic after the ETH result. It is not independent confirmatory evidence, does not authorize parameter tuning, and no best-performing coin may be selected as a replacement strategy."]
    (out/"r009_x002_summary.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--workspace",type=Path,required=True); a=ap.parse_args()
    try: run(a.workspace)
    except Exception as e:
        out=a.workspace/"results"; out.mkdir(parents=True,exist_ok=True)
        atomic_json(out/"r009_x002_run_state.json",{
            "status":"SOURCE_OR_ENGINE_ERROR","engine_version":VERSION,"protocol":PROTOCOL,
            "created_at_utc":datetime.now(timezone.utc).isoformat(),
            "error_type":type(e).__name__,"error":str(e)})
        raise

if __name__=="__main__": main()
