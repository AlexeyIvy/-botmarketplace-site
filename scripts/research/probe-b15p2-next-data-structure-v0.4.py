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
OUT_DIR=Path("/home/botmarket/sc001_data/SC001_B15P2_NEXT_DATA_STRUCTURE_PROBE")

CURL_CONNECT_TIMEOUT=5
CURL_TOTAL_TIMEOUT=15
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
MAX_CANDIDATES=100

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
        for c in d.get("structural_candidates") or []:
            candidates.append({
                **c,
                "script_role":role,
                "script_index":d["script_index"],
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

def derive_consensus(rows:list[dict[str,Any]])->dict[str,Any]:
    require(len(rows)==2,"CONSENSUS_EVENT_COUNT")
    by_symbol={r["symbol"]:r["hydration"] for r in rows}
    symbols=sorted(by_symbol)

    candidate_maps={
        sym:{c["identity"]:c for c in by_symbol[sym].get("structural_candidates",[])}
        for sym in symbols
    }
    common=set(candidate_maps[symbols[0]]) & set(candidate_maps[symbols[1]])
    consensus=[]
    for identity in sorted(common):
        cs=[candidate_maps[sym][identity] for sym in symbols]
        consensus.append({
            "identity":identity,
            "script_role":cs[0].get("script_role"),
            "path":cs[0].get("path"),
            "types":{sym:c.get("type") for sym,c in zip(symbols,cs)},
            "kinds":{sym:c.get("kind") for sym,c in zip(symbols,cs)},
            "scores":{sym:c.get("score") for sym,c in zip(symbols,cs)},
            "chars":{sym:c.get("chars") for sym,c in zip(symbols,cs)},
            "html_tag_counts":{
                sym:(c.get("html_tag_count") if c.get("kind")=="string" else c.get("descendant_html_tag_count"))
                for sym,c in zip(symbols,cs)
            },
            "min_score":min(int(c.get("score") or 0) for c in cs),
            "min_chars":min(int(c.get("chars") or 0) for c in cs),
            "path_depth":json_path_depth(str(cs[0].get("path") or "")),
        })
    consensus.sort(key=lambda x:(-x["min_score"],-x["path_depth"],-x["min_chars"],x["identity"]))

    title_ids={
        sym:{n["identity"] for n in by_symbol[sym].get("exact_title_nodes",[])}
        for sym in symbols
    }
    common_title_ids=sorted(title_ids[symbols[0]] & title_ids[symbols[1]])

    high_conf=[c for c in consensus if c["min_score"]>=6 and c["min_chars"]>=120]
    return {
        "symbols":symbols,
        "common_exact_title_identities":common_title_ids,
        "common_candidate_count":len(consensus),
        "common_candidates":consensus[:50],
        "high_confidence_candidate_count":len(high_conf),
        "high_confidence_candidates":high_conf[:20],
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

def fetch_page(url:str)->tuple[bytes,str]:
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

def synthetic_scripts(symbol:str,body_value:Any,*,title_in_next:bool=True)->list[dict[str,Any]]:
    title=f"Delisting of {symbol} Perpetual Contract"
    article={"title":title,"content":body_value,"description":"short"}
    if title_in_next:
        obj={"props":{"pageProps":{"article":article}}}
        return [{"attrs":{"id":"__NEXT_DATA__","type":"application/json"},"data":json.dumps(obj)}]
    next_obj={"props":{"pageProps":{"shell":{"locale":"en-US"}}}}
    other_obj={"article":article}
    return [
        {"attrs":{"id":"__NEXT_DATA__","type":"application/json"},"data":json.dumps(next_obj)},
        {"attrs":{"type":"application/json"},"data":json.dumps(other_obj)},
    ]

def selftest()->int:
    try:
        # 1) Tag metric counts opening and closing tags symmetrically.
        m=string_metrics("<p>Hello</p>","TEST")
        require(m["html_tag_count"]==2,"HTML_TAG_METRIC")

        # 2) Body as HTML string sibling to title.
        secret_body="<p>"+"X"*400+"</p>"
        out1=inspect_hydration_scripts(synthetic_scripts("TESTUSDT",secret_body),"TESTUSDT")
        require(out1["exact_title_node_count"]==1,"TITLE_NODE_STRING")
        require(out1["exact_title_nodes"][0].get("exact_string_match") is True,"TITLE_NODE_EXACT")
        require(any(c["path"].endswith(".content") and c["kind"]=="string" and c["chars"]>=400
                    for c in out1["structural_candidates"]),"STRING_CONTENT_CANDIDATE")
        title_node=out1["exact_title_nodes"][0]
        require(title_node["ancestors"][-1]["path"]=="$.props.pageProps.article","TITLE_ARTICLE_ANCESTOR")
        ancestor_fields={f["key"]:f for f in title_node["ancestors"][-1]["fields"]}
        require("content" in ancestor_fields,"TITLE_ANCESTOR_CONTENT_FIELD")
        require(ancestor_fields["content"]["normalized_length"]>=400,"TITLE_ANCESTOR_CONTENT_LENGTH")
        require(secret_body not in json.dumps(out1,sort_keys=True),"RAW_BODY_LEAK_STRING")

        # 3) Body as nested rich-text container, not a string.
        nested={"blocks":[{"children":[{"text":"Y"*220},{"text":"Z"*220}]}]}
        out2=inspect_hydration_scripts(synthetic_scripts("TESTUSDT",nested),"TESTUSDT")
        require(any(c["path"].endswith(".content") and c["kind"]=="container" and c["chars"]>=440
                    for c in out2["structural_candidates"]),"CONTAINER_CONTENT_CANDIDATE")
        require("Y"*80 not in json.dumps(out2,sort_keys=True),"RAW_BODY_LEAK_CONTAINER")

        # 4) Body as JSON-encoded string remains discoverable without decoding content.
        json_body=json.dumps({"blocks":[{"text":"J"*650}]})
        out_json=inspect_hydration_scripts(synthetic_scripts("TESTUSDT",json_body),"TESTUSDT")
        require(any(
            c["path"].endswith(".content")
            and c["kind"]=="string"
            and c.get("parseable_json_string") is True
            for c in out_json["structural_candidates"]
        ),"JSON_STRING_CONTENT_CANDIDATE")

        # 5) Title can live inside a list-backed article container.
        list_obj={"props":{"pageProps":{"articles":[
            {"title":"Delisting of TESTUSDT Perpetual Contract","blob":"Q"*700}
        ]}}}
        list_scripts=[{"attrs":{"id":"__NEXT_DATA__","type":"application/json"},"data":json.dumps(list_obj)}]
        out_list=inspect_hydration_scripts(list_scripts,"TESTUSDT")
        require(out_list["exact_title_node_count"]==1,"LIST_TITLE_COUNT")
        require("[0]" in out_list["exact_title_nodes"][0]["path"],"LIST_TITLE_PATH")
        require(any(c["path"].endswith(".blob") and c["chars"]>=700
                    for c in out_list["structural_candidates"]),"LARGE_UNHINTED_FALLBACK")

        # 6) Consensus identifies the same structural path across two events.
        rows=[
            {"symbol":"AAAUSDT","hydration":inspect_hydration_scripts(synthetic_scripts("AAAUSDT","<p>"+"A"*300+"</p>"),"AAAUSDT")},
            {"symbol":"BBBUSDT","hydration":inspect_hydration_scripts(synthetic_scripts("BBBUSDT","<p>"+"B"*350+"</p>"),"BBBUSDT")},
        ]
        cons=derive_consensus(rows)
        require("__NEXT_DATA__::$.props.pageProps.article.content" in {c["identity"] for c in cons["high_confidence_candidates"]},
                "CONSENSUS_CONTENT_PATH")
        require("__NEXT_DATA__::$.props.pageProps.article.title" in set(cons["common_exact_title_identities"]),
                "CONSENSUS_TITLE_PATH")

        # 7) A longer SEO/body string containing the title is not an exact-title node.
        seo_obj={"props":{"pageProps":{
            "seo":"News: Delisting of TESTUSDT Perpetual Contract | Bybit",
            "article":{"title":"Delisting of TESTUSDT Perpetual Contract","content":"S"*300}
        }}}
        seo_scripts=[{"attrs":{"id":"__NEXT_DATA__","type":"application/json"},"data":json.dumps(seo_obj)}]
        seo=inspect_hydration_scripts(seo_scripts,"TESTUSDT")
        require(seo["exact_title_node_count"]==1,"SEO_EXACT_TITLE_COUNT")

        # 8) Exact title outside __NEXT_DATA__ is detected instead of crashing or misattributing.
        outside=inspect_hydration_scripts(
            synthetic_scripts("TESTUSDT","<p>"+"R"*300+"</p>",title_in_next=False),
            "TESTUSDT",
        )
        require(outside["next_data_script_count"]==1,"OUTSIDE_NEXT_COUNT")
        require(outside["parseable_title_script_count"]==1,"OUTSIDE_TITLE_DOC_COUNT")
        require(outside["next_data_contains_exact_title"] is False,"OUTSIDE_NEXT_TITLE_FALSE")
        require(outside["title_outside_next_data"] is True,"OUTSIDE_TITLE_FLAG")
        require(any(n["script_role"].startswith("JSON_TYPE:") for n in outside["exact_title_nodes"]),
                "OUTSIDE_TITLE_ROLE")

        # 9) No candidate structure contains raw body text fields.
        for out in (out1,out2):
            for c in out["structural_candidates"]:
                require("value" not in c and "text" not in c,"RAW_TEXT_FIELD_LEAK")

        # 10) Curl contract.
        test_url="https://announcements.bybit.com/en-US/article/test/"
        cmd=build_curl_command("/usr/bin/curl",test_url,Path("/tmp/x"))
        require(cmd[-2:]==["--url",test_url],"CURL_URL_PAIR")
        require("-4" in cmd and "--http1.1" in cmd,"CURL_TRANSPORT")
        require("--noproxy" in cmd and "*" in cmd,"CURL_NOPROXY")
        require("--proto" in cmd and "=https" in cmd,"CURL_HTTPS_ONLY")
        require(not allowed_url("http://announcements.bybit.com/en-US/article/test/"),"HTTP_NOT_REJECTED")
        require(not allowed_url("https://example.com/en-US/article/test/"),"HOST_NOT_REJECTED")

        print("B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_SELF_TEST_PASS")
        return 0
    except Exception as exc:
        print("B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_SELF_TEST_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def write_report(path:Path,obj:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def live()->int:
    started=time.time()
    out=OUT_DIR/f"next_data_structure_probe_v0_4_{int(started)}_p{os.getpid()}.json"
    rows=[]
    try:
        events=load_events()
        for symbol in ("DOGUSDT","TONUSDT"):
            matches=[e for e in events if e.get("symbol")==symbol]
            require(len(matches)==1,f"EVENT_IDENTITY:{symbol}")
            e=matches[0]
            url=e["announcement_urls"][0]
            raw,final=fetch_page(url)
            scripts=parse_scripts(raw)
            hydration=inspect_hydration_scripts(scripts,symbol)
            rows.append({
                "symbol":symbol,
                "requested_url":url,
                "final_url":final,
                "raw_html_bytes":len(raw),
                "raw_html_sha256":sha256_bytes(raw),
                "hydration":hydration,
            })

        consensus=derive_consensus(rows)
        report={
            "schema":"sc001.b15p2_next_data_structure_probe.v0.4",
            "date":"2026-09-28",
            "status":"B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_COMPLETE",
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

        print("B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_COMPLETE")
        for row in rows:
            nd=row["hydration"]
            print(
                row["symbol"],
                "title_nodes="+str(nd["exact_title_node_count"]),
                "candidates="+str(nd["structural_candidate_count"]),
                "parseable_json_scripts="+str(nd["parseable_json_script_count"]),
                "next_data_scripts="+str(nd["next_data_script_count"]),
                "next_data_has_title="+str(nd["next_data_contains_exact_title"]),
                "title_outside_next_data="+str(nd["title_outside_next_data"]),
            )
            for node in nd["exact_title_nodes"][:3]:
                print(
                    "TITLE_NODE",
                    row["symbol"],
                    "identity="+str(node.get("identity")),
                    "script_role="+str(node.get("script_role")),
                    "path="+str(node.get("path")),
                    "ancestor_paths="+json.dumps([a.get("path") for a in node.get("ancestors",[])])
                )
            for c in nd["structural_candidates"][:12]:
                print(
                    "CANDIDATE",
                    row["symbol"],
                    "identity="+c["identity"],
                    "script_role="+str(c.get("script_role")),
                    "path="+c["path"],
                    "kind="+str(c.get("kind")),
                    "score="+str(c["score"]),
                    "chars="+str(c.get("chars")),
                    "html_tags="+str(c.get("html_tag_count") if c.get("kind")=="string" else c.get("descendant_html_tag_count")),
                )

        print("CONSENSUS",
              "common_title_identities="+json.dumps(consensus["common_exact_title_identities"]),
              "common_candidates="+str(consensus["common_candidate_count"]),
              "high_confidence="+str(consensus["high_confidence_candidate_count"]))
        for c in consensus["high_confidence_candidates"][:10]:
            print(
                "CONSENSUS_CANDIDATE",
                "identity="+c["identity"],
                "script_role="+str(c.get("script_role")),
                "path="+c["path"],
                "min_score="+str(c["min_score"]),
                "min_chars="+str(c["min_chars"]),
                "path_depth="+str(c.get("path_depth")),
                "types="+json.dumps(c["types"],sort_keys=True),
                "kinds="+json.dumps(c["kinds"],sort_keys=True),
            )

        print("article_body_text_persisted=False")
        print("semantic_classification_performed=False")
        print("price/index-values/basis/returns/PnL=CLOSED")
        print("report =",out)
        return 0
    except Exception as exc:
        review={
            "schema":"sc001.b15p2_next_data_structure_probe.v0.4",
            "date":"2026-09-28",
            "status":"B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_REVIEW",
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
        print("B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_REVIEW")
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
