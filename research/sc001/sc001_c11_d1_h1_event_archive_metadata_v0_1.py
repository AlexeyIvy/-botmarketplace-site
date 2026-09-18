from __future__ import annotations

import html
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C11-D1-H1-EVENT-ARCHIVE-METADATA-V0.1"
PASS = "C11_D1_H1_EVENT_ARCHIVE_METADATA_PASS"
REVIEW = "C11_D1_H1_EVENT_ARCHIVE_METADATA_REVIEW"

EVENTS = (
    ("EMPLOYMENT","2025-01-10","2025-01-10T13:30:00Z","https://www.bls.gov/schedule/2025/01_sched_list.htm","Employment Situation","January 10, 2025"),
    ("CPI","2025-01-15","2025-01-15T13:30:00Z","https://www.bls.gov/schedule/2025/01_sched_list.htm","Consumer Price Index","January 15, 2025"),
    ("EMPLOYMENT","2025-02-07","2025-02-07T13:30:00Z","https://www.bls.gov/schedule/2025/02_sched_list.htm","Employment Situation","February 7, 2025"),
    ("CPI","2025-02-12","2025-02-12T13:30:00Z","https://www.bls.gov/schedule/2025/02_sched_list.htm","Consumer Price Index","February 12, 2025"),
    ("EMPLOYMENT","2025-03-07","2025-03-07T13:30:00Z","https://www.bls.gov/schedule/2025/03_sched_list.htm","Employment Situation","March 7, 2025"),
    ("CPI","2025-03-12","2025-03-12T12:30:00Z","https://www.bls.gov/schedule/2025/03_sched_list.htm","Consumer Price Index","March 12, 2025"),
    ("EMPLOYMENT","2025-04-04","2025-04-04T12:30:00Z","https://www.bls.gov/schedule/2025/04_sched_list.htm","Employment Situation","April 4, 2025"),
    ("CPI","2025-04-10","2025-04-10T12:30:00Z","https://www.bls.gov/schedule/2025/04_sched_list.htm","Consumer Price Index","April 10, 2025"),
    ("EMPLOYMENT","2025-05-02","2025-05-02T12:30:00Z","https://www.bls.gov/schedule/2025/05_sched_list.htm","Employment Situation","May 2, 2025"),
    ("CPI","2025-05-13","2025-05-13T12:30:00Z","https://www.bls.gov/schedule/2025/05_sched_list.htm","Consumer Price Index","May 13, 2025"),
    ("EMPLOYMENT","2025-06-06","2025-06-06T12:30:00Z","https://www.bls.gov/schedule/2025/06_sched_list.htm","Employment Situation","June 6, 2025"),
    ("CPI","2025-06-11","2025-06-11T12:30:00Z","https://www.bls.gov/schedule/2025/06_sched_list.htm","Consumer Price Index","June 11, 2025"),
)

OKX_DOMAINS=("https://www.okx.com","https://us.okx.com")
OKX_STATIC_HOST="static.okx.com"
OKX_FAMILY="BTC-USDT"
TIMEOUT=60
RETRIES=3
MAX_TEXT=2_000_000
MAX_JSON=4_000_000

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-c11-d1-h1-event-archive-metadata-protocol-v0.1.md"
FREEZE=ROOT/"docs/research/sc001-c11-d1-implementation-freeze-v0.1.json"
DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_C11_D1_H1_EVENT_METADATA"
OUT=OUT_DIR/"sc001_c11_d1_h1_event_metadata_report_v0_1.json"

def fail(msg:str)->None: raise RuntimeError(msg)
def load_json(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict): fail(f"JSON object expected: {path}")
    return x
def atomic_json(path:Path,obj:object)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(str(path)+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)
def git_blob(path:Path)->str:
    return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(path.relative_to(ROOT))],text=True).strip()
def require_freeze():
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_C11_D1_RUN": fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()): fail("runner identity mismatch")
    if fr.get("protocol_git_blob_sha")!=git_blob(PROTOCOL): fail("protocol identity mismatch")
    if int(fr.get("event_count",0))!=12: fail("event count mismatch")
    for k in ("historical_trade_body_authorized","macro_release_value_authorized","macro_surprise_authorized","first_impulse_authorized","post_release_move_authorized","pnl_authorized","promotional_alpha_authorized"):
        if fr.get(k) is not False: fail(f"firewall mismatch: {k}")

def request_bytes(req,cap,label):
    last=None
    for a in range(1,RETRIES+1):
        try:
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(cap+1); status=int(getattr(resp,"status",200)); final=resp.geturl()
            if status!=200: fail(f"{label} HTTP {status}")
            if len(raw)>cap: fail(f"{label} response cap exceeded")
            return raw,final
        except Exception as exc:
            last=exc
            if a<RETRIES: time.sleep(float(a))
    raise RuntimeError(f"{label} failed: {type(last).__name__}: {last}")

def verify_bls(kind,date,url,title,date_text):
    req=urllib.request.Request(url,headers={"User-Agent":"BotMarketplace-SC001-C11-D1/0.1","Accept":"text/html,*/*"})
    raw,final=request_bytes(req,MAX_TEXT,f"{kind} BLS {date}")
    host=(urllib.parse.urlparse(final).hostname or "").lower()
    if host not in {"www.bls.gov","bls.gov"}: fail(f"unexpected BLS host: {host}")
    text=re.sub(r"\s+"," ",html.unescape(raw.decode("utf-8",errors="replace"))).lower()
    checks={"date":date_text.lower() in text,"title":title.lower() in text,"time":"08:30 am" in text}
    if not all(checks.values()): fail(f"BLS metadata mismatch {kind} {date}: {checks}")
    return {"pass":True,"url":url,"checks":checks,"response_bytes":len(raw)}

def day_ms(date:str):
    d=datetime.strptime(date,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    b=int(d.timestamp()*1000); return b,b+86_400_000
def walk(node):
    if isinstance(node,dict):
        yield node
        for v in node.values(): yield from walk(v)
    elif isinstance(node,list):
        for v in node: yield from walk(v)
def trusted(url,basename):
    p=urllib.parse.urlparse(url)
    return p.scheme=="https" and (p.hostname or "").lower()==OKX_STATIC_HOST and Path(p.path).name==basename

def resolve(date):
    begin,end=day_ms(date); basename=f"BTC-USDT-SWAP-trades-{date}.zip"
    payload={"module":"1","instType":"SWAP","instQueryParam":{"instFamilyList":[OKX_FAMILY]},"dateQuery":{"dateAggrType":"daily","begin":str(begin),"end":str(end-1)}}
    body=json.dumps(payload,separators=(",",":")).encode()
    last=None
    for domain in OKX_DOMAINS:
        try:
            req=urllib.request.Request(domain+"/priapi/v5/broker/public/trade-data/download-link?t="+str(int(time.time()*1000)),data=body,method="POST",headers={"User-Agent":"BotMarketplace-SC001-C11-D1/0.1","Accept":"application/json,*/*","Content-Type":"application/json","Referer":"https://www.okx.com/historical-data"})
            raw,final=request_bytes(req,MAX_JSON,f"OKX metadata {date}")
            host=(urllib.parse.urlparse(final).hostname or "").lower()
            if host not in {"www.okx.com","us.okx.com"}: fail(f"bad metadata host {host}")
            obj=json.loads(raw.decode())
            if str(obj.get("code"))!="0": fail("OKX code mismatch")
            found=[]
            for n in walk(obj.get("data")):
                if isinstance(n,dict):
                    fn=n.get("filename") or n.get("fileName"); u=n.get("url")
                    if fn==basename and isinstance(u,str) and trusted(u,basename) and u not in found: found.append(u)
            if len(found)==1: return basename,found[0]
            if len(found)>1: fail(f"multiple exact urls {date}")
            last=RuntimeError(f"exact archive missing {date}")
        except Exception as exc: last=exc
    raise RuntimeError(f"archive resolution failed {date}: {type(last).__name__}: {last}")

def head(url,basename):
    last=None
    for a in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"BotMarketplace-SC001-C11-D1/0.1","Referer":"https://www.okx.com/historical-data"})
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                final=resp.geturl(); cl=resp.headers.get("Content-Length"); status=int(getattr(resp,"status",200))
            if status!=200 or not trusted(final,basename) or not cl or not cl.isdigit() or int(cl)<=0: fail(f"HEAD mismatch {basename}")
            return int(cl)
        except Exception as exc:
            last=exc
            if a<RETRIES: time.sleep(float(a))
    raise RuntimeError(f"HEAD failed {basename}: {last}")

def main():
    try:
        require_freeze(); OUT_DIR.mkdir(parents=True,exist_ok=True); rows=[]
        for i,(kind,date,utc,url,title,date_text) in enumerate(EVENTS,1):
            print(f"C11-D1 [{i}/12] {kind} {date}",flush=True)
            bls=verify_bls(kind,date,url,title,date_text)
            basename,u=resolve(date); size=head(u,basename)
            rows.append({"kind":kind,"date":date,"frozen_utc":utc,"bls":bls,"archive":{"filename":basename,"content_length":size}})
            print(f"PASS {kind} {date} archive_bytes={size}",flush=True)
        report={"stage":STAGE,"version":"0.1","status":PASS,"window":"2025-01-01_to_2025-06-30","events":rows,"events_verified":len(rows),"historical_trade_body_downloaded":False,"historical_trade_body_opened":False,"macro_release_value_accessed":False,"macro_surprise_calculated":False,"first_impulse_calculated":False,"post_release_move_calculated":False,"strategy_signal_calculated":False,"pnl_calculated":False,"promotional_alpha_accessed":False}
        atomic_json(OUT,report)
        print(PASS); print("events_verified =",len(rows),"/ 12"); print("historical trade body downloaded/opened = False / False"); print("macro value/surprise/impulse/move/signal/PnL = False"); print("promotional alpha accessed = False"); print("report =",OUT)
        return 0
    except Exception as exc:
        print(REVIEW); print("error =",f"{type(exc).__name__}: {exc}"); return 2
if __name__=="__main__": raise SystemExit(main())
