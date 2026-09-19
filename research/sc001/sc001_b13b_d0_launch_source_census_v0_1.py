from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

STAGE="SC001-B13B-D0-LAUNCH-SOURCE-CENSUS-V0.1"
PASS="B13B_D0_SOURCE_FEASIBILITY_PASS_SURVIVOR_CENSORED"
REVIEW="B13B_D0_SOURCE_FEASIBILITY_REVIEW"

WINDOW_START_MS=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
WINDOW_END_MS=int(datetime(2026,9,1,tzinfo=timezone.utc).timestamp()*1000)
MATURE_REFERENCE_DAYS=90
MIN_MATURE_EVENTS=6
MIN_LAUNCH_MONTHS=3
MIN_DUAL_SOURCE_READY=5

OKX_DOMAINS=("https://www.okx.com","https://us.okx.com")
OKX_STATIC="static.okx.com"
BYBIT_BASE="https://api.bybit.com"
BYBIT_PUBLIC="https://public.bybit.com"

TIMEOUT=60
RETRIES=3
MAX_JSON=8_000_000

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-b13b-d0-launch-source-census-protocol-v0.1.md"
FREEZE=ROOT/"docs/research/sc001-b13b-d0-launch-source-census-implementation-freeze-v0.1.json"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_B13B_D0_SOURCE_CENSUS"
OUT=OUT_DIR/"sc001_b13b_d0_launch_source_census_v0_1.json"

BASE_RE=re.compile(r"^([A-Z0-9]+)-USDT-SWAP$")

def fail(msg:str)->None:
    raise RuntimeError(msg)

def load_json(path:Path)->dict:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail(f"JSON object expected: {path}")
    return obj

def atomic_json(path:Path,obj:object)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(str(path)+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)

def git_blob(path:Path)->str:
    return subprocess.check_output(
        ["git","-C",str(ROOT),"hash-object",str(path.relative_to(ROOT))],
        text=True
    ).strip()

def require_freeze()->None:
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_B13B_D0_RUN":
        fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()):
        fail("runner identity mismatch")
    if fr.get("protocol_git_blob_sha")!=git_blob(PROTOCOL):
        fail("protocol identity mismatch")
    if int(fr.get("window_start_ms",-1))!=WINDOW_START_MS or int(fr.get("window_end_ms",-1))!=WINDOW_END_MS:
        fail("window mismatch")
    if int(fr.get("mature_reference_days",-1))!=MATURE_REFERENCE_DAYS:
        fail("mature reference mismatch")
    for key in (
        "historical_trade_body_download_authorized",
        "historical_trade_body_open_authorized",
        "price_access_authorized",
        "relative_basis_authorized",
        "launch_dislocation_authorized",
        "strategy_signal_authorized",
        "execution_model_authorized",
        "pnl_authorized",
        "candidate_id_assignment_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(key) is not False:
            fail(f"firewall mismatch: {key}")

def request_json(url:str,label:str)->dict:
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"BotMarketplace-SC001-B13B-D0/0.1",
                "Accept":"application/json",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_JSON+1)
                status=int(getattr(resp,"status",200))
                final=resp.geturl()
            if status!=200:
                fail(f"{label} HTTP {status}")
            if len(raw)>MAX_JSON:
                fail(f"{label} response cap")
            obj=json.loads(raw.decode("utf-8"))
            return obj
        except Exception as exc:
            last=exc
            if attempt<RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} request failed: {type(last).__name__}: {last}")

def okx_get(path:str,params:dict[str,str])->dict:
    query=urllib.parse.urlencode(params)
    last=None
    for domain in OKX_DOMAINS:
        try:
            obj=request_json(domain+path+"?"+query,"OKX")
            if str(obj.get("code"))!="0":
                fail(f"OKX code mismatch: {obj.get('code')}")
            return obj
        except Exception as exc:
            last=exc
    raise RuntimeError(f"OKX request failed: {last}")

def bybit_get(path:str,params:dict[str,str])->dict:
    obj=request_json(BYBIT_BASE+path+"?"+urllib.parse.urlencode(params),"Bybit")
    if int(obj.get("retCode",-1))!=0:
        fail(f"Bybit retCode mismatch: {obj.get('retCode')} {obj.get('retMsg')}")
    return obj

def get_okx_launches()->list[dict]:
    obj=okx_get("/api/v5/public/instruments",{"instType":"SWAP"})
    rows=obj.get("data") or []
    out=[]
    for r in rows:
        if not isinstance(r,dict):
            continue
        inst=r.get("instId")
        m=BASE_RE.fullmatch(inst or "")
        if not m:
            continue
        try:
            list_ms=int(str(r.get("listTime") or "0"))
        except Exception:
            continue
        if not (WINDOW_START_MS<=list_ms<WINDOW_END_MS):
            continue
        if r.get("state")!="live":
            continue
        if r.get("settleCcy")!="USDT":
            continue
        if r.get("ctType")!="linear":
            continue
        out.append({
            "base":m.group(1),
            "instId":inst,
            "listTime_ms":list_ms,
            "listTime_utc":datetime.fromtimestamp(list_ms/1000,tz=timezone.utc).isoformat(),
            "uly":r.get("uly"),
            "instFamily":r.get("instFamily"),
        })
    out.sort(key=lambda x:(x["listTime_ms"],x["instId"]))
    return out

def get_bybit_instruments()->dict[str,dict]:
    out={}
    cursor=""
    seen=set()
    for page_no in range(1,20):
        params={"category":"linear","limit":"1000"}
        if cursor:
            params["cursor"]=cursor
        obj=bybit_get("/v5/market/instruments-info",params)
        result=obj.get("result") or {}
        rows=result.get("list") or []
        for r in rows:
            if not isinstance(r,dict):
                continue
            sym=r.get("symbol")
            if not isinstance(sym,str):
                continue
            if r.get("contractType")!="LinearPerpetual":
                continue
            if r.get("quoteCoin")!="USDT":
                continue
            if r.get("status")!="Trading":
                continue
            try:
                launch=int(str(r.get("launchTime") or "0"))
            except Exception:
                continue
            if launch<=0:
                continue
            out[sym]={
                "symbol":sym,
                "baseCoin":r.get("baseCoin"),
                "launchTime_ms":launch,
                "launchTime_utc":datetime.fromtimestamp(launch/1000,tz=timezone.utc).isoformat(),
            }
        nxt=str(result.get("nextPageCursor") or "")
        if not nxt or nxt in seen:
            break
        seen.add(nxt); cursor=nxt
    else:
        fail("Bybit instrument pagination cap")
    return out

def walk(node):
    if isinstance(node,dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node,list):
        for v in node:
            yield from walk(v)

def trusted_okx_archive(url:str,basename:str)->bool:
    p=urllib.parse.urlparse(url)
    return p.scheme=="https" and (p.hostname or "").lower()==OKX_STATIC and Path(p.path).name==basename

def day_ms(date_text:str)->tuple[int,int]:
    d=datetime.strptime(date_text,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    b=int(d.timestamp()*1000)
    return b,b+86_400_000

def resolve_okx_trade_archive(inst:str,base:str,date_text:str)->tuple[str,str]:
    begin,end=day_ms(date_text)
    basename=f"{inst}-trades-{date_text}.zip"
    payload={
        "module":"1",
        "instType":"SWAP",
        "instQueryParam":{"instFamilyList":[f"{base}-USDT"]},
        "dateQuery":{"dateAggrType":"daily","begin":str(begin),"end":str(end-1)},
    }
    body=json.dumps(payload,separators=(",",":")).encode()
    last=None
    for domain in OKX_DOMAINS:
        try:
            req=urllib.request.Request(
                domain+"/priapi/v5/broker/public/trade-data/download-link?t="+str(int(time.time()*1000)),
                data=body,method="POST",
                headers={
                    "User-Agent":"BotMarketplace-SC001-B13B-D0/0.1",
                    "Accept":"application/json,*/*",
                    "Content-Type":"application/json",
                    "Referer":"https://www.okx.com/historical-data",
                },
            )
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_JSON+1)
            if len(raw)>MAX_JSON:
                fail("OKX trade metadata cap")
            obj=json.loads(raw.decode("utf-8"))
            if str(obj.get("code"))!="0":
                fail(f"OKX trade metadata code mismatch {inst}")
            found=[]
            for n in walk(obj.get("data")):
                if not isinstance(n,dict):
                    continue
                fn=n.get("filename") or n.get("fileName")
                url=n.get("url") or n.get("fileUrl") or n.get("downloadUrl")
                if fn==basename and isinstance(url,str) and trusted_okx_archive(url,basename) and url not in found:
                    found.append(url)
            if len(found)==1:
                return basename,found[0]
            if len(found)>1:
                fail(f"multiple exact OKX launch-day URLs {inst} {date_text}")
            last=RuntimeError(f"exact OKX launch-day archive missing {basename}")
        except Exception as exc:
            last=exc
    raise RuntimeError(f"OKX archive resolution failed {inst} {date_text}: {last}")

def head_url(url:str,expected_host:str|None=None,expected_basename:str|None=None)->tuple[bool,int|None,str|None]:
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,method="HEAD",headers={
                "User-Agent":"BotMarketplace-SC001-B13B-D0/0.1",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                status=int(getattr(resp,"status",200))
                final=resp.geturl()
                cl=resp.headers.get("Content-Length")
            if status!=200:
                return False,None,final
            p=urllib.parse.urlparse(final)
            if expected_host and (p.hostname or "").lower()!=expected_host:
                return False,None,final
            if expected_basename and Path(p.path).name!=expected_basename:
                return False,None,final
            if not cl or not cl.isdigit() or int(cl)<=0:
                return False,None,final
            return True,int(cl),final
        except Exception as exc:
            last=exc
            if attempt<RETRIES:
                time.sleep(float(attempt))
    return False,None,None

def main()->int:
    try:
        require_freeze()
        OUT_DIR.mkdir(parents=True,exist_ok=True)

        okx=get_okx_launches()
        bybit=get_bybit_instruments()

        mature=[]
        rows=[]
        for e in okx:
            ref=bybit.get(e["base"]+"USDT")
            reference_ok=False
            age_days=None
            if ref:
                age_days=(e["listTime_ms"]-ref["launchTime_ms"])/86_400_000.0
                reference_ok=age_days>=MATURE_REFERENCE_DAYS
            if not reference_ok:
                rows.append({
                    **e,
                    "bybit_symbol":ref["symbol"] if ref else None,
                    "bybit_launchTime_ms":ref["launchTime_ms"] if ref else None,
                    "reference_age_days":age_days,
                    "mature_reference":False,
                    "okx_launch_day_archive_pass":False,
                    "bybit_launch_day_archive_pass":False,
                    "dual_source_ready":False,
                })
                continue

            date_text=datetime.fromtimestamp(e["listTime_ms"]/1000,tz=timezone.utc).strftime("%Y-%m-%d")
            okx_pass=False; okx_bytes=None; okx_file=None
            try:
                okx_file,okx_url=resolve_okx_trade_archive(e["instId"],e["base"],date_text)
                okx_pass,okx_bytes,_=head_url(okx_url,OKX_STATIC,okx_file)
            except Exception:
                okx_pass=False

            bybit_symbol=ref["symbol"]
            bybit_file=f"{bybit_symbol}{date_text}.csv.gz"
            bybit_url=f"{BYBIT_PUBLIC}/trading/{bybit_symbol}/{bybit_file}"
            bybit_pass,bybit_bytes,_=head_url(bybit_url,"public.bybit.com",bybit_file)

            row={
                **e,
                "bybit_symbol":bybit_symbol,
                "bybit_launchTime_ms":ref["launchTime_ms"],
                "bybit_launchTime_utc":ref["launchTime_utc"],
                "reference_age_days":age_days,
                "mature_reference":True,
                "launch_date_utc":date_text,
                "okx_launch_day_archive_file":okx_file,
                "okx_launch_day_archive_pass":okx_pass,
                "okx_launch_day_archive_bytes":okx_bytes,
                "bybit_launch_day_archive_file":bybit_file,
                "bybit_launch_day_archive_pass":bybit_pass,
                "bybit_launch_day_archive_bytes":bybit_bytes,
                "dual_source_ready":bool(okx_pass and bybit_pass),
            }
            rows.append(row)
            mature.append(row)

        months=sorted({datetime.fromtimestamp(r["listTime_ms"]/1000,tz=timezone.utc).strftime("%Y-%m") for r in mature})
        dual=[r for r in mature if r["dual_source_ready"]]

        gates={
            "mature_reference_events_gte6":len(mature)>=MIN_MATURE_EVENTS,
            "launch_months_gte3":len(months)>=MIN_LAUNCH_MONTHS,
            "dual_source_ready_gte5":len(dual)>=MIN_DUAL_SOURCE_READY,
        }
        status=PASS if all(gates.values()) else REVIEW

        report={
            "stage":STAGE,
            "version":"0.1",
            "status":status,
            "census_window":{"start_ms":WINDOW_START_MS,"end_exclusive_ms":WINDOW_END_MS},
            "mature_reference_days":MATURE_REFERENCE_DAYS,
            "historical_launch_universe_complete":False,
            "survivor_censored_current_instrument_census":True,
            "raw_okx_launches_in_window":len(okx),
            "mature_reference_events":len(mature),
            "mature_reference_launch_months":months,
            "dual_source_ready_events":len(dual),
            "gates":gates,
            "events":rows,
            "historical_trade_body_downloaded":False,
            "historical_trade_body_opened":False,
            "price_accessed":False,
            "relative_basis_calculated":False,
            "launch_dislocation_calculated":False,
            "strategy_signal_calculated":False,
            "execution_model_calculated":False,
            "pnl_calculated":False,
            "candidate_id_assigned":False,
            "promotional_alpha_accessed":False,
        }
        atomic_json(OUT,report)

        print(status)
        print("raw_okx_launches_in_window =",len(okx))
        print("mature_reference_events =",len(mature))
        print("launch_months =",months)
        print("dual_source_ready_events =",len(dual))
        print("historical_launch_universe_complete = False")
        print("survivor_censored_current_instrument_census = True")
        print("gates =",gates)
        print("trade bodies/price/basis/dislocation/PnL = False")
        print("candidate_id_assigned = False")
        print("report =",OUT)
        return 0 if status==PASS else 2
    except Exception as exc:
        print("B13B_D0_IMPLEMENTATION_FAIL")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

if __name__=="__main__":
    raise SystemExit(main())
