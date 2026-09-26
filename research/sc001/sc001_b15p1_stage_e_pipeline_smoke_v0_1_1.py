#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from pathlib import Path
from typing import Any

STAGE="SC001-B15P1-NONPRICE-TRANSFERABILITY-COLLECTOR-V0.1.4"
SELFTEST_PASS="B15P1_STAGE_E_PIPELINE_SMOKE_V011_SELF_TEST_PASS"
REAL_PASS="B15P1_STAGE_E_REAL_DATA_PIPELINE_SMOKE_PASS"

def fail(x): raise RuntimeError(x)

def load_json(p:Path)->Any:
    return json.loads(p.read_text(encoding="utf-8"))

def iter_jsonl(p:Path):
    if not p.exists(): return
    with p.open("r",encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if not line.strip(): continue
            try: obj=json.loads(line)
            except Exception as e: fail(f"invalid JSONL {p}:{n}:{e}")
            if not isinstance(obj,dict): fail(f"JSON object required {p}:{n}")
            yield obj

def chain_hash(prev,by,ok,norm,route):
    return hashlib.sha256("|".join([prev,by,ok,norm,route]).encode()).hexdigest()

def atomic_json(p:Path,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_name(p.name+".tmp")
    q.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(q,p)

def append_jsonl(p:Path,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8") as f:
        for x in rows: f.write(json.dumps(x,separators=(",",":"))+"\n")

def check_state_manifest(root:Path):
    sp=root/"collector_state.json"; mp=root/"collector_manifest.json"
    if not sp.is_file() or not mp.is_file(): fail("collector state/manifest missing")
    s=load_json(sp); m=load_json(mp)
    if s.get("stage")!=STAGE or s.get("version")!="0.1.4": fail("collector state identity mismatch")
    if s.get("status")!="B15P1_NONPRICE_COLLECTION_RUNNING": fail("collector not running in snapshot")
    if s.get("price_data_collected") is not False or s.get("pnl_calculated") is not False: fail("state firewall mismatch")
    if m.get("price_data_authorized") is not False or m.get("pnl_authorized") is not False: fail("manifest firewall mismatch")
    if int(m.get("fast_cadence_seconds") or 0)!=15: fail("cadence mismatch")
    if int(s.get("process_epoch") or 0)<1: fail("process epoch invalid")
    return s,m

def check_poll_file(p:Path):
    rows=[]; prev=None; both=0
    for x in iter_jsonl(p):
        if x.get("poll_chain_hash") is None: continue
        if x.get("price_data_collected") is not False: fail("poll price firewall mismatch")
        v=x.get("venues") or {}; by=v.get("BYBIT") or {}; ok=v.get("OKX") or {}
        h=chain_hash(str(x.get("previous_poll_chain_hash") or ""),
                     str(by.get("raw_body_sha256") or "0"*64),
                     str(ok.get("raw_body_sha256") or "0"*64),
                     str(x.get("normalized_state_sha256") or ""),
                     str(x.get("route_state_sha256") or ""))
        if h!=x.get("poll_chain_hash"): fail("poll chain hash mismatch")
        if prev is not None and x.get("previous_poll_chain_hash")!=prev: fail("poll chain continuity mismatch")
        prev=str(x["poll_chain_hash"])
        if by.get("status")=="OK" and ok.get("status")=="OK": both+=1
        rows.append(x)
    if len(rows)<2: fail("fewer than two scheduled poll rows")
    slots=[int(x["scheduled_slot_ms"]) for x in rows]
    if slots!=sorted(set(slots)): fail("scheduled slots not unique/increasing")
    return {"scheduled_rows":len(rows),"both_venue_valid_rows":both,
            "first_slot_ms":slots[0],"last_slot_ms":slots[-1],
            "terminal_poll_chain_hash":prev}

def parse_events(root:Path):
    total=route=0
    d=root/"events"
    if d.exists():
        for p in sorted(d.glob("*.jsonl")):
            for x in iter_jsonl(p):
                total+=1
                if str(x.get("event") or "").startswith("ROUTE_"): route+=1
    return total,route

def parse_fees(root:Path):
    total=ok=0; by=set(); ox=set()
    d=root/"fees"
    if d.exists():
        for p in sorted(d.glob("*/*.jsonl")):
            for x in iter_jsonl(p):
                total+=1
                if x.get("ok") is True:
                    ok+=1
                    venue=str(x.get("venue") or ""); inst=str(x.get("instrument") or "")
                    if venue=="BYBIT": by.add(inst)
                    elif venue=="OKX": ox.add(inst)
    return {"rows":total,"successful_rows":ok,
            "successful_bybit_instruments":len(by),
            "successful_okx_instruments":len(ox)}

def smoke(root:Path,out:Path,quiet=False):
    s,m=check_state_manifest(root)
    files=sorted((root/"polls").glob("*.jsonl"))
    if not files: fail("no poll files")
    pc=check_poll_file(files[-1])
    ev,rev=parse_events(root); fees=parse_fees(root)
    if s.get("last_fee_refresh_completed_ms") is not None:
        if fees["successful_bybit_instruments"]<1 or fees["successful_okx_instruments"]<1:
            fail("fee refresh completion marker exists but no successful fee rows for both venues")
    result={
      "schema":"sc001.b15.p1_stage_e_pipeline_smoke_result.v0.1",
      "status":REAL_PASS,
      "collector_snapshot":{
        "status":s.get("status"),"process_epoch":s.get("process_epoch"),
        "process_restart_count":s.get("process_restart_count"),
        "poll_count":s.get("poll_count"),"invalid_poll_count":s.get("invalid_poll_count"),
        "missed_poll_slots":s.get("missed_poll_slots"),"source_gap_count":s.get("source_gap_count"),
        "last_fee_refresh_completed_ms":s.get("last_fee_refresh_completed_ms")},
      "collector_binding":{
        "runner_sha256":m.get("runner_sha256"),"library_sha256":m.get("library_sha256"),
        "route_graph_sha256":m.get("route_graph_sha256"),
        "capability_snapshot_sha256":m.get("capability_snapshot_sha256"),
        "fast_cadence_seconds":m.get("fast_cadence_seconds")},
      "latest_poll_file":files[-1].name,"latest_poll_check":pc,
      "events_rows_parsed":ev,"route_event_rows_parsed":rev,"fee_parse":fees,
      "price_data_used":False,"pnl_data_used":False,
      "opportunity_rate_inference_performed":False,
      "collector_mutation_performed":False,"network_calls_performed":False}
    atomic_json(out/"stage_e_pipeline_smoke_manifest.json",result)
    if not quiet: print(REAL_PASS)
    return result

def validate_runner_launch_args(package_root_arg, entrypoint_arg):
    if (package_root_arg is None) != (entrypoint_arg is None):
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

def selftest():
    assert len(chain_hash("0"*64,"1"*64,"2"*64,"3"*64,"4"*64))==64
    current=Path(__file__).resolve()
    validate_runner_launch_args(str(current.parents[2]),str(current))
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); (root/"polls").mkdir()
        atomic_json(root/"collector_state.json",{
          "stage":STAGE,"version":"0.1.4","status":"B15P1_NONPRICE_COLLECTION_RUNNING",
          "process_epoch":1,"process_restart_count":0,"poll_count":2,"invalid_poll_count":0,
          "missed_poll_slots":0,"source_gap_count":0,"last_fee_refresh_completed_ms":None,
          "price_data_collected":False,"pnl_calculated":False})
        atomic_json(root/"collector_manifest.json",{
          "stage":STAGE,"version":"0.1.4","fast_cadence_seconds":15,
          "price_data_authorized":False,"pnl_authorized":False})
        prev="0"*64; rows=[]
        for slot in (15000,30000):
            b,o,n,r="1"*64,"2"*64,"3"*64,"4"*64
            h=chain_hash(prev,b,o,n,r)
            rows.append({"scheduled_slot_ms":slot,
              "venues":{"BYBIT":{"status":"OK","raw_body_sha256":b},
                        "OKX":{"status":"OK","raw_body_sha256":o}},
              "normalized_state_sha256":n,"route_state_sha256":r,
              "previous_poll_chain_hash":prev,"poll_chain_hash":h,
              "price_data_collected":False})
            prev=h
        append_jsonl(root/"polls"/"2099-01-01.jsonl",rows)
        x=smoke(root,root/"out",quiet=True)
        assert x["status"]==REAL_PASS and x["latest_poll_check"]["both_venue_valid_rows"]==2
    print(SELFTEST_PASS)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","smoke"),default="self-test")
    ap.add_argument("--data-root")
    ap.add_argument("--out-dir",default=os.environ.get("OUTPUT_DIR","/work/run/output"))
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_runner_launch_args(a._runner_package_root,a._runner_entrypoint)
    if a.mode=="self-test": selftest(); return 0
    if not a.data_root: fail("--data-root required for smoke")
    root=Path(a.data_root).resolve()
    if not root.is_dir(): fail("data root missing")
    smoke(root,Path(a.out_dir).resolve()); return 0

if __name__=="__main__":
    raise SystemExit(main())
