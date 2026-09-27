#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
import shutil
import tempfile
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="SC001-B13C-S0-PRICE-ANCHOR-EXTRACTOR-V0.1"
PASS="B13C_S0_PRICE_ANCHOR_EXTRACTION_PASS"
REVIEW="B13C_S0_PRICE_ANCHOR_EXTRACTION_REVIEW"
SELFTEST_PASS="B13C_S0_PRICE_ANCHOR_EXTRACTOR_V011_SELF_TEST_PASS"
SELFTEST_REVIEW="B13C_S0_PRICE_ANCHOR_EXTRACTOR_V011_SELF_TEST_REVIEW"

ROOT=Path(__file__).resolve().parents[2]
MASTER=ROOT/"docs/research/artifacts/b13c-s0/exact-cluster-freeze-v0.1/master-index.json"
EXPECTED_MASTER_SHA256="0636ac25d6b7a484a4a9959f256aa57e0a1ead7f4e228423715f688b194fb87b"
CENSUS_RESULT=ROOT/"docs/research/sc001-b13c-s0-real-event-only-cluster-census-result-v0.1.json"
EXPECTED_CENSUS_SHA256="fd08901e77bb73c00bb53826e925b2124d52e05d6c8f45cdc154b1c57a2ab1eb"
METADATA_SUMMARY=ROOT/"docs/research/sc001-b13c-s0-price-archive-metadata-preflight-result-v0.1.json"
EXPECTED_METADATA_SUMMARY_SHA256="8992235a0d7bc620c3e4ff14db9b0108977ff2e0c274a6ff11416bb41f446c30"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
METADATA_REPORT=DATA_ROOT/"SC001_B13C_S0_PRICE_ARCHIVE_PREFLIGHT"/"b13c_s0_price_archive_metadata_preflight_v0_1.json"
OUT_DIR=DATA_ROOT/"SC001_B13C_S0_PRICE_ANCHORS_V01"
LEDGER_DIR=OUT_DIR/"archive_ledger"
CANDIDATE_DIR=OUT_DIR/"candidates"
TMP_DIR=OUT_DIR/"tmp"
FINAL_ANCHORS=OUT_DIR/"price_anchors.jsonl"
FINAL_MANIFEST=OUT_DIR/"price_anchor_extraction_manifest.json"

TRUSTED_HOST="public.bybit.com"
EXPECTED_CLUSTER_COUNT=1905
EXPECTED_ARCHIVE_COUNT=76
EXPECTED_TOTAL_BYTES=2633144445
TIMEOUT=120
RETRIES=3
CHUNK=1024*1024
MIN_FREE_RESERVE=2*1024**3


def fail(msg:str)->None:
    raise RuntimeError(msg)


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


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*CHUNK),b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path:Path,obj:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n")
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)


def atomic_jsonl(path:Path,rows:list[dict])->str:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)
    return sha256_file(path)


def load_json(path:Path)->dict:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail(f"JSON object expected: {path}")
    return obj


def trusted_url(url:str,symbol:str,filename:str)->bool:
    try:
        p=urllib.parse.urlparse(url)
    except Exception:
        return False
    return (
        p.scheme=="https"
        and (p.hostname or "").lower()==TRUSTED_HOST
        and p.path==f"/trading/{symbol}/{filename}"
        and not p.params and not p.query and not p.fragment
    )


class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self,symbol:str,filename:str):
        super().__init__()
        self.symbol=symbol
        self.filename=filename
        self.count=0
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        self.count+=1
        if self.count>5:
            fail("redirect cap exceeded")
        if not trusted_url(newurl,self.symbol,self.filename):
            fail(f"untrusted redirect: {newurl}")
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def load_clusters()->tuple[list[dict],list[dict],dict]:
    if sha256_file(MASTER)!=EXPECTED_MASTER_SHA256:
        fail("master index SHA mismatch")
    master=load_json(MASTER)
    if master.get("status")!="B13C_S0_EXACT_CLUSTER_FREEZE_MANIFEST_PASS":
        fail("master status mismatch")
    clusters=[]
    for expected_idx,row in enumerate(master.get("chunks") or [],1):
        if int(row.get("part_index") or 0)!=expected_idx:
            fail("chunk index discontinuity")
        p=ROOT/str(row["path"])
        if sha256_file(p)!=row.get("sha256"):
            fail(f"chunk SHA mismatch: {p}")
        part=load_json(p)
        if part.get("parent_runner_artifact_sha256")!="1138d6a034eb4a7269b8649272e375e5056e2f5b2d361bad3ea6ba54ddc7861c":
            fail("chunk parent artifact mismatch")
        rows=part.get("eligible_clusters") or []
        if len(rows)!=int(part.get("cluster_count") or -1):
            fail("chunk cluster count mismatch")
        clusters.extend(rows)
    if len(clusters)!=EXPECTED_CLUSTER_COUNT:
        fail(f"reconstructed cluster count {len(clusters)}")
    for i,c in enumerate(clusters,1):
        if c.get("cluster_id")!=f"S0C{i:06d}":
            fail(f"cluster ID discontinuity at {i}")

    if sha256_file(CENSUS_RESULT)!=EXPECTED_CENSUS_SHA256:
        fail("census result SHA mismatch")
    census=load_json(CENSUS_RESULT)
    required=census.get("required_price_archives") or []
    if len(required)!=EXPECTED_ARCHIVE_COUNT:
        fail("required archive count mismatch")

    if sha256_file(METADATA_SUMMARY)!=EXPECTED_METADATA_SUMMARY_SHA256:
        fail("metadata summary SHA mismatch")
    summary=load_json(METADATA_SUMMARY)
    if summary.get("status")!="B13C_S0_PRICE_ARCHIVE_METADATA_PREFLIGHT_PASS":
        fail("metadata summary status mismatch")
    if int(summary.get("required_archive_count") or 0)!=EXPECTED_ARCHIVE_COUNT:
        fail("metadata summary file count mismatch")
    if int(summary.get("total_content_length_bytes") or 0)!=EXPECTED_TOTAL_BYTES:
        fail("metadata summary total-byte mismatch")
    return clusters,required,master


def load_metadata(required:list[dict])->dict[str,dict]:
    meta=load_json(METADATA_REPORT)
    if meta.get("status")!="B13C_S0_PRICE_ARCHIVE_METADATA_PREFLIGHT_PASS":
        fail("VPS metadata report status mismatch")
    files=meta.get("files") or []
    if len(files)!=EXPECTED_ARCHIVE_COUNT:
        fail(f"VPS metadata file count {len(files)}")
    if int(meta.get("total_content_length_bytes") or 0)!=EXPECTED_TOTAL_BYTES:
        fail("VPS metadata total bytes mismatch")
    want={(x["symbol"],x["utc_day"],x["filename"],x["url"]) for x in required}
    got={(x.get("symbol"),x.get("utc_day"),x.get("filename"),x.get("url")) for x in files}
    if got!=want:
        fail("VPS metadata archive identity set mismatch")
    by_name={}
    for x in files:
        fn=str(x["filename"])
        if fn in by_name:
            fail(f"duplicate metadata filename: {fn}")
        if int(x.get("http_status") or 0)!=200:
            fail(f"metadata HTTP status not 200: {fn}")
        if int(x.get("content_length") or 0)<=0:
            fail(f"metadata invalid Content-Length: {fn}")
        if not trusted_url(str(x.get("url") or ""),str(x.get("symbol") or ""),fn):
            fail(f"metadata URL identity mismatch: {fn}")
        by_name[fn]=x
    return by_name


def touched_days(start_ms:int,end_ms_exclusive:int)->set[str]:
    if end_ms_exclusive<=start_ms:
        fail("invalid bucket interval")
    a=datetime.fromtimestamp(start_ms/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    b=datetime.fromtimestamp((end_ms_exclusive-1)/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    return {a,b}


def build_targets(clusters:list[dict])->dict[str,list[dict]]:
    out=defaultdict(list)
    for c in clusters:
        cid=str(c["cluster_id"]); symbol=str(c["symbol"])
        for kind in ("entry","exit"):
            b=c[f"{kind}_bucket"]
            start_ms=int(b["start_ms"]); end_ms=int(b["end_ms_exclusive"])
            days=touched_days(start_ms,end_ms)
            for day in days:
                fn=f"{symbol}{day}.csv.gz"
                out[fn].append({
                    "cluster_id":cid,
                    "kind":kind,
                    "start_us":start_ms*1000,
                    "end_us":end_ms*1000,
                })
    for fn in out:
        out[fn].sort(key=lambda x:(x["start_us"],x["end_us"],x["cluster_id"],x["kind"]))
    return dict(out)


def download_exact(meta:dict,dest:Path)->tuple[str,int]:
    symbol=str(meta["symbol"]); filename=str(meta["filename"]); url=str(meta["url"])
    expected=int(meta["content_length"])
    if shutil.disk_usage(OUT_DIR).free < expected+MIN_FREE_RESERVE:
        fail(f"insufficient disk reserve before {filename}")
    dest.parent.mkdir(parents=True,exist_ok=True)
    tmp=dest.with_name(dest.name+".part")
    tmp.unlink(missing_ok=True)
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            h=hashlib.sha256(); total=0
            opener=urllib.request.build_opener(StrictRedirect(symbol,filename))
            req=urllib.request.Request(url,method="GET",headers={"User-Agent":"BotMarketplace-SC001-B13C-S0/0.1"})
            with opener.open(req,timeout=TIMEOUT) as resp, tmp.open("wb") as f:
                final=resp.geturl()
                if not trusted_url(final,symbol,filename):
                    fail(f"GET final URL mismatch: {filename}")
                while True:
                    chunk=resp.read(CHUNK)
                    if not chunk:
                        break
                    total+=len(chunk)
                    if total>expected:
                        fail(f"download overflow: {filename}")
                    h.update(chunk); f.write(chunk)
                f.flush(); os.fsync(f.fileno())
            if total!=expected:
                fail(f"download size mismatch {filename}: {total} != {expected}")
            os.replace(tmp,dest)
            return h.hexdigest(),total
        except Exception as exc:
            last=exc
            tmp.unlink(missing_ok=True)
            if attempt<RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"download failed {filename}: {type(last).__name__}: {last}")


def parse_archive(path:Path,meta:dict,targets:list[dict])->tuple[dict,list[dict]]:
    symbol=str(meta["symbol"]); day=str(meta["utc_day"]); filename=str(meta["filename"])
    day_start=int(datetime.fromisoformat(day+"T00:00:00+00:00").timestamp()*1_000_000)
    day_end=day_start+86_400_000_000

    sorted_targets=sorted(targets,key=lambda x:(x["start_us"],x["end_us"]))
    next_idx=0
    active=[]
    best={}
    row_count=invalid=out_of_day=reversals=same_ts=0
    prev_ts=None
    first_ts=last_ts=None
    header=None

    try:
        with gzip.open(path,"rt",encoding="utf-8",errors="strict",newline="") as f:
            r=csv.reader(f)
            header=next(r,None)
            if not header or len(header)<5:
                fail(f"Bybit header missing/short: {filename}")
            low=[str(x).strip().lower() for x in header]
            if low[:5]!=["timestamp","symbol","side","size","price"]:
                fail(f"Bybit header semantics mismatch {filename}: {header[:5]}")
            for row in r:
                if not row:
                    continue
                if len(row)<5:
                    invalid+=1; continue
                try:
                    ts_us=int(round(float(row[0])*1_000_000))
                    rsymbol=row[1].strip()
                    side=row[2].strip()
                    size=float(row[3])
                    price=float(row[4])
                    if rsymbol!=symbol:
                        raise ValueError("symbol")
                    if side not in {"Buy","Sell"}:
                        raise ValueError("side")
                    if not (math.isfinite(size) and size>0 and math.isfinite(price) and price>0):
                        raise ValueError("size/price")
                except Exception:
                    invalid+=1
                    continue

                row_count+=1
                if not (day_start<=ts_us<day_end):
                    out_of_day+=1
                if prev_ts is not None:
                    if ts_us<prev_ts:
                        reversals+=1
                    elif ts_us==prev_ts:
                        same_ts+=1
                prev_ts=ts_us
                if first_ts is None: first_ts=ts_us
                last_ts=ts_us

                while next_idx<len(sorted_targets) and sorted_targets[next_idx]["start_us"]<=ts_us:
                    active.append(sorted_targets[next_idx]); next_idx+=1
                if active:
                    active=[x for x in active if x["end_us"]>ts_us]
                    for target in active:
                        if target["start_us"]<=ts_us<target["end_us"]:
                            key=(target["cluster_id"],target["kind"])
                            prev=best.get(key)
                            if prev is None or ts_us>=prev["trade_ts_us"]:
                                best[key]={
                                    "cluster_id":target["cluster_id"],
                                    "kind":target["kind"],
                                    "trade_ts_us":ts_us,
                                    "price":format(price,".17g"),
                                    "side":side,
                                    "size":format(size,".17g"),
                                    "source_filename":filename,
                                }
    except (OSError,EOFError,gzip.BadGzipFile) as exc:
        raise RuntimeError(f"gzip read failure {filename}: {exc}") from exc

    if invalid!=0:
        fail(f"malformed/invalid rows {filename}: {invalid}")
    if out_of_day!=0:
        fail(f"out-of-day rows {filename}: {out_of_day}")
    if reversals!=0:
        fail(f"timestamp reversals {filename}: {reversals}")
    if row_count<=0:
        fail(f"empty archive rows: {filename}")

    diag={
        "filename":filename,
        "symbol":symbol,
        "utc_day":day,
        "row_count":row_count,
        "invalid_rows":invalid,
        "out_of_day_rows":out_of_day,
        "timestamp_reversals":reversals,
        "same_timestamp_adjacent":same_ts,
        "first_ts_us":first_ts,
        "last_ts_us":last_ts,
        "target_bucket_count":len(targets),
        "candidate_anchor_count":len(best),
        "header_first_five":header[:5],
    }
    rows=sorted(best.values(),key=lambda x:(x["cluster_id"],x["kind"],x["trade_ts_us"]))
    return diag,rows


def reusable_archive(meta:dict,ledger_path:Path,candidate_path:Path)->bool:
    if not ledger_path.is_file() or not candidate_path.is_file():
        return False
    try:
        led=load_json(ledger_path)
        if led.get("status")!="ARCHIVE_PASS":
            return False
        if led.get("filename")!=meta.get("filename"):
            return False
        if int(led.get("expected_content_length") or 0)!=int(meta.get("content_length") or -1):
            return False
        if led.get("candidate_file_sha256")!=sha256_file(candidate_path):
            return False
        return True
    except Exception:
        return False


def process_archive(meta:dict,targets:list[dict])->dict:
    filename=str(meta["filename"])
    ledger_path=LEDGER_DIR/f"{filename}.json"
    candidate_path=CANDIDATE_DIR/f"{filename}.jsonl"
    if reusable_archive(meta,ledger_path,candidate_path):
        return load_json(ledger_path)

    tmp=TMP_DIR/filename
    tmp.unlink(missing_ok=True)
    archive_sha,total=download_exact(meta,tmp)
    try:
        diag,candidates=parse_archive(tmp,meta,targets)
        candidate_sha=atomic_jsonl(candidate_path,candidates)
        ledger={
            "schema":"sc001.b13c_s0_price_archive_ledger.v0.1",
            "status":"ARCHIVE_PASS",
            "filename":filename,
            "symbol":meta["symbol"],
            "utc_day":meta["utc_day"],
            "url":meta["url"],
            "expected_content_length":int(meta["content_length"]),
            "downloaded_bytes":total,
            "archive_sha256":archive_sha,
            "metadata_last_modified":meta.get("last_modified"),
            "metadata_etag":meta.get("etag"),
            "metadata_content_type":meta.get("content_type"),
            "parse":diag,
            "candidate_file":str(candidate_path),
            "candidate_file_sha256":candidate_sha,
            "candidate_anchor_count":len(candidates),
            "archive_temp_deleted_after_success":True,
        }
        atomic_json(ledger_path,ledger)
        return ledger
    finally:
        tmp.unlink(missing_ok=True)


def aggregate_anchors(clusters:list[dict],ledgers:list[dict])->dict:
    candidates=defaultdict(list)
    archive_sha={}
    for led in ledgers:
        fn=str(led["filename"])
        archive_sha[fn]=str(led["archive_sha256"])
        p=CANDIDATE_DIR/f"{fn}.jsonl"
        with p.open("r",encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                row=json.loads(line)
                candidates[(row["cluster_id"],row["kind"])].append(row)

    final=[]
    missing_entry=missing_exit=missing_both=both=0
    for c in clusters:
        cid=str(c["cluster_id"])
        chosen={}
        for kind in ("entry","exit"):
            rows=candidates.get((cid,kind),[])
            if rows:
                rows.sort(key=lambda x:(int(x["trade_ts_us"]),x["source_filename"]))
                chosen[kind]=rows[-1]
        ef="entry" in chosen; xf="exit" in chosen
        if ef and xf: both+=1
        elif not ef and not xf: missing_both+=1
        elif not ef: missing_entry+=1
        else: missing_exit+=1
        row={
            "cluster_id":cid,
            "symbol":c["symbol"],
            "liquidation_side":c["liquidation_side"],
            "reversal_sign":c["reversal_sign"],
            "cluster_start_ms":c["start_ms"],
            "cluster_end_ms":c["end_ms"],
            "event_count":c["event_count"],
            "entry_bucket":c["entry_bucket"],
            "exit_bucket":c["exit_bucket"],
            "entry_found":ef,
            "exit_found":xf,
            "valid_price_cluster":ef and xf,
            "entry":chosen.get("entry"),
            "exit":chosen.get("exit"),
        }
        for kind in ("entry","exit"):
            if chosen.get(kind):
                fn=chosen[kind]["source_filename"]
                chosen[kind]["source_archive_sha256"]=archive_sha[fn]
        final.append(row)

    final_sha=atomic_jsonl(FINAL_ANCHORS,final)
    return {
        "cluster_rows":len(final),
        "clusters_with_both_anchors":both,
        "missing_entry_count":missing_entry,
        "missing_exit_count":missing_exit,
        "missing_both_count":missing_both,
        "price_anchors_sha256":final_sha,
    }


def self_test()->int:
    try:
        clusters,required,master=load_clusters()
        if len(clusters)!=EXPECTED_CLUSTER_COUNT or len(required)!=EXPECTED_ARCHIVE_COUNT:
            fail("canonical freeze self-test mismatch")
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"TESTUSDT2026-09-20.csv.gz"
            rows=[
                ["timestamp","symbol","side","size","price"],
                ["1790000000.100","TESTUSDT","Buy","1","100.0"],
                ["1790000000.900","TESTUSDT","Sell","2","101.0"],
                ["1790000030.100","TESTUSDT","Buy","1","102.0"],
                ["1790000030.900","TESTUSDT","Sell","3","103.0"],
            ]
            with gzip.open(p,"wt",encoding="utf-8",newline="") as f:
                w=csv.writer(f); w.writerows(rows)
            # Build target windows directly around fixture timestamps.
            targets=[
                {"cluster_id":"X","kind":"entry","start_us":1790000000_000000,"end_us":1790000001_000000},
                {"cluster_id":"X","kind":"exit","start_us":1790000030_000000,"end_us":1790000031_000000},
            ]
            meta={"symbol":"TESTUSDT","utc_day":"2026-09-20","filename":p.name}
            # Fixture timestamps intentionally belong to a different UTC day; derive the day from timestamp.
            fixture_day=datetime.fromtimestamp(1790000000,tz=timezone.utc).strftime("%Y-%m-%d")
            meta["utc_day"]=fixture_day
            diag,cands=parse_archive(p,meta,targets)
            by={x["kind"]:x for x in cands}
            if by["entry"]["price"]!="101" or by["exit"]["price"]!="103":
                fail("last-trade bucket selection mismatch")
            if diag["timestamp_reversals"]!=0 or diag["invalid_rows"]!=0:
                fail("fixture integrity mismatch")
        print(SELFTEST_PASS)
        print("canonical_clusters =",len(clusters))
        print("canonical_archives =",len(required))
        print("returns/PnL = CLOSED")
        return 0
    except Exception as exc:
        print(SELFTEST_REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2


def extract()->int:
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    LEDGER_DIR.mkdir(parents=True,exist_ok=True)
    CANDIDATE_DIR.mkdir(parents=True,exist_ok=True)
    TMP_DIR.mkdir(parents=True,exist_ok=True)
    try:
        clusters,required,master=load_clusters()
        metadata=load_metadata(required)
        targets=build_targets(clusters)

        required_names={x["filename"] for x in required}
        if set(targets)!=required_names:
            fail("target archive set mismatch")

        ledgers=[]
        for i,row in enumerate(required,1):
            fn=row["filename"]
            print(f"ARCHIVE {i}/{len(required)} {fn}",flush=True)
            ledgers.append(process_archive(metadata[fn],targets[fn]))

        if len(ledgers)!=EXPECTED_ARCHIVE_COUNT:
            fail("archive ledger count mismatch")
        if any(x.get("status")!="ARCHIVE_PASS" for x in ledgers):
            fail("non-PASS archive ledger")

        completeness=aggregate_anchors(clusters,ledgers)
        if completeness["cluster_rows"]!=EXPECTED_CLUSTER_COUNT:
            fail("final price-anchor row count mismatch")

        archive_shas={x["filename"]:x["archive_sha256"] for x in ledgers}
        manifest={
            "stage":STAGE,
            "version":"0.1",
            "status":PASS,
            "cluster_master_sha256":EXPECTED_MASTER_SHA256,
            "cluster_count":EXPECTED_CLUSTER_COUNT,
            "required_archive_count":EXPECTED_ARCHIVE_COUNT,
            "metadata_total_content_length_bytes":EXPECTED_TOTAL_BYTES,
            "archive_sha256":archive_shas,
            "archive_ledger_count":len(ledgers),
            "anchor_completeness":completeness,
            "price_anchors_file":str(FINAL_ANCHORS),
            "price_bodies_opened":True,
            "price_rows_parsed":True,
            "frozen_price_anchors_extracted":True,
            "returns_calculated":False,
            "signed_reversal_calculated":False,
            "threshold_outcome_calculated":False,
            "per_symbol_performance_ranked":False,
            "pnl_calculated":False,
            "collector_mutation_performed":False,
            "finished_utc":datetime.now(timezone.utc).isoformat(),
            "next_state":"FREEZE_PRICE_ANCHOR_DATASET_THEN_RUN_SEPARATE_OFFLINE_S0_OUTCOME",
        }
        atomic_json(FINAL_MANIFEST,manifest)
        print(PASS)
        print("clusters =",EXPECTED_CLUSTER_COUNT)
        print("archives =",EXPECTED_ARCHIVE_COUNT)
        print("valid_price_clusters =",completeness["clusters_with_both_anchors"])
        print("missing_entry =",completeness["missing_entry_count"])
        print("missing_exit =",completeness["missing_exit_count"])
        print("missing_both =",completeness["missing_both_count"])
        print("returns/PnL = CLOSED")
        print("manifest =",FINAL_MANIFEST)
        return 0
    except Exception as exc:
        failrep={
            "stage":STAGE,
            "version":"0.1",
            "status":REVIEW,
            "error":f"{type(exc).__name__}: {exc}",
            "price_bodies_opened":"UNKNOWN_OR_PARTIAL",
            "returns_calculated":False,
            "signed_reversal_calculated":False,
            "threshold_outcome_calculated":False,
            "per_symbol_performance_ranked":False,
            "pnl_calculated":False,
            "collector_mutation_performed":False,
        }
        try: atomic_json(FINAL_MANIFEST,failrep)
        except Exception: pass
        print(REVIEW)
        print("error =",failrep["error"])
        print("returns/PnL = CLOSED")
        return 2


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","extract"),default="self-test")
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)
    return self_test() if a.mode=="self-test" else extract()


if __name__=="__main__":
    raise SystemExit(main())
