from __future__ import annotations

import csv, io, json, math, os, subprocess, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
import statistics

STAGE="SC001-C11-S1-FIRST-IMPULSE-CONTINUATION-V0.1"
SURVIVE="C11_S1_FIRST_IMPULSE_CONTINUATION_SURVIVE"
REJECT="C11_S1_REJECT_FIRST_IMPULSE_CONTINUATION"
DEFER="C11_S1_DEFER_SAMPLE"

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-c11-s1-first-impulse-continuation-sentinel-v0.1.md"
REGISTRY=ROOT/"docs/research/sc001-contamination-registry-v0.17.json"
FREEZE=ROOT/"docs/research/sc001-c11-s1-implementation-freeze-v0.1.json"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
D1=DATA_ROOT/"SC001_C11_D1_H1_EVENT_METADATA"/"sc001_c11_d1_h1_event_metadata_report_v0_1.json"
S0=DATA_ROOT/"SC001_C11_S0_EVENT_HEADROOM"/"c11_s0_event_move_headroom_report_v0_1.json"
ARCH=DATA_ROOT/"SC001_C11_S0_EVENT_HEADROOM"/"archives"
OUT_DIR=DATA_ROOT/"SC001_C11_S1_FIRST_IMPULSE"
OUT=OUT_DIR/"c11_s1_first_impulse_continuation_report_v0_1.json"

HEADER=["instrument_name","trade_id","side","price","size","created_time"]
INST="BTC-USDT-SWAP"
FEE_BURDEN=20.0

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
    if fr.get("status")!="FROZEN_BEFORE_FIRST_C11_S1_OUTCOME": fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()): fail("runner identity mismatch")
    if fr.get("protocol_git_blob_sha")!=git_blob(PROTOCOL): fail("protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha")!=git_blob(REGISTRY): fail("registry identity mismatch")
    if float(fr.get("structural_burden_bps",-1))!=FEE_BURDEN: fail("burden mismatch")
    for k in ("macro_release_value_authorized","macro_surprise_authorized","execution_fill_model_authorized","pnl_authorized","promotional_alpha_authorized"):
        if fr.get(k) is not False: fail(f"firewall mismatch {k}")
    reg=load_json(REGISTRY)
    row=reg.get("c11_s1_directional_calibration") or {}
    if row.get("first_impulse_direction_authorized") is not True or row.get("continuation_outcome_authorized") is not True:
        fail("C11 S1 outcome not authorized")
    d1=load_json(D1); s0=load_json(S0)
    if d1.get("status")!="C11_D1_H1_EVENT_ARCHIVE_METADATA_PASS": fail("D1 not PASS")
    if s0.get("status")!="C11_S0_EVENT_MOVE_HEADROOM_SURVIVE": fail("S0 not SURVIVE")
    return d1

def norm_ts(x):
    v=int(str(x).strip()); a=abs(v)
    if a>=10**17:return v//1000
    if a>=10**14:return v
    if a>=10**11:return v*1000
    if a>=10**9:return v*1_000_000
    fail("timestamp scale")

def anchors(path,event_us):
    pre=p1=p60=None; tpre=t1=t60=None; last_ts=last_id=None
    target1=event_us+1_000_000; target60=event_us+60_000_000
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
                if ts<event_us: pre=price; tpre=ts
                if ts<=target1: p1=price; t1=ts
                if ts<=target60: p60=price; t60=ts
                else: break
    if None in (pre,p1,p60,tpre,t1,t60): return None
    if event_us-tpre>1_000_000 or target1-t1>1_000_000 or target60-t60>1_000_000: return None
    impulse=10000.0*math.log(p1/pre)
    if impulse==0: return None
    signed=(1.0 if impulse>0 else -1.0)*10000.0*math.log(p60/p1)
    return {"pre_price":pre,"price_1s":p1,"price_60s":p60,"first_impulse_bps":impulse,"signed_continuation_bps":signed}

def nr(vals,q):
    s=sorted(vals); i=max(0,min(len(s)-1,math.ceil(q*len(s))-1)); return s[i]

def main():
    try:
        d1=require()
        rows=[]
        for i,e in enumerate(d1["events"],1):
            b=e["archive"]["filename"]; expected=int(e["archive"]["content_length"]); p=ARCH/b
            if not p.exists() or p.stat().st_size!=expected: fail(f"local archive missing/size mismatch {b}")
            event_us=int(datetime.fromisoformat(e["frozen_utc"].replace("Z","+00:00")).timestamp()*1_000_000)
            a=anchors(p,event_us)
            rows.append({"kind":e["kind"],"date":e["date"],"event_utc":e["frozen_utc"],"anchor":a})
            print(f"C11-S1 [{i}/12] {e['kind']} {e['date']} valid={a is not None}",flush=True)
        valid=[x for x in rows if x["anchor"] is not None]
        if len(valid)!=12:
            status=DEFER; vals=[]; gates={}
        else:
            vals=[x["anchor"]["signed_continuation_bps"] for x in valid]
            pos=sum(1 for v in vals if v>0)
            ge20=sum(1 for v in vals if v>=20)
            med=statistics.median(vals); p75=nr(vals,0.75)
            gates={"positive_events_gte8":pos>=8,"events_signed_gte20bps_gte6":ge20>=6,"median_signed_gte20bps":med>=20,"p75_signed_gte30bps":p75>=30}
            status=SURVIVE if all(gates.values()) else REJECT
        if vals:
            pos=sum(1 for v in vals if v>0); ge20=sum(1 for v in vals if v>=20); med=statistics.median(vals); p75=nr(vals,0.75)
        else:
            pos=ge20=0; med=p75=None
        rep={"stage":STAGE,"version":"0.1","status":status,"events":rows,"valid_event_count":len(valid),"positive_signed_continuation_events":pos,"events_signed_continuation_gte20bps":ge20,"median_signed_continuation_bps":med,"p75_signed_continuation_bps":p75,"continuation_gates":gates,"macro_release_value_accessed":False,"macro_surprise_calculated":False,"execution_fill_model_calculated":False,"pnl_calculated":False,"promotional_alpha_accessed":False}
        atomic_json(OUT,rep)
        print(status); print("valid_event_count =",len(valid),"/ 12"); print("positive_signed_continuation_events =",pos); print("events_signed_continuation_gte20bps =",ge20); print("median_signed_continuation_bps =",med); print("p75_signed_continuation_bps =",p75); print("failed_continuation_gates =",[k for k,v in gates.items() if not v]); print("fill/PnL/promotional alpha = False"); print("report =",OUT)
        return 0
    except Exception as exc:
        print("C11_S1_IMPLEMENTATION_FAIL"); print("error =",f"{type(exc).__name__}: {exc}"); return 2

if __name__=="__main__": raise SystemExit(main())
