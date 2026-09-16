from __future__ import annotations
import json, os, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAGE='SC001-E007R1-TRADE-METADATA-PREFLIGHT'
PASS='E007R1_TRADE_METADATA_PREFLIGHT_PASS'
REVIEW='E007R1_TRADE_METADATA_PREFLIGHT_REVIEW'
DOMAINS=('https://www.okx.com','https://us.okx.com')
PATH='/priapi/v5/broker/public/trade-data/download-link'
REFERER='https://www.okx.com/historical-data'
UA='BotMarketplace-SC001-E007R1-TradePreflight/0.1'
ALLOWED_HOST='static.okx.com'
TIMEOUT=60
RETRIES=3
MAX_META_BYTES=8_000_000
MAX_TOTAL_BYTES=4_000_000_000
ASSETS=('BTC','ETH','DOGE','ORDI','UNI','XRP','OP','BCH')
PERF_START='2024-07-01'; PERF_END='2024-07-14'
ARCHIVE_DATES=tuple(['2024-06-30']+[f'2024-07-{d:02d}' for d in range(1,16)])
EXPECTED=len(ASSETS)*len(ARCHIVE_DATES)
DATA_ROOT=Path(os.environ.get('SC001_DATA_ROOT',str(Path.home()/'sc001_data'))).expanduser().resolve()
OUT_DIR=DATA_ROOT/'SC001_E007R1_TRADE_METADATA_PREFLIGHT'
OUT=OUT_DIR/'sc001_e007r1_trade_metadata_preflight_report.json'

def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+'.tmp')
    with q.open('w',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(q,p)

def bounds(d):
    x=datetime.strptime(d,'%Y-%m-%d').replace(tzinfo=timezone.utc)
    lo=int(x.timestamp()*1000); hi=int((x+timedelta(days=1)-timedelta(milliseconds=1)).timestamp()*1000)
    return lo,hi

def trusted(url,fn):
    try:
        u=urlparse(url)
        return u.scheme=='https' and (u.hostname or '').lower()==ALLOWED_HOST and Path(u.path).name==fn
    except Exception:return False

def walk(node):
    if isinstance(node,dict):
        fn=node.get('filename') or node.get('fileName')
        url=node.get('url') or node.get('fileUrl') or node.get('downloadUrl')
        if isinstance(fn,str) and isinstance(url,str): yield fn,url
        for v in node.values(): yield from walk(v)
    elif isinstance(node,list):
        for v in node: yield from walk(v)

def request(domain,payload):
    url=domain+PATH+'?t='+str(int(time.time()*1000))
    body=json.dumps(payload,separators=(',',':')).encode()
    req=Request(url,data=body,method='POST',headers={'User-Agent':UA,'Accept':'application/json,*/*','Content-Type':'application/json','Referer':REFERER})
    try:
        with urlopen(req,timeout=TIMEOUT) as r: raw=r.read(MAX_META_BYTES+1)
        if len(raw)>MAX_META_BYTES:return None,'response_cap'
        obj=json.loads(raw.decode('utf-8'))
        if isinstance(obj,dict) and obj.get('code')=='0':return obj,None
        return None,'code:'+str(obj.get('code') if isinstance(obj,dict) else 'not_dict')
    except HTTPError as e:return None,f'http:{e.code}'
    except (URLError,TimeoutError,OSError,ValueError) as e:return None,f'{type(e).__name__}:{e}'

def head(url,fn):
    req=Request(url,method='HEAD',headers={'User-Agent':UA,'Referer':REFERER})
    with urlopen(req,timeout=TIMEOUT) as r:
        final=r.geturl(); status=int(getattr(r,'status',200)); cl=r.headers.get('Content-Length')
    if status!=200 or not cl or not cl.isdigit() or int(cl)<=0 or not trusted(final,fn): raise RuntimeError('HEAD identity/size failure')
    return int(cl)

def resolve(symbol,date):
    inst=f'{symbol}-USDT-SWAP'; family=f'{symbol}-USDT'; fn=f'{inst}-trades-{date}.zip'
    qdates=(date,(datetime.strptime(date,'%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d'))
    attempts=[]
    for qd in qdates:
        lo,hi=bounds(qd)
        payload={'module':'1','instType':'SWAP','instQueryParam':{'instFamilyList':[family]},'dateQuery':{'dateAggrType':'daily','begin':str(lo),'end':str(hi)}}
        for domain in DOMAINS:
            for attempt in range(1,RETRIES+1):
                obj,err=request(domain,payload); attempts.append({'query_date':qd,'domain':domain,'attempt':attempt,'ok':obj is not None,'error':err})
                if obj is None:
                    if err=='http:429' and attempt<RETRIES: time.sleep(attempt); continue
                    break
                matches=[]
                for got,url in walk(obj.get('data')):
                    if got==fn and trusted(url,fn): matches.append(url)
                matches=list(dict.fromkeys(matches))
                if len(matches)==1:
                    try:return {'ok':True,'instrument':inst,'date':date,'filename':fn,'url':matches[0],'bytes':head(matches[0],fn),'attempts':attempts}
                    except Exception as e: attempts.append({'head_error':f'{type(e).__name__}:{e}'})
                elif len(matches)>1:return {'ok':False,'instrument':inst,'date':date,'filename':fn,'error':'multiple_exact_urls','attempts':attempts}
                break
        time.sleep(0.02)
    return {'ok':False,'instrument':inst,'date':date,'filename':fn,'error':'exact_archive_not_resolved','attempts':attempts}

def main():
    rows=[]; total=0
    for ai,s in enumerate(ASSETS,1):
        for di,d in enumerate(ARCHIVE_DATES,1):
            print(f'[{ai}/{len(ASSETS)} {di}/{len(ARCHIVE_DATES)}] {s} {d}',flush=True)
            r=resolve(s,d); rows.append(r)
            if r.get('ok'): total+=int(r['bytes']); print('PASS',r['filename'],r['bytes'],flush=True)
            else: print('REVIEW',r['filename'],r.get('error'),flush=True)
    oks=[r for r in rows if r.get('ok')]
    unique=len({r['filename'] for r in oks})==len(oks)
    passed=len(rows)==EXPECTED and len(oks)==EXPECTED and unique and total>0 and total<=MAX_TOTAL_BYTES
    status=PASS if passed else REVIEW
    rep={'stage':STAGE,'status':status,'assets':list(ASSETS),'performance_dates':{'start':PERF_START,'end':PERF_END},'archive_dates':list(ARCHIVE_DATES),'expected_files':EXPECTED,'resolved_files':len(oks),'unique_filenames':unique,'expected_total_bytes':total,'rows':rows,'trade_body_downloaded':False,'l2_body_downloaded':False,'strategy_signal_calculated':False,'strategy_pnl_calculated':False,'asset_holdout_accessed':False,'august_confirmation_accessed':False,'historical_exact_execution_specs_verified':False}
    atomic_json(OUT,rep)
    print(status)
    print('expected_files =',EXPECTED)
    print('resolved_files =',len(oks))
    print('expected_total_bytes =',total)
    print('trade body downloaded = False')
    print('asset holdout accessed = False')
    print('August Confirmation accessed = False')
    print('strategy signal/PnL calculated = False')
    print('report =',OUT)
    return 0 if passed else 2

if __name__=='__main__': raise SystemExit(main())
