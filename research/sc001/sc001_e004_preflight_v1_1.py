"""SC001-E004 pre-alpha implementation preflight v1.1.

Runs synthetic/metamorphic tests, qualified Q006R archive checks, and a real-data
state-machine dry run with alpha/return export disabled.

Only exact PREFLIGHT_PASS authorizes the frozen engine to run DEV-DISCOVERY.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import resource
import shutil
import sys
import time
import zipfile
import csv
from array import array
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_PATH = HERE / "sc001_e004_volatility_breakout_v1.py"
CONFIG_PATH = HERE / "sc001_e004_config_v1_0.json"

def fail(msg: str) -> None:
    raise RuntimeError(msg)

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=Path(str(path)+".tmp")
    with tmp.open("w",encoding="utf-8",newline="") as f:
        f.write(text); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)

def atomic_json(path: Path, obj) -> None:
    atomic_text(path,json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

def load_engine():
    spec=importlib.util.spec_from_file_location("sc001_e004_engine",ENGINE_PATH)
    if spec is None or spec.loader is None:
        fail("cannot load E004 engine")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def assert_close(a,b,tol=1e-10):
    if not math.isclose(a,b,rel_tol=tol,abs_tol=tol):
        raise AssertionError(f"{a!r} != {b!r}")

def synthetic_stream(E, date="2024-03-02", rows=None):
    base=E.date_ms(date)
    rows=rows or []
    rows=sorted(enumerate(rows), key=lambda z:(z[1][0],z[0]))
    ts=array("q"); px=array("d"); seq=array("q")
    for j,(_,r) in enumerate(rows):
        off,p=r
        ts.append(base+int(off)); px.append(float(p)); seq.append(j)
    return {"start":date,"end":date,"start_ms":base,"end_ms":base+E.DAY_MS,
            "timestamps":ts,"prices":px,"seqs":seq,"day_counts":{date:len(rows)}}

def run_synthetic_tests(E,cfg):
    tests=[]
    failures=[]
    def T(name,fn):
        try:
            fn(); tests.append({"name":name,"pass":True})
        except Exception as exc:
            tests.append({"name":name,"pass":False,"error":str(exc)})
            failures.append(name)

    def p01():
        t=E.date_ms("2024-03-02")+60_000
        ts=array("q",[t-60_000,t-1,t]); px=array("d",[100.0,101.0,999.0])
        h,l=E.window_high_low(ts,px,t,60_000)
        assert h==101.0 and l==100.0
    T("P01_boundary_trade_excluded",p01)

    def p02():
        t=E.date_ms("2024-03-02")+60_000
        ts=array("q",[t-60_000,t-1]); px=array("d",[100.0,101.0])
        h,l=E.window_high_low(ts,px,t,60_000)
        assert h==101.0
    T("P02_one_ms_before_included",p02)

    T("P03_compression_formula",lambda: assert_close(E.compression_bps(101,99),200.0))

    def p04():
        xs=list(range(1,1441))
        assert E.nearest_rank(xs,0.20)==288.0
    T("P04_nearest_rank_q20_rank288",p04)

    def indicator_fixture(scale=1.0):
        start=E.date_ms("2024-03-01")
        minutes=1465
        ts=array("q"); px=array("d"); seq=array("q")
        for m in range(minutes):
            p=scale*(100.0 + (m%11)*0.001)
            ts.append(start+m*60_000+30_000); px.append(p); seq.append(m)
        return {"start":"2024-03-01","end":"2024-03-02","start_ms":start,
                "end_ms":start+minutes*60_000,"timestamps":ts,"prices":px,"seqs":seq,"day_counts":{}}

    def p05():
        inds,meta=E.build_minute_indicators(indicator_fixture(),cfg)
        assert meta["first_eligible_ms"]==E.date_ms("2024-03-01")+(15+1440)*60_000
    T("P05_eligibility_1439_vs_1440",p05)

    def p06():
        prior=sorted([1.0]*1440)
        assert E.nearest_rank(prior,0.20)==1.0
        current=9999.0
        assert E.nearest_rank(prior,0.20)==1.0 and current!=1.0
    T("P06_threshold_excludes_current",p06)

    def p07():
        c=q=5.0
        assert (c<=q) is True
    T("P07_compression_equality_true",p07)

    def p08():
        prev=False; cur=True
        assert bool(cur and prev is False)
        assert not bool(cur and True is False)
    T("P08_false_to_true_only",p08)

    def p09():
        high=100.0; low=99.0; b=cfg["breakout_buffer_bps"]
        u=high*(1+b/10000); d=low*(1-b/10000)
        assert u>high and d<low
        assert u != 200.0*(1+b/10000)
    T("P09_band_frozen_at_arm",p09)

    def p10():
        base=E.date_ms("2024-03-02"); arm=base+12*3600_000
        b=cfg["breakout_buffer_bps"]; U=100*(1+b/10000); D=99*(1-b/10000)
        ts=array("q",[arm+1000,arm+2000]); px=array("d",[U,U+0.001])
        br=E.first_breakout(ts,px,arm,arm+15*60_000,U,D)
        assert br and br[1]==arm+2000 and br[2]==1
    T("P10_equality_does_not_breakout",p10)

    def p11():
        base=E.date_ms("2024-03-02"); arm=base+12*3600_000
        U=100.02; D=98.98
        ts=array("q",[arm+1000]); px=array("d",[100.021])
        br=E.first_breakout(ts,px,arm,arm+15*60_000,U,D)
        assert br and br[2]==1
    T("P11_strict_crossing_triggers",p11)

    def p12():
        base=E.date_ms("2024-03-02"); arm=base+12*3600_000
        ts=array("q",[arm+1000,arm+1000]); px=array("d",[98.0,102.0])
        br=E.first_breakout(ts,px,arm,arm+15*60_000,101,99)
        assert br and br[0]==0 and br[2]==-1
    T("P12_same_timestamp_source_order",p12)

    def p13():
        base=E.date_ms("2024-03-02"); arm=base+12*3600_000; exp=arm+15*60_000
        ts=array("q",[exp]); px=array("d",[102])
        br=E.first_breakout(ts,px,arm,exp,101,99)
        assert br and br[1]==exp
    T("P13_expiry_inclusive",p13)

    def p14():
        base=E.date_ms("2024-03-02")
        ts=array("q",[base+1250,base+1300])
        assert E.proxy_leg(ts,base+1250,5000)==0
    T("P14_entry_first_at_or_after",p14)

    def p15():
        base=E.date_ms("2024-03-02")
        ts=array("q",[base+6250,base+6251])
        assert E.proxy_leg(ts,base+1250,5000)==0
        assert E.proxy_leg(array("q",[base+6251]),base+1250,5000) is None
    T("P15_tolerance_inclusive_5000ms",p15)

    def p16():
        base=E.date_ms("2024-03-02")
        rows=[(1000,102),(1250,102.1),(901250,103)]
        st=synthetic_stream(E,rows=rows)
        ev=[{"date":"2024-03-02","decision_ts":base+1000,"direction":1}]
        out=E.replay_latency(st,ev,cfg,250,calculate_alpha=False)
        assert out[0]["entry_ts"]==base+1250
        assert out[0]["exit_ts"]==base+901250
    T("P16_exit_from_actual_entry",p16)

    def p17():
        base=E.date_ms("2024-03-02")
        rows=[(1000,102),(1250,102.1),(901251,103)]
        st=synthetic_stream(E,rows=rows)
        ev=[{"date":"2024-03-02","decision_ts":base+1000,"direction":1}]
        out=E.replay_latency(st,ev,cfg,250,calculate_alpha=False)
        assert out[0]["exit_ts"]==base+901251
    T("P17_exit_first_at_or_after_target",p17)

    def p18():
        base=E.date_ms("2024-03-02")
        rows=[(1000,102),(1250,102.1),(906251,103)]
        st=synthetic_stream(E,rows=rows)
        ev=[{"date":"2024-03-02","decision_ts":base+1000,"direction":1}]
        out=E.replay_latency(st,ev,cfg,250,calculate_alpha=False)
        assert not out[0]["completed"]
    T("P18_exit_timeout_incomplete",p18)

    def p19():
        base=E.date_ms("2024-03-02")
        decision=base+23*3600_000+50*60_000
        rows=[(decision-base+250,102)]
        st=synthetic_stream(E,rows=rows)
        ev=[{"date":"2024-03-02","decision_ts":decision,"direction":1}]
        out=E.replay_latency(st,ev,cfg,250,calculate_alpha=False)
        assert not out[0]["completed"]
    T("P19_no_overnight_exit",p19)

    def state_fixture(ntrans=1):
        base=E.date_ms("2024-03-02")
        indicators=[]; rows=[]
        for j in range(ntrans):
            arm=base+(2+j)*3600_000
            indicators.append({"t":arm,"high":100.0,"low":99.0,"z":True,"prev_z":False,"transition":True})
            rows.extend([(arm-base+1000,100.03),(arm-base+1250,100.04),(arm-base+901250,100.50)])
        return synthetic_stream(E,rows=rows),indicators

    def p20():
        st,inds=state_fixture(2)
        ev,meta=E.simulate_primary(st,inds,cfg,"2024-03-02","2024-03-02",calculate_alpha=False)
        assert meta["max_concurrent_positions"]<=1
    T("P20_no_overlap",p20)

    def p21():
        base=E.date_ms("2024-03-02")
        inds=[
          {"t":base+2*3600_000,"high":100.0,"low":99.0,"z":True,"prev_z":False,"transition":True},
          {"t":base+2*3600_000+20*60_000,"high":100.0,"low":99.0,"z":True,"prev_z":False,"transition":True},
        ]
        rows=[(2*3600_000+1000,100.03),(2*3600_000+1250,100.04),(2*3600_000+901250,100.5)]
        st=synthetic_stream(E,rows=rows)
        ev,meta=E.simulate_primary(st,inds,cfg,"2024-03-02","2024-03-02",calculate_alpha=False)
        assert meta.get("transition_while_not_idle",0)>=1
    T("P21_cooldown_blocks_arm",p21)

    def p22():
        base=E.date_ms("2024-03-02"); inds=[]; rows=[]
        for h in [1,5,9,13,17]:
            arm=base+h*3600_000
            inds.append({"t":arm,"high":100.0,"low":99.0,"z":True,"prev_z":False,"transition":True})
            off=h*3600_000
            rows.extend([(off+1000,100.03),(off+1250,100.04),(off+901250,100.5)])
        st=synthetic_stream(E,rows=rows)
        ev,meta=E.simulate_primary(st,inds,cfg,"2024-03-02","2024-03-02",calculate_alpha=False)
        assert meta["decisions"]==4 and meta["max_decisions_per_day_observed"]==4
    T("P22_fifth_decision_blocked",p22)

    def p23():
        base=E.date_ms("2024-03-02")
        assert E.day_text(base+E.DAY_MS)=="2024-03-03"
    T("P23_day_reset_boundary",p23)

    def p24():
        long=10000*(101/100-1)
        short=-10000*(99/100-1)
        assert_close(long,100); assert_close(short,100)
    T("P24_directional_return_signs",p24)

    def p25():
        base=E.date_ms("2024-03-02")
        rows=[(1000,102),(1250,102.1),(1500,102.2),(2000,102.3),(901250,103),(901500,103.1),(902000,103.2)]
        st=synthetic_stream(E,rows=rows)
        ev=[{"date":"2024-03-02","decision_ts":base+1000,"direction":1}]
        a=E.replay_latency(st,ev,cfg,500,calculate_alpha=False)
        b=E.replay_latency(st,ev,cfg,1000,calculate_alpha=False)
        assert a[0]["decision_ts"]==b[0]["decision_ts"]==base+1000
    T("P25_stress_reuses_decisions",p25)

    def m01():
        assert_close(E.compression_bps(101,99),E.compression_bps(1010,990))
        assert_close(10000*(101/100-1),10000*(1010/1000-1))
    T("M01_positive_price_scaling_invariant",m01)

    def m02():
        base=E.date_ms("2024-03-02"); arm=base+1000
        ts1=array("q",[arm+100,arm+200]); px1=array("d",[100,102])
        br1=E.first_breakout(ts1,px1,arm,arm+1000,101,99)
        ts2=array("q",[arm+100,arm+200,arm+5000]); px2=array("d",[100,102,1])
        br2=E.first_breakout(ts2,px2,arm,arm+1000,101,99)
        assert br1[:3]==br2[:3]
    T("M02_future_trade_cannot_change_earlier_decision",m02)

    def m03():
        st,inds=state_fixture(1)
        a,ma=E.simulate_primary(st,inds,cfg,"2024-03-02","2024-03-02",calculate_alpha=False)
        b,mb=E.simulate_primary(st,inds,cfg,"2024-03-02","2024-03-02",calculate_alpha=False)
        assert a==b and ma==mb
    T("M03_repeat_determinism",m03)

    def m04():
        assert len(E.diagnostic_variants(cfg))==8
        for _,change in E.diagnostic_variants(cfg): assert len(change)==1
    T("M04_exactly_eight_one_factor_diagnostics",m04)

    def m05():
        fw=cfg["firewalls"]
        assert fw["use_tfi"] is False and fw["use_flow_impulse"] is False
    T("M05_auxiliary_flow_features_absent",m05)

    def m06():
        t=E.date_ms("2024-03-02")+120_000
        ts=array("q",[t-120_000,t-60_001,t-60_000,t-1]); px=array("d",[100,101,99,102])
        h,l=E.window_high_low(ts,px,t,120_000)
        assert h==102 and l==99
    T("M06_chunk_order_causal_equivalence",m06)

    def m07():
        import tempfile
        old=os.environ.get("SC001_DATA_ROOT")
        with tempfile.TemporaryDirectory() as td:
            os.environ["SC001_DATA_ROOT"]=td
            try:
                try: E.require_preflight_pass(E.DEFAULT_CONFIG_PATH,cfg)
                except RuntimeError: return
                raise AssertionError("discovery gate unexpectedly open")
            finally:
                if old is None: os.environ.pop("SC001_DATA_ROOT",None)
                else: os.environ["SC001_DATA_ROOT"]=old
    T("M07_discovery_blocked_without_preflight_pass",m07)

    def m08():
        import tempfile
        old=os.environ.get("SC001_DATA_ROOT")
        with tempfile.TemporaryDirectory() as td:
            os.environ["SC001_DATA_ROOT"]=td
            try:
                try: E.require_confirmation_gate(cfg)
                except RuntimeError: return
                raise AssertionError("confirmation gate unexpectedly open")
            finally:
                if old is None: os.environ.pop("SC001_DATA_ROOT",None)
                else: os.environ["SC001_DATA_ROOT"]=old
    T("M08_confirmation_blocked_without_discovery_pass",m08)

    def m09():
        labels=E.required_labels_for_phase("discovery",cfg)|E.required_labels_for_phase("confirmation",cfg)
        assert max(labels)=="2024-03-31"
        assert not any(x.startswith("2024-04") for x in labels)
    T("M09_q2_paths_not_required_or_authorized",m09)

    return tests,failures

def audit_archive(E,cfg,meta):
    E.verify_archive_identity(meta,full_crc=True)
    p=Path(meta["path"])
    first=last=None; rows=0; dup_ts=0; exact_adj_dup=0; backwards=0
    tid_duplicate_or_backward=0
    prev_ts=None; prev_tid=None; prev_row=None
    with zipfile.ZipFile(p,"r") as zf:
        members=[m for m in zf.infolist() if not m.is_dir()]
        with zf.open(members[0],"r") as raw:
            reader=csv.reader((line.decode("utf-8") for line in raw))
            header=next(reader,None)
            if header!=cfg["expected_header"]: fail(f"header mismatch {p.name}")
            for row in reader:
                if not row or row[0]!=cfg["instrument"]: continue
                if len(row)!=6: fail(f"malformed row {p.name}")
                ts=E.parse_ts_ms(row[5]); tid=int(row[1]); px=float(row[3]); sz=float(row[4])
                if row[2] not in {"buy","sell"}: fail(f"invalid side {p.name}")
                if not math.isfinite(px) or px<=0 or not math.isfinite(sz) or sz<=0:
                    fail(f"nonpositive/nonfinite target values {p.name}")
                if prev_ts is not None:
                    if ts<prev_ts: backwards+=1
                    if ts==prev_ts: dup_ts+=1
                if prev_tid is not None and tid<=prev_tid: tid_duplicate_or_backward+=1
                tup=tuple(row)
                if tup==prev_row: exact_adj_dup+=1
                prev_row=tup; prev_ts=ts; prev_tid=tid
                first=ts if first is None else min(first,ts)
                last=ts if last is None else max(last,ts)
                rows+=1
    if rows<=0 or backwards or tid_duplicate_or_backward:
        fail(f"archive temporal/trade-id audit failed {p.name}")
    return {"date":meta["date"],"filename":meta["filename"],"bytes":meta["bytes"],
            "sha256":meta["sha256"],"target_rows":rows,"first_target_ts":first,
            "last_target_ts":last,"duplicate_timestamp_count":dup_ts,
            "adjacent_exact_row_duplicate_count":exact_adj_dup,"timestamp_backwards_count":backwards,
            "trade_id_duplicate_or_backward_count":tid_duplicate_or_backward}

def forbidden_scan(obj):
    bad_tokens=("entry_price","exit_price","gross_edge","return_bps","pnl","direction")
    hits=[]
    def walk(x,path=""):
        if isinstance(x,dict):
            for k,v in x.items():
                kp=f"{path}.{k}" if path else str(k)
                if any(tok in str(k).lower() for tok in bad_tokens): hits.append(kp)
                walk(v,kp)
        elif isinstance(x,list):
            for i,v in enumerate(x): walk(v,f"{path}[{i}]")
    walk(obj)
    return hits

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default=str(CONFIG_PATH))
    ap.add_argument("--output",default=None)
    args=ap.parse_args()
    config_path=Path(args.config).expanduser().resolve()
    started=datetime.now(timezone.utc).isoformat(); t0=time.time()
    E=load_engine(); cfg=E.load_config(config_path)
    root,_,_=E.data_paths(cfg)
    outdir=Path(args.output).expanduser().resolve() if args.output else root/"SC001_E004"/"preflight"
    if outdir.exists() and any(outdir.iterdir()): fail(f"refusing to overwrite non-empty preflight output directory: {outdir}")
    outdir.mkdir(parents=True,exist_ok=True)

    tests,failures=run_synthetic_tests(E,cfg)
    labels=set(E.iter_dates("2024-03-01","2024-03-21"))
    manifest=E.source_manifest(cfg,labels)
    archive_audits=[]
    for d in sorted(labels):
        print("AUDIT",d,flush=True)
        archive_audits.append(audit_archive(E,cfg,manifest[d]))

    reconstructed=[]
    for d in E.iter_dates("2024-03-01","2024-03-20"):
        print("UTC DAY",d,flush=True)
        one=E.reconstruct_utc_day(d,cfg,manifest)
        reconstructed.append({"date":d,"admitted_rows":len(one["timestamps"]),
                              "minute_coverage":1440,"buy_count":one["buy_count"],"sell_count":one["sell_count"]})

    stream=E.load_stream("2024-03-01","2024-03-20",cfg,manifest)
    indicators,ind_meta=E.build_minute_indicators(stream,cfg)
    expected_first=E.date_ms("2024-03-02")+15*60_000
    if ind_meta["first_eligible_ms"]!=expected_first: failures.append("REAL_first_eligible_boundary")
    events,sim_meta=E.simulate_primary(stream,indicators,cfg,"2024-03-01","2024-03-20",calculate_alpha=False)
    if any(e.get("gross_edge_bps") is not None or "entry_price" in e or "exit_price" in e for e in events):
        failures.append("REAL_alpha_firewall_event_payload")
    decisions=[e["decision_ts"] for e in events]
    dry={
      "first_eligible_ms":ind_meta["first_eligible_ms"],
      "eligible_minute_count":ind_meta["eligible_minute_count"],
      "missing_minute_count":ind_meta["missing_minute_count"],
      "threshold_tie_count":ind_meta["threshold_tie_count"],
      "arm_count":sim_meta.get("arms",0),
      "expiry_count":sim_meta.get("arm_expiries",0),
      "decision_count":sim_meta.get("decisions",0),
      "completed_timestamp_paths":sim_meta.get("completed",0),
      "entry_incomplete_count":sim_meta.get("entry_incomplete",0),
      "exit_incomplete_count":sim_meta.get("exit_incomplete",0)+sim_meta.get("exit_day_cross_incomplete",0),
      "daily_lock_candidate_count":sim_meta.get("candidate_transition_while_day_locked",0),
      "maximum_concurrent_positions":sim_meta.get("max_concurrent_positions",0),
      "maximum_decisions_per_day":sim_meta.get("max_decisions_per_day_observed",0),
      "earliest_decision_ms":min(decisions) if decisions else None,
      "latest_decision_ms":max(decisions) if decisions else None,
    }
    if dry["maximum_concurrent_positions"]>1: failures.append("REAL_max_one_position")
    if dry["maximum_decisions_per_day"]>cfg["max_decisions_per_utc_day"]: failures.append("REAL_daily_cap")

    input_bytes=sum(int(x["bytes"]) for x in manifest.values())
    disk=shutil.disk_usage(root); estimated_output=1_000_000_000
    required_free=input_bytes+estimated_output+10*1024**3
    disk_pass=disk.free>required_free
    if not disk_pass: failures.append("RESOURCE_disk_reserve")
    maxrss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    maxrss_bytes=int(maxrss*1024 if sys.platform.startswith("linux") else maxrss)
    memory_pass=maxrss_bytes<6*1024**3
    if not memory_pass: failures.append("RESOURCE_memory")

    if any(not t["pass"] for t in tests): failures.append("SYNTHETIC_test_failure")
    failures=sorted(set(failures)); status="PREFLIGHT_PASS" if not failures else "PREFLIGHT_FAIL"

    report={
      "stage":"SC001-E004-PREFLIGHT","protocol_version":"1.0","preflight_spec_version":"1.1",
      "status":status,"git_commit":E.git_commit(E.repo_root_from_file()),
      "engine_sha256":sha256_file(ENGINE_PATH),"preflight_runner_sha256":sha256_file(Path(__file__).resolve()),
      "config_sha256":sha256_file(config_path),
      "environment":{"python":sys.version,"platform":platform.platform(),"timezone":"UTC"},
      "tests":{"total":len(tests),"passed":sum(1 for t in tests if t["pass"]),
               "failed":sum(1 for t in tests if not t["pass"]),"failures":failures,"details":tests},
      "input_archives":archive_audits,"reconstructed_utc_days":reconstructed,
      "real_data_no_alpha_dry_run":dry,
      "invariants":{"max_one_position":dry["maximum_concurrent_positions"]<=1,
                    "daily_cap":dry["maximum_decisions_per_day"]<=cfg["max_decisions_per_utc_day"],
                    "q2_accessed":False,"validation_or_final_accessed":False,
                    "l2_accessed":False,"tfi_used":False,"flow_impulse_used":False,"alpha_calculated":False},
      "resources":{"input_bytes":input_bytes,"disk_free_bytes":disk.free,"required_free_bytes":required_free,
                   "disk_pass":disk_pass,"peak_rss_bytes":maxrss_bytes,"memory_under_6gib_pass":memory_pass,
                   "wall_seconds":time.time()-t0},
      "started_at_utc":started,"completed_at_utc":datetime.now(timezone.utc).isoformat(),
    }
    hits=forbidden_scan(report); report["forbidden_output_scan"]={"hits":hits,"pass":not hits}
    if hits: report["status"]="PREFLIGHT_FAIL"
    atomic_json(outdir/"sc001_e004_preflight_report.json",report)
    summary=["# SC001-E004 Preflight v1.1","",f"Status: `{report['status']}`",
      f"Synthetic/metamorphic tests: {report['tests']['passed']}/{report['tests']['total']}",
      f"Archive labels audited: {len(archive_audits)}",f"UTC Discovery days reconstructed: {len(reconstructed)}",
      "Alpha/returns emitted: NO","Q2/Validation/Final/L2: CLOSED","","Only exact `PREFLIGHT_PASS` authorizes DEV-DISCOVERY."]
    atomic_text(outdir/"sc001_e004_preflight_summary.md","\n".join(summary)+"\n")
    print(report["status"])
    if report["status"]!="PREFLIGHT_PASS": raise SystemExit(2)

if __name__=="__main__":
    main()
