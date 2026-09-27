#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

STAGE="SC001-B13C-S0-PRICE-ARCHIVE-METADATA-PREFLIGHT-V0.1"
PASS="B13C_S0_PRICE_ARCHIVE_METADATA_PREFLIGHT_PASS"
REVIEW="B13C_S0_PRICE_ARCHIVE_METADATA_PREFLIGHT_REVIEW"

ROOT=Path(__file__).resolve().parents[2]
CENSUS_RESULT=ROOT/"docs/research/sc001-b13c-s0-real-event-only-cluster-census-result-v0.1.json"
EXPECTED_CENSUS_SHA256="fd08901e77bb73c00bb53826e925b2124d52e05d6c8f45cdc154b1c57a2ab1eb"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_B13C_S0_PRICE_ARCHIVE_PREFLIGHT"
OUT=OUT_DIR/"b13c_s0_price_archive_metadata_preflight_v0_1.json"

TRUSTED_HOST="public.bybit.com"
EXPECTED_COUNT=76
TIMEOUT=30
RETRIES=3
MAX_REDIRECTS=5


def fail(msg:str)->None:
    raise RuntimeError(msg)


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path:Path,obj:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)


def trusted_url(url:str,symbol:str,filename:str)->bool:
    try:
        p=urllib.parse.urlparse(url)
    except Exception:
        return False
    expected_path=f"/trading/{symbol}/{filename}"
    return (
        p.scheme=="https"
        and (p.hostname or "").lower()==TRUSTED_HOST
        and p.path==expected_path
        and not p.params
        and not p.query
        and not p.fragment
    )


class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self,symbol:str,filename:str):
        super().__init__()
        self.symbol=symbol
        self.filename=filename
        self.count=0

    def redirect_request(self,req,fp,code,msg,headers,newurl):
        self.count+=1
        if self.count>MAX_REDIRECTS:
            fail("redirect cap exceeded")
        if not trusted_url(newurl,self.symbol,self.filename):
            fail(f"untrusted redirect: {newurl}")
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def head_one(item:dict)->dict:
    symbol=str(item["symbol"])
    day=str(item["utc_day"])
    filename=str(item["filename"])
    url=str(item["url"])
    if filename!=f"{symbol}{day}.csv.gz":
        fail(f"filename identity mismatch: {filename}")
    if not trusted_url(url,symbol,filename):
        fail(f"untrusted URL identity: {url}")

    last=None
    for attempt in range(1,RETRIES+1):
        try:
            opener=urllib.request.build_opener(StrictRedirect(symbol,filename))
            req=urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent":"BotMarketplace-SC001-B13C-S0/0.1"},
            )
            with opener.open(req,timeout=TIMEOUT) as resp:
                status=int(getattr(resp,"status",200))
                final=resp.geturl()
                headers=dict(resp.headers.items())
            if status!=200:
                fail(f"HEAD HTTP {status}: {filename}")
            if not trusted_url(final,symbol,filename):
                fail(f"final URL identity mismatch: {final}")
            cl=headers.get("Content-Length") or headers.get("content-length")
            if cl is None or not str(cl).isdigit() or int(cl)<=0:
                fail(f"invalid Content-Length: {filename} -> {cl!r}")
            return {
                "symbol":symbol,
                "utc_day":day,
                "filename":filename,
                "url":url,
                "final_url":final,
                "http_status":status,
                "content_length":int(cl),
                "last_modified":headers.get("Last-Modified") or headers.get("last-modified"),
                "etag":headers.get("ETag") or headers.get("etag"),
                "content_type":headers.get("Content-Type") or headers.get("content-type"),
            }
        except Exception as exc:
            last=exc
            if attempt<RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"HEAD failed {filename}: {type(last).__name__}: {last}")


def load_required()->list[dict]:
    if not CENSUS_RESULT.is_file():
        fail(f"missing census result: {CENSUS_RESULT}")
    actual=sha256_file(CENSUS_RESULT)
    if actual!=EXPECTED_CENSUS_SHA256:
        fail(f"census result SHA mismatch: {actual}")
    obj=json.loads(CENSUS_RESULT.read_text(encoding="utf-8"))
    if obj.get("status")!="B13C_S0_SOURCE_ONLY_CLUSTER_CENSUS_PASS":
        fail("census result status mismatch")
    cc=obj.get("cluster_census") or {}
    if cc.get("sample_gate_ready") is not True:
        fail("cluster sample gate not ready")
    rows=obj.get("required_price_archives") or []
    if len(rows)!=EXPECTED_COUNT:
        fail(f"required archive count mismatch: {len(rows)}")
    seen=set()
    out=[]
    for row in rows:
        if not isinstance(row,dict):
            fail("required archive row not object")
        key=(row.get("symbol"),row.get("utc_day"),row.get("filename"),row.get("url"))
        if key in seen:
            fail(f"duplicate archive identity: {key}")
        seen.add(key)
        symbol=str(row.get("symbol") or "")
        day=str(row.get("utc_day") or "")
        filename=str(row.get("filename") or "")
        url=str(row.get("url") or "")
        if not symbol.endswith("USDT"):
            fail(f"unexpected symbol: {symbol}")
        if len(day)!=10 or day[4]!="-" or day[7]!="-":
            fail(f"invalid UTC day: {day}")
        if filename!=f"{symbol}{day}.csv.gz":
            fail(f"filename mismatch: {filename}")
        if not trusted_url(url,symbol,filename):
            fail(f"URL mismatch: {url}")
        out.append({"symbol":symbol,"utc_day":day,"filename":filename,"url":url})
    return out


def self_test()->int:
    try:
        good={
            "symbol":"BTCUSDT",
            "utc_day":"2026-09-26",
            "filename":"BTCUSDT2026-09-26.csv.gz",
            "url":"https://public.bybit.com/trading/BTCUSDT/BTCUSDT2026-09-26.csv.gz",
        }
        assert trusted_url(good["url"],good["symbol"],good["filename"])
        assert not trusted_url(
            "https://evil.example/trading/BTCUSDT/BTCUSDT2026-09-26.csv.gz",
            good["symbol"],good["filename"]
        )
        assert not trusted_url(
            "https://public.bybit.com/trading/ETHUSDT/BTCUSDT2026-09-26.csv.gz",
            good["symbol"],good["filename"]
        )
        print("B13C_S0_PRICE_ARCHIVE_METADATA_PREFLIGHT_V01_SELF_TEST_PASS")
        return 0
    except Exception as exc:
        print("B13C_S0_PRICE_ARCHIVE_METADATA_PREFLIGHT_V01_SELF_TEST_REVIEW")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2


def metadata()->int:
    try:
        required=load_required()
        results=[]
        for i,item in enumerate(required,1):
            print(f"HEAD {i}/{len(required)} {item['filename']}",flush=True)
            results.append(head_one(item))

        total=sum(x["content_length"] for x in results)
        by_symbol=Counter(x["symbol"] for x in results)
        by_day=Counter(x["utc_day"] for x in results)
        report={
            "stage":STAGE,
            "version":"0.1",
            "status":PASS,
            "required_archive_count":len(results),
            "total_content_length_bytes":total,
            "total_content_length_gib":total/(1024**3),
            "by_symbol_file_count":dict(sorted(by_symbol.items())),
            "by_day_file_count":dict(sorted(by_day.items())),
            "files":results,
            "price_body_opened":False,
            "price_rows_parsed":False,
            "returns_calculated":False,
            "pnl_calculated":False,
            "network_calls_performed":True,
            "http_method":"HEAD_ONLY",
            "collector_mutation_performed":False,
            "next_state":"FREEZE_METADATA_SNAPSHOT_AND_PREPARE_STREAMING_DOWNLOAD_SCHEMA_QUALIFICATION",
        }
        atomic_json(OUT,report)
        print(PASS)
        print("required_archive_count =",len(results))
        print("total_content_length_bytes =",total)
        print("total_content_length_gib =",f"{report['total_content_length_gib']:.3f}")
        print("report =",OUT)
        return 0
    except Exception as exc:
        report={
            "stage":STAGE,
            "version":"0.1",
            "status":REVIEW,
            "error":f"{type(exc).__name__}: {exc}",
            "price_body_opened":False,
            "price_rows_parsed":False,
            "returns_calculated":False,
            "pnl_calculated":False,
            "network_calls_performed":True,
            "http_method":"HEAD_ONLY",
            "collector_mutation_performed":False,
        }
        try:
            atomic_json(OUT,report)
        except Exception:
            pass
        print(REVIEW)
        print("error =",report["error"])
        print("report =",OUT)
        return 2


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","metadata"),required=True)
    a=ap.parse_args()
    return self_test() if a.mode=="self-test" else metadata()


if __name__=="__main__":
    raise SystemExit(main())
