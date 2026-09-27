#!/usr/bin/env python3
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import os
import statistics
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

STAGE="SC001-B14B-PERSISTENT-MULTISETTLEMENT-FUNDING-CARRY-V0.1"
SURVIVE="B14B_PERSISTENT_CARRY_STRUCTURAL_SURVIVE"
REJECT="B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL"
DEFER="B14B_DEFER_SOURCE_OR_SAMPLE"
SELFTEST_PASS="B14B_PERSISTENT_CARRY_V01_SELF_TEST_PASS"

SYMBOLS=("BTC","ETH","SOL","DOGE","ORDI","FIL","UNI","XRP","LTC","OP","BCH","SUI")
START_MS=int(datetime(2026,7,1,tzinfo=timezone.utc).timestamp()*1000)
END_MS=int(datetime(2026,9,27,tzinfo=timezone.utc).timestamp()*1000)
HOLD_MS=7*24*60*60*1000
SIGNAL_LOOKBACK=3
MATCH_TOLERANCE_MS=5*60*1000
MAX_COVERAGE_GAP_MS=24*60*60*1000
MIN_FUNDING_EVENTS_PER_VENUE=7

STRUCTURAL_BURDEN_BPS=40.0
GROSS_HEADROOM_HURDLE_BPS=50.0

MIN_SOURCE_ELIGIBLE_SYMBOLS=8
MIN_VALID_CYCLES=24
MIN_CYCLE_SYMBOLS=8
MIN_CYCLE_MONTHS=2
MIN_POSITIVE_SHARE=0.60
MIN_POSITIVE_MEDIAN_SYMBOLS=6
MIN_POSITIVE_MEDIAN_MONTHS=2

OKX_BASE="https://www.okx.com"
BYBIT_BASE="https://api.bybit.com"
TIMEOUT=45
RETRIES=4
MAX_JSON=8_000_000
MAX_PAGES=12

ROOT=Path(__file__).resolve().parents[2]
DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_B14B_PERSISTENT_FUNDING"
OUT=OUT_DIR/"sc001_b14b_persistent_multisettlement_funding_carry_v0_1.json"


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


def finite_decimal(value:Any)->Decimal:
    try:
        x=Decimal(str(value).strip())
    except (InvalidOperation,ValueError) as exc:
        raise ValueError(f"invalid decimal {value!r}") from exc
    if not x.is_finite():
        raise ValueError(f"non-finite decimal {value!r}")
    return x


def request_json(url:str,label:str)->dict[str,Any]:
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"BotMarketplace-SC001-B14B/0.1",
                "Accept":"application/json",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_JSON+1)
            if len(raw)>MAX_JSON:
                fail(f"{label} response exceeds cap")
            obj=json.loads(raw.decode("utf-8"))
            if not isinstance(obj,dict):
                fail(f"{label} response not object")
            return obj
        except Exception as exc:
            last=exc
            if attempt<RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} request failed: {type(last).__name__}: {last}")


def okx_get(params:dict[str,str])->dict[str,Any]:
    url=OKX_BASE+"/api/v5/public/funding-rate-history?"+urllib.parse.urlencode(params)
    obj=request_json(url,"OKX")
    if str(obj.get("code"))!="0":
        fail(f"OKX response code mismatch: {obj.get('code')} {obj.get('msg')}")
    return obj


def bybit_get(params:dict[str,str])->dict[str,Any]:
    url=BYBIT_BASE+"/v5/market/funding/history?"+urllib.parse.urlencode(params)
    obj=request_json(url,"Bybit")
    if int(obj.get("retCode",-1))!=0:
        fail(f"Bybit response code mismatch: {obj.get('retCode')} {obj.get('retMsg')}")
    return obj


def fetch_okx(symbol:str)->list[dict[str,Any]]:
    inst=f"{symbol}-USDT-SWAP"
    rows={}
    after=None
    last_oldest=None
    for _ in range(MAX_PAGES):
        params={"instId":inst,"limit":"400"}
        if after is not None:
            params["after"]=str(after)
        data=okx_get(params).get("data") or []
        if not isinstance(data,list):
            fail(f"OKX data malformed {symbol}")
        if not data:
            break
        oldest=None
        for item in data:
            if item.get("instId")!=inst:
                fail(f"OKX instId mismatch {symbol}: {item.get('instId')}")
            ts=int(str(item.get("fundingTime") or "0"))
            rr=item.get("realizedRate")
            if rr in (None,""):
                fail(f"OKX realizedRate missing {symbol} {ts}")
            rate=finite_decimal(rr)
            oldest=ts if oldest is None else min(oldest,ts)
            if START_MS<=ts<END_MS:
                prev=rows.get(ts)
                if prev is not None and prev["rate"]!=rate:
                    fail(f"OKX conflicting duplicate {symbol} {ts}")
                rows[ts]={"timestamp_ms":ts,"rate":rate}
        if oldest is None:
            break
        if oldest<START_MS or len(data)<400:
            break
        if last_oldest==oldest:
            fail(f"OKX pagination did not advance {symbol}")
        last_oldest=oldest
        after=oldest
    else:
        fail(f"OKX pagination cap reached {symbol}")
    return [rows[k] for k in sorted(rows)]


def fetch_bybit(symbol:str)->list[dict[str,Any]]:
    inst=f"{symbol}USDT"
    rows={}
    end=END_MS-1
    for _ in range(MAX_PAGES):
        data=(bybit_get({
            "category":"linear",
            "symbol":inst,
            "endTime":str(end),
            "limit":"200",
        }).get("result") or {}).get("list") or []
        if not isinstance(data,list):
            fail(f"Bybit list malformed {symbol}")
        if not data:
            break
        oldest=None
        for item in data:
            if item.get("symbol")!=inst:
                fail(f"Bybit symbol mismatch {symbol}: {item.get('symbol')}")
            ts=int(str(item.get("fundingRateTimestamp") or "0"))
            rate=finite_decimal(item.get("fundingRate"))
            oldest=ts if oldest is None else min(oldest,ts)
            if START_MS<=ts<END_MS:
                prev=rows.get(ts)
                if prev is not None and prev["rate"]!=rate:
                    fail(f"Bybit conflicting duplicate {symbol} {ts}")
                rows[ts]={"timestamp_ms":ts,"rate":rate}
        if oldest is None or oldest<START_MS or len(data)<200:
            break
        end=oldest-1
    else:
        fail(f"Bybit pagination cap reached {symbol}")
    return [rows[k] for k in sorted(rows)]


def match_signal_pairs(okx:list[dict[str,Any]],bybit:list[dict[str,Any]])->list[dict[str,Any]]:
    bt=[x["timestamp_ms"] for x in bybit]
    candidates=[]
    for oi,o in enumerate(okx):
        pos=bisect.bisect_left(bt,o["timestamp_ms"])
        for bj in (pos-1,pos,pos+1):
            if 0<=bj<len(bybit):
                skew=abs(o["timestamp_ms"]-bybit[bj]["timestamp_ms"])
                if skew<=MATCH_TOLERANCE_MS:
                    candidates.append((skew,max(o["timestamp_ms"],bybit[bj]["timestamp_ms"]),oi,bj))
    candidates.sort()
    used_o=set(); used_b=set(); out=[]
    for skew,signal_ts,oi,bj in candidates:
        if oi in used_o or bj in used_b:
            continue
        used_o.add(oi); used_b.add(bj)
        o=okx[oi]; b=bybit[bj]
        diff=o["rate"]-b["rate"]
        out.append({
            "signal_ts_ms":signal_ts,
            "okx_ts_ms":o["timestamp_ms"],
            "bybit_ts_ms":b["timestamp_ms"],
            "skew_ms":skew,
            "diff":diff,
        })
    out.sort(key=lambda x:x["signal_ts_ms"])
    return out


def sign_decimal(x:Decimal)->int:
    return 1 if x>0 else -1 if x<0 else 0


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


def venue_window(rows:list[dict[str,Any]],start_ms:int,end_ms:int)->tuple[list[dict[str,Any]],bool,int]:
    ts=[x["timestamp_ms"] for x in rows]
    lo=bisect.bisect_right(ts,start_ms)
    hi=bisect.bisect_right(ts,end_ms)
    sel=rows[lo:hi]
    points=[start_ms]+[x["timestamp_ms"] for x in sel]+[end_ms]
    max_gap=max((b-a for a,b in zip(points,points[1:])),default=end_ms-start_ms)
    ok=len(sel)>=MIN_FUNDING_EVENTS_PER_VENUE and max_gap<=MAX_COVERAGE_GAP_MS
    return sel,ok,max_gap


def build_cycles(symbol:str,okx:list[dict[str,Any]],bybit:list[dict[str,Any]],matched:list[dict[str,Any]])->list[dict[str,Any]]:
    cycles=[]
    next_free=START_MS
    for i in range(SIGNAL_LOOKBACK-1,len(matched)):
        trail=matched[i-SIGNAL_LOOKBACK+1:i+1]
        signs=[sign_decimal(x["diff"]) for x in trail]
        if 0 in signs or len(set(signs))!=1:
            continue
        signal_ts=int(matched[i]["signal_ts_ms"])
        if signal_ts<next_free:
            continue
        end_ts=signal_ts+HOLD_MS
        if end_ts>END_MS:
            continue
        direction=signs[0]

        okw,ok_okx,okx_gap=venue_window(okx,signal_ts,end_ts)
        byw,ok_bybit,bybit_gap=venue_window(bybit,signal_ts,end_ts)
        if not (ok_okx and ok_bybit):
            continue

        sum_okx=sum((x["rate"] for x in okw),Decimal(0))
        sum_bybit=sum((x["rate"] for x in byw),Decimal(0))
        gross=float(Decimal(direction)*(sum_okx-sum_bybit)*Decimal(10000))
        cycles.append({
            "symbol":symbol,
            "signal_ts_ms":signal_ts,
            "cycle_end_ms":end_ts,
            "direction_sign":direction,
            "gross_carry_bps":gross,
            "okx_funding_events":len(okw),
            "bybit_funding_events":len(byw),
            "okx_max_coverage_gap_ms":okx_gap,
            "bybit_max_coverage_gap_ms":bybit_gap,
            "cycle_start_month":datetime.fromtimestamp(signal_ts/1000,tz=timezone.utc).strftime("%Y-%m"),
        })
        next_free=end_ts
    return cycles


def summarize(per_symbol_source:dict[str,dict[str,Any]],cycles:list[dict[str,Any]])->dict[str,Any]:
    source_eligible=[s for s,v in per_symbol_source.items() if v["source_eligible"]]
    cycle_symbols=sorted({x["symbol"] for x in cycles})
    months=sorted({x["cycle_start_month"] for x in cycles})
    vals=[x["gross_carry_bps"] for x in cycles]
    positive=sum(1 for x in vals if x>0)

    symbol_summary={}
    positive_symbol_medians=0
    for s in SYMBOLS:
        sv=[x["gross_carry_bps"] for x in cycles if x["symbol"]==s]
        med=statistics.median(sv) if sv else None
        if med is not None and med>0:
            positive_symbol_medians+=1
        symbol_summary[s]={"cycle_count":len(sv),"median_gross_carry_bps":med}

    month_summary={}
    positive_month_medians=0
    for m in months:
        mv=[x["gross_carry_bps"] for x in cycles if x["cycle_start_month"]==m]
        med=statistics.median(mv) if mv else None
        if med is not None and med>0:
            positive_month_medians+=1
        month_summary[m]={"cycle_count":len(mv),"median_gross_carry_bps":med}

    data_gates={
        "source_eligible_symbols_ge8":len(source_eligible)>=MIN_SOURCE_ELIGIBLE_SYMBOLS,
        "valid_cycles_ge24":len(cycles)>=MIN_VALID_CYCLES,
        "cycle_symbols_ge8":len(cycle_symbols)>=MIN_CYCLE_SYMBOLS,
        "cycle_months_ge2":len(months)>=MIN_CYCLE_MONTHS,
    }
    median=statistics.median(vals) if vals else None
    positive_share=(positive/len(vals)) if vals else None
    structural_gates={
        "median_gross_carry_ge50bps":bool(median is not None and median>=GROSS_HEADROOM_HURDLE_BPS),
        "positive_cycle_share_ge60pct":bool(positive_share is not None and positive_share>=MIN_POSITIVE_SHARE),
        "positive_median_symbols_ge6":positive_symbol_medians>=MIN_POSITIVE_MEDIAN_SYMBOLS,
        "positive_median_months_ge2":positive_month_medians>=MIN_POSITIVE_MEDIAN_MONTHS,
    }

    if not all(data_gates.values()):
        status=DEFER
    elif all(structural_gates.values()):
        status=SURVIVE
    else:
        status=REJECT

    return {
        "status":status,
        "source_eligible_symbols":source_eligible,
        "source_eligible_count":len(source_eligible),
        "valid_cycle_count":len(cycles),
        "cycle_symbols":cycle_symbols,
        "cycle_months":months,
        "data_gates":data_gates,
        "diagnostics":{
            "p25_gross_carry_bps":type7(vals,0.25),
            "median_gross_carry_bps":median,
            "p75_gross_carry_bps":type7(vals,0.75),
            "positive_cycle_count":positive,
            "positive_cycle_share":positive_share,
            "positive_median_symbol_count":positive_symbol_medians,
            "positive_median_month_count":positive_month_medians,
        },
        "structural_gates":structural_gates,
        "per_symbol":symbol_summary,
        "per_month":month_summary,
    }


def synthetic_rows(diff:Decimal,days:int=88)->tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    okx=[]; bybit=[]
    step=8*60*60*1000
    t=START_MS
    # Symmetric around zero so differential is exact.
    while t<min(END_MS,START_MS+days*24*60*60*1000):
        okx.append({"timestamp_ms":t,"rate":diff/2})
        bybit.append({"timestamp_ms":t,"rate":-diff/2})
        t+=step
    return okx,bybit


def selftest()->int:
    try:
        per={}
        cycles=[]
        for idx,s in enumerate(SYMBOLS[:8]):
            diff=Decimal("0.00030") if idx<4 else Decimal("-0.00030")
            o,b=synthetic_rows(diff)
            m=match_signal_pairs(o,b)
            c=build_cycles(s,o,b,m)
            per[s]={
                "source_eligible":bool(o and b and len(m)>=3),
                "okx_rows":len(o),"bybit_rows":len(b),"matched_signal_pairs":len(m),
            }
            cycles.extend(c)
        for s in SYMBOLS[8:]:
            per[s]={"source_eligible":False,"okx_rows":0,"bybit_rows":0,"matched_signal_pairs":0}
        good=summarize(per,cycles)
        assert good["status"]==SURVIVE
        assert good["diagnostics"]["median_gross_carry_bps"] is not None
        assert good["diagnostics"]["median_gross_carry_bps"]>=50.0

        per2={}
        cycles2=[]
        for idx,s in enumerate(SYMBOLS[:8]):
            diff=Decimal("0.000005") if idx<4 else Decimal("-0.000005")
            o,b=synthetic_rows(diff)
            m=match_signal_pairs(o,b)
            c=build_cycles(s,o,b,m)
            per2[s]={
                "source_eligible":bool(o and b and len(m)>=3),
                "okx_rows":len(o),"bybit_rows":len(b),"matched_signal_pairs":len(m),
            }
            cycles2.extend(c)
        for s in SYMBOLS[8:]:
            per2[s]={"source_eligible":False,"okx_rows":0,"bybit_rows":0,"matched_signal_pairs":0}
        bad=summarize(per2,cycles2)
        assert bad["status"]==REJECT
        assert bad["structural_gates"]["median_gross_carry_ge50bps"] is False

        # Negative differential must map to direction -1 and still collect positive carry if persistent.
        on,bn=synthetic_rows(Decimal("-0.00030"),days=20)
        mn=match_signal_pairs(on,bn)
        cn=build_cycles("BTC",on,bn,mn)
        assert cn and cn[0]["direction_sign"]==-1 and cn[0]["gross_carry_bps"]>0

        print(SELFTEST_PASS)
        return 0
    except Exception as exc:
        print("B14B_PERSISTENT_CARRY_V01_SELF_TEST_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2


def live()->int:
    try:
        OUT_DIR.mkdir(parents=True,exist_ok=True)
        per={}
        cycles=[]
        match_skews=[]
        for i,s in enumerate(SYMBOLS,1):
            print(f"B14-B [{i}/12] {s}",flush=True)
            o=fetch_okx(s)
            b=fetch_bybit(s)
            m=match_signal_pairs(o,b)
            c=build_cycles(s,o,b,m)
            eligible=bool(o and b and len(m)>=3)
            per[s]={
                "source_eligible":eligible,
                "okx_rows":len(o),
                "bybit_rows":len(b),
                "matched_signal_pairs":len(m),
                "valid_cycles":len(c),
            }
            match_skews.extend(int(x["skew_ms"]) for x in m)
            cycles.extend(c)
            print(f"  okx={len(o)} bybit={len(b)} matched={len(m)} cycles={len(c)}",flush=True)

        summary=summarize(per,cycles)
        report={
            "stage":STAGE,
            "version":"0.1",
            "status":summary["status"],
            "window":{"start_ms":START_MS,"end_exclusive_ms":END_MS},
            "symbols":list(SYMBOLS),
            "venues":["OKX","BYBIT"],
            "architecture":{
                "signal_lookback_matched_differentials":SIGNAL_LOOKBACK,
                "signal_requires_same_nonzero_sign":True,
                "funding_magnitude_threshold":None,
                "hold_days":7,
                "nonoverlapping_per_symbol":True,
                "match_tolerance_ms":MATCH_TOLERANCE_MS,
                "all_venue_cashflows_in_hold_used":True,
                "structural_burden_bps":STRUCTURAL_BURDEN_BPS,
                "gross_headroom_hurdle_bps":GROSS_HEADROOM_HURDLE_BPS,
            },
            "source":per,
            "matched_signal_skew":{
                "count":len(match_skews),
                "median_ms":statistics.median(match_skews) if match_skews else None,
                "p99_ms":type7([float(x) for x in match_skews],0.99),
                "max_ms":max(match_skews) if match_skews else None,
            },
            **summary,
            "cycle_rows_emitted":False,
            "price_accessed":False,
            "basis_calculated":False,
            "trade_body_accessed":False,
            "l2_accessed":False,
            "strategy_price_pnl_calculated":False,
            "candidate_id_assigned":False,
            "promotional_evidence":False,
            "next_state":(
                "PREPARE_BASIS_MARGIN_AND_CAPITAL_LOCK_FEASIBILITY"
                if summary["status"]==SURVIVE
                else "CLOSE_B14B_PERSISTENT_CARRY_ARCHITECTURE_AND_EXTRACT_REUSABLE_BLOCKS"
                if summary["status"]==REJECT
                else "REVIEW_B14B_SOURCE_OR_SAMPLE"
            ),
        }
        atomic_json(OUT,report)
        print(summary["status"])
        print("valid_cycles =",summary["valid_cycle_count"])
        print("diagnostics =",json.dumps(summary["diagnostics"],sort_keys=True))
        print("data_gates =",json.dumps(summary["data_gates"],sort_keys=True))
        print("structural_gates =",json.dumps(summary["structural_gates"],sort_keys=True))
        print("price/basis/PnL/promotional = False")
        print("report =",OUT)
        return 0
    except Exception as exc:
        print("B14B_PERSISTENT_CARRY_IMPLEMENTATION_FAIL")
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
