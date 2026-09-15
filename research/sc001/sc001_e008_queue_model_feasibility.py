"""SC001-E008 no-fill/no-P&L queue-model feasibility runner."""
from __future__ import annotations
import itertools,json,math,os
from datetime import datetime,timezone
from pathlib import Path
import sc001_e008_queue_audit_lib as L

STAGE="SC001-E008-QUEUE-MODEL-FEASIBILITY"
VERSION="0.1"
CAPS=(100,250,500,1000,5000)
OUT_DIR=L.DATA_ROOT/"SC001_E008_QUEUE_MODEL_FEASIBILITY"
OUT_JSON=OUT_DIR/"sc001_e008_queue_model_feasibility_report.json"

def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=Path(str(p)+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True);f.write("\n");f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)

def qrank(xs,q):
    if not xs:return None
    ys=sorted(xs);i=max(0,min(len(ys)-1,math.ceil(q*len(ys))-1));return int(ys[i])

def audit_day(day,l2,tr):
    asks={};bids={};ap=[];bp=[];seen_snapshot=False;first_action=None
    groups=usable=positive=crossed=empty=snapshots=updates=records=0
    ti=0;n=tr["rows"];same=non_same=prior=0;ages=[];caps={c:0 for c in CAPS}
    compat_den=compat=exact_best=through=0;buys=sells=0;book_ts=None;book_valid=False;best_bid=best_ask=None
    def one(i,amb=False):
        nonlocal same,non_same,prior,compat_den,compat,exact_best,through,buys,sells
        t=int(tr["ts"][i]);p=float(tr["px"][i]);buy=bool(tr["side"][i]);buys+=1 if buy else 0;sells+=0 if buy else 1
        if amb:same+=1;return
        non_same+=1
        if not book_valid or book_ts is None or book_ts>=t:return
        prior+=1;age=t-book_ts;ages.append(age)
        for c in CAPS:
            if age<=c:caps[c]+=1
        if age>5000:return
        compat_den+=1
        if buy:
            ok=p>=float(best_ask)-1e-9
            if ok:
                compat+=1
                if abs(p-float(best_ask))<=1e-9:exact_best+=1
                elif p>float(best_ask):through+=1
        else:
            ok=p<=float(best_bid)+1e-9
            if ok:
                compat+=1
                if abs(p-float(best_bid))<=1e-9:exact_best+=1
                elif p<float(best_bid):through+=1
    for t,g in itertools.groupby(L.iter_l2(l2),key=lambda x:x[0]):
        while ti<n and int(tr["ts"][ti])<t:one(ti);ti+=1
        while ti<n and int(tr["ts"][ti])==t:one(ti,True);ti+=1
        for _t,a,aa,bb in g:
            records+=1
            if first_action is None:first_action=a
            if a=="snapshot":
                snapshots+=1;seen_snapshot=True;asks.clear();bids.clear();ap.clear();bp.clear()
            else:updates+=1
            L.apply(asks,ap,aa);L.apply(bids,bp,bb)
        groups+=1;book_ts=t
        if not ap or not bp:empty+=1;book_valid=False;continue
        bid=bp[-1];ask=ap[0]
        if bid>=ask:crossed+=1;book_valid=False;continue
        book_valid=seen_snapshot;best_bid=bid;best_ask=ask
        if book_valid:
            usable+=1;bs,bo=bids[bid];as_,ao=asks[ask]
            if bs>0 and as_>0 and bo>0 and ao>0:positive+=1
    while ti<n:
        one(ti,book_ts is not None and int(tr["ts"][ti])==book_ts);ti+=1
    b=max(1,non_same);d=max(1,compat_den);u=max(1,usable)
    out={
        "date":day,"l2_records":records,"snapshots":snapshots,"updates":updates,"first_action":first_action,
        "state_groups":groups,"usable_book_states":usable,"positive_best_queue_states":positive,"positive_best_queue_share":positive/u,
        "crossed_states":crossed,"empty_states":empty,"trade_rows":n,"trade_minutes":tr["minutes"],"trade_id_gap_count":tr["id_gaps"],
        "buy_trades":buys,"sell_trades":sells,"same_ms_ambiguous":same,"same_ms_ambiguous_share":same/max(1,n),
        "non_same_ms_trades":non_same,"prior_valid_book_trades":prior,"prior_valid_book_share":prior/b,
        "book_age_ms":{"p50":qrank(ages,.5),"p95":qrank(ages,.95),"p99":qrank(ages,.99),"max":max(ages) if ages else None},
        "book_age_cap_share":{str(c):caps[c]/b for c in CAPS},"aligned_age_le_5000ms_trades":compat_den,
        "side_price_compatible":compat,"side_price_compatible_share":compat/d,"exact_best_trade_share":exact_best/d,"through_best_trade_share":through/d,
        "exact_order_ids_available":False,"aggregate_best_level_size_available":usable>0,"aggregate_best_level_order_count_available":positive>0,
    }
    gates={
        "trade_1440_minutes":out["trade_minutes"]==1440,
        "initial_snapshot":out["first_action"]=="snapshot" and out["snapshots"]>=1,
        "l2_integrity":out["crossed_states"]==0 and out["empty_states"]==0,
        "prior_book_share_ge_0_999":out["prior_valid_book_share"]>=.999,
        "age_5000_share_ge_0_995":out["book_age_cap_share"]["5000"]>=.995,
        "side_price_compat_ge_0_95":out["side_price_compatible_share"]>=.95,
        "positive_queue_fields_ge_0_9999":out["positive_best_queue_share"]>=.9999,
        "both_trade_sides":out["buy_trades"]>0 and out["sell_trades"]>0,
    }
    out["gates"]=gates;out["day_pass"]=all(gates.values());return out

def main():
    inv,q6=L.qualified_state();rows=[];errors=[]
    for day in L.DAYS:
        try:
            l2,lb,ld=L.resolve_l2(inv,day);ep,np=L.resolve_trades(q6[day])
            print(f"QUEUE AUDIT {day}: load UTC trades")
            tr=L.load_trade_day(day,ep,np)
            print(f"QUEUE AUDIT {day}: replay L2 + causal alignment")
            r=audit_day(day,l2,tr);r.update({"l2_path":str(l2),"l2_bytes":lb,"l2_sha256":ld,"trade_exact_path":str(ep),"trade_neighbor_path":str(np)})
            rows.append(r)
            print(f"QUEUE AUDIT {day} {'PASS' if r['day_pass'] else 'REVIEW'} prior={r['prior_valid_book_share']:.6f} age5={r['book_age_cap_share']['5000']:.6f} compat={r['side_price_compatible_share']:.6f}")
        except Exception as e:
            msg=f"{day}: {type(e).__name__}: {e}";errors.append(msg);rows.append({"date":day,"day_pass":False,"error":msg});print("QUEUE AUDIT REVIEW",msg)
    passed=len(rows)==4 and all(x.get("day_pass") for x in rows) and not errors
    status="E008_QUEUE_MODEL_FEASIBILITY_PASS" if passed else "E008_QUEUE_MODEL_FEASIBILITY_REVIEW"
    rep={"stage":STAGE,"version":VERSION,"status":status,"days":rows,"errors":errors,
         "exact_order_ids_available":False,"queue_model_mode_if_pass":"pessimistic transaction-volume-only; cancellations give zero queue progress",
         "conservative_trade_volume_only_queue_model_possible":passed,
         "hypothetical_orders_created":False,"fill_simulation_calculated":False,"spread_capture_calculated":False,"inventory_calculated":False,
         "markout_after_hypothetical_fill_calculated":False,"maker_fees_or_rebates_calculated":False,"maker_pnl_calculated":False,"profitability_calculated":False,
         "tfi_used":False,"q2_accessed":False,"validation_or_final_accessed":False,"finished_at_utc":datetime.now(timezone.utc).isoformat()}
    atomic_json(OUT_JSON,rep)
    print(status);print("qualified_day_count =",sum(1 for x in rows if x.get("day_pass")),"/ 4")
    print("exact_order_ids_available = False")
    print("queue_model_if_PASS = pessimistic transaction-volume-only; cancellations give zero progress")
    print("fills/spread_capture/inventory/maker_PnL/profitability calculated = False")
    print("TFI used = False");print("Q2/Validation/Final = CLOSED");print("report =",OUT_JSON)
    return 0 if passed else 2
if __name__=="__main__":raise SystemExit(main())
