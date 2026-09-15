"""SC001-E008 read-only 2024-02-13 stale-book forensic audit.
NO hypothetical orders, queue progress, fills, spread capture, inventory or P&L.
"""
from __future__ import annotations
import itertools,json,math,os
from datetime import datetime,timezone
from pathlib import Path
import sc001_e008_queue_audit_lib as L

DAY="2024-02-13"
OUT=L.DATA_ROOT/"SC001_E008_QUEUE_MODEL_FEASIBILITY"/"sc001_e008_feb13_stale_book_forensic.json"
CAPS=(1000,5000,10000,30000,60000)

def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=Path(str(p)+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True);f.write("\n");f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)

def qrank(xs,q):
    if not xs:return None
    ys=sorted(xs);i=max(0,min(len(ys)-1,math.ceil(q*len(ys))-1));return int(ys[i])

def iso(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()

def summarize(xs):
    return {"p50":qrank(xs,.5),"p95":qrank(xs,.95),"p99":qrank(xs,.99),"p999":qrank(xs,.999),"max":max(xs) if xs else None}

def main():
    inv,q6=L.qualified_state();l2,_b,_sha=L.resolve_l2(inv,DAY);ep,np=L.resolve_trades(q6[DAY]);tr=L.load_trade_day(DAY,ep,np)
    asks={};bids={};ap=[];bp=[];seen_snapshot=False;last_valid=None;prev_valid=None
    ti=0;n=tr["rows"];ages=[];same=0;prior=0;caps={c:0 for c in CAPS};stale=[];gaps=[]

    def consume_trade(i,amb=False,next_book_ts=None):
        nonlocal same,prior
        t=int(tr["ts"][i])
        if amb:
            same+=1;return
        if last_valid is None or last_valid>=t:return
        prior+=1;age=t-last_valid;ages.append(age)
        for c in CAPS:
            if age<=c:caps[c]+=1
        if age>5000:
            stale.append({"ts":t,"age_ms":age,"gap_start_ms":last_valid,"gap_end_ms":next_book_ts})

    for t,g in itertools.groupby(L.iter_l2(l2),key=lambda x:x[0]):
        while ti<n and int(tr["ts"][ti])<t:
            consume_trade(ti,False,t);ti+=1
        while ti<n and int(tr["ts"][ti])==t:
            consume_trade(ti,True,t);ti+=1
        for _t,a,aa,bb in g:
            if a=="snapshot":
                seen_snapshot=True;asks.clear();bids.clear();ap.clear();bp.clear()
            L.apply(asks,ap,aa);L.apply(bids,bp,bb)
        valid=bool(seen_snapshot and ap and bp and bp[-1]<ap[0])
        if valid:
            bid=bp[-1];ask=ap[0];bs,bo=bids[bid];as_,ao=asks[ask]
            valid=bs>0 and as_>0 and bo>0 and ao>0
        if valid:
            if prev_valid is not None:
                gap=t-prev_valid
                if gap>5000:gaps.append({"start_ms":prev_valid,"end_ms":t,"gap_ms":gap})
            prev_valid=t;last_valid=t
    while ti<n:
        consume_trade(ti,False,None);ti+=1

    episodes=[]
    if stale:
        cur={"first_ts":stale[0]["ts"],"last_ts":stale[0]["ts"],"trade_count":1,"max_age_ms":stale[0]["age_ms"],"gap_start_ms":stale[0]["gap_start_ms"],"gap_end_ms":stale[0]["gap_end_ms"]}
        for x in stale[1:]:
            if x["ts"]-cur["last_ts"]<=10000:
                cur["last_ts"]=x["ts"];cur["trade_count"]+=1;cur["max_age_ms"]=max(cur["max_age_ms"],x["age_ms"])
                if cur["gap_end_ms"] is None:cur["gap_end_ms"]=x["gap_end_ms"]
            else:
                episodes.append(cur);cur={"first_ts":x["ts"],"last_ts":x["ts"],"trade_count":1,"max_age_ms":x["age_ms"],"gap_start_ms":x["gap_start_ms"],"gap_end_ms":x["gap_end_ms"]}
        episodes.append(cur)
    for e in episodes:
        e["first_utc"]=iso(e["first_ts"]);e["last_utc"]=iso(e["last_ts"]);e["duration_ms"]=e["last_ts"]-e["first_ts"]
    top_count=sorted(episodes,key=lambda e:(e["trade_count"],e["max_age_ms"]),reverse=True)[:10]
    top_age=sorted(episodes,key=lambda e:(e["max_age_ms"],e["trade_count"]),reverse=True)[:10]
    top10_share=sum(e["trade_count"] for e in top_count)/max(1,len(stale))
    gap_lengths=[g["gap_ms"] for g in gaps]
    category="CONCENTRATED_SOURCE_GAPS" if len(stale)>0 and top10_share>=.90 else "DISTRIBUTED_STALENESS"
    rep={
        "stage":"SC001-E008-FEB13-STALE-BOOK-FORENSIC","version":"0.1","date":DAY,"status":"FORENSIC_COMPLETE","interpretation_category":category,
        "trade_rows":n,"same_ms_ambiguous":same,"strictly_prior_valid_book_trades":prior,
        "book_age_ms":summarize(ages),"book_age_cap_share":{str(c):caps[c]/max(1,prior) for c in CAPS},
        "stale_gt_5000_trade_count":len(stale),"stale_gt_5000_share":len(stale)/max(1,prior),"stale_episode_count":len(episodes),"top10_episode_trade_share":top10_share,
        "l2_gap_gt_5000_count":len(gaps),"l2_gap_ms":summarize(gap_lengths),
        "l2_gap_gt_10000_count":sum(1 for x in gap_lengths if x>10000),"l2_gap_gt_30000_count":sum(1 for x in gap_lengths if x>30000),"l2_gap_gt_60000_count":sum(1 for x in gap_lengths if x>60000),
        "top10_stale_episodes_by_trade_count":top_count,"top10_stale_episodes_by_max_age":top_age,
        "queue_feasibility_v0_1_verdict_unchanged":"E008_QUEUE_MODEL_FEASIBILITY_REVIEW",
        "hypothetical_orders_created":False,"queue_progress_calculated":False,"fills_calculated":False,"spread_capture_calculated":False,"inventory_calculated":False,"maker_pnl_calculated":False,"profitability_calculated":False,"tfi_used":False,"q2_accessed":False,"validation_or_final_accessed":False,
    }
    atomic_json(OUT,rep)
    print("E008_FEB13_STALE_BOOK_FORENSIC_COMPLETE")
    print("category =",category)
    print("prior_valid_book_trades =",prior)
    print("age_le_5000_share =",rep["book_age_cap_share"]["5000"])
    print("stale_gt_5000_trade_count =",len(stale))
    print("stale_episode_count =",len(episodes))
    print("top10_episode_trade_share =",top10_share)
    print("l2_gap_gt_5000_count =",len(gaps))
    print("l2_gap_max_ms =",rep["l2_gap_ms"]["max"])
    print("queue_feasibility_v0.1 remains REVIEW")
    print("fills/PnL/profitability calculated = False")
    print("report =",OUT)
if __name__=="__main__":main()
