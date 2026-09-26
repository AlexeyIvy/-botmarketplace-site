#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

STAGE="SC001-B14A-P0-PROSPECTIVE-TRADE-COLLECTOR-V0.3"
PASS="B14A_P0_CONNECTION_LEDGER_DIAGNOSTIC_PASS"


def fail(msg:str)->None:
    raise RuntimeError(msg)


def iter_jsonl(path:Path):
    with path.open("r",encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if not line.strip():
                continue
            try:
                obj=json.loads(line)
            except Exception as exc:
                fail(f"invalid JSONL line {n}: {exc}")
            if not isinstance(obj,dict):
                fail(f"JSON object required line {n}")
            yield obj


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
    if entrypoint!=current or package_root not in current.parents:
        fail("Runner launcher binding mismatch")


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--ledger-path",default="/work/run/input/b14aconn/connection_events.jsonl")
    ap.add_argument("--out-dir",default=os.environ.get("OUTPUT_DIR","/work/run/output"))
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)

    p=Path(a.ledger_path).resolve()
    if not p.is_file() or p.is_symlink():
        fail("connection_events input missing/invalid")

    events=Counter()
    error_signatures=Counter()
    first_ts=None
    last_ts=None
    rows=0
    for row in iter_jsonl(p):
        rows+=1
        if row.get("stage")!=STAGE:
            fail(f"stage mismatch at row {rows}")
        event=str(row.get("event") or "")
        if not event:
            fail(f"event missing at row {rows}")
        events[event]+=1
        ts=int(row.get("ts_ms") or 0)
        if ts>0:
            first_ts=ts if first_ts is None else min(first_ts,ts)
            last_ts=ts if last_ts is None else max(last_ts,ts)
        err=str(row.get("error") or "").strip()
        if err:
            # Keep only diagnostic class/message, never strategy data.
            if len(err)>500:
                err=err[:500]
            error_signatures[err]+=1

    result={
        "schema":"sc001.b14a_p0_connection_ledger_diagnostic.v0.1",
        "status":PASS,
        "rows":rows,
        "event_counts":dict(sorted(events.items())),
        "first_ts_ms":first_ts,
        "last_ts_ms":last_ts,
        "error_signatures":[
            {"error":e,"count":c}
            for e,c in sorted(error_signatures.items(),key=lambda kv:(-kv[1],kv[0]))
        ][:20],
        "price_data_read":False,
        "raw_trade_data_read":False,
        "headroom_calculated":False,
        "collector_mutation_performed":False,
        "network_calls_performed":False,
    }
    atomic_json(Path(a.out_dir).resolve()/"b14a_p0_connection_ledger_diagnostic_manifest.json",result)
    print(PASS)
    print("rows =",rows)
    print("event_counts =",json.dumps(result["event_counts"],sort_keys=True))
    print("error_signature_count =",len(result["error_signatures"]))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
