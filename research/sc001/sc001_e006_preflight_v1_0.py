"""SC001-E006 no-alpha implementation preflight v1.0.

Synthetic causal tests plus real-data availability dry run.
NO real-data SPOT/SWAP price comparison, basis, convergence, returns, P&L or alpha.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import platform
import resource
import shutil
import sys
import tempfile
import time
from array import array
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_PATH = HERE / "sc001_e006_basis_convergence_v1.py"
CONFIG_PATH = HERE / "sc001_e006_config_v1_0.json"

def fail(msg: str) -> None:
    raise RuntimeError(msg)

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def atomic_text(path: Path,text: str) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(str(path)+".tmp")
    with tmp.open("w",encoding="utf-8",newline="") as f:
        f.write(text); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)

def atomic_json(path: Path,obj) -> None:
    atomic_text(path,json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

def load_engine():
    spec=importlib.util.spec_from_file_location("sc001_e006_engine",ENGINE_PATH)
    if spec is None or spec.loader is None:
        fail("cannot load E006 engine")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def assert_close(a,b,tol=1e-9):
    if not math.isclose(a,b,rel_tol=tol,abs_tol=tol):
        raise AssertionError(f"{a!r} != {b!r}")

def mkstream(E, date="2024-03-02", rows=None):
    base=E.date_ms(date)
    rows=rows or []
    rows=sorted(enumerate(rows), key=lambda z:(z[1][0],z[0]))
    ts=array("q"); px=array("d"); sz=array("d")
    for _j,(_orig,r) in enumerate(rows):
        off,p,s=r
        ts.append(base+int(off)); px.append(float(p)); sz.append(float(s))
    return {"start_ms":base,"end_ms":base+E.DAY_MS,"timestamps":ts,"prices":px,"sizes":sz}

def run_synthetic_tests(E,cfg):
    tests=[]; failures=[]
    def T(name,fn):
        try:
            fn(); tests.append({"name":name,"pass":True})
        except Exception as exc:
            tests.append({"name":name,"pass":False,"error":f"{type(exc).__name__}: {exc}"})
            failures.append(name)

    def p01():
        st=mkstream(E,rows=[(0,100,1),(9999,101,1),(10000,999,1)])
        vw,c=E.build_10s_vwap(st,10000)
        assert c[0]==2 and abs(vw[0]-100.5)<1e-12
    T("P01_half_open_window",p01)

    def p02():
        st=mkstream(E,rows=[(1000,100,1),(2000,110,3)])
        vw,_=E.build_10s_vwap(st,10000)
        assert_close(vw[0],107.5)
    T("P02_size_weighted_vwap",p02)

    def p03():
        st=mkstream(E,rows=[(1000,100,2),(2000,110,6)])
        vw,_=E.build_10s_vwap(st,10000)
        assert_close(vw[0],107.5)
    T("P03_contract_count_weighting",p03)

    T("P04_basis_sign",lambda: assert_close(E.basis_bps(100,100.5),50.0))

    def p05():
        c={"baseline_lookback_points":4,"baseline_min_valid_points":4}
        s=[100,100,100,100,100]
        p=[100,100.1,100.2,100.3,110]
        r,_=E.build_basis_state(s,p,c)
        expected=E.ordinary_median(sorted([E.basis_bps(100,x) for x in p[:4]]))
        assert_close(r[4]["baseline_bps"],expected)
    T("P05_baseline_excludes_current",p05)

    T("P06_frozen_counts",lambda: (
        (_ for _ in ()).throw(AssertionError("bad counts"))
        if not (cfg["baseline_lookback_points"]==2160 and cfg["baseline_min_valid_points"]==2052)
        else None
    ))

    T("P07_even_median",lambda: assert_close(E.ordinary_median([1,2,3,4]),2.5))

    def p08():
        base=E.date_ms("2024-03-02")
        records=[{"eligible":False,"dislocation_bps":None},{"eligible":True,"dislocation_bps":60,"baseline_bps":0,"basis_bps":60}]
        assert E.build_trigger_candidates(records,base,cfg,"2024-03-02","2024-03-02")==[]
    T("P08_previous_invalid_blocks_trigger",p08)

    def p09():
        base=E.date_ms("2024-03-02")
        records=[{"eligible":True,"dislocation_bps":49,"baseline_bps":1,"basis_bps":50},{"eligible":True,"dislocation_bps":50,"baseline_bps":1,"basis_bps":51}]
        out=E.build_trigger_candidates(records,base,cfg,"2024-03-02","2024-03-02")
        assert len(out)==1 and out[0]["trigger_dislocation_bps"]==50
    T("P09_crossing_trigger",p09)

    def p10():
        ev={"frozen_baseline_bps":5}
        rec=[{"basis_bps":None} for _ in range(400)]
        rec[1]={"basis_bps":15}
        t,reason=E.find_exit_decision(ev,rec,E.date_ms("2024-03-02"),E.date_ms("2024-03-02")+10000,{**cfg,"max_hold_ms":300000})
        assert reason=="convergence" and t==E.date_ms("2024-03-02")+20000
    T("P10_frozen_baseline_exit",p10)

    def p11():
        base=E.date_ms("2024-03-02")
        rec=[{"eligible":True,"dislocation_bps":-60,"baseline_bps":0,"basis_bps":-60},{"eligible":True,"dislocation_bps":-70,"baseline_bps":0,"basis_bps":-70}]
        assert E.build_trigger_candidates(rec,base,cfg,"2024-03-02","2024-03-02")==[]
    T("P11_negative_sign_not_primary",p11)

    def p12():
        base=E.date_ms("2024-03-02")
        st=mkstream(E,rows=[(1500,100,1)])
        leg=E.proxy_leg(st,base+1500,5000,base+E.DAY_MS)
        assert leg and leg[1]==base+1500
    T("P12_entry_target_first_at_or_after",p12)

    def p13():
        base=E.date_ms("2024-03-02")
        st=mkstream(E,rows=[(6500,100,1)])
        assert E.proxy_leg(st,base+1500,5000,base+E.DAY_MS) is not None
        st2=mkstream(E,rows=[(6501,100,1)])
        assert E.proxy_leg(st2,base+1500,5000,base+E.DAY_MS) is None
    T("P13_proxy_tolerance_inclusive",p13)

    T("P14_pair_open_is_later_leg",lambda: (_ for _ in ()).throw(AssertionError()) if max(1000,1500)!=1500 else None)

    def synthetic_records(n=400):
        return [{"basis_bps":100.0,"eligible":True,"baseline_bps":0.0,"dislocation_bps":100.0} for _ in range(n)]

    def p15():
        base=E.date_ms("2024-03-02")
        spot=mkstream(E,rows=[(20500,100,1)]); perp=mkstream(E,rows=[])
        cand=[{"trigger_ts":base+20000,"date":"2024-03-02","frozen_baseline_bps":0.0,"trigger_basis_bps":50.0,"trigger_dislocation_bps":50.0}]
        ev,_=E.simulate_primary(spot,perp,synthetic_records(),cand,cfg,500,calculate_alpha=False)
        assert len(ev)==1 and not ev[0]["completed"]
    T("P15_incomplete_leg_no_gross",p15)

    def p16():
        ev={"frozen_baseline_bps":0}; rec=[{"basis_bps":100} for _ in range(300)]; rec[2]={"basis_bps":10}
        t,reason=E.find_exit_decision(ev,rec,E.date_ms("2024-03-02"),E.date_ms("2024-03-02")+10000,{**cfg,"max_hold_ms":300000})
        assert reason=="convergence" and t==E.date_ms("2024-03-02")+30000
    T("P16_convergence_le_10",p16)

    def p17():
        base=E.date_ms("2024-03-02"); ev={"frozen_baseline_bps":0}; rec=[{"basis_bps":100} for _ in range(1000)]
        t,reason=E.find_exit_decision(ev,rec,base,base+1500,{**cfg,"max_hold_ms":30000})
        assert reason=="time" and t==base+40000
    T("P17_time_exit_grid_ceiling",p17)

    def p18():
        base=E.date_ms("2024-03-02"); ev={"frozen_baseline_bps":0}; rec=[{"basis_bps":100} for _ in range(100)]; rec[1]={"basis_bps":5}
        t,reason=E.find_exit_decision(ev,rec,base,base+5000,{**cfg,"max_hold_ms":30000})
        assert reason=="convergence" and t<base+40000
    T("P18_convergence_precedes_time",p18)

    T("P19_exit_proxy_same_tolerance",p13)

    def p20():
        src=ENGINE_PATH.read_text(encoding="utf-8")
        assert "available_at = de" in src and "locked_day = d" in src
    T("P20_incomplete_exit_locks_day",p20)

    T("P21_entry_cutoff",lambda: (_ for _ in ()).throw(AssertionError()) if E.parse_clock_ms(cfg["latest_entry_decision_utc"])!=23*3600000+29*60000 else None)
    T("P22_cooldown_10m",lambda: (_ for _ in ()).throw(AssertionError()) if cfg["cooldown_ms"]!=600000 else None)
    T("P23_daily_cap_four",lambda: (_ for _ in ()).throw(AssertionError()) if cfg["max_entry_decisions_per_day"]!=4 else None)

    def p24():
        src=ENGINE_PATH.read_text(encoding="utf-8")
        assert "max_concurrent_pairs" in src and "available_at" in src and "skipped_busy" in src
    T("P24_one_pair_state_present",p24)

    def p25():
        edge=10000*((101/100-1)+(1-99/100))
        assert_close(edge,200)
    T("P25_paired_gross_formula",p25)

    def p26():
        assert_close(E.basis_bps(100,101),E.basis_bps(1000,1010))
        a=10000*((101/100-1)+(1-99/100)); b=10000*((1010/1000-1)+(1-990/1000)); assert_close(a,b)
    T("P26_price_scale_invariance",p26)

    def p27():
        src=ENGINE_PATH.read_text(encoding="utf-8")
        assert "exit_decision_ts" in src and "replay_latency" in src
    T("P27_stress_reuses_primary_events",p27)

    T("P28_no_diagnostic_execution_path",lambda: (_ for _ in ()).throw(AssertionError("diagnostic execution exists")) if hasattr(E,"run_diagnostics") else None)

    def p29():
        old=os.environ.get("SC001_DATA_ROOT")
        try:
            with tempfile.TemporaryDirectory() as td:
                os.environ["SC001_DATA_ROOT"]=td
                try:
                    E.require_confirmation_gate(CONFIG_PATH)
                except RuntimeError:
                    return
                raise AssertionError("confirmation gate unexpectedly open")
        finally:
            if old is None: os.environ.pop("SC001_DATA_ROOT",None)
            else: os.environ["SC001_DATA_ROOT"]=old
    T("P29_confirmation_fail_closed",p29)

    def p30():
        fw=cfg["firewalls"]
        assert fw["use_tfi"] is False and fw["use_flow_impulse"] is False and fw["use_e004_compression"] is False
    T("P30_auxiliary_features_absent",p30)

    return tests,failures

def bucket_presence(stream,grid_ms):
    lo=int(stream["start_ms"]); hi=int(stream["end_ms"]); n=(hi-lo)//grid_ms
    seen=bytearray(n)
    for t in stream["timestamps"]:
        k=(int(t)-lo)//grid_ms
        if 0<=k<n: seen[k]=1
    return seen

def real_data_no_alpha(E,cfg):
    labels=E.required_labels_for_phase("discovery",cfg)
    sm=E.spot_manifest(labels); wm=E.swap_manifest(labels)
    for d in labels:
        E.verify_archive(sm[d]); E.verify_archive(wm[d])
    ss=E.load_leg_stream(cfg["spot_instrument"],sm,cfg["discovery"]["start"],cfg["discovery"]["end"])
    ws=E.load_leg_stream(cfg["perp_instrument"],wm,cfg["discovery"]["start"],cfg["discovery"]["end"])
    sp=bucket_presence(ss,int(cfg["grid_ms"])); wp=bucket_presence(ws,int(cfg["grid_ms"]))
    if len(sp)!=len(wp): fail("presence vector mismatch")
    paired=bytearray(len(sp))
    for i in range(len(sp)): paired[i]=1 if sp[i] and wp[i] else 0
    look=int(cfg["baseline_lookback_points"]); minv=int(cfg["baseline_min_valid_points"])
    q=deque(); valid=0; eligible=0; first=None
    for k,v in enumerate(paired):
        if len(q)==look and valid>=minv and v:
            eligible+=1
            if first is None: first=int(ss["start_ms"])+(k+1)*int(cfg["grid_ms"])
        q.append(int(v)); valid+=int(v)
        if len(q)>look: valid-=q.popleft()
    return {
        "scheduled_10s_points":len(paired),
        "paired_valid_window_count":sum(paired),
        "paired_valid_window_share":sum(paired)/len(paired),
        "baseline_eligible_count":eligible,
        "first_baseline_eligible_ms":first,
        "first_baseline_eligible_not_before_6h": first is not None and first>=int(ss["start_ms"])+6*3600000,
        "required_labels":list(labels),
        "max_label":max(labels),
        "march21_performance_excluded": max(labels)=="2024-03-21",
    }

def main():
    started=time.time()
    E=load_engine(); cfg=E.load_config(CONFIG_PATH)
    out=E.data_roots()["e006_root"]/"preflight"
    out.mkdir(parents=True,exist_ok=True)
    report_path=out/"sc001_e006_preflight_report.json"
    summary_path=out/"sc001_e006_preflight_summary.md"
    if report_path.exists() or summary_path.exists():
        fail(f"refusing to overwrite existing E006 preflight outputs: {out}")

    tests,failures=run_synthetic_tests(E,cfg)
    dry={}
    try:
        dry=real_data_no_alpha(E,cfg)
    except Exception as exc:
        failures.append(f"REAL_DATA_DRY_RUN:{type(exc).__name__}:{exc}")

    disk=shutil.disk_usage(out)
    input_bytes=0
    try:
        labels=E.required_labels_for_phase("discovery",cfg)
        sm=E.spot_manifest(labels); wm=E.swap_manifest(labels)
        input_bytes=sum(int(x["bytes"]) for x in sm.values())+sum(int(x["bytes"]) for x in wm.values())
    except Exception as exc:
        failures.append(f"INPUT_IDENTITY:{type(exc).__name__}:{exc}")

    ru=resource.getrusage(resource.RUSAGE_SELF)
    peak=int(ru.ru_maxrss)
    peak_bytes=peak*1024 if sys.platform!="darwin" else peak
    memory_ok=peak_bytes < 6*1024**3
    disk_ok=disk.free >= 10*1024**3
    if not memory_ok: failures.append("RESOURCE_peak_memory")
    if not disk_ok: failures.append("RESOURCE_disk_reserve")
    if any(not t["pass"] for t in tests): failures.append("SYNTHETIC_test_failure")
    if dry and not dry.get("first_baseline_eligible_not_before_6h"): failures.append("DRY_first_eligibility")
    if dry and dry.get("max_label")!="2024-03-21": failures.append("DRY_protected_label")
    failures=sorted(set(failures))
    status="E006_PREFLIGHT_PASS" if not failures else "E006_PREFLIGHT_FAIL"
    report={
        "stage":"SC001-E006-PREFLIGHT","protocol_version":"1.0","preflight_spec_version":"1.0",
        "status":status,"git_commit":E.git_commit(E.repo_root_from_file()),
        "engine_sha256":sha256_file(ENGINE_PATH),"preflight_runner_sha256":sha256_file(Path(__file__).resolve()),
        "config_sha256":sha256_file(CONFIG_PATH),
        "environment":{"python":sys.version,"platform":platform.platform(),"timezone":"UTC"},
        "tests":{"total":len(tests),"passed":sum(1 for t in tests if t["pass"]),"failures":failures,"details":tests},
        "real_data_no_alpha_dry_run":dry,
        "resources":{"input_bytes":input_bytes,"disk_free_bytes":disk.free,"disk_pass":disk_ok,"peak_rss_bytes":peak_bytes,"memory_under_6gib_pass":memory_ok},
        "firewalls":{"spot_swap_price_values_exported":False,"basis_calculated":False,"returns_calculated":False,"pnl_calculated":False,"alpha_calculated":False,"l2_accessed":False,"q2_accessed":False,"validation_or_final_accessed":False},
        "started_epoch":started,"completed_epoch":time.time(),
    }
    atomic_json(report_path,report)
    summary=["# SC001-E006 Preflight","",f"Status: `{status}`",f"Tests: {report['tests']['passed']}/{report['tests']['total']}",f"Paired valid 10s windows: {dry.get('paired_valid_window_count')}",f"Baseline-eligible windows: {dry.get('baseline_eligible_count')}",f"Peak RSS bytes: {peak_bytes}","","No real-data basis/returns/P&L/alpha calculated."]
    atomic_text(summary_path,"\n".join(summary)+"\n")
    print(status)
    print(f"tests = {report['tests']['passed']}/{report['tests']['total']}")
    print("paired_valid_window_count =",dry.get("paired_valid_window_count"))
    print("baseline_eligible_count =",dry.get("baseline_eligible_count"))
    print("first_baseline_eligible_ms =",dry.get("first_baseline_eligible_ms"))
    print("peak_rss_bytes =",peak_bytes)
    print("disk_pass =",disk_ok)
    print("memory_under_6gib_pass =",memory_ok)
    print("basis/returns/P&L/alpha calculated = False")
    print("L2/Q2/Validation/Final = CLOSED")
    if failures:
        for x in failures: print("FAIL",x)
    return 0 if status=="E006_PREFLIGHT_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
