#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_STAGES={
    "SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.1",
    "SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3",
}
PASS="B13C_SOURCE_QUALITY_STATE_CENSUS_PASS"


def fail(msg:str)->None:
    raise RuntimeError(msg)


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


def ms_to_iso(ms):
    if ms is None:
        return None
    return datetime.fromtimestamp(int(ms)/1000,tz=timezone.utc).isoformat()


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--state-path",default="/work/run/input/b13cstate/collector_state.json")
    ap.add_argument("--out-dir",default=os.environ.get("OUTPUT_DIR","/work/run/output"))
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)

    p=Path(a.state_path).resolve()
    if not p.is_file() or p.is_symlink():
        fail("B13-C collector_state missing/invalid")
    state=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(state,dict):
        fail("B13-C collector_state not object")
    if state.get("stage") not in ALLOWED_STAGES:
        fail(f"unexpected B13-C stage: {state.get('stage')}")

    start=state.get("collector_start_ms")
    heartbeat=state.get("last_heartbeat_ms") or state.get("stopped_ms") or state.get("last_message_ms")
    elapsed_ms=None
    elapsed_days=None
    if start is not None and heartbeat is not None:
        elapsed_ms=max(0,int(heartbeat)-int(start))
        elapsed_days=elapsed_ms/86_400_000.0

    total_events=int(state.get("total_normalized_events") or 0)
    invalid=int(state.get("invalid_event_count") or 0)
    raw=int(state.get("total_raw_messages") or 0)
    reconnects=int(state.get("reconnect_count") or 0)
    gap_ms=int(state.get("cumulative_gap_ms") or 0)
    process_gap_ms=int(state.get("cumulative_process_gap_ms") or 0)
    process_restarts=int(state.get("process_restart_count") or 0)
    qualified=int(state.get("source_qualified_symbols") or 0)

    result={
        "schema":"sc001.b13c_source_quality_state_census.v0.1",
        "status":PASS,
        "collector":{
            "stage":state.get("stage"),
            "version":state.get("version"),
            "status":state.get("status"),
            "connection_status":state.get("connection_status"),
            "source_qualified_symbols":qualified,
            "collector_start_ms":start,
            "collector_start_utc":ms_to_iso(start),
            "last_heartbeat_ms":heartbeat,
            "last_heartbeat_utc":ms_to_iso(heartbeat),
            "observation_elapsed_ms":elapsed_ms,
            "observation_elapsed_days":elapsed_days,
            "total_raw_messages":raw,
            "total_normalized_events":total_events,
            "invalid_event_count":invalid,
            "reconnect_count":reconnects,
            "cumulative_connection_gap_ms":gap_ms,
            "process_restart_count":process_restarts,
            "cumulative_process_gap_ms":process_gap_ms,
            "strategy_outcomes_calculated":state.get("strategy_outcomes_calculated"),
        },
        "derived_source_diagnostics":{
            "events_per_observed_day_for_sufficiency_only":(
                total_events/elapsed_days if elapsed_days and elapsed_days>0 else None
            ),
            "invalid_event_fraction_of_normalized_plus_invalid":(
                invalid/(total_events+invalid) if (total_events+invalid)>0 else None
            ),
            "connection_gap_fraction_of_observation":(
                gap_ms/elapsed_ms if elapsed_ms and elapsed_ms>0 else None
            ),
            "process_gap_fraction_of_observation":(
                process_gap_ms/elapsed_ms if elapsed_ms and elapsed_ms>0 else None
            ),
        },
        "forbidden_outcomes_opened":False,
        "per_symbol_frequency_read":False,
        "liquidation_size_distribution_read":False,
        "long_short_predictive_behavior_read":False,
        "post_event_returns_read":False,
        "pre_event_returns_read":False,
        "threshold_selected":False,
        "execution_or_pnl_calculated":False,
        "collector_mutation_performed":False,
        "network_calls_performed":False,
    }
    atomic_json(Path(a.out_dir).resolve()/"b13c_source_quality_state_census_manifest.json",result)
    print(PASS)
    print("collector_status =",state.get("status"))
    print("source_qualified_symbols =",qualified)
    print("observation_elapsed_days =",elapsed_days)
    print("total_normalized_events =",total_events)
    print("reconnect_count =",reconnects)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
