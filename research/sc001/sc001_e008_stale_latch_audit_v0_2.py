"""SC001-E008 fail-closed stale-latch data-model audit v0.2.
NO hypothetical orders, fills, spread capture, inventory, markout, fees, P&L or profitability.
"""
from __future__ import annotations
import bisect,itertools,json,os
from datetime import datetime,timezone
from pathlib import Path
import sc001_e008_queue_audit_lib as L

STAGE="SC001-E008-STALE-LATCH-DATA-MODEL"
VERSION="0.2"
STALE_MS=5000
OUT_DIR=L.DATA_ROOT/"SC001_E008_STALE_LATCH_MODEL"
OUT_JSON=OUT_DIR/"sc001_e008_stale_latch_model_report.json"

def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); tmp=Path(str(p)+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,p)

def audit_day(day,l2,tr):
    day_start=L.day_bounds(day)[0] if hasattr(L,"day_bounds") else int(datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
    day_end=day_start+86400000
    groups=[]
    for t,g in itertools.groupby(L.iter_l2(l2),key=lambda x:x[0]):
        actions=[x[1] for x in g]
        groups.append((int(t),"snapshot" in actions))
    if not groups: raise RuntimeError(f"{day}: empty L2")
    if not groups[0][1]: raise RuntimeError(f"{day}: first L2 group is not snapshot")

    episodes=[]; source_gaps=0; trusted_intervals=1; latched=False; latch_start=None
    last_ts=groups[0][0]
    for t,is_snapshot in groups[1:]:
        if t<last_ts: raise RuntimeError(f"{day}: L2 timestamp reversal")
        gap=t-last_ts
        if gap>STALE_MS:
            source_gaps+=1
            if not latched:
                latch_start=last_ts+STALE_MS
                latched=True
        if latched and is_snapshot:
            episodes.append((int(latch_start),t))
            latched=False; latch_start=None; trusted_intervals+=1
        last_ts=t
    if latched:
        episodes.append((int(latch_start),day_end))

    ts=tr["ts"]; n=tr["rows"]
    stale_trades=0
    for a,b in episodes:
        lo=bisect.bisect_left(ts,a); hi=bisect.bisect_left(ts,b)
        stale_trades += max(0,hi-lo)
    durations=[b-a for a,b in episodes]
    unrecovered=1 if episodes and episodes[-1][1]==day_end else 0
    out={
        "date":day,
        "l2_group_count":len(groups),
        "source_gap_gt_5000_count":source_gaps,
        "stale_episode_count":len(episodes),
        "stale_total_ms":sum(durations),
        "stale_share_of_day":sum(durations)/86400000.0,
        "stale_trade_count":stale_trades,
        "stale_trade_share":stale_trades/max(1,n),
        "max_recovery_delay_ms":max(durations) if durations else 0,
        "unrecovered_latch_count":unrecovered,
        "trusted_interval_count":trusted_intervals,
        "trade_rows":n,
        "episodes":[{"start_ms":a,"end_ms":b,"duration_ms":b-a} for a,b in episodes],
    }
    out["day_pass"]=(trusted_intervals>=1 and all(a<b for a,b in episodes))
    return out

def main():
    inv,q6=L.qualified_state(); rows=[]; errors=[]
    for day in L.DAYS:
        try:
            l2,lb,ld=L.resolve_l2(inv,day); ep,np=L.resolve_trades(q6[day]); tr=L.load_trade_day(day,ep,np)
            print(f"STALE LATCH AUDIT {day}: replay L2 state chronology")
            r=audit_day(day,l2,tr); r.update({"l2_path":str(l2),"l2_bytes":lb,"l2_sha256":ld,"trade_exact_path":str(ep),"trade_neighbor_path":str(np)})
            rows.append(r)
            print(f"STALE LATCH {day} PASS gaps={r['source_gap_gt_5000_count']} episodes={r['stale_episode_count']} stale_share={r['stale_share_of_day']:.6f} stale_trades={r['stale_trade_count']}")
        except Exception as e:
            msg=f"{day}: {type(e).__name__}: {e}"; errors.append(msg); rows.append({"date":day,"day_pass":False,"error":msg}); print("STALE LATCH REVIEW",msg)
    passed=len(rows)==4 and all(x.get("day_pass") for x in rows) and not errors
    status="E008_STALE_LATCH_MODEL_PASS" if passed else "E008_STALE_LATCH_MODEL_REVIEW"
    rep={"stage":STAGE,"version":VERSION,"status":status,"days":rows,"errors":errors,
         "parent_queue_feasibility_v0_1":"REVIEW_UNCHANGED","stale_threshold_ms":STALE_MS,
         "recovery_rule":"only next full snapshot clears STALE_LATCH","incremental_update_clears_latch":False,
         "stale_trade_queue_progress_allowed":False,"hypothetical_orders_created":False,"fill_simulation_calculated":False,
         "spread_capture_calculated":False,"inventory_calculated":False,"markout_calculated":False,"maker_fees_or_rebates_calculated":False,
         "maker_pnl_calculated":False,"profitability_calculated":False,"tfi_used":False,"q2_accessed":False,"validation_or_final_accessed":False,
         "finished_at_utc":datetime.now(timezone.utc).isoformat()}
    atomic_json(OUT_JSON,rep)
    print(status)
    print("qualified_day_count =",sum(1 for x in rows if x.get("day_pass")),"/ 4")
    print("queue_feasibility_v0.1 = REVIEW_UNCHANGED")
    print("recovery_rule = next full snapshot only")
    print("fills/spread_capture/inventory/PnL/profitability calculated = False")
    print("Q2/Validation/Final = CLOSED")
    print("report =",OUT_JSON)
    return 0 if passed else 2
if __name__=="__main__": raise SystemExit(main())
