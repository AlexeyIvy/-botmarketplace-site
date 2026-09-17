from __future__ import annotations

import argparse, bisect, csv, hashlib, io, json, math, os, statistics, subprocess, zipfile
from array import array
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE='SC001-E007R1-GROSS-FEASIBILITY'
PREFLIGHT_PASS='E007R1_GROSS_FEASIBILITY_IMPLEMENTATION_PREFLIGHT_PASS'
PASS='E007R1_GROSS_FEASIBILITY_PASS'
FAIL='E007R1_GROSS_FEASIBILITY_FAIL'
UTC=timezone.utc; DAY_MS=86_400_000
ASSETS=('BTC','ETH','DOGE','ORDI','UNI','XRP','OP','BCH')
ARCHIVE_DATES=tuple(['2024-06-30']+[f'2024-07-{d:02d}' for d in range(1,16)])
PERF_START='2024-07-01'; PERF_END='2024-07-14'
GRID_MS=5000; ANCHOR_OFFSET=12; THRESHOLD_BPS=80.0; RETRACE=0.5
PRIMARY_LAT=500; STRESS_LATS=(1000,2000); TOLERANCE_MS=5000
MAX_HOLD_MS=600_000; COOLDOWN_MS=600_000; DAILY_CAP=4; LATEST_ENTRY_MS=(23*3600+49*60)*1000
HEADER=['instrument_name','trade_id','side','price','size','created_time']

ROOT=Path(__file__).resolve().parents[2]
DATA_ROOT=Path(os.environ.get('SC001_DATA_ROOT',str(Path.home()/'sc001_data'))).expanduser().resolve()
ARCH=DATA_ROOT/'SC001_E007R1_TRADE_ACQUISITION'/'archives'
SEM=DATA_ROOT/'SC001_E007R1_TRADE_SEMANTIC_INTEGRITY'/'sc001_e007r1_trade_semantic_integrity_report.json'
VERIFY=DATA_ROOT/'SC001_E007R1_TRADE_ACQUISITION'/'sc001_e007r1_trade_acquisition_verify_report.json'
OUT_DIR=DATA_ROOT/'SC001_E007R1_GROSS_FEASIBILITY'; PREFLIGHT=OUT_DIR/'sc001_e007r1_gross_feasibility_preflight.json'; REPORT=OUT_DIR/'sc001_e007r1_gross_feasibility_report.json'
PROTOCOL=ROOT/'docs/research/sc001-e007r1-multiasset-gross-feasibility-protocol-v0.1.md'
FREEZE=ROOT/'docs/research/sc001-e007r1-gross-feasibility-implementation-freeze-v1.0.json'


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
def next_day(s): return (datetime.strptime(s,'%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d')

def preflight():
    sem=load(SEM); ver=load(VERIFY); fr=load(FREEZE)
    if sem.get('status')!='E007R1_TRADE_SEMANTIC_INTEGRITY_PASS': fail('semantic parent not PASS')
    if int(sem.get('source_files_qualified',0))!=128 or int(sem.get('reconstructed_utc_days_qualified',0))!=120: fail('semantic counts mismatch')
    if ver.get('status')!='E007R1_TRADE_ACQUISITION_VERIFY_PASS' or int(ver.get('verified_files',0))!=128: fail('acquisition parent mismatch')
    if fr.get('status')!='FROZEN_BEFORE_FIRST_GROSS_OUTPUT': fail('implementation freeze status mismatch')
    if fr.get('runner_git_blob_sha')!=git_blob(Path(__file__).resolve()): fail('runner identity mismatch')
    if fr.get('protocol_git_blob_sha')!=git_blob(PROTOCOL): fail('protocol identity mismatch')
    if tuple(fr.get('assets') or [])!=ASSETS: fail('asset freeze mismatch')
    frozen=fr.get('parameters') or {}
    expected={'grid_ms':GRID_MS,'anchor_offset_buckets':ANCHOR_OFFSET,'threshold_bps':THRESHOLD_BPS,'retracement_fraction':RETRACE,'primary_latency_ms':PRIMARY_LAT,'stress_latencies_ms':list(STRESS_LATS),'tolerance_ms':TOLERANCE_MS,'max_hold_ms':MAX_HOLD_MS,'cooldown_ms':COOLDOWN_MS,'daily_cap':DAILY_CAP,'latest_entry_utc':'23:49:00'}
    if frozen!=expected: fail('parameter freeze mismatch')
    rep={'stage':STAGE+'-PREFLIGHT','status':PREFLIGHT_PASS,'runner_git_blob_sha':git_blob(Path(__file__).resolve()),'protocol_git_blob_sha':git_blob(PROTOCOL),'semantic_parent_status':sem.get('status'),'assets':list(ASSETS),'performance_dates':[PERF_START,PERF_END],'gross_calculated':False,'fees_or_net_pnl_calculated':False,'asset_holdout_accessed':False,'august_confirmation_accessed':False,'l2_accessed':False}
    atomic(PREFLIGHT,rep)
    print(PREFLIGHT_PASS); print('assets = 8'); print('gross calculated = False'); print('asset holdout accessed = False'); print('August Confirmation accessed = False'); return 0

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
    inst=f'{sym}-USDT-SWAP'; lo=date_ms('2024-06-30'); hi=date_ms('2024-07-15')
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
    return {'start_ms':lo,'end_ms':hi,'timestamps':ts,'prices':px,'sizes':sz}

def build_vwap(stream):
    lo,hi=stream['start_ms'],stream['end_ms']; n=(hi-lo)//GRID_MS
    pv=[0.0]*n; sv=[0.0]*n; cnt=[0]*n
    for i,t in enumerate(stream['timestamps']):
        k=(int(t)-lo)//GRID_MS
        if 0<=k<n:
            p=float(stream['prices'][i]); s=float(stream['sizes'][i]); pv[k]+=p*s; sv[k]+=s; cnt[k]+=1
    vw=[None]*n
    for k in range(n):
        if cnt[k] and sv[k]>0: vw[k]=pv[k]/sv[k]
    return vw

def records(vw,start):
    out=[]
    for k,cur in enumerate(vw):
        t=start+(k+1)*GRID_MS; anc=vw[k-ANCHOR_OFFSET] if k>=ANCHOR_OFFSET else None
        if cur is None or anc is None: out.append({'t':t,'valid':False}); continue
        d=10000.0*(float(cur)/float(anc)-1.0); out.append({'t':t,'valid':True,'anchor':float(anc),'current':float(cur),'disp_bps':d})
    return out

def candidates(rs):
    lo=date_ms(PERF_START); hi=date_ms(PERF_END)+DAY_MS; out=[]; prev=None
    for r in rs:
        if not r.get('valid'): prev=r; continue
        if prev is None or not prev.get('valid'): prev=r; continue
        pd=float(prev['disp_bps']); d=float(r['disp_bps']); t=int(r['t'])
        if lo<=t<hi and abs(pd)<THRESHOLD_BPS and abs(d)>=THRESHOLD_BPS:
            anc=float(r['anchor']); cur=float(r['current']); out.append({'date':day_text(t),'trigger_ts':t,'direction':-1 if d>0 else 1,'trigger_disp_bps':d,'target_price':anc+RETRACE*(cur-anc)})
        prev=r
    return out

def proxy(stream,target,day_end):
    i=bisect.bisect_left(stream['timestamps'],target)
    if i>=len(stream['timestamps']): return None
    actual=int(stream['timestamps'][i])
    if actual>target+TOLERANCE_MS or actual>=day_end: return None
    return actual,float(stream['prices'][i])
def reverted(direction,price,target): return price>=target if direction==1 else price<=target
def ceiling(t,origin):
    x=t-origin; return origin+((x+GRID_MS-1)//GRID_MS)*GRID_MS if x>0 else origin

def exit_decision(c,rs,start,entry):
    first=max(0,(entry-start)//GRID_MS); max_t=ceiling(entry+MAX_HOLD_MS,start); max_i=min(len(rs)-1,(max_t-start)//GRID_MS-1)
    for i in range(int(first),max_i+1):
        r=rs[i]; t=int(r['t'])
        if t<=entry or not r.get('valid'): continue
        cur=float(r['current']); hit=cur>=c['target_price'] if c['direction']==1 else cur<=c['target_price']
        if hit:return t,'reversion'
    return max_t,'time'

def simulate(stream,rs,cands,lat):
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
        if leg is None:
            e['incomplete_reason']='entry_missing'; counts['entry_missing']+=1; available=t+lat+TOLERANCE_MS+COOLDOWN_MS; ev.append(e); continue
        ets,ep=leg
        if reverted(c['direction'],ep,c['target_price']):
            e['entry_ts']=ets; e['entry_price']=ep; e['incomplete_reason']='entry_already_reverted'; counts['entry_already_reverted']+=1; available=ets+COOLDOWN_MS; ev.append(e); continue
        e['entry_ts']=ets; e['entry_price']=ep; xd,reason=exit_decision(c,rs,stream['start_ms'],ets); e['exit_decision_ts']=xd; e['exit_reason']=reason
        if xd>=de:
            e['incomplete_reason']='exit_day_cross'; counts['exit_day_cross']+=1; locked=d; available=de; ev.append(e); continue
        x=proxy(stream,xd+lat,de)
        if x is None:
            e['incomplete_reason']='exit_missing'; counts['exit_missing']+=1; locked=d; available=de; ev.append(e); continue
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
        if ets>=xd:r['incomplete_reason']='entry_after_exit_decision'; out.append(r); continue
        x=proxy(stream,xd+lat,de)
        if x is None:r['incomplete_reason']='exit_missing'; out.append(r); continue
        _xt,xp=x; r['completed']=True; r['gross_edge_bps']=p['direction']*10000.0*(xp/ep-1.0); out.append(r)
    return out

def trimmed(vals):
    if not vals:return None
    x=sorted(vals); k=math.floor(.1*len(x)); core=x[k:len(x)-k] if k else x
    return statistics.fmean(core) if core else None

def metrics(events):
    comp=[e for e in events if e.get('completed') and e.get('gross_edge_bps') is not None]; vals=[float(e['gross_edge_bps']) for e in comp]
    byday={}; side={1:[],-1:[]}
    for e in comp:
        v=float(e['gross_edge_bps']); byday.setdefault(e['date'],[]).append(v); side[e['direction']].append(v)
    daymeans={d:statistics.fmean(v) for d,v in byday.items()}
    return {'decisions':len(events),'completed':len(comp),'active_days':len(byday),'completion_rate':len(comp)/len(events) if events else 0.0,'mean_bps':statistics.fmean(vals) if vals else None,'median_bps':statistics.median(vals) if vals else None,'trimmed_mean_bps':trimmed(vals),'positive_event_share':sum(v>0 for v in vals)/len(vals) if vals else 0.0,'positive_active_day_share':sum(v>0 for v in daymeans.values())/len(daymeans) if daymeans else 0.0,'long_count':len(side[1]),'short_count':len(side[-1]),'long_mean_bps':statistics.fmean(side[1]) if side[1] else None,'short_mean_bps':statistics.fmean(side[-1]) if side[-1] else None,'sum_gross_bps':sum(vals),'day_means':daymeans}

def run():
    preflight()
    per={}; all_primary=[]; stress={1000:{},2000:{}}
    for i,sym in enumerate(ASSETS,1):
        print(f'E007R1 [{i}/8] {sym}: load stream',flush=True); st=load_stream(sym); vw=build_vwap(st); rs=records(vw,st['start_ms']); cs=candidates(rs)
        print(f'E007R1 {sym}: candidates={len(cs)}',flush=True); prim,state=simulate(st,rs,cs,PRIMARY_LAT); pm=metrics(prim)
        sm={}
        for lat in STRESS_LATS:
            se=replay(prim,st,lat); stress[lat][sym]=metrics(se); sm[str(lat)]=stress[lat][sym]
        per[sym]={'primary':pm,'stress':sm,'state':state,'candidate_count':len(cs)}; all_primary.extend([dict(e,instrument=sym) for e in prim])
        print(f'E007R1 {sym}: decisions={pm["decisions"]} completed={pm["completed"]} mean={pm["mean_bps"]}',flush=True)
    # Cross-asset aggregates use all 8; inactive/no-completion contributes 0 bps rather than disappearing.
    inst_means={s:(per[s]['primary']['mean_bps'] if per[s]['primary']['mean_bps'] is not None else 0.0) for s in ASSETS}
    eq=statistics.fmean(inst_means.values()); med=statistics.median(inst_means.values()); pos=sum(v>0 for v in inst_means.values()); active=sum(per[s]['primary']['completed']>0 for s in ASSETS); active5=sum(per[s]['primary']['completed']>=5 for s in ASSETS)
    completed=[e for e in all_primary if e.get('completed') and e.get('gross_edge_bps') is not None]; pooled=[float(e['gross_edge_bps']) for e in completed]
    stress_eq={}
    for lat in STRESS_LATS:
        xs=[]
        for s in ASSETS:
            m=stress[lat][s]['mean_bps']; xs.append(m if m is not None else 0.0)
        stress_eq[str(lat)]=statistics.fmean(xs)
    contrib={s:abs(float(per[s]['primary']['sum_gross_bps'])) for s in ASSETS}; denom=sum(contrib.values()); top_share=max(contrib.values())/denom if denom>0 else 1.0
    gates={
      'all_8_attempted':len(per)==8,
      'active_assets_gte_6':active>=6,
      'assets_completed_gte5_count_gte4':active5>=4,
      'pooled_completed_gte40':len(completed)>=40,
      'equal_weight_mean_gte20':eq>=20.0,
      'median_instrument_mean_gte15':med>=15.0,
      'positive_instruments_gte5':pos>=5,
      'pooled_trimmed_mean_gte15':(trimmed(pooled) is not None and trimmed(pooled)>=15.0),
      'pooled_median_gte10':(bool(pooled) and statistics.median(pooled)>=10.0),
      'lat1000_equal_weight_gte15':stress_eq['1000']>=15.0,
      'lat2000_equal_weight_gte10':stress_eq['2000']>=10.0,
      'top_instrument_abs_contribution_lte035':top_share<=0.35,
    }
    status=PASS if all(gates.values()) else FAIL
    rep={'stage':STAGE,'status':status,'protocol':'sc001-e007r1-multiasset-gross-feasibility-protocol-v0.1.md','assets':list(ASSETS),'performance_dates':[PERF_START,PERF_END],'per_instrument':per,'aggregate':{'active_assets':active,'assets_with_gte5_completed':active5,'pooled_completed':len(completed),'equal_weight_instrument_mean_bps':eq,'median_instrument_mean_bps':med,'positive_instrument_count':pos,'pooled_mean_bps':statistics.fmean(pooled) if pooled else None,'pooled_median_bps':statistics.median(pooled) if pooled else None,'pooled_trimmed_mean_bps':trimmed(pooled),'stress_equal_weight_mean_bps':stress_eq,'top_instrument_abs_contribution_share':top_share,'instrument_mean_bps':inst_means},'gates':gates,'failed_gates':[k for k,v in gates.items() if not v],'gross_bps_calculated':True,'discrete_contract_pnl_calculated':False,'fees_or_net_pnl_calculated':False,'l2_accessed':False,'asset_holdout_accessed':False,'august_confirmation_accessed':False,'historical_exact_execution_specs_verified':False}
    atomic(REPORT,rep)
    print(status); print('active_assets =',active,'/ 8'); print('pooled_completed =',len(completed)); print('equal_weight_mean_bps =',eq); print('median_instrument_mean_bps =',med); print('positive_instruments =',pos,'/ 8'); print('pooled_trimmed_mean_bps =',rep['aggregate']['pooled_trimmed_mean_bps']); print('pooled_median_bps =',rep['aggregate']['pooled_median_bps']); print('lat1000_equal_weight_mean_bps =',stress_eq['1000']); print('lat2000_equal_weight_mean_bps =',stress_eq['2000']); print('top_instrument_abs_contribution_share =',top_share); print('failed_gates =',rep['failed_gates']); print('discrete contract PnL calculated = False'); print('asset holdout accessed = False'); print('August Confirmation accessed = False'); print('report =',REPORT)
    return 0 if status==PASS else 2

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['preflight','run']); a=ap.parse_args(); return preflight() if a.mode=='preflight' else run()
if __name__=='__main__': raise SystemExit(main())
