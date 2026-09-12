"""SC001-DATA-A002-B01: frozen Binance BTCUSDT aggTrades 2023-Q2. Data-only."""
from __future__ import annotations
import csv, hashlib, io, json, os, shutil, zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen

STAGE="SC001-DATA-A002-B01"; VERSION="0.1"; BATCH_ID="2023-Q2"
SYMBOL="BTCUSDT"; DATASET="aggTrades"
FROZEN_CALENDAR_SHA256="e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b"
PREFLIGHT_STAGE="SC001-DATA-A002-PREFLIGHT"
PREFLIGHT_PATH=Path("/storage/emulated/0/Download/SC001_DATA_A002_PREFLIGHT/sc001_data_a002_preflight_report.json")
WORKSPACE=Path("/storage/emulated/0/Download/SC001_DATA_A002_B01_2023Q2"); ARCHIVES=WORKSPACE/"archives"
SESSION_DOWNLOAD_CAP_BYTES=300_000_000; WORKSPACE_CAP_BYTES=300_000_000
PER_FILE_CAP_BYTES=256_000_000; MINIMUM_FREE_RESERVE_BYTES=4_000_000_000
MAX_UNCOMPRESSED_MEMBER_BYTES=2_000_000_000; SMALL_CAP=1_000_000
EXPECTED_BATCH_COMPRESSED_BYTES=91_819_076; EXPECTED_DAYS=5
BASE=f"https://data.binance.vision/data/futures/um/daily/aggTrades/{SYMBOL}"
EXPECTED=[
("2023-04-12","EVENT","CPI",18877620,"07be4bf404751ae8e14749f3c5e5abd31de05feecbf34f9d8f95e9e790ce5af2"),
("2023-04-23","ORDINARY_WEEKEND",None,12440613,"0164fa1cc3380992990c44763b898bd1ab42533bd218ca1575c8526b2ec79e72"),
("2023-05-01","ORDINARY_WEEKDAY",None,22518837,"1978075ebf9b39fd4950d5fe4f72d08f650a6deabfd2cfc01c8fe763d0a7bf52"),
("2023-05-05","EVENT","NFP",21579218,"5efcc4c5faaf44ba6f2bd8bd80d32f64ca350a785f64da2862a7e93a1348837e"),
("2023-06-14","EVENT","FOMC",16402788,"73628c85d9d60ffd5dd0d5aa2c40b625ecfca68d302591d813ab3a8b7be1cfaf"),
]
HEADER=["agg_trade_id","price","quantity","first_trade_id","last_trade_id","transact_time","is_buyer_maker"]
network_bytes_read=0

def now(): return datetime.now(timezone.utc).isoformat()
def size_dir(p):
    if not p.exists(): return 0
    return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
def free(p): return shutil.disk_usage(p).free
def atomic_json(p,obj):
    t=p.with_suffix(p.suffix+'.tmp'); t.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding='utf-8'); os.replace(t,p)
def safety(extra=0):
    if network_bytes_read>SESSION_DOWNLOAD_CAP_BYTES: raise RuntimeError('session cap exceeded')
    if size_dir(WORKSPACE)+max(0,extra)>WORKSPACE_CAP_BYTES: raise RuntimeError('workspace cap exceeded')
    if free(WORKSPACE)-max(0,extra)<MINIMUM_FREE_RESERVE_BYTES: raise RuntimeError('free-space reserve violated')
def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def small(url):
    global network_bytes_read
    with urlopen(Request(url,headers={'User-Agent':'BotMarketplace-SC001-A002-B01/0.1'}),timeout=60) as r: b=r.read(SMALL_CAP+1)
    if len(b)>SMALL_CAP: raise RuntimeError('small response cap exceeded')
    network_bytes_read+=len(b); safety(); return b
def checksum(raw,fn):
    vals=[]
    for ln in raw.decode().splitlines():
        p=ln.split()
        if p and len(p[0])==64: vals.append((p[0].lower(),p[-1].lstrip('*')))
    exact=[s for s,n in vals if n==fn]
    if len(exact)==1:return exact[0]
    if len(vals)==1:return vals[0][0]
    raise RuntimeError(f'checksum parse failed: {fn}')
def head_len(url):
    q=Request(url,method='HEAD',headers={'User-Agent':'BotMarketplace-SC001-A002-B01/0.1'})
    with urlopen(q,timeout=60) as r:
        if r.status!=200 or r.geturl()!=url: raise RuntimeError('HEAD identity failure')
        x=r.headers.get('Content-Length')
        if x is None: raise RuntimeError('missing Content-Length')
        return int(x)
def download(url,dest,n,sha):
    global network_bytes_read
    if n>PER_FILE_CAP_BYTES: raise RuntimeError('per-file cap exceeded')
    if dest.exists() and dest.stat().st_size==n and sha_file(dest)==sha:
        return {'status':'REUSED','bytes':n,'sha256':sha,'network_bytes':0}
    if dest.exists(): dest.unlink()
    part=dest.with_suffix(dest.suffix+'.part')
    if part.exists(): part.unlink()
    safety(n); got=0; h=hashlib.sha256()
    try:
        with urlopen(Request(url,headers={'User-Agent':'BotMarketplace-SC001-A002-B01/0.1'}),timeout=120) as r, part.open('wb') as out:
            if r.status!=200 or r.geturl()!=url: raise RuntimeError('GET identity failure')
            cl=r.headers.get('Content-Length')
            if cl and int(cl)!=n: raise RuntimeError('Content-Length changed')
            while True:
                b=r.read(1024*1024)
                if not b: break
                got+=len(b); network_bytes_read+=len(b)
                if got>n or got>PER_FILE_CAP_BYTES or network_bytes_read>SESSION_DOWNLOAD_CAP_BYTES: raise RuntimeError('download cap/size failure')
                h.update(b); out.write(b)
            out.flush(); os.fsync(out.fileno())
        if got!=n or h.hexdigest()!=sha: raise RuntimeError('download size/SHA mismatch')
        os.replace(part,dest); return {'status':'DOWNLOADED','bytes':got,'sha256':sha,'network_bytes':got}
    except Exception:
        if part.exists(): part.unlink()
        raise

def posdec(s):
    x=Decimal(s.strip())
    if not x.is_finite() or x<=0: raise ValueError('bad decimal')
    return x

def validate_zip(path,date):
    start=datetime.fromisoformat(date).replace(tzinfo=timezone.utc); end=start+timedelta(days=1)
    lo=int(start.timestamp()*1000); hi=int(end.timestamp()*1000); member=f'{SYMBOL}-aggTrades-{date}.csv'
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None: raise RuntimeError('ZIP CRC failure')
        infos=[x for x in z.infolist() if not x.is_dir()]
        if len(infos)!=1 or Path(infos[0].filename).name!=member: raise RuntimeError('ZIP member mismatch')
        inf=infos[0]
        if inf.file_size>MAX_UNCOMPRESSED_MEMBER_BYTES: raise RuntimeError('uncompressed member cap exceeded')
        rows=bad=outday=back=dupback=gaps=overlap=ugaps=samems=mt=mf=0
        firstaid=lastaid=firsttid=lasttid=firstts=lastts=None
        pa=pu=pt=None; mins=set(); mode=None; seen=False
        with z.open(inf) as raw:
            for r in csv.reader(io.TextIOWrapper(raw,encoding='utf-8',newline='')):
                if not r: continue
                if not seen:
                    try:int(r[0].strip())
                    except Exception:
                        if [x.strip().lower() for x in r]!=HEADER: raise RuntimeError('unexpected CSV header')
                        mode='HEADER_PRESENT'; seen=True; continue
                    mode='NO_HEADER'; seen=True
                if len(r)!=7: bad+=1; continue
                try:
                    aid=int(r[0]); posdec(r[1]); posdec(r[2]); f=int(r[3]); l=int(r[4]); ts=int(r[5]); mk=r[6].strip().lower()
                    if f>l or mk not in {'true','false'}: raise ValueError
                except Exception: bad+=1; continue
                rows+=1
                if firstaid is None:firstaid,firsttid,firstts=aid,f,ts
                lastaid,lasttid,lastts=aid,l,ts
                if lo<=ts<hi: mins.add((ts-lo)//60000)
                else: outday+=1
                if pt is not None:
                    if ts<pt: back+=1
                    elif ts==pt: samems+=1
                if pa is not None:
                    d=aid-pa
                    if d<=0: dupback+=1
                    elif d!=1: gaps+=1
                if pu is not None:
                    if f<=pu: overlap+=1
                    elif f!=pu+1: ugaps+=1
                if mk=='true': mt+=1
                else: mf+=1
                pa,pu,pt=aid,l,ts
    gates={'rows_positive':rows>0,'invalid_rows_zero':bad==0,'all_rows_inside_target_utc_day':outday==0,
           'timestamps_monotonic_nondecreasing':back==0,'agg_trade_ids_strict_contiguous':dupback==0 and gaps==0,
           'underlying_trade_ranges_nonoverlapping':overlap==0,'all_1440_minutes_observed':len(mins)==1440,
           'both_maker_flags_observed':mt>0 and mf>0}
    return {'status':'PASS' if all(gates.values()) else 'REVIEW','member':inf.filename,'compressed_size':inf.compress_size,
            'uncompressed_size':inf.file_size,'header_mode':mode,'rows':rows,'invalid_rows':bad,'out_of_day_rows':outday,
            'timestamp_backwards':back,'same_ms_adjacent':samems,'agg_id_duplicate_or_backwards':dupback,'agg_id_gap_count':gaps,
            'underlying_overlap_or_backwards':overlap,'underlying_gap_count_diagnostic':ugaps,'minute_buckets_observed':len(mins),
            'maker_true_rows':mt,'maker_false_rows':mf,'first_agg_trade_id':firstaid,'last_agg_trade_id':lastaid,
            'first_underlying_trade_id':firsttid,'last_underlying_trade_id':lasttid,'first_ts':firstts,'last_ts':lastts,
            'first_ts_utc':datetime.fromtimestamp(firstts/1000,tz=timezone.utc).isoformat() if firstts else None,
            'last_ts_utc':datetime.fromtimestamp(lastts/1000,tz=timezone.utc).isoformat() if lastts else None,'gates':gates}
def verify_preflight():
    if not PREFLIGHT_PATH.exists(): raise RuntimeError(f'missing preflight: {PREFLIGHT_PATH}')
    o=json.loads(PREFLIGHT_PATH.read_text(encoding='utf-8')); s=o.get('scope') or {}
    if o.get('stage')!=PREFLIGHT_STAGE or o.get('overall_status')!='PASS' or o.get('strategy_pnl_calculated') is not False or o.get('archive_bodies_downloaded') is not False: raise RuntimeError('preflight state mismatch')
    if s.get('frozen_calendar_sha256')!=FROZEN_CALENDAR_SHA256 or s.get('split')!='DEV_ONLY' or o.get('days_total')!=25 or o.get('days_passed')!=25: raise RuntimeError('preflight scope/count mismatch')
    by={x['date']:x for x in o.get('days',[])}
    if len(by)!=25: raise RuntimeError('preflight unique-day mismatch')
    for d,_,_,n,sha in EXPECTED:
        x=by.get(d)
        if not x or x.get('status')!='PASS' or x.get('expected_sha256')!=sha or (x.get('archive_metadata') or {}).get('content_length')!=n: raise RuntimeError(f'preflight identity mismatch: {d}')
    return {'path':str(PREFLIGHT_PATH),'frozen_calendar_sha256':s['frozen_calendar_sha256'],'days_verified':[x[0] for x in EXPECTED]}
def outputs(rep):
    atomic_json(WORKSPACE/'sc001_data_a002_b01_report.json',rep)
    man={'stage':STAGE,'version':VERSION,'batch_id':BATCH_ID,'overall_status':rep.get('overall_status'),'strategy_pnl_calculated':False,'strategy_features_calculated':False,'archives_retained':True,'files':[]}
    for x in rep.get('days',[]):
        v=x['validation']; man['files'].append({'date':x['date'],'sample_type':x['sample_type'],'event_class':x['event_class'],'filename':x['filename'],'bytes':x['archive']['bytes'],'sha256':x['archive']['sha256'],'rows':v['rows'],'first_agg_trade_id':v['first_agg_trade_id'],'last_agg_trade_id':v['last_agg_trade_id'],'first_ts':v['first_ts'],'last_ts':v['last_ts'],'minute_buckets_observed':v['minute_buckets_observed'],'status':x['status']})
    atomic_json(WORKSPACE/'sc001_data_a002_b01_manifest.json',man)
    lines=['# SC001-DATA-A002-B01 — Binance BTCUSDT aggTrades 2023-Q2','',f"- Overall: `{rep.get('overall_status')}`",'- Strategy/P&L calculated: **NO**','- Strategy features calculated: **NO**',f"- Days passed: {rep.get('days_passed',0)} / {EXPECTED_DAYS}",f"- Network bytes read: {rep.get('network_bytes_read',0)}",'','## Day checks']
    for x in rep.get('days',[]):
        v=x['validation']; lines.append(f"- {x['date']} [{x['sample_type']}{('/'+x['event_class']) if x['event_class'] else ''}]: **{x['status']}**; rows={v['rows']}; minutes={v['minute_buckets_observed']}/1440; agg_id_gaps={v['agg_id_gap_count']}; timestamp_backwards={v['timestamp_backwards']}; invalid_rows={v['invalid_rows']}; out_of_day={v['out_of_day_rows']}")
    lines+=['','## Boundary','Data qualification only. No strategy/P&L, VALIDATION/FINAL, maker-queue inference, or L2 execution model.']
    (WORKSPACE/'sc001_data_a002_b01_summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    atomic_json(WORKSPACE/'sc001_data_a002_b01_final_safety.json',{'stage':STAGE,'network_bytes_read':rep.get('network_bytes_read',0),'workspace_bytes_after_outputs':size_dir(WORKSPACE),'free_bytes_after_outputs':free(WORKSPACE),'caps':{'session_download':SESSION_DOWNLOAD_CAP_BYTES,'workspace':WORKSPACE_CAP_BYTES,'per_file':PER_FILE_CAP_BYTES,'reserve':MINIMUM_FREE_RESERVE_BYTES,'max_uncompressed_member':MAX_UNCOMPRESSED_MEMBER_BYTES}})
def main():
    global network_bytes_read
    WORKSPACE.mkdir(parents=True,exist_ok=True); ARCHIVES.mkdir(parents=True,exist_ok=True); safety(); pre=verify_preflight()
    rep={'stage':STAGE,'version':VERSION,'batch_id':BATCH_ID,'started_at_utc':now(),'strategy_pnl_calculated':False,'strategy_features_calculated':False,'validation_or_final_accessed':False,
         'scope':{'venue':'Binance USD-M Futures','symbol':SYMBOL,'dataset':DATASET,'split':'DEV_ONLY','batch':BATCH_ID,'dates':[x[0] for x in EXPECTED],'frozen_calendar_sha256':FROZEN_CALENDAR_SHA256,'expected_compressed_bytes':EXPECTED_BATCH_COMPRESSED_BYTES},
         'preflight_verification':pre,'safety':{'session_download_cap_bytes':SESSION_DOWNLOAD_CAP_BYTES,'workspace_cap_bytes':WORKSPACE_CAP_BYTES,'per_file_cap_bytes':PER_FILE_CAP_BYTES,'minimum_free_reserve_bytes':MINIMUM_FREE_RESERVE_BYTES,'free_bytes_start':free(WORKSPACE)},'days':[]}
    pa=pu=None; order=[]
    try:
        for date,stype,eclass,n,sha in EXPECTED:
            fn=f'{SYMBOL}-aggTrades-{date}.zip'; url=f'{BASE}/{fn}'; cu=url+'.CHECKSUM'
            print(f'[{date}] checksum/HEAD...'); live=checksum(small(cu),fn); ln=head_len(url)
            if live!=sha or ln!=n: raise RuntimeError(f'remote identity changed: {date}')
            print(f'[{date}] download/reuse...'); arc=download(url,ARCHIVES/fn,n,sha)
            print(f'[{date}] ZIP/CSV validation...'); val=validate_zip(ARCHIVES/fn,date)
            if pa is not None and val['first_agg_trade_id']<=pa: order.append({'date':date,'kind':'agg_trade_id','previous_last':pa,'current_first':val['first_agg_trade_id']})
            if pu is not None and val['first_underlying_trade_id']<=pu: order.append({'date':date,'kind':'underlying_trade_id','previous_last':pu,'current_first':val['first_underlying_trade_id']})
            pa,pu=val['last_agg_trade_id'],val['last_underlying_trade_id']
            day={'date':date,'sample_type':stype,'event_class':eclass,'filename':fn,'url':url,'checksum_url':cu,'frozen_expected_bytes':n,'frozen_expected_sha256':sha,'live_head_bytes':ln,'live_checksum_sha256':live,'archive':arc,'validation':val,'status':'PASS' if arc['bytes']==n and arc['sha256']==sha and val['status']=='PASS' else 'REVIEW'}
            rep['days'].append(day); rep['network_bytes_read']=network_bytes_read; rep['days_passed_so_far']=sum(x['status']=='PASS' for x in rep['days']); atomic_json(WORKSPACE/'sc001_data_a002_b01_report.json',rep); safety()
        rep['cross_selected_day_order_violations']=order; rep['days_total']=len(rep['days']); rep['days_passed']=sum(x['status']=='PASS' for x in rep['days']); rep['network_bytes_read']=network_bytes_read
        rep['overall_status']='PASS' if rep['days_total']==EXPECTED_DAYS and rep['days_passed']==EXPECTED_DAYS and not order else 'REVIEW'; rep['finished_at_utc']=now(); outputs(rep)
    except Exception as e:
        rep['overall_status']='ERROR'; rep['error']=repr(e); rep['network_bytes_read']=network_bytes_read; rep['finished_at_utc']=now(); outputs(rep); raise
    rep['workspace_bytes_after_outputs']=size_dir(WORKSPACE); outputs(rep)
    print(f"COMPLETE: {rep['overall_status']} {rep['days_passed']}/{rep['days_total']} | network={network_bytes_read} | P&L=NO")
if __name__=='__main__': main()
