#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE = "SC001-B15P2-P0S-2025-CROSS-TYPE-INDEX-AUDIT-V0.1"
PASS = "B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_PASS_TO_PARSER_DESIGN"
DEFER = "B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_DEFER_TO_BODY_AUDIT"
REVIEW = "B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_REVIEW"
SELFTEST_PASS = "B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_V01_SELF_TEST_PASS"

REPO = Path(__file__).resolve().parents[2]
SOURCE_DEP_REL = Path("research/sc001/sc001_b15p2_bybit_delisting_source_census_v0_1_1.py")
SOURCE_DEP_SHA256 = "7da36641ed71e0195320f0cc7cc389d629d4f843a646f64c41c1739fc0cd6b35"
CANONICAL_SOURCE_REL = Path("docs/research/sc001-b15p2-p0s-2025-holdout-source-census-result-v0.1.json")
CANONICAL_SOURCE_SHA256 = "706cc5696e863ad7cd6e81efabe1629b2f9013e2ad9cbeacad46345f17ee1c36"
UNMATCHED_LIST_SHA256 = "12478369be90bc7f20cb93bd952dffb7068c165f5f33ba4a91e7f00bf73a2847"

TARGET_SYMBOLS = (
    "A8USDT","AGTUSDT","AVAILUSDT","BALUSDT","BDXNUSDT","CELRUSDT","COSUSDT",
    "DMCUSDT","EOSUSDT","ETHWUSDT","FISUSDT","FRAGUSDT","FUELUSDT","GLMRUSDT",
    "GORKUSDT","GTCUSDT","GUSDT","LAUNCHCOINUSDT","LOOKSUSDT","MAJORUSDT",
    "NODEUSDT","OSMOUSDT","PERPUSDT","PUMPUSDT","RADUSDT","RSS3USDT","SCAUSDT",
    "SKATEUSDT","SUNDOGUSDT","SWEATUSDT","SWELLUSDT","TANSSIUSDT","TOKENUSDT",
    "ZRCUSDT",
)

OFFICIAL_TYPES = {
    "new_crypto",
    "latest_bybit_news",
    "delistings",
    "latest_activities",
    "product_updates",
    "maintenance_updates",
    "new_fiat_listings",
    "other",
}

START_MS = int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
END_MS = int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
MIN_PLAUSIBLE_MS = int(datetime(2000,1,1,tzinfo=timezone.utc).timestamp()*1000)
MAX_PLAUSIBLE_MS = int(datetime(2100,1,1,tzinfo=timezone.utc).timestamp()*1000)

ORIGINAL_CLOSED = 154
ORIGINAL_ADMITTED = 120
COVERAGE_GATE = 0.80
MIN_RECOVERIES = 4

ANN_LIMIT = 20
ANN_PAGE_CAP = 500
INST_LIMIT = 1000
INST_PAGE_CAP = 20

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT/"SC001_B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT"
OUT = OUT_DIR/"sc001_b15p2_p0s_2025_cross_type_index_audit_v0_1.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def require(cond: bool, msg: str) -> None:
    if not cond:
        fail(msg)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def compact_json_sha(obj: Any) -> str:
    raw=json.dumps(obj,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return sha256_bytes(raw)


def validate_launcher_args(package_root_arg: str|None, entrypoint_arg: str|None) -> None:
    if (package_root_arg is None)!=(entrypoint_arg is None):
        fail("INCOMPLETE_RUNNER_LAUNCHER_POSITIONAL_CONTRACT")
    if package_root_arg is None:
        return
    package_root=Path(package_root_arg).resolve()
    entrypoint=Path(entrypoint_arg).resolve()
    current=Path(__file__).resolve()
    require(entrypoint==current,"RUNNER_ENTRYPOINT_MISMATCH")
    require(package_root in current.parents,"RUNNER_PACKAGE_ROOT_MISMATCH")


def atomic_json(path: Path, obj: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)


def load_source_dependency():
    dep=REPO/SOURCE_DEP_REL
    require(dep.is_file(),"SOURCE_DEPENDENCY_MISSING")
    require(sha256_file(dep)==SOURCE_DEP_SHA256,"SOURCE_DEPENDENCY_SHA_MISMATCH")
    spec=importlib.util.spec_from_file_location("b15p2_source_dep",dep)
    require(spec is not None and spec.loader is not None,"SOURCE_DEPENDENCY_IMPORT_SPEC")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def optional_ms(value: Any) -> tuple[int|None,str|None]:
    if value in (None,""):
        return None,"MISSING"
    try:
        out=int(str(value))
    except (TypeError,ValueError):
        return None,"INVALID"
    if out<MIN_PLAUSIBLE_MS or out>MAX_PLAUSIBLE_MS:
        return None,"INVALID_OR_NON_MS"
    return out,None


def derivative_relevant(row: dict[str,Any]) -> bool:
    tset={str(x).strip().upper() for x in (row.get("tags") or [])}
    txt=(str(row.get("title") or "")+" "+str(row.get("description") or "")).upper()
    return ("DERIVATIVES" in tset) or ("FUTURES" in tset) or ("PERPETUAL" in txt)


def exact_symbol_match(symbol: str, text: str) -> bool:
    pat=r"(?<![A-Z0-9])"+re.escape(symbol.upper())+r"(?![A-Z0-9])"
    return re.search(pat,text.upper()) is not None


def normalize_any_announcement(raw: dict[str,Any]) -> dict[str,Any]:
    typ=raw.get("type") or {}
    require(isinstance(typ,dict),"ANNOUNCEMENT_TYPE_NOT_OBJECT")
    type_key=str(typ.get("key") or "")
    require(bool(type_key),"ANNOUNCEMENT_TYPE_KEY_EMPTY")
    require(type_key in OFFICIAL_TYPES,f"UNKNOWN_ANNOUNCEMENT_TYPE:{type_key}")

    url=str(raw.get("url") or "")
    require(url.startswith("https://announcements.bybit.com/"),"UNTRUSTED_ANNOUNCEMENT_URL")

    publish_ms,publish_issue=optional_ms(raw.get("publishTime"))
    date_ms,date_issue=optional_ms(raw.get("dateTimestamp"))

    tags=raw.get("tags") or []
    if not isinstance(tags,list):
        tags=[]

    return {
        "title":str(raw.get("title") or ""),
        "description":str(raw.get("description") or ""),
        "type_key":type_key,
        "type_title":str(typ.get("title") or ""),
        "tags":[str(x) for x in tags],
        "url":url,
        "publish_ms":publish_ms,
        "publish_time_issue":publish_issue,
        "date_ms":date_ms,
        "date_time_issue":date_issue,
    }


def fetch_all_announcements(src) -> tuple[list[dict[str,Any]],dict[str,Any]]:
    rows=[]
    seen=set()
    total=None
    raw_seen=0
    duplicate_rows=0
    pages=0

    for page in range(1,ANN_PAGE_CAP+1):
        obj=src.bybit_get(
            "/v5/announcements/index",
            {"locale":"en-US","page":str(page),"limit":str(ANN_LIMIT)},
            f"Bybit all-announcement page {page}",
        )
        result=obj.get("result") or {}
        if total is None:
            raw_total=result.get("total")
            if raw_total not in (None,""):
                try:
                    total=int(str(raw_total))
                except (TypeError,ValueError):
                    fail(f"ANNOUNCEMENT_TOTAL_MALFORMED:{raw_total!r}")

        batch=result.get("list") or []
        require(isinstance(batch,list),"ANNOUNCEMENT_LIST_NOT_ARRAY")
        pages=page
        raw_seen+=len(batch)

        for item in batch:
            require(isinstance(item,dict),"ANNOUNCEMENT_ROW_NOT_OBJECT")
            row=normalize_any_announcement(item)
            key=(row["url"],row["publish_ms"],row["date_ms"],row["title"],row["type_key"])
            if key in seen:
                duplicate_rows+=1
                continue
            seen.add(key)
            rows.append(row)

        if len(batch)<ANN_LIMIT:
            break
        if total is not None and raw_seen>=total:
            break
    else:
        fail("ANNOUNCEMENT_PAGINATION_CAP_REACHED")

    if total is not None:
        require(raw_seen>=total,"ANNOUNCEMENT_PAGINATION_INCOMPLETE")

    meta={
        "endpoint":"/v5/announcements/index",
        "locale":"en-US",
        "type_filter":None,
        "reported_total":total,
        "raw_rows_seen":raw_seen,
        "deduplicated_rows":len(rows),
        "duplicate_rows":duplicate_rows,
        "pages":pages,
        "page_cap":ANN_PAGE_CAP,
    }
    return rows,meta


def normalize_target_instrument(item: dict[str,Any]) -> dict[str,Any]|None:
    symbol=str(item.get("symbol") or "")
    if symbol not in TARGET_SYMBOLS:
        return None
    if str(item.get("contractType") or "")!="LinearPerpetual":
        return None
    if str(item.get("quoteCoin") or "")!="USDT":
        return None
    if str(item.get("status") or "")!="Closed":
        return None

    pre=item.get("isPreListing")
    if pre is True or str(pre).strip().lower() in {"true","1"}:
        return None

    delivery,delivery_issue=optional_ms(item.get("deliveryTime"))
    require(delivery is not None,f"TARGET_DELIVERY_INVALID:{symbol}:{delivery_issue}")
    if not (START_MS<=delivery<END_MS):
        return None

    launch,launch_issue=optional_ms(item.get("launchTime"))
    if item.get("launchTime") not in (None,""):
        require(launch is not None,f"TARGET_LAUNCH_INVALID:{symbol}:{launch_issue}")
    if launch is not None:
        require(launch<delivery,f"TARGET_NONCAUSAL_LAUNCH:{symbol}")

    return {
        "symbol":symbol,
        "symbol_id":item.get("symbolId"),
        "launch_ms":launch,
        "delivery_ms":delivery,
        "delivery_utc":datetime.fromtimestamp(delivery/1000,tz=timezone.utc).isoformat(),
    }


def fetch_target_instruments(src) -> tuple[dict[str,dict[str,Any]],dict[str,Any]]:
    found={}
    cursor=""
    pages=0
    for page in range(1,INST_PAGE_CAP+1):
        params={"category":"linear","status":"Closed","limit":str(INST_LIMIT)}
        if cursor:
            params["cursor"]=cursor
        obj=src.bybit_get(
            "/v5/market/instruments-info",
            params,
            f"Bybit closed instruments page {page}",
        )
        result=obj.get("result") or {}
        batch=result.get("list") or []
        require(isinstance(batch,list),"INSTRUMENT_LIST_NOT_ARRAY")
        pages=page
        for item in batch:
            require(isinstance(item,dict),"INSTRUMENT_ROW_NOT_OBJECT")
            row=normalize_target_instrument(item)
            if row is None:
                continue
            sym=row["symbol"]
            require(sym not in found,f"DUPLICATE_TARGET_2025_EVENT:{sym}")
            found[sym]=row

        nxt=str(result.get("nextPageCursor") or "")
        if not nxt:
            break
        require(nxt!=cursor,"INSTRUMENT_CURSOR_DID_NOT_ADVANCE")
        cursor=nxt
    else:
        fail("INSTRUMENT_PAGINATION_CAP_REACHED")

    require(set(found)==set(TARGET_SYMBOLS),
            "TARGET_INSTRUMENT_IDENTITY_MISMATCH:"
            +json.dumps(sorted(set(TARGET_SYMBOLS)-set(found))))

    return found,{
        "endpoint":"/v5/market/instruments-info",
        "category":"linear",
        "status":"Closed",
        "target_count":len(found),
        "pages":pages,
    }


def classify_route(ann: dict[str,Any]) -> str:
    if ann["type_key"]!="delistings":
        return "NON_DELISTINGS_TYPE"
    if not derivative_relevant(ann):
        return "DELISTINGS_DERIVATIVE_FILTER"
    return "DELISTINGS_FEED_OR_RETRIEVAL_DELTA"


def analyze(
    instruments: dict[str,dict[str,Any]],
    announcements: list[dict[str,Any]],
    *,
    target_symbols: tuple[str,...]|list[str],
    original_closed: int,
    original_admitted: int,
    min_recoveries: int,
) -> dict[str,Any]:
    rows=[]
    integrity=[]
    route_counts={}
    recovered=[]

    for symbol in sorted(target_symbols):
        inst=instruments[symbol]
        exact=[]
        invalid_ts=[]
        pre_launch=0
        post_delivery=0

        for ann in announcements:
            text=ann["title"]+" "+ann["description"]
            if not exact_symbol_match(symbol,text):
                continue

            pub=ann.get("publish_ms")
            if pub is None:
                invalid_ts.append({
                    "symbol":symbol,
                    "type_key":ann["type_key"],
                    "url":ann["url"],
                    "issue":ann.get("publish_time_issue") or "INVALID",
                    "date_ms_diagnostic_only":ann.get("date_ms"),
                })
                continue

            launch=inst.get("launch_ms")
            if launch is not None and pub<launch:
                pre_launch+=1
                continue
            if pub>=inst["delivery_ms"]:
                post_delivery+=1
                continue

            route=classify_route(ann)
            route_counts[route]=route_counts.get(route,0)+1
            exact.append({
                "type_key":ann["type_key"],
                "tags":ann["tags"],
                "url":ann["url"],
                "publish_ms":pub,
                "route":route,
                "original_derivative_relevant":derivative_relevant(ann),
            })

        if invalid_ts:
            integrity.extend(invalid_ts)

        exact.sort(key=lambda x:(x["publish_ms"],x["url"]))
        if exact:
            recovered.append(symbol)

        rows.append({
            "symbol":symbol,
            "launch_ms":inst.get("launch_ms"),
            "delivery_ms":inst["delivery_ms"],
            "delivery_utc":inst["delivery_utc"],
            "causal_exact_match_count":len(exact),
            "causal_matches":exact,
            "pre_launch_exact_match_count":pre_launch,
            "post_delivery_exact_match_count":post_delivery,
            "missing_or_invalid_publish_exact_match_count":len(invalid_ts),
            "recovered":bool(exact),
        })

    recovery_count=len(recovered)
    potential_admitted=original_admitted+recovery_count
    potential_coverage=potential_admitted/original_closed

    if integrity:
        status=REVIEW
    elif recovery_count>=min_recoveries:
        status=PASS
    else:
        status=DEFER

    return {
        "status":status,
        "target_unmatched_count":len(target_symbols),
        "recovered_symbol_count":recovery_count,
        "recovered_symbols":sorted(recovered),
        "still_unmatched_symbols":sorted(set(target_symbols)-set(recovered)),
        "route_match_counts":dict(sorted(route_counts.items())),
        "source_integrity_issue_count":len(integrity),
        "source_integrity_issues":integrity,
        "original_closed_count":original_closed,
        "original_admitted_count":original_admitted,
        "minimum_recoveries_for_80pct":min_recoveries,
        "potential_admitted_count_if_recovery_routes_are_later_validated":potential_admitted,
        "potential_coverage_if_recovery_routes_are_later_validated":potential_coverage,
        "rows":rows,
        "firewalls":{
            "affected_contract_price_accessed":False,
            "index_value_accessed":False,
            "basis_calculated":False,
            "returns_calculated":False,
            "pnl_calculated":False,
            "l1_l2_accessed":False,
            "individual_trades_accessed":False,
            "funding_accessed":False,
            "external_venue_accessed":False,
            "trading":False,
        },
    }


def validate_canonical_input() -> dict[str,Any]:
    path=REPO/CANONICAL_SOURCE_REL
    require(path.is_file(),"CANONICAL_SOURCE_RESULT_MISSING")
    raw=path.read_bytes()
    require(sha256_bytes(raw)==CANONICAL_SOURCE_SHA256,"CANONICAL_SOURCE_RESULT_SHA_MISMATCH")
    obj=json.loads(raw.decode("utf-8"))
    require(isinstance(obj,dict),"CANONICAL_SOURCE_RESULT_NOT_OBJECT")
    unmatched=obj.get("unmatched_symbols")
    require(isinstance(unmatched,list),"CANONICAL_UNMATCHED_NOT_ARRAY")
    frozen=sorted(str(x) for x in unmatched)
    require(tuple(frozen)==tuple(TARGET_SYMBOLS),"CANONICAL_UNMATCHED_SET_MISMATCH")
    require(compact_json_sha(frozen)==UNMATCHED_LIST_SHA256,"CANONICAL_UNMATCHED_LIST_SHA_MISMATCH")
    require(int(obj.get("closed_in_scope_count"))==ORIGINAL_CLOSED,"ORIGINAL_CLOSED_COUNT_MISMATCH")
    require(int(obj.get("admitted_event_count"))==ORIGINAL_ADMITTED,"ORIGINAL_ADMITTED_COUNT_MISMATCH")
    require(ORIGINAL_ADMITTED+MIN_RECOVERIES >= COVERAGE_GATE*ORIGINAL_CLOSED,"RECOVERY_THRESHOLD_TOO_LOW")
    require(ORIGINAL_ADMITTED+MIN_RECOVERIES-1 < COVERAGE_GATE*ORIGINAL_CLOSED,"RECOVERY_THRESHOLD_NOT_MINIMAL")
    return obj


def selftest() -> int:
    try:
        syms=("AUSDT","BUSDT","CUSDT","DUSDT","EUSDT")
        base=int(datetime(2025,7,1,9,tzinfo=timezone.utc).timestamp()*1000)
        instruments={}
        for i,s in enumerate(syms):
            delivery=base+i*86_400_000
            instruments[s]={
                "symbol":s,
                "launch_ms":delivery-30*86_400_000,
                "delivery_ms":delivery,
                "delivery_utc":datetime.fromtimestamp(delivery/1000,tz=timezone.utc).isoformat(),
            }

        anns=[]
        kinds=[
            ("AUSDT","product_updates",["Derivatives"],"AUSDT update",False),
            ("BUSDT","other",["Futures"],"BUSDT notice",False),
            ("CUSDT","delistings",["Spot"],"CUSDT removal",False),
            ("DUSDT","delistings",["Derivatives"],"Delisting of DUSDT Perpetual Contract",False),
        ]
        for idx,(sym,typ,tags,title,_bad) in enumerate(kinds):
            delivery=instruments[sym]["delivery_ms"]
            anns.append({
                "title":title,
                "description":"Official notice for "+sym,
                "type_key":typ,
                "type_title":typ,
                "tags":tags,
                "url":f"https://announcements.bybit.com/en-US/article/{sym.lower()}-{idx}",
                "publish_ms":delivery-48*3_600_000,
                "publish_time_issue":None,
                "date_ms":delivery-48*3_600_000,
                "date_time_issue":None,
            })

        out=analyze(
            instruments,anns,target_symbols=syms,
            original_closed=10,original_admitted=4,min_recoveries=4,
        )
        assert out["status"]==PASS
        assert out["recovered_symbol_count"]==4
        assert set(out["recovered_symbols"])==set(("AUSDT","BUSDT","CUSDT","DUSDT"))
        routes={r["route"] for row in out["rows"] for r in row["causal_matches"]}
        assert "NON_DELISTINGS_TYPE" in routes
        assert "DELISTINGS_DERIVATIVE_FILTER" in routes
        assert "DELISTINGS_FEED_OR_RETRIEVAL_DELTA" in routes

        out2=analyze(
            instruments,anns[:3],target_symbols=syms,
            original_closed=10,original_admitted=4,min_recoveries=4,
        )
        assert out2["status"]==DEFER
        assert out2["recovered_symbol_count"]==3

        bad=dict(anns[0])
        bad["publish_ms"]=None
        bad["publish_time_issue"]="MISSING"
        out3=analyze(
            instruments,[bad]+anns[1:],target_symbols=syms,
            original_closed=10,original_admitted=4,min_recoveries=4,
        )
        assert out3["status"]==REVIEW
        assert out3["source_integrity_issue_count"]==1

        assert exact_symbol_match("AUSDT","notice AUSDT perpetual")
        assert not exact_symbol_match("AUSDT","notice XAUSDT perpetual")
        assert not exact_symbol_match("AUSDT","notice AUSDTX perpetual")

        fake={
            "type":{"key":"product_updates","title":"Product Updates"},
            "title":"AUSDT update","description":"","tags":["Derivatives"],
            "url":"https://announcements.bybit.com/en-US/article/a",
            "publishTime":str(base),"dateTimestamp":str(base),
        }
        norm=normalize_any_announcement(fake)
        assert norm["type_key"]=="product_updates"
        assert norm["publish_ms"]==base

        print(SELFTEST_PASS)
        return 0
    except Exception as exc:
        print("B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_V01_SELF_TEST_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2


def live() -> int:
    try:
        source=validate_canonical_input()
        src=load_source_dependency()
        instruments,inst_meta=fetch_target_instruments(src)
        announcements,ann_meta=fetch_all_announcements(src)
        audit=analyze(
            instruments,
            announcements,
            target_symbols=TARGET_SYMBOLS,
            original_closed=ORIGINAL_CLOSED,
            original_admitted=ORIGINAL_ADMITTED,
            min_recoveries=MIN_RECOVERIES,
        )
        report={
            "schema":"sc001.b15p2_p0s_2025_cross_type_index_audit_result.v0.1",
            "date":"2026-09-29",
            "stage":STAGE,
            "status":audit["status"],
            "canonical_source":{
                "path":str(CANONICAL_SOURCE_REL),
                "sha256":CANONICAL_SOURCE_SHA256,
                "frozen_unmatched_count":len(TARGET_SYMBOLS),
                "frozen_unmatched_list_sha256":UNMATCHED_LIST_SHA256,
            },
            "dependency":{
                "path":str(SOURCE_DEP_REL),
                "sha256":SOURCE_DEP_SHA256,
            },
            "official_announcement_types":sorted(OFFICIAL_TYPES),
            "announcement_source":ann_meta,
            "instrument_source":inst_meta,
            **audit,
            "article_body_hydration_performed":False,
            "date_timestamp_used_as_publish_fallback":False,
            "source_gate_threshold_changed":False,
            "next_state":(
                "DESIGN_CORRECTED_2025_SOURCE_CENSUS_PARSER_KEEP_80PCT_GATE"
                if audit["status"]==PASS
                else (
                    "PREREGISTER_OFFICIAL_BYBIT_ARTICLE_BODY_STRUCTURE_AUDIT_NO_PRICE"
                    if audit["status"]==DEFER
                    else "REVIEW_SOURCE_INDEX_INTEGRITY_NO_PRICE"
                )
            ),
        }
        atomic_json(OUT,report)
        print(report["status"])
        print("all_announcement_rows =",ann_meta["deduplicated_rows"])
        print("announcement_pages =",ann_meta["pages"])
        print("recovered_symbols =",audit["recovered_symbol_count"])
        print("route_match_counts =",json.dumps(audit["route_match_counts"],sort_keys=True))
        print("source_integrity_issues =",audit["source_integrity_issue_count"])
        print("potential_coverage =",audit["potential_coverage_if_recovery_routes_are_later_validated"])
        print("article_body_hydration = CLOSED")
        print("price/index/basis/returns/PnL/trading = CLOSED")
        print("report =",OUT)
        return 0
    except Exception as exc:
        err={
            "schema":"sc001.b15p2_p0s_2025_cross_type_index_audit_result.v0.1",
            "date":"2026-09-29",
            "stage":STAGE,
            "status":REVIEW,
            "error_type":type(exc).__name__,
            "error_message":str(exc),
            "article_body_hydration_performed":False,
            "firewalls":{
                "affected_contract_price_accessed":False,
                "index_value_accessed":False,
                "basis_calculated":False,
                "returns_calculated":False,
                "pnl_calculated":False,
                "trading":False,
            },
            "next_state":"TECHNICAL_SOURCE_AUDIT_REVIEW_NO_PRICE",
        }
        atomic_json(OUT,err)
        print(REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        print("price/index/basis/returns/PnL/trading = CLOSED")
        print("report =",OUT)
        return 2


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","live"),default="self-test")
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)
    return selftest() if a.mode=="self-test" else live()


if __name__=="__main__":
    raise SystemExit(main())
