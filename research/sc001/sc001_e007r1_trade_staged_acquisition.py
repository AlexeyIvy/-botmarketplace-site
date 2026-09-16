from __future__ import annotations
import argparse,csv,hashlib,io,json,os,shutil,time,zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen

DATA_ROOT=Path(os.environ.get('SC001_DATA_ROOT',str(Path.home()/'sc001_data'))).expanduser().resolve()
PARENT=DATA_ROOT/'SC001_E007R1_TRADE_METADATA_PREFLIGHT'/'sc001_e007r1_trade_metadata_preflight_report.json'
ROOT=DATA_ROOT/'SC001_E007R1_TRADE_ACQUISITION'; ARCH=ROOT/'archives'; REPORTS=ROOT/'reports'
UA='BotMarketplace-SC001-E007R1-Acquisition/0.1'; REFERER='https://www.okx.com/historical-data'; HOST='static.okx.com'
HEADER=['instrument_name','trade_id','side','price','size','created_time']
BATCHES={'a':('BTC','ETH'),'b':('DOGE','ORDI'),'c':('UNI','XRP'),'d':('OP','BCH')}
TOKENS={k:f'E007R1_TRADE_ACQUISITION_BATCH_{k.upper()}_PASS' for k in BATCHES}
VERIFY='E007R1_TRADE_ACQUISITION_VERIFY_PASS'; MIN_FREE=5_000_000_000

def fail(s): raise RuntimeError(s)
def load(p):
    if not p.exists(): fail(f'missing {p}')
    x=json.loads(p.read_text());
    if not isinstance(x,dict): fail('json object expected')
    return x

def atomic(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+'.tmp')
    with q.open('w') as f:
        json.dump(obj,f,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(q,p)

def sha256(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()

def trusted(url,fn):
    u=urlparse(url); return u.scheme=='https' and (u.hostname or '').lower()==HOST and Path(u.path).name==fn

def archive_check(p,inst):
    with zipfile.ZipFile(p,'r') as z:
        bad=z.testzip()
        if bad is not None: fail(f'CRC fail {p.name}: {bad}')
        members=[m for m in z.infolist() if not m.is_dir()]
        if len(members)!=1: fail(f'bad member count {p.name}: {len(members)}')
        with z.open(members[0]) as raw:
            r=csv.reader(io.TextIOWrapper(raw,encoding='utf-8',newline=''))
            if next(r,None)!=HEADER: fail(f'bad header {p.name}')
            first=next(r,None)
            if first is None or len(first)!=6 or first[0]!=inst: fail(f'bad first data row {p.name}')
        return {'member':members[0].filename,'member_uncompressed_bytes':members[0].file_size}

def parent_rows():
    p=load(PARENT)
    if p.get('status')!='E007R1_TRADE_METADATA_PREFLIGHT_PASS': fail('parent not PASS')
    rows=p.get('rows') or []
    if len(rows)!=128 or int(p.get('resolved_files',0))!=128: fail('parent row count mismatch')
    return p,rows

def download(row):
    fn=row['filename']; url=row['url']; expected=int(row['bytes']); inst=row['instrument']
    if not trusted(url,fn): fail(f'untrusted parent url {fn}')
    sym=inst.split('-')[0]; dest=ARCH/sym/fn; dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and dest.stat().st_size==expected:
        meta=archive_check(dest,inst); return dest,sha256(dest),meta,'reused'
    tmp=Path(str(dest)+'.part'); tmp.unlink(missing_ok=True)
    req=Request(url,headers={'User-Agent':UA,'Referer':REFERER})
    with urlopen(req,timeout=120) as resp:
        final=resp.geturl()
        if not trusted(final,fn): fail(f'final url mismatch {fn}')
        with tmp.open('wb') as f:
            while True:
                b=resp.read(4*1024*1024)
                if not b: break
                f.write(b)
    if tmp.stat().st_size!=expected:
        got=tmp.stat().st_size; tmp.unlink(missing_ok=True); fail(f'size mismatch {fn}: {got}!={expected}')
    os.replace(tmp,dest); meta=archive_check(dest,inst)
    return dest,sha256(dest),meta,'downloaded'

def batch(name):
    parent,rows=parent_rows(); syms=set(BATCHES[name]); selected=[r for r in rows if r['instrument'].split('-')[0] in syms]
    if len(selected)!=32: fail(f'batch {name} parent rows={len(selected)}')
    expected=sum(int(r['bytes']) for r in selected)
    free=shutil.disk_usage(DATA_ROOT).free
    if free-expected<MIN_FREE: fail(f'insufficient disk reserve free={free} expected={expected}')
    out=[]
    for i,r in enumerate(selected,1):
        print(f'[{i}/32] {r["filename"]}',flush=True)
        p,h,m,mode=download(r)
        out.append({'filename':r['filename'],'instrument':r['instrument'],'date':r['date'],'expected_bytes':int(r['bytes']),'local_bytes':p.stat().st_size,'sha256':h,'member':m['member'],'member_uncompressed_bytes':m['member_uncompressed_bytes'],'mode':mode})
        print('PASS',mode,r['filename'],flush=True)
    rep={'stage':'SC001-E007R1-TRADE-ACQUISITION','batch':name.upper(),'status':TOKENS[name],'files':out,'verified_files':len(out),'total_bytes':sum(x['local_bytes'] for x in out),'asset_holdout_accessed':False,'august_confirmation_accessed':False,'strategy_signal_calculated':False,'strategy_pnl_calculated':False}
    atomic(REPORTS/f'batch_{name}.json',rep)
    print(TOKENS[name]); print('verified_files =',len(out)); print('strategy signal/PnL calculated = False'); return 0

def verify():
    parent,rows=parent_rows(); byfn={r['filename']:r for r in rows}; acquired={}
    for b in BATCHES:
        rp=REPORTS/f'batch_{b}.json'; x=load(rp)
        if x.get('status')!=TOKENS[b] or int(x.get('verified_files',0))!=32: fail(f'batch {b} report not exact PASS')
        for f in x.get('files') or []:
            if f['filename'] in acquired: fail('duplicate acquisition row')
            acquired[f['filename']]=f
    if len(acquired)!=128 or set(acquired)!=set(byfn): fail('acquired file identity mismatch')
    total=0
    for i,fn in enumerate(sorted(acquired),1):
        r=byfn[fn]; a=acquired[fn]; inst=r['instrument']; p=ARCH/inst.split('-')[0]/fn
        if not p.exists() or p.stat().st_size!=int(r['bytes']): fail(f'local identity fail {fn}')
        h=sha256(p)
        if h!=a['sha256']: fail(f'sha mismatch {fn}')
        archive_check(p,inst); total+=p.stat().st_size
        print(f'PASS [{i}/128] {fn}',flush=True)
    expected=int(parent['expected_total_bytes'])
    if total!=expected: fail(f'aggregate bytes mismatch {total}!={expected}')
    rep={'stage':'SC001-E007R1-TRADE-ACQUISITION-VERIFY','status':VERIFY,'verified_files':128,'verified_total_bytes':total,'expected_total_bytes':expected,'asset_holdout_accessed':False,'august_confirmation_accessed':False,'strategy_signal_calculated':False,'strategy_pnl_calculated':False}
    atomic(ROOT/'sc001_e007r1_trade_acquisition_verify_report.json',rep)
    print(VERIFY); print('verified_files = 128'); print('verified_total_bytes =',total); print('asset holdout accessed = False'); print('August Confirmation accessed = False'); print('strategy signal/PnL calculated = False'); return 0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['batch-a','batch-b','batch-c','batch-d','verify']); a=ap.parse_args()
    if a.mode=='verify': return verify()
    return batch(a.mode[-1])

if __name__=='__main__': raise SystemExit(main())
