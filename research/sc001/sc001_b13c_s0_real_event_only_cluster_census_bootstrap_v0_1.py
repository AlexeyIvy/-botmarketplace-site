#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ANALYZER=ROOT/"research/sc001/sc001_b13c_s0_source_only_cluster_census_v0_1.py"
INPUT_ROOT=Path("/work/run/input/b13cs0")
OUT=Path("/work/run/output")
CENSUS_MANIFEST=OUT/"b13c_s0_source_only_cluster_census_manifest.json"
BOOTSTRAP_MANIFEST=OUT/"b13c_s0_real_event_only_cluster_census_bootstrap_manifest.json"

EXPECTED_ANALYZER_SHA256="601252728e8fa7caf2d9c467d99e61296268a78879a42323725b67bac223db5b"
CENSUS_PASS="B13C_S0_SOURCE_ONLY_CLUSTER_CENSUS_PASS"
BOOTSTRAP_PASS="B13C_S0_REAL_EVENT_ONLY_CLUSTER_CENSUS_BOOTSTRAP_PASS"
BOOTSTRAP_REVIEW="B13C_S0_REAL_EVENT_ONLY_CLUSTER_CENSUS_BOOTSTRAP_REVIEW"

REQUIRED=[
    "collector_state.json",
    "connection/connection_events.jsonl",
    "events/2026-09-19.jsonl",
    "events/2026-09-20.jsonl",
    "events/2026-09-21.jsonl",
    "events/2026-09-22.jsonl",
    "events/2026-09-23.jsonl",
    "events/2026-09-24.jsonl",
    "events/2026-09-25.jsonl",
    "events/2026-09-26.jsonl",
]


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def write(obj:dict)->None:
    OUT.mkdir(parents=True,exist_ok=True)
    BOOTSTRAP_MANIFEST.write_text(
        json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf-8"
    )


def main()->int:
    checks={}
    try:
        actual=sha256_file(ANALYZER)
        checks["analyzer_sha256"]=actual
        if actual!=EXPECTED_ANALYZER_SHA256:
            raise RuntimeError("analyzer SHA mismatch")
        compile(ANALYZER.read_text(encoding="utf-8"),str(ANALYZER),"exec")
        checks["analyzer_compile"]=True

        snapshot={}
        for rel in REQUIRED:
            p=INPUT_ROOT/rel
            if not p.is_file() or p.is_symlink():
                raise RuntimeError(f"required input missing/invalid: {rel}")
            if p.stat().st_size<=0:
                raise RuntimeError(f"required input empty: {rel}")
            snapshot[rel]={"sha256":sha256_file(p),"size_bytes":p.stat().st_size}
        checks["input_snapshot"]=snapshot

        proc=subprocess.run(
            [
                sys.executable,str(ANALYZER),
                "--mode","census",
                "--data-root",str(INPUT_ROOT),
                "--out-dir",str(OUT),
            ],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
            timeout=180,
        )
        checks["analyzer_returncode"]=proc.returncode
        checks["stdout_tail"]=proc.stdout[-12000:]
        checks["stderr_tail"]=proc.stderr[-12000:]
        if proc.stdout:
            print(proc.stdout,end="")
        if proc.stderr:
            print(proc.stderr,file=sys.stderr,end="")
        if proc.returncode!=0:
            raise RuntimeError(f"cluster census rc={proc.returncode}")
        if CENSUS_PASS not in proc.stdout:
            raise RuntimeError("cluster census PASS token missing")
        if not CENSUS_MANIFEST.is_file():
            raise RuntimeError("cluster census manifest missing")

        manifest=json.loads(CENSUS_MANIFEST.read_text(encoding="utf-8"))
        if manifest.get("status")!=CENSUS_PASS:
            raise RuntimeError("cluster census manifest status mismatch")
        for key in (
            "price_data_opened","returns_calculated","per_symbol_performance_ranked",
            "liquidation_size_distribution_read","threshold_tuned","pnl_calculated",
            "collector_mutation_performed","network_calls_performed",
        ):
            if manifest.get(key) is not False:
                raise RuntimeError(f"firewall mismatch: {key}")

        checks["census_manifest_sha256"]=sha256_file(CENSUS_MANIFEST)
        write({
            "schema":"sc001.b13c_s0_real_event_only_cluster_census_bootstrap_result.v0.1",
            "status":BOOTSTRAP_PASS,
            "checks":checks,
            "input_snapshot":snapshot,
            "census_manifest_sha256":checks["census_manifest_sha256"],
            "price_data_opened":False,
            "returns_calculated":False,
            "pnl_calculated":False,
            "network_calls_performed":False,
            "collector_mutation_performed":False,
            "next_state":manifest.get("next_state"),
        })
        print(BOOTSTRAP_PASS)
        return 0
    except Exception as exc:
        write({
            "schema":"sc001.b13c_s0_real_event_only_cluster_census_bootstrap_result.v0.1",
            "status":BOOTSTRAP_REVIEW,
            "error":f"{type(exc).__name__}: {exc}",
            "checks":checks,
            "price_data_opened":False,
            "returns_calculated":False,
            "pnl_calculated":False,
            "network_calls_performed":False,
            "collector_mutation_performed":False,
            "next_state":"STOP_AND_REVIEW_B13C_S0_EVENT_ONLY_CENSUS",
        })
        print(BOOTSTRAP_REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2


if __name__=="__main__":
    raise SystemExit(main())
