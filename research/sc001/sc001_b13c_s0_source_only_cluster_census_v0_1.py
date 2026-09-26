#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGES={
    "SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.1",
    "SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3",
}
SYMBOLS=(
    "BTCUSDT","ETHUSDT","SOLUSDT","DOGEUSDT","ORDIUSDT","FILUSDT",
    "UNIUSDT","XRPUSDT","LTCUSDT","OPUSDT","BCHUSDT","SUIUSDT",
)
START_MS=1789800458969
END_MS=1790456732973
EVENT_DAYS=(
    "2026-09-19","2026-09-20","2026-09-21","2026-09-22",
    "2026-09-23","2026-09-24","2026-09-25","2026-09-26",
)
CLUSTER_GAP_MS=5_000
GAP_PAD_MS=5_000
MIN_EVENTS=3
MIN_SAMPLE=100

PASS="B13C_S0_SOURCE_ONLY_CLUSTER_CENSUS_PASS"
SELFTEST_PASS="B13C_S0_SOURCE_ONLY_CLUSTER_CENSUS_V01_SELF_TEST_PASS"


def fail(msg:str)->None:
    raise RuntimeError(msg)


def atomic_json(path:Path,obj:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)


def load_json(path:Path)->dict[str,Any]:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail(f"JSON object required: {path}")
    return obj


def iter_jsonl(path:Path):
    with path.open("r",encoding="utf-8") as f:
        for line_no,line in enumerate(f,1):
            if not line.strip():
                continue
            try:
                obj=json.loads(line)
            except Exception as exc:
                fail(f"invalid JSONL {path}:{line_no}: {exc}")
            if not isinstance(obj,dict):
                fail(f"JSON object required {path}:{line_no}")
            yield obj


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


def merge_intervals(rows:list[tuple[int,int]])->list[tuple[int,int]]:
    clean=[]
    for a,b in rows:
        a=int(a); b=int(b)
        if b<a:
            fail("negative gap interval")
        if b<START_MS or a>END_MS:
            continue
        clean.append((max(a,START_MS),min(b,END_MS)))
    clean.sort()
    out=[]
    for a,b in clean:
        if not out or a>out[-1][1]:
            out.append([a,b])
        else:
            out[-1][1]=max(out[-1][1],b)
    return [(int(a),int(b)) for a,b in out]


def build_source_gaps(state:dict[str,Any], ledger_path:Path)->tuple[list[tuple[int,int]],dict[str,int]]:
    rows=list(iter_jsonl(ledger_path))
    for row in rows:
        if row.get("stage") not in STAGES:
            fail(f"connection ledger stage mismatch: {row.get('stage')}")
    rows.sort(key=lambda r:int(r.get("ts_ms") or 0))

    gaps=[]
    counts=defaultdict(int)
    unavailable_start=START_MS
    subscribed=False

    for row in rows:
        event=str(row.get("event") or "")
        ts=int(row.get("ts_ms") or 0)
        if ts<=0:
            fail("connection ledger timestamp missing")
        if event:
            counts[event]+=1

        if event=="SUBSCRIBED":
            if unavailable_start is not None and ts>=unavailable_start:
                gaps.append((unavailable_start,ts))
            unavailable_start=None
            subscribed=True
        elif event=="DISCONNECTED":
            if unavailable_start is None:
                unavailable_start=ts
            subscribed=False
        elif event=="STOPPED":
            if unavailable_start is None:
                unavailable_start=ts
            subscribed=False
        elif event=="PROCESS_RESTART_GAP":
            a=row.get("start_ms"); b=row.get("end_ms")
            if a is not None and b is not None:
                gaps.append((int(a),int(b)))

    if unavailable_start is not None and unavailable_start<END_MS:
        gaps.append((unavailable_start,END_MS))

    for row in state.get("process_restart_gaps") or []:
        if isinstance(row,dict) and row.get("start_ms") is not None and row.get("end_ms") is not None:
            gaps.append((int(row["start_ms"]),int(row["end_ms"])))

    return merge_intervals(gaps),dict(sorted(counts.items()))


def overlaps_any(start:int,end:int,gaps:list[tuple[int,int]])->bool:
    for a,b in gaps:
        if max(start,a)<=min(end,b):
            return True
    return False


def utc_day(ms:int)->str:
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).strftime("%Y-%m-%d")


def touched_days(start_ms:int,end_ms_exclusive:int)->set[str]:
    if end_ms_exclusive<=start_ms:
        fail("invalid bucket interval")
    return {utc_day(start_ms),utc_day(end_ms_exclusive-1)}


def parse_events(root:Path)->tuple[list[dict[str,Any]],dict[str,int]]:
    raw_rows=0
    duplicate_rows=0
    unique={}
    for day in EVENT_DAYS:
        p=root/"events"/f"{day}.jsonl"
        if not p.is_file() or p.is_symlink():
            fail(f"required event file missing/invalid: {day}")
        for row in iter_jsonl(p):
            raw_rows+=1
            stage=row.get("collector_stage")
            if stage not in STAGES:
                fail(f"event stage mismatch: {stage}")
            symbol=str(row.get("symbol") or "")
            side=str(row.get("liquidated_position_side") or "")
            fp=str(row.get("event_fingerprint_sha256") or "")
            t=int(row.get("liquidation_ts_ms") or 0)
            recv=int(row.get("recv_ts_ms") or 0)
            if symbol not in SYMBOLS:
                fail(f"unexpected symbol={symbol}")
            if side not in {"LONG_LIQUIDATED","SHORT_LIQUIDATED"}:
                fail(f"unexpected liquidation side={side}")
            if len(fp)!=64 or t<=0 or recv<=0:
                fail("invalid event identity/timestamp")
            if not (START_MS<=t<=END_MS):
                continue
            rec={
                "symbol":symbol,
                "side":side,
                "fingerprint":fp,
                "t":t,
                "recv":recv,
            }
            prev=unique.get(fp)
            if prev is None:
                unique[fp]=rec
            else:
                if (prev["symbol"],prev["side"],prev["t"])!=(symbol,side,t):
                    fail("same fingerprint with conflicting semantics")
                duplicate_rows+=1
                if recv<prev["recv"]:
                    unique[fp]=rec
    events=sorted(unique.values(),key=lambda x:(x["symbol"],x["t"],x["recv"],x["fingerprint"]))
    return events,{
        "raw_rows_read":raw_rows,
        "unique_events_in_window":len(events),
        "duplicate_rows_collapsed":duplicate_rows,
    }


def cluster_events(events:list[dict[str,Any]],gaps:list[tuple[int,int]])->dict[str,Any]:
    by_symbol=defaultdict(list)
    for e in events:
        by_symbol[e["symbol"]].append(e)

    total_clusters=0
    under_min=0
    mixed_side=0
    gap_censored=0
    eligible=[]
    required=set()

    for symbol in SYMBOLS:
        rows=by_symbol.get(symbol,[])
        clusters=[]
        cur=[]
        prev_t=None
        for e in rows:
            if prev_t is None or e["t"]-prev_t<=CLUSTER_GAP_MS:
                cur.append(e)
            else:
                if cur:
                    clusters.append(cur)
                cur=[e]
            prev_t=e["t"]
        if cur:
            clusters.append(cur)

        for c in clusters:
            total_clusters+=1
            if len(c)<MIN_EVENTS:
                under_min+=1
                continue
            sides={x["side"] for x in c}
            if len(sides)!=1:
                mixed_side+=1
                continue
            c_start=int(c[0]["t"])
            c_end=int(c[-1]["t"])
            if overlaps_any(c_start-GAP_PAD_MS,c_end+GAP_PAD_MS,gaps):
                gap_censored+=1
                continue

            entry_start=c_end+1_000
            entry_end=c_end+2_000
            exit_start=c_end+31_000
            exit_end=c_end+32_000
            archive_days=touched_days(entry_start,entry_end)|touched_days(exit_start,exit_end)
            for day in archive_days:
                required.add((symbol,day))

            eligible.append({
                "cluster_id":f"S0C{len(eligible)+1:06d}",
                "symbol":symbol,
                "side":next(iter(sides)),
                "start_ms":c_start,
                "end_ms":c_end,
                "event_count":len(c),
                "required_archive_days":sorted(archive_days),
            })

    required_files=[
        {
            "symbol":symbol,
            "utc_day":day,
            "filename":f"{symbol}{day}.csv.gz",
            "url":f"https://public.bybit.com/trading/{symbol}/{symbol}{day}.csv.gz",
        }
        for symbol,day in sorted(required)
    ]

    return {
        "total_raw_clusters_before_filters":total_clusters,
        "clusters_under_min_events":under_min,
        "mixed_side_clusters_excluded":mixed_side,
        "gap_censored_clusters":gap_censored,
        "eligible_cluster_count":len(eligible),
        "minimum_sample_gate":MIN_SAMPLE,
        "sample_gate_ready":len(eligible)>=MIN_SAMPLE,
        "required_price_archive_count":len(required_files),
        "required_price_archives":required_files,
        "clusters":eligible,
    }


def run_census(root:Path,out:Path,quiet:bool=False)->dict[str,Any]:
    state_path=root/"collector_state.json"
    ledger_path=root/"connection"/"connection_events.jsonl"
    if not state_path.is_file() or state_path.is_symlink():
        fail("collector_state missing/invalid")
    if not ledger_path.is_file() or ledger_path.is_symlink():
        fail("connection ledger missing/invalid")

    state=load_json(state_path)
    if state.get("stage")!="SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3":
        fail("collector state must be v0.3 snapshot")
    if state.get("strategy_outcomes_calculated") is not False:
        fail("collector outcome firewall mismatch")
    if int(state.get("source_qualified_symbols") or 0)!=12:
        fail("source-qualified symbol count mismatch")

    gaps,event_counts=build_source_gaps(state,ledger_path)
    events,event_diag=parse_events(root)
    clusters=cluster_events(events,gaps)

    result={
        "schema":"sc001.b13c_s0_source_only_cluster_census.v0.1",
        "status":PASS,
        "frozen_interval":{
            "start_ms":START_MS,
            "end_ms":END_MS,
            "start_utc":"2026-09-19T06:47:38.969Z",
            "end_utc":"2026-09-26T21:05:32.973Z",
        },
        "frozen_cluster_rule":{
            "inter_event_gap_ms":CLUSTER_GAP_MS,
            "minimum_distinct_events":MIN_EVENTS,
            "pure_side_required":True,
            "gap_censor_padding_ms":GAP_PAD_MS,
            "size_threshold_used":False,
            "size_weighting_used":False,
        },
        "event_diagnostics":event_diag,
        "connection_event_counts":event_counts,
        "merged_source_gap_count":len(gaps),
        "merged_source_gap_ms":sum(b-a for a,b in gaps),
        "cluster_census":{
            k:v for k,v in clusters.items() if k!="clusters"
        },
        "required_price_archives":clusters["required_price_archives"],
        "price_data_opened":False,
        "returns_calculated":False,
        "per_symbol_performance_ranked":False,
        "liquidation_size_distribution_read":False,
        "threshold_tuned":False,
        "pnl_calculated":False,
        "collector_mutation_performed":False,
        "network_calls_performed":False,
        "next_state":(
            "QUALIFY_EXACT_REQUIRED_PRICE_ARCHIVES"
            if clusters["sample_gate_ready"]
            else "B13C_S0_DEFER_SAMPLE"
        ),
    }
    atomic_json(out/"b13c_s0_source_only_cluster_census_manifest.json",result)
    if not quiet:
        print(PASS)
        print("unique_events =",event_diag["unique_events_in_window"])
        print("eligible_clusters =",clusters["eligible_cluster_count"])
        print("sample_gate_ready =",clusters["sample_gate_ready"])
        print("required_price_archives =",clusters["required_price_archive_count"])
    return result


def write_jsonl(path:Path,rows:list[dict[str,Any]])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row,separators=(",",":"))+"\n")


def selftest()->None:
    current=Path(__file__).resolve()
    validate_launcher_args(str(current.parents[2]),str(current))
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/"in"
        out=Path(td)/"out"
        root.mkdir(parents=True)
        atomic_json(root/"collector_state.json",{
            "stage":"SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3",
            "strategy_outcomes_calculated":False,
            "source_qualified_symbols":12,
            "process_restart_gaps":[{"start_ms":START_MS+50_000,"end_ms":START_MS+51_000}],
        })
        write_jsonl(root/"connection"/"connection_events.jsonl",[
            {"stage":"SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3","event":"SUBSCRIBED","ts_ms":START_MS+100,"connection_epoch":"e1"},
            {"stage":"SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3","event":"DISCONNECTED","ts_ms":START_MS+100_000,"connection_epoch":"e1"},
            {"stage":"SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3","event":"SUBSCRIBED","ts_ms":START_MS+101_000,"connection_epoch":"e2"},
        ])
        for day in EVENT_DAYS:
            write_jsonl(root/"events"/f"{day}.jsonl",[])
        base=START_MS+10_000
        rows=[]
        for i,t in enumerate([base,base+1000,base+2000]):
            rows.append({
                "collector_stage":"SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3",
                "recv_ts_ms":t+10,
                "liquidation_ts_ms":t,
                "symbol":"BTCUSDT",
                "liquidated_position_side":"LONG_LIQUIDATED",
                "event_fingerprint_sha256":f"{i+1:064x}",
            })
        # duplicate one exact fingerprint
        dup=dict(rows[-1]); dup["recv_ts_ms"]+=50; rows.append(dup)
        # mixed-side cluster excluded
        mbase=START_MS+30_000
        for i,side in enumerate(["LONG_LIQUIDATED","SHORT_LIQUIDATED","LONG_LIQUIDATED"],10):
            rows.append({
                "collector_stage":"SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3",
                "recv_ts_ms":mbase+i,
                "liquidation_ts_ms":mbase+(i-10)*1000,
                "symbol":"ETHUSDT",
                "liquidated_position_side":side,
                "event_fingerprint_sha256":f"{i:064x}",
            })
        # cluster censored by process gap
        gbase=START_MS+49_000
        for i,t in enumerate([gbase,gbase+1000,gbase+2000],20):
            rows.append({
                "collector_stage":"SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3",
                "recv_ts_ms":t+10,
                "liquidation_ts_ms":t,
                "symbol":"SOLUSDT",
                "liquidated_position_side":"SHORT_LIQUIDATED",
                "event_fingerprint_sha256":f"{i:064x}",
            })
        write_jsonl(root/"events"/"2026-09-19.jsonl",rows)

        r=run_census(root,out,quiet=True)
        assert r["event_diagnostics"]["duplicate_rows_collapsed"]==1
        assert r["cluster_census"]["eligible_cluster_count"]==1
        assert r["cluster_census"]["mixed_side_clusters_excluded"]==1
        assert r["cluster_census"]["gap_censored_clusters"]==1
        assert r["price_data_opened"] is False
    print(SELFTEST_PASS)


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","census"),default="self-test")
    ap.add_argument("--data-root")
    ap.add_argument("--out-dir",default=os.environ.get("OUTPUT_DIR","/work/run/output"))
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)
    if a.mode=="self-test":
        selftest()
        return 0
    if not a.data_root:
        fail("--data-root required")
    root=Path(a.data_root).resolve()
    if not root.is_dir():
        fail("data root missing")
    run_census(root,Path(a.out_dir).resolve())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
