from __future__ import annotations

import csv, io, json, math, os, subprocess, time, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

STAGE="SC001-C12-D1-SPOT-TRADE-SEMANTICS-V0.1"
PASS="C12_D1_SPOT_TRADE_SEMANTICS_PASS"
REVIEW="C12_D1_SPOT_TRADE_SEMANTICS_REVIEW"

INST="USDC-USDT"; D="2025-01-15"; D1="2025-01-16"
F0=f"{INST}-trades-{D}.zip"; F1=f"{INST}-trades-{D1}.zip"
DAY0=1736899200000*1000; DAY1=1736985600000*1000
OKX_DOMAINS=("https://www.okx.com","https://us.okx.com"); STATIC="static.okx.com"
HEADER=["instrument_name","trade_id","side","price","size","created_time"]
TIMEOUT=120; RETRIES=3; MAX_JSON=4_000_000; MAX_FILE=100*1024*1024; CHUNK=1024*1024

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-c12-d1-spot-trade-semantics-protocol-v0.1.md"
REGISTRY=ROOT/"docs/research/sc001-contamination-registry-v0.15.json"
FREEZE=ROOT/"docs/research/sc001-c12-d1-implementation-freeze-v0.1.json"
DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
D0=DATA_ROOT/"SC001_C12_D0_SOURCE_PARITY"/"sc001_c12_d0_source_parity_report_v0_1.json"
OUT_DIR=DATA_ROOT/"SC001_C12_D1_SPOT_SEMANTICS"; ARCH=OUT_DIR/"archives"
OUT=OUT_DIR/"sc001_c12_d1_spot_trade_semantics_report_v0_1.json"

def fail(m): raise RuntimeError(m)
def load_json(p): return json.loads(p.read_text(encoding="utf-8"))
def atomic_json(p,o):
    p.parent.mkdir(parents=True,exist_ok=True); t=Path(str(p)+".tmp")
    with t.open("w",encoding="utf-8") as f: json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)
def git_blob(p): return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()
def require():
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_C12_D1_RUN": fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()): fail("runner identity mismatch")
    if fr.get("protocol_git_blob_sha")!=git_blob(PROTOCOL): fail("protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha")!=git_blob(REGISTRY): fail("registry identity mismatch")
    reg=load_json(REGISTRY); row=reg.get("c12_engineering_source_semantics") or {}
    if row.get("authorized_bodies")!=[F0,F1]: fail("authorized body mismatch")
    d0=load_json(D0)
    if d0.get("status")!="C12_D0_SOURCE_PARITY_PREFLIGHT_PASS": fail("D0 not PASS")
    return d0
def walk(n):
    if isinstance(n,dict):
        yield n
        for v in n.values(): yield from walk(v)
    elif isinstance(n,list):
        for v in n: yield from walk(v)
def trusted(u,b):
    p=urllib.parse.urlparse(u); return p.scheme=="https" and (p.hostname or "").lower()==STATIC and Path(p.path).name==b
def date_ms(s):
    d=datetime.strptime(s,"%Y-%m-%d").replace(tzinfo=timezone.utc); b=int(d.timestamp()*1000); return b,b+86_400_000
def resolve(date,basename):
    b,e=date_ms(date)
    payload={"module":"1","instType":"SPOT","instQueryParam":{"instIdList":[INST]},"dateQuery":{"dateAggrType":"daily","begin":str(b),"end":str(e-1)}}
    body=json.dumps(payload,separators=(",",":")).encode(); last=None
    for dom in OKX_DOMAINS:
        try:
            req=urllib.request.Request(dom+"/priapi/v5/broker/public/trade-data/download-link?t="+str(int(time.time()*1000)),data=body,method="POST",headers={"User-Agent":"BotMarketplace-SC001-C12-D1/0.1","Accept":"application/json,*/*","Content-Type":"application/json","Referer":"https://www.okx.com/historical-data"})
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp: raw=resp.read(MAX_JSON+1)
            if len(raw)>MAX_JSON: fail("metadata cap")
            obj=json.loads(raw.decode()); 
            if str(obj.get("code"))!="0": fail("metadata code")
            found=[]
            for n in walk(obj.get("data")):
                if isinstance(n,dict):
                    fn=n.get("filename") or n.get("fileName"); u=n.get("url")
                    if fn==basename and isinstance(u,str) and trusted(u,basename) and u not in found: found.append(u)
            if len(found)==1: return found[0]
            if len(found)>1: fail("multiple exact URLs")
            last=RuntimeError("exact archive not found")
        except Exception as exc: last=exc
    raise RuntimeError(f"resolve failed {basename}: {last}")
def head(u,b):
    req=urllib.request.Request(u,method="HEAD",headers={"User-Agent":"BotMarketplace-SC001-C12-D1/0.1","Referer":"https://www.okx.com/historical-data"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp: final=resp.geturl(); cl=resp.headers.get("Content-Length")
    if not trusted(final,b) or not cl or not cl.isdigit() or int(cl)<=0: fail(f"HEAD mismatch {b}")
    return int(cl)
def download(u,b,size):
    if size>MAX_FILE: fail("file cap")
    ARCH.mkdir(parents=True,exist_ok=True); p=ARCH/b
    if p.exists() and p.stat().st_size==size: return p,True
    tmp=Path(str(p)+".part"); tmp.unlink(missing_ok=True)
    req=urllib.request.Request(u,headers={"User-Agent":"BotMarketplace-SC001-C12-D1/0.1","Referer":"https://www.okx.com/historical-data"})
    got=0
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp,tmp.open("wb") as f:
        if not trusted(resp.geturl(),b): fail("GET identity mismatch")
        while True:
            c=resp.read(CHUNK)
            if not c: break
            got+=len(c)
            if got>size: fail("download overflow")
            f.write(c)
    if got!=size: fail(f"size mismatch {got}!={size}")
    os.replace(tmp,p); return p,False
def norm_ts(x):
    v=int(str(x).strip()); a=abs(v)
    if a>=10**17:return v//1000,"ns"
    if a>=10**14:return v,"us"
    if a>=10**11:return v*1000,"ms"
    if a>=10**9:return v*1_000_000,"s"
    fail("timestamp scale")
def scan(p,b):
    out={"filename":b,"rows":0,"invalid":0,"reversals":0,"id_nonmono":0,"scales":set(),"first_ts":None,"last_ts":None,"target_rows":[]}
    with zipfile.ZipFile(p) as z:
        bad=z.testzip()
        if bad is not None: fail(f"CRC {bad}")
        mem=[x for x in z.infolist() if not x.is_dir()]
        if len(mem)!=1: fail("member count")
        with z.open(mem[0]) as raw:
            r=csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline=""))
            if next(r,None)!=HEADER: fail(f"header mismatch {b}")
            pts=pid=None
            for row in r:
                if not row: continue
                try:
                    if len(row)!=6 or row[0]!=INST or row[2] not in {"buy","sell"}: raise ValueError()
                    tid=int(row[1]); price=float(row[3]); size=float(row[4]); ts,scale=norm_ts(row[5])
                    if not(math.isfinite(price) and price>0 and math.isfinite(size) and size>0): raise ValueError()
                except Exception:
                    out["invalid"]+=1; continue
                out["rows"]+=1; out["scales"].add(scale)
                if out["first_ts"] is None: out["first_ts"]=ts
                out["last_ts"]=ts
                if pts is not None and ts<pts: out["reversals"]+=1
                if pid is not None and tid<=pid: out["id_nonmono"]+=1
                pts,pid=ts,tid
                if DAY0<=ts<DAY1: out["target_rows"].append((ts,tid,row[2]))
    out["scales"]=sorted(out["scales"]); return out
def main():
    try:
        d0=require(); expected=int((d0.get("historical_archive") or {}).get("content_length",0))
        print("C12-D1 resolve D/D+1",flush=True)
        u0=resolve(D,F0); u1=resolve(D1,F1); s0=head(u0,F0); s1=head(u1,F1)
        if s0!=expected: fail("D size changed from D0")
        p0,r0=download(u0,F0,s0); p1,r1=download(u1,F1,s1)
        print("C12-D1 parse D",flush=True); a=scan(p0,F0)
        print("C12-D1 parse D+1",flush=True); b=scan(p1,F1)
        for src in (a,b):
            if src["invalid"]!=0 or src["reversals"]!=0 or src["id_nonmono"]!=0 or len(src["scales"])!=1: fail(f"source integrity failed {src['filename']}")
        rows=a["target_rows"]+b["target_rows"]; rows.sort(key=lambda x:(x[0],x[1]))
        if not rows: fail("no target UTC rows")
        if not a["target_rows"] or not b["target_rows"]: fail("both D and D+1 must contribute")
        rev=sum(1 for x,y in zip(rows,rows[1:]) if y[0]<x[0]); ids=sum(1 for x,y in zip(rows,rows[1:]) if y[1]<=x[1])
        sides={x[2] for x in rows}
        if rev or ids or sides!={"buy","sell"}: fail(f"target integrity rev={rev} id={ids} sides={sides}")
        rep={"stage":STAGE,"version":"0.1","status":PASS,"target_utc_date":D,"archives":[{"filename":F0,"bytes":s0,"reused":r0,"source_rows":a["rows"],"first_ts_us":a["first_ts"],"last_ts_us":a["last_ts"]},{"filename":F1,"bytes":s1,"reused":r1,"source_rows":b["rows"],"first_ts_us":b["first_ts"],"last_ts_us":b["last_ts"]}],"target_utc_rows":len(rows),"d_contribution":len(a["target_rows"]),"d1_contribution":len(b["target_rows"]),"peg_deviation_calculated":False,"parity_threshold_selected":False,"reversion_outcome_calculated":False,"strategy_signal_calculated":False,"pnl_calculated":False,"promotional_alpha_accessed":False}
        atomic_json(OUT,rep)
        print(PASS); print("target_utc_rows =",len(rows)); print("D/D+1 contribution =",len(a["target_rows"]),"/",len(b["target_rows"])); print("peg deviation/threshold/reversion/signal/PnL = False"); print("promotional alpha accessed = False"); print("report =",OUT)
        return 0
    except Exception as exc:
        print(REVIEW); print("error =",f"{type(exc).__name__}: {exc}"); return 2
if __name__=="__main__": raise SystemExit(main())
