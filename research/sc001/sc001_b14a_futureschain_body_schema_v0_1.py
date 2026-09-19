from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE="SC001-B14A-FUTURESCHAIN-BODY-SCHEMA-QUALIFICATION-V0.1"
PASS="B14A_FUTURESCHAIN_BODY_SCHEMA_PASS"
REVIEW="B14A_FUTURESCHAIN_BODY_SCHEMA_REVIEW"
SELFTEST_PASS="B14A_CHAIN_SCHEMA_SELF_TEST_PASS"
SELFTEST_REVIEW="B14A_CHAIN_SCHEMA_SELF_TEST_REVIEW"

D0_SHA="a7a36245ee668450960873e22f0ce515c95e6c990564fa8df4fedf97d6fbd5e8"
PROBE_DATE="2026-09-16"

FAMILIES={
    "BTC-USD":{
        "archive":"BTC-USD-futureschain-trades-2026-09-16.zip",
        "target":"BTC-USD-260925",
        "pattern":re.compile(r"^BTC-USD-[0-9]{6}$"),
    },
    "ETH-USD":{
        "archive":"ETH-USD-futureschain-trades-2026-09-16.zip",
        "target":"ETH-USD-260925",
        "pattern":re.compile(r"^ETH-USD-[0-9]{6}$"),
    },
}

HEADER6=("instrument_name","trade_id","side","price","size","created_time")
HEADER7=("instrument_name","trade_id","side","price","size","created_time","source")

OKX_DOMAINS=("https://www.okx.com","https://us.okx.com")
OKX_STATIC="static.okx.com"
TIMEOUT=60
RETRIES=3
MAX_JSON=8_000_000
MAX_FILE=100*1024*1024
CHUNK=1024*1024

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-b14a-futureschain-body-schema-qualification-protocol-v0.1.md"
IDENTITY_FREEZE=ROOT/"docs/research/sc001-b14a-exact-12-future-expiry-identity-freeze-v0.1.json"
REGISTRY=ROOT/"docs/research/sc001-contamination-registry-v0.27.json"
FREEZE=ROOT/"docs/research/sc001-b14a-futureschain-body-schema-implementation-freeze-v0.1.json"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
D0=DATA_ROOT/"SC001_B14A_D0_SOURCE_ARCHIVE"/"sc001_b14a_d0_source_archive_metadata_v0_8.json"
OUT_DIR=DATA_ROOT/"SC001_B14A_CHAIN_SCHEMA"
ARCH_DIR=OUT_DIR/"archives"
OUT=OUT_DIR/"sc001_b14a_futureschain_body_schema_v0_1.json"

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

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def git_blob(path:Path)->str:
    return subprocess.check_output(
        ["git","-C",str(ROOT),"hash-object",str(path.relative_to(ROOT))],
        text=True,
    ).strip()

def require_freeze()->dict:
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_B14A_CHAIN_SCHEMA_RUN":
        fail("freeze status mismatch")
    checks={
        "runner_git_blob_sha":git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha":git_blob(PROTOCOL),
        "identity_freeze_git_blob_sha":git_blob(IDENTITY_FREEZE),
        "contamination_registry_git_blob_sha":git_blob(REGISTRY),
    }
    for k,v in checks.items():
        if fr.get(k)!=v:
            fail(f"freeze identity mismatch: {k}")
    if fr.get("canonical_d0_report_sha256")!=D0_SHA:
        fail("canonical D0 SHA freeze mismatch")
    if fr.get("probe_date")!=PROBE_DATE:
        fail("probe date mismatch")
    if tuple(fr.get("families") or ())!=tuple(FAMILIES):
        fail("family freeze mismatch")
    for k in (
        "price_value_parse_or_store_authorized",
        "basis_authorized",
        "return_authorized",
        "settlePx_authorized",
        "delivery_price_authorized",
        "convergence_authorized",
        "strategy_signal_authorized",
        "execution_model_authorized",
        "pnl_authorized",
        "candidate_id_assignment_authorized",
        "promotional_evidence_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"firewall mismatch: {k}")

    reg=load_json(REGISTRY).get("b14a_body_schema_qualification") or {}
    if reg.get("classification")!="ENGINEERING_SOURCE_SCHEMA_QUALIFICATION":
        fail("registry role mismatch")
    for k in (
        "futureschain_body_download_authorized",
        "futureschain_body_open_authorized",
        "header_schema_access_authorized",
        "instrument_name_column_access_authorized",
    ):
        if reg.get(k) is not True:
            fail(f"registry authorization mismatch: {k}")
    if reg.get("price_value_parse_or_store_authorized") is not False:
        fail("registry price firewall mismatch")

    if not D0.exists():
        fail(f"canonical D0 report missing: {D0}")
    if sha256_file(D0)!=D0_SHA:
        fail("canonical D0 report SHA mismatch")
    d0=load_json(D0)
    if d0.get("status")!="B14A_D0_V08_SOURCE_ARCHIVE_METADATA_PASS":
        fail("canonical D0 status mismatch")
    return d0

def request_json(url:str,label:str)->dict:
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"BotMarketplace-SC001-B14A-ChainSchema/0.1",
                "Accept":"application/json",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_JSON+1)
                status=int(getattr(resp,"status",200))
            if status!=200:
                fail(f"{label} HTTP {status}")
            if len(raw)>MAX_JSON:
                fail(f"{label} response cap")
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            last=exc
            if attempt<RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} request failed: {type(last).__name__}: {last}")

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

def day_bounds(day:str)->tuple[int,int]:
    d=datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo=int(d.timestamp()*1000)
    return lo,lo+86_400_000

def resolve_archive(family:str,basename:str)->tuple[str,dict]:
    label=datetime.strptime(PROBE_DATE,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    qdays=(("LABEL_DAY",label),("PREVIOUS_DAY",label-timedelta(days=1)))
    attempts=[]
    unique=[]

    for qlabel,qd in qdays:
        lo=int(qd.timestamp()*1000); hi=lo+86_400_000
        params={
            "module":"1",
            "instType":"FUTURES",
            "instFamilyList":family,
            "dateAggrType":"daily",
            "begin":str(lo),
            "end":str(hi),
        }
        query=urllib.parse.urlencode(params)
        found=[]
        last_error=None
        for domain in OKX_DOMAINS:
            try:
                obj=request_json(domain+"/api/v5/public/market-data-history?"+query,"OKX historical metadata")
                if not isinstance(obj,dict) or str(obj.get("code"))!="0":
                    fail(f"OKX metadata code mismatch family={family}")
                for node in walk(obj.get("data")):
                    if not isinstance(node,dict):
                        continue
                    fn=node.get("filename") or node.get("fileName")
                    u=node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
                    if fn==basename and isinstance(u,str) and trusted_archive(u,basename) and u not in found:
                        found.append(u)
            except Exception as exc:
                last_error=f"{type(exc).__name__}: {exc}"
        attempts.append({
            "query_label":qlabel,
            "query_date":qd.strftime("%Y-%m-%d"),
            "exact_trusted_url_count":len(found),
            "last_error":last_error,
        })
        for u in found:
            if u not in unique:
                unique.append(u)
        if unique:
            break

    if len(unique)!=1:
        fail(f"exact archive resolution count={len(unique)} family={family} basename={basename}")
    return unique[0],{"selected_query_label":attempts[-1]["query_label"],"attempts":attempts}

def head_size(url:str,basename:str)->int:
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,method="HEAD",headers={
                "User-Agent":"BotMarketplace-SC001-B14A-ChainSchema/0.1",
                "Referer":"https://www.okx.com/historical-data",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                status=int(getattr(resp,"status",200))
                final=resp.geturl()
                cl=resp.headers.get("Content-Length")
            if status!=200 or not trusted_archive(final,basename):
                fail(f"HEAD identity/status mismatch {basename}")
            if not cl or not cl.isdigit() or int(cl)<=0:
                fail(f"HEAD invalid Content-Length {basename}")
            return int(cl)
        except Exception as exc:
            last=exc
            if attempt<RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"HEAD failed {basename}: {last}")

def download_exact(url:str,basename:str,expected:int)->Path:
    if expected<=0 or expected>MAX_FILE:
        fail(f"archive size outside cap {basename}: {expected}")
    ARCH_DIR.mkdir(parents=True,exist_ok=True)
    path=ARCH_DIR/basename
    if path.exists() and path.stat().st_size==expected:
        return path
    tmp=Path(str(path)+".part"); tmp.unlink(missing_ok=True)
    got=0
    req=urllib.request.Request(url,headers={
        "User-Agent":"BotMarketplace-SC001-B14A-ChainSchema/0.1",
        "Referer":"https://www.okx.com/historical-data",
    })
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp,tmp.open("wb") as f:
        final=resp.geturl()
        if not trusted_archive(final,basename):
            fail(f"GET identity mismatch {basename}")
        while True:
            chunk=resp.read(CHUNK)
            if not chunk:
                break
            got+=len(chunk)
            if got>expected or got>MAX_FILE:
                fail(f"download overflow {basename}")
            f.write(chunk)
        f.flush(); os.fsync(f.fileno())
    if got!=expected:
        fail(f"download size mismatch {basename}: {got}!={expected}")
    os.replace(tmp,path)
    return path

def normalize_header(line:bytes)->tuple[str,...]:
    text=line.decode("utf-8-sig").strip("\r\n")
    return tuple(x.strip() for x in text.split(","))

def first_field(line:bytes)->str:
    token=line.split(b",",1)[0].strip().strip(b'"')
    return token.decode("utf-8","strict")

def inspect_archive(path:Path,family:str,target:str,pattern:re.Pattern)->dict:
    schemas=set()
    distinct=set()
    total_rows=0
    csv_members=[]

    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {path.name}: {bad}")
        regular=[x for x in z.infolist() if not x.is_dir()]
        if not regular:
            fail(f"no regular ZIP members {path.name}")
        non_csv=[x.filename for x in regular if not x.filename.lower().endswith(".csv")]
        if non_csv:
            fail(f"non-CSV regular ZIP members {path.name}: {non_csv}")

        for info in regular:
            csv_members.append(info.filename)
            with z.open(info) as f:
                header_line=f.readline()
                if not header_line:
                    fail(f"empty CSV member {info.filename}")
                header=normalize_header(header_line)
                if header==HEADER6:
                    schemas.add("LEGACY_6")
                elif header==HEADER7:
                    schemas.add("SOURCE_7")
                else:
                    fail(f"header mismatch {info.filename}: {header}")

                for line in f:
                    if not line.strip():
                        continue
                    total_rows+=1
                    inst=first_field(line)
                    if not pattern.fullmatch(inst):
                        fail(f"instrument_name family/pattern mismatch: {inst}")
                    distinct.add(inst)

    if total_rows<=0:
        fail(f"no data rows {path.name}")
    if len(distinct)<2:
        fail(f"distinct contract IDs <2 {path.name}: {sorted(distinct)}")
    if target not in distinct:
        fail(f"target nearest contract missing {target} in {path.name}")

    return {
        "archive":path.name,
        "zip_crc_pass":True,
        "csv_members":csv_members,
        "schema_classes":sorted(schemas),
        "total_nonempty_data_rows":total_rows,
        "distinct_contract_ids":sorted(distinct),
        "distinct_contract_count":len(distinct),
        "target_nearest_contract":target,
        "target_present":True,
        "price_column_present_in_schema":True,
        "price_values_parsed_or_stored":False,
    }

def self_test()->int:
    try:
        require_freeze()
        if normalize_header(b"instrument_name,trade_id,side,price,size,created_time\r\n")!=HEADER6:
            fail("LEGACY_6 fixture mismatch")
        if normalize_header(b"\xef\xbb\xbfinstrument_name,trade_id,side,price,size,created_time,source\n")!=HEADER7:
            fail("SOURCE_7/BOM fixture mismatch")
        if first_field(b'BTC-USD-260925,1,buy,123,1,1\n')!="BTC-USD-260925":
            fail("first-field fixture mismatch")
        if not FAMILIES["BTC-USD"]["pattern"].fullmatch("BTC-USD-260925"):
            fail("BTC pattern fixture mismatch")
        if FAMILIES["BTC-USD"]["pattern"].fullmatch("ETH-USD-260925"):
            fail("cross-family rejection fixture failed")
        print(SELFTEST_PASS)
        print("canonical_d0_sha =",D0_SHA)
        print("authorized_archives =",[x["archive"] for x in FAMILIES.values()])
        print("price_values_parsed_or_stored = False")
        print("basis/convergence/PnL = CLOSED")
        return 0
    except Exception as exc:
        print(SELFTEST_REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def run()->int:
    try:
        d0=require_freeze()
        probes=d0.get("family_archive_probes") or {}
        results={}

        for family,spec in FAMILIES.items():
            print(f"B14-A CHAIN-SCHEMA {family}",flush=True)
            d0p=probes.get(family) or {}
            if d0p.get("archive_file")!=spec["archive"] or d0p.get("archive_pass") is not True:
                fail(f"canonical D0 archive identity mismatch {family}")
            expected=int(d0p.get("content_length") or 0)
            if expected<=0:
                fail(f"canonical D0 content length missing {family}")

            url,meta=resolve_archive(family,spec["archive"])
            actual=head_size(url,spec["archive"])
            if actual!=expected:
                fail(f"HEAD size changed {family}: {actual}!={expected}")

            path=download_exact(url,spec["archive"],expected)
            inspected=inspect_archive(path,family,spec["target"],spec["pattern"])
            inspected["content_length"]=expected
            inspected["metadata_query"]=meta
            results[family]=inspected

            print("  archive =",spec["archive"],flush=True)
            print("  schema =",inspected["schema_classes"],flush=True)
            print("  rows =",inspected["total_nonempty_data_rows"],"distinct_contracts =",inspected["distinct_contract_count"],flush=True)
            print("  target_present =",inspected["target_present"],flush=True)

        report={
            "stage":STAGE,
            "version":"0.1",
            "status":PASS,
            "canonical_d0_sha256":D0_SHA,
            "probe_date":PROBE_DATE,
            "families":results,
            "futureschain_body_downloaded":True,
            "futureschain_body_opened":True,
            "header_schema_accessed":True,
            "instrument_name_accessed":True,
            "price_values_parsed_or_stored":False,
            "price_outcome_calculated":False,
            "basis_calculated":False,
            "return_calculated":False,
            "settlePx_accessed":False,
            "delivery_price_accessed":False,
            "convergence_calculated":False,
            "strategy_signal_calculated":False,
            "execution_model_calculated":False,
            "pnl_calculated":False,
            "candidate_id_assigned":False,
            "promotional_alpha_accessed":False,
        }
        atomic_json(OUT,report)

        print(PASS)
        print("BTC distinct contracts =",results["BTC-USD"]["distinct_contract_ids"])
        print("ETH distinct contracts =",results["ETH-USD"]["distinct_contract_ids"])
        print("price_values_parsed_or_stored = False")
        print("basis/convergence/execution/PnL = False")
        print("candidate_id_assigned = False")
        print("report =",OUT)
        return 0

    except Exception as exc:
        report={
            "stage":STAGE,
            "version":"0.1",
            "status":REVIEW,
            "error":f"{type(exc).__name__}: {exc}",
            "price_values_parsed_or_stored":False,
            "basis_calculated":False,
            "convergence_calculated":False,
            "pnl_calculated":False,
            "candidate_id_assigned":False,
        }
        try:
            atomic_json(OUT,report)
        except Exception:
            pass
        print(REVIEW)
        print("error =",report["error"])
        return 2

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","run"),required=True)
    args=ap.parse_args()
    return self_test() if args.mode=="self-test" else run()

if __name__=="__main__":
    raise SystemExit(main())
