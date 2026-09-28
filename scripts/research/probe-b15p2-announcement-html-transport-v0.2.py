#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import grp
import json
import os
import pwd
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DOG_URL="https://announcements.bybit.com/en-US/article/delisting-of-dogusdt-perpetual-contract-blt9ee6b6807b7ba01f/"
TON_URL="https://announcements.bybit.com/en-US/article/delisting-of-tonusdt-perpetual-contract-bltd27f1f00e6b0f5ed/"
API_URL="https://api.bybit.com/v5/announcements/index?locale=en-US&type=delistings&limit=1"

ANNOUNCEMENT_HOST="announcements.bybit.com"
API_HOST="api.bybit.com"

BROWSER_UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/126.0 Mobile Safari/537.36"
BOT_UA="BotMarketplace-SC001-B15P2-TransportProbe/0.2"

CONNECT_TIMEOUT=4
CURL_HOP_TIMEOUT=10
URLLIB_TIMEOUT=10
MAX_REDIRECT_HOPS=3
READ_BYTES=4096

OUT_DIR=Path("/home/botmarket/sc001_data/SC001_B15P2_ANNOUNCEMENT_TRANSPORT_PROBE")

def utc_now()->str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def require(cond:bool, code:str)->None:
    if not cond:
        raise RuntimeError(code)

def allowed_url(url:str, expected_host:str)->bool:
    p=urllib.parse.urlparse(url)
    return p.scheme=="https" and p.hostname==expected_host

def dns_probe(host:str)->dict[str,Any]:
    out={"host":host,"ipv4":[],"ipv6":[],"error":None}
    try:
        infos=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        v4=set()
        v6=set()
        for family,_,_,_,sockaddr in infos:
            if family==socket.AF_INET:
                v4.add(sockaddr[0])
            elif family==socket.AF_INET6:
                v6.add(sockaddr[0])
        out["ipv4"]=sorted(v4)
        out["ipv6"]=sorted(v6)
    except Exception as exc:
        out["error"]=f"{type(exc).__name__}: {exc}"
    return out

def curl_version(curl_bin:str|None)->dict[str,Any]:
    if not curl_bin:
        return {"available":False,"path":None,"version_line":None,"error":"curl_not_found"}
    try:
        cp=subprocess.run([curl_bin,"--version"],capture_output=True,text=True,timeout=5,check=False)
        line=(cp.stdout.splitlines() or cp.stderr.splitlines() or [""])[0]
        return {
            "available":cp.returncode==0,
            "path":curl_bin,
            "version_line":line,
            "returncode":cp.returncode,
            "stderr":cp.stderr.strip() or None,
        }
    except Exception as exc:
        return {"available":False,"path":curl_bin,"version_line":None,"error":f"{type(exc).__name__}: {exc}"}

def parse_curl_metrics(raw:str)->dict[str,Any]:
    try:
        obj=json.loads(raw)
        require(isinstance(obj,dict),"curl_metrics_not_object")
        return obj
    except Exception as exc:
        return {"metrics_parse_error":f"{type(exc).__name__}: {exc}","metrics_raw":raw}

def curl_one_hop(
    curl_bin:str,
    *,
    label:str,
    url:str,
    family:int|None,
    ua:str,
    http1:bool,
)->dict[str,Any]:
    cmd=[
        curl_bin,
        "-sS",
        "--noproxy","*",
        "--proto","=https",
        "--connect-timeout",str(CONNECT_TIMEOUT),
        "--max-time",str(CURL_HOP_TIMEOUT),
        "--max-redirs","0",
        "-A",ua,
        "-H","Accept: text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "-o","/dev/null",
        "-w",
        json.dumps({
            "http_code":"%{http_code}",
            "remote_ip":"%{remote_ip}",
            "remote_port":"%{remote_port}",
            "http_version":"%{http_version}",
            "content_type":"%{content_type}",
            "size_download":"%{size_download}",
            "time_namelookup":"%{time_namelookup}",
            "time_connect":"%{time_connect}",
            "time_appconnect":"%{time_appconnect}",
            "time_starttransfer":"%{time_starttransfer}",
            "time_total":"%{time_total}",
            "ssl_verify_result":"%{ssl_verify_result}",
            "url_effective":"%{url_effective}",
            "redirect_url":"%{redirect_url}",
        },separators=(",",":")),
    ]
    if family==4:
        cmd.insert(1,"-4")
    elif family==6:
        cmd.insert(1,"-6")
    if http1:
        cmd.insert(1,"--http1.1")

    t0=time.monotonic()
    try:
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=CURL_HOP_TIMEOUT+5,check=False)
        elapsed=round(time.monotonic()-t0,3)
        out={
            "label":label,
            "url":url,
            "curl_exit_code":cp.returncode,
            "elapsed_seconds":elapsed,
            "stderr":cp.stderr.strip() or None,
            "family":family,
            "http1_forced":http1,
            "user_agent_kind":"browser" if ua==BROWSER_UA else "bot",
        }
        out.update(parse_curl_metrics(cp.stdout))
        return out
    except subprocess.TimeoutExpired as exc:
        return {
            "label":label,
            "url":url,
            "curl_exit_code":None,
            "elapsed_seconds":round(time.monotonic()-t0,3),
            "error_type":"SubprocessTimeoutExpired",
            "error_message":str(exc),
            "family":family,
            "http1_forced":http1,
            "user_agent_kind":"browser" if ua==BROWSER_UA else "bot",
        }
    except Exception as exc:
        return {
            "label":label,
            "url":url,
            "curl_exit_code":None,
            "elapsed_seconds":round(time.monotonic()-t0,3),
            "error_type":type(exc).__name__,
            "error_message":str(exc),
            "family":family,
            "http1_forced":http1,
            "user_agent_kind":"browser" if ua==BROWSER_UA else "bot",
        }

def curl_safe_chain(
    curl_bin:str|None,
    *,
    label:str,
    url:str,
    expected_host:str,
    family:int|None,
    ua:str,
    http1:bool=False,
)->dict[str,Any]:
    result={
        "label":label,
        "client":"curl",
        "initial_url":url,
        "expected_host":expected_host,
        "family":family,
        "http1_forced":http1,
        "hops":[],
        "ok":False,
        "terminal_reason":None,
    }
    if not curl_bin:
        result["terminal_reason"]="curl_not_available"
        return result
    current=url
    seen=set()
    for hop in range(MAX_REDIRECT_HOPS+1):
        if current in seen:
            result["terminal_reason"]="redirect_loop"
            return result
        seen.add(current)
        if not allowed_url(current,expected_host):
            result["terminal_reason"]="redirect_outside_allowed_host"
            result["blocked_url"]=current
            return result
        one=curl_one_hop(
            curl_bin,
            label=f"{label}_hop{hop}",
            url=current,
            family=family,
            ua=ua,
            http1=http1,
        )
        result["hops"].append(one)
        rc=one.get("curl_exit_code")
        code=str(one.get("http_code") or "")
        if rc!=0:
            result["terminal_reason"]="curl_transport_error"
            return result
        redirect=str(one.get("redirect_url") or "").strip()
        if code.startswith("3") and redirect:
            next_url=urllib.parse.urljoin(current,redirect)
            if not allowed_url(next_url,expected_host):
                result["terminal_reason"]="redirect_outside_allowed_host"
                result["blocked_url"]=next_url
                return result
            current=next_url
            continue
        result["final_url"]=current
        result["final_http_code"]=code
        result["ok"]=code.startswith("2")
        result["terminal_reason"]="http_success" if result["ok"] else "http_non_2xx"
        return result
    result["terminal_reason"]="redirect_hop_cap"
    return result

class SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, expected_host:str):
        super().__init__()
        self.expected_host=expected_host

    def redirect_request(self,req,fp,code,msg,headers,newurl):
        target=urllib.parse.urljoin(req.full_url,newurl)
        if not allowed_url(target,self.expected_host):
            raise RuntimeError(f"redirect_outside_allowed_host:{target}")
        return super().redirect_request(req,fp,code,msg,headers,target)

@contextlib.contextmanager
def forced_address_family(family:int|None):
    if family is None:
        yield
        return
    original=socket.getaddrinfo
    def filtered(host,port,*args,**kwargs):
        infos=original(host,port,*args,**kwargs)
        wanted=socket.AF_INET if family==4 else socket.AF_INET6
        selected=[x for x in infos if x[0]==wanted]
        if not selected:
            raise OSError(f"no_addresses_for_forced_ipv{family}")
        return selected
    socket.getaddrinfo=filtered
    try:
        yield
    finally:
        socket.getaddrinfo=original

def urllib_probe(label:str,url:str,expected_host:str,family:int|None,ua:str)->dict[str,Any]:
    t0=time.monotonic()
    out={
        "label":label,
        "client":"urllib",
        "url":url,
        "expected_host":expected_host,
        "family":family,
        "ok":False,
    }
    try:
        require(allowed_url(url,expected_host),"initial_url_not_allowed")
        opener=urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            SameHostRedirectHandler(expected_host),
        )
        req=urllib.request.Request(url,headers={
            "User-Agent":ua,
            "Accept":"text/html,application/xhtml+xml",
        })
        with forced_address_family(family):
            with opener.open(req,timeout=URLLIB_TIMEOUT) as resp:
                final=resp.geturl()
                require(allowed_url(final,expected_host),"final_url_not_allowed")
                chunk=resp.read(READ_BYTES)
                out.update({
                    "http_status":getattr(resp,"status",None),
                    "final_url":final,
                    "read_bytes":len(chunk),
                    "content_type":resp.headers.get("Content-Type"),
                    "ok":200 <= int(getattr(resp,"status",0) or 0) < 300 and len(chunk)>0,
                })
    except Exception as exc:
        out["error_type"]=type(exc).__name__
        out["error_message"]=str(exc)
    out["elapsed_seconds"]=round(time.monotonic()-t0,3)
    return out

def curl_probe_ok(p:dict[str,Any])->bool:
    return bool(p.get("ok"))

def urllib_probe_ok(p:dict[str,Any])->bool:
    return bool(p.get("ok"))

def derive_pattern(probes:list[dict[str,Any]])->str:
    by={p["label"]:p for p in probes}
    curl_labels=(
        "curl_ipv4_dog_browser",
        "curl_ipv4_dog_browser_http1",
        "curl_ipv6_dog_browser",
        "curl_ipv4_dog_bot",
        "curl_ipv4_ton_browser",
        "curl_ipv4_announcement_api_control",
    )
    if all((by.get(k) or {}).get("terminal_reason")=="curl_not_available" for k in curl_labels):
        return "CURL_UNAVAILABLE_REVIEW"
    v4=curl_probe_ok(by["curl_ipv4_dog_browser"])
    v6=curl_probe_ok(by["curl_ipv6_dog_browser"])
    curl_bot=curl_probe_ok(by["curl_ipv4_dog_bot"])
    http1=curl_probe_ok(by["curl_ipv4_dog_browser_http1"])
    ton=curl_probe_ok(by["curl_ipv4_ton_browser"])
    api=curl_probe_ok(by["curl_ipv4_announcement_api_control"])
    udef=urllib_probe_ok(by["urllib_default_dog_bot"])
    uv4=urllib_probe_ok(by["urllib_ipv4_dog_bot"])
    uv6=urllib_probe_ok(by["urllib_ipv6_dog_bot"])

    if v4 and ton and not udef and uv4:
        return "PYTHON_DEFAULT_ADDRESS_SELECTION_PROBLEM_IPV4_WORKS"
    if v4 and ton and not udef and not uv4:
        return "CURL_HTML_WORKS_URLLIB_HTML_FAILS"
    if v4 and not v6:
        return "IPV4_HTML_WORKS_IPV6_HTML_FAILS"
    if v4 and not curl_bot:
        return "HTML_USER_AGENT_DEPENDENT"
    if v4 and not http1:
        return "HTML_HTTP_PROTOCOL_DEPENDENT"
    if not v4 and not ton and api:
        return "ANNOUNCEMENT_HTML_FAILS_BUT_ANNOUNCEMENT_API_CONTROL_WORKS"
    if not v4 and not ton and not api:
        return "ANNOUNCEMENT_HTML_AND_API_CONTROL_FAIL_FROM_VPS"
    if v4 and ton and udef:
        return "HTML_TRANSPORT_CURRENTLY_WORKS_ALL_PRIMARY_CONTROLS"
    if uv4 and not uv6:
        return "URLLIB_IPV4_WORKS_IPV6_FAILS"
    return "MIXED_TRANSPORT_RESULT_REVIEW"

def atomic_write(path:Path,obj:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)
    try:
        uid=pwd.getpwnam("botmarket").pw_uid
        gid=grp.getgrnam("botmarket").gr_gid
        os.chown(path,uid,gid)
        os.chmod(path,0o640)
    except Exception:
        pass

def selftest()->int:
    try:
        require(allowed_url(DOG_URL,ANNOUNCEMENT_HOST),"dog_url")
        require(allowed_url(TON_URL,ANNOUNCEMENT_HOST),"ton_url")
        require(allowed_url(API_URL,API_HOST),"api_url")
        require(not allowed_url("http://announcements.bybit.com/x",ANNOUNCEMENT_HOST),"http_not_rejected")
        require(not allowed_url("https://example.com/x",ANNOUNCEMENT_HOST),"cross_host_not_rejected")

        sample_ok={"label":"curl_ipv4_dog_browser","ok":True}
        sample_bad={"label":"curl_ipv6_dog_browser","ok":False}
        probes=[
            sample_ok,
            sample_bad,
            {"label":"curl_ipv4_dog_bot","ok":True},
            {"label":"curl_ipv4_dog_browser_http1","ok":True},
            {"label":"curl_ipv4_ton_browser","ok":True},
            {"label":"curl_ipv4_announcement_api_control","ok":True},
            {"label":"urllib_default_dog_bot","ok":False},
            {"label":"urllib_ipv4_dog_bot","ok":False},
            {"label":"urllib_ipv6_dog_bot","ok":False},
        ]
        require(derive_pattern(probes)=="CURL_HTML_WORKS_URLLIB_HTML_FAILS","pattern_fixture_curl_vs_urllib")

        ipv4_only=[
            {"label":"curl_ipv4_dog_browser","ok":True},
            {"label":"curl_ipv4_dog_browser_http1","ok":True},
            {"label":"curl_ipv6_dog_browser","ok":False},
            {"label":"curl_ipv4_dog_bot","ok":True},
            {"label":"curl_ipv4_ton_browser","ok":False},
            {"label":"curl_ipv4_announcement_api_control","ok":True},
            {"label":"urllib_default_dog_bot","ok":True},
            {"label":"urllib_ipv4_dog_bot","ok":True},
            {"label":"urllib_ipv6_dog_bot","ok":False},
        ]
        require(derive_pattern(ipv4_only)=="IPV4_HTML_WORKS_IPV6_HTML_FAILS","pattern_fixture_ipv4_only")

        api_only=[
            {"label":"curl_ipv4_dog_browser","ok":False},
            {"label":"curl_ipv4_dog_browser_http1","ok":False},
            {"label":"curl_ipv6_dog_browser","ok":False},
            {"label":"curl_ipv4_dog_bot","ok":False},
            {"label":"curl_ipv4_ton_browser","ok":False},
            {"label":"curl_ipv4_announcement_api_control","ok":True},
            {"label":"urllib_default_dog_bot","ok":False},
            {"label":"urllib_ipv4_dog_bot","ok":False},
            {"label":"urllib_ipv6_dog_bot","ok":False},
        ]
        require(derive_pattern(api_only)=="ANNOUNCEMENT_HTML_FAILS_BUT_ANNOUNCEMENT_API_CONTROL_WORKS","pattern_fixture_api_only")

        curl_missing=[
            {"label":k,"client":"curl","ok":False,"terminal_reason":"curl_not_available"}
            for k in (
                "curl_ipv4_dog_browser","curl_ipv4_dog_browser_http1","curl_ipv6_dog_browser",
                "curl_ipv4_dog_bot","curl_ipv4_ton_browser","curl_ipv4_announcement_api_control"
            )
        ] + [
            {"label":"urllib_default_dog_bot","client":"urllib","ok":False},
            {"label":"urllib_ipv4_dog_bot","client":"urllib","ok":False},
            {"label":"urllib_ipv6_dog_bot","client":"urllib","ok":False},
        ]
        require(derive_pattern(curl_missing)=="CURL_UNAVAILABLE_REVIEW","pattern_fixture_curl_unavailable")

        require(parse_curl_metrics('{"http_code":"200","remote_ip":"1.2.3.4"}').get("http_code")=="200","curl_metrics_fixture")

        print("B15P2_ANNOUNCEMENT_HTML_TRANSPORT_PROBE_V02_SELF_TEST_PASS")
        return 0
    except Exception as exc:
        print("B15P2_ANNOUNCEMENT_HTML_TRANSPORT_PROBE_V02_SELF_TEST_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def live()->int:
    os.umask(0o027)
    run_id=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")+f"_p{os.getpid()}"
    out_path=OUT_DIR/f"announcement_html_transport_probe_v0_2_{run_id}.json"
    curl_bin=shutil.which("curl")
    probes:list[dict[str,Any]]=[]
    started=utc_now()
    try:
        probes.extend([
            curl_safe_chain(curl_bin,label="curl_ipv4_dog_browser",url=DOG_URL,expected_host=ANNOUNCEMENT_HOST,family=4,ua=BROWSER_UA),
            curl_safe_chain(curl_bin,label="curl_ipv4_dog_browser_http1",url=DOG_URL,expected_host=ANNOUNCEMENT_HOST,family=4,ua=BROWSER_UA,http1=True),
            curl_safe_chain(curl_bin,label="curl_ipv6_dog_browser",url=DOG_URL,expected_host=ANNOUNCEMENT_HOST,family=6,ua=BROWSER_UA),
            curl_safe_chain(curl_bin,label="curl_ipv4_dog_bot",url=DOG_URL,expected_host=ANNOUNCEMENT_HOST,family=4,ua=BOT_UA),
            curl_safe_chain(curl_bin,label="curl_ipv4_ton_browser",url=TON_URL,expected_host=ANNOUNCEMENT_HOST,family=4,ua=BROWSER_UA),
            curl_safe_chain(curl_bin,label="curl_ipv4_announcement_api_control",url=API_URL,expected_host=API_HOST,family=4,ua=BOT_UA),
            urllib_probe("urllib_default_dog_bot",DOG_URL,ANNOUNCEMENT_HOST,None,BOT_UA),
            urllib_probe("urllib_ipv4_dog_bot",DOG_URL,ANNOUNCEMENT_HOST,4,BOT_UA),
            urllib_probe("urllib_ipv6_dog_bot",DOG_URL,ANNOUNCEMENT_HOST,6,BOT_UA),
        ])
        pattern=derive_pattern(probes)
        status="B15P2_ANNOUNCEMENT_HTML_TRANSPORT_PROBE_COMPLETE"
        report={
            "schema":"sc001.b15p2_announcement_html_transport_probe.v0.2",
            "date":"2026-09-28",
            "run_id":run_id,
            "status":status,
            "started_utc":started,
            "finished_utc":utc_now(),
            "runtime":{
                "python_version":sys.version.split()[0],
                "uid":os.getuid(),
                "euid":os.geteuid(),
            },
            "curl":curl_version(curl_bin),
            "proxy_environment_present":any(k.lower().endswith("_proxy") for k in os.environ),
            "proxy_usage_disabled_for_probes":True,
            "dns":{
                ANNOUNCEMENT_HOST:dns_probe(ANNOUNCEMENT_HOST),
                API_HOST:dns_probe(API_HOST),
            },
            "probes":probes,
            "observed_pattern":pattern,
            "price_accessed":False,
            "external_reference_price_accessed":False,
            "index_value_accessed":False,
            "basis_accessed":False,
            "returns_accessed":False,
            "pnl_accessed":False,
            "semantic_classification_performed":False,
        }
        atomic_write(out_path,report)

        print(status)
        print("observed_pattern =",pattern)
        for p in probes:
            if p.get("client")=="curl":
                last=(p.get("hops") or [{}])[-1]
                print(
                    p["label"],
                    "ok="+str(p.get("ok")),
                    "reason="+str(p.get("terminal_reason")),
                    "curl_rc="+str(last.get("curl_exit_code")),
                    "http="+str(last.get("http_code")),
                    "remote_ip="+str(last.get("remote_ip")),
                    "http_version="+str(last.get("http_version")),
                    "ttfb="+str(last.get("time_starttransfer")),
                    "total="+str(last.get("time_total") or last.get("elapsed_seconds")),
                    "error="+str(last.get("stderr") or last.get("error_message")),
                )
            else:
                print(
                    p["label"],
                    "ok="+str(p.get("ok")),
                    "http="+str(p.get("http_status")),
                    "total="+str(p.get("elapsed_seconds")),
                    "error="+str(p.get("error_message")),
                )
        print("price/index-values/basis/returns/PnL=CLOSED")
        print("semantic_classification_performed=False")
        print("report =",out_path)
        return 0
    except Exception as exc:
        report={
            "schema":"sc001.b15p2_announcement_html_transport_probe.v0.2",
            "date":"2026-09-28",
            "run_id":run_id,
            "status":"B15P2_ANNOUNCEMENT_HTML_TRANSPORT_PROBE_REVIEW",
            "started_utc":started,
            "finished_utc":utc_now(),
            "error_type":type(exc).__name__,
            "error_message":str(exc),
            "probes":probes,
            "price_accessed":False,
            "external_reference_price_accessed":False,
            "index_value_accessed":False,
            "basis_accessed":False,
            "returns_accessed":False,
            "pnl_accessed":False,
            "semantic_classification_performed":False,
        }
        try:
            atomic_write(out_path,report)
        except Exception:
            pass
        print("B15P2_ANNOUNCEMENT_HTML_TRANSPORT_PROBE_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        print("price/index-values/basis/returns/PnL=CLOSED")
        print("semantic_classification_performed=False")
        print("report =",out_path)
        return 2

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","live"),required=True)
    args=ap.parse_args()
    return selftest() if args.mode=="self-test" else live()

if __name__=="__main__":
    raise SystemExit(main())
