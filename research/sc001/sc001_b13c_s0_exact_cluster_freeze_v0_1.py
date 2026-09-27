#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ANALYZER_PATH=ROOT/"research/sc001/sc001_b13c_s0_source_only_cluster_census_v0_1.py"
EXPECTED_ANALYZER_SHA256="601252728e8fa7caf2d9c467d99e61296268a78879a42323725b67bac223db5b"
OFFICIAL_RESULT=ROOT/"docs/research/sc001-b13c-s0-real-event-only-cluster-census-result-v0.1.json"
EXPECTED_OFFICIAL_RESULT_SHA256="fd08901e77bb73c00bb53826e925b2124d52e05d6c8f45cdc154b1c57a2ab1eb"

EXPECTED={
    "unique_events_in_window":32381,
    "total_raw_clusters_before_filters":10734,
    "clusters_under_min_events":8743,
    "mixed_side_clusters_excluded":83,
    "gap_censored_clusters":3,
    "eligible_cluster_count":1905,
    "required_price_archive_count":76,
    "merged_source_gap_count":15,
    "merged_source_gap_ms":324430,
}

PASS="B13C_S0_EXACT_CLUSTER_FREEZE_MANIFEST_PASS"


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
    if entrypoint!=current or package_root not in current.parents:
        fail("Runner launcher binding mismatch")


def load_analyzer():
    actual=sha256_file(ANALYZER_PATH)
    if actual!=EXPECTED_ANALYZER_SHA256:
        fail(f"analyzer SHA mismatch: {actual}")
    spec=importlib.util.spec_from_file_location("b13c_s0_cluster_analyzer",ANALYZER_PATH)
    if spec is None or spec.loader is None:
        fail("cannot load analyzer module")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-root",default="/work/run/input/b13cs0")
    ap.add_argument("--out-dir",default=os.environ.get("OUTPUT_DIR","/work/run/output"))
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)

    if sha256_file(OFFICIAL_RESULT)!=EXPECTED_OFFICIAL_RESULT_SHA256:
        fail("official census result SHA mismatch")
    official=json.loads(OFFICIAL_RESULT.read_text(encoding="utf-8"))
    if official.get("status")!="B13C_S0_SOURCE_ONLY_CLUSTER_CENSUS_PASS":
        fail("official census result status mismatch")

    mod=load_analyzer()
    root=Path(a.data_root).resolve()
    state=mod.load_json(root/"collector_state.json")
    gaps,event_counts=mod.build_source_gaps(state,root/"connection"/"connection_events.jsonl")
    events,event_diag=mod.parse_events(root)
    clustered=mod.cluster_events(events,gaps)

    observed={
        "unique_events_in_window":event_diag["unique_events_in_window"],
        "total_raw_clusters_before_filters":clustered["total_raw_clusters_before_filters"],
        "clusters_under_min_events":clustered["clusters_under_min_events"],
        "mixed_side_clusters_excluded":clustered["mixed_side_clusters_excluded"],
        "gap_censored_clusters":clustered["gap_censored_clusters"],
        "eligible_cluster_count":clustered["eligible_cluster_count"],
        "required_price_archive_count":clustered["required_price_archive_count"],
        "merged_source_gap_count":len(gaps),
        "merged_source_gap_ms":sum(b-a for a,b in gaps),
    }
    if observed!=EXPECTED:
        fail(f"aggregate census mismatch: {observed}")

    official_cc=official.get("cluster_census") or {}
    for key in (
        "total_raw_clusters_before_filters","clusters_under_min_events",
        "mixed_side_clusters_excluded","gap_censored_clusters",
        "eligible_cluster_count","required_price_archive_count"
    ):
        if official_cc.get(key)!=observed[key]:
            fail(f"official result mismatch: {key}")
    if official.get("event_diagnostics",{}).get("unique_events_in_window")!=EXPECTED["unique_events_in_window"]:
        fail("official unique-event count mismatch")
    if official.get("required_price_archives")!=clustered["required_price_archives"]:
        fail("required price archive identity list mismatch")

    exact=[]
    for i,c in enumerate(clustered["clusters"],1):
        if c["cluster_id"]!=f"S0C{i:06d}":
            fail("cluster ordinal mismatch")
        end_ms=int(c["end_ms"])
        exact.append({
            "cluster_id":c["cluster_id"],
            "symbol":c["symbol"],
            "liquidation_side":c["side"],
            "reversal_sign":1 if c["side"]=="LONG_LIQUIDATED" else -1,
            "start_ms":int(c["start_ms"]),
            "end_ms":end_ms,
            "event_count":int(c["event_count"]),
            "entry_bucket":{
                "start_ms":end_ms+1000,
                "end_ms_exclusive":end_ms+2000,
            },
            "exit_bucket":{
                "start_ms":end_ms+31000,
                "end_ms_exclusive":end_ms+32000,
            },
            "required_archive_days":list(c["required_archive_days"]),
        })

    result={
        "schema":"sc001.b13c_s0_exact_cluster_freeze_manifest.v0.1",
        "status":PASS,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "parent_census_result_sha256":EXPECTED_OFFICIAL_RESULT_SHA256,
        "analyzer_sha256":EXPECTED_ANALYZER_SHA256,
        "frozen_interval":{
            "start_ms":mod.START_MS,
            "end_ms":mod.END_MS,
        },
        "aggregate_integrity":observed,
        "eligible_clusters":exact,
        "required_price_archives":clustered["required_price_archives"],
        "price_data_opened":False,
        "returns_calculated":False,
        "per_symbol_performance_ranked":False,
        "threshold_tuned":False,
        "pnl_calculated":False,
        "network_calls_performed":False,
        "collector_mutation_performed":False,
        "next_state":"STREAM_EXACT_76_PRICE_ARCHIVES_AND_EXTRACT_FROZEN_ENTRY_EXIT_ANCHORS",
    }
    out=Path(a.out_dir).resolve()/"b13c_s0_exact_cluster_freeze_manifest.json"
    atomic_json(out,result)
    print(PASS)
    print("eligible_clusters =",len(exact))
    print("required_price_archives =",len(clustered["required_price_archives"]))
    print("price/returns/PnL = CLOSED")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
