from __future__ import annotations

import argparse
import csv
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
from decimal import Decimal, InvalidOperation
from pathlib import Path

STAGE="SC001-B14A-HEDGE-FUNDING-SETTLEMENT-COST-PREFLIGHT-V0.1"
PASS="B14A_COST_PREFLIGHT_PASS"
REVIEW="B14A_COST_PREFLIGHT_REVIEW"
SELFTEST_PASS="B14A_COST_PREFLIGHT_SELF_TEST_PASS"
SELFTEST_REVIEW="B14A_COST_PREFLIGHT_SELF_TEST_REVIEW"

TARGETS={
    "BTC-USD":{"inst":"BTC-USD-SWAP"},
    "ETH-USD":{"inst":"ETH-USD-SWAP"},
}

START_MS=int(datetime(2026,6,1,tzinfo=timezone.utc).timestamp()*1000)
END_MS_EXCL=int(datetime(2026,9,1,tzinfo=timezone.utc).timestamp()*1000)

# Historical monthly archive queries use the same qualified broad boundary treatment as B13-A.
ARCHIVE_BEGIN_MS=int(datetime(2026,5,31,16,tzinfo=timezone.utc).timestamp()*1000)
ARCHIVE_END_MS=int(datetime(2026,9,1,16,tzinfo=timezone.utc).timestamp()*1000)

MIN_ROWS=200
MIN_MONTHS=3
MIN_DATES_08UTC=80

TAKER_FILL_BPS=5.0
TAKER_FILL_COUNT=3
SETTLEMENT_FEE_BPS=1.0
SPREAD_DEPTH_RESERVE_BPS=10.0
EXECUTION_MODEL_RESERVE_BPS=10.0
MIN_ECONOMIC_RESERVE_BPS=10.0

OKX_BASE="https://www.okx.com"
OKX_STATIC="static.okx.com"
TIMEOUT=60
RETRIES=4
MAX_JSON=6_000_000
MAX_FILE=20*1024*1024
MAX_TOTAL=100*1024*1024
CHUNK=1024*1024

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-b14a-hedge-funding-settlement-cost-preflight-v0.1.md"
REGISTRY=ROOT/"docs/research/sc001-contamination-registry-v0.28.json"
FREEZE=ROOT/"docs/research/sc001-b14a-cost-preflight-implementation-freeze-v0.1.json"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_B14A_COST_PREFLIGHT"
ARCH_DIR=OUT_DIR/"funding_archives"
OUT=OUT_DIR/"sc001_b14a_cost_preflight_v0_1.json"

def fail(msg:str)->None:
    raise RuntimeError(msg)

def load_json(path:Path)->dict:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail(f"JSON object expected: {path}")
    return obj

def atomic_json(path:Path,obj:object)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(str(path)+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)

def git_blob(path:Path)->str:
    return subprocess.check_output(
        ["git","-C",str(ROOT),"hash-object",str(path.relative_to(ROOT))],
        text=True
    ).strip()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def finite_decimal(value)->Decimal:
    try:
        x=Decimal(str(value).strip())
    except (InvalidOperation,ValueError) as exc:
        raise ValueError(f"invalid decimal {value!r}") from exc
    if not x.is_finite():
        raise ValueError(f"non-finite decimal {value!r}")
    return x

def require_freeze()->dict:
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_B14A_COST_PREFLIGHT_RUN":
        fail("freeze status mismatch")
    checks={
        "runner_git_blob_sha":git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha":git_blob(PROTOCOL),
        "contamination_registry_git_blob_sha":git_blob(REGISTRY),
    }
    for k,v in checks.items():
        if fr.get(k)!=v:
            fail(f"freeze identity mismatch: {k}")
    if int(fr.get("window_start_ms",-1))!=START_MS or int(fr.get("window_end_exclusive_ms",-1))!=END_MS_EXCL:
        fail("window mismatch")
    if tuple(fr.get("instruments") or ())!=tuple(v["inst"] for v in TARGETS.values()):
        fail("instrument freeze mismatch")
    for k in (
        "futures_price_access_authorized",
        "swap_price_access_authorized",
        "basis_authorized",
        "return_authorized",
        "settlePx_authorized",
        "delivery_price_authorized",
        "convergence_authorized",
        "strategy_signal_authorized",
        "execution_model_authorized",
        "pnl_authorized",
        "candidate_id_assignment_authorized",
        "promotional_evidence_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"firewall mismatch: {k}")

    reg=load_json(REGISTRY).get("b14a_cost_calibration") or {}
    if reg.get("classification")!="NONPROMOTIONAL_STRUCTURAL_COST_CALIBRATION":
        fail("registry classification mismatch")
    for k in ("funding_rate_access_authorized","funding_timestamp_access_authorized","static_cost_arithmetic_authorized"):
        if reg.get(k) is not True:
            fail(f"registry authorization mismatch: {k}")
    if reg.get("basis_authorized") is not False or reg.get("pnl_authorized") is not False:
        fail("registry market firewall mismatch")
    return fr

def request_json(url:str,label:str)->dict:
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"BotMarketplace-SC001-B14A-Cost/0.1",
                "Accept":"application/json",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_JSON+1)
            if len(raw)>MAX_JSON:
                fail(f"{label} response cap")
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            last=exc
            if attempt<RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} request failed: {type(last).__name__}: {last}")

def okx_get(path:str,params:dict[str,str])->dict:
    url=OKX_BASE+path+"?"+urllib.parse.urlencode(params)
    obj=request_json(url,"OKX")
    if not isinstance(obj,dict) or str(obj.get("code"))!="0":
        fail(f"OKX response code mismatch: {obj!r}")
    return obj

def trusted_archive(url:str,filename:str)->bool:
    p=urllib.parse.urlparse(url)
    return (
        p.scheme=="https"
        and (p.hostname or "").lower()==OKX_STATIC
        and Path(p.path).name==filename
    )

def walk_file_nodes(node):
    if isinstance(node,dict):
        fn=node.get("filename") or node.get("fileName")
        u=node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
        if isinstance(fn,str) and isinstance(u,str):
            yield node
        for v in node.values():
            yield from walk_file_nodes(v)
    elif isinstance(node,list):
        for v in node:
            yield from walk_file_nodes(v)

def archive_metadata(family:str)->list[dict]:
    obj=okx_get("/api/v5/public/market-data-history",{
        "module":"3",
        "instType":"SWAP",
        "instFamilyList":family,
        "dateAggrType":"monthly",
        "begin":str(ARCHIVE_BEGIN_MS),
        "end":str(ARCHIVE_END_MS),
    })
    files={}
    for node in walk_file_nodes(obj.get("data")):
        fn=node.get("filename") or node.get("fileName")
        u=node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
        if not isinstance(fn,str) or not isinstance(u,str):
            continue
        if not trusted_archive(u,fn):
            fail(f"untrusted funding archive {family}: {fn} {u}")
        prev=files.get(fn)
        if prev is not None and prev["url"]!=u:
            fail(f"conflicting funding archive URL {fn}")
        files[fn]={"filename":fn,"url":u,"sizeMB_raw":node.get("sizeMB")}
    if not files:
        fail(f"no funding archive metadata for {family}")
    return [files[k] for k in sorted(files)]

def download(meta:dict)->dict:
    fn=meta["filename"]; u=meta["url"]
    ARCH_DIR.mkdir(parents=True,exist_ok=True)
    path=ARCH_DIR/fn
    if path.exists():
        size=path.stat().st_size
        if size<=0 or size>MAX_FILE:
            fail(f"bad reused archive size {fn}: {size}")
        return {**meta,"path":str(path),"bytes":size,"sha256":sha256_file(path),"reused":True}

    tmp=Path(str(path)+".part"); tmp.unlink(missing_ok=True)
    req=urllib.request.Request(u,headers={
        "User-Agent":"BotMarketplace-SC001-B14A-Cost/0.1",
        "Referer":"https://www.okx.com/historical-data",
    })
    got=0; h=hashlib.sha256()
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp,tmp.open("wb") as f:
        final=resp.geturl()
        if not trusted_archive(final,fn):
            fail(f"archive redirect identity mismatch {fn}")
        while True:
            chunk=resp.read(CHUNK)
            if not chunk:
                break
            got+=len(chunk)
            if got>MAX_FILE:
                fail(f"archive file cap exceeded {fn}")
            f.write(chunk); h.update(chunk)
        f.flush(); os.fsync(f.fileno())
    if got<=0:
        fail(f"empty archive {fn}")
    os.replace(tmp,path)
    return {**meta,"path":str(path),"bytes":got,"sha256":h.hexdigest(),"reused":False}

def parse_funding(target_inst:str,archives:list[dict])->list[dict]:
    by_ts={}
    for meta in archives:
        path=Path(meta["path"])
        with zipfile.ZipFile(path) as z:
            bad=z.testzip()
            if bad is not None:
                fail(f"ZIP CRC failure {path.name}: {bad}")
            members=[x for x in z.infolist() if not x.is_dir()]
            if not members:
                fail(f"no funding ZIP members {path.name}")
            for info in members:
                with z.open(info) as raw:
                    reader=csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline=""))
                    for fields in reader:
                        if not fields:
                            continue
                        if fields[0]=="instrument_name":
                            if fields[:3]!=["instrument_name","funding_rate","funding_time"]:
                                fail(f"funding header mismatch {path.name}: {fields}")
                            continue
                        if fields[0]!=target_inst:
                            continue
                        if len(fields)!=3:
                            fail(f"target funding row width mismatch {target_inst}")
                        rate=finite_decimal(fields[1])
                        ts=int(fields[2].strip())
                        if not (START_MS<=ts<END_MS_EXCL):
                            continue
                        prev=by_ts.get(ts)
                        if prev is not None and prev!=rate:
                            fail(f"conflicting duplicate funding row {target_inst} {ts}")
                        by_ts[ts]=rate
    return [{"timestamp_ms":ts,"rate":by_ts[ts]} for ts in sorted(by_ts)]

def nearest_rank(vals:list[float],q:float):
    if not vals:
        return None
    s=sorted(vals)
    idx=max(0,min(len(s)-1,math.ceil(q*len(s))-1))
    return s[idx]

def summarize(rows:list[dict])->dict:
    vals=[float(abs(x["rate"])*Decimal(10000)) for x in rows]
    months=sorted({
        datetime.fromtimestamp(x["timestamp_ms"]/1000,tz=timezone.utc).strftime("%Y-%m")
        for x in rows
    })
    dates08=sorted({
        datetime.fromtimestamp(x["timestamp_ms"]/1000,tz=timezone.utc).strftime("%Y-%m-%d")
        for x in rows
        if datetime.fromtimestamp(x["timestamp_ms"]/1000,tz=timezone.utc).hour==8
        and datetime.fromtimestamp(x["timestamp_ms"]/1000,tz=timezone.utc).minute==0
    })
    return {
        "row_count":len(rows),
        "months":months,
        "dates_with_08utc_funding":dates08,
        "dates_with_08utc_funding_count":len(dates08),
        "median_abs_funding_bps":statistics.median(vals) if vals else None,
        "p95_abs_funding_bps":nearest_rank(vals,0.95),
        "p99_abs_funding_bps":nearest_rank(vals,0.99),
        "max_abs_funding_bps":max(vals) if vals else None,
    }

def self_test()->int:
    try:
        require_freeze()
        if TAKER_FILL_COUNT!=3 or TAKER_FILL_BPS!=5.0 or SETTLEMENT_FEE_BPS!=1.0:
            fail("fee fixture mismatch")
        if 5*math.ceil((36+1+10)/5)!=50:
            fail("headroom rounding fixture mismatch")
        print(SELFTEST_PASS)
        print("instruments =",[v["inst"] for v in TARGETS.values()])
        print("window = 2026-06-01 .. 2026-08-31")
        print("known_subtotal_before_funding_bps = 36")
        print("price/basis/convergence/PnL = CLOSED")
        return 0
    except Exception as exc:
        print(SELFTEST_REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def run()->int:
    try:
        require_freeze()
        total_bytes=0
        summaries={}
        source_files={}

        for family,spec in TARGETS.items():
            print(f"B14-A COST {spec['inst']} funding",flush=True)
            metas=archive_metadata(family)
            dls=[]
            for m in metas:
                d=download(m)
                total_bytes+=int(d["bytes"])
                if total_bytes>MAX_TOTAL:
                    fail("total archive cap exceeded")
                dls.append(d)
            rows=parse_funding(spec["inst"],dls)
            summaries[spec["inst"]]=summarize(rows)
            source_files[spec["inst"]]=[x["filename"] for x in dls]
            print("  rows =",len(rows),"p99_abs_bps =",summaries[spec["inst"]]["p99_abs_funding_bps"],"dates08 =",summaries[spec["inst"]]["dates_with_08utc_funding_count"],flush=True)

        gates={}
        for inst,s in summaries.items():
            gates[f"{inst}_rows_gte200"]=s["row_count"]>=MIN_ROWS
            gates[f"{inst}_months_gte3"]=len(s["months"])>=MIN_MONTHS
            gates[f"{inst}_dates08_gte80"]=s["dates_with_08utc_funding_count"]>=MIN_DATES_08UTC

        if not all(gates.values()):
            status=REVIEW
            funding_reserve=None
            final_burden=None
            headroom=None
        else:
            raw=max(float(s["p99_abs_funding_bps"]) for s in summaries.values())
            funding_reserve=max(1,math.ceil(raw))
            final_burden=(
                TAKER_FILL_COUNT*TAKER_FILL_BPS
                + SETTLEMENT_FEE_BPS
                + SPREAD_DEPTH_RESERVE_BPS
                + EXECUTION_MODEL_RESERVE_BPS
                + funding_reserve
            )
            headroom=5*math.ceil((final_burden+MIN_ECONOMIC_RESERVE_BPS)/5)
            status=PASS

        report={
            "stage":STAGE,
            "version":"0.1",
            "status":status,
            "window":{"start_ms":START_MS,"end_exclusive_ms":END_MS_EXCL},
            "summaries":summaries,
            "source_files":source_files,
            "gates":gates,
            "explicit_fee_floor_bps":TAKER_FILL_COUNT*TAKER_FILL_BPS+SETTLEMENT_FEE_BPS,
            "spread_depth_reserve_bps":SPREAD_DEPTH_RESERVE_BPS,
            "execution_model_reserve_bps":EXECUTION_MODEL_RESERVE_BPS,
            "funding_reserve_bps":funding_reserve,
            "final_structural_burden_bps":final_burden,
            "minimum_economic_reserve_bps":MIN_ECONOMIC_RESERVE_BPS,
            "headroom_hurdle_bps":headroom,
            "funding_rates_accessed":True,
            "funding_timestamps_accessed":True,
            "futures_price_accessed":False,
            "swap_price_accessed":False,
            "basis_calculated":False,
            "return_calculated":False,
            "settlePx_accessed":False,
            "delivery_price_accessed":False,
            "convergence_calculated":False,
            "strategy_signal_calculated":False,
            "execution_model_calculated":False,
            "pnl_calculated":False,
            "candidate_id_assigned":False,
            "promotional_evidence_accessed":False,
        }
        atomic_json(OUT,report)

        print(status)
        print("gates =",gates)
        print("funding_reserve_bps =",funding_reserve)
        print("final_structural_burden_bps =",final_burden)
        print("headroom_hurdle_bps =",headroom)
        print("price/basis/convergence/execution/PnL = False")
        print("candidate_id_assigned = False")
        print("report =",OUT)
        return 0 if status==PASS else 2

    except Exception as exc:
        print(REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","run"),required=True)
    args=ap.parse_args()
    return self_test() if args.mode=="self-test" else run()

if __name__=="__main__":
    raise SystemExit(main())
