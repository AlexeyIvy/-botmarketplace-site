from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FAMILIES=("BTC-USD","ETH-USD")
DATES=("2026-09-16","2026-09-15")
DOMAINS=("https://www.okx.com","https://us.okx.com")
ENDPOINT="/api/v5/public/market-data-history"
TIMEOUT=45
MAX_BYTES=8_000_000

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT=DATA_ROOT/"SC001_B14A_D0_SOURCE_ARCHIVE"/"sc001_b14a_futures_metadata_shape_diag_v0_1.json"

def day_bounds(day:str):
    d=datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo=int(d.timestamp()*1000)
    return lo,lo+86_400_000

def fetch(domain,family,day):
    lo,hi=day_bounds(day)
    params={
        "module":"1",
        "instType":"FUTURES",
        "instFamilyList":family,
        "dateAggrType":"daily",
        "begin":str(lo),
        "end":str(hi),
    }
    url=domain+ENDPOINT+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={
        "User-Agent":"BotMarketplace-SC001-B14A-MetadataDiag/0.1",
        "Accept":"application/json",
    })
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
        raw=resp.read(MAX_BYTES+1)
        final=resp.geturl()
        status=int(getattr(resp,"status",200))
    if len(raw)>MAX_BYTES:
        raise RuntimeError("response cap exceeded")
    return json.loads(raw.decode("utf-8")),final,status,url

def walk(node,path="$"):
    if isinstance(node,dict):
        yield path,node
        for k,v in node.items():
            yield from walk(v,f"{path}.{k}")
    elif isinstance(node,list):
        for i,v in enumerate(node):
            yield from walk(v,f"{path}[{i}]")

def inventory(obj):
    out=[]
    for path,node in walk(obj.get("data")):
        if not isinstance(node,dict):
            continue
        fn=node.get("filename") or node.get("fileName")
        urls=[]
        for key in ("url","fileUrl","downloadUrl"):
            u=node.get(key)
            if isinstance(u,str):
                p=urllib.parse.urlparse(u)
                urls.append({
                    "field":key,
                    "host":p.hostname,
                    "basename":Path(p.path).name,
                })
        id_fields={}
        for key in ("instId","instFamily","instType","module","dateAggrType","begin","end","sizeMB","fileSize","type"):
            v=node.get(key)
            if isinstance(v,(str,int,float,bool)) or v is None:
                if key in node:
                    id_fields[key]=v
        if fn is not None or urls or id_fields:
            out.append({
                "path":path,
                "filename":fn,
                "urls":urls,
                "identity":id_fields,
                "keys":sorted(node.keys()),
            })
    return out

def main():
    report={
        "stage":"SC001-B14A-FUTURES-METADATA-SHAPE-DIAG-V0.1",
        "price_accessed":False,
        "archive_body_accessed":False,
        "queries":[],
    }
    for family in FAMILIES:
        for day in DATES:
            rec={"family":family,"day":day}
            last=None
            for domain in DOMAINS:
                try:
                    obj,final,status,request_url=fetch(domain,family,day)
                    rec.update({
                        "domain":domain,
                        "http_status":status,
                        "final_host":urllib.parse.urlparse(final).hostname,
                        "request_url":request_url,
                        "code":obj.get("code") if isinstance(obj,dict) else None,
                        "msg":obj.get("msg") if isinstance(obj,dict) else None,
                        "data_type":type(obj.get("data")).__name__ if isinstance(obj,dict) else None,
                        "data_len":len(obj.get("data")) if isinstance(obj,dict) and isinstance(obj.get("data"),list) else None,
                        "inventory":inventory(obj if isinstance(obj,dict) else {}),
                    })
                    break
                except Exception as exc:
                    last=f"{type(exc).__name__}: {exc}"
            if "http_status" not in rec:
                rec["error"]=last
            report["queries"].append(rec)

    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    print("B14A_FUTURES_METADATA_SHAPE_DIAG_COMPLETE")
    for q in report["queries"]:
        print("QUERY",q["family"],q["day"],"http=",q.get("http_status"),"code=",q.get("code"),"inventory=",len(q.get("inventory") or []))
        for item in (q.get("inventory") or []):
            print(" ",item["path"],"filename=",item.get("filename"),"urls=",item.get("urls"),"identity=",item.get("identity"))
    print("archive_body_accessed = False")
    print("price_accessed = False")
    print("report =",OUT)

if __name__=="__main__":
    main()
