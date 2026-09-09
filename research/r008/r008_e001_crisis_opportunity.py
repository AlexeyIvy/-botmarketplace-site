"""R008-E001 crisis-opportunity barbell sanity-screen engine v0.1."""

from __future__ import annotations
import argparse, hashlib, json, math
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

VERSION="0.1"
BASE=0.10
TRANCHE=0.025
THRESH=(-0.20,-0.35,-0.50,-0.65)
FEES=(0.0005,0.0010,0.0025,0.0050)
BASE_FEE=0.0010
LATE=pd.Timestamp("2023-01-01")
DAYS_PER_YEAR=365.25
EPS=1e-12

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def load_btc(path):
    hdr=pd.read_csv(path,nrows=0)
    req={"symbol","date_utc","close"}
    if not req.issubset(hdr.columns): raise ValueError(f"Missing columns: {sorted(req-set(hdr.columns))}")
    x=pd.read_csv(path,usecols=["symbol","date_utc","close"])
    x=x[x["symbol"].astype(str)=="BTCUSDT"].copy()
    if x.empty: raise ValueError("BTCUSDT not found")
    x["date"]=pd.to_datetime(x["date_utc"],errors="coerce")
    x["close"]=pd.to_numeric(x["close"],errors="coerce")
    x=x.dropna(subset=["date","close"])
    x=x[x["close"]>0].sort_values("date").drop_duplicates("date",keep="last")
    if len(x)<200: raise ValueError("BTC history too short")
    return x.set_index("date")[["close"]]

def next_date(idx,date):
    p=idx.searchsorted(date,side="right")
    return None if p>=len(idx) else idx[p]

def build_state(close):
    idx=close.index
    peak=float(close.iloc[0]); peak_date=idx[0]
    triggered=[False]*4; active=None; event_no=1
    states=[]; done=[]
    for i,(date,raw) in enumerate(close.items()):
        c=float(raw); new_ath=(i==0 or c>peak+EPS)
        if new_ath:
            if i>0 and active is not None:
                active["reset_date"]=date; active["status"]="CLOSED"; done.append(active); active=None
            peak=c; peak_date=date; triggered=[False]*4; dd=0.0
        else:
            dd=c/peak-1.0; crossed=[]
            for j,t in enumerate(THRESH):
                if (not triggered[j]) and dd<=t+EPS:
                    triggered[j]=True; crossed.append(j)
            if crossed:
                if active is None:
                    active={"event_id":event_no,"prior_peak_date":peak_date,"prior_peak_close":peak,
                            "first_breach_date":date,"reset_date":pd.NaT,"status":"OPEN",
                            "max_drawdown":dd,"max_drawdown_date":date,
                            "breach_20_date":pd.NaT,"breach_35_date":pd.NaT,
                            "breach_50_date":pd.NaT,"breach_65_date":pd.NaT}
                    event_no+=1
                for j in crossed:
                    key=f"breach_{(20,35,50,65)[j]}_date"
                    if pd.isna(active[key]): active[key]=date
            if active is not None and dd<float(active["max_drawdown"]):
                active["max_drawdown"]=dd; active["max_drawdown_date"]=date
        level=sum(triggered); target=BASE+TRANCHE*level
        states.append({"date":date,"close":c,"running_peak_close":peak,"running_peak_date":peak_date,
                       "drawdown":dd,"active_tranches":level,"target_btc_weight":target,
                       "event_id":active["event_id"] if active else np.nan,"new_ath":bool(new_ath)})
    if active is not None:
        active["status"]="OPEN_CENSORED"; done.append(active)
    state=pd.DataFrame(states).set_index("date")
    events=pd.DataFrame(done)
    return state,events

def simulate(close,target,fee):
    target=target.reindex(close.index).astype(float)
    r=close.pct_change(fill_method=None).fillna(0.0)
    held=target.shift(1).fillna(0.0)
    dturn=target.diff().abs(); dturn.iloc[0]=abs(float(target.iloc[0]))
    turn=dturn.shift(1).fillna(0.0)
    gross=held*r; cost=fee*turn; net=gross-cost
    eq=(1+net).cumprod()
    return pd.DataFrame({"btc_return":r,"target_weight":target,"held_weight":held,"turnover":turn,
                         "gross_return":gross,"fee_cost":cost,"net_return":net,"equity":eq},index=close.index)

def longest_dd(eq):
    peak=eq.cummax(); under=eq<peak-1e-15; start=None; best=0
    for d,f in under.items():
        if f and start is None: start=d
        elif (not f) and start is not None: best=max(best,(d-start).days); start=None
    if start is not None: best=max(best,(eq.index[-1]-start).days)
    return int(best)

def period_return(r,freq):
    return (1+r).groupby(r.index.to_period(freq)).prod()-1

def metrics(name,fee,sim,slice_name,start):
    x=sim[sim.index>=start]; r=x["net_return"]; eq=(1+r).cumprod()
    years=(eq.index[-1]-eq.index[0]).days/DAYS_PER_YEAR
    cagr=float(eq.iloc[-1]**(1/years)-1) if years>0 else np.nan
    dd=float((eq/eq.cummax()-1).min()); vol=float(r.std()*math.sqrt(365))
    yr=period_return(r,"Y"); qr=period_return(r,"Q"); mo=period_return(r,"M")
    roll=(eq/eq.shift(365)-1).dropna()
    return {"strategy":name,"fee_bps":fee*10000,"slice":slice_name,
            "start":eq.index[0].date().isoformat(),"end":eq.index[-1].date().isoformat(),"days":len(eq),
            "cagr":cagr,"ending_multiple":float(eq.iloc[-1]),"annualized_vol":vol,"max_drawdown":dd,
            "calmar":cagr/abs(dd) if dd<0 else np.nan,
            "worst_calendar_year":float(yr.min()) if len(yr) else np.nan,
            "worst_calendar_year_label":str(yr.idxmin()) if len(yr) else "",
            "worst_calendar_quarter":float(qr.min()) if len(qr) else np.nan,
            "worst_calendar_quarter_label":str(qr.idxmin()) if len(qr) else "",
            "worst_month":float(mo.min()) if len(mo) else np.nan,
            "worst_month_label":str(mo.idxmin()) if len(mo) else "",
            "worst_rolling_12m":float(roll.min()) if len(roll) else np.nan,
            "longest_drawdown_days":longest_dd(eq),
            "average_btc_exposure":float(x["held_weight"].mean()),"max_btc_exposure":float(x["held_weight"].max()),
            "turnover":float(x["turnover"].sum()),"fee_drag_simple":float(x["fee_cost"].sum())}

def event_diag(events,sims,state):
    if events.empty: return pd.DataFrame()
    idx=state.index; rows=[]
    for _,e in events.iterrows():
        breach=pd.Timestamp(e["first_breach_date"]); reset=pd.Timestamp(e["reset_date"]) if pd.notna(e["reset_date"]) else None
        start=next_date(idx,breach)
        if start is None: continue
        end=next_date(idx,reset) if reset is not None else idx[-1]
        if end is None: end=idx[-1]
        deepest=sum(pd.notna(e[f"breach_{p}_date"]) for p in (20,35,50,65))
        row={"event_id":int(e["event_id"]),"status":e["status"],
             "prior_peak_date":pd.Timestamp(e["prior_peak_date"]).date().isoformat(),
             "first_breach_date":breach.date().isoformat(),"start_execution_date":start.date().isoformat(),
             "reset_date":reset.date().isoformat() if reset is not None else "",
             "end_execution_date":end.date().isoformat(),"max_drawdown":float(e["max_drawdown"]),
             "max_drawdown_date":pd.Timestamp(e["max_drawdown_date"]).date().isoformat(),
             "deepest_level":int(deepest),"deployed_tranches":int(deepest)}
        for p in (20,35,50,65):
            v=e[f"breach_{p}_date"]; row[f"breach_{p}_date"]=pd.Timestamp(v).date().isoformat() if pd.notna(v) else ""
        for n in ("R008","STATIC10","STATIC20"):
            rr=sims[n].loc[start:end,"net_return"]; row[f"{n.lower()}_event_return"]=float((1+rr).prod()-1)
        row["benefit_vs_static10"]=row["r008_event_return"]-row["static10_event_return"]
        row["benefit_vs_static20"]=row["r008_event_return"]-row["static20_event_return"]
        rows.append(row)
    return pd.DataFrame(rows)

def self_test():
    idx=pd.date_range("2020-01-01",periods=12)
    c=pd.Series([100,110,105,88,80,70,50,35,55,90,111,100],index=idx,dtype=float)
    s,e=build_state(c)
    exp=[.10,.10,.10,.125,.125,.15,.175,.20,.20,.20,.10,.10]
    if s["target_btc_weight"].round(6).tolist()!=exp: raise AssertionError("state self-test failed")
    if len(e)!=1 or e.iloc[0]["status"]!="CLOSED": raise AssertionError("event self-test failed")

def write_summary(path,metrics_df,events,state,info):
    base=metrics_df[metrics_df["fee_bps"]==10.0]
    L=["# R008-E001 Crisis-Opportunity Barbell — Engine Output v0.1","",
       "**Status:** raw sanity-screen output; no automatic promotion.","",
       f"- BTC rows: **{info['btc_rows']}**",f"- Period: **{info['start']} -> {info['end']}**",
       "- Frozen architecture: **10% BTC base + four 2.5% crisis tranches at -20/-35/-50/-65%**",
       "- Reset: **new closing all-time high**","- Baseline cost: **10 bps**","",
       "## Baseline metrics","",
       "| Strategy | Slice | CAGR | Max DD | Calmar | Ending | Avg BTC | Turnover | Worst 12m |",
       "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in base.itertuples(index=False):
        L.append(f"| {r.strategy} | {r.slice} | {r.cagr:.2%} | {r.max_drawdown:.2%} | {r.calmar:.2f} | "
                 f"{r.ending_multiple:.3f}x | {r.average_btc_exposure:.2%} | {r.turnover:.3f} | {r.worst_rolling_12m:.2%} |")
    L+=["","## Dry-powder utilization",""]
    for w,share in state["target_btc_weight"].value_counts(normalize=True).sort_index().items():
        L.append(f"- Target BTC {w:.1%}: **{share:.1%}** of observed days")
    L+=["","## Crisis events",""]
    if events.empty: L.append("- No -20% drawdown episode detected.")
    else:
        L.append(f"- Mechanically detected crisis episodes: **{len(events)}**")
        for r in events.itertuples(index=False):
            L.append(f"- Event {r.event_id}: level {r.deepest_level}, max DD {r.max_drawdown:.2%}, "
                     f"R008 {r.r008_event_return:.2%}, benefit vs STATIC10 {r.benefit_vs_static10:.2%}, status {r.status}.")
    L+=["","## Important","",
        "This 2020-2026 run is only a sanity screen. Even a strong result does not qualify R008 for historical PASS; a promising result requires longer independent BTC history.",""]
    Path(path).write_text("\n".join(L),encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("csv"); ap.add_argument("--outdir")
    a=ap.parse_args()
    csv=Path(a.csv).expanduser().resolve()
    if not csv.exists(): raise FileNotFoundError(csv)
    out=Path(a.outdir).expanduser().resolve() if a.outdir else csv.parent/f"R008_E001_RUN_{datetime.now():%Y-%m-%d_%H-%M-%S}"
    out.mkdir(parents=True,exist_ok=True)

    print("="*72); print("R008-E001 CRISIS-OPPORTUNITY BARBELL v0.1"); print("="*72)
    print("[1/7] Self-test..."); self_test(); print("      PASS")
    print("[2/7] Loading BTCUSDT..."); btc=load_btc(csv); close=btc["close"]
    print("      ",len(btc),"rows",close.index[0].date(),"->",close.index[-1].date())
    print("[3/7] Building state..."); state,raw_events=build_state(close); print("      crisis episodes:",len(raw_events))

    targets={"R008":state["target_btc_weight"],
             "CASH":pd.Series(0.0,index=close.index),
             "STATIC10":pd.Series(0.10,index=close.index),
             "STATIC20":pd.Series(0.20,index=close.index),
             "BTC100":pd.Series(1.0,index=close.index)}
    print("[4/7] Cost grid...")
    rows=[]; sims_by_fee={}
    for fee in FEES:
        sims={n:simulate(close,t,fee) for n,t in targets.items()}; sims_by_fee[fee]=sims
        for n,s in sims.items():
            rows.append(metrics(n,fee,s,"FULL",close.index[0]))
            rows.append(metrics(n,fee,s,"POST_2023",max(LATE,close.index[0])))
    m=pd.DataFrame(rows)

    print("[5/7] Yearly + crisis diagnostics...")
    yf=[]
    for fee,sims in sims_by_fee.items():
        for n,s in sims.items():
            y=period_return(s["net_return"],"Y")
            yf.append(pd.DataFrame({"strategy":n,"fee_bps":fee*10000,"year":[int(p.year) for p in y.index],"return":y.values}))
    yearly=pd.concat(yf,ignore_index=True)
    base=sims_by_fee[BASE_FEE]
    ev=event_diag(raw_events,base,state)

    print("[6/7] Writing outputs...")
    daily=state.copy(); daily["btc_return"]=base["R008"]["btc_return"]
    for n in ("R008","STATIC10","STATIC20","BTC100","CASH"):
        s=base[n]; daily[f"{n.lower()}_held_weight"]=s["held_weight"]; daily[f"{n.lower()}_net_return"]=s["net_return"]; daily[f"{n.lower()}_equity"]=s["equity"]
    m.to_csv(out/"r008_e001_metrics.csv",index=False)
    yearly.to_csv(out/"r008_e001_yearly_returns.csv",index=False)
    state.to_csv(out/"r008_e001_state_daily.csv")
    raw_events.to_csv(out/"r008_e001_crisis_events_raw.csv",index=False)
    ev.to_csv(out/"r008_e001_crisis_event_diagnostics.csv",index=False)
    daily.to_csv(out/"r008_e001_baseline_daily.csv")

    info={"csv":str(csv),"csv_sha256":sha256_file(csv),"btc_rows":len(btc),
          "start":close.index[0].date().isoformat(),"end":close.index[-1].date().isoformat()}
    run={"status":"PASS","engine_version":VERSION,"protocol":"r008-antifragile-crisis-opportunity-barbell-protocol-v0.1",
         "research_freeze":{"base_weight":BASE,"opportunity_reserve":0.10,"tranche_weight":TRANCHE,
                            "thresholds":list(THRESH),"reset":"new_closing_all_time_high","fee_grid":list(FEES),
                            "late_start":LATE.date().isoformat(),"cash_return":0.0},
         "input":info,"crisis_events":len(raw_events),
         "outputs":["r008_e001_metrics.csv","r008_e001_yearly_returns.csv","r008_e001_state_daily.csv",
                    "r008_e001_crisis_events_raw.csv","r008_e001_crisis_event_diagnostics.csv",
                    "r008_e001_baseline_daily.csv","r008_e001_summary.md","r008_e001_run_state.json"]}
    (out/"r008_e001_run_state.json").write_text(json.dumps(run,indent=2,ensure_ascii=False),encoding="utf-8")
    write_summary(out/"r008_e001_summary.md",m,ev,state,info)
    print("[7/7] FINISHED"); print("Results:",out)

if __name__=="__main__": main()
