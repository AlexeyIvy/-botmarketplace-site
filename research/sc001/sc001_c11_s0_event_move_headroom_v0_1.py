from __future__ import annotations

import csv
import io
import json
import math
import os
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C11-S0-EVENT-MOVE-HEADROOM-V0.1"
SURVIVE = "C11_S0_EVENT_MOVE_HEADROOM_SURVIVE"
REJECT = "C11_S0_REJECT_EVENT_MOVE_HEADROOM"
DEFER = "C11_S0_DEFER_SAMPLE"

FEE_BURDEN_BPS = 20.0
EVENTS_GTE20_MIN = 6
MEDIAN_MIN = 20.0
P75_MIN = 30.0
MAX_MIN = 50.0

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
OKX_STATIC = "static.okx.com"
OKX_FAMILY = "BTC-USDT"
INST = "BTC-USDT-SWAP"
HEADER = ["instrument_name","trade_id","side","price","size","created_time"]

TIMEOUT = 120
RETRIES = 3
MAX_JSON = 4_000_000
MAX_FILE = 100 * 1024 * 1024
CHUNK = 1024 * 1024

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c11-s0-event-move-headroom-sentinel-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.16.json"
FREEZE = ROOT / "docs/research/sc001-c11-s0-implementation-freeze-v0.1.json"

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home()/"sc001_data"))).expanduser().resolve()
D1 = DATA_ROOT / "SC001_C11_D1_H1_EVENT_METADATA" / "sc001_c11_d1_h1_event_metadata_report_v0_1.json"
OUT_DIR = DATA_ROOT / "SC001_C11_S0_EVENT_HEADROOM"
ARCH = OUT_DIR / "archives"
OUT = OUT_DIR / "c11_s0_event_move_headroom_report_v0_1.json"

def fail(m): raise RuntimeError(m)
def load_json(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): fail(f"JSON object expected: {p}")
    return x
def atomic_json(p,o):
    p.parent.mkdir(parents=True,exist_ok=True); t=Path(str(p)+".tmp")
    with t.open("w",encoding="utf-8") as f:
        json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)
def git_blob(p): return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()
def require():
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_FIRST_C11_S0_OUTCOME": fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()): fail("runner identity mismatch")
    if fr.get("protocol_git_blob_sha")!=git_blob(PROTOCOL): fail("protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha")!=git_blob(REGISTRY): fail("registry identity mismatch")
    if int(fr.get("event_count",0))!=12: fail("event count mismatch")
    if float(fr.get("structural_burden_bps",-1))!=FEE_BURDEN_BPS: fail("burden mismatch")
    for k in ("macro_release_value_authorized","macro_surprise_authorized","first_impulse_direction_authorized","continuation_outcome_authorized","strategy_signal_authorized","execution_fill_model_authorized","pnl_authorized","promotional_alpha_authorized"):
        if fr.get(k) is not False: fail(f"firewall mismatch: {k}")
    reg=load_json(REGISTRY); row=reg.get("c11_h1_price_headroom_calibration") or {}
    if row.get("historical_trade_body_access_authorized") is not True: fail("C11 body access not authorized")
    d1=load_json(D1)
    if d1.get("status")!="C11_D1_H1_EVENT_ARCHIVE_METADATA_PASS" or int(d1.get("events_verified",0))!=12: fail("D1 parent mismatch")
    return d1

def day_ms(date):
    d=datetime.strptime(date,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    b=int(d.timestamp()*1000); return b,b+86_400_000
def walk(n):
    if isinstance(n,dict):
        yield n
        for v in n.values(): yield from walk(v)
    elif isinstance(n,list):
        for v in n: yield from walk(v)
def trusted(u,b):
    p=urllib.parse.urlparse(u)
    return p.scheme=="https" and (p.hostname or "").lower()==OKX_STATIC and Path(p.path).name==b
def resolve(date,basename):
    b,e=day_ms(date)
    payload={"module":"1","instType":"SWAP","instQueryParam":{"instFamilyList":[OKX_FAMILY]},"dateQuery":{"dateAggrType":"daily","begin":str(b),"end":str(e-1)}}
    body=json.dumps(payload,separators=(",",":")).encode()
    last=None
    for dom in OKX_DOMAINS:
        try:
            req=urllib.request.Request(dom+"/priapi/v5/broker/public/trade-data/download-link?t="+str(int(time.time()*1000)),data=body,method="POST",headers={"User-Agent":"BotMarketplace-SC001-C11-S0/0.1","Accept":"application/json,*/*","Content-Type":"application/json","Referer":"https://www.okx.com/historical-data"})
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp: raw=resp.read(MAX_JSON+1)
            if len(raw)>MAX_JSON: fail("metadata cap")
            obj=json.loads(raw.decode())
            if str(obj.get("code"))!="0": fail("metadata code")
            found=[]
            for n in walk(obj.get("data")):
                if isinstance(n,dict):
                    fn=n.get("filename") or n.get("fileName"); u=n.get("url")
                    if fn==basename and isinstance(u,str) and trusted(u,basename) and u not in found: found.append(u)
            if len(found)==1: return found[0]
            if len(found)>1: fail("multiple exact URLs")
            last=RuntimeError("exact archive missing")
        except Exception as exc: last=exc
    raise RuntimeError(f"resolve failed {date}: {last}")
def head(u,b):
    req=urllib.request.Request(u,method="HEAD",headers={"User-Agent":"BotMarketplace-SC001-C11-S0/0.1","Referer":"https://www.okx.com/historical-data"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp: final=resp.geturl(); cl=resp.headers.get("Content-Length")
    if not trusted(final,b) or not cl or not cl.isdigit() or int(cl)<=0: fail(f"HEAD mismatch {b}")
    return int(cl)
def download(u,b,size):
    if size>MAX_FILE: fail(f"file cap {b}")
    ARCH.mkdir(parents=True,exist_ok=True); p=ARCH/b
    if p.exists() and p.stat().st_size==size: return p,True
    tmp=Path(str(p)+".part"); tmp.unlink(missing_ok=True)
    req=urllib.request.Request(u,headers={"User-Agent":"BotMarketplace-SC001-C11-S0/0.1","Referer":"https://www.okx.com/historical-data"})
    got=0
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp,tmp.open("wb") as f:
        if not trusted(resp.geturl(),b): fail(f"GET identity {b}")
        while True:
            c=resp.read(CHUNK)
            if not c: break
            got+=len(c)
            if got>size: fail(f"download overflow {b}")
            f.write(c)
    if got!=size: fail(f"size mismatch {b}: {got}!={size}")
    os.replace(tmp,p); return p,False
def norm_ts(x):
    v=int(str(x).strip()); a=abs(v)
    if a>=10**17:return v//1000
    if a>=10**14:return v
    if a>=10**11:return v*1000
    if a>=10**9:return v*1_000_000
    fail("timestamp scale")
def event_anchor(path,event_us):
    pre=None; fut=None; pre_ts=None; fut_ts=None; last_ts=None; last_id=None
    target=event_us+60_000_000
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad is not None: fail(f"CRC {bad}")
        mem=[x for x in z.infolist() if not x.is_dir()]
        if len(mem)!=1: fail("member count")
        with z.open(mem[0]) as raw:
            r=csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline=""))
            if next(r,None)!=HEADER: fail("header mismatch")
            for row in r:
                if not row: continue
                if len(row)!=6 or row[0]!=INST or row[2] not in {"buy","sell"}: fail("row semantics")
                tid=int(row[1]); price=float(row[3]); size=float(row[4]); ts=norm_ts(row[5])
                if not(math.isfinite(price) and price>0 and math.isfinite(size) and size>0): fail("price/size")
                if last_ts is not None and ts<last_ts: fail("timestamp reversal")
                if last_id is not None and tid<=last_id: fail("trade id nonmono")
                last_ts,last_id=ts,tid
                if ts<event_us:
                    pre=(price); pre_ts=ts
                if ts<=target:
                    fut=(price); fut_ts=ts
                else:
                    break
    if pre is None or fut is None: return None
    if event_us-pre_ts>1_000_000: return None
    if target-fut_ts>1_000_000: return None
    return {"pre_price":pre,"pre_ts_us":pre_ts,"price_60s":fut,"price_60s_ts_us":fut_ts,"abs_move_60s_bps":10000.0*abs(math.log(fut/pre))}
def nr(values,q):
    vals=sorted(values); idx=max(0,min(len(vals)-1,math.ceil(q*len(vals))-1)); return vals[idx]
def main():
    try:
        d1=require()
        if OUT.exists():
            old=load_json(OUT)
            if old.get("status") in {SURVIVE,REJECT,DEFER}: fail(f"one-shot guard: {old.get('status')}")
        rows=[]
        for i,e in enumerate(d1["events"],1):
            kind=e["kind"]; date=e["date"]; utc=e["frozen_utc"]; meta=e["archive"]; b=meta["filename"]; expected=int(meta["content_length"])
            print(f"C11-S0 [{i}/12] {kind} {date}",flush=True)
            u=resolve(date,b); s=head(u,b)
            if s!=expected: fail(f"HEAD size changed {date}: {s}!={expected}")
            p,reused=download(u,b,s)
            event_us=int(datetime.fromisoformat(utc.replace("Z","+00:00")).timestamp()*1_000_000)
            a=event_anchor(p,event_us)
            rows.append({"kind":kind,"date":date,"event_utc":utc,"archive":b,"bytes":s,"reused":reused,"anchor":a})
        valid=[x for x in rows if x["anchor"] is not None]
        sample_ok=len(valid)==12
        if not sample_ok:
            status=DEFER; moves=[]
        else:
            moves=[x["anchor"]["abs_move_60s_bps"] for x in valid]
            med=statistics.median(moves); p75=nr(moves,0.75); mx=max(moves); ge20=sum(1 for x in moves if x>=20)
            gates={"events_gte20bps_gte6":ge20>=EVENTS_GTE20_MIN,"median_gte20bps":med>=MEDIAN_MIN,"p75_gte30bps":p75>=P75_MIN,"max_gte50bps":mx>=MAX_MIN}
            status=SURVIVE if all(gates.values()) else REJECT
        if moves:
            med=statistics.median(moves); p75=nr(moves,0.75); mx=max(moves); ge20=sum(1 for x in moves if x>=20)
            gates={"events_gte20bps_gte6":ge20>=EVENTS_GTE20_MIN,"median_gte20bps":med>=MEDIAN_MIN,"p75_gte30bps":p75>=P75_MIN,"max_gte50bps":mx>=MAX_MIN}
        else:
            med=p75=mx=None; ge20=0; gates={}
        rep={"stage":STAGE,"version":"0.1","status":status,"events":rows,"valid_event_count":len(valid),"events_abs_move_gte20bps":ge20,"median_abs_move_60s_bps":med,"p75_abs_move_60s_bps":p75,"max_abs_move_60s_bps":mx,"headroom_gates":gates,"macro_release_value_accessed":False,"macro_surprise_calculated":False,"first_impulse_direction_calculated":False,"continuation_outcome_calculated":False,"strategy_signal_calculated":False,"execution_fill_model_calculated":False,"pnl_calculated":False,"promotional_alpha_accessed":False}
        atomic_json(OUT,rep)
        print(status); print("valid_event_count =",len(valid),"/ 12"); print("events_abs_move_gte20bps =",ge20); print("median_abs_move_60s_bps =",med); print("p75_abs_move_60s_bps =",p75); print("max_abs_move_60s_bps =",mx); print("failed_headroom_gates =",[k for k,v in gates.items() if not v]); print("macro surprise/direction/continuation/fill/PnL = False"); print("promotional alpha accessed = False"); print("report =",OUT)
        return 0
    except Exception as exc:
        print("C11_S0_IMPLEMENTATION_FAIL"); print("error =",f"{type(exc).__name__}: {exc}"); return 2
if __name__=="__main__":
    import statistics
    raise SystemExit(main())
