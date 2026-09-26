#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

STAGE="SC001-B14A-P0-PROSPECTIVE-TRADE-COLLECTOR-V0.3"
COMPLETE="B14A_P0_COLLECTION_COMPLETE"
T0_MS=1790321400000
CRITICAL_START_MS=T0_MS-1000
CRITICAL_END_MS=T0_MS+6000
BUCKET_MS=1000
BUCKET_COUNT=5
HURDLE_BPS=50.0
FAMILIES={
    "BTC":{"future":"BTC-USD-260925","swap":"BTC-USD-SWAP"},
    "ETH":{"future":"ETH-USD-260925","swap":"ETH-USD-SWAP"},
}
PASS_STRONG="B14A_P0_STRONG_HEADROOM_2_OF_2"
PASS_MIXED="B14A_P0_MIXED_HEADROOM_1_OF_2"
PASS_WEAK="B14A_P0_WEAK_HEADROOM_0_OF_2"
DEFER="B14A_P0_DEFER_DATA"
SELFTEST_PASS="B14A_P0_READOUT_V01_SELF_TEST_PASS"


def fail(msg:str)->None:
    raise RuntimeError(msg)


def load_json(path:Path)->dict[str,Any]:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail(f"JSON object required: {path}")
    return obj


def iter_jsonl(path:Path):
    with path.open("r",encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if not line.strip():
                continue
            try:
                obj=json.loads(line)
            except Exception as exc:
                fail(f"invalid JSONL {path}:{n}: {exc}")
            if not isinstance(obj,dict):
                fail(f"JSON object required {path}:{n}")
            yield obj


def atomic_json(path:Path,obj:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)


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
        fail("Runner launcher package root mismatch")


def overlap(a0:int,a1:int,b0:int,b1:int)->bool:
    return max(a0,b0)<=min(a1,b1)


def validate_state(state:dict[str,Any])->dict[str,Any]:
    if state.get("stage")!=STAGE:
        fail(f"collector stage mismatch: {state.get('stage')}")
    if str(state.get("version"))!="0.3":
        fail(f"collector version mismatch: {state.get('version')}")
    if state.get("status")!=COMPLETE:
        return {"complete":False,"reason":"COLLECTOR_NOT_COMPLETE"}
    if state.get("subscription_ack") is not True:
        return {"complete":False,"reason":"SUBSCRIPTION_ACK_FALSE"}
    if state.get("basis_calculated") is not False or state.get("convergence_calculated") is not False or state.get("pnl_calculated") is not False:
        fail("collector firewall mismatch")
    intersecting=[]
    for source,rows in (
        ("connection_gap",state.get("connection_gaps") or []),
        ("process_restart_gap",state.get("process_restart_gaps") or []),
    ):
        for row in rows:
            try:
                start=int(row["start_ms"]); end=int(row["end_ms"])
            except Exception:
                fail(f"invalid {source} row")
            if end<start:
                fail(f"negative {source} interval")
            if overlap(start,end,CRITICAL_START_MS,CRITICAL_END_MS):
                intersecting.append({"source":source,"start_ms":start,"end_ms":end})
    return {"complete":True,"reason":None,"critical_gap_intersections":intersecting}


def load_trades(raw_path:Path)->dict[str,list[dict[str,Any]]]:
    allowed={v for fam in FAMILIES.values() for v in fam.values()}
    out={inst:[] for inst in allowed}
    seq=0
    for msg in iter_jsonl(raw_path):
        if msg.get("stage")!=STAGE:
            fail("raw message stage mismatch")
        trades=msg.get("trades")
        if not isinstance(trades,list):
            fail("raw trades field not list")
        for row in trades:
            if not isinstance(row,dict):
                fail("raw trade row not object")
            inst=str(row.get("instId") or "")
            if inst not in allowed:
                fail(f"unexpected instrument {inst}")
            ts=int(row.get("ts") or 0)
            px=float(row.get("px") or 0)
            if ts<=0 or not math.isfinite(px) or px<=0:
                fail("invalid trade timestamp/price")
            if T0_MS<=ts<T0_MS+BUCKET_COUNT*BUCKET_MS:
                seq+=1
                out[inst].append({
                    "instId":inst,
                    "ts":ts,
                    "tradeId":str(row.get("tradeId") or ""),
                    "px":px,
                    "_capture_seq":seq,
                })
    for inst in out:
        out[inst].sort(key=lambda x:(x["ts"],x["_capture_seq"]))
    return out


def family_readout(name:str,trades:dict[str,list[dict[str,Any]]],global_gap:bool)->dict[str,Any]:
    future=FAMILIES[name]["future"]; swap=FAMILIES[name]["swap"]
    if global_gap:
        return {"family":name,"valid":False,"reason":"CRITICAL_GAP_INTERSECTION"}
    for i in range(BUCKET_COUNT):
        start=T0_MS+i*BUCKET_MS
        end=start+BUCKET_MS
        f=[x for x in trades[future] if start<=x["ts"]<end]
        s=[x for x in trades[swap] if start<=x["ts"]<end]
        if f and s:
            fp=f[-1]; sp=s[-1]
            basis=10000.0*abs(math.log(fp["px"]/sp["px"]))
            return {
                "family":name,
                "valid":True,
                "reason":None,
                "selected_bucket_index":i,
                "bucket_start_ms":start,
                "bucket_end_ms":end,
                "future_inst":future,
                "swap_inst":swap,
                "future_last_trade_ts_ms":fp["ts"],
                "swap_last_trade_ts_ms":sp["ts"],
                "future_price":fp["px"],
                "swap_price":sp["px"],
                "abs_basis_bps":basis,
                "headroom_ge_50bps":basis>=HURDLE_BPS,
            }
    return {"family":name,"valid":False,"reason":"NO_COACTIVE_BUCKET_IN_FROZEN_5S"}


def analyze(root:Path,out:Path,quiet:bool=False)->dict[str,Any]:
    state_path=root/"collector_state.json"
    raw_path=root/"raw_trades.jsonl"
    conn_path=root/"connection_events.jsonl"
    for p in (state_path,raw_path,conn_path):
        if not p.is_file() or p.is_symlink():
            fail(f"required input missing/invalid: {p.name}")
    state=load_json(state_path)
    state_gate=validate_state(state)
    # Parse connection ledger for syntax/stage integrity. Gap authority is persisted state.
    conn_rows=0
    for row in iter_jsonl(conn_path):
        conn_rows+=1
        if row.get("stage")!=STAGE:
            fail("connection ledger stage mismatch")
        if not row.get("event"):
            fail("connection ledger event missing")
    trades=load_trades(raw_path)
    state_invalid=state_gate.get("complete") is not True
    global_gap=bool(state_gate.get("critical_gap_intersections"))
    suppress_outcome=state_invalid or global_gap
    families={name:family_readout(name,trades,suppress_outcome) for name in ("BTC","ETH")}
    if state_invalid:
        for x in families.values():
            x["reason"]=state_gate.get("reason") or "COLLECTOR_STATE_INVALID"
    valid=all(x["valid"] for x in families.values()) and state_gate.get("complete") is True
    if not valid:
        status=DEFER
    else:
        hits=sum(1 for x in families.values() if x["headroom_ge_50bps"])
        status={0:PASS_WEAK,1:PASS_MIXED,2:PASS_STRONG}[hits]
    result={
        "schema":"sc001.b14a_p0_prospective_headroom_readout.v0.1",
        "status":status,
        "frozen_event":{
            "expiry_ms":1790323200000,
            "t0_ms":T0_MS,
            "bucket_count":BUCKET_COUNT,
            "bucket_seconds":1,
            "headroom_hurdle_bps":HURDLE_BPS,
            "representation":"STRICT_COACTIVE_1S_NO_CARRY_FORWARD",
        },
        "state_gate":state_gate,
        "collector_snapshot":{
            "status":state.get("status"),
            "subscription_ack":state.get("subscription_ack"),
            "raw_trade_messages":state.get("raw_trade_messages"),
            "normalized_trade_rows":state.get("normalized_trade_rows"),
            "invalid_trade_rows":state.get("invalid_trade_rows"),
            "reconnect_count":state.get("reconnect_count"),
            "process_restart_count":state.get("process_restart_count"),
        },
        "connection_ledger_rows":conn_rows,
        "trade_rows_in_frozen_5s":{k:len(v) for k,v in sorted(trades.items())},
        "families":families,
        "convergence_calculated":False,
        "settlement_price_analyzed":False,
        "execution_model_calculated":False,
        "pnl_calculated":False,
        "candidate_id_assigned":False,
        "promotional_claim_made":False,
        "next_state":(
            "B14A_CONTINUE_PROSPECTIVE_MULTI_EXPIRY_PROGRAM"
            if status in {PASS_STRONG,PASS_MIXED}
            else "B14A_NO_RESCUE_OF_FINAL_30M_ARCHITECTURE"
            if status==PASS_WEAK
            else "B14A_STOP_AND_REVIEW_P0_DATA_QUALITY"
        ),
    }
    atomic_json(out/"b14a_p0_headroom_readout_manifest.json",result)
    if not quiet:
        print(status)
        for name in ("BTC","ETH"):
            x=families[name]
            print(name,"valid =",x["valid"],"basis_bps =",x.get("abs_basis_bps"))
    return result


def write_jsonl(path:Path,rows:list[dict[str,Any]])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row,separators=(",",":"))+"\n")


def selftest()->None:
    current=Path(__file__).resolve()
    validate_launcher_args(str(current.parents[2]),str(current))
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/"in"; out=Path(td)/"out"; root.mkdir(parents=True)
        state={
            "stage":STAGE,"version":"0.3","status":COMPLETE,"subscription_ack":True,
            "basis_calculated":False,"convergence_calculated":False,"pnl_calculated":False,
            "connection_gaps":[],"process_restart_gaps":[],"raw_trade_messages":4,
            "normalized_trade_rows":8,"invalid_trade_rows":0,"reconnect_count":0,"process_restart_count":0,
        }
        atomic_json(root/"collector_state.json",state)
        write_jsonl(root/"connection_events.jsonl",[{"stage":STAGE,"event":"CONNECTED","ts_ms":T0_MS-10000,"epoch":"e1"}])
        write_jsonl(root/"raw_trades.jsonl",[
            {"stage":STAGE,"trades":[
                {"instId":"BTC-USD-260925","tradeId":"b1","ts":T0_MS+100,"px":"101"},
                {"instId":"BTC-USD-SWAP","tradeId":"b2","ts":T0_MS+200,"px":"100"},
                {"instId":"ETH-USD-260925","tradeId":"e1","ts":T0_MS+1100,"px":"100.2"},
                {"instId":"ETH-USD-SWAP","tradeId":"e2","ts":T0_MS+1200,"px":"100"},
            ]}
        ])
        r=analyze(root,out,quiet=True)
        assert r["status"]==PASS_MIXED
        assert r["families"]["BTC"]["selected_bucket_index"]==0
        assert r["families"]["ETH"]["selected_bucket_index"]==1
        state["process_restart_gaps"]=[{"start_ms":T0_MS-500,"end_ms":T0_MS+500,"duration_ms":1000}]
        atomic_json(root/"collector_state.json",state)
        r2=analyze(root,out,quiet=True)
        assert r2["status"]==DEFER
    print(SELFTEST_PASS)


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","readout"),default="self-test")
    ap.add_argument("--data-root")
    ap.add_argument("--out-dir",default=os.environ.get("OUTPUT_DIR","/work/run/output"))
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)
    if a.mode=="self-test":
        selftest(); return 0
    if not a.data_root:
        fail("--data-root required for readout")
    root=Path(a.data_root).resolve()
    if not root.is_dir():
        fail("data root missing")
    analyze(root,Path(a.out_dir).resolve())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
