#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, os, subprocess, time, urllib.parse, urllib.request
from pathlib import Path

DATES=("2026-09-29","2026-09-28","2026-09-23")
STARTS={
 "2026-09-29":1790640000000,
 "2026-09-28":1790553600000,
 "2026-09-23":1790121600000,
}
DOMAINS=("https://www.okx.com","https://us.okx.com")
HOST="static.okx.com"
INST_FAMILY="BTC-USDT"
TIMEOUT=45
RETRIES=2
MAX_BYTES=4_000_000
ROOT=Path(__file__).resolve().parents[2]
FREEZE=ROOT/"docs/research/sc001-next-primary-okx-archive-publication-resolver-diagnostic-freeze-v0.1.json"

PASS="OKX_ARCHIVE_DIAGNOSTIC_PASS"
LAG="OKX_ARCHIVE_DIAGNOSTIC_RECENT_PUBLICATION_LAG"
CONTRACT="OKX_ARCHIVE_DIAGNOSTIC_RESOLVER_CONTRACT_REVIEW"
REVIEW="OKX_ARCHIVE_DIAGNOSTIC_SOURCE_REVIEW"

def fail(msg:str)->None: raise RuntimeError(msg)

def git_blob(p:Path)->str:
    return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()

def require_freeze()->dict:
    if not FREEZE.is_file() or FREEZE.is_symlink(): fail("freeze missing/invalid")
    fr=json.loads(FREEZE.read_text(encoding="utf-8"))
    if fr.get("status")!="FROZEN_BEFORE_OKX_ARCHIVE_DIAGNOSTIC": fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()): fail("runner blob mismatch")
    if tuple(fr.get("frozen_dates") or ())!=DATES: fail("date freeze mismatch")
    if fr.get("frozen_instrument_family")!=INST_FAMILY: fail("instrument freeze mismatch")
    if fr.get("live_run_authorized") is not False: fail("live authorization firewall mismatch")
    if fr.get("archive_body_access_authorized") is not False: fail("archive body firewall mismatch")
    return fr

def walk(node):
    if isinstance(node,dict):
        yield node
        for v in node.values(): yield from walk(v)
    elif isinstance(node,list):
        for v in node: yield from walk(v)

def trusted(url:str,basename:str)->bool:
    try:
        p=urllib.parse.urlparse(url)
        return p.scheme=="https" and (p.hostname or "").lower()==HOST and Path(p.path).name==basename
    except Exception:
        return False

def request(url:str,body:bytes)->dict:
    last=None
    for attempt in range(RETRIES):
        try:
            req=urllib.request.Request(url,data=body,method="POST",headers={
              "User-Agent":"BotMarketplace-SC001-OKX-Archive-Diagnostic-v0.1",
              "Accept":"application/json,*/*",
              "Content-Type":"application/json",
              "Referer":"https://www.okx.com/historical-data",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_BYTES+1)
                code=int(getattr(resp,"status",200))
            if code!=200: fail(f"HTTP {code}")
            if len(raw)>MAX_BYTES: fail("response cap")
            obj=json.loads(raw.decode("utf-8"))
            if not isinstance(obj,dict): fail("JSON object expected")
            return obj
        except Exception as exc:
            last=exc
            if attempt+1<RETRIES: time.sleep(1)
    raise RuntimeError(f"request failed: {type(last).__name__}: {last}")

def safe_schema(node):
    if isinstance(node,dict):
        return sorted(str(k) for k in node.keys())[:80]
    if isinstance(node,list):
        return {"type":"list","len":len(node),"first_type":type(node[0]).__name__ if node else None}
    return {"type":type(node).__name__}

def head(url:str,basename:str)->dict:
    req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"BotMarketplace-SC001-OKX-Archive-Diagnostic-v0.1"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
        status=int(getattr(resp,"status",200)); final=resp.geturl(); cl=resp.headers.get("Content-Length")
    if status!=200 or not trusted(final,basename) or not cl or not cl.isdigit() or int(cl)<=0:
        fail("HEAD identity/content-length")
    return {"http_status":status,"content_length":int(cl),"host":HOST}

def one(day:str)->dict:
    start=STARTS[day]; end=start+86400000
    basename=f"BTC-USDT-SWAP-trades-{day}.zip"
    payload={
      "module":"1","instType":"SWAP",
      "instQueryParam":{"instFamilyList":[INST_FAMILY]},
      "dateQuery":{"dateAggrType":"daily","begin":str(start),"end":str(end-1)}
    }
    body=json.dumps(payload,separators=(",",":")).encode()
    attempts=[]
    structurally_valid=False
    for domain in DOMAINS:
        try:
            url=domain+"/priapi/v5/broker/public/trade-data/download-link?t="+str(int(time.time()*1000))
            obj=request(url,body)
            structurally_valid = structurally_valid or (str(obj.get("code"))=="0")
            found=[]
            for node in walk(obj.get("data")):
                if not isinstance(node,dict): continue
                fn=node.get("filename") or node.get("fileName")
                u=node.get("url")
                if fn==basename and isinstance(u,str) and trusted(u,basename) and u not in found:
                    found.append(u)
            rec={"domain":domain,"code":str(obj.get("code")),"top_level_keys":safe_schema(obj),"data_shape":safe_schema(obj.get("data")),"exact_trusted_url_count":len(found)}
            attempts.append(rec)
            if len(found)==1:
                return {"date":day,"filename":basename,"resolved":True,"attempts":attempts,"head":head(found[0],basename),"structurally_valid_success_payload":structurally_valid}
            if len(found)>1: fail("multiple exact URLs")
        except Exception as exc:
            attempts.append({"domain":domain,"error":f"{type(exc).__name__}: {exc}"})
    return {"date":day,"filename":basename,"resolved":False,"attempts":attempts,"structurally_valid_success_payload":structurally_valid}

def selftest():
    assert len(DATES)==3
    assert DATES[0]=="2026-09-29" and DATES[-1]=="2026-09-23"
    assert trusted("https://static.okx.com/x/BTC-USDT-SWAP-trades-2026-09-29.zip","BTC-USDT-SWAP-trades-2026-09-29.zip")
    assert not trusted("https://evil.example/BTC-USDT-SWAP-trades-2026-09-29.zip","BTC-USDT-SWAP-trades-2026-09-29.zip")
    return True

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["self-test","live"],required=True)
    ap.add_argument("--out-dir",default=os.environ.get("BM_TEST_OUTPUT_DIR",os.environ.get("OUTPUT_DIR",str(Path.cwd()/"test-output"))))
    a=ap.parse_args()
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    try:
        require_freeze()
        selftest()
        if a.mode=="self-test":
            result={"schema":"sc001.okx_archive_publication_resolver_diagnostic.v0.1","mode":"self-test","status":PASS,"network_calls_performed":False,"archive_body_accessed":False}
        else:
            rows=[one(d) for d in DATES]
            resolved={r["date"]:r["resolved"] for r in rows}
            if all(resolved.values()): status=PASS
            elif not resolved["2026-09-29"] and (resolved["2026-09-28"] or resolved["2026-09-23"]): status=LAG
            elif not any(resolved.values()) and all(r["structurally_valid_success_payload"] for r in rows): status=CONTRACT
            else: status=REVIEW
            result={"schema":"sc001.okx_archive_publication_resolver_diagnostic.v0.1","mode":"live","status":status,"instrument_family":INST_FAMILY,"rows":rows,"archive_body_accessed":False,"trade_rows_accessed":False,"price_accessed":False,"s0_executed":False}
        p=out/"okx_archive_publication_resolver_diagnostic_result.json"
        if p.exists(): fail("output collision")
        p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(result["status"])
        return 0 if result["status"] in {PASS,LAG,CONTRACT} else 2
    except Exception as exc:
        print(REVIEW); print(f"{type(exc).__name__}: {exc}"); return 2

if __name__=="__main__":
    raise SystemExit(main())
