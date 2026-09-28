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
OUT_DIR=Path("/home/botmarket/sc001_data/SC001_B15P2_NEXT_DATA_STRUCTURE_PROBE")

CURL_CONNECT_TIMEOUT=5
CURL_TOTAL_TIMEOUT=15
MAX_REDIRECT_HOPS=3
MAX_HTML=2_000_000
BROWSER_UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/126.0 Mobile Safari/537.36"

STRUCTURAL_KEY_HINTS=frozenset({
    "article","body","content","description","detail","details","html","text","message","announcement",
    "data","payload","richtext","rich_text","document","post","page"
})

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
            data="".join(self.parts)
            self.scripts.append({"attrs":dict(self.attrs),"data":data})
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

def json_type(value:Any)->str:
    if value is None: return "null"
    if isinstance(value,bool): return "bool"
    if isinstance(value,str): return "string"
    if isinstance(value,(int,float)): return "number"
    if isinstance(value,list): return "list"
    if isinstance(value,dict): return "dict"
    return type(value).__name__

def walk_json(value:Any,path:str="$")->Iterable[tuple[str,Any,Any,str|int|None]]:
    yield path,value,None,None
    if isinstance(value,dict):
        for k,v in value.items():
            child=f"{path}.{k}"
            yield child,v,value,k
            yield from walk_json_children(v,child)
    elif isinstance(value,list):
        for i,v in enumerate(value):
            child=f"{path}[{i}]"
            yield child,v,value,i
            yield from walk_json_children(v,child)

def walk_json_children(value:Any,path:str)->Iterable[tuple[str,Any,Any,str|int|None]]:
    if isinstance(value,dict):
        for k,v in value.items():
            child=f"{path}.{k}"
            yield child,v,value,k
            yield from walk_json_children(v,child)
    elif isinstance(value,list):
        for i,v in enumerate(value):
            child=f"{path}[{i}]"
            yield child,v,value,i
            yield from walk_json_children(v,child)

def path_leaf(path:str)->str:
    leaf=re.split(r"[.\[]",path)[-1].rstrip("]")
    return leaf.lower()

def html_metrics(text:str)->dict[str,Any]:
    return {
        "length":len(text),
        "sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "html_tag_count":len(re.findall(r"<[A-Za-z][^>]*>",text)),
        "escaped_html_marker_count":text.count("&lt;"),
        "newline_count":text.count("\n"),
    }

def candidate_score(path:str,text:str)->int:
    leaf=path_leaf(path)
    score=0
    if leaf in STRUCTURAL_KEY_HINTS:
        score+=5
    if any(h in leaf for h in STRUCTURAL_KEY_HINTS):
        score+=3
    if len(text)>=120:
        score+=1
    if len(text)>=500:
        score+=1
    if re.search(r"<[A-Za-z][^>]*>",text):
        score+=2
    if "&lt;" in text:
        score+=1
    return score

def parent_summary(parent:Any,parent_path:str,title:str)->dict[str,Any]:
    if not isinstance(parent,dict):
        return {"parent_path":parent_path,"parent_type":json_type(parent)}
    fields=[]
    for k,v in parent.items():
        entry={"key":str(k),"type":json_type(v)}
        if isinstance(v,str):
            normalized=normalize_space(v)
            entry.update({
                "length":len(normalized),
                "sha256":hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                "contains_exact_title":title.lower() in normalized.lower(),
                "html_tag_count":len(re.findall(r"<[A-Za-z][^>]*>",v)),
                "escaped_html_marker_count":v.count("&lt;"),
            })
        elif isinstance(v,(dict,list)):
            entry["child_count"]=len(v)
        fields.append(entry)
    return {
        "parent_path":parent_path,
        "parent_type":"dict",
        "field_count":len(fields),
        "fields":sorted(fields,key=lambda x:x["key"])[:100],
    }

def inspect_next_data(scripts:list[dict[str,Any]],symbol:str)->dict[str,Any]:
    title=f"Delisting of {symbol} Perpetual Contract"
    matches=[s for s in scripts if (s["attrs"].get("id") or "")=="__NEXT_DATA__"]
    require(len(matches)==1,f"NEXT_DATA_SCRIPT_COUNT:{len(matches)}")
    raw=matches[0]["data"]
    obj=json.loads(raw)

    title_nodes=[]
    string_candidates=[]
    key_inventory=set()
    top_level_keys=sorted(obj.keys()) if isinstance(obj,dict) else []
    pageprops_keys=[]
    if isinstance(obj,dict) and isinstance(obj.get("props"),dict):
        pp=obj["props"].get("pageProps")
        if isinstance(pp,dict):
            pageprops_keys=sorted(pp.keys())

    for path,value,parent,key in walk_json(obj):
        if isinstance(key,str):
            key_inventory.add(key)
        if not isinstance(value,str):
            continue
        normalized=normalize_space(value)
        if not normalized:
            continue
        low=normalized.lower()
        if title.lower() in low:
            parent_path=path.rsplit(".",1)[0] if "." in path else "$"
            title_nodes.append({
                "path":path,
                "length":len(normalized),
                "sha256":hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                "parent":parent_summary(parent,parent_path,title),
            })
        score=candidate_score(path,value)
        if score>=4:
            m=html_metrics(value)
            string_candidates.append({
                "path":path,
                "score":score,
                "length":m["length"],
                "sha256":m["sha256"],
                "html_tag_count":m["html_tag_count"],
                "escaped_html_marker_count":m["escaped_html_marker_count"],
                "newline_count":m["newline_count"],
                "contains_exact_title":title.lower() in low,
            })

    string_candidates.sort(key=lambda x:(-x["score"],-x["length"],x["path"]))
    return {
        "next_data_script_length":len(raw),
        "next_data_script_sha256":hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "top_level_keys":top_level_keys,
        "pageprops_keys":pageprops_keys,
        "key_inventory":sorted(key_inventory)[:500],
        "exact_title_node_count":len(title_nodes),
        "exact_title_nodes":title_nodes[:20],
        "structural_string_candidate_count":len(string_candidates),
        "structural_string_candidates":string_candidates[:50],
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
    raw=source_path.read_bytes()
    require(sha256_bytes(raw)==EXPECTED_SOURCE_SHA,"SOURCE_RESULT_SHA")
    source=json.loads(raw.decode("utf-8"))
    freeze=json.loads(freeze_path.read_text(encoding="utf-8"))
    require(source.get("status")=="B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS","SOURCE_STATUS")
    require(source.get("admitted_event_count")==94,"SOURCE_COUNT")
    require(freeze.get("status")=="B15P2_EXACT_ADMITTED_EVENT_SET_FROZEN","FREEZE_STATUS")
    require(freeze.get("event_set_sha256")==EXPECTED_EVENT_SET_SHA,"EVENT_SET_SHA")
    return source["events"]

def selftest()->int:
    try:
        title="Delisting of TESTUSDT Perpetual Contract"
        obj={
            "props":{
                "pageProps":{
                    "article":{
                        "title":title,
                        "content":"<p>"+"X"*400+"</p>",
                        "description":"Y"*80,
                    }
                }
            }
        }
        raw=json.dumps(obj)
        scripts=[{"attrs":{"id":"__NEXT_DATA__","type":"application/json"},"data":raw}]
        out=inspect_next_data(scripts,"TESTUSDT")
        require(out["exact_title_node_count"]==1,"TITLE_NODE_COUNT")
        node=out["exact_title_nodes"][0]
        fields={f["key"]:f for f in node["parent"]["fields"]}
        require(fields["title"]["contains_exact_title"] is True,"PARENT_TITLE")
        require(fields["content"]["length"]>=400,"PARENT_CONTENT_LENGTH")
        require(fields["content"]["html_tag_count"]>=2,"PARENT_CONTENT_HTML")
        require(any(c["path"].endswith(".content") and c["score"]>=4 for c in out["structural_string_candidates"]),"CONTENT_CANDIDATE")

        cmd=build_curl_command("/usr/bin/curl","https://announcements.bybit.com/en-US/article/test/",Path("/tmp/x"))
        require(cmd[-2:]==["--url","https://announcements.bybit.com/en-US/article/test/"],"URL_PAIR")
        require("-4" in cmd and "--http1.1" in cmd,"CURL_TRANSPORT")

        print("B15P2_NEXT_DATA_STRUCTURE_PROBE_V02_SELF_TEST_PASS")
        return 0
    except Exception as exc:
        print("B15P2_NEXT_DATA_STRUCTURE_PROBE_V02_SELF_TEST_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def write_report(path:Path,obj:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def live()->int:
    started=time.time()
    out=OUT_DIR/f"next_data_structure_probe_v0_2_{int(started)}_p{os.getpid()}.json"
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
            nd=inspect_next_data(scripts,symbol)
            rows.append({
                "symbol":symbol,
                "requested_url":url,
                "final_url":final,
                "raw_html_bytes":len(raw),
                "raw_html_sha256":sha256_bytes(raw),
                "next_data":nd,
            })

        report={
            "schema":"sc001.b15p2_next_data_structure_probe.v0.2",
            "date":"2026-09-28",
            "status":"B15P2_NEXT_DATA_STRUCTURE_PROBE_V02_COMPLETE",
            "events":rows,
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
        print("B15P2_NEXT_DATA_STRUCTURE_PROBE_V02_COMPLETE")
        for row in rows:
            nd=row["next_data"]
            print(
                row["symbol"],
                "title_nodes="+str(nd["exact_title_node_count"]),
                "candidates="+str(nd["structural_string_candidate_count"]),
                "pageprops_keys="+json.dumps(nd["pageprops_keys"]),
            )
            for node in nd["exact_title_nodes"][:3]:
                parent=node.get("parent") or {}
                fields=parent.get("fields") or []
                print(
                    "TITLE_PARENT",
                    row["symbol"],
                    "path="+str(parent.get("parent_path")),
                    "fields="+json.dumps([
                        {
                            "key":f.get("key"),"type":f.get("type"),"length":f.get("length"),
                            "html_tag_count":f.get("html_tag_count"),
                            "contains_exact_title":f.get("contains_exact_title")
                        } for f in fields
                    ],sort_keys=True),
                )
            for c in nd["structural_string_candidates"][:10]:
                print(
                    "CANDIDATE",
                    row["symbol"],
                    "path="+c["path"],
                    "score="+str(c["score"]),
                    "length="+str(c["length"]),
                    "html_tags="+str(c["html_tag_count"]),
                    "escaped_html="+str(c["escaped_html_marker_count"]),
                    "contains_title="+str(c["contains_exact_title"]),
                )
        print("article_body_text_persisted=False")
        print("semantic_classification_performed=False")
        print("price/index-values/basis/returns/PnL=CLOSED")
        print("report =",out)
        return 0
    except Exception as exc:
        review={
            "schema":"sc001.b15p2_next_data_structure_probe.v0.2",
            "date":"2026-09-28",
            "status":"B15P2_NEXT_DATA_STRUCTURE_PROBE_V02_REVIEW",
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
        print("B15P2_NEXT_DATA_STRUCTURE_PROBE_V02_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        print("report =",out)
        return 2

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","live"),required=True)
    a=ap.parse_args()
    return selftest() if a.mode=="self-test" else live()

if __name__=="__main__":
    raise SystemExit(main())
