#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess
from pathlib import Path

PASS="FORCED_FLOW_S0_PROVENANCE_PLANNER_PASS"
REVIEW="FORCED_FLOW_S0_PROVENANCE_PLANNER_REVIEW"
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"docs/research/sc001-next-primary-forced-flow-relative-dislocation-s0-input-provenance-contract-v0.1.json"
PROTOCOL=ROOT/"docs/research/sc001-next-primary-forced-flow-relative-dislocation-s0-input-provenance-materialization-protocol-v0.1.md"
FREEZE=ROOT/"docs/research/sc001-next-primary-forced-flow-relative-dislocation-s0-input-provenance-planner-freeze-v0.1.json"

SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","DOGEUSDT","ORDIUSDT","FILUSDT","UNIUSDT","XRPUSDT","LTCUSDT","OPUSDT","BCHUSDT","SUIUSDT")
BASES=tuple(s[:-4] for s in SYMBOLS)
EVENT_DATES=("2026-09-30","2026-10-01","2026-10-02","2026-10-03","2026-10-04","2026-10-05","2026-10-06")
TRADE_DATES=("2026-09-29","2026-09-30","2026-10-01","2026-10-02","2026-10-03","2026-10-04","2026-10-05","2026-10-06","2026-10-07")

def fail(msg:str)->None: raise RuntimeError(msg)

def git_blob(p:Path)->str:
    return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()

def load_json(p:Path)->dict:
    if not p.is_file() or p.is_symlink(): fail(f"missing/invalid JSON: {p}")
    obj=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj,dict): fail(f"object expected: {p}")
    return obj

def require_freeze()->dict:
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_FORCED_FLOW_S0_PROVENANCE_PLANNER":
        fail("freeze status mismatch")
    for key,path in (("runner_git_blob_sha",Path(__file__).resolve()),("contract_git_blob_sha",CONTRACT),("protocol_git_blob_sha",PROTOCOL)):
        if fr.get(key)!=git_blob(path): fail(f"freeze identity mismatch: {key}")
    if tuple(fr.get("symbols") or ())!=SYMBOLS: fail("symbol freeze mismatch")
    if tuple(fr.get("trade_dates") or ())!=TRADE_DATES: fail("trade-date freeze mismatch")
    if fr.get("real_materialization_authorized") is not False: fail("materialization firewall mismatch")
    return fr

def build_plan()->dict:
    contract=load_json(CONTRACT)
    if tuple(contract["frozen_symbols"])!=SYMBOLS: fail("contract symbols mismatch")
    if tuple(contract["trade_archive_dates"])!=TRADE_DATES: fail("contract trade dates mismatch")
    event_paths=[
      "SC001_B13C_PROSPECTIVE_LIQUIDATIONS/collector_state.json",
      "SC001_B13C_PROSPECTIVE_LIQUIDATIONS/connection/connection_events.jsonl",
      *[f"SC001_B13C_PROSPECTIVE_LIQUIDATIONS/events/{d}.jsonl" for d in EVENT_DATES],
    ]
    if event_paths!=contract["b13c_inputs"]: fail("contract B13-C inputs mismatch")

    bybit=[]; okx=[]
    for day in TRADE_DATES:
        for symbol,base in zip(SYMBOLS,BASES):
            bname=f"{symbol}{day}.csv.gz"
            bybit.append({
              "venue":"BYBIT","symbol":symbol,"base":base,"utc_day":day,
              "filename":bname,
              "url":f"https://public.bybit.com/trading/{symbol}/{bname}",
              "role":"PUBLIC_LINEAR_PERPETUAL_TRADE_ARCHIVE",
              "body_materialization_authorized":False,
            })
            oname=f"{base}-USDT-SWAP-trades-{day}.zip"
            okx.append({
              "venue":"OKX","inst_id":f"{base}-USDT-SWAP","base":base,"utc_day":day,
              "filename":oname,
              "resolver":"OFFICIAL_OKX_HISTORICAL_DATA_METADATA",
              "trusted_body_host":"static.okx.com",
              "role":"PUBLIC_LINEAR_SWAP_TRADE_ARCHIVE",
              "body_materialization_authorized":False,
            })

    if len(bybit)!=108 or len(okx)!=108: fail("trade identity count mismatch")
    if len(event_paths)!=9: fail("B13-C input count mismatch")

    derived=[
      "MERGED_SOURCE_GAP_LEDGER",
      "LIQUIDATION_CLUSTER_FILE",
      "BYBIT_LAST_VALID_TRADE_PER_SECOND",
      "OKX_LAST_VALID_TRADE_PER_SECOND",
      "STRICT_COACTIVE_INTERSECTION",
      "S0_ANALYZER_INPUT_MANIFEST",
    ]
    return {
      "schema":"sc001.forced_flow_s0_input_provenance_plan.v0.1",
      "status":PASS,
      "task_id":"SC001-NEXT-PRIMARY-PREFREEZE-01",
      "event_window":{"start_utc":"2026-09-30T00:00:00Z","end_exclusive_utc":"2026-10-07T00:00:00Z"},
      "event_source_inputs":[{"logical_path":p,"sha256":None,"bytes":None,"materialized":False} for p in event_paths],
      "bybit_archive_identities":bybit,
      "okx_archive_identities":okx,
      "counts":{
        "event_source_inputs":len(event_paths),
        "bybit_trade_archives":len(bybit),
        "okx_trade_archives":len(okx),
        "total_trade_archive_identities":len(bybit)+len(okx),
        "total_source_identity_records":len(event_paths)+len(bybit)+len(okx),
      },
      "derived_artifact_roles":derived,
      "required_hashing":"SHA256_EXACT_BYTES",
      "real_materialization_authorized":False,
      "archive_body_get_authorized":False,
      "trade_row_access_authorized":False,
      "price_outcome_access_authorized":False,
      "s0_execution_authorized":False,
    }

def write_json(path:Path,obj:dict)->None:
    if path.exists(): fail("output collision")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def selftest()->dict:
    require_freeze()
    p=build_plan()
    assert p["counts"]["bybit_trade_archives"]==108
    assert p["counts"]["okx_trade_archives"]==108
    assert p["counts"]["total_trade_archive_identities"]==216
    assert p["counts"]["event_source_inputs"]==9
    assert p["event_source_inputs"][0]["logical_path"].endswith("collector_state.json")
    assert p["bybit_archive_identities"][0]["utc_day"]=="2026-09-29"
    assert p["bybit_archive_identities"][-1]["utc_day"]=="2026-10-07"
    assert p["okx_archive_identities"][0]["filename"]=="BTC-USDT-SWAP-trades-2026-09-29.zip"
    assert p["archive_body_get_authorized"] is False
    return {"freeze_handshake":True,"counts_exact":True,"boundary_dates_exact":True,"no_materialization":True}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["self-test","plan"],required=True)
    ap.add_argument("--out-dir",default=os.environ.get("BM_TEST_OUTPUT_DIR",os.environ.get("OUTPUT_DIR",str(Path.cwd()/"test-output"))))
    a=ap.parse_args()
    try:
        checks=selftest()
        obj=build_plan()
        obj["mode"]=a.mode
        obj["selftest_checks"]=checks
        write_json(Path(a.out_dir)/"forced_flow_s0_input_provenance_plan.json",obj)
        print(PASS)
        print("trade_archive_identities =",obj["counts"]["total_trade_archive_identities"])
        print("source_identity_records =",obj["counts"]["total_source_identity_records"])
        return 0
    except Exception as exc:
        try:
            write_json(Path(a.out_dir)/"forced_flow_s0_input_provenance_plan_review.json",{
              "schema":"sc001.forced_flow_s0_input_provenance_plan.v0.1","status":REVIEW,
              "error":f"{type(exc).__name__}: {exc}",
              "real_materialization_authorized":False,"price_outcome_access_authorized":False,"s0_execution_authorized":False
            })
        except Exception: pass
        print(REVIEW); print(f"{type(exc).__name__}: {exc}"); return 2

if __name__=="__main__":
    raise SystemExit(main())
