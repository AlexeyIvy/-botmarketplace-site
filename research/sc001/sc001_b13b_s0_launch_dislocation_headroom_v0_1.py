from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import os
import statistics
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

STAGE="SC001-B13B-S0-LAUNCH-DISLOCATION-HEADROOM-V0.1"
SURVIVE="B13B_S0_LAUNCH_DISLOCATION_HEADROOM_SURVIVE"
REJECT="B13B_S0_REJECT_LAUNCH_DISLOCATION_HEADROOM"
DEFER="B13B_S0_DEFER_SAMPLE"

STRUCTURAL_BURDEN_BPS=40.0
HEADROOM_BPS=50.0
SEARCH_BUCKETS=5
MIN_COACTIVE_VALID=6
MIN_VALID_MONTHS=3
MIN_QUALIFYING=4
MIN_QUAL_MONTHS=3

CANONICAL_D0_SHA="82012a614a1f5652c483df87fb70f811f66b56e9035e41f8d146f7accd81e2f6"

EVENTS=(
    ("KITE","KITE-USDT-SWAP","2026-04-09T03:00:00+00:00","KITEUSDT","2026-04-09","KITE-USDT-SWAP-trades-2026-04-09.zip","KITEUSDT2026-04-09.csv.gz"),
    ("UB","UB-USDT-SWAP","2026-04-28T13:30:00+00:00","UBUSDT","2026-04-28","UB-USDT-SWAP-trades-2026-04-28.zip","UBUSDT2026-04-28.csv.gz"),
    ("MEGA","MEGA-USDT-SWAP","2026-04-30T12:00:00+00:00","MEGAUSDT","2026-04-30","MEGA-USDT-SWAP-trades-2026-04-30.zip","MEGAUSDT2026-04-30.csv.gz"),
    ("IRYS","IRYS-USDT-SWAP","2026-05-27T11:15:00+00:00","IRYSUSDT","2026-05-27","IRYS-USDT-SWAP-trades-2026-05-27.zip","IRYSUSDT2026-05-27.csv.gz"),
    ("BB","BB-USDT-SWAP","2026-06-01T09:00:00+00:00","BBUSDT","2026-06-01","BB-USDT-SWAP-trades-2026-06-01.zip","BBUSDT2026-06-01.csv.gz"),
    ("QNT","QNT-USDT-SWAP","2026-06-05T10:30:00+00:00","QNTUSDT","2026-06-05","QNT-USDT-SWAP-trades-2026-06-05.zip","QNTUSDT2026-06-05.csv.gz"),
    ("VVV","VVV-USDT-SWAP","2026-07-03T06:00:00+00:00","VVVUSDT","2026-07-03","VVV-USDT-SWAP-trades-2026-07-03.zip","VVVUSDT2026-07-03.csv.gz"),
)

OKX_DOMAINS=("https://www.okx.com","https://us.okx.com")
OKX_STATIC="static.okx.com"
BYBIT_PUBLIC="https://public.bybit.com"
TIMEOUT=120
RETRIES=3
MAX_JSON=4_000_000
MAX_FILE=300*1024*1024
MAX_TOTAL=2*1024*1024*1024
CHUNK=1024*1024

HEADER6=["instrument_name","trade_id","side","price","size","created_time"]
HEADER7=["instrument_name","trade_id","side","price","size","created_time","source"]
SOURCE_ALLOWED={"0","1"}

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-b13b-s0-launch-dislocation-headroom-sentinel-v0.1.md"
REGISTRY=ROOT/"docs/research/sc001-contamination-registry-v0.24.json"
EVENT_FREEZE=ROOT/"docs/research/sc001-b13b-exact-7-event-launch-set-freeze-v0.1.md"
FREEZE=ROOT/"docs/research/sc001-b13b-s0-implementation-freeze-v0.1.json"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
D0=DATA_ROOT/"SC001_B13B_D0_SOURCE_CENSUS"/"sc001_b13b_d0_launch_source_census_v0_1.json"
OUT_DIR=DATA_ROOT/"SC001_B13B_S0_LAUNCH_HEADROOM"
ARCH=OUT_DIR/"archives"
OUT=OUT_DIR/"sc001_b13b_s0_launch_dislocation_headroom_v0_1.json"

def fail(m): raise RuntimeError(m)

def load_json(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): fail(f"JSON object expected: {p}")
    return x

def atomic_json(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=Path(str(p)+".tmp")
    with t.open("w",encoding="utf-8") as f:
        json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)

def sha256_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(8*1024*1024),b""): h.update(c)
    return h.hexdigest()

def git_blob(p):
    return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()

def require():
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_B13B_S0_RUN": fail("freeze status mismatch")
    expected={
        "runner_git_blob_sha":git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha":git_blob(PROTOCOL),
        "contamination_registry_git_blob_sha":git_blob(REGISTRY),
        "event_freeze_git_blob_sha":git_blob(EVENT_FREEZE),
    }
    for k,v in expected.items():
        if fr.get(k)!=v: fail(f"freeze identity mismatch: {k}")
    if int(fr.get("event_count",0))!=7: fail("event count mismatch")
    if int(fr.get("search_buckets",0))!=SEARCH_BUCKETS: fail("search bucket mismatch")
    if float(fr.get("structural_burden_bps",-1))!=STRUCTURAL_BURDEN_BPS: fail("burden mismatch")
    if float(fr.get("headroom_threshold_bps",-1))!=HEADROOM_BPS: fail("headroom mismatch")

    reg=(load_json(REGISTRY).get("b13b_historical_launch_calibration") or {})
    for key in ("historical_trade_body_access_authorized","price_access_authorized","absolute_launch_basis_authorized"):
        if reg.get(key) is not True: fail(f"registry authorization mismatch: {key}")
    for key in ("convergence_authorized","relative_return_authorized","strategy_signal_authorized","execution_model_authorized","pnl_authorized","candidate_id_assignment_authorized","promotional_evidence_authorized"):
        if reg.get(key) is not False: fail(f"registry firewall mismatch: {key}")

    if not D0.exists(): fail(f"missing D0 report: {D0}")
    if sha256_file(D0)!=CANONICAL_D0_SHA: fail("D0 report SHA mismatch")
    d0=load_json(D0)
    if d0.get("status")!="B13B_D0_SOURCE_FEASIBILITY_PASS_SURVIVOR_CENSORED": fail("D0 status mismatch")
    return d0

def d0_event_map(d0):
    out={}
    for e in d0.get("events") or []:
        if e.get("dual_source_ready") is True:
            out[e.get("instId")]=e
    if len(out)!=7: fail(f"D0 dual-source-ready count mismatch: {len(out)}")
    for base,inst,list_utc,bybit,date,okx_file,bybit_file in EVENTS:
        e=out.get(inst)
        if not e: fail(f"D0 event missing: {inst}")
        checks={
            "base":base,
            "listTime_utc":list_utc,
            "bybit_symbol":bybit,
            "launch_date_utc":date,
            "okx_launch_day_archive_file":okx_file,
            "bybit_launch_day_archive_file":bybit_file,
        }
        for k,v in checks.items():
            if e.get(k)!=v: fail(f"D0 identity mismatch {inst} {k}: {e.get(k)!r}!={v!r}")
    return out

def walk(n):
    if isinstance(n,dict):
        yield n
        for v in n.values(): yield from walk(v)
    elif isinstance(n,list):
        for v in n: yield from walk(v)

def trusted_okx(u,b):
    p=urllib.parse.urlparse(u)
    return p.scheme=="https" and (p.hostname or "").lower()==OKX_STATIC and Path(p.path).name==b

def day_ms(ds):
    d=datetime.strptime(ds,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    b=int(d.timestamp()*1000); return b,b+86_400_000

def resolve_okx(base,inst,date,basename):
    b,e=day_ms(date)
    payload={"module":"1","instType":"SWAP","instQueryParam":{"instFamilyList":[f"{base}-USDT"]},"dateQuery":{"dateAggrType":"daily","begin":str(b),"end":str(e-1)}}
    body=json.dumps(payload,separators=(",",":")).encode()
    last=None
    for dom in OKX_DOMAINS:
        try:
            req=urllib.request.Request(dom+"/priapi/v5/broker/public/trade-data/download-link?t="+str(int(time.time()*1000)),data=body,method="POST",headers={"User-Agent":"BotMarketplace-SC001-B13B-S0/0.1","Accept":"application/json,*/*","Content-Type":"application/json","Referer":"https://www.okx.com/historical-data"})
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp: raw=resp.read(MAX_JSON+1)
            if len(raw)>MAX_JSON: fail("OKX metadata cap")
            obj=json.loads(raw.decode())
            if str(obj.get("code"))!="0": fail(f"OKX code mismatch {inst}")
            found=[]
            for n in walk(obj.get("data")):
                if not isinstance(n,dict): continue
                fn=n.get("filename") or n.get("fileName")
                u=n.get("url") or n.get("fileUrl") or n.get("downloadUrl")
                if fn==basename and isinstance(u,str) and trusted_okx(u,basename) and u not in found: found.append(u)
            if len(found)==1:return found[0]
            if len(found)>1:fail(f"multiple exact OKX URLs {inst}")
            last=RuntimeError("exact archive missing")
        except Exception as exc:last=exc
    raise RuntimeError(f"OKX resolve failed {inst}: {last}")

def head(u,host,basename):
    req=urllib.request.Request(u,method="HEAD",headers={"User-Agent":"BotMarketplace-SC001-B13B-S0/0.1"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
        final=resp.geturl(); cl=resp.headers.get("Content-Length"); status=int(getattr(resp,"status",200))
    p=urllib.parse.urlparse(final)
    if status!=200 or (p.hostname or "").lower()!=host or Path(p.path).name!=basename or not cl or not cl.isdigit() or int(cl)<=0:
        fail(f"HEAD identity/size mismatch {basename}")
    return int(cl)

def download(u,host,basename,expected):
    if expected<=0 or expected>MAX_FILE: fail(f"file cap/size {basename}: {expected}")
    ARCH.mkdir(parents=True,exist_ok=True)
    p=ARCH/basename
    if p.exists() and p.stat().st_size==expected:return p,True
    tmp=Path(str(p)+".part"); tmp.unlink(missing_ok=True)
    got=0
    req=urllib.request.Request(u,headers={"User-Agent":"BotMarketplace-SC001-B13B-S0/0.1","Referer":"https://www.okx.com/historical-data"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp,tmp.open("wb") as f:
        final=resp.geturl(); parsed=urllib.parse.urlparse(final)
        if (parsed.hostname or "").lower()!=host or Path(parsed.path).name!=basename: fail(f"GET identity mismatch {basename}")
        while True:
            c=resp.read(CHUNK)
            if not c:break
            got+=len(c)
            if got>expected:fail(f"download overflow {basename}")
            f.write(c)
        f.flush(); os.fsync(f.fileno())
    if got!=expected:fail(f"download size mismatch {basename}: {got}!={expected}")
    os.replace(tmp,p); return p,False

def norm_okx_ts_us(x):
    v=int(str(x).strip()); a=abs(v)
    if a>=10**17:return v//1000
    if a>=10**14:return v
    if a>=10**11:return v*1000
    if a>=10**9:return v*1_000_000
    fail("OKX timestamp scale")

def parse_okx(path,inst,basename,t_us):
    expected_member=basename[:-4]+".csv"
    last_by_sec={}; last_ts=None; last_id=None; schema=None; source0=source1=None
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad is not None:fail(f"OKX ZIP CRC {basename}: {bad}")
        members=[x for x in z.infolist() if not x.is_dir()]
        if len(members)!=1 or Path(members[0].filename).name!=expected_member:fail(f"OKX member mismatch {basename}")
        with z.open(members[0]) as raw:
            r=csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline=""))
            h=next(r,None)
            if h==HEADER6:schema="LEGACY_6"; width=6
            elif h==HEADER7:schema="SOURCE_7"; width=7; source0=source1=0
            else:fail(f"OKX header mismatch {basename}: {h}")
            for row in r:
                if not row:continue
                if len(row)!=width or row[0]!=inst or row[2] not in {"buy","sell"}:fail(f"OKX row semantics {basename}")
                if schema=="SOURCE_7":
                    if row[6] not in SOURCE_ALLOWED:fail(f"OKX source value {basename}: {row[6]!r}")
                    if row[6]=="0":source0+=1
                    else:source1+=1
                tid=int(row[1]); price=float(row[3]); size=float(row[4]); ts=norm_okx_ts_us(row[5])
                if not(math.isfinite(price) and price>0 and math.isfinite(size) and size>0):fail(f"OKX price/size {basename}")
                if last_ts is not None and ts<last_ts:fail(f"OKX timestamp reversal {basename}")
                if last_id is not None and tid<=last_id:fail(f"OKX trade id nonmono {basename}")
                last_ts,last_id=ts,tid
                if t_us<=ts<t_us+SEARCH_BUCKETS*1_000_000:
                    last_by_sec[ts//1_000_000]=(ts,price)
    return {"last_by_sec":last_by_sec,"schema":schema,"source_0_rows":source0,"source_1_rows":source1}

def parse_bybit(path,symbol,date,t_us):
    start_us=int(datetime.strptime(date,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1_000_000)
    end_us=start_us+86_400_000_000
    last_by_sec={}; last_ts=None; invalid=0; outday=0
    with gzip.open(path,"rt",encoding="utf-8",errors="strict",newline="") as f:
        r=csv.reader(f); h=next(r,None)
        if not h or len(h)<5:fail(f"Bybit header missing {symbol}")
        low=[str(x).strip().lower() for x in h[:5]]
        if low!=["timestamp","symbol","side","size","price"]:fail(f"Bybit header mismatch {symbol}: {h[:5]}")
        for row in r:
            if not row:continue
            if len(row)<5:invalid+=1; continue
            try:
                ts=int(round(float(row[0])*1_000_000))
                if row[1].strip()!=symbol or row[2].strip() not in {"Buy","Sell"}:raise ValueError("identity/side")
                size=float(row[3]); price=float(row[4])
                if not(math.isfinite(size) and size>0 and math.isfinite(price) and price>0):raise ValueError("price/size")
            except Exception:
                invalid+=1; continue
            if not(start_us<=ts<end_us):outday+=1; continue
            if last_ts is not None and ts<last_ts:fail(f"Bybit timestamp reversal {symbol}")
            last_ts=ts
            if t_us<=ts<t_us+SEARCH_BUCKETS*1_000_000:
                last_by_sec[ts//1_000_000]=(ts,price)
    if invalid!=0 or outday!=0:fail(f"Bybit integrity {symbol}: invalid={invalid} outday={outday}")
    return {"last_by_sec":last_by_sec}

def nr(vals,q):
    if not vals:return None
    s=sorted(vals); i=max(0,min(len(s)-1,math.ceil(q*len(s))-1)); return s[i]

def main():
    try:
        d0=require(); d0m=d0_event_map(d0)
        if OUT.exists():
            old=load_json(OUT)
            if old.get("status") in {SURVIVE,REJECT,DEFER}:fail(f"one-shot guard: {old.get('status')}")

        rows=[]; total_bytes=0
        for i,(base,inst,list_utc,bybit,date,okx_file,bybit_file) in enumerate(EVENTS,1):
            print(f"B13-B-S0 [{i}/7] {base} launch-headroom",flush=True)
            e=d0m[inst]
            okx_expected=int(e.get("okx_launch_day_archive_bytes") or 0)
            bybit_expected=int(e.get("bybit_launch_day_archive_bytes") or 0)
            okx_url=resolve_okx(base,inst,date,okx_file)
            if head(okx_url,OKX_STATIC,okx_file)!=okx_expected:fail(f"OKX HEAD size changed {inst}")
            bybit_url=f"{BYBIT_PUBLIC}/trading/{bybit}/{bybit_file}"
            if head(bybit_url,"public.bybit.com",bybit_file)!=bybit_expected:fail(f"Bybit HEAD size changed {bybit}")
            total_bytes+=okx_expected+bybit_expected
            if total_bytes>MAX_TOTAL:fail(f"total download cap exceeded {total_bytes}")
            op,oreuse=download(okx_url,OKX_STATIC,okx_file,okx_expected)
            bp,breuse=download(bybit_url,"public.bybit.com",bybit_file,bybit_expected)
            t_us=int(datetime.fromisoformat(list_utc).timestamp()*1_000_000)
            o=parse_okx(op,inst,okx_file,t_us)
            b=parse_bybit(bp,bybit,date,t_us)
            joint=sorted(set(o["last_by_sec"]) & set(b["last_by_sec"]))
            first=joint[0] if joint else None
            if first is None:
                row={"base":base,"instId":inst,"listTime_utc":list_utc,"launch_month":date[:7],"launch_price_state":"NO_COACTIVE_LAUNCH_PRICE","abs_launch_basis_bps":None,"first_coactive_offset_seconds":None,"last_event_skew_ms":None,"okx_schema":o["schema"],"source_0_rows":o["source_0_rows"],"source_1_rows":o["source_1_rows"],"okx_reused":oreuse,"bybit_reused":breuse}
            else:
                ots,opx=o["last_by_sec"][first]; bts,bpx=b["last_by_sec"][first]
                basis=10000.0*abs(math.log(opx/bpx))
                row={"base":base,"instId":inst,"listTime_utc":list_utc,"launch_month":date[:7],"launch_price_state":"COACTIVE_VALID","abs_launch_basis_bps":basis,"first_coactive_offset_seconds":int(first-(t_us//1_000_000)),"last_event_skew_ms":abs(ots-bts)/1000.0,"okx_schema":o["schema"],"source_0_rows":o["source_0_rows"],"source_1_rows":o["source_1_rows"],"okx_reused":oreuse,"bybit_reused":breuse}
            rows.append(row)
            print(f"  state={row['launch_price_state']} offset={row['first_coactive_offset_seconds']} basis_bps={row['abs_launch_basis_bps']}",flush=True)

        valid=[r for r in rows if r["launch_price_state"]=="COACTIVE_VALID"]
        valid_months=sorted({r["launch_month"] for r in valid})
        sample_gates={"coactive_valid_gte6":len(valid)>=MIN_COACTIVE_VALID,"valid_months_gte3":len(valid_months)>=MIN_VALID_MONTHS}
        if not all(sample_gates.values()):
            status=DEFER; headroom_gates=None
        else:
            vals=[r["abs_launch_basis_bps"] for r in valid]
            qual=[r for r in valid if r["abs_launch_basis_bps"]>=HEADROOM_BPS]
            qmonths=sorted({r["launch_month"] for r in qual})
            headroom_gates={"scheduled_ge50_gte4":len(qual)>=MIN_QUALIFYING,"median_ge50":statistics.median(vals)>=HEADROOM_BPS,"qualifying_months_gte3":len(qmonths)>=MIN_QUAL_MONTHS}
            status=SURVIVE if all(headroom_gates.values()) else REJECT

        vals=[r["abs_launch_basis_bps"] for r in valid]
        qual=[r for r in valid if r["abs_launch_basis_bps"] is not None and r["abs_launch_basis_bps"]>=HEADROOM_BPS]
        skews=[r["last_event_skew_ms"] for r in valid]
        rep={"stage":STAGE,"version":"0.1","status":status,"scheduled_events":7,"coactive_valid_events":len(valid),"no_coactive_events":7-len(valid),"valid_launch_months":valid_months,"structural_burden_bps":STRUCTURAL_BURDEN_BPS,"headroom_threshold_bps":HEADROOM_BPS,"events_ge50bps":len(qual),"qualifying_months":sorted({r["launch_month"] for r in qual}),"median_abs_launch_basis_bps":statistics.median(vals) if vals else None,"p75_abs_launch_basis_bps_diagnostic":nr(vals,0.75),"max_abs_launch_basis_bps_diagnostic":max(vals) if vals else None,"median_last_event_skew_ms_diagnostic":statistics.median(skews) if skews else None,"p99_last_event_skew_ms_diagnostic":nr(skews,0.99),"sample_gates":sample_gates,"headroom_gates":headroom_gates,"events":rows,"historical_trade_bodies_opened":True,"price_accessed":True,"absolute_launch_basis_calculated":True,"convergence_calculated":False,"relative_return_calculated":False,"strategy_signal_calculated":False,"execution_model_calculated":False,"pnl_calculated":False,"candidate_id_assigned":False,"promotional_alpha_accessed":False}
        atomic_json(OUT,rep)
        print(status)
        print("coactive_valid =",len(valid),"/ 7")
        print("events_ge50bps =",len(qual))
        print("valid_months =",valid_months)
        print("qualifying_months =",rep["qualifying_months"])
        print("median_abs_launch_basis_bps =",rep["median_abs_launch_basis_bps"])
        print("p75/max diagnostic =",rep["p75_abs_launch_basis_bps_diagnostic"],"/",rep["max_abs_launch_basis_bps_diagnostic"])
        print("sample_gates =",sample_gates)
        print("headroom_gates =",headroom_gates)
        print("convergence/relative-return/signal/execution/PnL = False")
        print("candidate_id_assigned = False")
        print("promotional_alpha_accessed = False")
        print("report =",OUT)
        return 0
    except Exception as exc:
        print("B13B_S0_IMPLEMENTATION_FAIL")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

if __name__=="__main__":
    raise SystemExit(main())
