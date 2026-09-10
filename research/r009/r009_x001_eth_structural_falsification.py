"""R009-X001 ETH unchanged-rule structural falsification v0.1."""
from __future__ import annotations
import argparse, gzip, hashlib, json, math, os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import numpy as np
import pandas as pd

VERSION="0.1"
PROTOCOL="r009-x001-eth-unchanged-rule-structural-falsification-v0.1"
SYMBOL="ETHUSDT"
URL="https://data-api.binance.vision/api/v3/klines"
SEARCH_START=pd.Timestamp("2017-01-01", tz="UTC")
SMA=120
TREND_W=0.10
TRANCHE=0.025
THRESH=(-0.20,-0.35,-0.50,-0.65)
LEVELS=(20,35,50,65)
FEES=(0.0005,0.0010,0.0025,0.0050)
BASE_FEE=0.0010
EPS=1e-12
DAYS_PER_YEAR=365.25
MIN_ONE_DAY_SHARE=0.98
MAX_GAP_DAYS=7
HORIZONS=(7,30,90,180,365)

def atomic_bytes(path:Path,data:bytes):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    with open(tmp,"wb") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)

def atomic_json(path:Path,obj):
    atomic_bytes(path,json.dumps(obj,indent=2,ensure_ascii=False,default=str).encode())

def get_raw(params):
    req=Request(URL+"?"+urlencode(params),headers={"User-Agent":"botmarketplace-r009-x001-eth/0.1"})
    with urlopen(req,timeout=90) as r: raw=r.read()
    obj=json.loads(raw.decode())
    if not isinstance(obj,list): raise RuntimeError(f"Binance source error: {obj}")
    return raw,obj

def snapshot(work:Path):
    p=work/"snapshot.json"
    if p.exists():
        x=json.loads(p.read_text())
        if x.get("protocol")!=PROTOCOL: raise RuntimeError("Workspace protocol mismatch")
        return x
    now=datetime.now(timezone.utc)
    x={"protocol":PROTOCOL,"created_at_utc":now.isoformat(),"cutoff_ms":int(now.timestamp()*1000)}
    atomic_json(p,x); return x

def fetch_price(work:Path,cutoff_ms:int):
    cache=work/"_cache"; cache.mkdir(parents=True,exist_ok=True)
    manifest_path=cache/"manifest.json"
    if manifest_path.exists():
        m=json.loads(manifest_path.read_text())
        if m.get("protocol")!=PROTOCOL or int(m.get("cutoff_ms",-1))!=cutoff_ms:
            raise RuntimeError("Cache manifest mismatch")
    else:
        m={"protocol":PROTOCOL,"cutoff_ms":cutoff_ms,"complete":False,"pages":[]}
        atomic_json(manifest_path,m)
    rows=[]; hashes=[]; start=int(SEARCH_START.timestamp()*1000)
    for meta in m["pages"]:
        raw=gzip.decompress((cache/meta["file"]).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=meta["sha256"]: raise RuntimeError("Cached page checksum mismatch")
        obj=json.loads(raw.decode()); rows.extend(obj); hashes.append(meta["sha256"])
        if obj: start=int(obj[-1][0])+1
    if m["pages"]: print(f"price: resumed {len(m['pages'])} cached pages")
    while not m.get("complete",False):
        raw,obj=get_raw({"symbol":SYMBOL,"interval":"1d","startTime":start,"endTime":cutoff_ms,"limit":1000})
        name=f"page_{len(m['pages']):04d}.json.gz"
        atomic_bytes(cache/name,gzip.compress(raw,compresslevel=6))
        meta={"file":name,"sha256":hashlib.sha256(raw).hexdigest(),"rows":len(obj)}
        m["pages"].append(meta); atomic_json(manifest_path,m)
        rows.extend(obj); hashes.append(meta["sha256"])
        print(f"price: page {len(m['pages'])}, raw rows {len(rows):,}")
        if not obj or len(obj)<1000:
            m["complete"]=True; atomic_json(manifest_path,m); break
        start=int(obj[-1][0])+1
    valid=[r for r in rows if isinstance(r,list) and len(r)>=7 and int(r[6])<cutoff_ms]
    if not valid: raise RuntimeError("No fully closed ETHUSDT daily bars")
    x=pd.DataFrame(valid)
    z=pd.DataFrame({
        "date":pd.to_datetime(pd.to_numeric(x.iloc[:,0]),unit="ms",utc=True).dt.tz_convert(None).dt.normalize(),
        "open":pd.to_numeric(x.iloc[:,1],errors="coerce"),
        "high":pd.to_numeric(x.iloc[:,2],errors="coerce"),
        "low":pd.to_numeric(x.iloc[:,3],errors="coerce"),
        "price":pd.to_numeric(x.iloc[:,4],errors="coerce"),
        "close_time":pd.to_datetime(pd.to_numeric(x.iloc[:,6]),unit="ms",utc=True)
    }).dropna()
    dup=int(z.date.duplicated().sum())
    z=z[(z[["open","high","low","price"]]>0).all(axis=1)].sort_values("date").drop_duplicates("date",keep="last").reset_index(drop=True)
    return z,hashes,len(rows),dup

def first_full_year(first_date):
    d=pd.Timestamp(first_date)
    return d.year if (d.month,d.day)==(1,1) else d.year+1

def audit(z,hashes,raw_rows,dup,cutoff):
    ff=first_full_year(z.date.iloc[0]); p=z[z.date>=pd.Timestamp(f"{ff}-01-01")]
    pg=p.date.diff().dt.days.dropna(); one=float((pg==1).mean()) if len(pg) else 0.0; mx=int(pg.max()) if len(pg) else 0
    passed=len(p)>=1000 and one>=MIN_ONE_DAY_SHARE and mx<=MAX_GAP_DAYS
    return {"status":"PASS" if passed else "DATA_REDESIGN","venue":"Binance Spot","symbol":SYMBOL,"source":URL,
            "snapshot_cutoff_utc":pd.to_datetime(cutoff,unit="ms",utc=True).isoformat(),"raw_rows":raw_rows,"clean_rows":len(z),
            "clean_start":z.date.iloc[0].date().isoformat(),"clean_end":z.date.iloc[-1].date().isoformat(),
            "first_full_calendar_year":ff,"duplicate_dates_before_dedup":dup,"page_sha256":hashes,"primary_rows":len(p),
            "primary_one_day_gap_share":one,"primary_max_gap_days":mx,
            "primary_missing_days":int((pg[pg>1]-1).sum()) if len(pg) else 0,
            "gate_min_one_day_share":MIN_ONE_DAY_SHARE,"gate_max_gap_days":MAX_GAP_DAYS}

def build_state(price:pd.Series):
    ma=price.rolling(SMA,min_periods=SMA).mean(); trend=(price>ma)&ma.notna()
    peak=float(price.iloc[0]); peak_date=price.index[0]; sticky=[False]*4; active=None; event_no=0; states=[]; events=[]
    for i,(d,v) in enumerate(price.items()):
        p=float(v); new=(i==0 or p>peak+EPS)
        if new:
            if i>0 and active is not None:
                active["reset_date"]=d; active["status"]="CLOSED"; events.append(active); active=None
            peak=p; peak_date=d; sticky=[False]*4; dd=0.0
        else:
            dd=p/peak-1.0; newly=[]
            for j,t in enumerate(THRESH):
                if not sticky[j] and dd<=t+EPS: sticky[j]=True; newly.append(j)
            if newly and active is None:
                event_no+=1
                active={"event_id":event_no,"prior_peak_date":peak_date,"first_breach_date":d,"reset_date":pd.NaT,
                        "status":"OPEN","max_drawdown":dd,"max_drawdown_date":d,**{f"breach_{q}_date":pd.NaT for q in LEVELS}}
            if active is not None:
                if dd<float(active["max_drawdown"]): active["max_drawdown"]=dd; active["max_drawdown_date"]=d
                for j in newly:
                    k=f"breach_{LEVELS[j]}_date"
                    if pd.isna(active[k]): active[k]=d
        cl=sum(sticky); ct=TRANCHE*cl; tt=TREND_W if bool(trend.loc[d]) else 0.0
        states.append({"date":d,"price":p,"sma120":float(ma.loc[d]) if pd.notna(ma.loc[d]) else np.nan,"trend_on":bool(trend.loc[d]),
                       "trend_target":tt,"running_peak_price":peak,"running_peak_date":peak_date,"drawdown":dd,"crisis_level":int(cl),
                       "crisis_target":ct,"combined_target":tt+ct,"permanent10_plus_crisis_target":TREND_W+ct,
                       "event_id":active["event_id"] if active else np.nan,"new_ath":new})
    if active is not None: active["status"]="OPEN_CENSORED"; events.append(active)
    return pd.DataFrame(states).set_index("date"),pd.DataFrame(events)

def sim_daily(price,target,fee):
    target=target.reindex(price.index).astype(float); idx=price.index; out=[]; w=float(target.iloc[0]); eq=1-fee*abs(w)
    out.append({"asset_return":0.0,"desired_target":w,"held_weight":0.0,"pretrade_weight":0.0,"turnover":abs(w),"fee_cost":fee*abs(w),"net_return":-fee*abs(w),"equity":eq})
    for i in range(1,len(idx)):
        r=float(price.iloc[i]/price.iloc[i-1]-1); held=w; gf=1+held*r; pre=held*(1+r)/gf if gf>0 else 0.0
        desired=float(target.iloc[i]); turn=abs(desired-pre); cost=fee*turn; net=gf-1-cost; eq*=1+net; w=desired
        out.append({"asset_return":r,"desired_target":desired,"held_weight":held,"pretrade_weight":pre,"turnover":turn,"fee_cost":cost,"net_return":net,"equity":eq})
    return pd.DataFrame(out,index=idx)

def sim_monthly(price,weight,fee):
    idx=price.index; out=[]; w=float(weight); eq=1-fee*abs(w)
    out.append({"asset_return":0.0,"desired_target":weight,"held_weight":0.0,"pretrade_weight":0.0,"turnover":abs(w),"fee_cost":fee*abs(w),"net_return":-fee*abs(w),"equity":eq})
    for i in range(1,len(idx)):
        r=float(price.iloc[i]/price.iloc[i-1]-1); held=w; gf=1+held*r; pre=held*(1+r)/gf if gf>0 else 0.0
        me=(i==len(idx)-1) or (idx[i+1].month!=idx[i].month); turn=abs(weight-pre) if me else 0.0; cost=fee*turn; net=gf-1-cost; eq*=1+net; w=weight if me else pre
        out.append({"asset_return":r,"desired_target":weight,"held_weight":held,"pretrade_weight":pre,"turnover":turn,"fee_cost":cost,"net_return":net,"equity":eq})
    return pd.DataFrame(out,index=idx)

def period_ret(r,freq): return (1+r).groupby(r.index.to_period(freq)).prod()-1

def cvar(r,q):
    v=float(r.quantile(q)); t=r[r<=v]; return v,float(t.mean()) if len(t) else np.nan

def longest_dd(eq):
    peak=eq.cummax(); under=eq<peak-EPS; start=None; best=0
    for d,f in under.items():
        if f and start is None: start=d
        elif not f and start is not None: best=max(best,(d-start).days); start=None
    if start is not None: best=max(best,(eq.index[-1]-start).days)
    return int(best)

def metric(name,fee,sim,slice_name,start,end=None):
    x=sim[sim.index>=start]
    if end is not None: x=x[x.index<=end]
    if len(x)<2: return None
    r=x.net_return; eq=(1+r).cumprod(); years=max((eq.index[-1]-eq.index[0]).days/DAYS_PER_YEAR,1/DAYS_PER_YEAR)
    cagr=float(eq.iloc[-1]**(1/years)-1); dd=float((eq/eq.cummax()-1).min()); yr=period_ret(r,"Y"); qr=period_ret(r,"Q"); mo=period_ret(r,"M"); roll=(eq/eq.shift(365)-1).dropna(); v1,c1=cvar(r,0.01); v5,c5=cvar(r,0.05)
    return {"strategy":name,"fee_bps":fee*10000,"slice":slice_name,"start":eq.index[0].date().isoformat(),"end":eq.index[-1].date().isoformat(),"observations":len(eq),
            "cagr":cagr,"ending_multiple":float(eq.iloc[-1]),"annualized_vol":float(r.std(ddof=0)*math.sqrt(365)),"max_drawdown":dd,"calmar":cagr/abs(dd) if dd<0 else np.nan,
            "worst_calendar_year":float(yr.min()) if len(yr) else np.nan,"worst_calendar_quarter":float(qr.min()) if len(qr) else np.nan,"worst_calendar_month":float(mo.min()) if len(mo) else np.nan,
            "worst_rolling_365d":float(roll.min()) if len(roll) else np.nan,"longest_drawdown_days":longest_dd(eq),"avg_held_weight":float(x.held_weight.mean()),"max_held_weight":float(x.held_weight.max()),
            "turnover":float(x.turnover.sum()),"fee_drag":float(x.fee_cost.sum()),"var_1pct":v1,"cvar_1pct":c1,"var_5pct":v5,"cvar_5pct":c5}

def state_diag(st,name,start,end=None):
    x=st[st.index>=start]
    if end is not None: x=x[x.index<=end]
    if x.empty:return None
    occ=x.combined_target.value_counts(normalize=True).sort_index()
    return {"slice":name,"observations":len(x),"trend_on_fraction":float(x.trend_on.mean()),"crisis_active_fraction":float((x.crisis_level>0).mean()),"crisis_full_fraction":float((x.crisis_level==4).mean()),
            "avg_trend_target":float(x.trend_target.mean()),"avg_crisis_target":float(x.crisis_target.mean()),"avg_combined_target":float(x.combined_target.mean()),
            "trend_transitions":int(x.trend_on.astype(int).diff().abs().fillna(0).sum()),"joint_on_crisis":float((x.trend_on&(x.crisis_level>0)).mean()),
            "joint_off_crisis":float(((~x.trend_on)&(x.crisis_level>0)).mean()),"joint_on_no_crisis":float((x.trend_on&(x.crisis_level==0)).mean()),
            "joint_off_no_crisis":float(((~x.trend_on)&(x.crisis_level==0)).mean()),"target_occupancy_json":json.dumps({f"{100*k:g}%":float(v) for k,v in occ.items()},sort_keys=True)}

def pareto_dominated(c,s):
    return bool((s.cagr>=c.cagr-EPS) and (s.max_drawdown>=c.max_drawdown-EPS) and ((s.cagr>c.cagr+EPS) or (s.max_drawdown>c.max_drawdown+EPS)))

def shock_table(events,sims):
    rows=[]
    if events.empty:return pd.DataFrame()
    idx=sims["R009_COMBINED_DAILY"].index
    for _,e in events.iterrows():
        for lvl in LEVELS:
            d=e.get(f"breach_{lvl}_date",pd.NaT)
            if pd.isna(d) or d not in idx: continue
            for h in HORIZONS:
                j=idx.get_loc(d)+h
                if j>=len(idx): continue
                end=idx[j]; vals={}
                for n in ("R009_COMBINED_DAILY","TREND10_DAILY","CRISIS10_DAILY","STATIC15_DAILY","STATIC20_DAILY","STATIC15_MONTHLY"):
                    eq=sims[n].equity; vals[n]=float(eq.loc[end]/eq.loc[d]-1)
                rows.append({"event_id":int(e.event_id),"trigger_level":lvl,"breach_date":d.date().isoformat(),"horizon_days":h,"end_date":end.date().isoformat(),**vals,
                             "benefit_vs_trend10":vals["R009_COMBINED_DAILY"]-vals["TREND10_DAILY"],"benefit_vs_static15_daily":vals["R009_COMBINED_DAILY"]-vals["STATIC15_DAILY"],
                             "benefit_vs_static20_daily":vals["R009_COMBINED_DAILY"]-vals["STATIC20_DAILY"]})
    return pd.DataFrame(rows)

def run(work:Path):
    work.mkdir(parents=True,exist_ok=True); out=work/"results"; out.mkdir(parents=True,exist_ok=True); snap=snapshot(work); cutoff=int(snap["cutoff_ms"])
    z,hashes,raw_rows,dup=fetch_price(work,cutoff); au=audit(z,hashes,raw_rows,dup,cutoff); atomic_json(out/"r009_x001_eth_source_audit.json",au)
    if au["status"]!="PASS":
        state={"status":"DATA_REDESIGN","protocol":PROTOCOL,"engine_version":VERSION,"source_audit":au}; atomic_json(out/"r009_x001_eth_run_state.json",state); print(json.dumps(state,indent=2)); return
    z.to_csv(out/"r009_x001_eth_price_clean.csv",index=False); price=z.set_index("date").price; st,events=build_state(price); st.to_csv(out/"r009_x001_eth_state_daily.csv",index_label="date")
    ff=au["first_full_calendar_year"]; primary=pd.Timestamp(f"{ff}-01-01"); pre_end=pd.Timestamp("2019-12-31"); replay=pd.Timestamp("2020-01-01"); post=pd.Timestamp("2023-01-01")
    slices=[("FULL_AVAILABLE",price.index[0],None),("PRIMARY_FULL_YEARS",primary,None),("PRE_2020",primary,pre_end),("REPLAY_2020",replay,None),("POST_2023",post,None)]
    all_metrics=[]; baseline_sims={}
    targets={"TREND10_DAILY":st.trend_target,"CRISIS10_DAILY":st.crisis_target,"R009_COMBINED_DAILY":st.combined_target,
             "PERMANENT10_PLUS_CRISIS10_REF":st.permanent10_plus_crisis_target,"STATIC10_DAILY":pd.Series(0.10,index=price.index),
             "STATIC15_DAILY":pd.Series(0.15,index=price.index),"STATIC20_DAILY":pd.Series(0.20,index=price.index),"CASH":pd.Series(0.0,index=price.index),"ETH100":pd.Series(1.0,index=price.index)}
    for fee in FEES:
        sims={n:sim_daily(price,t,fee) for n,t in targets.items()}; sims["STATIC10_MONTHLY"]=sim_monthly(price,0.10,fee); sims["STATIC15_MONTHLY"]=sim_monthly(price,0.15,fee); sims["STATIC20_MONTHLY"]=sim_monthly(price,0.20,fee)
        if abs(fee-BASE_FEE)<EPS: baseline_sims=sims
        for sn,ss in sims.items():
            for sl,a,b in slices:
                m=metric(sn,fee,ss,sl,a,b)
                if m: all_metrics.append(m)
    met=pd.DataFrame(all_metrics); met.to_csv(out/"r009_x001_eth_metrics.csv",index=False)
    di=pd.DataFrame([x for x in (state_diag(st,*s) for s in slices) if x]); di.to_csv(out/"r009_x001_eth_state_diagnostics.csv",index=False)
    events.to_csv(out/"r009_x001_eth_crisis_events.csv",index=False); shock_table(events,baseline_sims).to_csv(out/"r009_x001_eth_shock_diagnostics.csv",index=False)
    base=met[met.fee_bps==10].set_index(["strategy","slice"]); stress=met[met.fee_bps==50].set_index(["strategy","slice"])
    C=base.loc[("R009_COMBINED_DAILY","PRIMARY_FULL_YEARS")]; T=base.loc[("TREND10_DAILY","PRIMARY_FULL_YEARS")]; S10=base.loc[("STATIC10_DAILY","PRIMARY_FULL_YEARS")]
    S15=base.loc[("STATIC15_DAILY","PRIMARY_FULL_YEARS")]; S15M=base.loc[("STATIC15_MONTHLY","PRIMARY_FULL_YEARS")]; S20=base.loc[("STATIC20_DAILY","PRIMARY_FULL_YEARS")]
    S20M=base.loc[("STATIC20_MONTHLY","PRIMARY_FULL_YEARS")]; REF=base.loc[("PERMANENT10_PLUS_CRISIS10_REF","PRIMARY_FULL_YEARS")]; CR=base.loc[("CRISIS10_DAILY","PRIMARY_FULL_YEARS")]
    R=base.loc[("R009_COMBINED_DAILY","REPLAY_2020")]; RT=base.loc[("TREND10_DAILY","REPLAY_2020")]; RS=base.loc[("STATIC10_DAILY","REPLAY_2020")]
    didx=di.set_index("slice"); pre_eligible=(("R009_COMBINED_DAILY","PRE_2020") in base.index and int(base.loc[("R009_COMBINED_DAILY","PRE_2020")].observations)>=365)
    checks={"primary_combined_gt_static10":bool(C.cagr>S10.cagr),"primary_combined_gt_trend10":bool(C.cagr>T.cagr),
            "replay2020_combined_gt_static10":bool(R.cagr>RS.cagr),"replay2020_combined_gt_trend10":bool(R.cagr>RT.cagr),
            "primary_not_pareto_dominated_static15_daily":not pareto_dominated(C,S15),"primary_not_pareto_dominated_static15_monthly":not pareto_dominated(C,S15M),
            "primary_dd_better_than_static20_daily":bool(C.max_drawdown>S20.max_drawdown),"primary_dd_better_than_static20_monthly":bool(C.max_drawdown>S20M.max_drawdown),
            "primary_dd_better_than_permanent10_crisis_ref":bool(C.max_drawdown>REF.max_drawdown),"primary_avg_target_lt_15pct":bool(didx.loc["PRIMARY_FULL_YEARS","avg_combined_target"]<0.15),
            "primary_crisis10_ending_gt_1":bool(CR.ending_multiple>1),
            "fee50_primary_combined_gt_static10":bool(stress.loc[("R009_COMBINED_DAILY","PRIMARY_FULL_YEARS")].cagr>stress.loc[("STATIC10_DAILY","PRIMARY_FULL_YEARS")].cagr),
            "fee50_primary_combined_gt_trend10":bool(stress.loc[("R009_COMBINED_DAILY","PRIMARY_FULL_YEARS")].cagr>stress.loc[("TREND10_DAILY","PRIMARY_FULL_YEARS")].cagr),
            "fee50_primary_not_pareto_dominated_static15_daily":not pareto_dominated(stress.loc[("R009_COMBINED_DAILY","PRIMARY_FULL_YEARS")],stress.loc[("STATIC15_DAILY","PRIMARY_FULL_YEARS")])}
    if pre_eligible:
        PC=base.loc[("R009_COMBINED_DAILY","PRE_2020")]; PT=base.loc[("TREND10_DAILY","PRE_2020")]; PS=base.loc[("STATIC10_DAILY","PRE_2020")]
        checks["pre2020_combined_gt_static10"]=bool(PC.cagr>PS.cagr); checks["pre2020_combined_gt_trend10"]=bool(PC.cagr>PT.cagr)
    hard={"primary_combined_cagr_positive":bool(C.cagr>0),"primary_combined_gt_static10":bool(C.cagr>S10.cagr),"primary_combined_gt_trend10":bool(C.cagr>T.cagr),
          "crisis10_ending_gt1":bool(CR.ending_multiple>1),"avg_target_lt15":bool(didx.loc["PRIMARY_FULL_YEARS","avg_combined_target"]<0.15),
          "dd_better_than_static20_daily":bool(C.max_drawdown>S20.max_drawdown),"fee50_combined_cagr_positive":bool(stress.loc[("R009_COMBINED_DAILY","PRIMARY_FULL_YEARS")].cagr>0)}
    decision="UNCHANGED_RULE_SUPPORT" if all(checks.values()) else ("UNCHANGED_RULE_FAIL" if not all(hard.values()) else "UNCHANGED_RULE_MIXED")
    outputs=["r009_x001_eth_run_state.json","r009_x001_eth_source_audit.json","r009_x001_eth_price_clean.csv","r009_x001_eth_state_daily.csv","r009_x001_eth_metrics.csv","r009_x001_eth_state_diagnostics.csv","r009_x001_eth_crisis_events.csv","r009_x001_eth_shock_diagnostics.csv","r009_x001_eth_summary.md"]
    state={"status":"PASS","engine_version":VERSION,"protocol":PROTOCOL,"evidence_status":"CROSS_ASSET_STRUCTURAL_FALSIFICATION_ONLY","asset":"ETH","symbol":SYMBOL,"source_audit":au,
           "decision":decision,"checks":checks,"hard_checks":hard,"primary":{"cagr":float(C.cagr),"max_drawdown":float(C.max_drawdown),"calmar":float(C.calmar),"avg_target":float(didx.loc["PRIMARY_FULL_YEARS","avg_combined_target"])},"outputs":outputs}
    atomic_json(out/"r009_x001_eth_run_state.json",state)
    def pct(x): return f"{float(x):.2%}"
    md="# R009-X001 ETH Unchanged-Rule Structural Falsification — Raw Output v0.1\n\n"+f"- Data gate: **{au['status']}**\n- Period: **{au['clean_start']} -> {au['clean_end']}**\n- First full year: **{ff}**\n- Decision: **{decision}**\n\n"
    md+="| Strategy | PRIMARY CAGR | Max DD | Calmar | Ending |\n|---|---:|---:|---:|---:|\n"
    for n in ("R009_COMBINED_DAILY","TREND10_DAILY","CRISIS10_DAILY","PERMANENT10_PLUS_CRISIS10_REF","STATIC10_DAILY","STATIC15_DAILY","STATIC20_DAILY","STATIC15_MONTHLY"):
        q=base.loc[(n,"PRIMARY_FULL_YEARS")]; md+=f"| {n} | {pct(q.cagr)} | {pct(q.max_drawdown)} | {float(q.calmar):.2f} | {float(q.ending_multiple):.3f}x |\n"
    md+="\nThis is historical cross-asset structural falsification only. It does not reset the BTC forward clock and cannot authorize demo/live trading.\n"
    (out/"r009_x001_eth_summary.md").write_text(md,encoding="utf-8"); print(md)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--workspace",type=Path,required=True); a=ap.parse_args()
    try: run(a.workspace)
    except Exception as e:
        out=a.workspace/"results"; out.mkdir(parents=True,exist_ok=True); atomic_json(out/"r009_x001_eth_run_state.json",{"status":"SOURCE_OR_ENGINE_ERROR","engine_version":VERSION,"protocol":PROTOCOL,"error_type":type(e).__name__,"error":str(e)}); raise
if __name__=="__main__": main()
