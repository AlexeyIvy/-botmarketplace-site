#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

EXPECTED_DIR="SC001_B14A_P0_20260925"
ALLOWED_STAGES={
    "SC001-B14A-P0-PROSPECTIVE-TRADE-COLLECTOR-V0.1",
    "SC001-B14A-P0-PROSPECTIVE-TRADE-COLLECTOR-V0.3",
}
PASS="B14A_P0_STATE_ONLY_DIAGNOSTIC_PASS"


def fail(msg:str)->None:
    raise RuntimeError(msg)


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path:Path,obj:dict)->None:
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


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--state-path",default="/work/run/input/b14astate/collector_state.json")
    ap.add_argument("--out-dir",default=os.environ.get("OUTPUT_DIR","/work/run/output"))
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)

    p=Path(a.state_path).resolve()
    if not p.is_file() or p.is_symlink():
        fail("collector_state materialized input missing/invalid")
    obj=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail("collector_state is not a JSON object")
    if obj.get("stage") not in ALLOWED_STAGES:
        fail(f"unexpected collector stage: {obj.get('stage')}")

    result={
        "schema":"sc001.b14a_p0_state_only_diagnostic.v0.1",
        "status":PASS,
        "state_file_sha256":sha256_file(p),
        "state_file_size_bytes":p.stat().st_size,
        "collector_state":{
            "stage":obj.get("stage"),
            "version":obj.get("version"),
            "status":obj.get("status"),
            "subscription_ack":obj.get("subscription_ack"),
            "raw_trade_messages":obj.get("raw_trade_messages"),
            "normalized_trade_rows":obj.get("normalized_trade_rows"),
            "invalid_trade_rows":obj.get("invalid_trade_rows"),
            "reconnect_count":obj.get("reconnect_count"),
            "process_restart_count":obj.get("process_restart_count"),
            "connection_gap_count":len(obj.get("connection_gaps") or []),
            "process_restart_gap_count":len(obj.get("process_restart_gaps") or []),
            "finished_ms":obj.get("finished_ms"),
            "finished_utc":obj.get("finished_utc"),
            "basis_calculated":obj.get("basis_calculated"),
            "convergence_calculated":obj.get("convergence_calculated"),
            "pnl_calculated":obj.get("pnl_calculated"),
        },
        "raw_trade_data_read":False,
        "price_data_read":False,
        "outcome_calculated":False,
        "collector_mutation_performed":False,
        "network_calls_performed":False,
    }
    atomic_json(Path(a.out_dir).resolve()/"b14a_p0_state_only_diagnostic_manifest.json",result)
    print(PASS)
    print("collector_status =",obj.get("status"))
    print("raw_trade_messages =",obj.get("raw_trade_messages"))
    print("normalized_trade_rows =",obj.get("normalized_trade_rows"))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
