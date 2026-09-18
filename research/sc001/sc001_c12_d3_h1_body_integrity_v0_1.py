from __future__ import annotations

import csv, hashlib, io, json, math, os, subprocess, time, urllib.error, urllib.parse, urllib.request, zipfile
from pathlib import Path

STAGE="SC001-C12-D3-H1-BODY-INTEGRITY-V0.1"
PASS="C12_D3_H1_BODY_INTEGRITY_PASS"
REVIEW="C12_D3_H1_BODY_INTEGRITY_REVIEW"

INST="USDC-USDT"
OKX_DOMAINS=("https://www.okx.com","https://us.okx.com"); STATIC="static.okx.com"
TIMEOUT=120; MAX_JSON=4_000_000; MIN_GAP=1.5; MAX_ATTEMPTS=8; BACKOFF_BASE=15; BACKOFF_MAX=240; CHUNK=1024*1024
HEADER=["instrument_name","trade_id","side","price","size","created_time"]

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-c12-d3-h1-body-integrity-protocol-v0.1.md"
REGISTRY=ROOT/"docs/research/sc001-contamination-registry-v0.17.json"
FREEZE=ROOT/"docs/research/sc001-c12-d3-implementation-freeze-v0.1.json"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
D2=DATA_ROOT/"SC001_C12_D2_V02_H1_METADATA"/"sc001_c12_d2_v02_h1_archive_metadata_report_v0_1.json"
OUT_DIR=DATA_ROOT/"SC001_C12_D3_H1_BODY_INTEGRITY"; ARCH=OUT_DIR/"archives"
OUT=OUT_DIR/"sc001_c12_d3_h1_body_integrity_report_v0_1.json"; CHECK=OUT_DIR/"sc001_c12_d3_checkpoint.json"
_last=0.0

def fail(m): raise RuntimeError(m)
def load_json(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): fail(f"JSON object expected: {p}")
    return x
def atomic_json(p,o):
    p.parent.mkdir(parents=True,exist_ok=True); t=Path(str(p)+".tmp")
    with t.open("w",encoding="utf-8") as f: json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)
def git_blob(p): return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()
def sha256_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(8*CHUNK),b""): h.update(c)
    return h.hexdigest()
def require():
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_C12_D3_RUN": fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()): fail("runner identity mismatch")
    if fr.get("protocol_git_blob_sha")!=git_blob(PROTOCOL): fail("protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha")!=git_blob(REGISTRY): fail("registry identity mismatch")
    if int(fr.get("archive_count",0))!=182: fail("archive count mismatch")
    for k in ("peg_deviation_authorized","parity_episode_authorized","reversion_outcome_authorized","strategy_signal_authorized","fill_model_authorized","pnl_authorized","promotional_alpha_authorized"):
        if fr.get(k) is not False: fail(f"firewall mismatch {k}")
    reg=load_json(REGISTRY); row=reg.get("c12_s0_h1_parity_calibration") or {}
    if row.get("historical_trade_body_access_authorized") is not True: fail("body access not authorized")
    d2=load_json(D2)
    if d2.get("status")!="C12_D2_V02_H1_ARCHIVE_METADATA_PASS" or int(d2.get("archive_count",0))!=182: fail("D2 parent mismatch")
    return d2
def walk(n):
    if isinstance(n,dict):
        yield n
        for v in n.values(): yield from walk(v)
    elif isinstance(n,list):
        for v in n: yield from walk(v)
def trusted(u,b):
    p=urllib.parse.urlparse(u); return p.scheme=="https" and (p.hostname or "").lower()==STATIC and Path(p.path).name==b
def pace():
    global _last
    w=MIN_GAP-(time.monotonic()-_last)
    if w>0: time.sleep(w)
    _last=time.monotonic()
def wait429(exc,attempt):
    ra=exc.headers.get("Retry-After") if exc.headers else None
    try:
        if ra and int(ra)>0: return min(max(int(ra),BACKOFF_BASE),BACKOFF_MAX)
    except Exception: pass
    return min(BACKOFF_BASE*(2**(attempt-1)),BACKOFF_MAX)
def open_retry(factory,label,read_cap=None):
    last=None
    for a in range(1,MAX_ATTEMPTS+1):
        try:
            pace()
            req=factory()
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                final=resp.geturl(); status=int(getattr(resp,"status",200)); raw=resp.read(read_cap+1) if read_cap is not None else None
            if read_cap is not None and len(raw)>read_cap: fail(f"{label} cap")
            return status,final,raw
        except urllib.error.HTTPError as exc:
            last=exc
            if exc.code==429:
                w=wait429(exc,a); print(f"RATE_LIMIT {label} attempt={a}/{MAX_ATTEMPTS} sleep={w}s",flush=True); time.sleep(w)
            else:
                if a<MAX_ATTEMPTS: time.sleep(min(5*a,30))
        except Exception as exc:
            last=exc
            if a<MAX_ATTEMPTS: time.sleep(min(5*a,30))
    raise RuntimeError(f"{label} failed after {MAX_ATTEMPTS}: {type(last).__name__}: {last}")
def date_ms(ds):
    from datetime import datetime,timezone
    d=datetime.strptime(ds,"%Y-%m-%d").replace(tzinfo=timezone.utc); b=int(d.timestamp()*1000); return b,b+86_400_000
def resolve(ds,bname):
    b,e=date_ms(ds); payload={"module":"1","instType":"SPOT","instQueryParam":{"instIdList":[INST]},"dateQuery":{"dateAggrType":"daily","begin":str(b),"end":str(e-1)}}; body=json.dumps(payload,separators=(",",":")).encode()
    last=None
    for dom in OKX_DOMAINS:
        def mk(dom=dom):
            return urllib.request.Request(dom+"/priapi/v5/broker/public/trade-data/download-link?t="+str(int(time.time()*1000)),data=body,method="POST",headers={"User-Agent":"BotMarketplace-SC001-C12-D3/0.1","Accept":"application/json,*/*","Content-Type":"application/json","Referer":"https://www.okx.com/historical-data"})
        try:
            st,final,raw=open_retry(mk,f"resolve {ds}",MAX_JSON)
            if st!=200: fail(f"metadata HTTP {st}")
            obj=json.loads(raw.decode()); 
            if str(obj.get("code"))!="0": fail("metadata code")
            found=[]
            for n in walk(obj.get("data")):
                if isinstance(n,dict):
                    fn=n.get("filename") or n.get("fileName"); u=n.get("url")
                    if fn==bname and isinstance(u,str) and trusted(u,bname) and u not in found: found.append(u)
            if len(found)==1:return found[0]
            if len(found)>1: fail("multiple exact URLs")
            last=RuntimeError("exact archive missing")
        except Exception as exc: last=exc
    raise RuntimeError(f"resolve failed {ds}: {last}")
def download(u,bname,size):
    ARCH.mkdir(parents=True,exist_ok=True); p=ARCH/bname
    if p.exists() and p.stat().st_size==size: return p,True
    tmp=Path(str(p)+".part"); tmp.unlink(missing_ok=True)
    def mk(): return urllib.request.Request(u,headers={"User-Agent":"BotMarketplace-SC001-C12-D3/0.1","Referer":"https://www.okx.com/historical-data"})
    last=None
    for a in range(1,MAX_ATTEMPTS+1):
        try:
            pace(); req=mk()
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp,tmp.open("wb") as f:
                if not trusted(resp.geturl(),bname): fail("GET identity mismatch")
                got=0
                while True:
                    c=resp.read(CHUNK)
                    if not c: break
                    got+=len(c)
                    if got>size: fail("download overflow")
                    f.write(c)
            if got!=size: fail(f"download size mismatch {got}!={size}")
            os.replace(tmp,p); return p,False
        except urllib.error.HTTPError as exc:
            last=exc
            if exc.code==429:
                w=wait429(exc,a); print(f"RATE_LIMIT GET {bname} sleep={w}s",flush=True); time.sleep(w)
            elif a<MAX_ATTEMPTS: time.sleep(min(5*a,30))
        except Exception as exc:
            last=exc
            if a<MAX_ATTEMPTS: time.sleep(min(5*a,30))
    raise RuntimeError(f"download failed {bname}: {last}")
def norm_ts(x):
    v=int(str(x).strip()); a=abs(v)
    if a>=10**17:return v//1000,"ns"
    if a>=10**14:return v,"us"
    if a>=10**11:return v*1000,"ms"
    if a>=10**9:return v*1_000_000,"s"
    fail("timestamp scale")
def validate(p,bname):
    rows=bad=rev=idbad=0; first=last=None; prev_ts=prev_id=None; scales=set()
    with zipfile.ZipFile(p) as z:
        x=z.testzip()
        if x is not None: fail(f"CRC {bname}:{x}")
        mem=[m for m in z.infolist() if not m.is_dir()]
        if len(mem)!=1: fail(f"member count {bname}")
        with z.open(mem[0]) as raw:
            r=csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline=""))
            if next(r,None)!=HEADER: fail(f"header {bname}")
            for row in r:
                if not row: continue
                try:
                    if len(row)!=6 or row[0]!=INST or row[2] not in {"buy","sell"}: raise ValueError()
                    tid=int(row[1]); pr=float(row[3]); sz=float(row[4]); ts,sc=norm_ts(row[5])
                    if not(math.isfinite(pr) and pr>0 and math.isfinite(sz) and sz>0): raise ValueError()
                except Exception:
                    bad+=1; continue
                rows+=1; scales.add(sc)
                if first is None:first=ts
                last=ts
                if prev_ts is not None and ts<prev_ts: rev+=1
                if prev_id is not None and tid<=prev_id: idbad+=1
                prev_ts,prev_id=ts,tid
    if rows<=0 or bad or rev or idbad or len(scales)!=1: fail(f"integrity {bname} rows={rows} bad={bad} rev={rev} id={idbad} scales={scales}")
    return {"rows":rows,"first_ts_us":first,"last_ts_us":last,"timestamp_scale":next(iter(scales))}
def load_check():
    if not CHECK.exists(): return {}
    x=load_json(CHECK)
    if x.get("stage")!=STAGE: fail("checkpoint stage")
    out={}
    for r in x.get("verified") or []:
        p=ARCH/r["filename"]
        if not p.exists() or p.stat().st_size!=r["bytes"] or sha256_file(p)!=r["sha256"]: fail(f"checkpoint local identity mismatch {r['filename']}")
        out[r["date"]]=r
    return out
def save_check(v,ordered_dates):
    atomic_json(CHECK,{"stage":STAGE,"version":"0.1","verified":[v[d] for d in ordered_dates if d in v]})
def main():
    try:
        d2=require(); OUT_DIR.mkdir(parents=True,exist_ok=True)
        meta={r["date"]:r for r in d2["archives"]}; dates=[r["date"] for r in d2["archives"]]
        v=load_check(); print(f"C12-D3 resume={len(v)}/182",flush=True)
        for i,ds in enumerate(dates,1):
            if ds in v:
                if i%20==0 or i==182: print(f"C12-D3 [{i}/182] {ds} CHECKPOINT",flush=True)
                continue
            m=meta[ds]; b=m["filename"]; size=int(m["content_length"])
            print(f"C12-D3 [{i}/182] {ds}",flush=True)
            u=resolve(ds,b); p,reused=download(u,b,size); integ=validate(p,b); sha=sha256_file(p)
            v[ds]={"date":ds,"filename":b,"bytes":size,"sha256":sha,"reused":reused,**integ}; save_check(v,dates)
            print(f"PASS {ds} rows={integ['rows']} checkpoint={len(v)}/182",flush=True)
        if len(v)!=182: fail(f"verified count {len(v)}")
        rep={"stage":STAGE,"version":"0.1","status":PASS,"archive_count":182,"archives":[v[d] for d in dates],"peg_deviation_calculated":False,"parity_episode_calculated":False,"reversion_outcome_calculated":False,"strategy_signal_calculated":False,"fill_model_calculated":False,"pnl_calculated":False,"promotional_alpha_accessed":False}
        atomic_json(OUT,rep)
        print(PASS); print("archives_passed =",len(v),"/ 182"); print("peg deviation/episode/reversion/signal/fill/PnL = False"); print("promotional alpha accessed = False"); print("report =",OUT); return 0
    except Exception as exc:
        print(REVIEW); print("error =",f"{type(exc).__name__}: {exc}"); print("checkpoint =",CHECK); return 2
if __name__=="__main__": raise SystemExit(main())
