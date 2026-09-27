#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ANALYZER=ROOT/"research/sc001/sc001_b13c_s0_outcome_analyzer_v0_1.py"
INPUT_ROOT=Path("/work/run/input/b13coutcome")
OUT=Path("/work/run/output")
OUTCOME=OUT/"b13c_s0_simple_reversal_outcome.json"
BOOTSTRAP=OUT/"b13c_s0_real_outcome_bootstrap_manifest.json"

EXPECTED_ANALYZER_SHA256="45724b5670caa1b264b1d8c455e9dc6271b4e9bb600320f25c25a76f28202cdb"
EXPECTED_ANCHOR_SHA256="5f84f40a91c3a7bc57bf3c4e878a53130ef696a28be162c014c10f8253223a1e"
EXPECTED_EXTRACTION_SHA256="79db43a19249c8f56f886cf01616f3e56704d4a8fc8e5c5e03609254b2de1acf"

ALLOWED={
    "B13C_S0_SIMPLE_REVERSAL_HEADROOM_SURVIVE",
    "B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT",
    "B13C_S0_DEFER_SAMPLE",
}
PASS="B13C_S0_REAL_OUTCOME_BOOTSTRAP_PASS"
REVIEW="B13C_S0_REAL_OUTCOME_BOOTSTRAP_REVIEW"


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
    tmp.replace(path)


def main()->int:
    checks={}
    try:
        actual=sha256_file(ANALYZER)
        checks["analyzer_sha256"]=actual
        if actual!=EXPECTED_ANALYZER_SHA256:
            raise RuntimeError("analyzer SHA mismatch")

        anchors=INPUT_ROOT/"price_anchors.jsonl"
        extraction=INPUT_ROOT/"price_anchor_extraction_manifest.json"
        for p in (anchors,extraction):
            if not p.is_file() or p.is_symlink():
                raise RuntimeError(f"required input missing/invalid: {p.name}")

        a_sha=sha256_file(anchors)
        e_sha=sha256_file(extraction)
        checks["price_anchors_sha256"]=a_sha
        checks["extraction_manifest_sha256"]=e_sha
        if a_sha!=EXPECTED_ANCHOR_SHA256:
            raise RuntimeError("price_anchors SHA mismatch")
        if e_sha!=EXPECTED_EXTRACTION_SHA256:
            raise RuntimeError("extraction manifest SHA mismatch")

        proc=subprocess.run(
            [
                sys.executable,str(ANALYZER),
                "--mode","outcome",
                "--input-root",str(INPUT_ROOT),
                "--out-dir",str(OUT),
            ],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        checks["returncode"]=proc.returncode
        checks["stdout_tail"]=proc.stdout[-12000:]
        checks["stderr_tail"]=proc.stderr[-12000:]
        if proc.stdout:
            print(proc.stdout,end="")
        if proc.stderr:
            print(proc.stderr,file=sys.stderr,end="")
        if proc.returncode!=0:
            raise RuntimeError(f"outcome analyzer rc={proc.returncode}")
        if not OUTCOME.is_file():
            raise RuntimeError("outcome artifact missing")

        result=json.loads(OUTCOME.read_text(encoding="utf-8"))
        status=result.get("status")
        if status not in ALLOWED:
            raise RuntimeError(f"unexpected outcome status: {status}")

        pooled=result.get("pooled") or {}
        if int(pooled.get("n") or 0)!=1793:
            raise RuntimeError(f"valid sample mismatch: {pooled.get('n')}")
        days=result.get("complete_days") or []
        if len(days)!=6:
            raise RuntimeError("complete-day count mismatch")
        gates=result.get("gates") or {}
        for k in ("sample_ge_100","median_ge_30bps","positive_share_ge_55pct","positive_complete_days_ge_4_of_6"):
            if not isinstance(gates.get(k),bool):
                raise RuntimeError(f"gate missing/non-bool: {k}")
        for k,expected in (
            ("gross_headroom_only",True),
            ("per_cluster_returns_emitted",False),
            ("per_symbol_performance_ranked",False),
            ("liquidation_size_stratified",False),
            ("alternate_horizons_tested",False),
            ("pnl_calculated",False),
        ):
            if result.get(k) is not expected:
                raise RuntimeError(f"outcome firewall mismatch: {k}")

        checks["outcome_sha256"]=sha256_file(OUTCOME)
        atomic_json(BOOTSTRAP,{
            "schema":"sc001.b13c_s0_real_outcome_bootstrap_result.v0.1",
            "status":PASS,
            "classification":status,
            "checks":checks,
            "price_anchors_sha256":a_sha,
            "extraction_manifest_sha256":e_sha,
            "outcome_sha256":checks["outcome_sha256"],
            "valid_price_clusters":1793,
            "pnl_calculated":False,
            "network_calls_performed":False,
            "next_state":"REVIEW_FROZEN_S0_OUTCOME_AND_APPLY_BINDING_PROTOCOL_CONSEQUENCE",
        })
        print(PASS)
        return 0
    except Exception as exc:
        atomic_json(BOOTSTRAP,{
            "schema":"sc001.b13c_s0_real_outcome_bootstrap_result.v0.1",
            "status":REVIEW,
            "error":f"{type(exc).__name__}: {exc}",
            "checks":checks,
            "pnl_calculated":False,
            "network_calls_performed":False,
            "next_state":"STOP_AND_REVIEW_B13C_S0_REAL_OUTCOME",
        })
        print(REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2


if __name__=="__main__":
    raise SystemExit(main())
