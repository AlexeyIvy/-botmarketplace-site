"""SC001-E008 read-only microstructure forensic v1.0.

Replays only the already-qualified L2 archives to measure market structure.
It does NOT rerun E008, create hypothetical orders/fills, alter parameters/gates,
or access Confirmation/Q2/Validation/Final.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import math
import os
import statistics
import tarfile
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-E008-READONLY-MICROSTRUCTURE-FORENSIC"
VERSION = "1.0"
PASS = "E008_READONLY_MICROSTRUCTURE_FORENSIC_PASS"
INST = "BTC-USDT-SWAP"
DAYS = (
    "2024-01-06", "2024-01-13", "2024-01-19", "2024-01-24",
    "2024-02-06", "2024-02-11", "2024-02-21", "2024-02-23",
)

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home()/"sc001_data"))).expanduser().resolve()
SEMANTIC_REPORT = DATA_ROOT/"SC001_E008_DISCOVERY_SEMANTIC_INTEGRITY"/"sc001_e008_discovery_semantic_integrity_report.json"
MAKER_REPORT = DATA_ROOT/"SC001_E008_MAKER_DISCOVERY"/"sc001_e008_maker_discovery_report.json"
OUT_DIR = DATA_ROOT/"SC001_E008_READONLY_MICROSTRUCTURE_FORENSIC"
CHECKPOINTS = OUT_DIR/"checkpoints"
OUT_JSON = OUT_DIR/"sc001_e008_readonly_microstructure_forensic_report.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists(): fail(f"missing JSON: {path}")
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict): fail(f"JSON object expected: {path}")
    return x


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(str(path)+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(8*1024*1024),b""): h.update(c)
    return h.hexdigest()


def day_bounds(day: str) -> tuple[int,int]:
    d=datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo=int(d.timestamp()*1000)
    return lo,lo+86_400_000


def parse_level(x) -> tuple[float,float,int]:
    if not isinstance(x,list) or len(x)!=3: fail("L2 level shape")
    p=float(x[0]); s=float(x[1]); of=float(x[2]); o=int(round(of))
    if not (math.isfinite(p) and math.isfinite(s) and math.isfinite(of)): fail("nonfinite L2 level")
    if p<=0 or s<0 or o<0 or abs(of-o)>1e-9: fail("invalid L2 level")
    if s==0 and o!=0: fail("zero-size delete with nonzero order count")
    return p,s,o


def apply(book: dict, prices: list, levels: list[tuple[float,float,int]]) -> None:
    for p,s,o in levels:
        if s==0:
            if p not in book: fail(f"delete-missing level {p}")
            del book[p]
            i=bisect.bisect_left(prices,p)
            if i<len(prices) and prices[i]==p: prices.pop(i)
        else:
            if p not in book: bisect.insort(prices,p)
            book[p]=(s,o)


def best_state(asks,bids,ap,bp):
    if not ap or not bp: return None
    bid=bp[-1]; ask=ap[0]
    if bid>=ask: fail(f"crossed book {bid} >= {ask}")
    bs,bo=bids[bid]; a_s,ao=asks[ask]
    if bs<=0 or a_s<=0 or bo<=0 or ao<=0: fail("invalid best level")
    mid=(bid+ask)/2.0
    spread_bps=(ask-bid)/mid*10_000.0
    return {"bid":float(bid),"ask":float(ask),"bid_size":float(bs),"ask_size":float(a_s),"spread_bps":float(spread_bps)}


def cp_path(day: str) -> Path:
    return CHECKPOINTS/f"{day}.json"


def quantile(vals: list[float], p: float):
    if not vals: return None
    xs=sorted(float(x) for x in vals)
    if len(xs)==1: return xs[0]
    pos=(len(xs)-1)*p
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi: return xs[lo]
    w=pos-lo
    return xs[lo]*(1-w)+xs[hi]*w


def scan_day(day: str, path: Path, expected_sha: str) -> dict:
    cur_sha=sha256_file(path)
    if cur_sha!=expected_sha: fail(f"L2 SHA mismatch {day}")
    cp=cp_path(day)
    if cp.exists():
        try: old=load_json(cp)
        except Exception: old=None
        if isinstance(old,dict) and old.get("stage")==STAGE and old.get("version")==VERSION and old.get("date")==day and old.get("l2_sha256")==cur_sha and old.get("status")=="DAY_PASS":
            print(f"MICROSTRUCTURE {day} REUSED DAY_PASS")
            return old

    lo,hi=day_bounds(day)
    asks={}; bids={}; ap=[]; bp=[]
    records=snapshots=updates=0
    prev_ts=None; prev_state=None
    total_ms=0
    spread_ms_sum=0.0
    bid_size_ms_sum=0.0; ask_size_ms_sum=0.0
    ge4=ge5=ge7=le1=le2=0
    min_spread=None; max_spread=None
    bid_changes=ask_changes=0
    bid_same_inc=bid_same_dec=ask_same_inc=ask_same_dec=0
    bid_inc_qty=bid_dec_qty=ask_inc_qty=ask_dec_qty=0.0
    bid_prev_disappear=ask_prev_disappear=0
    snapshot_ts=[]

    def accrue(to_ts: int):
        nonlocal prev_ts,total_ms,spread_ms_sum,bid_size_ms_sum,ask_size_ms_sum,ge4,ge5,ge7,le1,le2
        if prev_ts is None or prev_state is None: return
        dt=max(0,int(to_ts)-int(prev_ts))
        if dt<=0: return
        s=prev_state["spread_bps"]
        total_ms += dt
        spread_ms_sum += s*dt
        bid_size_ms_sum += prev_state["bid_size"]*dt
        ask_size_ms_sum += prev_state["ask_size"]*dt
        if s>=4.0: ge4+=dt
        if s>=5.0: ge5+=dt
        if s>=7.0: ge7+=dt
        if s<=1.0: le1+=dt
        if s<=2.0: le2+=dt

    with tarfile.open(path,mode="r|gz") as tf:
        regular=0
        for m in tf:
            if not m.isfile(): continue
            regular+=1
            if regular>1: fail(f"multiple regular L2 members {path.name}")
            f=tf.extractfile(m)
            if f is None: fail(f"cannot extract {path.name}")
            for raw in f:
                if not raw.strip(): continue
                r=json.loads(raw)
                if not isinstance(r,dict) or r.get("instId")!=INST: fail("L2 record/instrument mismatch")
                action=r.get("action")
                if action not in {"snapshot","update"}: fail("bad L2 action")
                ts=int(r.get("ts"))
                if not (lo<=ts<hi): fail(f"out-of-day L2 timestamp {day}: {ts}")
                if prev_ts is not None and ts<prev_ts: fail("L2 timestamp reversal")
                aa=r.get("asks"); bb=r.get("bids")
                if not isinstance(aa,list) or not isinstance(bb,list): fail("bad L2 sides")
                pa=[parse_level(x) for x in aa]; pb=[parse_level(x) for x in bb]

                accrue(ts)
                old=best_state(asks,bids,ap,bp)
                old_bid_present = old is not None and old["bid"] in bids
                old_ask_present = old is not None and old["ask"] in asks

                if action=="snapshot":
                    snapshots+=1; snapshot_ts.append(ts)
                    asks.clear(); bids.clear(); ap.clear(); bp.clear()
                else:
                    updates+=1
                apply(asks,ap,pa); apply(bids,bp,pb)
                new=best_state(asks,bids,ap,bp)
                if new is None: fail("empty book after valid record")

                if old is not None:
                    if new["bid"] != old["bid"]: bid_changes+=1
                    else:
                        d=new["bid_size"]-old["bid_size"]
                        if d>1e-12: bid_same_inc+=1; bid_inc_qty+=d
                        elif d< -1e-12: bid_same_dec+=1; bid_dec_qty+=-d
                    if new["ask"] != old["ask"]: ask_changes+=1
                    else:
                        d=new["ask_size"]-old["ask_size"]
                        if d>1e-12: ask_same_inc+=1; ask_inc_qty+=d
                        elif d< -1e-12: ask_same_dec+=1; ask_dec_qty+=-d
                    if old_bid_present and old["bid"] not in bids: bid_prev_disappear+=1
                    if old_ask_present and old["ask"] not in asks: ask_prev_disappear+=1

                s=new["spread_bps"]
                min_spread=s if min_spread is None else min(min_spread,s)
                max_spread=s if max_spread is None else max(max_spread,s)
                prev_state=new; prev_ts=ts; records+=1
        if regular!=1: fail(f"regular L2 member count {path.name}: {regular}")

    accrue(hi)
    if total_ms<=0: fail(f"no time-weighted coverage {day}")
    snap_intervals=[snapshot_ts[i]-snapshot_ts[i-1] for i in range(1,len(snapshot_ts))]
    hours=total_ms/3_600_000.0
    row={
        "stage":STAGE,"version":VERSION,"date":day,"status":"DAY_PASS","l2_sha256":cur_sha,
        "records":records,"snapshots":snapshots,"updates":updates,"time_covered_ms":total_ms,
        "time_weighted_mean_spread_bps":spread_ms_sum/total_ms,
        "time_weighted_mean_best_bid_size_contracts":bid_size_ms_sum/total_ms,
        "time_weighted_mean_best_ask_size_contracts":ask_size_ms_sum/total_ms,
        "time_share_spread_ge_4bps":ge4/total_ms,
        "time_share_spread_ge_5bps":ge5/total_ms,
        "time_share_spread_ge_7bps":ge7/total_ms,
        "time_share_spread_le_1bps":le1/total_ms,
        "time_share_spread_le_2bps":le2/total_ms,
        "min_event_spread_bps":min_spread,"max_event_spread_bps":max_spread,
        "best_bid_price_changes":bid_changes,"best_ask_price_changes":ask_changes,
        "best_bid_same_price_size_increase_events":bid_same_inc,"best_bid_same_price_size_decrease_events":bid_same_dec,
        "best_ask_same_price_size_increase_events":ask_same_inc,"best_ask_same_price_size_decrease_events":ask_same_dec,
        "best_bid_same_price_total_increase_contracts":bid_inc_qty,"best_bid_same_price_total_decrease_contracts":bid_dec_qty,
        "best_ask_same_price_total_increase_contracts":ask_inc_qty,"best_ask_same_price_total_decrease_contracts":ask_dec_qty,
        "prior_best_bid_disappearance_events":bid_prev_disappear,"prior_best_ask_disappearance_events":ask_prev_disappear,
        "best_price_change_events_per_hour":(bid_changes+ask_changes)/hours if hours>0 else None,
        "snapshot_interval_ms_p50":quantile([float(x) for x in snap_intervals],0.5),
        "snapshot_interval_ms_p90":quantile([float(x) for x in snap_intervals],0.9),
    }
    atomic_json(cp,row)
    print(f"MICROSTRUCTURE {day} PASS spread_mean={row['time_weighted_mean_spread_bps']:.6f}bps ge4={row['time_share_spread_ge_4bps']:.6f} snapshots={snapshots}")
    return row


def cycle_group(cycles: list[dict]) -> dict:
    if not cycles: return {"cycles":0}
    gross=[float(c["gross_edge_bps"]) for c in cycles]
    net=[float(c["net_edge_bps"]) for c in cycles]
    dur=[float(c.get("duration_ms",0)) for c in cycles]
    return {
        "cycles":len(cycles),
        "mean_gross_bps":statistics.fmean(gross),"median_gross_bps":statistics.median(gross),
        "mean_net_bps":statistics.fmean(net),"median_net_bps":statistics.median(net),
        "gross_positive_share":sum(x>0 for x in gross)/len(gross),
        "net_positive_share":sum(x>0 for x in net)/len(net),
        "duration_ms_p50":quantile(dur,0.50),"duration_ms_p90":quantile(dur,0.90),"duration_ms_p99":quantile(dur,0.99),
    }


def terminal_diagnostics(maker: dict) -> dict:
    days=list((maker.get("scenarios") or {}).get("primary") or [])
    if len(days)!=8: fail("primary terminal days != 8")
    cycles=[c for d in days for c in d.get("cycles",[])]
    forced=[c for c in cycles if c.get("forced_taker") is True]
    maker_only=[c for c in cycles if c.get("forced_taker") is not True]
    long_first=[c for c in cycles if c.get("first_side")=="BUY"]
    short_first=[c for c in cycles if c.get("first_side")=="SELL"]
    per_day=[]
    for d in days:
        cs=d.get("cycles",[])
        per_day.append({
            "date":d.get("date"),"cycles":len(cs),
            "forced_share":sum(c.get("forced_taker") is True for c in cs)/len(cs) if cs else None,
            "mean_gross_bps":statistics.fmean(float(c["gross_edge_bps"]) for c in cs) if cs else None,
            "mean_net_bps":statistics.fmean(float(c["net_edge_bps"]) for c in cs) if cs else None,
        })
    return {
        "all":cycle_group(cycles),"forced":cycle_group(forced),"maker_only":cycle_group(maker_only),
        "long_first":cycle_group(long_first),"short_first":cycle_group(short_first),"per_day":per_day,
    }


def pooled(rows: list[dict]) -> dict:
    total_ms=sum(int(r["time_covered_ms"]) for r in rows)
    if total_ms<=0: fail("pooled time zero")
    def wmean(key): return sum(float(r[key])*int(r["time_covered_ms"]) for r in rows)/total_ms
    return {
        "time_covered_ms":total_ms,
        "time_weighted_mean_spread_bps":wmean("time_weighted_mean_spread_bps"),
        "time_share_spread_ge_4bps":wmean("time_share_spread_ge_4bps"),
        "time_share_spread_ge_5bps":wmean("time_share_spread_ge_5bps"),
        "time_share_spread_ge_7bps":wmean("time_share_spread_ge_7bps"),
        "time_share_spread_le_1bps":wmean("time_share_spread_le_1bps"),
        "time_share_spread_le_2bps":wmean("time_share_spread_le_2bps"),
        "snapshots":sum(int(r["snapshots"]) for r in rows),
        "best_bid_price_changes":sum(int(r["best_bid_price_changes"]) for r in rows),
        "best_ask_price_changes":sum(int(r["best_ask_price_changes"]) for r in rows),
        "same_price_size_increase_events":sum(int(r["best_bid_same_price_size_increase_events"])+int(r["best_ask_same_price_size_increase_events"]) for r in rows),
        "same_price_size_decrease_events":sum(int(r["best_bid_same_price_size_decrease_events"])+int(r["best_ask_same_price_size_decrease_events"]) for r in rows),
        "same_price_total_increase_contracts":sum(float(r["best_bid_same_price_total_increase_contracts"])+float(r["best_ask_same_price_total_increase_contracts"]) for r in rows),
        "same_price_total_decrease_contracts":sum(float(r["best_bid_same_price_total_decrease_contracts"])+float(r["best_ask_same_price_total_decrease_contracts"]) for r in rows),
        "prior_best_disappearance_events":sum(int(r["prior_best_bid_disappearance_events"])+int(r["prior_best_ask_disappearance_events"]) for r in rows),
    }


def main() -> int:
    sem=load_json(SEMANTIC_REPORT); maker=load_json(MAKER_REPORT)
    if sem.get("status")!="E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS": fail("semantic parent not PASS")
    if maker.get("status")!="E008_DISCOVERY_FAIL": fail("E008 terminal FAIL not preserved")
    sem_rows={r.get("date"):r for r in sem.get("days",[]) if isinstance(r,dict)}
    if tuple(sem_rows)!=DAYS and set(sem_rows)!=set(DAYS): fail("semantic day set mismatch")

    rows=[]
    for day in DAYS:
        sr=sem_rows[day]; l2=sr.get("l2") or {}
        path=Path(str(l2.get("path","")))
        expected=str(sr.get("l2_sha256") or "")
        if not path.exists() or len(expected)!=64: fail(f"missing qualified L2 identity {day}")
        rows.append(scan_day(day,path,expected))

    pool=pooled(rows)
    term=terminal_diagnostics(maker)
    flags=[]
    if pool["time_weighted_mean_spread_bps"] < 4.0: flags.append("MEAN_SPREAD_BELOW_MAKER_MAKER_FEE_FLOOR")
    if pool["time_share_spread_ge_4bps"] < 0.10: flags.append("SPREAD_RARELY_COVERS_4BPS_FEE_FLOOR")
    if pool["same_price_size_decrease_events"] > 0: flags.append("ZERO_CANCELLATION_CREDIT_IS_MATERIAL_MODEL_ASSUMPTION")
    if pool["same_price_size_increase_events"] > 0: flags.append("ALL_ADDITIONS_AHEAD_IS_MATERIAL_MODEL_ASSUMPTION")
    if pool["prior_best_disappearance_events"] > 0: flags.append("OWN_ORDER_ABSENCE_CAN_BIAS_LEVEL_DISAPPEAR_PATH")
    if pool["snapshots"] > 8: flags.append("PERIODIC_SNAPSHOT_CANCEL_SEMANTICS_MAY_BIAS_QUEUE_RESET")
    if term["all"].get("mean_gross_bps",0) < 0: flags.append("NEGATIVE_GROSS_EDGE_ROBUST_IN_FROZEN_RESULT")

    rep={
        "stage":STAGE,"version":VERSION,"status":PASS,
        "e008_terminal_status_preserved":maker.get("status"),
        "days":rows,"pooled_market":pool,"terminal_cycle_diagnostics":term,"forensic_flags":flags,
        "strategy_rerun_performed":False,"hypothetical_orders_created":False,"fill_simulation_calculated":False,
        "strategy_parameters_changed":False,"promotion_gates_changed":False,
        "confirmation_body_accessed":False,"q2_accessed":False,"validation_or_final_accessed":False,
    }
    atomic_json(OUT_JSON,rep)
    print(PASS)
    print("pooled time-weighted mean spread bps =",pool["time_weighted_mean_spread_bps"])
    print("time share spread >=4bps =",pool["time_share_spread_ge_4bps"])
    print("time share spread >=5bps =",pool["time_share_spread_ge_5bps"])
    print("time share spread >=7bps =",pool["time_share_spread_ge_7bps"])
    print("time share spread <=1bps =",pool["time_share_spread_le_1bps"])
    print("time share spread <=2bps =",pool["time_share_spread_le_2bps"])
    print("same-price best-size increase events =",pool["same_price_size_increase_events"])
    print("same-price best-size decrease events =",pool["same_price_size_decrease_events"])
    print("same-price total increase contracts =",pool["same_price_total_increase_contracts"])
    print("same-price total decrease contracts =",pool["same_price_total_decrease_contracts"])
    print("prior-best disappearance events =",pool["prior_best_disappearance_events"])
    print("snapshots =",pool["snapshots"])
    print("primary duration p50/p90/p99 ms =",term["all"].get("duration_ms_p50"),term["all"].get("duration_ms_p90"),term["all"].get("duration_ms_p99"))
    print("primary gross-positive share =",term["all"].get("gross_positive_share"))
    print("long-first mean gross/net bps =",term["long_first"].get("mean_gross_bps"),term["long_first"].get("mean_net_bps"))
    print("short-first mean gross/net bps =",term["short_first"].get("mean_gross_bps"),term["short_first"].get("mean_net_bps"))
    print("forensic flags =",flags)
    print("strategy rerun performed = False")
    print("E008 terminal decision changed = False")
    print("Confirmation/Q2/Validation/Final = CLOSED")
    print("report =",OUT_JSON)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
