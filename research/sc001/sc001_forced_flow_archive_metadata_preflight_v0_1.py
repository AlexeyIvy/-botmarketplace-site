#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, os, time, urllib.parse, urllib.request
from pathlib import Path

PASS="FORCED_FLOW_ARCHIVE_METADATA_PREFLIGHT_PASS"
REVIEW="FORCED_FLOW_ARCHIVE_METADATA_PREFLIGHT_REVIEW"
DATE="2026-09-29"
START_MS=1790640000000
END_MS=1790726400000
BASES=("BTC","ETH","SOL","DOGE","ORDI","FIL","UNI","XRP","LTC","OP","BCH","SUI")
OKX_DOMAINS=("https://www.okx.com","https://us.okx.com")
OKX_STATIC_HOST="static.okx.com"
BYBIT_HOST="public.bybit.com"
TIMEOUT=45
RETRIES=2
MAX_RESPONSE_BYTES=4_000_000

def fail(msg:str)->None:
    raise RuntimeError(msg)

def request_json(url:str,body:bytes,referer:str)->dict:
    last=None
    for attempt in range(RETRIES):
        try:
            req=urllib.request.Request(
                url,data=body,method="POST",
                headers={
                    "User-Agent":"BotMarketplace-SC001-ForcedFlow-ArchiveMeta-v0.1",
                    "Accept":"application/json,*/*",
                    "Content-Type":"application/json",
                    "Referer":referer,
                },
            )
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_RESPONSE_BYTES+1)
                if int(getattr(resp,"status",200))!=200:
                    fail("metadata HTTP non-200")
            if len(raw)>MAX_RESPONSE_BYTES:
                fail("metadata response cap exceeded")
            obj=json.loads(raw.decode("utf-8"))
            if not isinstance(obj,dict):
                fail("metadata JSON object expected")
            return obj
        except Exception as exc:
            last=exc
            if attempt+1<RETRIES:
                time.sleep(1.0)
    raise RuntimeError(f"metadata request failed: {type(last).__name__}: {last}")

def walk(node):
    if isinstance(node,dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node,list):
        for v in node:
            yield from walk(v)

def trusted(url:str,host:str,basename:str)->bool:
    try:
        p=urllib.parse.urlparse(url)
        return p.scheme=="https" and (p.hostname or "").lower()==host and Path(p.path).name==basename
    except Exception:
        return False

def head_exact(url:str,host:str,basename:str)->dict:
    last=None
    for attempt in range(RETRIES):
        try:
            req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"BotMarketplace-SC001-ForcedFlow-ArchiveMeta-v0.1"})
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                status=int(getattr(resp,"status",200))
                final=resp.geturl()
                cl=resp.headers.get("Content-Length")
            if status!=200: fail(f"HEAD HTTP {status}")
            if not trusted(final,host,basename): fail("HEAD identity mismatch")
            if not cl or not cl.isdigit() or int(cl)<=0: fail("invalid Content-Length")
            return {"pass":True,"host":host,"filename":basename,"content_length":int(cl)}
        except Exception as exc:
            last=exc
            if attempt+1<RETRIES: time.sleep(1.0)
    raise RuntimeError(f"HEAD failed: {type(last).__name__}: {last}")

def bybit_meta(base:str)->dict:
    symbol=base+"USDT"
    basename=symbol+DATE+".csv.gz"
    url=f"https://{BYBIT_HOST}/trading/{symbol}/{basename}"
    rec=head_exact(url,BYBIT_HOST,basename)
    rec["symbol"]=symbol
    return rec

def okx_meta(base:str)->dict:
    fam=base+"-USDT"
    basename=base+"-USDT-SWAP-trades-"+DATE+".zip"
    payload={
        "module":"1",
        "instType":"SWAP",
        "instQueryParam":{"instFamilyList":[fam]},
        "dateQuery":{"dateAggrType":"daily","begin":str(START_MS),"end":str(END_MS-1)},
    }
    body=json.dumps(payload,separators=(",",":")).encode("utf-8")
    attempts=[]
    for domain in OKX_DOMAINS:
        try:
            url=domain+"/priapi/v5/broker/public/trade-data/download-link?t="+str(int(time.time()*1000))
            obj=request_json(url,body,"https://www.okx.com/historical-data")
            if str(obj.get("code"))!="0":
                fail(f"OKX code {obj.get('code')}")
            found=[]
            for node in walk(obj.get("data")):
                if not isinstance(node,dict): continue
                fn=node.get("filename") or node.get("fileName")
                u=node.get("url")
                if fn==basename and isinstance(u,str) and trusted(u,OKX_STATIC_HOST,basename) and u not in found:
                    found.append(u)
            attempts.append({"domain":domain,"exact_trusted_url_count":len(found)})
            if len(found)==1:
                rec=head_exact(found[0],OKX_STATIC_HOST,basename)
                rec["inst_family"]=fam
                rec["resolver_domain"]=domain
                rec["attempts"]=attempts
                return rec
            if len(found)>1:
                fail("multiple exact trusted OKX URLs")
        except Exception as exc:
            attempts.append({"domain":domain,"error":f"{type(exc).__name__}: {exc}"})
    raise RuntimeError(f"OKX exact archive unresolved: {attempts}")

def selftest()->dict:
    assert len(BASES)==12
    assert START_MS<END_MS and END_MS-START_MS==86400000
    assert trusted("https://public.bybit.com/trading/BTCUSDT/BTCUSDT2026-09-29.csv.gz",BYBIT_HOST,"BTCUSDT2026-09-29.csv.gz")
    assert not trusted("https://evil.example/BTCUSDT2026-09-29.csv.gz",BYBIT_HOST,"BTCUSDT2026-09-29.csv.gz")
    assert trusted("https://static.okx.com/cdn/okex/traderecords/trades/daily/20260929/BTC-USDT-SWAP-trades-2026-09-29.zip",OKX_STATIC_HOST,"BTC-USDT-SWAP-trades-2026-09-29.zip")
    return {"frozen_base_count":12,"date":DATE,"trusted_host_checks":True,"archive_body_accessed":False}

def write_result(out_dir:Path,obj:dict)->None:
    out_dir.mkdir(parents=True,exist_ok=True)
    p=out_dir/"forced_flow_archive_metadata_preflight_result.json"
    if p.exists(): fail("output collision")
    p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["self-test","live"],required=True)
    ap.add_argument("--out-dir",default=os.environ.get("BM_TEST_OUTPUT_DIR",os.environ.get("OUTPUT_DIR",str(Path.cwd()/"test-output"))))
    a=ap.parse_args()
    try:
        fixture=selftest()
        if a.mode=="self-test":
            result={
              "schema":"sc001.forced_flow_archive_metadata_preflight.v0.1",
              "mode":"self-test","status":PASS,"fixture":fixture,
              "network_calls_performed":False,"archive_body_accessed":False,
              "price_accessed":False,"trade_rows_accessed":False,"s0_executed":False
            }
            write_result(Path(a.out_dir),result); print(PASS); return 0
        rows=[]; failed=[]
        for base in BASES:
            rec={"base":base}
            try:
                rec["bybit"]=bybit_meta(base)
            except Exception as exc:
                rec["bybit"]={"pass":False,"error":f"{type(exc).__name__}: {exc}"}
            try:
                rec["okx"]=okx_meta(base)
            except Exception as exc:
                rec["okx"]={"pass":False,"error":f"{type(exc).__name__}: {exc}"}
            rec["pass"]=rec["bybit"].get("pass") is True and rec["okx"].get("pass") is True
            if not rec["pass"]: failed.append(base)
            rows.append(rec)
        status=PASS if not failed and len(rows)==12 else REVIEW
        result={
          "schema":"sc001.forced_flow_archive_metadata_preflight.v0.1",
          "mode":"live","status":status,"qualification_date":DATE,
          "pair_count":12,"passed_pair_count":sum(1 for x in rows if x["pass"]),
          "failed_bases":failed,"rows":rows,
          "network_scope":["BYBIT_ARCHIVE_HEAD","OKX_HISTORICAL_METADATA_RESOLVER","OKX_ARCHIVE_HEAD"],
          "archive_body_accessed":False,"trade_rows_accessed":False,"price_accessed":False,
          "cross_venue_ratio_calculated":False,"returns_calculated":False,"pnl_calculated":False,"s0_executed":False
        }
        write_result(Path(a.out_dir),result)
        print(status); print("passed_pairs =",result["passed_pair_count"]); print("failed_bases =",failed)
        return 0 if status==PASS else 2
    except Exception as exc:
        result={
          "schema":"sc001.forced_flow_archive_metadata_preflight.v0.1",
          "mode":a.mode,"status":REVIEW,"error":f"{type(exc).__name__}: {exc}",
          "archive_body_accessed":False,"trade_rows_accessed":False,"price_accessed":False,
          "cross_venue_ratio_calculated":False,"returns_calculated":False,"pnl_calculated":False,"s0_executed":False
        }
        try: write_result(Path(a.out_dir),result)
        except Exception: pass
        print(REVIEW); print(result["error"]); return 2

if __name__=="__main__":
    raise SystemExit(main())
