#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PASS="FORCED_FLOW_S0_IMPLEMENTATION_HANDSHAKE_PASS"
REVIEW="FORCED_FLOW_S0_IMPLEMENTATION_HANDSHAKE_REVIEW"
ROOT=Path(__file__).resolve().parents[2]
FREEZE=ROOT/"docs/research/sc001-next-primary-forced-flow-relative-dislocation-s0-implementation-freeze-v0.1.json"

SYMBOLS=(
"BTCUSDT","ETHUSDT","SOLUSDT","DOGEUSDT","ORDIUSDT","FILUSDT",
"UNIUSDT","XRPUSDT","LTCUSDT","OPUSDT","BCHUSDT","SUIUSDT",
)
WINDOW_START_MS=1790726400000
WINDOW_END_MS=1791331200000
H_BPS=52.0
MIN_VALID_CLUSTERS=300
MIN_REP_SYMBOLS=8
MIN_REP_DAYS=5
MIN_BASELINE_OBS=120
LOOKBACK_MS=300000
FROZEN_DATES=("2026-09-30","2026-10-01","2026-10-02","2026-10-03","2026-10-04","2026-10-05","2026-10-06")
PRESSURE={"LONG_LIQUIDATED":-1.0,"SHORT_LIQUIDATED":1.0}

def fail(msg:str)->None:
    raise RuntimeError(msg)

def git_blob(path:Path)->str:
    return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(path.relative_to(ROOT))],text=True).strip()

def load_json(path:Path)->dict:
    if not path.is_file() or path.is_symlink():
        fail(f"missing/invalid JSON: {path}")
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail(f"object expected: {path}")
    return obj

def require_freeze()->dict:
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_FORCED_FLOW_S0_IMPLEMENTATION_HANDSHAKE":
        fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()):
        fail("runner blob mismatch")
    parents=fr.get("parents")
    if not isinstance(parents,list) or not parents:
        fail("parents missing")
    for rec in parents:
        if not isinstance(rec,dict):
            fail("parent record invalid")
        p=ROOT/str(rec.get("path") or "")
        if not p.is_file() or p.is_symlink():
            fail(f"parent missing: {p}")
        if git_blob(p)!=rec.get("git_blob_sha"):
            fail(f"parent blob mismatch: {rec.get('path')}")
    if tuple(fr.get("frozen_symbols") or [])!=SYMBOLS:
        fail("universe mismatch")
    if int(fr.get("window_start_ms") or 0)!=WINDOW_START_MS or int(fr.get("window_end_ms") or 0)!=WINDOW_END_MS:
        fail("fresh window mismatch")
    if float(fr.get("H_bps"))!=H_BPS:
        fail("H mismatch")
    if fr.get("s0_execution_authorized") is not False:
        fail("S0 authorization firewall mismatch")
    return fr

def utc_date(ms:int)->str:
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).date().isoformat()

def med(xs:list[float])->float:
    if not xs:
        fail("median empty")
    return float(statistics.median(xs))

def raw_basis(bybit:float,okx:float)->float:
    if not (math.isfinite(bybit) and bybit>0 and math.isfinite(okx) and okx>0):
        fail("invalid price")
    return 10000.0*math.log(bybit/okx)

def validate_cluster(r:dict)->None:
    required={"cluster_id","symbol","cluster_end_ms","liquidated_side","distinct_event_count","max_inter_event_gap_ms","source_gap_pass"}
    if not required.issubset(r):
        fail("cluster fields missing")
    if r["symbol"] not in SYMBOLS:
        fail("cluster symbol")
    end=int(r["cluster_end_ms"])
    if not (WINDOW_START_MS<=end<WINDOW_END_MS):
        fail("cluster outside frozen window")
    if r["liquidated_side"] not in PRESSURE:
        fail("cluster side")
    if int(r["distinct_event_count"])<3:
        fail("cluster distinct count")
    if int(r["max_inter_event_gap_ms"])>5000:
        fail("cluster gap")
    if r["source_gap_pass"] is not True:
        fail("cluster source gap")

def validate_coactive(r:dict)->None:
    required={"symbol","second_start_ms","bybit_price","okx_price","source_identity_pass"}
    if not required.issubset(r):
        fail("coactive fields missing")
    if r["symbol"] not in SYMBOLS:
        fail("coactive symbol")
    s=int(r["second_start_ms"])
    if s%1000!=0:
        fail("coactive second not aligned")
    if r["source_identity_pass"] is not True:
        fail("source identity not pass")
    raw_basis(float(r["bybit_price"]),float(r["okx_price"]))

def index_coactive(rows:list[dict])->dict[str,dict[int,tuple[float,float]]]:
    out={s:{} for s in SYMBOLS}
    for r in rows:
        validate_coactive(r)
        sym=r["symbol"]; sec=int(r["second_start_ms"])
        if sec in out[sym]:
            fail("duplicate symbol+second")
        out[sym][sec]=(float(r["bybit_price"]),float(r["okx_price"]))
    return out

def cluster_metric(c:dict,idx:dict[str,dict[int,tuple[float,float]]])->dict|None:
    validate_cluster(c)
    sym=c["symbol"]; end=int(c["cluster_end_ms"])
    candidates=[sec for sec in idx[sym] if end+1000<=sec<end+2000]
    if not candidates:
        return None
    obs=min(candidates)
    bp,op=idx[sym][obs]
    current=raw_basis(bp,op)
    prior=[]
    for sec,(b,o) in idx[sym].items():
        if obs-LOOKBACK_MS<=sec<obs:
            prior.append(raw_basis(b,o))
    if len(prior)<MIN_BASELINE_OBS:
        return None
    ref=med(prior)
    dev=current-ref
    ff=PRESSURE[c["liquidated_side"]]*dev
    return {
      "cluster_id":c["cluster_id"],"symbol":sym,"cluster_end_ms":end,
      "utc_date":utc_date(end),"observation_second_start_ms":obs,
      "baseline_observation_count":len(prior),"raw_basis_bps":current,
      "local_basis_ref_bps":ref,"relative_dev_bps":dev,
      "forced_flow_dislocation_bps":ff,
    }

def summarize(metrics:list[dict])->dict:
    by_sym={s:[] for s in SYMBOLS}
    by_day={d:[] for d in FROZEN_DATES}
    for m in metrics:
        by_sym[m["symbol"]].append(float(m["forced_flow_dislocation_bps"]))
        if m["utc_date"] in by_day:
            by_day[m["utc_date"]].append(float(m["forced_flow_dislocation_bps"]))
    sym_medians={s:(med(v) if v else None) for s,v in by_sym.items()}
    day_medians={d:(med(v) if v else None) for d,v in by_day.items()}
    pos_sym=sum(1 for v in sym_medians.values() if v is not None and v>0)
    pos_day=sum(1 for v in day_medians.values() if v is not None and v>0)
    represented_symbols=sum(1 for v in by_sym.values() if v)
    represented_days=sum(1 for v in by_day.values() if v)
    source_sample_pass=(
      len(metrics)>=MIN_VALID_CLUSTERS and
      represented_symbols>=MIN_REP_SYMBOLS and
      represented_days>=MIN_REP_DAYS
    )
    pooled=med([float(m["forced_flow_dislocation_bps"]) for m in metrics]) if metrics else None
    if not source_sample_pass:
        terminal="DEFER_SOURCE_OR_SAMPLE"
    elif pooled is not None and pooled>=H_BPS and pos_sym>=6 and pos_day>=5:
        terminal="SURVIVE_HEADROOM"
    else:
        terminal="REJECT_FORCED_FLOW_RELATIVE_HEADROOM"
    return {
      "valid_cluster_count":len(metrics),
      "represented_symbol_count":represented_symbols,
      "represented_frozen_date_count":represented_days,
      "pooled_median_forced_flow_dislocation_bps":pooled,
      "symbol_medians":sym_medians,
      "day_medians":day_medians,
      "positive_frozen_symbols":pos_sym,
      "positive_frozen_utc_dates":pos_day,
      "source_sample_gate_pass":source_sample_pass,
      "terminal_state":terminal,
    }

def load_jsonl(path:Path)->list[dict]:
    if not path.is_file() or path.is_symlink():
        fail(f"input missing: {path}")
    out=[]
    for i,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        obj=json.loads(line)
        if not isinstance(obj,dict): fail(f"JSONL object expected line {i}")
        out.append(obj)
    return out

def require_authorization(path:Path,fr:dict)->dict:
    auth=load_json(path)
    if auth.get("status")!="S0_EXECUTION_AUTHORIZED":
        fail("S0 authorization status missing")
    if auth.get("task_id")!="SC001-NEXT-PRIMARY-PREFREEZE-01":
        fail("S0 authorization task mismatch")
    if auth.get("implementation_freeze_path")!=str(FREEZE.relative_to(ROOT)):
        fail("S0 authorization freeze path mismatch")
    if auth.get("implementation_freeze_git_blob_sha")!=git_blob(FREEZE):
        fail("S0 authorization freeze blob mismatch")
    if auth.get("outcome_scope")!="S0_ONLY_FORCED_FLOW_DISLOCATION":
        fail("S0 authorization scope mismatch")
    return auth

def write_json(path:Path,obj:dict)->None:
    if path.exists():
        fail("output collision")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def self_test()->dict:
    fr=require_freeze()
    base_sec=WINDOW_START_MS+600000
    rows=[]
    for i in range(130):
        sec=base_sec-(130-i)*1000
        rows.append({"symbol":"BTCUSDT","second_start_ms":sec,"bybit_price":100.0,"okx_price":100.0,"source_identity_pass":True})
    cluster_end=base_sec-1500
    rows.append({"symbol":"BTCUSDT","second_start_ms":base_sec,"bybit_price":101.0,"okx_price":100.0,"source_identity_pass":True})
    idx=index_coactive(rows)
    c={"cluster_id":"SYN1","symbol":"BTCUSDT","cluster_end_ms":cluster_end,"liquidated_side":"SHORT_LIQUIDATED","distinct_event_count":3,"max_inter_event_gap_ms":5000,"source_gap_pass":True}
    m=cluster_metric(c,idx)
    if m is None: fail("synthetic metric missing")
    if m["baseline_observation_count"]!=130: fail("baseline count")
    if not (99.0<m["forced_flow_dislocation_bps"]<100.0): fail("pressure/basis formula")
    c2=dict(c); c2["liquidated_side"]="LONG_LIQUIDATED"; c2["cluster_id"]="SYN2"
    m2=cluster_metric(c2,idx)
    if m2 is None or m2["forced_flow_dislocation_bps"]>=0: fail("long pressure sign")
    short_rows=[r for r in rows if int(r["second_start_ms"])>=base_sec-119000]
    if cluster_metric(c,index_coactive(short_rows)) is not None: fail("minimum 120 gate")
    s=summarize([m])
    if len(s["day_medians"])!=7 or len(s["symbol_medians"])!=12: fail("fixed denominator")
    if sum(1 for v in s["day_medians"].values() if v is None)!=6: fail("null day semantics")
    if sum(1 for v in s["symbol_medians"].values() if v is None)!=11: fail("null symbol semantics")
    bad=dict(rows[0]); bad["second_start_ms"]=rows[0]["second_start_ms"]+1
    try:
        index_coactive([bad]); fail("malformed second accepted")
    except RuntimeError as e:
        if str(e)=="malformed second accepted": raise
    try:
        index_coactive([rows[0],dict(rows[0])]); fail("duplicate accepted")
    except RuntimeError as e:
        if str(e)=="duplicate accepted": raise
    try:
        require_authorization(Path("/definitely/missing/authorization.json"),fr)
        fail("missing authorization accepted")
    except RuntimeError as e:
        if str(e)=="missing authorization accepted": raise
    return {
      "freeze_handshake_pass":True,"synthetic_pressure_sign_pass":True,
      "synthetic_causal_baseline_pass":True,"current_second_exclusion_pass":True,
      "minimum_120_gate_pass":True,"exact_observation_bucket_pass":True,
      "fixed_7_day_denominator_pass":True,"fixed_12_symbol_denominator_pass":True,
      "malformed_fixture_rejected":True,"duplicate_fixture_rejected":True,
      "missing_authorization_rejected":True,"output_collision_check_active":True,
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["self-test","analyze"],required=True)
    ap.add_argument("--clusters")
    ap.add_argument("--coactive")
    ap.add_argument("--authorization")
    ap.add_argument("--out-dir",default=os.environ.get("BM_TEST_OUTPUT_DIR",os.environ.get("OUTPUT_DIR",str(Path.cwd()/"test-output"))))
    a=ap.parse_args()
    out_dir=Path(a.out_dir)
    try:
        fr=require_freeze()
        if a.mode=="self-test":
            checks=self_test()
            result={
              "schema":"sc001.forced_flow_s0_implementation_handshake.v0.1",
              "mode":"self-test","status":PASS,"checks":checks,
              "real_input_opened":False,"network_calls_performed":False,
              "price_outcome_accessed":False,"return_calculated":False,
              "pnl_calculated":False,"s0_executed":False
            }
            write_json(out_dir/"forced_flow_s0_implementation_handshake_result.json",result)
            print(PASS); return 0

        if not (a.clusters and a.coactive and a.authorization):
            fail("analyze requires clusters/coactive/authorization")
        require_authorization(Path(a.authorization),fr)
        clusters=load_jsonl(Path(a.clusters))
        coactive=load_jsonl(Path(a.coactive))
        idx=index_coactive(coactive)
        metrics=[]
        seen=set()
        for c in clusters:
            cid=str(c.get("cluster_id"))
            if cid in seen: fail("duplicate cluster_id")
            seen.add(cid)
            try:
                m=cluster_metric(c,idx)
            except RuntimeError as exc:
                # source-gap and malformed clusters are fail-closed inputs, not silently dropped
                raise
            if m is not None: metrics.append(m)
        summary=summarize(metrics)
        result={
          "schema":"sc001.forced_flow_s0_result.v0.1",
          "mode":"analyze","status":summary["terminal_state"],
          "H_bps":H_BPS,"summary":summary,"cluster_metrics":metrics,
          "network_calls_performed":False,"later_price_opened":False,
          "return_calculated":False,"pnl_calculated":False,"trading_performed":False
        }
        write_json(out_dir/"sc001_forced_flow_s0_result_v0.1.json",result)
        print(summary["terminal_state"]); return 0

    except Exception as exc:
        result={
          "schema":"sc001.forced_flow_s0_implementation_handshake.v0.1",
          "mode":a.mode,"status":REVIEW,"error":f"{type(exc).__name__}: {exc}",
          "network_calls_performed":False,"return_calculated":False,
          "pnl_calculated":False
        }
        try: write_json(out_dir/"forced_flow_s0_implementation_handshake_review.json",result)
        except Exception: pass
        print(REVIEW); print(result["error"]); return 2

if __name__=="__main__":
    raise SystemExit(main())
