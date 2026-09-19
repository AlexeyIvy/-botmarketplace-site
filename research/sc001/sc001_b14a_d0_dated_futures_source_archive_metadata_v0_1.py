from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE="SC001-B14A-D0-DATED-FUTURES-SOURCE-ARCHIVE-METADATA-V0.1"
PASS="B14A_D0_SOURCE_ARCHIVE_METADATA_PASS"
REVIEW="B14A_D0_SOURCE_ARCHIVE_METADATA_REVIEW"
SELFTEST_PASS="B14A_D0_SELF_TEST_PASS"
SELFTEST_REVIEW="B14A_D0_SELF_TEST_REVIEW"

FAMILIES=("BTC-USDT","ETH-USDT")
HEDGES={"BTC-USDT":"BTC-USDT-SWAP","ETH-USDT":"ETH-USDT-SWAP"}

OKX_DOMAINS=("https://www.okx.com","https://us.okx.com")
OKX_STATIC="static.okx.com"
TIMEOUT=60
RETRIES=3
MAX_JSON=8_000_000

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-b14a-d0-dated-futures-source-archive-metadata-protocol-v0.1.md"
SOURCE_AUDIT=ROOT/"docs/research/sc001-b14a-okx-dated-futures-source-settlement-spec-audit-v0.1.md"
FREEZE=ROOT/"docs/research/sc001-b14a-d0-implementation-freeze-v0.1.json"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_B14A_D0_SOURCE_ARCHIVE"
OUT=OUT_DIR/"sc001_b14a_d0_source_archive_metadata_v0_1.json"

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
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp,path)

def git_blob(path:Path)->str:
    return subprocess.check_output(
        ["git","-C",str(ROOT),"hash-object",str(path.relative_to(ROOT))],
        text=True,
    ).strip()

def require_freeze()->dict:
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_B14A_D0_RUN":
        fail("freeze status mismatch")
    checks={
        "runner_git_blob_sha":git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha":git_blob(PROTOCOL),
        "source_audit_git_blob_sha":git_blob(SOURCE_AUDIT),
    }
    for k,v in checks.items():
        if fr.get(k)!=v:
            fail(f"freeze identity mismatch: {k}")
    if tuple(fr.get("families") or ())!=FAMILIES:
        fail("family freeze mismatch")
    for k in (
        "futures_trade_body_download_authorized",
        "futures_trade_body_open_authorized",
        "swap_trade_body_open_authorized",
        "price_access_authorized",
        "basis_authorized",
        "estimated_settlement_price_authorized",
        "delivery_price_authorized",
        "convergence_authorized",
        "strategy_signal_authorized",
        "execution_model_authorized",
        "pnl_authorized",
        "candidate_id_assignment_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"firewall mismatch: {k}")
    return fr

def request_json(url:str,label:str)->dict:
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"BotMarketplace-SC001-B14A-D0/0.1",
                "Accept":"application/json",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_JSON+1)
                status=int(getattr(resp,"status",200))
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
    q=urllib.parse.urlencode(params)
    last=None
    for domain in OKX_DOMAINS:
        try:
            obj=request_json(domain+path+("?" + q if q else ""),"OKX")
            if not isinstance(obj,dict) or str(obj.get("code"))!="0":
                fail(f"OKX code mismatch path={path} code={obj.get('code') if isinstance(obj,dict) else None}")
            return obj
        except Exception as exc:
            last=exc
    raise RuntimeError(f"OKX request failed {path}: {last}")

def future_rows()->list[dict]:
    obj=okx_get("/api/v5/public/instruments",{"instType":"FUTURES"})
    rows=obj.get("data") or []
    out=[]
    now=now_ms()
    for r in rows:
        if not isinstance(r,dict):
            continue
        if r.get("instFamily") not in FAMILIES:
            continue
        try:
            list_ms=int(str(r.get("listTime") or "0"))
            exp_ms=int(str(r.get("expTime") or "0"))
        except Exception:
            continue
        semantic_pass=(
            r.get("instType")=="FUTURES"
            and r.get("ruleType")=="normal"
            and str(r.get("instCategory") or "")=="1"
            and r.get("ctType")=="linear"
            and r.get("settleCcy")=="USDT"
            and r.get("state") in {"live","preopen"}
            and list_ms>0
            and exp_ms>now
            and exp_ms>list_ms
            and str(r.get("ctVal") or "")!=""
            and str(r.get("ctMult") or "")!=""
            and str(r.get("ctValCcy") or "")!=""
        )
        if not semantic_pass:
            continue
        out.append({
            "instId":r.get("instId"),
            "instFamily":r.get("instFamily"),
            "listTime_ms":list_ms,
            "listTime_utc":iso_ms(list_ms),
            "expTime_ms":exp_ms,
            "expTime_utc":iso_ms(exp_ms),
            "state":r.get("state"),
            "ruleType":r.get("ruleType"),
            "futureSettlement":r.get("futureSettlement"),
            "ctVal":r.get("ctVal"),
            "ctMult":r.get("ctMult"),
            "ctValCcy":r.get("ctValCcy"),
            "settleCcy":r.get("settleCcy"),
            "ctType":r.get("ctType"),
            "instCategory":r.get("instCategory"),
            "groupId":r.get("groupId"),
        })
    out.sort(key=lambda x:(x["instFamily"],x["expTime_ms"],x["instId"]))
    return out

def hedge_rows()->dict[str,dict]:
    out={}
    for family,inst in HEDGES.items():
        obj=okx_get("/api/v5/public/instruments",{"instType":"SWAP","instId":inst})
        rows=obj.get("data") or []
        exact=[r for r in rows if isinstance(r,dict) and r.get("instId")==inst]
        if len(exact)!=1:
            fail(f"hedge row mismatch {inst}: {len(exact)}")
        r=exact[0]
        passed=(
            r.get("instType")=="SWAP"
            and r.get("ctType")=="linear"
            and r.get("settleCcy")=="USDT"
            and str(r.get("instCategory") or "")=="1"
            and r.get("state")=="live"
        )
        out[family]={
            "instId":inst,
            "pass":passed,
            "ctVal":r.get("ctVal"),
            "ctMult":r.get("ctMult"),
            "ctValCcy":r.get("ctValCcy"),
            "settleCcy":r.get("settleCcy"),
            "ctType":r.get("ctType"),
            "instCategory":r.get("instCategory"),
            "state":r.get("state"),
        }
    return out

def now_ms()->int:
    return int(time.time()*1000)

def iso_ms(ms:int)->str:
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()

def day_bounds_ms(ds:str)->tuple[int,int]:
    d=datetime.strptime(ds,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    b=int(d.timestamp()*1000)
    return b,b+86_400_000

def yesterday_utc_date()->str:
    return (datetime.now(timezone.utc).date()-timedelta(days=1)).isoformat()

def walk(node):
    if isinstance(node,dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node,list):
        for v in node:
            yield from walk(v)

def trusted_archive(url:str,basename:str)->bool:
    p=urllib.parse.urlparse(url)
    return (
        p.scheme=="https"
        and (p.hostname or "").lower()==OKX_STATIC
        and Path(p.path).name==basename
    )

def resolve_trade_archive(inst_id:str,family:str,date_text:str)->tuple[str,str]:
    b,e=day_bounds_ms(date_text)
    basename=f"{inst_id}-trades-{date_text}.zip"
    payload={
        "module":"1",
        "instType":"FUTURES",
        "instQueryParam":{"instFamilyList":[family]},
        "dateQuery":{"dateAggrType":"daily","begin":str(b),"end":str(e-1)},
    }
    body=json.dumps(payload,separators=(",",":")).encode()
    last=None
    for domain in OKX_DOMAINS:
        try:
            req=urllib.request.Request(
                domain+"/priapi/v5/broker/public/trade-data/download-link?t="+str(now_ms()),
                data=body,
                method="POST",
                headers={
                    "User-Agent":"BotMarketplace-SC001-B14A-D0/0.1",
                    "Accept":"application/json,*/*",
                    "Content-Type":"application/json",
                    "Referer":"https://www.okx.com/historical-data",
                },
            )
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_JSON+1)
            if len(raw)>MAX_JSON:
                fail("archive metadata response cap")
            obj=json.loads(raw.decode("utf-8"))
            if str(obj.get("code"))!="0":
                fail(f"archive metadata code mismatch {inst_id}: {obj.get('code')}")
            found=[]
            for n in walk(obj.get("data")):
                if not isinstance(n,dict):
                    continue
                fn=n.get("filename") or n.get("fileName")
                url=n.get("url") or n.get("fileUrl") or n.get("downloadUrl")
                if fn==basename and isinstance(url,str) and trusted_archive(url,basename) and url not in found:
                    found.append(url)
            if len(found)==1:
                return basename,found[0]
            if len(found)>1:
                fail(f"multiple exact archive URLs {inst_id} {date_text}")
            last=RuntimeError(f"exact archive missing {basename}")
        except Exception as exc:
            last=exc
    raise RuntimeError(f"archive resolution failed {inst_id} {date_text}: {last}")

def head_archive(url:str,basename:str)->int:
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(
                url,
                method="HEAD",
                headers={
                    "User-Agent":"BotMarketplace-SC001-B14A-D0/0.1",
                    "Referer":"https://www.okx.com/historical-data",
                },
            )
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                status=int(getattr(resp,"status",200))
                final=resp.geturl()
                cl=resp.headers.get("Content-Length")
            if status!=200 or not trusted_archive(final,basename):
                fail(f"archive HEAD identity/status mismatch {basename}")
            if not cl or not cl.isdigit() or int(cl)<=0:
                fail(f"archive Content-Length invalid {basename}")
            return int(cl)
        except Exception as exc:
            last=exc
            if attempt<RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"archive HEAD failed {basename}: {last}")

def choose_probe(contract:dict)->dict:
    probe_date=yesterday_utc_date()
    probe_start=int(datetime.strptime(probe_date,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
    if int(contract["listTime_ms"])>=probe_start:
        return {
            "probe_state":"ARCHIVE_PROBE_NOT_YET_ELIGIBLE",
            "probe_date":probe_date,
            "archive_pass":False,
            "archive_file":None,
            "content_length":None,
        }
    try:
        fn,url=resolve_trade_archive(contract["instId"],contract["instFamily"],probe_date)
        size=head_archive(url,fn)
        return {
            "probe_state":"ARCHIVE_METADATA_PASS",
            "probe_date":probe_date,
            "archive_pass":True,
            "archive_file":fn,
            "content_length":size,
        }
    except Exception as exc:
        return {
            "probe_state":"ARCHIVE_METADATA_REVIEW",
            "probe_date":probe_date,
            "archive_pass":False,
            "archive_file":None,
            "content_length":None,
            "error":f"{type(exc).__name__}: {exc}",
        }

def self_test()->int:
    try:
        require_freeze()
        if len(FAMILIES)!=2 or set(HEDGES)!=set(FAMILIES):
            fail("static family/hedge fixture mismatch")
        good="BTC-USDT-261225-trades-2026-09-18.zip"
        if Path("/x/"+good).name!=good:
            fail("basename fixture failed")
        print(SELFTEST_PASS)
        print("families =",list(FAMILIES))
        print("hedges =",HEDGES)
        print("price outcomes = CLOSED")
        return 0
    except Exception as exc:
        print(SELFTEST_REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def run()->int:
    try:
        require_freeze()
        futures=future_rows()
        hedges=hedge_rows()

        by_family={f:[] for f in FAMILIES}
        for c in futures:
            by_family[c["instFamily"]].append(c)

        for c in futures:
            c["archive_probe"]=choose_probe(c)

        counts={f:len(by_family[f]) for f in FAMILIES}
        archive_pass_counts={
            f:sum(1 for c in by_family[f] if c["archive_probe"]["archive_pass"])
            for f in FAMILIES
        }

        gates={
            "btc_future_contracts_gte2":counts["BTC-USDT"]>=2,
            "eth_future_contracts_gte2":counts["ETH-USDT"]>=2,
            "btc_swap_hedge_pass":bool(hedges["BTC-USDT"]["pass"]),
            "eth_swap_hedge_pass":bool(hedges["ETH-USDT"]["pass"]),
            "btc_future_archive_pass_gte1":archive_pass_counts["BTC-USDT"]>=1,
            "eth_future_archive_pass_gte1":archive_pass_counts["ETH-USDT"]>=1,
        }

        status=PASS if all(gates.values()) else REVIEW

        rep={
            "stage":STAGE,
            "version":"0.1",
            "status":status,
            "run_time_utc":datetime.now(timezone.utc).isoformat(),
            "probe_date_utc":yesterday_utc_date(),
            "families":list(FAMILIES),
            "future_contracts":futures,
            "future_contract_counts":counts,
            "archive_pass_counts":archive_pass_counts,
            "hedges":hedges,
            "gates":gates,
            "futures_trade_body_downloaded":False,
            "futures_trade_body_opened":False,
            "swap_trade_body_opened":False,
            "price_accessed":False,
            "basis_calculated":False,
            "estimated_settlement_price_accessed":False,
            "delivery_price_accessed":False,
            "convergence_calculated":False,
            "strategy_signal_calculated":False,
            "execution_model_calculated":False,
            "pnl_calculated":False,
            "candidate_id_assigned":False,
        }
        atomic_json(OUT,rep)

        print(status)
        print("future_contract_counts =",counts)
        print("archive_pass_counts =",archive_pass_counts)
        print("hedges =",{k:v["pass"] for k,v in hedges.items()})
        print("gates =",gates)
        print("price/basis/settlePx/deliveryPx/convergence/PnL = False")
        print("candidate_id_assigned = False")
        print("report =",OUT)
        return 0 if status==PASS else 2

    except Exception as exc:
        print(REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","run"),required=True)
    args=ap.parse_args()
    return self_test() if args.mode=="self-test" else run()

if __name__=="__main__":
    raise SystemExit(main())
