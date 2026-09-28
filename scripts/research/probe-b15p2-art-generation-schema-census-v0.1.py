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

REPO=Path(os.environ.get("B15P2_REPO_ROOT","/var/lib/botmarket-github-control/repo"))
SOURCE_REL=Path("docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json")
FREEZE_REL=Path("docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json")
OUT_DIR=Path("/home/botmarket/sc001_data/SC001_B15P2_ART_GENERATION_SCHEMA_CENSUS")

CURL_CONNECT_TIMEOUT=5
CURL_TOTAL_TIMEOUT=15
CURL_ATTEMPTS=2
MAX_REDIRECT_HOPS=3
MAX_HTML=2_000_000
BROWSER_UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/126.0 Mobile Safari/537.36"

HTML_TAG_RE=re.compile(r"</?[A-Za-z][^>]*>")
STRUCTURAL_KEY_HINTS=frozenset({
    "article","body","content","description","detail","details","html","text","message",
    "announcement","data","payload","richtext","rich_text","document","post","page",
    "blocks","children","value","richcontent","rich_content"
})
MAX_ANCESTOR_LEVELS=5
MAX_FIELDS_PER_ANCESTOR=100
MAX_CANDIDATES=150
ART_URL_RE=re.compile(r"--art[0-9a-f]+/?$",re.I)
EXPECTED_ART_EVENT_COUNT=18

def sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def normalize_space(text:str)->str:
    return re.sub(r"\s+"," ",html.unescape(text)).strip()

def require(cond:bool,code:str)->None:
    if not cond:
        raise RuntimeError(code)

def allowed_url(url:str)->bool:
    p=urllib.parse.urlparse(url)
    return p.scheme=="https" and p.hostname==ALLOWED_HOST

def is_art_generation_url(url:str)->bool:
    if not allowed_url(url):
        return False
    p=urllib.parse.urlparse(url)
    return bool(ART_URL_RE.search(p.path))

def json_type(value:Any)->str:
    if value is None: return "null"
    if isinstance(value,bool): return "bool"
    if isinstance(value,str): return "string"
    if isinstance(value,(int,float)): return "number"
    if isinstance(value,list): return "list"
    if isinstance(value,dict): return "dict"
    return type(value).__name__

def path_leaf(path:str)->str:
    leaf=re.split(r"[.\[]",path)[-1].rstrip("]")
    return leaf.lower()

class ScriptParser(HTMLParser):
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

def parse_scripts(raw:bytes)->list[dict[str,Any]]:
    decoded=raw.decode("utf-8",errors="strict")
    p=ScriptParser()
    p.feed(decoded)
    return p.scripts

def iter_strings(value:Any,path:str="$")->Iterable[tuple[str,str]]:
    if isinstance(value,str):
        yield path,value
    elif isinstance(value,dict):
        for k,v in value.items():
            yield from iter_strings(v,f"{path}.{k}")
    elif isinstance(value,list):
        for i,v in enumerate(value):
            yield from iter_strings(v,f"{path}[{i}]")

def string_metrics(value:str,title:str)->dict[str,Any]:
    normalized=normalize_space(value)
    stripped=value.lstrip()
    parseable_json=False
    if stripped.startswith(("{","[")):
        try:
            json.loads(value)
            parseable_json=True
        except Exception:
            pass
    return {
        "raw_length":len(value),
        "normalized_length":len(normalized),
        "sha256":hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "html_tag_count":len(HTML_TAG_RE.findall(value)),
        "escaped_html_marker_count":value.count("&lt;"),
        "newline_count":value.count("\n"),
        "contains_exact_title":title.lower() in normalized.lower(),
        "parseable_json_string":parseable_json,
    }

def container_metrics(value:Any,title:str)->dict[str,Any]:
    string_count=0
    total_chars=0
    max_len=0
    max_path=None
    html_tags=0
    escaped_html=0
    title_matches=0
    parseable_json_strings=0
    for rel_path,text in iter_strings(value,"$"):
        m=string_metrics(text,title)
        string_count+=1
        total_chars+=m["normalized_length"]
        html_tags+=m["html_tag_count"]
        escaped_html+=m["escaped_html_marker_count"]
        title_matches+=1 if m["contains_exact_title"] else 0
        parseable_json_strings+=1 if m["parseable_json_string"] else 0
        if m["normalized_length"]>max_len:
            max_len=m["normalized_length"]
            max_path=rel_path
    child_count=len(value) if isinstance(value,(dict,list)) else None
    return {
        "child_count":child_count,
        "descendant_string_count":string_count,
        "descendant_total_normalized_chars":total_chars,
        "descendant_max_string_length":max_len,
        "descendant_max_string_path":max_path,
        "descendant_html_tag_count":html_tags,
        "descendant_escaped_html_marker_count":escaped_html,
        "descendant_title_match_count":title_matches,
        "descendant_parseable_json_string_count":parseable_json_strings,
    }

def field_metrics(key:str,value:Any,title:str)->dict[str,Any]:
    entry={"key":str(key),"type":json_type(value)}
    if isinstance(value,str):
        entry.update(string_metrics(value,title))
    elif isinstance(value,(dict,list)):
        entry.update(container_metrics(value,title))
    return entry

def summarize_container(path:str,value:Any,title:str)->dict[str,Any]:
    if isinstance(value,dict):
        fields=[field_metrics(str(k),v,title) for k,v in value.items()]
        fields=sorted(fields,key=lambda x:x["key"])[:MAX_FIELDS_PER_ANCESTOR]
        return {
            "path":path,
            "type":"dict",
            "field_count":len(value),
            "fields":fields,
        }
    if isinstance(value,list):
        return {
            "path":path,
            "type":"list",
            "item_count":len(value),
            "metrics":container_metrics(value,title),
        }
    return {"path":path,"type":json_type(value)}

def title_nodes_with_ancestors(value:Any,title:str)->list[dict[str,Any]]:
    out:list[dict[str,Any]]=[]
    title_lower=title.lower()

    def rec(node:Any,path:str,ancestors:list[tuple[str,Any]])->None:
        if isinstance(node,str):
            normalized=normalize_space(node)
            low=normalized.lower()
            if title_lower in low:
                out.append({
                    "path":path,
                    "length":len(normalized),
                    "sha256":hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                    "exact_string_match":low==title_lower,
                    "ancestors":[
                        summarize_container(p,v,title)
                        for p,v in ancestors[-MAX_ANCESTOR_LEVELS:]
                    ],
                })
            return
        if isinstance(node,dict):
            next_anc=ancestors+[(path,node)]
            for k,v in node.items():
                rec(v,f"{path}.{k}",next_anc)
        elif isinstance(node,list):
            next_anc=ancestors+[(path,node)]
            for i,v in enumerate(node):
                rec(v,f"{path}[{i}]",next_anc)

    rec(value,"$",[])
    return out

def candidate_score(path:str,value:Any,title:str)->tuple[int,dict[str,Any]]:
    leaf=path_leaf(path)
    exact_hint=leaf in STRUCTURAL_KEY_HINTS
    fuzzy_hint=any(h in leaf for h in STRUCTURAL_KEY_HINTS)
    score=5 if exact_hint else (3 if fuzzy_hint else 0)

    if isinstance(value,str):
        m=string_metrics(value,title)
        chars=m["normalized_length"]
        if chars>=120: score+=1
        if chars>=500: score+=1
        if m["html_tag_count"]>=1: score+=2
        if m["escaped_html_marker_count"]>=1: score+=1
        if m["parseable_json_string"]: score+=1
        return score,{
            "kind":"string",
            "chars":chars,
            **m,
        }

    if isinstance(value,(dict,list)):
        m=container_metrics(value,title)
        chars=m["descendant_total_normalized_chars"]
        if chars>=120: score+=1
        if chars>=500: score+=1
        if m["descendant_max_string_length"]>=120: score+=1
        if m["descendant_html_tag_count"]>=1: score+=2
        if m["descendant_parseable_json_string_count"]>=1: score+=1
        return score,{
            "kind":"container",
            "chars":chars,
            **m,
        }

    return score,{"kind":"scalar","chars":0}

def collect_candidates(value:Any,title:str)->list[dict[str,Any]]:
    out=[]

    def rec(node:Any,path:str)->None:
        if path!="$":
            score,metrics=candidate_score(path,node,title)
            chars=int(metrics.get("chars",0) or 0)
            html_tags=int(
                metrics.get("html_tag_count",0)
                if metrics.get("kind")=="string"
                else metrics.get("descendant_html_tag_count",0)
            )
            fallback_large=(
                (metrics.get("kind")=="string" and chars>=500)
                or (metrics.get("kind")=="container" and chars>=1000)
                or html_tags>=2
            )
            if chars>=120 and (score>=4 or fallback_large):
                out.append({
                    "path":path,
                    "score":score,
                    "fallback_large":fallback_large,
                    "type":json_type(node),
                    **metrics,
                })
        if isinstance(node,dict):
            for k,v in node.items():
                rec(v,f"{path}.{k}")
        elif isinstance(node,list):
            for i,v in enumerate(node):
                rec(v,f"{path}[{i}]")

    rec(value,"$")
    out.sort(key=lambda x:(-x["score"],-x.get("chars",0),x["path"]))
    return out[:MAX_CANDIDATES]

def script_role(index:int,attrs:dict[str,str],parseable_json:bool)->str:
    sid=(attrs.get("id") or "").strip()
    typ=(attrs.get("type") or "").strip().lower()
    if sid=="__NEXT_DATA__":
        return "__NEXT_DATA__"
    if "json" in typ:
        return f"JSON_TYPE:{typ}:INDEX:{index}"
    if parseable_json:
        return f"PARSEABLE_JSON_SCRIPT:INDEX:{index}"
    return f"SCRIPT_INDEX:{index}"

def inspect_json_document(obj:Any,title:str,role:str)->dict[str,Any]:
    containing=title_nodes_with_ancestors(obj,title)
    exact=[n for n in containing if n.get("exact_string_match") is True]
    nonexact=[n for n in containing if n.get("exact_string_match") is not True]
    candidates=collect_candidates(obj,title)
    return {
        "role":role,
        "exact_title_node_count":len(exact),
        "exact_title_nodes":exact[:20],
        "containing_title_node_count":len(containing),
        "nonexact_containing_title_nodes":nonexact[:20],
        "structural_candidate_count":len(candidates),
        "structural_candidates":candidates,
    }

def inspect_hydration_scripts(scripts:list[dict[str,Any]],symbol:str)->dict[str,Any]:
    title=f"Delisting of {symbol} Perpetual Contract"
    title_lower=title.lower()
    docs=[]
    scripts_with_raw_title=[]
    key_inventory=set()
    next_data_count=0

    for index,s in enumerate(scripts):
        attrs=s.get("attrs") or {}
        data=s.get("data") or ""
        sid=(attrs.get("id") or "").strip()
        typ=(attrs.get("type") or "").strip().lower()
        stripped=data.strip()

        if title_lower in data.lower():
            scripts_with_raw_title.append({
                "script_index":index,
                "script_id":sid or None,
                "script_type":typ or None,
                "script_length":len(data),
                "script_sha256":hashlib.sha256(data.encode("utf-8")).hexdigest(),
            })

        should_try_json=(
            sid=="__NEXT_DATA__"
            or "json" in typ
            or stripped.startswith(("{","["))
        )
        if not should_try_json:
            continue

        parse_error=None
        obj=None
        try:
            obj=json.loads(data)
        except Exception as exc:
            parse_error=f"{type(exc).__name__}: {exc}"

        role=script_role(index,attrs,obj is not None)
        if role=="__NEXT_DATA__":
            next_data_count+=1

        doc={
            "script_index":index,
            "script_id":sid or None,
            "script_type":typ or None,
            "role":role,
            "script_length":len(data),
            "script_sha256":hashlib.sha256(data.encode("utf-8")).hexdigest(),
            "parseable_json":obj is not None,
            "parse_error":parse_error,
        }
        if obj is not None:
            mapped=inspect_json_document(obj,title,role)
            doc.update(mapped)

            def collect_keys(node:Any)->None:
                if isinstance(node,dict):
                    for k,v in node.items():
                        key_inventory.add(str(k))
                        collect_keys(v)
                elif isinstance(node,list):
                    for v in node:
                        collect_keys(v)
            collect_keys(obj)

            doc["top_level_keys"]=sorted(obj.keys()) if isinstance(obj,dict) else []
            pageprops_keys=[]
            if isinstance(obj,dict) and isinstance(obj.get("props"),dict):
                pp=obj["props"].get("pageProps")
                if isinstance(pp,dict):
                    pageprops_keys=sorted(pp.keys())
            doc["pageprops_keys"]=pageprops_keys
        docs.append(doc)

    parseable=[d for d in docs if d.get("parseable_json")]
    title_docs=[d for d in parseable if int(d.get("exact_title_node_count") or 0)>0]
    next_title_docs=[d for d in title_docs if d.get("role")=="__NEXT_DATA__"]

    candidates=[]
    title_nodes=[]
    for d in title_docs:
        role=d["role"]
        for node in d.get("exact_title_nodes") or []:
            title_nodes.append({
                **node,
                "script_role":role,
                "script_index":d["script_index"],
                "identity":f"{role}::{node['path']}",
            })

    for d in parseable:
        role=d["role"]
        script_has_exact_title=int(d.get("exact_title_node_count") or 0)>0
        for c in d.get("structural_candidates") or []:
            candidates.append({
                **c,
                "script_role":role,
                "script_index":d["script_index"],
                "script_has_exact_title":script_has_exact_title,
                "identity":f"{role}::{c['path']}",
            })

    candidates.sort(key=lambda x:(-x["score"],-x.get("chars",0),x["identity"]))

    return {
        "script_count":len(scripts),
        "scripts_with_raw_exact_title_count":len(scripts_with_raw_title),
        "scripts_with_raw_exact_title":scripts_with_raw_title[:20],
        "json_candidate_script_count":len(docs),
        "parseable_json_script_count":len(parseable),
        "next_data_script_count":next_data_count,
        "parseable_title_script_count":len(title_docs),
        "next_data_contains_exact_title":len(next_title_docs)>0,
        "title_outside_next_data":len(title_docs)>0 and len(next_title_docs)==0,
        "key_inventory":sorted(key_inventory)[:500],
        "exact_title_node_count":len(title_nodes),
        "exact_title_nodes":title_nodes[:40],
        "structural_candidate_count":len(candidates),
        "structural_candidates":candidates[:MAX_CANDIDATES],
        "json_documents":[{
            "script_index":d.get("script_index"),
            "script_id":d.get("script_id"),
            "script_type":d.get("script_type"),
            "role":d.get("role"),
            "script_length":d.get("script_length"),
            "script_sha256":d.get("script_sha256"),
            "parseable_json":d.get("parseable_json"),
            "parse_error":d.get("parse_error"),
            "top_level_keys":d.get("top_level_keys"),
            "pageprops_keys":d.get("pageprops_keys"),
            "exact_title_node_count":d.get("exact_title_node_count"),
            "containing_title_node_count":d.get("containing_title_node_count"),
            "structural_candidate_count":d.get("structural_candidate_count"),
        } for d in docs[:20]],
    }

def json_path_depth(path:str)->int:
    return path.count(".")+path.count("[")

def derive_frequency_consensus(rows:list[dict[str,Any]])->dict[str,Any]:
    require(len(rows)==EXPECTED_ART_EVENT_COUNT,"CONSENSUS_EVENT_COUNT")
    symbols=sorted(r["symbol"] for r in rows)
    by_symbol={r["symbol"]:r["hydration"] for r in rows}

    title_freq:dict[str,list[str]]={}
    candidate_freq:dict[str,list[tuple[str,dict[str,Any]]]]={}

    for symbol in symbols:
        hydration=by_symbol[symbol]
        for node in hydration.get("exact_title_nodes") or []:
            identity=node["identity"]
            title_freq.setdefault(identity,[]).append(symbol)
        for cand in hydration.get("structural_candidates") or []:
            identity=cand["identity"]
            candidate_freq.setdefault(identity,[]).append((symbol,cand))

    title_identities=[]
    for identity,syms in title_freq.items():
        title_identities.append({
            "identity":identity,
            "event_count":len(syms),
            "coverage_fraction":round(len(syms)/len(symbols),6),
            "symbols":sorted(syms),
        })
    title_identities.sort(key=lambda x:(-x["event_count"],x["identity"]))

    candidates=[]
    for identity,items in candidate_freq.items():
        cs=[c for _,c in items]
        syms=[s for s,_ in items]
        first=cs[0]
        candidates.append({
            "identity":identity,
            "script_role":first.get("script_role"),
            "path":first.get("path"),
            "event_count":len(items),
            "coverage_fraction":round(len(items)/len(symbols),6),
            "symbols":sorted(syms),
            "types":sorted({str(c.get("type")) for c in cs}),
            "kinds":sorted({str(c.get("kind")) for c in cs}),
            "title_document_event_count":sum(1 for c in cs if c.get("script_has_exact_title") is True),
            "all_events_title_coupled":all(c.get("script_has_exact_title") is True for c in cs),
            "min_score":min(int(c.get("score") or 0) for c in cs),
            "max_score":max(int(c.get("score") or 0) for c in cs),
            "min_chars":min(int(c.get("chars") or 0) for c in cs),
            "max_chars":max(int(c.get("chars") or 0) for c in cs),
            "path_depth":json_path_depth(str(first.get("path") or "")),
        })

    candidates.sort(key=lambda x:(
        -x["event_count"],
        -x["title_document_event_count"],
        -x["min_score"],
        -x["path_depth"],
        -x["min_chars"],
        x["identity"],
    ))

    common=[
        c for c in candidates
        if c["event_count"]==len(symbols) and c["min_chars"]>=120
    ]
    common_high_conf=[
        c for c in common
        if c["min_score"]>=6
    ]

    return {
        "expected_event_count":EXPECTED_ART_EVENT_COUNT,
        "symbols":symbols,
        "exact_title_identity_count":len(title_identities),
        "exact_title_identities":title_identities[:50],
        "candidate_identity_count":len(candidates),
        "candidate_identity_frequency":candidates[:200],
        "common_candidate_count":len(common),
        "common_candidates":common[:100],
        "common_high_confidence_candidate_count":len(common_high_conf),
        "common_high_confidence_candidates":common_high_conf[:50],
    }

def build_curl_command(curl_bin:str,url:str,body_path:Path)->list[str]:
    require(allowed_url(url),"URL_POLICY")
    cmd=[
        curl_bin,"-4","--http1.1","-sS","--noproxy","*","--proto","=https",
        "--connect-timeout",str(CURL_CONNECT_TIMEOUT),"--max-time",str(CURL_TOTAL_TIMEOUT),
        "--max-filesize",str(MAX_HTML),"--max-redirs","0",
        "-A",BROWSER_UA,"-H","Accept: text/html,application/xhtml+xml",
        "-o",str(body_path),
        "-w",json.dumps({
            "http_code":"%{http_code}","content_type":"%{content_type}",
            "remote_ip":"%{remote_ip}","http_version":"%{http_version}",
            "redirect_url":"%{redirect_url}","url_effective":"%{url_effective}",
        },separators=(",",":")),
        "--url",url,
    ]
    require(cmd[-2:]==["--url",url],"CURL_URL_PAIR")
    require(cmd.count(url)==1,"CURL_URL_COUNT")
    return cmd

def curl_one_hop(curl_bin:str,url:str)->tuple[bytes,dict[str,Any]]:
    fd,tmp_name=tempfile.mkstemp(prefix="b15p2_nextdata_",suffix=".html")
    os.close(fd)
    body_path=Path(tmp_name)
    try:
        cmd=build_curl_command(curl_bin,url,body_path)
        env={"PATH":os.environ.get("PATH","/usr/bin:/bin"),"LANG":"C","LC_ALL":"C"}
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=CURL_TOTAL_TIMEOUT+5,check=False,env=env)
        metrics=json.loads(cp.stdout) if cp.stdout.strip() else {}
        body=body_path.read_bytes() if body_path.exists() else b""
        return body,{"curl_exit_code":cp.returncode,"stderr":cp.stderr.strip() or None,"metrics":metrics}
    finally:
        try: body_path.unlink()
        except FileNotFoundError: pass

def fetch_page_once(url:str)->tuple[bytes,str]:
    curl_bin=shutil.which("curl")
    require(curl_bin is not None,"CURL_NOT_AVAILABLE")
    current=url
    seen=set()
    for _ in range(MAX_REDIRECT_HOPS+1):
        require(current not in seen,"REDIRECT_LOOP")
        seen.add(current)
        require(allowed_url(current),"REDIRECT_HOST")
        body,hop=curl_one_hop(curl_bin,current)
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
        return body,current
    raise RuntimeError("REDIRECT_HOP_CAP")

def fetch_page(url:str)->tuple[bytes,str]:
    last:Exception|None=None
    for attempt in range(1,CURL_ATTEMPTS+1):
        try:
            return fetch_page_once(url)
        except Exception as exc:
            last=exc
            if attempt<CURL_ATTEMPTS:
                print(
                    f"ART_FETCH_RETRY attempt={attempt}/{CURL_ATTEMPTS} "
                    f"kind={type(exc).__name__} url={url}",
                    flush=True,
                )
                time.sleep(float(attempt))
                continue
            raise RuntimeError(f"ART_FETCH_FAILED:{type(exc).__name__}:{exc}") from exc
    raise RuntimeError(f"ART_FETCH_FAILED:{type(last).__name__}:{last}")


def load_events()->list[dict[str,Any]]:
    source_path=REPO/SOURCE_REL
    freeze_path=REPO/FREEZE_REL
    require(source_path.is_file(),"SOURCE_RESULT_MISSING")
    require(freeze_path.is_file(),"EVENT_FREEZE_MISSING")
    raw=source_path.read_bytes()
    require(sha256_bytes(raw)==EXPECTED_SOURCE_SHA,"SOURCE_RESULT_SHA")
    source=json.loads(raw.decode("utf-8"))
    freeze=json.loads(freeze_path.read_text(encoding="utf-8"))
    require(source.get("status")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS","SOURCE_STATUS")
    require(source.get("admitted_event_count")==94,"SOURCE_COUNT")
    require(freeze.get("status")=="B15P2_EXACT_ADMITTED_EVENT_SET_FROZEN","FREEZE_STATUS")
    require(freeze.get("event_set_sha256")==EXPECTED_EVENT_SET_SHA,"EVENT_SET_SHA")
    return source["events"]

def synthetic_art_scripts(symbol:str,body_key:str="body")->list[dict[str,Any]]:
    title=f"Delisting of {symbol} Perpetual Contract"
    obj={
        "props":{
            "pageProps":{
                "articleDetail":{
                    "title":title,
                    body_key:{
                        "blocks":[
                            {"children":[{"text":"X"*220}]},
                            {"children":[{"text":"Y"*220}]},
                        ]
                    },
                }
            }
        }
    }
    return [{"attrs":{"id":"__NEXT_DATA__","type":"application/json"},"data":json.dumps(obj)}]

def selftest()->int:
    try:
        require(is_art_generation_url("https://announcements.bybit.com/en-US/article/test--artabcdef123/"),"ART_URL_TRUE")
        require(not is_art_generation_url("https://announcements.bybit.com/en-US/article/test-bltabcdef123/"),"BLT_URL_FALSE")
        require(not is_art_generation_url("https://example.com/en-US/article/test--artabcdef123/"),"ART_HOST_FALSE")

        m=string_metrics("<p>Hello</p>","TEST")
        require(m["html_tag_count"]==2,"HTML_TAG_METRIC")

        rows=[]
        for symbol in ("AAAUSDT","BBBUSDT","CCCUSDT"):
            h=inspect_hydration_scripts(synthetic_art_scripts(symbol,"body"),symbol)
            require(h["exact_title_node_count"]==1,f"TITLE_NODE:{symbol}")
            require(h["next_data_contains_exact_title"] is True,f"TITLE_NEXT_DATA:{symbol}")
            require(any(
                c["path"]=="$.props.pageProps.articleDetail.body"
                and c["kind"]=="container"
                and c["chars"]>=440
                for c in h["structural_candidates"]
            ),f"BODY_CANDIDATE:{symbol}")
            require("X"*80 not in json.dumps(h,sort_keys=True),f"RAW_BODY_LEAK:{symbol}")
            rows.append({"symbol":symbol,"hydration":h})

        # Expand to exactly 18 synthetic rows to exercise all-event frequency logic.
        census_rows=[]
        for i in range(EXPECTED_ART_EVENT_COUNT):
            symbol=f"T{i:02d}USDT"
            h=inspect_hydration_scripts(synthetic_art_scripts(symbol,"body"),symbol)
            census_rows.append({"symbol":symbol,"hydration":h})
        cons=derive_frequency_consensus(census_rows)
        common_ids={c["identity"] for c in cons["common_candidates"]}
        require(
            "__NEXT_DATA__::$.props.pageProps.articleDetail.body" in common_ids,
            "COMMON_BODY_IDENTITY",
        )
        require(
            any(
                t["identity"]=="__NEXT_DATA__::$.props.pageProps.articleDetail.title"
                and t["event_count"]==EXPECTED_ART_EVENT_COUNT
                for t in cons["exact_title_identities"]
            ),
            "COMMON_TITLE_IDENTITY",
        )

        # Candidate discovery must not be limited to the title-containing JSON document.
        title_obj={"title":"Delisting of SPLITUSDT Perpetual Contract"}
        body_obj={"body":{"blocks":[{"children":[{"text":"K"*600}]}]}}
        split_scripts=[
            {"attrs":{"type":"application/json"},"data":json.dumps(title_obj)},
            {"attrs":{"type":"application/json"},"data":json.dumps(body_obj)},
        ]
        split=inspect_hydration_scripts(split_scripts,"SPLITUSDT")
        require(split["exact_title_node_count"]==1,"SPLIT_TITLE")
        require(any(
            c["path"]=="$.body"
            and c.get("script_has_exact_title") is False
            and c["chars"]>=600
            for c in split["structural_candidates"]
        ),"SPLIT_BODY_CANDIDATE")

        test_url="https://announcements.bybit.com/en-US/article/test--artabcdef123/"
        cmd=build_curl_command("/usr/bin/curl",test_url,Path("/tmp/x"))
        require(cmd[-2:]==["--url",test_url],"CURL_URL_PAIR")
        require("-4" in cmd and "--http1.1" in cmd,"CURL_TRANSPORT")
        require("--noproxy" in cmd and "*" in cmd,"CURL_NOPROXY")
        require("--proto" in cmd and "=https" in cmd,"CURL_HTTPS_ONLY")

        print("B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_SELF_TEST_PASS")
        return 0
    except Exception as exc:
        print("B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_SELF_TEST_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def write_report(path:Path,obj:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def live()->int:
    started=time.time()
    out=OUT_DIR/"art_generation_schema_census_v0_1.json"
    rows=[]
    try:
        events=load_events()
        selected=[]
        for e in events:
            urls=e.get("announcement_urls") or []
            require(len(urls)==1,f"EVENT_URL_COUNT:{e.get('symbol')}")
            url=urls[0]
            if is_art_generation_url(url):
                selected.append(e)

        selected.sort(key=lambda e:(int(e.get("delivery_ms") or 0),str(e.get("symbol") or "")))
        require(len(selected)==EXPECTED_ART_EVENT_COUNT,f"ART_EVENT_COUNT:{len(selected)}")
        require(len({e["announcement_urls"][0] for e in selected})==EXPECTED_ART_EVENT_COUNT,"ART_URL_UNIQUENESS")

        for idx,e in enumerate(selected,1):
            symbol=e["symbol"]
            url=e["announcement_urls"][0]
            print(f"ART_EVENT_START {idx:02d}/{EXPECTED_ART_EVENT_COUNT:02d} symbol={symbol}",flush=True)
            raw,final=fetch_page(url)
            scripts=parse_scripts(raw)
            hydration=inspect_hydration_scripts(scripts,symbol)
            rows.append({
                "symbol":symbol,
                "delivery_ms":e.get("delivery_ms"),
                "requested_url":url,
                "final_url":final,
                "raw_html_bytes":len(raw),
                "raw_html_sha256":sha256_bytes(raw),
                "hydration":hydration,
            })
            print(
                f"ART_EVENT_DONE {idx:02d}/{EXPECTED_ART_EVENT_COUNT:02d} symbol={symbol} "
                f"title_nodes={hydration['exact_title_node_count']} "
                f"candidates={hydration['structural_candidate_count']}",
                flush=True,
            )

        consensus=derive_frequency_consensus(rows)
        report={
            "schema":"sc001.b15p2_art_generation_schema_census.v0.1",
            "date":"2026-09-28",
            "status":"B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_COMPLETE",
            "selection":{
                "rule":"frozen announcement URL path matches --art[0-9a-f]+",
                "expected_event_count":EXPECTED_ART_EVENT_COUNT,
                "selected_event_count":len(rows),
                "selection_uses_semantic_or_price_outcomes":False,
            },
            "events":rows,
            "consensus":consensus,
            "article_body_text_persisted":False,
            "semantic_classification_performed":False,
            "price_accessed":False,
            "external_reference_price_accessed":False,
            "index_value_accessed":False,
            "basis_accessed":False,
            "returns_accessed":False,
            "pnl_accessed":False,
            "elapsed_seconds":round(time.time()-started,3),
        }
        write_report(out,report)

        print("B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_COMPLETE")
        print("selected_events =",len(rows))
        print("exact_title_identities =",json.dumps([
            {"identity":x["identity"],"event_count":x["event_count"]}
            for x in consensus["exact_title_identities"][:10]
        ],sort_keys=True))
        print("common_candidates =",consensus["common_candidate_count"])
        print("common_high_confidence =",consensus["common_high_confidence_candidate_count"])
        for c in consensus["common_candidates"][:15]:
            print(
                "COMMON_CANDIDATE",
                "identity="+str(c.get("identity")),
                "events="+str(c.get("event_count")),
                "title_coupled="+str(c.get("title_document_event_count")),
                "min_score="+str(c.get("min_score")),
                "min_chars="+str(c.get("min_chars")),
                "max_chars="+str(c.get("max_chars")),
                "path_depth="+str(c.get("path_depth")),
                "types="+json.dumps(c.get("types"),sort_keys=True),
                "kinds="+json.dumps(c.get("kinds"),sort_keys=True),
            )
        print("article_body_text_persisted=False")
        print("semantic_classification_performed=False")
        print("price/index-values/basis/returns/PnL=CLOSED")
        print("report =",out)
        return 0
    except Exception as exc:
        review={
            "schema":"sc001.b15p2_art_generation_schema_census.v0.1",
            "date":"2026-09-28",
            "status":"B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_REVIEW",
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
            "elapsed_seconds":round(time.time()-started,3),
        }
        try: write_report(out,review)
        except Exception: pass
        print("B15P2_ART_GENERATION_SCHEMA_CENSUS_V01_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        print("article_body_text_persisted=False")
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
