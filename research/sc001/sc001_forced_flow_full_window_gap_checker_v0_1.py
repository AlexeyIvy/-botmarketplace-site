#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess, tempfile, time
from collections import defaultdict
from pathlib import Path

PASS="FORCED_FLOW_FULL_WINDOW_GAP_LEDGER_PASS"
REVIEW="FORCED_FLOW_FULL_WINDOW_GAP_LEDGER_REVIEW"
ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-next-primary-forced-flow-relative-dislocation-full-window-gap-completeness-protocol-v0.1.md"
FREEZE=ROOT/"docs/research/sc001-next-primary-forced-flow-relative-dislocation-full-window-gap-checker-freeze-v0.1.json"
START_MS=1790726400000
END_MS=1791331200000
WINDOW_MS=END_MS-START_MS
STAGE="SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3"

def fail(msg:str)->None: raise RuntimeError(msg)

def git_blob(p:Path)->str:
    return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()

def load_json(p:Path)->dict:
    if not p.is_file() or p.is_symlink(): fail(f"missing/invalid JSON: {p}")
    obj=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj,dict): fail("JSON object expected")
    return obj

def iter_jsonl(p:Path):
    if not p.is_file() or p.is_symlink(): fail(f"missing/invalid JSONL: {p}")
    with p.open("r",encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if not line.strip(): continue
            obj=json.loads(line)
            if not isinstance(obj,dict): fail(f"ledger line {n} not object")
            yield obj

def require_freeze()->dict:
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_FORCED_FLOW_FULL_WINDOW_GAP_CHECKER": fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()): fail("runner blob mismatch")
    if fr.get("protocol_git_blob_sha")!=git_blob(PROTOCOL): fail("protocol blob mismatch")
    if int(fr.get("window_start_ms") or 0)!=START_MS or int(fr.get("window_end_ms") or 0)!=END_MS: fail("window mismatch")
    if fr.get("real_window_readout_authorized") is not False: fail("real-readout firewall mismatch")
    return fr

def merge(rows):
    clean=[]
    for a,b,kind in rows:
        a=int(a); b=int(b)
        if b<a: fail("negative gap interval")
        if b<=START_MS or a>=END_MS: continue
        clean.append([max(a,START_MS),min(b,END_MS),{kind}])
    clean.sort(key=lambda x:(x[0],x[1]))
    out=[]
    for a,b,kinds in clean:
        if not out or a>out[-1][1]:
            out.append([a,b,set(kinds)])
        else:
            out[-1][1]=max(out[-1][1],b)
            out[-1][2].update(kinds)
    return [{"start_ms":a,"end_ms":b,"duration_ms":b-a,"kinds":sorted(k)} for a,b,k in out]

def reconstruct(state:dict,ledger:list[dict])->dict:
    if state.get("stage")!=STAGE: fail("collector stage mismatch")
    if tuple(state.get("symbols") or ())!=(
      "BTCUSDT","ETHUSDT","SOLUSDT","DOGEUSDT","ORDIUSDT","FILUSDT",
      "UNIUSDT","XRPUSDT","LTCUSDT","OPUSDT","BCHUSDT","SUIUSDT",
    ): fail("collector symbol universe mismatch")
    if int(state.get("source_qualified_symbols") or 0)!=12: fail("source-qualified symbols !=12")
    if state.get("strategy_outcomes_calculated") is not False: fail("collector outcome firewall mismatch")
    start=int(state.get("collector_start_ms") or 0)
    if start<=0 or start>START_MS: fail("collector did not predate window")
    close_marker=state.get("last_heartbeat_ms") or state.get("stopped_ms") or state.get("last_message_ms")
    if close_marker is None or int(close_marker)<END_MS: fail("collector state does not cover window close")

    rows=sorted(ledger,key=lambda r:int(r.get("ts_ms") or 0))
    counts=defaultdict(int)
    availability=None
    for r in rows:
        if r.get("stage")!=STAGE: fail(f"ledger stage mismatch: {r.get('stage')}")
        ts=int(r.get("ts_ms") or 0)
        if ts<=0: fail("ledger timestamp missing")
        ev=str(r.get("event") or "")
        counts[ev]+=1
        if ts<=START_MS:
            if ev=="SUBSCRIBED": availability=True
            elif ev in {"DISCONNECTED","STOPPED"}: availability=False

    if availability is None: fail("opening availability state unresolved")

    gaps=[]
    unavailable_start=None if availability else START_MS
    for r in rows:
        ts=int(r.get("ts_ms") or 0)
        ev=str(r.get("event") or "")
        if ts<=START_MS: 
            if ev=="PROCESS_RESTART_GAP" and r.get("start_ms") is not None and r.get("end_ms") is not None:
                gaps.append((int(r["start_ms"]),int(r["end_ms"]),"PROCESS_RESTART_GAP"))
            continue
        if ts>=END_MS: 
            if ev=="PROCESS_RESTART_GAP" and r.get("start_ms") is not None and r.get("end_ms") is not None:
                gaps.append((int(r["start_ms"]),int(r["end_ms"]),"PROCESS_RESTART_GAP"))
            continue
        if ev=="DISCONNECTED":
            if unavailable_start is None: unavailable_start=ts
        elif ev=="STOPPED":
            if unavailable_start is None: unavailable_start=ts
        elif ev=="SUBSCRIBED":
            if unavailable_start is not None:
                gaps.append((unavailable_start,ts,"CONNECTION_UNAVAILABLE"))
                unavailable_start=None
        elif ev=="PROCESS_RESTART_GAP":
            a=r.get("start_ms"); b=r.get("end_ms")
            if a is None or b is None: fail("process restart gap missing bounds")
            gaps.append((int(a),int(b),"PROCESS_RESTART_GAP"))

    if unavailable_start is not None:
        gaps.append((unavailable_start,END_MS,"CONNECTION_UNAVAILABLE"))

    for rec in state.get("process_restart_gaps") or []:
        if not isinstance(rec,dict) or rec.get("start_ms") is None or rec.get("end_ms") is None:
            fail("state process gap malformed")
        gaps.append((int(rec["start_ms"]),int(rec["end_ms"]),"STATE_PROCESS_RESTART_GAP"))

    merged=merge(gaps)
    total=sum(x["duration_ms"] for x in merged)
    return {
      "schema":"sc001.forced_flow_full_window_gap_readout.v0.1",
      "status":PASS,
      "window":{"start_ms":START_MS,"end_ms":END_MS,"duration_ms":WINDOW_MS},
      "collector_start_ms":start,
      "closing_marker_ms":int(close_marker),
      "source_qualified_symbols":12,
      "connection_event_counts":dict(sorted(counts.items())),
      "process_restart_count":int(state.get("process_restart_count") or 0),
      "merged_gap_count":len(merged),
      "merged_gap_ms":total,
      "gap_fraction":total/WINDOW_MS,
      "merged_gap_intervals":merged,
      "cluster_gap_padding_ms":5000,
      "outcome_firewall":{
        "liquidation_event_rows_opened":False,"clusters_constructed":False,
        "trade_archives_opened":False,"prices_opened":False,"basis_calculated":False,
        "returns_calculated":False,"pnl_calculated":False,"s0_executed":False,
        "collector_mutated":False
      }
    }

def write_json(path:Path,obj:dict)->None:
    if path.exists(): fail("output collision")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def write_jsonl(path:Path,rows:list[dict])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r,separators=(",",":"))+"\n")

def synthetic()->dict:
    state={
      "stage":STAGE,
      "symbols":["BTCUSDT","ETHUSDT","SOLUSDT","DOGEUSDT","ORDIUSDT","FILUSDT","UNIUSDT","XRPUSDT","LTCUSDT","OPUSDT","BCHUSDT","SUIUSDT"],
      "source_qualified_symbols":12,"strategy_outcomes_calculated":False,
      "collector_start_ms":START_MS-100000,"last_heartbeat_ms":END_MS+10000,
      "process_restart_count":1,
      "process_restart_gaps":[{"start_ms":START_MS+300000,"end_ms":START_MS+302000}],
    }
    rows=[
      {"stage":STAGE,"event":"SUBSCRIBED","ts_ms":START_MS-50000},
      {"stage":STAGE,"event":"DISCONNECTED","ts_ms":START_MS+100000},
      {"stage":STAGE,"event":"SUBSCRIBED","ts_ms":START_MS+105000},
      {"stage":STAGE,"event":"PROCESS_RESTART_GAP","ts_ms":START_MS+302000,"start_ms":START_MS+300000,"end_ms":START_MS+302000},
    ]
    r=reconstruct(state,rows)
    assert r["merged_gap_count"]==2
    assert r["merged_gap_ms"]==7000
    assert abs(r["gap_fraction"]-(7000/WINDOW_MS))<1e-15
    assert r["outcome_firewall"]["prices_opened"] is False
    bad=dict(state); bad["last_heartbeat_ms"]=END_MS-1
    try: reconstruct(bad,rows); fail("premature close accepted")
    except RuntimeError as e:
        if str(e)=="premature close accepted": raise
    return {"opening_state_pass":True,"disconnect_gap_pass":True,"process_gap_merge_pass":True,"closing_boundary_gate_pass":True}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["self-test","readout"],required=True)
    ap.add_argument("--state")
    ap.add_argument("--ledger")
    ap.add_argument("--out-dir",default=os.environ.get("BM_TEST_OUTPUT_DIR",os.environ.get("OUTPUT_DIR",str(Path.cwd()/"test-output"))))
    a=ap.parse_args()
    try:
        fr=require_freeze()
        checks=synthetic()
        if a.mode=="self-test":
            obj={"schema":"sc001.forced_flow_full_window_gap_checker_handshake.v0.1","status":PASS,"mode":"self-test","checks":checks,"real_window_inputs_opened":False}
            write_json(Path(a.out_dir)/"forced_flow_full_window_gap_checker_selftest.json",obj)
            print(PASS); return 0

        if int(time.time()*1000)<END_MS: fail("full-window readout locked until 2026-10-07T00:00:00Z")
        if fr.get("real_window_readout_authorized") is not True: fail("real-window readout not authorized by freeze")
        if not a.state or not a.ledger: fail("state/ledger required")
        obj=reconstruct(load_json(Path(a.state)),list(iter_jsonl(Path(a.ledger))))
        write_json(Path(a.out_dir)/"forced_flow_full_window_gap_readout.json",obj)
        print(PASS); print("merged_gap_count =",obj["merged_gap_count"]); print("merged_gap_ms =",obj["merged_gap_ms"]); return 0
    except Exception as exc:
        try: write_json(Path(a.out_dir)/"forced_flow_full_window_gap_checker_review.json",{"schema":"sc001.forced_flow_full_window_gap_checker.v0.1","status":REVIEW,"error":f"{type(exc).__name__}: {exc}","real_window_inputs_opened":False,"s0_executed":False})
        except Exception: pass
        print(REVIEW); print(f"{type(exc).__name__}: {exc}"); return 2

if __name__=="__main__":
    raise SystemExit(main())
