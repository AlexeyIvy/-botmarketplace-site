#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
MASTER=ROOT/"docs/research/artifacts/b13c-s0/exact-cluster-freeze-v0.1/master-index.json"
EXPECTED_MASTER_SHA256="0636ac25d6b7a484a4a9959f256aa57e0a1ead7f4e228423715f688b194fb87b"
INPUT_ROOT=Path("/work/run/input/b13canchors")
MANIFEST=INPUT_ROOT/"price_anchor_extraction_manifest.json"
ANCHORS=INPUT_ROOT/"price_anchors.jsonl"
OUT=Path("/work/run/output")/"b13c_s0_price_anchor_dataset_freeze_manifest.json"

EXPECTED_CLUSTER_COUNT=1905
EXPECTED_ARCHIVE_COUNT=76
EXPECTED_VALID=1793
EXPECTED_MISSING_ENTRY=25
EXPECTED_MISSING_EXIT=75
EXPECTED_MISSING_BOTH=12
EXPECTED_TOTAL_BYTES=2633144445
PASS="B13C_S0_PRICE_ANCHOR_DATASET_FREEZE_PASS"


def fail(msg:str)->None:
    raise RuntimeError(msg)


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path:Path)->dict[str,Any]:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail(f"JSON object required: {path}")
    return obj


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
        fail("Runner launcher package-root mismatch")


def canonical_clusters()->list[dict[str,Any]]:
    if sha256_file(MASTER)!=EXPECTED_MASTER_SHA256:
        fail("canonical master SHA mismatch")
    m=load_json(MASTER)
    rows=[]
    for expected_idx,ch in enumerate(m.get("chunks") or [],1):
        if int(ch.get("part_index") or 0)!=expected_idx:
            fail("canonical chunk index mismatch")
        p=ROOT/str(ch["path"])
        if sha256_file(p)!=ch.get("sha256"):
            fail(f"canonical chunk SHA mismatch: {p}")
        part=load_json(p)
        r=part.get("eligible_clusters") or []
        if len(r)!=int(ch.get("cluster_count") or -1):
            fail("canonical chunk row-count mismatch")
        rows.extend(r)
    if len(rows)!=EXPECTED_CLUSTER_COUNT:
        fail(f"canonical cluster count={len(rows)}")
    for i,row in enumerate(rows,1):
        if row.get("cluster_id")!=f"S0C{i:06d}":
            fail(f"canonical ID discontinuity {i}")
    return rows


def parse_anchors(canon:list[dict[str,Any]])->tuple[list[dict[str,Any]],dict[str,int]]:
    if not ANCHORS.is_file() or ANCHORS.is_symlink():
        fail("price_anchors input missing/invalid")
    rows=[]
    counts={"valid":0,"missing_entry":0,"missing_exit":0,"missing_both":0}
    with ANCHORS.open("r",encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if not line.strip():
                continue
            try:
                row=json.loads(line)
            except Exception as exc:
                fail(f"invalid anchor JSONL line {n}: {exc}")
            if not isinstance(row,dict):
                fail(f"anchor row {n} not object")
            rows.append(row)

    if len(rows)!=EXPECTED_CLUSTER_COUNT:
        fail(f"anchor row count={len(rows)}")

    for i,(row,c) in enumerate(zip(rows,canon),1):
        cid=f"S0C{i:06d}"
        if row.get("cluster_id")!=cid:
            fail(f"anchor cluster ID mismatch {i}")
        for a,b,name in (
            (row.get("symbol"),c.get("symbol"),"symbol"),
            (row.get("liquidation_side"),c.get("liquidation_side"),"liquidation_side"),
            (row.get("reversal_sign"),c.get("reversal_sign"),"reversal_sign"),
            (row.get("cluster_start_ms"),c.get("start_ms"),"cluster_start_ms"),
            (row.get("cluster_end_ms"),c.get("end_ms"),"cluster_end_ms"),
            (row.get("event_count"),c.get("event_count"),"event_count"),
            (row.get("entry_bucket"),c.get("entry_bucket"),"entry_bucket"),
            (row.get("exit_bucket"),c.get("exit_bucket"),"exit_bucket"),
        ):
            if a!=b:
                fail(f"{cid} canonical mismatch: {name}")

        ef=row.get("entry_found")
        xf=row.get("exit_found")
        valid=row.get("valid_price_cluster")
        if not isinstance(ef,bool) or not isinstance(xf,bool) or not isinstance(valid,bool):
            fail(f"{cid} boolean anchor flags invalid")
        if valid!=(ef and xf):
            fail(f"{cid} valid_price_cluster mismatch")

        if ef and xf:
            counts["valid"]+=1
        elif not ef and not xf:
            counts["missing_both"]+=1
        elif not ef:
            counts["missing_entry"]+=1
        else:
            counts["missing_exit"]+=1

        for kind,found,bucket in (
            ("entry",ef,c["entry_bucket"]),
            ("exit",xf,c["exit_bucket"]),
        ):
            obj=row.get(kind)
            if not found:
                if obj is not None:
                    fail(f"{cid} {kind} object present while found=false")
                continue
            if not isinstance(obj,dict):
                fail(f"{cid} {kind} object missing")
            try:
                ts_us=int(obj["trade_ts_us"])
                px=float(obj["price"])
                size=float(obj["size"])
            except Exception as exc:
                fail(f"{cid} {kind} parse failure: {exc}")
            if not (math.isfinite(px) and px>0 and math.isfinite(size) and size>0):
                fail(f"{cid} {kind} nonpositive/nonfinite price/size")
            start_us=int(bucket["start_ms"])*1000
            end_us=int(bucket["end_ms_exclusive"])*1000
            if not (start_us<=ts_us<end_us):
                fail(f"{cid} {kind} timestamp outside frozen bucket")
            if obj.get("side") not in {"Buy","Sell"}:
                fail(f"{cid} {kind} trade side invalid")
            fn=str(obj.get("source_filename") or "")
            if not fn.startswith(str(c["symbol"])) or not fn.endswith(".csv.gz"):
                fail(f"{cid} {kind} source filename mismatch")
            ash=str(obj.get("source_archive_sha256") or "")
            if len(ash)!=64 or any(ch not in "0123456789abcdef" for ch in ash.lower()):
                fail(f"{cid} {kind} archive SHA malformed")

    return rows,counts


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)

    if not MANIFEST.is_file() or MANIFEST.is_symlink():
        fail("extraction manifest missing/invalid")
    m=load_json(MANIFEST)
    if m.get("status")!="B13C_S0_PRICE_ANCHOR_EXTRACTION_PASS":
        fail(f"extraction manifest status={m.get('status')}")
    if int(m.get("cluster_count") or 0)!=EXPECTED_CLUSTER_COUNT:
        fail("manifest cluster count mismatch")
    if int(m.get("required_archive_count") or 0)!=EXPECTED_ARCHIVE_COUNT:
        fail("manifest archive count mismatch")
    if int(m.get("archive_ledger_count") or 0)!=EXPECTED_ARCHIVE_COUNT:
        fail("manifest archive ledger count mismatch")
    if int(m.get("metadata_total_content_length_bytes") or 0)!=EXPECTED_TOTAL_BYTES:
        fail("manifest metadata total bytes mismatch")
    for key,expected in (
        ("price_bodies_opened",True),
        ("price_rows_parsed",True),
        ("frozen_price_anchors_extracted",True),
        ("returns_calculated",False),
        ("signed_reversal_calculated",False),
        ("threshold_outcome_calculated",False),
        ("per_symbol_performance_ranked",False),
        ("pnl_calculated",False),
        ("collector_mutation_performed",False),
    ):
        if m.get(key) is not expected:
            fail(f"manifest firewall/status mismatch: {key}")

    comp=m.get("anchor_completeness") or {}
    expected_counts={
        "cluster_rows":EXPECTED_CLUSTER_COUNT,
        "clusters_with_both_anchors":EXPECTED_VALID,
        "missing_entry_count":EXPECTED_MISSING_ENTRY,
        "missing_exit_count":EXPECTED_MISSING_EXIT,
        "missing_both_count":EXPECTED_MISSING_BOTH,
    }
    for k,v in expected_counts.items():
        if int(comp.get(k) or 0)!=v:
            fail(f"manifest completeness mismatch {k}: {comp.get(k)}")
    actual_anchor_sha=sha256_file(ANCHORS)
    if comp.get("price_anchors_sha256")!=actual_anchor_sha:
        fail("price_anchors SHA mismatch vs extraction manifest")

    canon=canonical_clusters()
    rows,counts=parse_anchors(canon)
    if counts!={
        "valid":EXPECTED_VALID,
        "missing_entry":EXPECTED_MISSING_ENTRY,
        "missing_exit":EXPECTED_MISSING_EXIT,
        "missing_both":EXPECTED_MISSING_BOTH,
    }:
        fail(f"anchor partition mismatch: {counts}")

    archive_shas=m.get("archive_sha256") or {}
    if len(archive_shas)!=EXPECTED_ARCHIVE_COUNT:
        fail("archive SHA map count mismatch")
    for fn,sha in archive_shas.items():
        if len(str(sha))!=64:
            fail(f"archive SHA malformed: {fn}")

    result={
        "schema":"sc001.b13c_s0_price_anchor_dataset_freeze.v0.1",
        "status":PASS,
        "extraction_manifest_sha256":sha256_file(MANIFEST),
        "price_anchors_sha256":actual_anchor_sha,
        "canonical_master_sha256":EXPECTED_MASTER_SHA256,
        "cluster_rows":len(rows),
        "valid_price_clusters":counts["valid"],
        "missing_entry":counts["missing_entry"],
        "missing_exit":counts["missing_exit"],
        "missing_both":counts["missing_both"],
        "archive_sha256_count":len(archive_shas),
        "price_data_opened":True,
        "returns_calculated":False,
        "signed_reversal_calculated":False,
        "threshold_outcome_calculated":False,
        "per_symbol_performance_ranked":False,
        "pnl_calculated":False,
        "network_calls_performed":False,
        "collector_mutation_performed":False,
        "next_state":"PREPARE_SEPARATE_OFFLINE_S0_OUTCOME_BUNDLE",
    }
    atomic_json(OUT,result)
    print(PASS)
    print("cluster_rows =",len(rows))
    print("valid_price_clusters =",counts["valid"])
    print("missing_entry =",counts["missing_entry"])
    print("missing_exit =",counts["missing_exit"])
    print("missing_both =",counts["missing_both"])
    print("returns/PnL = CLOSED")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
