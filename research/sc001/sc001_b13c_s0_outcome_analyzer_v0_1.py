#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_ANCHOR_SHA="5f84f40a91c3a7bc57bf3c4e878a53130ef696a28be162c014c10f8253223a1e"
EXPECTED_EXTRACTION_MANIFEST_SHA="79db43a19249c8f56f886cf01616f3e56704d4a8fc8e5c5e03609254b2de1acf"
EXPECTED_TOTAL=1905
EXPECTED_VALID=1793
COMPLETE_DAYS=("2026-09-20","2026-09-21","2026-09-22","2026-09-23","2026-09-24","2026-09-25")

SURVIVE="B13C_S0_SIMPLE_REVERSAL_HEADROOM_SURVIVE"
REJECT="B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT"
DEFER="B13C_S0_DEFER_SAMPLE"
SELFTEST_PASS="B13C_S0_OUTCOME_ANALYZER_V01_SELF_TEST_PASS"


def fail(msg:str)->None:
    raise RuntimeError(msg)


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def validate_launcher_args(package_root_arg:str|None,entrypoint_arg:str|None)->None:
    if (package_root_arg is None)!=(entrypoint_arg is None):
        fail("incomplete Runner launcher positional contract")
    if package_root_arg is None:
        return
    package_root=Path(package_root_arg).resolve()
    entrypoint=Path(entrypoint_arg).resolve()
    current=Path(__file__).resolve()
    if entrypoint!=current:
        fail("Runner launcher entrypoint mismatch")
    if package_root not in current.parents:
        fail("Runner launcher package-root mismatch")


def quantile_type7(values:list[float],p:float)->float:
    if not values:
        fail("quantile on empty values")
    if not (0.0<=p<=1.0):
        fail("quantile p outside [0,1]")
    xs=sorted(values)
    if len(xs)==1:
        return xs[0]
    h=(len(xs)-1)*p
    lo=math.floor(h); hi=math.ceil(h)
    if lo==hi:
        return xs[lo]
    frac=h-lo
    return xs[lo]+frac*(xs[hi]-xs[lo])


def utc_day(ms:int)->str:
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).strftime("%Y-%m-%d")


def evaluate_rows(rows:list[dict[str,Any]],require_expected_count:bool=True)->dict[str,Any]:
    if require_expected_count and len(rows)!=EXPECTED_TOTAL:
        fail(f"anchor row count {len(rows)} != {EXPECTED_TOTAL}")

    signed=[]
    daily={d:[] for d in COMPLETE_DAYS}
    valid_count=0
    for i,row in enumerate(rows,1):
        valid=row.get("valid_price_cluster")
        if not isinstance(valid,bool):
            fail(f"row {i} valid_price_cluster not bool")
        if not valid:
            continue
        valid_count+=1
        try:
            sign=int(row["reversal_sign"])
            entry=float((row["entry"] or {})["price"])
            exitp=float((row["exit"] or {})["price"])
            end_ms=int(row["cluster_end_ms"])
        except Exception as exc:
            fail(f"row {i} valid anchor parse error: {exc}")
        if sign not in {-1,1}:
            fail(f"row {i} invalid reversal_sign")
        if not (math.isfinite(entry) and entry>0 and math.isfinite(exitp) and exitp>0):
            fail(f"row {i} invalid prices")
        val=sign*10000.0*math.log(exitp/entry)
        if not math.isfinite(val):
            fail(f"row {i} nonfinite signed reversal")
        signed.append(val)
        d=utc_day(end_ms)
        if d in daily:
            daily[d].append(val)

    if require_expected_count and valid_count!=EXPECTED_VALID:
        fail(f"valid price count {valid_count} != {EXPECTED_VALID}")

    n=len(signed)
    if n==0:
        pooled={"n":0,"p25":None,"median":None,"p75":None,"positive_count":0,"positive_share":None}
    else:
        pos=sum(1 for x in signed if x>0.0)
        pooled={
            "n":n,
            "p25":quantile_type7(signed,0.25),
            "median":quantile_type7(signed,0.50),
            "p75":quantile_type7(signed,0.75),
            "positive_count":pos,
            "positive_share":pos/n,
        }

    day_rows=[]
    positive_days=0
    for d in COMPLETE_DAYS:
        vals=daily[d]
        med=quantile_type7(vals,0.50) if vals else None
        positive=bool(med is not None and med>0.0)
        if positive:
            positive_days+=1
        day_rows.append({
            "utc_day":d,
            "valid_cluster_count":len(vals),
            "median_signed_reversal_bps":med,
            "positive_median":positive,
        })

    sample_gate=n>=100
    median_gate=bool(pooled["median"] is not None and pooled["median"]>=30.0)
    positive_share_gate=bool(pooled["positive_share"] is not None and pooled["positive_share"]>=0.55)
    breadth_gate=positive_days>=4

    if not sample_gate:
        status=DEFER
    elif median_gate and positive_share_gate and breadth_gate:
        status=SURVIVE
    else:
        status=REJECT

    return {
        "status":status,
        "pooled":pooled,
        "complete_days":day_rows,
        "positive_complete_day_count":positive_days,
        "gates":{
            "sample_ge_100":sample_gate,
            "median_ge_30bps":median_gate,
            "positive_share_ge_55pct":positive_share_gate,
            "positive_complete_days_ge_4_of_6":breadth_gate,
        },
    }


def load_jsonl(path:Path)->list[dict[str,Any]]:
    rows=[]
    with path.open("r",encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if not line.strip():
                continue
            try:
                row=json.loads(line)
            except Exception as exc:
                fail(f"JSONL line {n}: {exc}")
            if not isinstance(row,dict):
                fail(f"JSONL line {n} not object")
            rows.append(row)
    return rows


def selftest()->None:
    # Quantile type-7 fixtures.
    xs=[0.0,10.0,20.0,30.0,40.0]
    assert quantile_type7(xs,0.25)==10.0
    assert quantile_type7(xs,0.50)==20.0
    assert quantile_type7(xs,0.75)==30.0
    ys=[0.0,10.0,20.0,30.0]
    assert abs(quantile_type7(ys,0.25)-7.5)<1e-12
    assert abs(quantile_type7(ys,0.50)-15.0)<1e-12
    assert abs(quantile_type7(ys,0.75)-22.5)<1e-12

    # Synthetic rows with known signed direction:
    # LONG +10% => positive reversal; SHORT -10% raw => positive signed reversal.
    base_ms=int(datetime(2026,9,20,tzinfo=timezone.utc).timestamp()*1000)
    rows=[]
    for i in range(120):
        day=i%6
        end_ms=base_ms+day*86_400_000+10_000
        if i%2==0:
            sign=1; entry=100.0; exitp=100.5
        else:
            sign=-1; entry=100.0; exitp=99.5
        rows.append({
            "valid_price_cluster":True,
            "reversal_sign":sign,
            "entry":{"price":str(entry)},
            "exit":{"price":str(exitp)},
            "cluster_end_ms":end_ms,
        })
    r=evaluate_rows(rows,require_expected_count=False)
    assert r["status"]==SURVIVE
    assert r["pooled"]["n"]==120
    assert r["positive_complete_day_count"]==6

    # Reverse both directions -> reject.
    bad=[]
    for i in range(120):
        day=i%6
        end_ms=base_ms+day*86_400_000+10_000
        if i%2==0:
            sign=1; entry=100.0; exitp=99.9
        else:
            sign=-1; entry=100.0; exitp=100.1
        bad.append({
            "valid_price_cluster":True,
            "reversal_sign":sign,
            "entry":{"price":str(entry)},
            "exit":{"price":str(exitp)},
            "cluster_end_ms":end_ms,
        })
    r2=evaluate_rows(bad,require_expected_count=False)
    assert r2["status"]==REJECT
    print(SELFTEST_PASS)


def outcome(input_root:Path,out_dir:Path)->int:
    anchors=input_root/"price_anchors.jsonl"
    extraction=input_root/"price_anchor_extraction_manifest.json"
    if not anchors.is_file() or anchors.is_symlink():
        fail("price_anchors missing/invalid")
    if not extraction.is_file() or extraction.is_symlink():
        fail("extraction manifest missing/invalid")
    if sha256_file(anchors)!=EXPECTED_ANCHOR_SHA:
        fail("price_anchors SHA mismatch")
    if sha256_file(extraction)!=EXPECTED_EXTRACTION_MANIFEST_SHA:
        fail("extraction manifest SHA mismatch")
    rows=load_jsonl(anchors)
    result=evaluate_rows(rows,require_expected_count=True)
    report={
        "schema":"sc001.b13c_s0_simple_reversal_outcome.v0.1",
        "status":result["status"],
        "price_anchors_sha256":EXPECTED_ANCHOR_SHA,
        "extraction_manifest_sha256":EXPECTED_EXTRACTION_MANIFEST_SHA,
        "pooled":result["pooled"],
        "complete_days":result["complete_days"],
        "positive_complete_day_count":result["positive_complete_day_count"],
        "gates":result["gates"],
        "gross_headroom_only":True,
        "per_cluster_returns_emitted":False,
        "per_symbol_performance_ranked":False,
        "liquidation_size_stratified":False,
        "alternate_horizons_tested":False,
        "pnl_calculated":False,
        "next_state":(
            "PREPARE_EXECUTION_COST_FEASIBILITY_STAGE"
            if result["status"]==SURVIVE
            else "CLOSE_B13C_S0_SIMPLE_REVERSAL_ARCHITECTURE_NO_RESCUE"
            if result["status"]==REJECT
            else "B13C_S0_DEFER_SAMPLE"
        ),
    }
    out_dir.mkdir(parents=True,exist_ok=True)
    p=out_dir/"b13c_s0_simple_reversal_outcome.json"
    p.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(result["status"])
    print("valid_price_clusters =",result["pooled"]["n"])
    print("median_signed_reversal_bps =",result["pooled"]["median"])
    print("p25 =",result["pooled"]["p25"])
    print("p75 =",result["pooled"]["p75"])
    print("positive_share =",result["pooled"]["positive_share"])
    print("positive_complete_days =",result["positive_complete_day_count"],"/ 6")
    print("PnL = CLOSED")
    return 0


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","outcome"),default="self-test")
    ap.add_argument("--input-root")
    ap.add_argument("--out-dir",default=os.environ.get("OUTPUT_DIR","/work/run/output"))
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)
    if a.mode=="self-test":
        selftest()
        return 0
    if not a.input_root:
        fail("--input-root required for outcome")
    return outcome(Path(a.input_root).resolve(),Path(a.out_dir).resolve())


if __name__=="__main__":
    raise SystemExit(main())
