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
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

EXPECTED_SOURCE_SHA="c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c"
EXPECTED_EVENT_SET_SHA="1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2"
ALLOWED_HOST="announcements.bybit.com"

REPO=Path("/var/lib/botmarket-github-control/repo")
SOURCE_REL=Path("docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json")
FREEZE_REL=Path("docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json")
OUT_DIR=Path("/home/botmarket/sc001_data/SC001_B15P2_ANNOUNCEMENT_STRUCTURE_PROBE")

CURL_CONNECT_TIMEOUT=5
CURL_TOTAL_TIMEOUT=15
MAX_REDIRECT_HOPS=3
MAX_HTML=2_000_000
BROWSER_UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/126.0 Mobile Safari/537.36"

SKIP_TAGS=frozenset({"head","script","style","noscript","svg"})
TERMINATORS=(
    "If you have any questions",
    "Thank you for your continued support",
    "The Bybit Team",
)

def sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def normalize_space(text:str)->str:
    return re.sub(r"\s+"," ",html.unescape(text)).strip()

def require(cond:bool, code:str)->None:
    if not cond:
        raise RuntimeError(code)

def allowed_url(url:str)->bool:
    p=urllib.parse.urlparse(url)
    return p.scheme=="https" and p.hostname==ALLOWED_HOST

class StructuralHTMLParser(HTMLParser):
    def __init__(self)->None:
        super().__init__(convert_charrefs=True)
        self.skip=0
        self.visible_parts:list[str]=[]
        self.in_script=False
        self.current_script_attrs:dict[str,str]={}
        self.current_script_parts:list[str]=[]
        self.scripts:list[dict[str,Any]]=[]

    def handle_starttag(self,tag:str,attrs:list[tuple[str,str|None]])->None:
        lower=tag.lower()
        if lower=="script":
            self.in_script=True
            self.current_script_attrs={k.lower():(v or "") for k,v in attrs}
            self.current_script_parts=[]
        if lower in SKIP_TAGS:
            self.skip+=1

    def handle_endtag(self,tag:str)->None:
        lower=tag.lower()
        if lower=="script" and self.in_script:
            data="".join(self.current_script_parts)
            self.scripts.append({
                "attrs":dict(self.current_script_attrs),
                "data":data,
            })
            self.in_script=False
            self.current_script_attrs={}
            self.current_script_parts=[]
        if lower in SKIP_TAGS and self.skip:
            self.skip-=1

    def handle_data(self,data:str)->None:
        if self.in_script:
            self.current_script_parts.append(data)
        if not self.skip and data.strip():
            self.visible_parts.append(data)

def parse_html(raw:bytes)->tuple[str,list[dict[str,Any]],str]:
    decoded=raw.decode("utf-8",errors="strict")
    p=StructuralHTMLParser()
    p.feed(decoded)
    visible=normalize_space(" ".join(p.visible_parts))
    return visible,p.scripts,decoded

def visible_region_diagnostics(visible:str,symbol:str)->dict[str,Any]:
    title=f"Delisting of {symbol} Perpetual Contract"
    lower=visible.lower()
    start=lower.find(title.lower())
    count=lower.count(title.lower())
    out={
        "visible_text_length":len(visible),
        "exact_title_present":start>=0,
        "exact_title_count":count,
        "exact_title_position":start,
        "pre_cut_region_length":None,
        "post_cut_region_length":None,
        "terminator_positions":{},
    }
    if start<0:
        out["structural_pattern"]="VISIBLE_TITLE_ABSENT"
        return out

    region=visible[start:start+20_000]
    out["pre_cut_region_length"]=len(normalize_space(region))
    cut=None
    rlower=region.lower()
    for marker in TERMINATORS:
        pos=rlower.find(marker.lower())
        out["terminator_positions"][marker]=pos
        if pos>=0:
            end=pos+len(marker)
            cut=end if cut is None else min(cut,end)
    post=normalize_space(region[:cut] if cut is not None else region)
    out["post_cut_region_length"]=len(post)
    if len(post)>=120:
        out["structural_pattern"]="VISIBLE_REGION_SUFFICIENT"
    elif out["pre_cut_region_length"] is not None and out["pre_cut_region_length"]>=120 and cut is not None:
        out["structural_pattern"]="EARLY_TERMINATOR_COLLISION"
    else:
        out["structural_pattern"]="VISIBLE_DOM_BODY_INSUFFICIENT"
    return out

def walk_json(value:Any,path:str="$")->Iterable[tuple[str,Any]]:
    yield path,value
    if isinstance(value,dict):
        for k,v in value.items():
            yield from walk_json(v,f"{path}.{k}")
    elif isinstance(value,list):
        for i,v in enumerate(value):
            yield from walk_json(v,f"{path}[{i}]")

def script_structure(scripts:list[dict[str,Any]],symbol:str)->dict[str,Any]:
    title=f"Delisting of {symbol} Perpetual Contract"
    title_lower=title.lower()
    total_chars=sum(len(s["data"]) for s in scripts)
    scripts_with_title=[]
    json_scripts=0
    valid_json_scripts=0
    jsonld_scripts=0
    articlebody_candidates=[]
    title_string_candidates=[]

    for idx,s in enumerate(scripts):
        data=s["data"]
        attrs=s["attrs"]
        typ=(attrs.get("type") or "").lower()
        sid=attrs.get("id") or ""
        if title_lower in data.lower():
            scripts_with_title.append({
                "script_index":idx,
                "script_type":typ or None,
                "script_id":sid or None,
                "script_length":len(data),
                "script_sha256":hashlib.sha256(data.encode("utf-8")).hexdigest(),
            })

        is_json=("json" in typ) or sid=="__NEXT_DATA__"
        if is_json:
            json_scripts+=1
            try:
                obj=json.loads(data)
                valid_json_scripts+=1
            except Exception:
                continue
            if "ld+json" in typ:
                jsonld_scripts+=1
            for path,value in walk_json(obj):
                if not isinstance(value,str):
                    continue
                normalized=normalize_space(value)
                low=normalized.lower()
                if path.lower().endswith(".articlebody") and len(normalized)>=120:
                    articlebody_candidates.append({
                        "path":path,
                        "length":len(normalized),
                        "sha256":hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                        "contains_exact_title":title_lower in low,
                    })
                if title_lower in low and len(normalized)>=120:
                    title_string_candidates.append({
                        "path":path,
                        "length":len(normalized),
                        "sha256":hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                    })

    return {
        "script_count":len(scripts),
        "script_total_chars":total_chars,
        "scripts_with_exact_title_count":len(scripts_with_title),
        "scripts_with_exact_title":scripts_with_title[:10],
        "json_script_count":json_scripts,
        "valid_json_script_count":valid_json_scripts,
        "jsonld_script_count":jsonld_scripts,
        "articlebody_candidate_count":len(articlebody_candidates),
        "articlebody_candidates":articlebody_candidates[:10],
        "json_string_with_title_candidate_count":len(title_string_candidates),
        "json_string_with_title_candidates":title_string_candidates[:10],
    }

def raw_markers(decoded:str,symbol:str)->dict[str,Any]:
    title=f"Delisting of {symbol} Perpetual Contract"
    low=decoded.lower()
    return {
        "raw_exact_title_count":low.count(title.lower()),
        "has_next_data_marker":"__NEXT_DATA__" in decoded,
        "has_next_f_marker":"self.__next_f.push" in decoded,
        "has_articlebody_literal":"articleBody" in decoded,
        "has_application_ld_json":"application/ld+json" in low,
        "has_next_static_marker":"/_next/static/" in decoded,
    }

def derive_pattern(visible:dict[str,Any],scripts:dict[str,Any],raw:dict[str,Any])->str:
    if visible.get("structural_pattern")=="VISIBLE_REGION_SUFFICIENT":
        return "VISIBLE_REGION_SUFFICIENT"
    if visible.get("structural_pattern")=="EARLY_TERMINATOR_COLLISION":
        return "VISIBLE_REGION_EARLY_TERMINATOR_COLLISION"
    if scripts.get("articlebody_candidate_count",0)>0:
        return "JSONLD_OR_JSON_ARTICLEBODY_CANDIDATE"
    if scripts.get("json_string_with_title_candidate_count",0)>0:
        return "JSON_HYDRATION_TITLE_BODY_CANDIDATE"
    if scripts.get("scripts_with_exact_title_count",0)>0 and (raw.get("has_next_data_marker") or raw.get("has_next_f_marker")):
        return "NEXT_HYDRATION_SCRIPT_CONTAINS_TITLE"
    if raw.get("raw_exact_title_count",0)>0:
        return "RAW_HTML_HAS_TITLE_BUT_VISIBLE_BODY_INSUFFICIENT"
    return "ARTICLE_STRUCTURE_UNRESOLVED"

def build_curl_command(curl_bin:str,url:str,body_path:Path)->list[str]:
    require(allowed_url(url),"URL_POLICY")
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

def curl_one_hop(curl_bin:str,url:str)->tuple[bytes,dict[str,Any]]:
    fd,tmp_name=tempfile.mkstemp(prefix="b15p2_structure_",suffix=".html")
    os.close(fd)
    body_path=Path(tmp_name)
    try:
        cmd=build_curl_command(curl_bin,url,body_path)
        env={"PATH":os.environ.get("PATH","/usr/bin:/bin"),"LANG":"C","LC_ALL":"C"}
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=CURL_TOTAL_TIMEOUT+5,check=False,env=env)
        metrics=json.loads(cp.stdout) if cp.stdout.strip() else {}
        body=body_path.read_bytes() if body_path.exists() else b""
        return body,{
            "curl_exit_code":cp.returncode,
            "stderr":cp.stderr.strip() or None,
            "metrics":metrics,
        }
    finally:
        try:
            body_path.unlink()
        except FileNotFoundError:
            pass

def fetch_page(url:str)->tuple[bytes,str,dict[str,Any]]:
    curl_bin=shutil.which("curl")
    require(curl_bin is not None,"CURL_NOT_AVAILABLE")
    current=url
    seen=set()
    hops=[]
    for _ in range(MAX_REDIRECT_HOPS+1):
        require(current not in seen,"REDIRECT_LOOP")
        seen.add(current)
        require(allowed_url(current),"REDIRECT_HOST")
        body,hop=curl_one_hop(curl_bin,current)
        hops.append({
            "url":current,
            "curl_exit_code":hop["curl_exit_code"],
            "stderr":hop["stderr"],
            "metrics":hop["metrics"],
        })
        require(hop["curl_exit_code"]==0,f"CURL_ERROR:{hop['curl_exit_code']}:{hop['stderr']}")
        code=str(hop["metrics"].get("http_code") or "")
        redirect=str(hop["metrics"].get("redirect_url") or "").strip()
        if code.startswith("3") and redirect:
            nxt=urllib.parse.urljoin(current,redirect)
            require(allowed_url(nxt),"REDIRECT_HOST")
            current=nxt
            continue
        require(code.startswith("2"),f"HTTP_STATUS:{code}")
        require(0<len(body)<=MAX_HTML,"HTML_SIZE_OR_EMPTY")
        ctype=str(hop["metrics"].get("content_type") or "").lower()
        require("text/html" in ctype or "application/xhtml+xml" in ctype,f"CONTENT_TYPE:{ctype}")
        return body,current,{"hops":hops}
    raise RuntimeError("REDIRECT_HOP_CAP")

def load_frozen_events()->list[dict[str,Any]]:
    source_path=REPO/SOURCE_REL
    freeze_path=REPO/FREEZE_REL
    require(source_path.is_file(),"SOURCE_RESULT_MISSING")
    require(freeze_path.is_file(),"EVENT_FREEZE_MISSING")
    raw=source_path.read_bytes()
    require(sha256_bytes(raw)==EXPECTED_SOURCE_SHA,"SOURCE_RESULT_SHA")
    source=json.loads(raw.decode("utf-8"))
    freeze=json.loads(freeze_path.read_text(encoding="utf-8"))
    require(source.get("status")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS","SOURCE_STATUS")
    require(source.get("admitted_event_count")==94,"SOURCE_EVENT_COUNT")
    require(freeze.get("status")=="B15P2_EXACT_ADMITTED_EVENT_SET_FROZEN","FREEZE_STATUS")
    require(freeze.get("event_set_sha256")==EXPECTED_EVENT_SET_SHA,"EVENT_SET_SHA")
    return source["events"]

def selftest()->int:
    try:
        body=("Bybit will be delisting the TESTUSDT Perpetual Contract at Jul 25, 2026, 9:00AM UTC. "
              "X"*180)
        html1=f"<html><body><h1>Delisting of TESTUSDT Perpetual Contract</h1><p>{body}</p></body></html>".encode()
        vis,scripts,decoded=parse_html(html1)
        vd=visible_region_diagnostics(vis,"TESTUSDT")
        sd=script_structure(scripts,"TESTUSDT")
        rd=raw_markers(decoded,"TESTUSDT")
        require(derive_pattern(vd,sd,rd)=="VISIBLE_REGION_SUFFICIENT","VISIBLE_FIXTURE")

        article=("Delisting of TESTUSDT Perpetual Contract "+"Y"*180)
        ld=json.dumps({"@type":"Article","headline":"Delisting of TESTUSDT Perpetual Contract","articleBody":article})
        html2=f'<html><body><h1>Delisting of TESTUSDT Perpetual Contract</h1><script type="application/ld+json">{ld}</script></body></html>'.encode()
        vis2,scripts2,decoded2=parse_html(html2)
        vd2=visible_region_diagnostics(vis2,"TESTUSDT")
        sd2=script_structure(scripts2,"TESTUSDT")
        rd2=raw_markers(decoded2,"TESTUSDT")
        require(derive_pattern(vd2,sd2,rd2)=="JSONLD_OR_JSON_ARTICLEBODY_CANDIDATE","JSONLD_FIXTURE")

        next_script='self.__next_f.push(["Delisting of TESTUSDT Perpetual Contract","'+"Z"*180+'"])'
        html3=f"<html><body><h1>Delisting of TESTUSDT Perpetual Contract</h1><script>{next_script}</script></body></html>".encode()
        vis3,scripts3,decoded3=parse_html(html3)
        vd3=visible_region_diagnostics(vis3,"TESTUSDT")
        sd3=script_structure(scripts3,"TESTUSDT")
        rd3=raw_markers(decoded3,"TESTUSDT")
        require(derive_pattern(vd3,sd3,rd3)=="NEXT_HYDRATION_SCRIPT_CONTAINS_TITLE","NEXT_FIXTURE")

        print("B15P2_ANNOUNCEMENT_ARTICLE_STRUCTURE_PROBE_V01_SELF_TEST_PASS")
        return 0
    except Exception as exc:
        print("B15P2_ANNOUNCEMENT_ARTICLE_STRUCTURE_PROBE_V01_SELF_TEST_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def write_report(path:Path,obj:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def live()->int:
    started=time.time()
    run_id=f"{int(started)}_p{os.getpid()}"
    out=OUT_DIR/f"announcement_article_structure_probe_v0_1_{run_id}.json"
    rows=[]
    try:
        events=load_frozen_events()
        selected=[]
        for symbol in ("DOGUSDT","TONUSDT"):
            matches=[e for e in events if e.get("symbol")==symbol]
            require(len(matches)==1,f"EVENT_IDENTITY:{symbol}")
            selected.append(matches[0])

        for e in selected:
            symbol=e["symbol"]
            url=e["announcement_urls"][0]
            raw,final,transport=fetch_page(url)
            visible,scripts,decoded=parse_html(raw)
            vd=visible_region_diagnostics(visible,symbol)
            sd=script_structure(scripts,symbol)
            rd=raw_markers(decoded,symbol)
            rows.append({
                "symbol":symbol,
                "requested_url":url,
                "final_url":final,
                "raw_html_bytes":len(raw),
                "raw_html_sha256":sha256_bytes(raw),
                "transport":transport,
                "visible":vd,
                "scripts":sd,
                "raw_markers":rd,
                "derived_structure_pattern":derive_pattern(vd,sd,rd),
            })

        report={
            "schema":"sc001.b15p2_announcement_article_structure_probe.v0.1",
            "date":"2026-09-28",
            "status":"B15P2_ANNOUNCEMENT_ARTICLE_STRUCTURE_PROBE_COMPLETE",
            "events":rows,
            "semantic_classification_performed":False,
            "article_body_text_persisted":False,
            "price_accessed":False,
            "external_reference_price_accessed":False,
            "index_value_accessed":False,
            "basis_accessed":False,
            "returns_accessed":False,
            "pnl_accessed":False,
            "elapsed_seconds":round(time.time()-started,3),
        }
        write_report(out,report)

        print("B15P2_ANNOUNCEMENT_ARTICLE_STRUCTURE_PROBE_COMPLETE")
        for row in rows:
            v=row["visible"]
            s=row["scripts"]
            rm=row["raw_markers"]
            print(
                row["symbol"],
                "pattern="+row["derived_structure_pattern"],
                "raw_bytes="+str(row["raw_html_bytes"]),
                "visible_len="+str(v.get("visible_text_length")),
                "title_pos="+str(v.get("exact_title_position")),
                "pre_cut_len="+str(v.get("pre_cut_region_length")),
                "post_cut_len="+str(v.get("post_cut_region_length")),
                "scripts="+str(s.get("script_count")),
                "scripts_with_title="+str(s.get("scripts_with_exact_title_count")),
                "jsonld="+str(s.get("jsonld_script_count")),
                "articlebody_candidates="+str(s.get("articlebody_candidate_count")),
                "json_title_candidates="+str(s.get("json_string_with_title_candidate_count")),
                "next_data="+str(rm.get("has_next_data_marker")),
                "next_f="+str(rm.get("has_next_f_marker")),
            )
        print("semantic_classification_performed=False")
        print("article_body_text_persisted=False")
        print("price/index-values/basis/returns/PnL=CLOSED")
        print("report =",out)
        return 0
    except Exception as exc:
        review={
            "schema":"sc001.b15p2_announcement_article_structure_probe.v0.1",
            "date":"2026-09-28",
            "status":"B15P2_ANNOUNCEMENT_ARTICLE_STRUCTURE_PROBE_REVIEW",
            "events":rows,
            "error_type":type(exc).__name__,
            "error_message":str(exc),
            "semantic_classification_performed":False,
            "article_body_text_persisted":False,
            "price_accessed":False,
            "external_reference_price_accessed":False,
            "index_value_accessed":False,
            "basis_accessed":False,
            "returns_accessed":False,
            "pnl_accessed":False,
            "elapsed_seconds":round(time.time()-started,3),
        }
        try:
            write_report(out,review)
        except Exception:
            pass
        print("B15P2_ANNOUNCEMENT_ARTICLE_STRUCTURE_PROBE_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        print("semantic_classification_performed=False")
        print("price/index-values/basis/returns/PnL=CLOSED")
        print("report =",out)
        return 2

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","live"),required=True)
    a=ap.parse_args()
    return selftest() if a.mode=="self-test" else live()

if __name__=="__main__":
    raise SystemExit(main())
