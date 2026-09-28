#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_PASS"
REVIEW="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_REVIEW"
SELFTEST_PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V013_SELF_TEST_PASS"

EXPECTED_SOURCE_SHA="c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c"
EXPECTED_EVENT_SET_SHA="1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2"
ALLOWED_HOST="announcements.bybit.com"
TIMEOUT=30
RETRIES=2
MAX_HTML=2_000_000
REQUEST_SLEEP=0.25

DEFAULT_REPO=Path(os.environ.get("B15P2_REPO_ROOT","/var/lib/botmarket-github-control/repo"))
SOURCE_REL=Path("docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json")
FREEZE_REL=Path("docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json")
DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_B15P2_ANNOUNCEMENT_SEMANTIC_AUDIT"
OUT=OUT_DIR/"sc001_b15p2_announcement_body_semantic_audit_v0_1.json"

MONTH_FORMATS=("%b %d, %Y, %I:%M%p UTC","%B %d, %Y, %I:%M%p UTC")

SKIP_TAGS=frozenset({"head","script","style","noscript","svg"})

class VisibleTextParser(HTMLParser):
    def __init__(self)->None:
        super().__init__(convert_charrefs=True)
        self.skip=0
        self.parts:list[str]=[]

    def handle_starttag(self,tag:str,attrs:list[tuple[str,str|None]])->None:
        if tag.lower() in SKIP_TAGS:
            self.skip+=1

    def handle_endtag(self,tag:str)->None:
        if tag.lower() in SKIP_TAGS and self.skip:
            self.skip-=1

    def handle_data(self,data:str)->None:
        if not self.skip and data.strip():
            self.parts.append(data)

def sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def utc_now()->str:
    return datetime.now(timezone.utc).isoformat()

def normalize_space(text:str)->str:
    return re.sub(r"\s+"," ",html.unescape(text)).strip()

def visible_text(raw:bytes)->str:
    text=raw.decode("utf-8",errors="strict")
    p=VisibleTextParser()
    p.feed(text)
    out=normalize_space(" ".join(p.parts))
    if not out:
        raise RuntimeError("visible body empty")
    return out

def article_region(text:str,symbol:str)->str:
    title=f"Delisting of {symbol} Perpetual Contract"
    start=text.lower().find(title.lower())
    if start<0:
        raise RuntimeError("exact announcement title not found in visible text")

    region=text[start:start+20_000]
    terminators=(
        "If you have any questions",
        "Thank you for your continued support",
        "The Bybit Team",
    )
    cut=None
    lower=region.lower()
    for marker in terminators:
        pos=lower.find(marker.lower())
        if pos>=0:
            end=pos+len(marker)
            cut=end if cut is None else min(cut,end)
    if cut is not None:
        region=region[:cut]
    region=normalize_space(region)
    if len(region)<120:
        raise RuntimeError("announcement article region unexpectedly short")
    return region

def validate_launcher_args(package_root_arg:str|None,entrypoint_arg:str|None)->None:
    if (package_root_arg is None)!=(entrypoint_arg is None):
        raise RuntimeError("incomplete Runner launcher positional contract")
    if package_root_arg is None:
        return
    package_root=Path(package_root_arg).resolve()
    entrypoint=Path(entrypoint_arg).resolve()
    current=Path(__file__).resolve()
    if entrypoint!=current:
        raise RuntimeError("Runner launcher entrypoint mismatch")
    if package_root not in current.parents:
        raise RuntimeError("Runner launcher package-root mismatch")

def load_json(path:Path)->dict[str,Any]:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        raise RuntimeError(f"JSON object required: {path}")
    return obj

def require(cond:bool,code:str)->None:
    if not cond:
        raise RuntimeError(code)

def parse_announcement_time(text:str,symbol:str)->int|None:
    pat=re.compile(
        r"delisting\s+the\s+"+re.escape(symbol)+
        r"\s+perpetual\s+contract\s+at\s+"
        r"([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s*(?:AM|PM)\s+UTC)",
        re.I,
    )
    m=pat.search(text)
    if not m:
        return None
    raw=re.sub(r"\s+(AM|PM)",r"\1",m.group(1),flags=re.I)
    for fmt in MONTH_FORMATS:
        try:
            dt=datetime.strptime(raw,fmt).replace(tzinfo=timezone.utc)
            return int(dt.timestamp()*1000)
        except ValueError:
            pass
    return None

def classify_text(text:str,symbol:str,delivery_ms:int)->dict[str,Any]:
    upper=text.upper()
    symbol_upper=symbol.upper()
    title_ok=bool(re.search(
        r"DEL(?:ISTING)?\s+OF\s+"+re.escape(symbol_upper)+r"\s+PERPETUAL\s+CONTRACT",
        upper,
    ))

    announced_ms=parse_announcement_time(text,symbol)
    time_class=(
        "TIME_UNRESOLVED" if announced_ms is None
        else ("TIME_MATCH" if announced_ms==delivery_ms else "TIME_MISMATCH")
    )

    trading_stop=bool(re.search(
        r"TRADING\s+WILL\s+NO\s+LONGER\s+BE\s+SUPPORTED",
        upper,
    ))
    order_cancel=bool(re.search(
        r"ACTIVE\s+ORDERS.*CONDITIONAL\s+ORDERS.*AUTOMATICALLY\s+CANCEL",
        upper,
    ))
    auto_close=bool(re.search(
        r"OPEN\s+POSITIONS.*AUTOMATICALLY\s+CLOSED",
        upper,
    ))

    basis="BASIS_UNRESOLVED"
    window=None
    avg=re.search(
        r"CLOSING\s+PRICE.*AVERAGE\s+INDEX\s+PRICE.*?(\d+)\s+MINUTES?\s+PRIOR\s+TO\s+THE\s+DELISTING",
        upper,
    )
    if avg:
        basis="AVERAGE_INDEX_PRICE_WINDOW"
        window=int(avg.group(1))
    elif auto_close:
        close_sentence=re.search(r"CLOSING\s+PRICE[^.]{0,400}",upper)
        if close_sentence:
            basis="OTHER_EXPLICIT_BASIS"

    funding=bool(re.search(r"\bFUNDING\b",upper))
    revision=bool(re.search(r"\b(POSTPON\w*|RESCHEDUL\w*|REVIS\w*|UPDATED?)\b",upper))

    resolved=(
        title_ok and
        time_class=="TIME_MATCH" and
        auto_close and
        basis!="BASIS_UNRESOLVED"
    )

    return {
        "symbol":symbol,
        "delivery_ms":delivery_ms,
        "title_symbol_match":title_ok,
        "announced_delisting_ms":announced_ms,
        "time_class":time_class,
        "trading_stop":"TRADING_STOP_EXPLICIT" if trading_stop else "TRADING_STOP_UNRESOLVED",
        "active_order_handling":"ACTIVE_ORDERS_AUTO_CANCEL_EXPLICIT" if order_cancel else "ACTIVE_ORDER_HANDLING_UNRESOLVED",
        "open_position_handling":"OPEN_POSITIONS_AUTO_CLOSE_EXPLICIT" if auto_close else "OPEN_POSITION_HANDLING_UNRESOLVED",
        "closing_price_basis":basis,
        "closing_price_window_minutes":window,
        "funding_treatment":"FUNDING_EXPLICITLY_MENTIONED" if funding else "FUNDING_NOT_STATED",
        "revision_wording":"REVISION_OR_POSTPONEMENT_MENTIONED" if revision else "NO_REVISION_OR_POSTPONEMENT_WORDING",
        "semantic_resolved":resolved,
    }

def fetch_page(url:str)->tuple[bytes,str]:
    parsed=urllib.parse.urlparse(url)
    require(parsed.scheme=="https","URL_SCHEME")
    require(parsed.hostname==ALLOWED_HOST,"URL_HOST")

    last:Exception|None=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"BotMarketplace-SC001-B15P2-SemanticAudit/0.1",
                "Accept":"text/html,application/xhtml+xml",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                final=resp.geturl()
                final_host=urllib.parse.urlparse(final).hostname
                require(final_host==ALLOWED_HOST,"REDIRECT_HOST")
                raw=resp.read(MAX_HTML+1)
            require(len(raw)<=MAX_HTML,"HTML_SIZE_CAP")
            return raw,final
        except urllib.error.HTTPError as exc:
            last=exc
            if exc.code in {408,425,429,500,502,503,504} and attempt<RETRIES:
                print(f"FETCH_RETRY attempt={attempt}/{RETRIES} kind=HTTP code={exc.code} url={url}",flush=True)
                time.sleep(float(attempt))
                continue
            raise RuntimeError(f"HTTP_ERROR:{exc.code}:{exc.reason}") from exc
        except (urllib.error.URLError,TimeoutError,OSError) as exc:
            last=exc
            if attempt<RETRIES:
                print(f"FETCH_RETRY attempt={attempt}/{RETRIES} kind={type(exc).__name__} url={url}",flush=True)
                time.sleep(float(attempt))
                continue
            raise RuntimeError(f"NETWORK_ERROR:{type(exc).__name__}:{exc}") from exc
    raise RuntimeError(f"FETCH_FAILED:{type(last).__name__}:{last}")

def validate_frozen_input(repo:Path)->tuple[dict[str,Any],dict[str,Any]]:
    source_path=repo/SOURCE_REL
    freeze_path=repo/FREEZE_REL
    require(source_path.is_file(),"SOURCE_RESULT_MISSING")
    require(freeze_path.is_file(),"EVENT_FREEZE_MISSING")
    raw=source_path.read_bytes()
    require(sha256_bytes(raw)==EXPECTED_SOURCE_SHA,"SOURCE_RESULT_SHA")
    source=json.loads(raw.decode("utf-8"))
    freeze=load_json(freeze_path)
    require(freeze.get("status")=="B15P2_EXACT_ADMITTED_EVENT_SET_FROZEN","FREEZE_STATUS")
    require(freeze.get("event_count")==94,"FREEZE_EVENT_COUNT")
    require(freeze.get("event_set_sha256")==EXPECTED_EVENT_SET_SHA,"EVENT_SET_SHA")
    require((freeze.get("source_result") or {}).get("sha256")==EXPECTED_SOURCE_SHA,"FREEZE_SOURCE_SHA")
    require(source.get("status")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS","SOURCE_STATUS")
    require(source.get("admitted_event_count")==94,"SOURCE_EVENT_COUNT")
    require(source.get("announcement_match_coverage")==1.0,"SOURCE_COVERAGE")
    require(source.get("source_integrity_issue_count")==0,"SOURCE_INTEGRITY")
    require(source.get("price_accessed") is False,"SOURCE_PRICE_FIREWALL")
    require(source.get("basis_calculated") is False,"SOURCE_BASIS_FIREWALL")
    require(source.get("pnl_calculated") is False,"SOURCE_PNL_FIREWALL")
    require(source.get("event_ranked_by_outcome") is False,"SOURCE_RANKING_FIREWALL")
    return source,freeze

def build_report(source:dict[str,Any],fetcher)->dict[str,Any]:
    rows=[]
    errors=[]
    total=len(source["events"])
    started_utc=utc_now()
    for idx,e in enumerate(source["events"]):
        url=e["announcement_urls"][0]
        symbol=e["symbol"]
        t0=time.monotonic()
        if fetcher is fetch_page:
            print(f"EVENT_START {idx+1:03d}/{total:03d} symbol={symbol}",flush=True)
        try:
            raw,final=fetcher(url)
            text=visible_text(raw)
            region=article_region(text,symbol)
            sem=classify_text(region,symbol,e["delivery_ms"])
            sem.update({
                "requested_url":url,
                "final_url":final,
                "fetched_utc":utc_now(),
                "fetch_elapsed_seconds":round(time.monotonic()-t0,3),
                "raw_html_sha256":sha256_bytes(raw),
                "normalized_text_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "normalized_text_length":len(text),
                "article_region_sha256":hashlib.sha256(region.encode("utf-8")).hexdigest(),
                "article_region_length":len(region),
            })
            rows.append(sem)
            if fetcher is fetch_page:
                print(
                    f"EVENT_DONE {idx+1:03d}/{total:03d} symbol={symbol} "
                    f"elapsed_s={sem['fetch_elapsed_seconds']}",
                    flush=True,
                )
        except Exception as exc:
            elapsed=round(time.monotonic()-t0,3)
            errors.append({
                "symbol":symbol,
                "delivery_ms":e["delivery_ms"],
                "requested_url":url,
                "fetched_utc":utc_now(),
                "fetch_elapsed_seconds":elapsed,
                "error_type":type(exc).__name__,
                "error_message":str(exc),
            })
            if fetcher is fetch_page:
                print(
                    f"EVENT_ERROR {idx+1:03d}/{total:03d} symbol={symbol} "
                    f"kind={type(exc).__name__} elapsed_s={elapsed} error={exc}",
                    flush=True,
                )
        if fetcher is fetch_page and idx+1<total:
            time.sleep(REQUEST_SLEEP)
    finished_utc=utc_now()

    basis_counts=Counter(r["closing_price_basis"] for r in rows)
    window_counts=Counter(str(r["closing_price_window_minutes"]) for r in rows if r["closing_price_window_minutes"] is not None)
    unresolved=[r["symbol"] for r in rows if not r["semantic_resolved"]]
    time_mismatch=[r["symbol"] for r in rows if r["time_class"]!="TIME_MATCH"]

    status=PASS if len(rows)==94 and not errors and not unresolved and not time_mismatch else REVIEW

    return {
        "schema":"sc001.b15p2_announcement_body_semantic_audit_result.v0.1",
        "date":"2026-09-27",
        "status":status,
        "frozen_event_set_sha256":EXPECTED_EVENT_SET_SHA,
        "event_count_expected":94,
        "acquisition_started_utc":started_utc,
        "acquisition_finished_utc":finished_utc,
        "page_fetch_success_count":len(rows),
        "page_fetch_error_count":len(errors),
        "exact_time_match_count":sum(1 for r in rows if r["time_class"]=="TIME_MATCH"),
        "automatic_close_explicit_count":sum(1 for r in rows if r["open_position_handling"]=="OPEN_POSITIONS_AUTO_CLOSE_EXPLICIT"),
        "active_order_auto_cancel_explicit_count":sum(1 for r in rows if r["active_order_handling"]=="ACTIVE_ORDERS_AUTO_CANCEL_EXPLICIT"),
        "trading_stop_explicit_count":sum(1 for r in rows if r["trading_stop"]=="TRADING_STOP_EXPLICIT"),
        "funding_mentioned_count":sum(1 for r in rows if r["funding_treatment"]=="FUNDING_EXPLICITLY_MENTIONED"),
        "revision_wording_count":sum(1 for r in rows if r["revision_wording"]=="REVISION_OR_POSTPONEMENT_MENTIONED"),
        "closing_price_basis_counts":dict(sorted(basis_counts.items())),
        "closing_price_window_minute_counts":dict(sorted(window_counts.items())),
        "unresolved_symbols":unresolved,
        "time_mismatch_or_unresolved_symbols":time_mismatch,
        "fetch_errors":errors,
        "events":rows,
        "firewalls":{
            "price_accessed":False,
            "external_reference_price_accessed":False,
            "index_values_accessed":False,
            "basis_calculated":False,
            "returns_calculated":False,
            "pnl_calculated":False,
            "event_ranked_by_outcome":False,
        },
        "next_state":(
            "FREEZE_SEMANTIC_CLASSES_AND_RUN_PRE_PRICE_STRATEGY_GATE"
            if status==PASS
            else "REVIEW_SEMANTIC_SOURCE_INTEGRITY_WITHOUT_OPENING_PRICES"
        ),
    }

def selftest()->int:
    stage="INIT"
    try:
        fixture_symbol="TESTUSDT"
        delivery=int(datetime(2026,7,25,9,0,tzinfo=timezone.utc).timestamp()*1000)
        html1=b"""<html><body><h1>Delisting of TESTUSDT Perpetual Contract</h1>
        <p>Bybit will be delisting the TESTUSDT Perpetual Contract at Jul 25, 2026, 9:00AM UTC.</p>
        <p>The TESTUSDT Perpetual Contract will be delisted and trading will no longer be supported.</p>
        <p>All active orders and conditional orders for the TESTUSDT Perpetual Contract will be automatically canceled.</p>
        <p>Any open positions in the TESTUSDT Perpetual Contract will be automatically closed. The closing price will be based on the average index price in the 30 minutes prior to the delisting.</p>
        </body></html>"""
        stage="FIXTURE1_VISIBLE"
        text=visible_text(html1)
        stage="FIXTURE1_REGION"
        region=article_region(text,fixture_symbol)
        stage="FIXTURE1_CLASSIFY"
        r=classify_text(region,fixture_symbol,delivery)
        assert r["title_symbol_match"] is True
        assert r["time_class"]=="TIME_MATCH"
        assert r["trading_stop"]=="TRADING_STOP_EXPLICIT"
        assert r["active_order_handling"]=="ACTIVE_ORDERS_AUTO_CANCEL_EXPLICIT"
        assert r["open_position_handling"]=="OPEN_POSITIONS_AUTO_CLOSE_EXPLICIT"
        assert r["closing_price_basis"]=="AVERAGE_INDEX_PRICE_WINDOW"
        assert r["closing_price_window_minutes"]==30
        assert r["funding_treatment"]=="FUNDING_NOT_STATED"
        assert r["semantic_resolved"] is True

        html2=b"""<html><body><h1>Delisting of TESTUSDT Perpetual Contract</h1>
        <p>Bybit will be delisting the TESTUSDT Perpetual Contract at Jul 25, 2026, 10:00AM UTC.</p>
        <p>Any open positions in the TESTUSDT Perpetual Contract will be automatically closed. The closing price will use the mark price.</p>
        </body></html>"""
        stage="FIXTURE2_VISIBLE_REGION_CLASSIFY"
        r2=classify_text(article_region(visible_text(html2),fixture_symbol),fixture_symbol,delivery)
        assert r2["time_class"]=="TIME_MISMATCH"
        assert r2["open_position_handling"]=="OPEN_POSITIONS_AUTO_CLOSE_EXPLICIT"
        assert r2["closing_price_basis"]=="OTHER_EXPLICIT_BASIS"
        assert r2["semantic_resolved"] is False

        html3=b"""<html><head><script>fake open positions automatically closed</script></head>
        <body><h1>Delisting of TESTUSDT Perpetual Contract</h1>
        <p>Bybit will be delisting the TESTUSDT Perpetual Contract at Jul 25, 2026, 9:00AM UTC.</p>
        </body></html>"""
        stage="FIXTURE3_VISIBLE"
        visible3=visible_text(html3)
        assert "fake open positions automatically closed" not in visible3
        assert "Delisting of TESTUSDT Perpetual Contract" in visible3
        stage="FIXTURE3_REGION_CLASSIFY"
        r3=classify_text(article_region(visible3,fixture_symbol),fixture_symbol,delivery)
        assert r3["open_position_handling"]=="OPEN_POSITION_HANDLING_UNRESOLVED"
        assert r3["semantic_resolved"] is False

        html4=b"""<html><body>
        <nav>Funding Products Updated News</nav>
        <h1>Delisting of TESTUSDT Perpetual Contract</h1>
        <p>Bybit will be delisting the TESTUSDT Perpetual Contract at Jul 25, 2026, 9:00AM UTC.</p>
        <p>Any open positions in the TESTUSDT Perpetual Contract will be automatically closed. The closing price will be based on the average index price in the 30 minutes prior to the delisting.</p>
        <p>Thank you for your continued support.</p>
        <footer>Funding Updated Products</footer>
        </body></html>"""
        stage="FIXTURE4_VISIBLE_REGION"
        region4=article_region(visible_text(html4),fixture_symbol)
        stage="FIXTURE4_CLASSIFY"
        r4=classify_text(region4,fixture_symbol,delivery)
        assert r4["funding_treatment"]=="FUNDING_NOT_STATED"
        assert r4["revision_wording"]=="NO_REVISION_OR_POSTPONEMENT_WORDING"

        print(SELFTEST_PASS)
        return 0
    except Exception as exc:
        print("B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V013_SELF_TEST_REVIEW")
        print("stage =",stage)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def live()->int:
    try:
        source,_=validate_frozen_input(DEFAULT_REPO)
        report=build_report(source,fetch_page)
        OUT_DIR.mkdir(parents=True,exist_ok=True)
        tmp=OUT.with_name(OUT.name+".tmp")
        tmp.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        os.replace(tmp,OUT)
        print(report["status"])
        print("page_fetch_success =",report["page_fetch_success_count"])
        print("page_fetch_errors =",report["page_fetch_error_count"])
        print("exact_time_matches =",report["exact_time_match_count"])
        print("automatic_close_explicit =",report["automatic_close_explicit_count"])
        print("basis_counts =",json.dumps(report["closing_price_basis_counts"],sort_keys=True))
        print("window_minute_counts =",json.dumps(report["closing_price_window_minute_counts"],sort_keys=True))
        print("funding_mentioned =",report["funding_mentioned_count"])
        print("revision_wording =",report["revision_wording_count"])
        print("unresolved =",len(report["unresolved_symbols"]))
        print("price/basis/returns/PnL = CLOSED")
        print("report =",OUT)
        return 0 if report["status"]==PASS else 2
    except Exception as exc:
        OUT_DIR.mkdir(parents=True,exist_ok=True)
        err={
            "schema":"sc001.b15p2_announcement_body_semantic_audit_result.v0.1",
            "date":"2026-09-27",
            "status":REVIEW,
            "error_type":type(exc).__name__,
            "error_message":str(exc),
            "firewalls":{
                "price_accessed":False,
                "basis_calculated":False,
                "returns_calculated":False,
                "pnl_calculated":False,
                "event_ranked_by_outcome":False,
            },
            "next_state":"REVIEW_SEMANTIC_SOURCE_INTEGRITY_WITHOUT_OPENING_PRICES",
        }
        tmp=OUT.with_name(OUT.name+".tmp")
        tmp.write_text(json.dumps(err,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        os.replace(tmp,OUT)
        print(REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        print("price/basis/returns/PnL = CLOSED")
        print("report =",OUT)
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
