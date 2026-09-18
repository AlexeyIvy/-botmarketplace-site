from __future__ import annotations

import csv, io, json, math, os, statistics, subprocess, time, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

STAGE="SC001-C11-V2-SELECTION-STAGE-AB-V1.0"
DEFER="C11_V2_SC_DEFER_DATA_QUALITY"
REJECT_A="C11_V2_SC_REJECT_RESIDUAL_HEADROOM"
REJECT_B="C11_V2_SC_REJECT_DIRECTION_RETENTION"
SURVIVE="C11_V2_SC_SURVIVE_TO_PROSPECTIVE_CONFIRMATION"

STRUCTURAL_BURDEN_BPS=20.0
MIN_VALID_TOTAL=22
MIN_VALID_FAMILY=11
MIN_A_GE20_TOTAL=12
MIN_A_GE20_FAMILY=5
MIN_ACTIONABLE_TOTAL=18
MIN_ACTIONABLE_FAMILY=8
MIN_B_GE20_TOTAL=10
MIN_B_GE20_FAMILY=4
MIN_B_MEDIAN=20.0

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-c11-direction-rule-v2-stage-ab-selection-protocol-v1.0.md"
REGISTRY=ROOT/"docs/research/sc001-contamination-registry-v0.20.json"
FREEZE=ROOT/"docs/research/sc001-c11-v2-stage-ab-selection-implementation-freeze-v1.0.json"
META_RESULT=ROOT/"docs/research/sc001-c11-v2-selection-metadata-preflight-pass-result-v0.3.md"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
META=DATA_ROOT/"SC001_C11_V2_SC_METADATA"/"sc001_c11_v2_sc_metadata_preflight_report_v0_3.json"
OUT_DIR=DATA_ROOT/"SC001_C11_V2_SELECTION_AB"
ARCH=OUT_DIR/"archives"
OUT=OUT_DIR/"sc001_c11_v2_selection_stage_ab_report_v1_0.json"

OKX_DOMAINS=("https://www.okx.com","https://us.okx.com")
OKX_STATIC="static.okx.com"
OKX_FAMILY="BTC-USDT"
INST="BTC-USDT-SWAP"
HEADER=["instrument_name","trade_id","side","price","size","created_time"]
TIMEOUT=120
RETRIES=3
MAX_JSON=4_000_000
MAX_FILE=100*1024*1024
MAX_TOTAL=2*1024*1024*1024
CHUNK=1024*1024

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

def git_blob(p):
    return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()

def require():
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_C11_V2_SELECTION_STAGE_AB_RUN": fail("freeze status mismatch")
    expected={
        "runner_git_blob_sha":git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha":git_blob(PROTOCOL),
        "contamination_registry_git_blob_sha":git_blob(REGISTRY),
        "metadata_pass_result_git_blob_sha":git_blob(META_RESULT),
    }
    for k,v in expected.items():
        if fr.get(k)!=v: fail(f"freeze identity mismatch: {k}")
    reg=load_json(REGISTRY).get("c11_v2_selection_calibration") or {}
    if reg.get("historical_trade_body_access_authorized") is not True: fail("body access not authorized")
    if reg.get("residual_post_decision_headroom_authorized") is not True: fail("Stage A not authorized")
    if reg.get("first_impulse_direction_authorized") is not True or reg.get("continuation_outcome_authorized") is not True:
        fail("Stage B not authorized")
    for k in ("macro_release_value_authorized","macro_surprise_authorized","execution_model_authorized","pnl_authorized","confirmation_outcome_authorized","promotional_alpha_authorized"):
        if reg.get(k) is not False: fail(f"registry firewall mismatch: {k}")
    meta=load_json(META)
    if meta.get("status")!="C11_V2_SC_METADATA_PREFLIGHT_PASS": fail("metadata report not PASS")
    if int(meta.get("events_verified",0))!=24 or int(meta.get("cpi_verified",0))!=12 or int(meta.get("employment_verified",0))!=12:
        fail("metadata counts mismatch")
    for k in ("historical_trade_body_downloaded","historical_trade_body_opened","macro_release_value_accessed","macro_surprise_calculated","first_impulse_calculated","residual_post_decision_move_calculated","direction_signal_calculated","continuation_outcome_calculated","execution_model_calculated","pnl_calculated","confirmation_outcome_accessed","promotional_alpha_accessed"):
        if meta.get(k) is not False: fail(f"metadata firewall mismatch: {k}")
    if OUT.exists():
        old=load_json(OUT)
        if old.get("status") in {DEFER,REJECT_A,REJECT_B,SURVIVE}: fail(f"one-shot guard: {old.get('status')}")
    return meta

def day_ms(ds):
    d=datetime.strptime(ds,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    b=int(d.timestamp()*1000)
    return b,b+86_400_000

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
            req=urllib.request.Request(dom+"/priapi/v5/broker/public/trade-data/download-link?t="+str(int(time.time()*1000)),
                data=body,method="POST",headers={"User-Agent":"BotMarketplace-SC001-C11-V2-AB/1.0","Accept":"application/json,*/*","Content-Type":"application/json","Referer":"https://www.okx.com/historical-data"})
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_JSON+1); final=resp.geturl()
            if len(raw)>MAX_JSON: fail("metadata cap")
            host=(urllib.parse.urlparse(final).hostname or "").lower()
            if host not in {"www.okx.com","us.okx.com"}: fail("metadata host")
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
    req=urllib.request.Request(u,method="HEAD",headers={"User-Agent":"BotMarketplace-SC001-C11-V2-AB/1.0","Referer":"https://www.okx.com/historical-data"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
        final=resp.geturl(); cl=resp.headers.get("Content-Length"); status=int(getattr(resp,"status",200))
    if status!=200 or not trusted(final,b) or not cl or not cl.isdigit() or int(cl)<=0: fail(f"HEAD mismatch {b}")
    return int(cl)

def download(u,b,size):
    if size>MAX_FILE: fail(f"file cap {b}")
    ARCH.mkdir(parents=True,exist_ok=True)
    p=ARCH/b
    if p.exists() and p.stat().st_size==size: return p,True
    tmp=Path(str(p)+".part"); tmp.unlink(missing_ok=True)
    got=0
    req=urllib.request.Request(u,headers={"User-Agent":"BotMarketplace-SC001-C11-V2-AB/1.0","Referer":"https://www.okx.com/historical-data"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp,tmp.open("wb") as f:
        if not trusted(resp.geturl(),b): fail(f"GET identity {b}")
        while True:
            c=resp.read(CHUNK)
            if not c: break
            got+=len(c)
            if got>size: fail(f"download overflow {b}")
            f.write(c)
    if got!=size: fail(f"size mismatch {b}: {got}!={size}")
    os.replace(tmp,p)
    return p,False

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
    if None in (pre,p1,p60,tpre,t1,t60):
        return {"valid":False,"reason":"MISSING_ANCHOR"}
    if event_us-tpre>1_000_000:
        return {"valid":False,"reason":"PRE_STALE"}
    if target1-t1>1_000_000:
        return {"valid":False,"reason":"PLUS1_STALE"}
    if target60-t60>1_000_000:
        return {"valid":False,"reason":"PLUS60_STALE"}
    return {"valid":True,"pre_price":pre,"price_1s":p1,"price_60s":p60,
            "pre_staleness_ms":(event_us-tpre)/1000.0,
            "plus1_staleness_ms":(target1-t1)/1000.0,
            "plus60_staleness_ms":(target60-t60)/1000.0}

def nr(vals,q):
    if not vals:return None
    s=sorted(vals); i=max(0,min(len(s)-1,math.ceil(q*len(s))-1)); return s[i]

def main():
    try:
        meta=require()
        total_expected=sum(int(e["archive"]["content_length"]) for e in meta["events"])
        if total_expected>MAX_TOTAL: fail(f"total download cap exceeded: {total_expected}")
        rows=[]
        for i,e in enumerate(meta["events"],1):
            kind=e["kind"]; date=e["date"]; utc=e["frozen_utc"]; m=e["archive"]; b=m["filename"]; expected=int(m["content_length"])
            print(f"C11-V2-AB [{i}/24] {kind} {date} metadata/body-check",flush=True)
            u=resolve(date,b); size=head(u,b)
            if size!=expected: fail(f"HEAD size changed {date}: {size}!={expected}")
            p,reused=download(u,b,size)
            event_us=int(datetime.fromisoformat(utc.replace("Z","+00:00")).timestamp()*1_000_000)
            a=anchors(p,event_us)
            row={"kind":kind,"date":date,"event_utc":utc,"archive":b,"bytes":size,"reused":reused,"anchor_valid":bool(a["valid"]),"data_invalid_reason":None if a["valid"] else a["reason"]}
            if a["valid"]:
                row["_pre"]=a["pre_price"]; row["_p1"]=a["price_1s"]; row["_p60"]=a["price_60s"]
                row["pre_staleness_ms"]=a["pre_staleness_ms"]; row["plus1_staleness_ms"]=a["plus1_staleness_ms"]; row["plus60_staleness_ms"]=a["plus60_staleness_ms"]
                row["abs_residual_move_1s_to_60s_bps"]=10000.0*abs(math.log(a["price_60s"]/a["price_1s"]))
            else:
                row["abs_residual_move_1s_to_60s_bps"]=None
            rows.append(row)

        valid=[r for r in rows if r["anchor_valid"]]
        cpi_valid=sum(1 for r in valid if r["kind"]=="CPI")
        emp_valid=sum(1 for r in valid if r["kind"]=="EMPLOYMENT")
        data_gates={
            "valid_total_gte22":len(valid)>=MIN_VALID_TOTAL,
            "cpi_valid_gte11":cpi_valid>=MIN_VALID_FAMILY,
            "employment_valid_gte11":emp_valid>=MIN_VALID_FAMILY,
        }

        status=None; stage_a=None; stage_b=None

        if not all(data_gates.values()):
            status=DEFER
        else:
            residuals=[r["abs_residual_move_1s_to_60s_bps"] for r in valid]
            ge20=[r for r in valid if r["abs_residual_move_1s_to_60s_bps"]>=STRUCTURAL_BURDEN_BPS]
            a_med=statistics.median(residuals)
            a_gates={
                "scheduled_ge20_gte12":len(ge20)>=MIN_A_GE20_TOTAL,
                "median_residual_gte20":a_med>=STRUCTURAL_BURDEN_BPS,
                "cpi_ge20_gte5":sum(1 for r in ge20 if r["kind"]=="CPI")>=MIN_A_GE20_FAMILY,
                "employment_ge20_gte5":sum(1 for r in ge20 if r["kind"]=="EMPLOYMENT")>=MIN_A_GE20_FAMILY,
            }
            stage_a={
                "verdict_computed":True,
                "survive":all(a_gates.values()),
                "events_abs_residual_gte20bps":len(ge20),
                "cpi_abs_residual_gte20bps":sum(1 for r in ge20 if r["kind"]=="CPI"),
                "employment_abs_residual_gte20bps":sum(1 for r in ge20 if r["kind"]=="EMPLOYMENT"),
                "median_abs_residual_bps":a_med,
                "p75_abs_residual_bps_diagnostic":nr(residuals,0.75),
                "max_abs_residual_bps_diagnostic":max(residuals),
                "gates":a_gates,
            }
            if not stage_a["survive"]:
                status=REJECT_A
            else:
                actionable=[]
                for r in rows:
                    if not r["anchor_valid"]:
                        r["signal_state"]="DATA_INVALID"; r["first_impulse_bps"]=None; r["signed_continuation_bps"]=None
                        continue
                    impulse=10000.0*math.log(r["_p1"]/r["_pre"])
                    r["first_impulse_bps"]=impulse
                    if impulse>0:
                        r["signal_state"]="LONG"; direction=1.0
                    elif impulse<0:
                        r["signal_state"]="SHORT"; direction=-1.0
                    else:
                        r["signal_state"]="NO_TRADE"; r["signed_continuation_bps"]=None; continue
                    signed=direction*10000.0*math.log(r["_p60"]/r["_p1"])
                    r["signed_continuation_bps"]=signed
                    actionable.append(r)

                cpi_act=sum(1 for r in actionable if r["kind"]=="CPI")
                emp_act=sum(1 for r in actionable if r["kind"]=="EMPLOYMENT")
                signed=[r["signed_continuation_bps"] for r in actionable]
                ge20b=[r for r in actionable if r["signed_continuation_bps"]>=STRUCTURAL_BURDEN_BPS]
                b_med=statistics.median(signed) if signed else None
                b_gates={
                    "actionable_total_gte18":len(actionable)>=MIN_ACTIONABLE_TOTAL,
                    "cpi_actionable_gte8":cpi_act>=MIN_ACTIONABLE_FAMILY,
                    "employment_actionable_gte8":emp_act>=MIN_ACTIONABLE_FAMILY,
                    "median_signed_gte20":b_med is not None and b_med>=MIN_B_MEDIAN,
                    "scheduled_signed_ge20_gte10":len(ge20b)>=MIN_B_GE20_TOTAL,
                    "cpi_signed_ge20_gte4":sum(1 for r in ge20b if r["kind"]=="CPI")>=MIN_B_GE20_FAMILY,
                    "employment_signed_ge20_gte4":sum(1 for r in ge20b if r["kind"]=="EMPLOYMENT")>=MIN_B_GE20_FAMILY,
                }
                stage_b={
                    "verdict_computed":True,
                    "survive":all(b_gates.values()),
                    "actionable_events":len(actionable),
                    "no_trade_events":sum(1 for r in rows if r.get("signal_state")=="NO_TRADE"),
                    "long_events":sum(1 for r in rows if r.get("signal_state")=="LONG"),
                    "short_events":sum(1 for r in rows if r.get("signal_state")=="SHORT"),
                    "cpi_actionable":cpi_act,
                    "employment_actionable":emp_act,
                    "events_signed_continuation_gte20bps":len(ge20b),
                    "cpi_signed_continuation_gte20bps":sum(1 for r in ge20b if r["kind"]=="CPI"),
                    "employment_signed_continuation_gte20bps":sum(1 for r in ge20b if r["kind"]=="EMPLOYMENT"),
                    "median_signed_continuation_bps":b_med,
                    "positive_signed_count_diagnostic":sum(1 for v in signed if v>0),
                    "p75_signed_continuation_bps_diagnostic":nr(signed,0.75),
                    "worst_signed_continuation_bps_diagnostic":min(signed) if signed else None,
                    "best_signed_continuation_bps_diagnostic":max(signed) if signed else None,
                    "gates":b_gates,
                }
                status=SURVIVE if stage_b["survive"] else REJECT_B

        if stage_a is None:
            stage_a={"verdict_computed":False,"survive":None,"events_abs_residual_gte20bps":None,"cpi_abs_residual_gte20bps":None,"employment_abs_residual_gte20bps":None,"median_abs_residual_bps":None,"p75_abs_residual_bps_diagnostic":None,"max_abs_residual_bps_diagnostic":None,"gates":None}
        if stage_b is None:
            for r in rows:
                r["signal_state"]="DATA_INVALID" if not r["anchor_valid"] else None
                r["first_impulse_bps"]=None
                r["signed_continuation_bps"]=None
            stage_b={"verdict_computed":False,"survive":None,"actionable_events":None,"no_trade_events":None,"long_events":None,"short_events":None,"cpi_actionable":None,"employment_actionable":None,"events_signed_continuation_gte20bps":None,"cpi_signed_continuation_gte20bps":None,"employment_signed_continuation_gte20bps":None,"median_signed_continuation_bps":None,"positive_signed_count_diagnostic":None,"p75_signed_continuation_bps_diagnostic":None,"worst_signed_continuation_bps_diagnostic":None,"best_signed_continuation_bps_diagnostic":None,"gates":None}

        for r in rows:
            r.pop("_pre",None); r.pop("_p1",None); r.pop("_p60",None)

        rep={
            "stage":STAGE,"version":"1.0","status":status,
            "scheduled_events":24,
            "data_valid_events":len(valid),
            "data_invalid_events":24-len(valid),
            "cpi_data_valid":cpi_valid,
            "employment_data_valid":emp_valid,
            "data_validity_gates":data_gates,
            "structural_burden_bps":STRUCTURAL_BURDEN_BPS,
            "stage_a":stage_a,
            "stage_b":stage_b,
            "events":rows,
            "execution_model_calculated":False,
            "pnl_calculated":False,
            "confirmation_outcome_accessed":False,
            "macro_release_value_accessed":False,
            "macro_surprise_calculated":False,
            "promotional_alpha_accessed":False,
        }
        atomic_json(OUT,rep)

        print(status)
        print("scheduled / data_valid / data_invalid =",24,"/",len(valid),"/",24-len(valid))
        print("CPI valid / Employment valid =",cpi_valid,"/",emp_valid)
        print("Stage A =",stage_a)
        print("Stage B =",stage_b)
        print("execution/PnL/Confirmation/promotional alpha = False")
        print("report =",OUT)
        return 0
    except Exception as exc:
        print("C11_V2_SELECTION_IMPLEMENTATION_FAIL")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

if __name__=="__main__":
    raise SystemExit(main())
