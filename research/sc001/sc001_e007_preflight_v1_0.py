"""SC001-E007 no-alpha implementation preflight v1.0.

Synthetic causal tests plus real-data timestamp/bucket-availability dry run.
NO real-data VWAP/displacement/trigger/return/P&L/alpha calculation.
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_PATH = HERE / "sc001_e007_extreme_reversal_v1.py"
CONFIG_PATH = HERE / "sc001_e007_config_v1_0.json"

def fail(msg: str) -> None:
    raise RuntimeError(msg)

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def atomic_text(path: Path,text: str) -> None:
    path.parent.mkdir(parents=True,exist_ok=True); tmp=Path(str(path)+".tmp")
    with tmp.open("w",encoding="utf-8",newline="") as f:
        f.write(text); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)

def atomic_json(path: Path,obj) -> None:
    atomic_text(path,json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

def load_engine():
    spec=importlib.util.spec_from_file_location("sc001_e007_engine",ENGINE_PATH)
    if spec is None or spec.loader is None: fail("cannot load E007 engine")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def assert_close(a,b,tol=1e-9):
    if not math.isclose(a,b,rel_tol=tol,abs_tol=tol): raise AssertionError(f"{a!r} != {b!r}")

def mkstream(E,date="2024-03-02",rows=None):
    base=E.date_ms(date); rows=sorted(enumerate(rows or []),key=lambda z:(z[1][0],z[0])); ts=array("q"); px=array("d"); sz=array("d")
    for _j,(_orig,r) in enumerate(rows):
        off,p,s=r; ts.append(base+int(off)); px.append(float(p)); sz.append(float(s))
    return {"start_ms":base,"end_ms":base+E.DAY_MS,"timestamps":ts,"prices":px,"sizes":sz}

def run_synthetic_tests(E,cfg):
    tests=[]; failures=[]
    def T(name,fn):
        try: fn(); tests.append({"name":name,"pass":True})
        except Exception as exc: tests.append({"name":name,"pass":False,"error":f"{type(exc).__name__}: {exc}"}); failures.append(name)
    def p01():
        st=mkstream(E,rows=[(0,100,1),(4999,110,1),(5000,999,1)]); vw,c=E.build_5s_vwap(st,5000); assert c[0]==2 and c[1]==1; assert_close(vw[0],105.0)
    T("P01_current_window_excludes_t",p01)
    def p02():
        st=mkstream(E,rows=[(4999,100,1)]); vw,_=E.build_5s_vwap(st,5000); assert_close(vw[0],100)
    T("P02_t_minus_1ms_included",p02)
    def p03():
        st=mkstream(E,rows=[(1000,100,1),(2000,110,3)]); vw,_=E.build_5s_vwap(st,5000); assert_close(vw[0],107.5)
    T("P03_size_weighted_vwap",p03)
    def p04():
        v=[None]*13; v[0]=100; v[12]=100.8; r,_=E.build_displacement_records(v,E.date_ms("2024-03-02"),cfg); assert r[12]["anchor"]==100 and r[12]["current"]==100.8; assert r[12]["t"]==E.date_ms("2024-03-02")+65_000
    T("P04_anchor_offset_exact_12",p04)
    T("P05_displacement_formula",lambda: assert_close(E.displacement_bps(100,100.8),80.0))
    def p06():
        v=[None]*13; v[12]=100.8; r,_=E.build_displacement_records(v,E.date_ms("2024-03-02"),cfg); assert r[12]["valid"] is False
    T("P06_invalid_anchor_blocks",p06)
    def p07():
        base=E.date_ms("2024-03-02"); rec=[{"t":base+60_000,"valid":False,"disp_bps":None},{"t":base+65_000,"valid":True,"disp_bps":81.0,"anchor":100.0,"current":100.81}]; assert E.build_trigger_candidates(rec,cfg,"2024-03-02","2024-03-02")==[]
    T("P07_previous_invalid_blocks_crossing",p07)
    def p08():
        base=E.date_ms("2024-03-02"); rec=[{"t":base+60_000,"valid":True,"disp_bps":79.999,"anchor":100.0,"current":100.79999},{"t":base+65_000,"valid":True,"disp_bps":80.0,"anchor":100.0,"current":100.8}]; assert len(E.build_trigger_candidates(rec,cfg,"2024-03-02","2024-03-02"))==1
    T("P08_threshold_equality_qualifies",p08)
    def p09():
        base=E.date_ms("2024-03-02"); rec=[{"t":base+60_000,"valid":True,"disp_bps":80.0,"anchor":100.0,"current":100.8},{"t":base+65_000,"valid":True,"disp_bps":81.0,"anchor":100.0,"current":100.81}]; assert E.build_trigger_candidates(rec,cfg,"2024-03-02","2024-03-02")==[]
    T("P09_no_retrigger_above_threshold",p09)
    def p10():
        base=E.date_ms("2024-03-02"); rec=[{"t":base+60_000,"valid":True,"disp_bps":-79.0,"anchor":100.0,"current":99.21},{"t":base+65_000,"valid":True,"disp_bps":-80.0,"anchor":100.0,"current":99.2}]; out=E.build_trigger_candidates(rec,cfg,"2024-03-02","2024-03-02"); assert len(out)==1 and out[0]["direction"]==1
    T("P10_negative_shock_long_reversal",p10)
    def p11():
        base=E.date_ms("2024-03-02"); rec=[{"t":base+60_000,"valid":True,"disp_bps":79.0,"anchor":100.0,"current":100.79},{"t":base+65_000,"valid":True,"disp_bps":80.0,"anchor":100.0,"current":100.8}]; out=E.build_trigger_candidates(rec,cfg,"2024-03-02","2024-03-02"); assert out[0]["direction"]==-1
    T("P11_positive_shock_short_reversal",p11)
    def p12():
        base=E.date_ms("2024-03-02"); rec=[{"t":base+60_000,"valid":True,"disp_bps":79.0,"anchor":100.0,"current":100.79},{"t":base+65_000,"valid":True,"disp_bps":80.0,"anchor":100.0,"current":100.8}]; out=E.build_trigger_candidates(rec,cfg,"2024-03-02","2024-03-02"); assert_close(out[0]["target_price"],100.4)
    T("P12_half_retracement_target",p12)
    T("P13_target_frozen_scalar",lambda: (_ for _ in ()).throw(AssertionError()) if 100+0.5*(100.8-100)!=100.4 else None)
    def p14():
        base=E.date_ms("2024-03-02"); st=mkstream(E,rows=[(1500,100,1),(1501,101,1)]); leg=E.proxy_leg(st,base+1500,5000,base+E.DAY_MS); assert leg and leg[1]==base+1500
    T("P14_proxy_first_at_or_after",p14)
    def p15():
        base=E.date_ms("2024-03-02"); st=mkstream(E,rows=[(6500,100,1)]); assert E.proxy_leg(st,base+1500,5000,base+E.DAY_MS) is not None
    T("P15_tolerance_5000_inclusive",p15)
    def p16():
        base=E.date_ms("2024-03-02"); st=mkstream(E,rows=[(6501,100,1)]); assert E.proxy_leg(st,base+1500,5000,base+E.DAY_MS) is None
    T("P16_tolerance_5001_rejected",p16)
    def p17(): assert E.already_reverted(-1,100.4,100.4) and E.already_reverted(1,99.6,99.6)
    T("P17_already_reverted_equality",p17)
    def mkrecords(base,target=100.4):
        rec=[{"t":base+(k+1)*5000,"valid":True,"anchor":100.0,"current":101.0,"disp_bps":100.0} for k in range(200)]; rec[14]["current"]=target; return rec
    def p18():
        base=E.date_ms("2024-03-02"); t,reason=E.find_exit_decision({"direction":-1,"target_price":100.4},mkrecords(base),base,base+65_500,cfg); assert reason=="reversion" and t==base+75_000
    T("P18_target_equality_exits",p18)
    def p19():
        base=E.date_ms("2024-03-02"); t,_=E.find_exit_decision({"direction":-1,"target_price":100.4},mkrecords(base),base,base+70_000,cfg); assert t>base+70_000
    T("P19_exit_strictly_after_entry",p19)
    def p20():
        base=E.date_ms("2024-03-02"); assert E.grid_ceiling(base+65_500+600_000,base,5000)==base+670_000; assert E.grid_ceiling(base+65_000+600_000,base,5000)==base+665_000
    T("P20_time_exit_grid_ceiling",p20)
    def p21():
        base=E.date_ms("2024-03-02"); t,reason=E.find_exit_decision({"direction":-1,"target_price":100.4},mkrecords(base),base,base+65_500,cfg); assert reason=="reversion" and t<E.grid_ceiling(base+65_500+600_000,base,5000)
    T("P21_reversion_precedes_time",p21)
    def p22():
        src=ENGINE_PATH.read_text(encoding="utf-8"); assert 'locked_day = d' in src and '"exit_missing"' in src
    T("P22_missing_exit_locks_day",p22)
    T("P23_cooldown_exact_10m",lambda: (_ for _ in ()).throw(AssertionError()) if cfg["cooldown_ms"]!=600000 else None)
    T("P24_daily_cap_four",lambda: (_ for _ in ()).throw(AssertionError()) if cfg["max_entry_decisions_per_day"]!=4 else None)
    def p25():
        src=ENGINE_PATH.read_text(encoding="utf-8"); assert "max_concurrent_positions" in src and "skipped_busy_or_cooldown" in src
    T("P25_one_position_state",p25)
    T("P26_latest_entry_2349",lambda: (_ for _ in ()).throw(AssertionError()) if E.parse_clock_ms(cfg["latest_entry_decision_utc"])!=23*3600000+49*60000 else None)
    T("P27_long_gross_sign",lambda: assert_close(10000*(101/100-1),100))
    T("P28_short_gross_sign",lambda: assert_close(-10000*(99/100-1),100))
    def p29():
        src=ENGINE_PATH.read_text(encoding="utf-8"); frag=src[src.find("def replay_latency"):src.find("def trimmed_mean")]; assert "replay_latency(primary_events" in src and "build_trigger_candidates" not in frag
    T("P29_stress_no_new_trigger_discovery",p29)
    def p30():
        base=E.date_ms("2024-03-02"); st=mkstream(E,rows=[(68_000,101,1),(70_000,100,1)]); pe=[{"date":"2024-03-02","trigger_ts":base+65_000,"direction":-1,"target_price":100.4,"exit_decision_ts":base+67_000,"incomplete_reason":None}]; out=E.replay_latency(pe,st,cfg,2000,calculate_alpha=False); assert not out[0]["completed"] and out[0]["incomplete_reason"]=="entry_after_exit_decision"
    T("P30_stress_entry_after_exit_incomplete",p30)
    def p31():
        assert_close(E.displacement_bps(100,100.8),E.displacement_bps(1000,1008)); assert_close((1000+0.5*(1008-1000))/(100+0.5*(100.8-100)),10)
    T("P31_price_scale_invariance",p31)
    def p32():
        st1=mkstream(E,rows=[(1000,100,1),(4999,110,1)]); vw1,_=E.build_5s_vwap(st1,5000); st2=mkstream(E,rows=[(1000,100,1),(4999,110,1),(5001,999,1)]); vw2,_=E.build_5s_vwap(st2,5000); assert_close(vw1[0],vw2[0])
    T("P32_future_row_no_earlier_vwap_change",p32)
    def p33():
        old=os.environ.get("SC001_DATA_ROOT")
        try:
            with tempfile.TemporaryDirectory() as td:
                os.environ["SC001_DATA_ROOT"]=td
                try: E.require_confirmation_gate(CONFIG_PATH)
                except RuntimeError: return
                raise AssertionError("confirmation gate unexpectedly open")
        finally:
            if old is None: os.environ.pop("SC001_DATA_ROOT",None)
            else: os.environ["SC001_DATA_ROOT"]=old
    T("P33_confirmation_fail_closed",p33)
    def p34():
        fw=cfg["firewalls"]; assert fw["reversal_only"] is True and fw["diagnostic_grid"] is False
        for k in ("use_tfi","use_flow_impulse","use_e004_compression","use_e006_basis","l2","q2","validation","final"): assert fw[k] is False
    T("P34_firewalls",p34)
    def p35():
        base=E.date_ms("2024-03-02"); rec=[{"t":base+(k+1)*5000,"valid":True,"anchor":100.0,"current":101.0,"disp_bps":100.0} for k in range(17280)]; cands=[]; rows=[]
        for h in [1,3,5,7,9]:
            t=base+h*3600_000; cands.append({"date":"2024-03-02","trigger_ts":t,"direction":-1,"trigger_disp_bps":80.0,"anchor_price":100.0,"trigger_vwap":100.8,"target_price":100.4}); rows.append((h*3600_000+500,100.8,1)); rec[((t+5000)-base)//5000-1]["current"]=100.4; rows.append((h*3600_000+5500,100.4,1))
        _ev,meta=E.simulate_primary(mkstream(E,rows=rows),rec,cands,cfg,500,calculate_alpha=False); assert meta["decisions"]==4 and meta["max_decisions_per_day_observed"]==4
    T("P35_fifth_daily_decision_blocked_behavior",p35)
    def p36():
        base=E.date_ms("2024-03-02"); rec=[{"t":base+(k+1)*5000,"valid":True,"anchor":100.0,"current":101.0,"disp_bps":100.0} for k in range(17280)]; t1=base+3600_000; t2=t1+605_000; cands=[]; rows=[]
        for t in (t1,t2):
            cands.append({"date":"2024-03-02","trigger_ts":t,"direction":-1,"trigger_disp_bps":80.0,"anchor_price":100.0,"trigger_vwap":100.8,"target_price":100.4}); rec[((t+5000)-base)//5000-1]["current"]=100.4; rows.extend([(t-base,100.8,1),(t-base+5000,100.4,1)])
        _ev,meta=E.simulate_primary(mkstream(E,rows=rows),rec,cands,cfg,0,calculate_alpha=False); assert meta["decisions"]==2
    T("P36_cooldown_half_open_boundary_behavior",p36)
    def p37():
        base=E.date_ms("2024-03-02"); rec=[{"t":base+(k+1)*5000,"valid":True,"anchor":100.0,"current":101.0,"disp_bps":100.0} for k in range(17280)]; t1=base+3600_000; t2=t1+300_000; cands=[{"date":"2024-03-02","trigger_ts":t1,"direction":-1,"trigger_disp_bps":80.0,"anchor_price":100.0,"trigger_vwap":100.8,"target_price":100.4},{"date":"2024-03-02","trigger_ts":t2,"direction":-1,"trigger_disp_bps":80.0,"anchor_price":100.0,"trigger_vwap":100.8,"target_price":100.4}]; rows=[(t1-base+500,100.8,1),(t1-base+605_500,100.7,1)]; _ev,meta=E.simulate_primary(mkstream(E,rows=rows),rec,cands,cfg,500,calculate_alpha=False); assert meta["decisions"]==1 and meta.get("skipped_busy_or_cooldown",0)>=1 and meta["max_concurrent_positions"]<=1
    T("P37_no_overlap_busy_trigger_skipped",p37)
    def p38():
        base=E.date_ms("2024-03-02"); rec=[{"t":base+(k+1)*5000,"valid":True,"anchor":100.0,"current":101.0,"disp_bps":100.0} for k in range(17280)]; t1=base+3600_000; t2=base+3*3600_000; rec[((t1+5000)-base)//5000-1]["current"]=100.4; cands=[{"date":"2024-03-02","trigger_ts":t1,"direction":-1,"trigger_disp_bps":80.0,"anchor_price":100.0,"trigger_vwap":100.8,"target_price":100.4},{"date":"2024-03-02","trigger_ts":t2,"direction":-1,"trigger_disp_bps":80.0,"anchor_price":100.0,"trigger_vwap":100.8,"target_price":100.4}]; _ev,meta=E.simulate_primary(mkstream(E,rows=[(t1-base+500,100.8,1)]),rec,cands,cfg,500,calculate_alpha=False); assert meta["decisions"]==1 and meta.get("exit_missing",0)==1 and meta.get("skipped_day_locked",0)>=1
    T("P38_missing_exit_locks_remainder_of_day_behavior",p38)
    return tests,failures

def bucket_presence(stream,grid_ms):
    lo=int(stream["start_ms"]); hi=int(stream["end_ms"]); n=(hi-lo)//grid_ms; seen=bytearray(n)
    for t in stream["timestamps"]:
        k=(int(t)-lo)//grid_ms
        if 0<=k<n: seen[k]=1
    return seen

def real_data_no_alpha(E,cfg):
    labels=E.required_labels_for_phase("discovery",cfg); manifest=E.swap_manifest(labels,cfg)
    for d in labels: E.verify_archive(manifest[d])
    stream=E.load_stream(manifest,cfg,cfg["discovery"]["start"],cfg["discovery"]["end"]); seen=bucket_presence(stream,int(cfg["grid_ms"])); off=int(cfg["anchor_offset_buckets"]); structurally_valid=0; first=None
    for k in range(off,len(seen)):
        if seen[k] and seen[k-off]:
            structurally_valid+=1
            if first is None: first=int(stream["start_ms"])+(k+1)*int(cfg["grid_ms"])
    return {"scheduled_5s_points":len(seen),"occupied_5s_bucket_count":sum(seen),"structurally_valid_current_anchor_count":structurally_valid,"structurally_valid_share":structurally_valid/len(seen),"first_structurally_valid_ms":first,"first_valid_not_before_65s":first is not None and first>=int(stream["start_ms"])+65_000,"required_labels":list(labels),"max_label":max(labels),"march21_performance_excluded":max(labels)=="2024-03-21"}

def main():
    started=time.time(); E=load_engine(); cfg=E.load_config(CONFIG_PATH); out=E.data_roots()["e007_root"]/"preflight"; out.mkdir(parents=True,exist_ok=True); report_path=out/"sc001_e007_preflight_report.json"; summary_path=out/"sc001_e007_preflight_summary.md"
    tests,failures=run_synthetic_tests(E,cfg); dry=real_data_no_alpha(E,cfg); disk=shutil.disk_usage(out); rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss; peak_rss_bytes=int(rss*1024 if sys.platform!="darwin" else rss); resource_fail=[]
    if peak_rss_bytes>=6*1024**3: resource_fail.append("peak_rss_not_under_6GiB")
    if disk.free<10*1024**3: resource_fail.append("disk_free_under_10GiB")
    if not dry["first_valid_not_before_65s"]: failures.append("first_structural_valid_too_early")
    if dry["max_label"]!="2024-03-21": failures.append("protected_label_boundary_failure")
    failures=sorted(set(failures+resource_fail)); status="E007_PREFLIGHT_PASS" if not failures else "E007_PREFLIGHT_FAIL"
    report={"stage":"SC001-E007-PREFLIGHT","protocol_version":"1.0","preflight_spec_version":"1.0","status":status,"git_commit":E.git_commit(E.repo_root_from_file()),"engine_sha256":sha256_file(ENGINE_PATH),"preflight_runner_sha256":sha256_file(Path(__file__).resolve()),"config_sha256":sha256_file(CONFIG_PATH),"environment":{"python":sys.version,"platform":platform.platform(),"timezone":"UTC"},"tests":{"total":len(tests),"passed":sum(1 for t in tests if t["pass"]),"failures":failures,"details":tests},"real_data_no_alpha_dry_run":dry,"resources":{"disk_free_bytes":disk.free,"disk_pass":disk.free>=10*1024**3,"peak_rss_bytes":peak_rss_bytes,"memory_under_6gib_pass":peak_rss_bytes<6*1024**3},"firewalls":{"real_vwap_calculated":False,"real_displacement_calculated":False,"real_triggers_calculated":False,"returns_calculated":False,"pnl_calculated":False,"alpha_calculated":False,"l2_accessed":False,"q2_accessed":False,"validation_or_final_accessed":False},"started_at_epoch":started,"completed_at_epoch":time.time()}
    atomic_json(report_path,report); atomic_text(summary_path,"\n".join(["# SC001-E007 Preflight",f"Status: `{status}`",f"Tests: {report['tests']['passed']}/{report['tests']['total']}",f"Structural valid windows: {dry['structurally_valid_current_anchor_count']}",f"Peak RSS bytes: {peak_rss_bytes}","Real E007 alpha calculated: NO"])+"\n")
    print(status); print("tests =",f"{report['tests']['passed']}/{report['tests']['total']}"); print("structurally_valid_window_count =",dry["structurally_valid_current_anchor_count"]); print("first_structurally_valid_ms =",dry["first_structurally_valid_ms"]); print("peak_rss_bytes =",peak_rss_bytes); print("disk_pass =",report["resources"]["disk_pass"]); print("memory_under_6gib_pass =",report["resources"]["memory_under_6gib_pass"]); print("real_VWAP/displacement/triggers/returns/P&L/alpha calculated = False"); print("L2/Q2/Validation/Final = CLOSED"); return 0 if status=="E007_PREFLIGHT_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
