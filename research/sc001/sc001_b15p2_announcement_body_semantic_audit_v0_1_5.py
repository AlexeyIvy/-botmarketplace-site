#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.parse
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_PASS"
REVIEW="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_REVIEW"
SELFTEST_PASS="B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V015_SELF_TEST_PASS"

EXPECTED_SOURCE_SHA="c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c"
EXPECTED_EVENT_SET_SHA="1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2"
ALLOWED_HOST="announcements.bybit.com"
CURL_CONNECT_TIMEOUT=5
CURL_TOTAL_TIMEOUT=15
CURL_ATTEMPTS=2
MAX_REDIRECT_HOPS=3
MAX_HTML=2_000_000
REQUEST_SLEEP=0.25
BROWSER_UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/126.0 Mobile Safari/537.36"

DEFAULT_REPO=Path(os.environ.get("B15P2_REPO_ROOT","/var/lib/botmarket-github-control/repo"))
SOURCE_REL=Path("docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json")
FREEZE_REL=Path("docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json")
DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_B15P2_ANNOUNCEMENT_SEMANTIC_AUDIT"
OUT=OUT_DIR/"sc001_b15p2_announcement_body_semantic_audit_v0_1_5.json"
SMOKE_OUT=OUT_DIR/"sc001_b15p2_announcement_body_hydration_smoke_v0_1_5.json"

MONTH_FORMATS=("%b %d, %Y, %I:%M%p UTC","%B %d, %Y, %I:%M%p UTC")

SKIP_TAGS=frozenset({"head","script","style","noscript","svg"})
HYDRATION_TITLE_PATH=("props","pageProps","articleDetail","title")
HYDRATION_PRIMARY_BODY_PATH=("props","pageProps","articleDetail","content","json","children")
HYDRATION_SECONDARY_BODY_PATH=("props","pageProps","articleDetail","entry","entryKey","children")
HYDRATION_PRIMARY_PATH_TEXT="$.props.pageProps.articleDetail.content.json.children"
HYDRATION_SECONDARY_PATH_TEXT="$.props.pageProps.articleDetail.entry.entryKey.children"
HYDRATION_TITLE_PATH_TEXT="$.props.pageProps.articleDetail.title"
MIN_HYDRATION_BODY_CHARS=120

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

class ScriptJSONParser(HTMLParser):
    def __init__(self)->None:
        super().__init__(convert_charrefs=True)
        self.in_script=False
        self.attrs:dict[str,str]={}
        self.parts:list[str]=[]
        self.scripts:list[dict[str,Any]]=[]

    def handle_starttag(self,tag:str,attrs:list[tuple[str,str|None]])->None:
        if tag.lower()=="script":
            self.in_script=True
            self.attrs={k.lower():(v or "") for k,v in attrs}
            self.parts=[]

    def handle_endtag(self,tag:str)->None:
        if tag.lower()=="script" and self.in_script:
            self.scripts.append({"attrs":dict(self.attrs),"data":"".join(self.parts)})
            self.in_script=False
            self.attrs={}
            self.parts=[]

    def handle_data(self,data:str)->None:
        if self.in_script:
            self.parts.append(data)

def get_nested(obj:Any,path:tuple[str,...])->tuple[bool,Any]:
    current=obj
    for key in path:
        if not isinstance(current,dict) or key not in current:
            return False,None
        current=current[key]
    return True,current

def flatten_rich_text(node:Any)->tuple[str,int]:
    leaves:list[str]=[]

    def rec(value:Any)->None:
        if isinstance(value,list):
            for item in value:
                rec(item)
            return
        if not isinstance(value,dict):
            return

        text_value=value.get("text")
        if isinstance(text_value,str) and text_value.strip():
            leaves.append(text_value)

        children=value.get("children")
        if isinstance(children,list):
            rec(children)

    rec(node)
    normalized=normalize_space(" ".join(leaves))
    return normalized,len(leaves)

def parse_exact_next_data(raw:bytes)->dict[str,Any]:
    decoded=raw.decode("utf-8",errors="strict")
    parser=ScriptJSONParser()
    parser.feed(decoded)
    matches=[s for s in parser.scripts if (s.get("attrs") or {}).get("id")=="__NEXT_DATA__"]
    require(len(matches)==1,f"NEXT_DATA_SCRIPT_COUNT:{len(matches)}")
    attrs=matches[0].get("attrs") or {}
    script_type=(attrs.get("type") or "").lower()
    require("json" in script_type,"NEXT_DATA_TYPE")
    try:
        obj=json.loads(matches[0].get("data") or "")
    except Exception as exc:
        raise RuntimeError(f"NEXT_DATA_JSON:{type(exc).__name__}:{exc}") from exc
    require(isinstance(obj,dict),"NEXT_DATA_OBJECT")
    return obj

def extract_hydration_article(raw:bytes,symbol:str)->tuple[str,dict[str,Any]]:
    obj=parse_exact_next_data(raw)
    expected_title=f"Delisting of {symbol} Perpetual Contract"

    title_ok,title_value=get_nested(obj,HYDRATION_TITLE_PATH)
    require(title_ok and isinstance(title_value,str),"HYDRATION_TITLE_MISSING")
    title=normalize_space(title_value)
    require(title.lower()==expected_title.lower(),"HYDRATION_TITLE_MISMATCH")

    primary_ok,primary=get_nested(obj,HYDRATION_PRIMARY_BODY_PATH)
    require(primary_ok and isinstance(primary,list) and len(primary)>0,"HYDRATION_PRIMARY_BODY_PATH")
    body,leaf_count=flatten_rich_text(primary)
    require(leaf_count>0,"HYDRATION_PRIMARY_NO_TEXT_LEAVES")
    require(len(body)>=MIN_HYDRATION_BODY_CHARS,"HYDRATION_PRIMARY_BODY_TOO_SHORT")
    body_sha=hashlib.sha256(body.encode("utf-8")).hexdigest()

    secondary_ok,secondary=get_nested(obj,HYDRATION_SECONDARY_BODY_PATH)
    secondary_present=secondary_ok
    secondary_match=None
    secondary_leaf_count=None
    secondary_sha=None
    if secondary_ok:
        require(isinstance(secondary,list) and len(secondary)>0,"HYDRATION_SECONDARY_BODY_TYPE")
        secondary_body,secondary_leaf_count=flatten_rich_text(secondary)
        require(secondary_leaf_count>0,"HYDRATION_SECONDARY_NO_TEXT_LEAVES")
        secondary_sha=hashlib.sha256(secondary_body.encode("utf-8")).hexdigest()
        secondary_match=(secondary_body==body)
        require(secondary_match,"HYDRATION_SECONDARY_MISMATCH")

    region=normalize_space(title+" "+body)
    require(len(region)>=MIN_HYDRATION_BODY_CHARS,"HYDRATION_ARTICLE_REGION_TOO_SHORT")

    return region,{
        "title_path":HYDRATION_TITLE_PATH_TEXT,
        "primary_body_path":HYDRATION_PRIMARY_PATH_TEXT,
        "secondary_consistency_path":HYDRATION_SECONDARY_PATH_TEXT,
        "title_sha256":hashlib.sha256(title.encode("utf-8")).hexdigest(),
        "primary_body_sha256":body_sha,
        "primary_body_length":len(body),
        "primary_text_leaf_count":leaf_count,
        "secondary_present":secondary_present,
        "secondary_match":secondary_match,
        "secondary_body_sha256":secondary_sha,
        "secondary_text_leaf_count":secondary_leaf_count,
        "article_region_sha256":hashlib.sha256(region.encode("utf-8")).hexdigest(),
        "article_region_length":len(region),
    }

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

def allowed_page_url(url:str)->bool:
    p=urllib.parse.urlparse(url)
    return p.scheme=="https" and p.hostname==ALLOWED_HOST

def parse_curl_metrics(raw:str)->dict[str,Any]:
    obj=json.loads(raw)
    require(isinstance(obj,dict),"CURL_METRICS_NOT_OBJECT")
    return obj

def build_curl_command(curl_bin:str,url:str,body_path:Path)->list[str]:
    require(allowed_page_url(url),"URL_POLICY")
    cmd=[
        curl_bin,
        "-4",
        "--http1.1",
        "-sS",
        "--noproxy","*",
        "--proto","=https",
        "--connect-timeout",str(CURL_CONNECT_TIMEOUT),
        "--max-time",str(CURL_TOTAL_TIMEOUT),
        "--max-filesize",str(MAX_HTML),
        "--max-redirs","0",
        "-A",BROWSER_UA,
        "-H","Accept: text/html,application/xhtml+xml",
        "-o",str(body_path),
        "-w",
        json.dumps({
            "http_code":"%{http_code}",
            "remote_ip":"%{remote_ip}",
            "http_version":"%{http_version}",
            "content_type":"%{content_type}",
            "size_download":"%{size_download}",
            "time_starttransfer":"%{time_starttransfer}",
            "time_total":"%{time_total}",
            "url_effective":"%{url_effective}",
            "redirect_url":"%{redirect_url}",
        },separators=(",",":")),
        "--url",url,
    ]
    require(cmd[-2:]==["--url",url],"CURL_URL_PAIR")
    require(cmd.count(url)==1,"CURL_URL_COUNT")
    return cmd

def curl_one_hop(curl_bin:str,url:str)->dict[str,Any]:
    require(allowed_page_url(url),"URL_POLICY")
    fd,tmp_name=tempfile.mkstemp(prefix="b15p2_semantic_",suffix=".html")
    os.close(fd)
    body_path=Path(tmp_name)
    try:
        cmd=build_curl_command(curl_bin,url,body_path)
        env={"PATH":os.environ.get("PATH","/usr/bin:/bin"),"LANG":"C","LC_ALL":"C"}
        t0=time.monotonic()
        cp=subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CURL_TOTAL_TIMEOUT+5,
            check=False,
            env=env,
        )
        elapsed=round(time.monotonic()-t0,3)
        metrics={}
        if cp.stdout.strip():
            try:
                metrics=parse_curl_metrics(cp.stdout.strip())
            except Exception as exc:
                metrics={"metrics_parse_error":f"{type(exc).__name__}: {exc}","metrics_raw":cp.stdout}
        body=body_path.read_bytes() if body_path.exists() else b""
        return {
            "curl_exit_code":cp.returncode,
            "stderr":cp.stderr.strip() or None,
            "elapsed_seconds":elapsed,
            "metrics":metrics,
            "body":body,
        }
    finally:
        try:
            body_path.unlink()
        except FileNotFoundError:
            pass

def curl_fetch_once(url:str)->tuple[bytes,str]:
    curl_bin=shutil.which("curl")
    require(curl_bin is not None,"CURL_NOT_AVAILABLE")
    current=url
    seen=set()
    for _hop in range(MAX_REDIRECT_HOPS+1):
        require(current not in seen,"REDIRECT_LOOP")
        seen.add(current)
        require(allowed_page_url(current),"REDIRECT_HOST")
        hop=curl_one_hop(curl_bin,current)
        metrics=hop["metrics"]
        rc=hop["curl_exit_code"]
        code=str(metrics.get("http_code") or "")
        if rc!=0:
            raise RuntimeError(
                f"CURL_ERROR:{rc}:"
                f"{hop.get('stderr') or metrics.get('metrics_parse_error') or 'unknown'}"
            )
        redirect=str(metrics.get("redirect_url") or "").strip()
        if code.startswith("3") and redirect:
            next_url=urllib.parse.urljoin(current,redirect)
            require(allowed_page_url(next_url),"REDIRECT_HOST")
            current=next_url
            continue
        require(code.startswith("2"),f"HTTP_STATUS:{code}")
        body=hop["body"]
        require(0<len(body)<=MAX_HTML,"HTML_SIZE_OR_EMPTY")
        content_type=str(metrics.get("content_type") or "").lower()
        require(
            "text/html" in content_type or "application/xhtml+xml" in content_type,
            f"CONTENT_TYPE:{content_type}",
        )
        return body,current
    raise RuntimeError("REDIRECT_HOP_CAP")

def fetch_page(url:str)->tuple[bytes,str]:
    require(allowed_page_url(url),"URL_POLICY")
    last=None
    for attempt in range(1,CURL_ATTEMPTS+1):
        try:
            return curl_fetch_once(url)
        except Exception as exc:
            last=exc
            if attempt<CURL_ATTEMPTS:
                print(
                    f"FETCH_RETRY attempt={attempt}/{CURL_ATTEMPTS} "
                    f"transport=curl_ipv4_http11 kind={type(exc).__name__} url={url}",
                    flush=True,
                )
                time.sleep(float(attempt))
                continue
            raise RuntimeError(f"CURL_FETCH_FAILED:{type(exc).__name__}:{exc}") from exc
    raise RuntimeError(f"CURL_FETCH_FAILED:{type(last).__name__}:{last}")

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
            region,hydration=extract_hydration_article(raw,symbol)
            sem=classify_text(region,symbol,e["delivery_ms"])
            sem.update({
                "requested_url":url,
                "final_url":final,
                "fetched_utc":utc_now(),
                "fetch_elapsed_seconds":round(time.monotonic()-t0,3),
                "raw_html_sha256":sha256_bytes(raw),
                "normalized_text_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "normalized_text_length":len(text),
                "body_source":"NEXT_DATA_HYDRATION",
                "hydration_title_path":hydration["title_path"],
                "hydration_primary_body_path":hydration["primary_body_path"],
                "hydration_secondary_consistency_path":hydration["secondary_consistency_path"],
                "hydration_primary_body_sha256":hydration["primary_body_sha256"],
                "hydration_primary_body_length":hydration["primary_body_length"],
                "hydration_primary_text_leaf_count":hydration["primary_text_leaf_count"],
                "hydration_secondary_present":hydration["secondary_present"],
                "hydration_secondary_match":hydration["secondary_match"],
                "hydration_secondary_body_sha256":hydration["secondary_body_sha256"],
                "hydration_secondary_text_leaf_count":hydration["secondary_text_leaf_count"],
                "article_region_sha256":hydration["article_region_sha256"],
                "article_region_length":hydration["article_region_length"],
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
        "date":"2026-09-28",
        "status":status,
        "frozen_event_set_sha256":EXPECTED_EVENT_SET_SHA,
        "event_count_expected":94,
        "acquisition_transport":{
            "client":"curl",
            "address_family":"IPv4",
            "http_version":"HTTP/1.1",
            "user_agent":"browser-like",
            "proxy":False,
            "same_host_redirects_only":True,
            "connect_timeout_seconds":CURL_CONNECT_TIMEOUT,
            "total_timeout_seconds":CURL_TOTAL_TIMEOUT,
            "attempts_per_url":CURL_ATTEMPTS,
        },
        "body_extraction":{
            "source":"__NEXT_DATA__",
            "exact_title_path":HYDRATION_TITLE_PATH_TEXT,
            "primary_body_path":HYDRATION_PRIMARY_PATH_TEXT,
            "secondary_consistency_path":HYDRATION_SECONDARY_PATH_TEXT,
            "minimum_normalized_body_chars":MIN_HYDRATION_BODY_CHARS,
            "adaptive_fallback_paths":False,
        },
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

def hydration_smoke()->int:
    rows=[]
    try:
        source,_=validate_frozen_input(DEFAULT_REPO)
        for symbol in ("DOGUSDT","TONUSDT"):
            matches=[e for e in source["events"] if e["symbol"]==symbol]
            require(len(matches)==1,f"SMOKE_EVENT_IDENTITY:{symbol}")
            e=matches[0]
            require(len(e["announcement_urls"])==1,f"SMOKE_URL_COUNT:{symbol}")
            url=e["announcement_urls"][0]
            raw,final=fetch_page(url)
            region,hydration=extract_hydration_article(raw,symbol)
            rows.append({
                "symbol":symbol,
                "requested_url":url,
                "final_url":final,
                "raw_html_sha256":sha256_bytes(raw),
                "raw_html_bytes":len(raw),
                "title_path":hydration["title_path"],
                "primary_body_path":hydration["primary_body_path"],
                "secondary_consistency_path":hydration["secondary_consistency_path"],
                "primary_body_sha256":hydration["primary_body_sha256"],
                "primary_body_length":hydration["primary_body_length"],
                "primary_text_leaf_count":hydration["primary_text_leaf_count"],
                "secondary_present":hydration["secondary_present"],
                "secondary_match":hydration["secondary_match"],
                "secondary_body_sha256":hydration["secondary_body_sha256"],
                "secondary_text_leaf_count":hydration["secondary_text_leaf_count"],
                "article_region_sha256":hydration["article_region_sha256"],
                "article_region_length":hydration["article_region_length"],
            })

        require(len(rows)==2,"SMOKE_EVENT_COUNT")
        require(all(r["primary_body_length"]>=MIN_HYDRATION_BODY_CHARS for r in rows),"SMOKE_BODY_LENGTH")
        require(all((r["secondary_match"] is not False) for r in rows),"SMOKE_SECONDARY_MISMATCH")

        OUT_DIR.mkdir(parents=True,exist_ok=True)
        report={
            "schema":"sc001.b15p2_announcement_body_hydration_smoke.v0.1.5",
            "date":"2026-09-28",
            "status":"B15P2_ANNOUNCEMENT_BODY_HYDRATION_SMOKE_V015_PASS",
            "transport":{
                "client":"curl",
                "address_family":"IPv4",
                "http_version":"HTTP/1.1",
                "user_agent":"browser-like",
                "proxy":False,
                "same_host_redirects_only":True,
            },
            "body_extraction":{
                "source":"__NEXT_DATA__",
                "exact_title_path":HYDRATION_TITLE_PATH_TEXT,
                "primary_body_path":HYDRATION_PRIMARY_PATH_TEXT,
                "secondary_consistency_path":HYDRATION_SECONDARY_PATH_TEXT,
                "adaptive_fallback_paths":False,
            },
            "events":rows,
            "article_body_text_persisted":False,
            "semantic_classification_performed":False,
            "price_accessed":False,
            "external_reference_price_accessed":False,
            "index_value_accessed":False,
            "basis_accessed":False,
            "returns_accessed":False,
            "pnl_accessed":False,
        }
        tmp=SMOKE_OUT.with_name(SMOKE_OUT.name+".tmp")
        tmp.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        os.replace(tmp,SMOKE_OUT)
        print("B15P2_ANNOUNCEMENT_BODY_HYDRATION_SMOKE_V015_PASS")
        for r in rows:
            print(
                r["symbol"],
                "body_len="+str(r["primary_body_length"]),
                "leaf_count="+str(r["primary_text_leaf_count"]),
                "secondary_present="+str(r["secondary_present"]),
                "secondary_match="+str(r["secondary_match"]),
            )
        print("article_body_text_persisted=False")
        print("semantic_classification_performed=False")
        print("price/basis/returns/PnL/index-values=CLOSED")
        print("report =",SMOKE_OUT)
        return 0
    except Exception as exc:
        OUT_DIR.mkdir(parents=True,exist_ok=True)
        review={
            "schema":"sc001.b15p2_announcement_body_hydration_smoke.v0.1.5",
            "date":"2026-09-28",
            "status":"B15P2_ANNOUNCEMENT_BODY_HYDRATION_SMOKE_V015_REVIEW",
            "events":rows,
            "error_type":type(exc).__name__,
            "error_message":str(exc),
            "article_body_text_persisted":False,
            "semantic_classification_performed":False,
            "price_accessed":False,
            "external_reference_price_accessed":False,
            "index_value_accessed":False,
            "basis_accessed":False,
            "returns_accessed":False,
            "pnl_accessed":False,
        }
        tmp=SMOKE_OUT.with_name(SMOKE_OUT.name+".tmp")
        tmp.write_text(json.dumps(review,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        os.replace(tmp,SMOKE_OUT)
        print("B15P2_ANNOUNCEMENT_BODY_HYDRATION_SMOKE_V015_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        print("article_body_text_persisted=False")
        print("semantic_classification_performed=False")
        print("price/basis/returns/PnL/index-values=CLOSED")
        print("report =",SMOKE_OUT)
        return 2

def synthetic_hydration_html(
    symbol:str,
    body_children:list[dict[str,Any]],
    *,
    include_secondary:bool=True,
    secondary_children:list[dict[str,Any]]|None=None,
    title_override:str|None=None,
    duplicate_next_data:bool=False,
)->bytes:
    title=title_override or f"Delisting of {symbol} Perpetual Contract"
    article={
        "title":title,
        "content":{"json":{"children":body_children},"html":""},
    }
    if include_secondary:
        article["entry"]={
            "entryKey":{
                "children":secondary_children if secondary_children is not None else body_children
            }
        }
    obj={"props":{"pageProps":{"articleDetail":article}}}
    script=json.dumps(obj,separators=(",",":"))
    extra=(
        f'<script id="__NEXT_DATA__" type="application/json">{script}</script>'
        if duplicate_next_data else ""
    )
    return (
        "<html><head><title>Funding Updated Products</title></head>"
        "<body><nav>Funding Updated Products</nav>"
        f'<script id="__NEXT_DATA__" type="application/json">{script}</script>{extra}'
        "<footer>Funding Updated Products</footer></body></html>"
    ).encode("utf-8")

def selftest()->int:
    stage="INIT"
    try:
        fixture_symbol="TESTUSDT"
        delivery=int(datetime(2026,7,25,9,0,tzinfo=timezone.utc).timestamp()*1000)
        body_children=[
            {"type":"p","children":[{"text":"Bybit will be delisting the TESTUSDT Perpetual Contract at Jul 25, 2026, 9:00AM UTC."}]},
            {"type":"p","children":[{"text":"The TESTUSDT Perpetual Contract will be delisted and trading will no longer be supported."}]},
            {"type":"p","children":[{"text":"All active orders and conditional orders for the TESTUSDT Perpetual Contract will be automatically canceled."}]},
            {"type":"p","children":[{"text":"Any open positions in the TESTUSDT Perpetual Contract will be automatically closed. The closing price will be based on the average index price in the 30 minutes prior to the delisting."}]},
        ]

        stage="HYDRATION_PRIMARY_SECONDARY"
        raw=synthetic_hydration_html(fixture_symbol,body_children)
        region,h=extract_hydration_article(raw,fixture_symbol)
        assert h["title_path"]==HYDRATION_TITLE_PATH_TEXT
        assert h["primary_body_path"]==HYDRATION_PRIMARY_PATH_TEXT
        assert h["primary_text_leaf_count"]==4
        assert h["primary_body_length"]>=MIN_HYDRATION_BODY_CHARS
        assert h["secondary_present"] is True
        assert h["secondary_match"] is True
        assert h["primary_body_sha256"]==h["secondary_body_sha256"]

        stage="HYDRATION_CLASSIFY"
        r=classify_text(region,fixture_symbol,delivery)
        assert r["title_symbol_match"] is True
        assert r["time_class"]=="TIME_MATCH"
        assert r["trading_stop"]=="TRADING_STOP_EXPLICIT"
        assert r["active_order_handling"]=="ACTIVE_ORDERS_AUTO_CANCEL_EXPLICIT"
        assert r["open_position_handling"]=="OPEN_POSITIONS_AUTO_CLOSE_EXPLICIT"
        assert r["closing_price_basis"]=="AVERAGE_INDEX_PRICE_WINDOW"
        assert r["closing_price_window_minutes"]==30
        assert r["funding_treatment"]=="FUNDING_NOT_STATED"
        assert r["revision_wording"]=="NO_REVISION_OR_POSTPONEMENT_WORDING"
        assert r["semantic_resolved"] is True

        stage="SECONDARY_OPTIONAL"
        raw_no_secondary=synthetic_hydration_html(fixture_symbol,body_children,include_secondary=False)
        region2,h2=extract_hydration_article(raw_no_secondary,fixture_symbol)
        assert h2["secondary_present"] is False
        assert h2["secondary_match"] is None
        assert classify_text(region2,fixture_symbol,delivery)["semantic_resolved"] is True

        stage="SECONDARY_MISMATCH"
        mismatch=[{"type":"p","children":[{"text":"Different CMS duplicate text that must fail closed."}]}]
        try:
            extract_hydration_article(
                synthetic_hydration_html(
                    fixture_symbol,body_children,include_secondary=True,secondary_children=mismatch,
                ),
                fixture_symbol,
            )
            raise AssertionError("secondary mismatch was not rejected")
        except RuntimeError as exc:
            assert "HYDRATION_SECONDARY_MISMATCH" in str(exc)

        stage="TITLE_MISMATCH"
        try:
            extract_hydration_article(
                synthetic_hydration_html(
                    fixture_symbol,body_children,
                    title_override="Delisting of OTHERUSDT Perpetual Contract",
                ),
                fixture_symbol,
            )
            raise AssertionError("title mismatch was not rejected")
        except RuntimeError as exc:
            assert "HYDRATION_TITLE_MISMATCH" in str(exc)

        stage="DUPLICATE_NEXT_DATA"
        try:
            extract_hydration_article(
                synthetic_hydration_html(
                    fixture_symbol,body_children,duplicate_next_data=True,
                ),
                fixture_symbol,
            )
            raise AssertionError("duplicate NEXT_DATA was not rejected")
        except RuntimeError as exc:
            assert "NEXT_DATA_SCRIPT_COUNT" in str(exc)

        stage="PRIMARY_TOO_SHORT"
        try:
            extract_hydration_article(
                synthetic_hydration_html(
                    fixture_symbol,
                    [{"type":"p","children":[{"text":"short"}]}],
                    include_secondary=False,
                ),
                fixture_symbol,
            )
            raise AssertionError("short body was not rejected")
        except RuntimeError as exc:
            assert "HYDRATION_PRIMARY_BODY_TOO_SHORT" in str(exc)

        stage="VISIBLE_CHROME_NOT_SEMANTIC_SOURCE"
        visible=visible_text(raw)
        assert "Funding Updated Products" in visible
        assert classify_text(region,fixture_symbol,delivery)["funding_treatment"]=="FUNDING_NOT_STATED"
        assert classify_text(region,fixture_symbol,delivery)["revision_wording"]=="NO_REVISION_OR_POSTPONEMENT_WORDING"

        stage="CURL_CONTRACT"
        fake_curl="/usr/bin/curl"
        fake_body=Path("/tmp/b15p2_semantic_selftest_body.html")
        cmd=build_curl_command(fake_curl,"https://announcements.bybit.com/en-US/article/test/",fake_body)
        assert cmd[-2:]==["--url","https://announcements.bybit.com/en-US/article/test/"]
        assert "-4" in cmd
        assert "--http1.1" in cmd
        assert "--noproxy" in cmd and "*" in cmd
        assert "--proto" in cmd and "=https" in cmd
        assert "--connect-timeout" in cmd and str(CURL_CONNECT_TIMEOUT) in cmd
        assert "--max-time" in cmd and str(CURL_TOTAL_TIMEOUT) in cmd
        assert "--max-filesize" in cmd and str(MAX_HTML) in cmd
        assert "-A" in cmd and BROWSER_UA in cmd
        assert "-o" in cmd and str(fake_body) in cmd
        assert not allowed_page_url("http://announcements.bybit.com/en-US/article/test/")
        assert not allowed_page_url("https://example.com/en-US/article/test/")

        print(SELFTEST_PASS)
        return 0
    except Exception as exc:
        print("B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V015_SELF_TEST_REVIEW")
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
            "date":"2026-09-28",
            "status":REVIEW,
            "error_type":type(exc).__name__,
            "error_message":str(exc),
            "firewalls":{
                "price_accessed":False,
                "external_reference_price_accessed":False,
                "index_values_accessed":False,
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
    ap.add_argument("--mode",choices=("self-test","hydration-smoke","live"),default="self-test")
    ap.add_argument("_runner_package_root",nargs="?")
    ap.add_argument("_runner_entrypoint",nargs="?")
    a=ap.parse_args()
    validate_launcher_args(a._runner_package_root,a._runner_entrypoint)
    if a.mode=="self-test":
        return selftest()
    if a.mode=="hydration-smoke":
        return hydration_smoke()
    return live()

if __name__=="__main__":
    raise SystemExit(main())
