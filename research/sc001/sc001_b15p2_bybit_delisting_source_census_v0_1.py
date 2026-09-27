#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="SC001-B15P2-BYBIT-DELISTING-SOURCE-CENSUS-V0.1"
PASS="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS"
DEFER="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_DEFER"
REVIEW="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_REVIEW"
SELFTEST_PASS="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V01_SELF_TEST_PASS"

START_MS=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
END_MS=int(datetime(2026,9,27,tzinfo=timezone.utc).timestamp()*1000)

MIN_CLOSED=5
MIN_ADMITTED=5
MIN_COVERAGE=0.80
MIN_MONTHS=3

BYBIT_BASE="https://api.bybit.com"
TIMEOUT=45
RETRIES=4
MAX_JSON=8_000_000
ANN_LIMIT=20
ANN_PAGE_CAP=100
INST_LIMIT=1000
INST_PAGE_CAP=20

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_B15P2_BYBIT_DELISTING_SOURCE_CENSUS"
OUT=OUT_DIR/"sc001_b15p2_bybit_delisting_source_census_v0_1.json"


def fail(msg:str)->None:
    raise RuntimeError(msg)


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
        fail("Runner launcher package-root mismatch")


def atomic_json(path:Path,obj:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)


def request_json(url:str,label:str)->dict[str,Any]:
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"BotMarketplace-SC001-B15P2/0.1",
                "Accept":"application/json",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_JSON+1)
            if len(raw)>MAX_JSON:
                fail(f"{label} response exceeds cap")
            obj=json.loads(raw.decode("utf-8"))
            if not isinstance(obj,dict):
                fail(f"{label} response not object")
            if int(obj.get("retCode",-1))!=0:
                fail(f"{label} retCode={obj.get('retCode')} retMsg={obj.get('retMsg')}")
            return obj
        except Exception as exc:
            last=exc
            if attempt<RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} request failed: {type(last).__name__}: {last}")


def bybit_get(path:str,params:dict[str,str],label:str)->dict[str,Any]:
    return request_json(BYBIT_BASE+path+"?"+urllib.parse.urlencode(params),label)


def type7(values:list[float],p:float)->float|None:
    if not values:
        return None
    xs=sorted(values)
    if len(xs)==1:
        return xs[0]
    h=(len(xs)-1)*p
    lo=math.floor(h); hi=math.ceil(h)
    if lo==hi:
        return xs[lo]
    return xs[lo]+(h-lo)*(xs[hi]-xs[lo])


def derivative_relevant(ann:dict[str,Any])->bool:
    tags=ann.get("tags") or []
    if not isinstance(tags,list):
        tags=[]
    tset={str(x).strip().upper() for x in tags}
    text=(str(ann.get("title") or "")+" "+str(ann.get("description") or "")).upper()
    return ("DERIVATIVES" in tset) or ("FUTURES" in tset) or ("PERPETUAL" in text)


def normalize_announcement(ann:dict[str,Any])->dict[str,Any]:
    typ=ann.get("type") or {}
    key=str(typ.get("key") or "")
    if key!="delistings":
        fail(f"announcement type mismatch: {key}")
    pub=ann.get("publishTime")
    if pub in (None,""):
        fail("announcement publishTime missing")
    pub=int(pub)
    if pub<=0:
        fail("announcement publishTime invalid")
    url=str(ann.get("url") or "")
    if not url.startswith("https://announcements.bybit.com/"):
        fail(f"untrusted announcement URL: {url}")
    return {
        "title":str(ann.get("title") or ""),
        "description":str(ann.get("description") or ""),
        "tags":[str(x) for x in (ann.get("tags") or [])],
        "url":url,
        "publish_ms":pub,
        "derivative_relevant":derivative_relevant(ann),
    }


def normalize_instrument(item:dict[str,Any])->dict[str,Any]|None:
    if str(item.get("contractType") or "")!="LinearPerpetual":
        return None
    if str(item.get("quoteCoin") or "")!="USDT":
        return None
    if str(item.get("status") or "")!="Closed":
        return None
    if item.get("isPreListing") is True:
        return None
    symbol=str(item.get("symbol") or "")
    if not symbol.endswith("USDT"):
        return None
    try:
        delivery=int(str(item.get("deliveryTime") or "0"))
    except ValueError:
        fail(f"invalid deliveryTime for {symbol}")
    if not (START_MS<=delivery<END_MS):
        return None
    return {
        "symbol":symbol,
        "symbol_id":item.get("symbolId"),
        "base_coin":str(item.get("baseCoin") or ""),
        "quote_coin":"USDT",
        "contract_type":"LinearPerpetual",
        "status":"Closed",
        "delivery_ms":delivery,
    }


def fetch_announcements()->list[dict[str,Any]]:
    rows=[]
    total=None
    for page in range(1,ANN_PAGE_CAP+1):
        obj=bybit_get("/v5/announcements/index",{
            "locale":"en-US",
            "type":"delistings",
            "page":str(page),
            "limit":str(ANN_LIMIT),
        },f"Bybit announcements page {page}")
        result=obj.get("result") or {}
        if total is None:
            total=int(result.get("total") or 0)
        batch=result.get("list") or []
        if not isinstance(batch,list):
            fail("announcement list malformed")
        for ann in batch:
            if not isinstance(ann,dict):
                fail("announcement row malformed")
            rows.append(normalize_announcement(ann))
        if len(batch)<ANN_LIMIT or len(rows)>=total:
            break
    else:
        fail("announcement pagination cap reached")
    if total is not None and len(rows)<min(total,ANN_LIMIT):
        fail("announcement retrieval unexpectedly short")
    return rows


def fetch_closed_linear()->list[dict[str,Any]]:
    out=[]
    cursor=""
    seen=set()
    for page in range(1,INST_PAGE_CAP+1):
        params={
            "category":"linear",
            "status":"Closed",
            "limit":str(INST_LIMIT),
        }
        if cursor:
            params["cursor"]=cursor
        obj=bybit_get("/v5/market/instruments-info",params,f"Bybit closed instruments page {page}")
        result=obj.get("result") or {}
        batch=result.get("list") or []
        if not isinstance(batch,list):
            fail("instrument list malformed")
        for item in batch:
            if not isinstance(item,dict):
                fail("instrument row malformed")
            row=normalize_instrument(item)
            if row is None:
                continue
            key=(row["symbol"],row["delivery_ms"])
            if key in seen:
                continue
            seen.add(key)
            out.append(row)
        nxt=str(result.get("nextPageCursor") or "")
        if not nxt:
            break
        if nxt==cursor:
            fail("instrument cursor did not advance")
        cursor=nxt
    else:
        fail("instrument pagination cap reached")
    return sorted(out,key=lambda x:(x["delivery_ms"],x["symbol"]))


def build_census(instruments:list[dict[str,Any]],announcements:list[dict[str,Any]])->dict[str,Any]:
    derivative=[a for a in announcements if a["derivative_relevant"]]
    events=[]
    unmatched=[]
    for inst in instruments:
        symbol=inst["symbol"]
        matches=[]
        for ann in derivative:
            text=(ann["title"]+" "+ann["description"]).upper()
            pattern=r"(?<![A-Z0-9])"+re.escape(symbol.upper())+r"(?![A-Z0-9])"
            if re.search(pattern,text) and ann["publish_ms"]<inst["delivery_ms"]:
                matches.append(ann)
        matches.sort(key=lambda x:(x["publish_ms"],x["url"]))
        if not matches:
            unmatched.append(symbol)
            continue
        first=matches[0]
        last=matches[-1]
        lead_h=(inst["delivery_ms"]-first["publish_ms"])/3_600_000.0
        if not (lead_h>0):
            fail(f"nonpositive causal lead for {symbol}")
        events.append({
            "venue":"BYBIT",
            "symbol":symbol,
            "delivery_ms":inst["delivery_ms"],
            "delivery_utc":datetime.fromtimestamp(inst["delivery_ms"]/1000,tz=timezone.utc).isoformat(),
            "first_notice_ms":first["publish_ms"],
            "last_pre_event_notice_ms":last["publish_ms"],
            "notice_count":len(matches),
            "lead_hours":lead_h,
            "announcement_urls":[x["url"] for x in matches],
            "delivery_month":datetime.fromtimestamp(inst["delivery_ms"]/1000,tz=timezone.utc).strftime("%Y-%m"),
        })

    n_closed=len(instruments)
    n_admitted=len(events)
    coverage=(n_admitted/n_closed) if n_closed else None
    months=sorted({e["delivery_month"] for e in events})
    leads=[float(e["lead_hours"]) for e in events]

    gates={
        "closed_perpetuals_ge5":n_closed>=MIN_CLOSED,
        "admitted_events_ge5":n_admitted>=MIN_ADMITTED,
        "announcement_match_coverage_ge80pct":bool(coverage is not None and coverage>=MIN_COVERAGE),
        "all_admitted_positive_lead":all(e["lead_hours"]>0 for e in events),
        "delivery_months_ge3":len(months)>=MIN_MONTHS,
    }
    status=PASS if all(gates.values()) else DEFER
    return {
        "status":status,
        "closed_in_scope_count":n_closed,
        "admitted_event_count":n_admitted,
        "unmatched_symbols":sorted(unmatched),
        "announcement_match_coverage":coverage,
        "delivery_months":months,
        "lead_hours":{
            "min":min(leads) if leads else None,
            "p25":type7(leads,0.25),
            "median":statistics.median(leads) if leads else None,
            "p75":type7(leads,0.75),
            "max":max(leads) if leads else None,
        },
        "gates":gates,
        "events":events,
        "price_accessed":False,
        "basis_calculated":False,
        "pnl_calculated":False,
        "event_ranked_by_outcome":False,
    }


def selftest()->int:
    try:
        months=[1,2,3,4,5,6]
        instruments=[]
        announcements=[]
        for i,m in enumerate(months,1):
            delivery=int(datetime(2026,m,15,9,tzinfo=timezone.utc).timestamp()*1000)
            sym=f"T{i}USDT"
            instruments.append({
                "symbol":sym,"delivery_ms":delivery,"status":"Closed",
                "contract_type":"LinearPerpetual","quote_coin":"USDT",
            })
            if i<=5:
                pub=delivery-48*3_600_000
                announcements.append({
                    "title":f"Delisting of {sym} Perpetual Contract",
                    "description":"",
                    "tags":["Derivatives","Delistings"],
                    "url":f"https://announcements.bybit.com/en/article/{sym.lower()}",
                    "publish_ms":pub,
                    "derivative_relevant":True,
                })
                # later revision remains before event
                if i==2:
                    announcements.append({
                        "title":f"Update: Delisting of {sym} Perpetual Contract",
                        "description":"",
                        "tags":["Derivatives"],
                        "url":f"https://announcements.bybit.com/en/article/{sym.lower()}-update",
                        "publish_ms":delivery-24*3_600_000,
                        "derivative_relevant":True,
                    })
        r=build_census(instruments,announcements)
        assert r["status"]==PASS
        assert r["admitted_event_count"]==5
        assert abs(r["announcement_match_coverage"]-(5/6))<1e-12
        ev=[x for x in r["events"] if x["symbol"]=="T2USDT"][0]
        assert ev["notice_count"]==2
        assert abs(ev["lead_hours"]-48.0)<1e-12

        # Exact-symbol rule: embedded longer ticker must not match.
        one=[{
            "symbol":"ABCUSDT",
            "delivery_ms":int(datetime(2026,7,1,tzinfo=timezone.utc).timestamp()*1000),
            "status":"Closed","contract_type":"LinearPerpetual","quote_coin":"USDT",
        }]
        wrong=[{
            "title":"Delisting of XABCUSDT Perpetual Contract",
            "description":"",
            "tags":["Derivatives"],
            "url":"https://announcements.bybit.com/en/article/wrong",
            "publish_ms":int(datetime(2026,6,29,tzinfo=timezone.utc).timestamp()*1000),
            "derivative_relevant":True,
        }]
        rwrong=build_census(one,wrong)
        # ABCUSDT is a substring of XABCUSDT but not an exact alphanumeric token.
        assert rwrong["admitted_event_count"]==0

        # DEFER fixture: 4/6 coverage.
        r2=build_census(instruments,announcements[:4])
        assert r2["status"]==DEFER

        # Pre-market-only closed identity must be excluded.
        pre=normalize_instrument({
            "contractType":"LinearPerpetual","quoteCoin":"USDT","status":"Closed",
            "symbol":"PREUSDT","deliveryTime":str(int(datetime(2026,5,1,tzinfo=timezone.utc).timestamp()*1000)),
            "isPreListing":True,
        })
        assert pre is None

        # Type-7 fixture.
        xs=[0.0,10.0,20.0,30.0]
        assert abs(type7(xs,0.25)-7.5)<1e-12
        assert abs(type7(xs,0.75)-22.5)<1e-12

        print(SELFTEST_PASS)
        return 0
    except Exception as exc:
        print("B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V01_SELF_TEST_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2


def live()->int:
    try:
        anns=fetch_announcements()
        inst=fetch_closed_linear()
        census=build_census(inst,anns)
        report={
            "stage":STAGE,
            "version":"0.1",
            "window":{"start_ms":START_MS,"end_exclusive_ms":END_MS},
            "announcement_source":{
                "endpoint":"/v5/announcements/index",
                "locale":"en-US",
                "type":"delistings",
                "retrieved_count":len(anns),
                "derivative_relevant_count":sum(1 for a in anns if a["derivative_relevant"]),
            },
            "instrument_source":{
                "endpoint":"/v5/market/instruments-info",
                "category":"linear",
                "status":"Closed",
                "in_scope_count":len(inst),
            },
            **census,
            "settlement_semantics_interpreted":False,
            "next_state":(
                "FREEZE_ADMITTED_EVENT_SET_AND_RUN_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT"
                if census["status"]==PASS
                else "REVIEW_SOURCE_COVERAGE_WITHOUT_OPENING_PRICES"
            ),
        }
        atomic_json(OUT,report)
        print(census["status"])
        print("announcements =",len(anns))
        print("derivative_relevant =",report["announcement_source"]["derivative_relevant_count"])
        print("closed_in_scope =",census["closed_in_scope_count"])
        print("admitted =",census["admitted_event_count"])
        print("coverage =",census["announcement_match_coverage"])
        print("months =",census["delivery_months"])
        print("lead_hours =",json.dumps(census["lead_hours"],sort_keys=True))
        print("gates =",json.dumps(census["gates"],sort_keys=True))
        print("price/basis/PnL = CLOSED")
        print("report =",OUT)
        return 0
    except Exception as exc:
        print(REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","live"),default="self-test")
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)
    return selftest() if a.mode=="self-test" else live()


if __name__=="__main__":
    raise SystemExit(main())
