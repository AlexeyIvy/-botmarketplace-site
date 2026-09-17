from __future__ import annotations

import argparse, csv, io, json, math, os, statistics, subprocess, zipfile
from array import array
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

STAGE='SC001-E009-GROSS-FEASIBILITY'
PREFLIGHT_PASS='E009_GROSS_FEASIBILITY_IMPLEMENTATION_PREFLIGHT_PASS'
PASS='E009_GROSS_FEASIBILITY_PASS'
FAIL='E009_GROSS_FEASIBILITY_FAIL'
UTC=timezone.utc; DAY_MS=86_400_000
ASSETS=('BTC','ETH','DOGE','ORDI','UNI','XRP','OP','BCH')
ARCHIVE_DATES=tuple(['2024-08-31']+[f'2024-09-{d:02d}' for d in range(1,16)])
PERF_START='2024-09-01'; PERF_END='2024-09-14'
GRID_MS=5000; ANCHOR_OFFSET=12; Z_THRESHOLD=3.0; RETRACE=0.5
VOL_WINDOW_RETURNS=360; VOL_END_OFFSET_BUCKETS=12; MIN_VALID_RETURNS=240
MAD_SCALE=1.4826; SQRT12=math.sqrt(12.0)
PRIMARY_LAT=500; STRESS_LATS=(1000,2000); TOLERANCE_MS=5000
MAX_HOLD_MS=600_000; COOLDOWN_MS=600_000; DAILY_CAP=4; LATEST_ENTRY_MS=(23*3600+49*60)*1000
HEADER=['instrument_name','trade_id','side','price','size','created_time']
CHUNK=5000

ROOT=Path(__file__).resolve().parents[2]
DATA_ROOT=Path(os.environ.get('SC001_DATA_ROOT',str(Path.home()/'sc001_data'))).expanduser().resolve()
ARCH=DATA_ROOT/'SC001_E009_TRADE_ACQUISITION'/'archives'
SEM=DATA_ROOT/'SC001_E009_TRADE_SEMANTIC_INTEGRITY'/'sc001_e009_trade_semantic_integrity_report.json'
VERIFY=DATA_ROOT/'SC001_E009_TRADE_ACQUISITION'/'sc001_e009_trade_acquisition_verify_report.json'
OUT_DIR=DATA_ROOT/'SC001_E009_GROSS_FEASIBILITY'
PREFLIGHT=OUT_DIR/'sc001_e009_gross_feasibility_preflight.json'
REPORT=OUT_DIR/'sc001_e009_gross_feasibility_report.json'
PROTOCOL=ROOT/'docs/research/sc001-e009-gross-feasibility-executable-protocol-v0.1.md'
FREEZE=ROOT/'docs/research/sc001-e009-gross-feasibility-implementation-freeze-v1.0.json'

def fail(s): raise RuntimeError(s)
def load(p):
    if not p.exists(): fail(f'missing {p}')
    x=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(x,dict): fail(f'object expected {p}')
    return x

def atomic(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+'.tmp')
    with q.open('w',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(q,p)
def git_blob(p): return subprocess.check_output(['git','-C',str(ROOT),'hash-object',str(p.relative_to(ROOT))],text=True).strip()
def date_ms(s): return int(datetime.strptime(s,'%Y-%m-%d').replace(tzinfo=UTC).timestamp()*1000)
def day_text(t): return datetime.fromtimestamp(t/1000,tz=UTC).strftime('%Y-%m-%d')

def expected_parameters():
    return {
      'grid_ms':GRID_MS,'anchor_offset_buckets':ANCHOR_OFFSET,'z_threshold':Z_THRESHOLD,
      'retracement_fraction':RETRACE,'vol_window_return_slots':VOL_WINDOW_RETURNS,
      'vol_window_end_offset_buckets':VOL_END_OFFSET_BUCKETS,'min_valid_returns':MIN_VALID_RETURNS,
      'mad_scale':MAD_SCALE,'sigma60_sqrt_periods':12,'invalid_grid_breaks_crossing_chain':True,
      'primary_latency_ms':PRIMARY_LAT,'stress_latencies_ms':list(STRESS_LATS),
      'tolerance_ms':TOLERANCE_MS,'max_hold_ms':MAX_HOLD_MS,'cooldown_ms':COOLDOWN_MS,
      'daily_cap':DAILY_CAP,'latest_entry_utc':'23:49:00'
    }

def preflight():
    sem=load(SEM); ver=load(VERIFY); fr=load(FREEZE)
    if sem.get('status')!='E009_TRADE_SEMANTIC_INTEGRITY_PASS': fail('semantic parent not exact PASS')
    if int(sem.get('source_files_qualified',0))!=128 or int(sem.get('reconstructed_utc_days_qualified',0))!=120: fail('semantic counts mismatch')
    if sem.get('asset_holdout_accessed') is not False or sem.get('october_confirmation_accessed') is not False or sem.get('august_repurposed') is not False: fail('semantic firewall mismatch')
    if ver.get('status')!='E009_TRADE_ACQUISITION_VERIFY_PASS' or int(ver.get('verified_files',0))!=128 or int(ver.get('verified_total_bytes',-1))!=419552195: fail('acquisition parent mismatch')
    if fr.get('status')!='FROZEN_BEFORE_FIRST_GROSS_OUTPUT': fail('implementation freeze status mismatch')
    if fr.get('runner_git_blob_sha')!=git_blob(Path(__file__).resolve()): fail('runner identity mismatch')
    if fr.get('protocol_git_blob_sha')!=git_blob(PROTOCOL): fail('protocol identity mismatch')
    if tuple(fr.get('assets') or [])!=ASSETS or fr.get('parameters')!=expected_parameters(): fail('frozen identity/parameters mismatch')
    if REPORT.exists():
        old=load(REPORT)
        if old.get('status') in {PASS,FAIL}: fail(f'one-shot guard: terminal report already exists: {old.get("status")}')
    rep={'stage':STAGE+'-PREFLIGHT','status':PREFLIGHT_PASS,'runner_git_blob_sha':git_blob(Path(__file__).resolve()),'protocol_git_blob_sha':git_blob(PROTOCOL),'semantic_parent_status':sem.get('status'),'semantic_sparse_days':int(sem.get('sparse_but_id_continuous_days',0)),'assets':list(ASSETS),'performance_dates':[PERF_START,PERF_END],'gross_calculated':False,'fees_or_net_pnl_calculated':False,'asset_holdout_accessed':False,'october_confirmation_accessed':False,'august_repurposed':False,'l2_accessed':False}
    atomic(PREFLIGHT,rep)
    print(PREFLIGHT_PASS); print('assets = 8'); print('gross calculated = False'); print('asset holdout accessed = False'); print('October Confirmation accessed = False'); print('August repurposed = False'); return 0

def open_rows(path,inst):
    with zipfile.ZipFile(path,'r') as z:
        members=[m for m in z.infolist() if not m.is_dir()]
        if len(members)!=1: fail(f'bad member count {path.name}')
        with z.open(members[0]) as raw:
            r=csv.reader(io.TextIOWrapper(raw,encoding='utf-8',newline=''))
            if next(r,None)!=HEADER: fail(f'header mismatch {path.name}')
            for row in r:
                if not row: continue
                if len(row)!=6 or row[0]!=inst: fail(f'bad row {path.name}')
                try: tid=int(row[1]); px=float(row[3]); sz=float(row[4]); ts=int(row[5])
                except Exception as e: raise RuntimeError(f'parse failure {path.name}') from e
                if tid<0 or ts<0 or not math.isfinite(px) or px<=0 or not math.isfinite(sz) or sz<=0: fail(f'invalid row {path.name}')
                yield ts,tid,px,sz

def load_stream(sym):
    inst=f'{sym}-USDT-SWAP'; lo=date_ms('2024-08-31'); hi=date_ms('2024-09-15')
    ts=array('q'); px=array('d'); sz=array('d'); prev_ts=prev_id=None
    for d in ARCHIVE_DATES:
        p=ARCH/sym/f'{inst}-trades-{d}.zip'
        if not p.exists(): fail(f'missing archive {p}')
        for t,tid,price,size in open_rows(p,inst):
            if lo<=t<hi:
                if prev_ts is not None and t<prev_ts: fail(f'stitched timestamp reversal {sym}')
                if prev_id is not None and tid<=prev_id: fail(f'stitched id duplicate/backward {sym}')
                prev_ts,prev_id=t,tid; ts.append(t); px.append(price); sz.append(size)
    if not ts: fail(f'empty stream {sym}')
    return {'start_ms':lo,'end_ms':hi,'timestamps':np.frombuffer(ts,dtype=np.int64),'prices':np.frombuffer(px,dtype=np.float64),'sizes':np.frombuffer(sz,dtype=np.float64)}

def build_vwap(stream):
    lo,hi=stream['start_ms'],stream['end_ms']; n=(hi-lo)//GRID_MS
    k=((stream['timestamps']-lo)//GRID_MS).astype(np.int64); mask=(k>=0)&(k<n); k=k[mask]
    pv=np.bincount(k,weights=stream['prices'][mask]*stream['sizes'][mask],minlength=n).astype(float)
    sv=np.bincount(k,weights=stream['sizes'][mask],minlength=n).astype(float)
    cnt=np.bincount(k,minlength=n)
    vw=np.full(n,np.nan,dtype=float); ok=(cnt>0)&(sv>0); vw[ok]=pv[ok]/sv[ok]
    return vw

def build_normalized(vw,start):
    n=len(vw); r5=np.full(n,np.nan); adj=np.isfinite(vw[1:])&np.isfinite(vw[:-1]); r5[1:][adj]=np.log(vw[1:][adj]/vw[:-1][adj])
    sigma=np.full(n,np.nan)
    if n>371:
        wins=sliding_window_view(r5,VOL_WINDOW_RETURNS)
        k0=371; k1=n
        for ks in range(k0,k1,CHUNK):
            ke=min(k1,ks+CHUNK); w0=ks-371; w1=ke-371; block=wins[w0:w1]
            counts=np.count_nonzero(np.isfinite(block),axis=1); good=counts>=MIN_VALID_RETURNS
            if not np.any(good): continue
            sub=block[good]; med=np.nanmedian(sub,axis=1); mad=np.nanmedian(np.abs(sub-med[:,None]),axis=1); vals=MAD_SCALE*mad*SQRT12
            idx=np.arange(ks,ke)[good]; finite=np.isfinite(vals)&(vals>0); sigma[idx[finite]]=vals[finite]
    valid=np.zeros(n,dtype=bool); z=np.full(n,np.nan); anchor=np.full(n,np.nan); r60=np.full(n,np.nan)
    idx=np.arange(ANCHOR_OFFSET,n); a=vw[idx-ANCHOR_OFFSET]; c=vw[idx]; ok=np.isfinite(a)&np.isfinite(c)&np.isfinite(sigma[idx])&(sigma[idx]>0)
    ii=idx[ok]; anchor[ii]=a[ok]; rr=np.log(c[ok]/a[ok]); r60[ii]=rr; z[ii]=rr/sigma[ii]; valid[ii]=np.isfinite(z[ii])
    return {'vw':vw,'sigma':sigma,'z':z,'anchor':anchor,'r60':r60,'valid':valid,'start_ms':start,'valid_count':int(np.count_nonzero(valid))}

def candidates(norm):
    lo=date_ms(PERF_START); hi=date_ms(PERF_END)+DAY_MS; out=[]; prev_valid=False; prev_z=None
    vw,z,anc,sig,valid=norm['vw'],norm['z'],norm['anchor'],norm['sigma'],norm['valid']; start=norm['start_ms']
    for k in range(len(vw)):
        t=start+(k+1)*GRID_MS
        if not valid[k]: prev_valid=False; prev_z=None; continue
        curz=float(z[k])
        if prev_valid and lo<=t<hi and abs(float(prev_z))<Z_THRESHOLD and abs(curz)>=Z_THRESHOLD:
            a=float(anc[k]); c=float(vw[k]); out.append({'date':day_text(t),'trigger_ts':t,'direction':-1 if curz>0 else 1,'trigger_z':curz,'trigger_abs_z':abs(curz),'sigma60':float(sig[k]),'r60':float(norm['r60'][k]),'anchor_price':a,'trigger_vwap':c,'target_price':a+RETRACE*(c-a)})
        prev_valid=True; prev_z=curz
    return out

def proxy(stream,target,day_end):
    ts=stream['timestamps']; i=int(np.searchsorted(ts,target,side='left'))
    if i>=len(ts): return None
    actual=int(ts[i])
    if actual>target+TOLERANCE_MS or actual>=day_end: return None
    return actual,float(stream['prices'][i])
def reverted(direction,price,target): return price>=target if direction==1 else price<=target
def ceiling(t,origin):
    x=t-origin; return origin+((x+GRID_MS-1)//GRID_MS)*GRID_MS if x>0 else origin

def exit_decision(c,norm,entry):
    start=norm['start_ms']; vw=norm['vw']; first=max(0,(entry-start)//GRID_MS); max_t=ceiling(entry+MAX_HOLD_MS,start); max_i=min(len(vw)-1,(max_t-start)//GRID_MS-1)
    for i in range(int(first),max_i+1):
        t=start+(i+1)*GRID_MS
        if t<=entry or not np.isfinite(vw[i]): continue
        cur=float(vw[i]); hit=cur>=c['target_price'] if c['direction']==1 else cur<=c['target_price']
        if hit:return t,'reversion'
    return max_t,'time'

def simulate(stream,norm,cands,lat):
    ev=[]; daily=Counter(); counts=Counter(); available=0; locked=None; current=None
    for c in cands:
        t=int(c['trigger_ts']); d=c['date']; ds=date_ms(d); de=ds+DAY_MS
        if current!=d:
            current=d; available=max(available,ds)
            if locked!=d: locked=None
        if locked==d: counts['skipped_day_locked']+=1; continue
        if t<available: counts['skipped_busy_or_cooldown']+=1; continue
        if daily[d]>=DAILY_CAP: counts['skipped_daily_cap']+=1; continue
        if t-ds>LATEST_ENTRY_MS: counts['skipped_late']+=1; continue
        daily[d]+=1; counts['decisions']+=1
        e=dict(c); e.update({'completed':False,'entry_ts':None,'exit_decision_ts':None,'exit_ts':None,'entry_price':None,'exit_price':None,'gross_edge_bps':None,'incomplete_reason':None,'exit_reason':None})
        leg=proxy(stream,t+lat,de)
        if leg is None: e['incomplete_reason']='entry_missing'; counts['entry_missing']+=1; available=t+lat+TOLERANCE_MS+COOLDOWN_MS; ev.append(e); continue
        ets,ep=leg
        if reverted(c['direction'],ep,c['target_price']): e['entry_ts']=ets; e['entry_price']=ep; e['incomplete_reason']='entry_already_reverted'; counts['entry_already_reverted']+=1; available=ets+COOLDOWN_MS; ev.append(e); continue
        e['entry_ts']=ets; e['entry_price']=ep; xd,reason=exit_decision(c,norm,ets); e['exit_decision_ts']=xd; e['exit_reason']=reason
        if xd>=de: e['incomplete_reason']='exit_day_cross'; counts['exit_day_cross']+=1; locked=d; available=de; ev.append(e); continue
        x=proxy(stream,xd+lat,de)
        if x is None: e['incomplete_reason']='exit_missing'; counts['exit_missing']+=1; locked=d; available=de; ev.append(e); continue
        xt,xp=x; e['exit_ts']=xt; e['exit_price']=xp; e['completed']=True; e['gross_edge_bps']=c['direction']*10000.0*(xp/ep-1.0); counts['completed']+=1; available=xt+COOLDOWN_MS; ev.append(e)
    return ev,{'counts':dict(counts),'daily_decisions':dict(daily)}

def replay(primary,stream,lat):
    out=[]
    for p in primary:
        r={'date':p['date'],'trigger_ts':p['trigger_ts'],'direction':p['direction'],'target_price':p['target_price'],'completed':False,'gross_edge_bps':None,'incomplete_reason':None}
        xd=p.get('exit_decision_ts')
        if xd is None:r['incomplete_reason']=p.get('incomplete_reason') or 'primary_no_exit_decision'; out.append(r); continue
        de=date_ms(p['date'])+DAY_MS; leg=proxy(stream,p['trigger_ts']+lat,de)
        if leg is None:r['incomplete_reason']='entry_missing'; out.append(r); continue
        ets,ep=leg
        if reverted(p['direction'],ep,p['target_price']):r['incomplete_reason']='entry_already_reverted'; out.append(r); continue
        if ets>=int(xd): r['incomplete_reason']='entry_after_exit_decision'; out.append(r); continue
        x=proxy(stream,int(xd)+lat,de)
        if x is None:r['incomplete_reason']='exit_missing'; out.append(r); continue
        _xt,xp=x; r['completed']=True; r['gross_edge_bps']=p['direction']*10000.0*(xp/ep-1.0); out.append(r)
    return out

def trimmed(vals):
    if not vals:return None
    x=sorted(vals); k=math.floor(.1*len(x)); core=x[k:len(x)-k] if k else x
    return statistics.fmean(core) if core else None

def metrics(events):
    comp=[e for e in events if e.get('completed') and e.get('gross_edge_bps') is not None]; vals=[float(e['gross_edge_bps']) for e in comp]; byday={}; side={1:[],-1:[]}
    for e in comp:
        v=float(e['gross_edge_bps']); byday.setdefault(e['date'],[]).append(v); side[e['direction']].append(v)
    dm={d:statistics.fmean(v) for d,v in byday.items()}
    return {'decisions':len(events),'completed':len(comp),'active_days':len(byday),'completion_rate':len(comp)/len(events) if events else 0.0,'mean_bps':statistics.fmean(vals) if vals else None,'median_bps':statistics.median(vals) if vals else None,'trimmed_mean_bps':trimmed(vals),'positive_event_share':sum(v>0 for v in vals)/len(vals) if vals else 0.0,'positive_active_day_share':sum(v>0 for v in dm.values())/len(dm) if dm else 0.0,'long_count':len(side[1]),'short_count':len(side[-1]),'long_mean_bps':statistics.fmean(side[1]) if side[1] else None,'short_mean_bps':statistics.fmean(side[-1]) if side[-1] else None,'sum_gross_bps':sum(vals),'day_means':dm}

def qstats(vals):
    if not vals:return {'min':None,'median':None,'p90':None,'max':None}
    x=sorted(float(v) for v in vals); return {'min':x[0],'median':statistics.median(x),'p90':x[min(len(x)-1,math.ceil(.9*len(x))-1)],'max':x[-1]}

def run():
    preflight(); per={}; all_primary=[]; stress={1000:{},2000:{}}
    for i,sym in enumerate(ASSETS,1):
        print(f'E009 [{i}/8] {sym}: load stream',flush=True); st=load_stream(sym); vw=build_vwap(st); norm=build_normalized(vw,st['start_ms']); cs=candidates(norm)
        print(f'E009 {sym}: normalized_valid={norm["valid_count"]} candidates={len(cs)}',flush=True); prim,state=simulate(st,norm,cs,PRIMARY_LAT); pm=metrics(prim); sm={}
        for lat in STRESS_LATS: se=replay(prim,st,lat); stress[lat][sym]=metrics(se); sm[str(lat)]=stress[lat][sym]
        perf_points=((date_ms(PERF_END)+DAY_MS)-date_ms(PERF_START))//GRID_MS
        per[sym]={'primary':pm,'stress':sm,'state':state,'candidate_count':len(cs),'normalized_valid_count':norm['valid_count'],'normalized_valid_coverage':norm['valid_count']/len(vw),'performance_grid_points':perf_points,'trigger_abs_z_stats':qstats([c['trigger_abs_z'] for c in cs]),'trigger_sigma60_stats':qstats([c['sigma60'] for c in cs])}; all_primary.extend([dict(e,instrument=sym) for e in prim])
        print(f'E009 {sym}: decisions={pm["decisions"]} completed={pm["completed"]} mean={pm["mean_bps"]}',flush=True)
    inst_means={s:(per[s]['primary']['mean_bps'] if per[s]['primary']['mean_bps'] is not None else 0.0) for s in ASSETS}; eq=statistics.fmean(inst_means.values()); med=statistics.median(inst_means.values()); pos=sum(v>0 for v in inst_means.values()); active=sum(per[s]['primary']['completed']>0 for s in ASSETS); active5=sum(per[s]['primary']['completed']>=5 for s in ASSETS)
    completed=[e for e in all_primary if e.get('completed') and e.get('gross_edge_bps') is not None]; pooled=[float(e['gross_edge_bps']) for e in completed]; stress_eq={str(lat):statistics.fmean([(stress[lat][s]['mean_bps'] if stress[lat][s]['mean_bps'] is not None else 0.0) for s in ASSETS]) for lat in STRESS_LATS}
    contrib={s:abs(float(per[s]['primary']['sum_gross_bps'])) for s in ASSETS}; denom=sum(contrib.values()); top_share=max(contrib.values())/denom if denom>0 else 1.0
    gates={'all_8_attempted':len(per)==8,'active_assets_gte_6':active>=6,'assets_completed_gte5_count_gte4':active5>=4,'pooled_completed_gte40':len(completed)>=40,'equal_weight_mean_gte20':eq>=20.0,'median_instrument_mean_gte15':med>=15.0,'positive_instruments_gte5':pos>=5,'pooled_trimmed_mean_gte15':trimmed(pooled) is not None and trimmed(pooled)>=15.0,'pooled_median_gte10':bool(pooled) and statistics.median(pooled)>=10.0,'lat1000_equal_weight_gte15':stress_eq['1000']>=15.0,'lat2000_equal_weight_gte10':stress_eq['2000']>=10.0,'top_instrument_abs_contribution_lte035':top_share<=0.35}
    status=PASS if all(gates.values()) else FAIL
    rep={'stage':STAGE,'status':status,'protocol':'sc001-e009-gross-feasibility-executable-protocol-v0.1.md','assets':list(ASSETS),'performance_dates':[PERF_START,PERF_END],'per_instrument':per,'aggregate':{'active_assets':active,'assets_with_gte5_completed':active5,'pooled_completed':len(completed),'equal_weight_instrument_mean_bps':eq,'median_instrument_mean_bps':med,'positive_instrument_count':pos,'pooled_mean_bps':statistics.fmean(pooled) if pooled else None,'pooled_median_bps':statistics.median(pooled) if pooled else None,'pooled_trimmed_mean_bps':trimmed(pooled),'stress_equal_weight_mean_bps':stress_eq,'top_instrument_abs_contribution_share':top_share,'instrument_mean_bps':inst_means},'gates':gates,'failed_gates':[k for k,v in gates.items() if not v],'gross_bps_calculated':True,'discrete_contract_pnl_calculated':False,'fees_or_net_pnl_calculated':False,'l2_accessed':False,'asset_holdout_accessed':False,'october_confirmation_accessed':False,'august_repurposed':False,'historical_exact_execution_specs_verified':False,'volatility_window_semantics':{'return_slots':360,'end_offset_buckets':12,'min_valid_returns':240,'current_60s_excluded':True,'invalid_grid_breaks_crossing_chain':True},'stress_entry_after_exit_guard':True}
    atomic(REPORT,rep)
    print(status); print('active_assets =',active,'/ 8'); print('pooled_completed =',len(completed)); print('equal_weight_mean_bps =',eq); print('median_instrument_mean_bps =',med); print('positive_instruments =',pos,'/ 8'); print('pooled_trimmed_mean_bps =',rep['aggregate']['pooled_trimmed_mean_bps']); print('pooled_median_bps =',rep['aggregate']['pooled_median_bps']); print('lat1000_equal_weight_mean_bps =',stress_eq['1000']); print('lat2000_equal_weight_mean_bps =',stress_eq['2000']); print('top_instrument_abs_contribution_share =',top_share); print('failed_gates =',rep['failed_gates']); print('discrete contract PnL calculated = False'); print('asset holdout accessed = False'); print('October Confirmation accessed = False'); print('August repurposed = False'); print('report =',REPORT)
    return 0 if status==PASS else 2

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['preflight','run']); a=ap.parse_args(); return preflight() if a.mode=='preflight' else run()
if __name__=='__main__': raise SystemExit(main())
