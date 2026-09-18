from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

STAGE="SC001-C12-D2-H1-ARCHIVE-METADATA-V0.1"
PASS="C12_D2_H1_ARCHIVE_METADATA_PASS"
REVIEW="C12_D2_H1_ARCHIVE_METADATA_REVIEW"

START=date(2025,1,1); END=date(2025,7,1)
INST="USDC-USDT"
OKX_DOMAINS=("https://www.okx.com","https://us.okx.com"); STATIC="static.okx.com"
TIMEOUT=60; RETRIES=3; MAX_JSON=4_000_000

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-c12-d2-h1-archive-metadata-protocol-v0.1.md"
REGISTRY=ROOT/"docs/research/sc001-contamination-registry-v0.16.json"
FREEZE=ROOT/"docs/research/sc001-c12-d2-implementation-freeze-v0.1.json"
DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
D1=DATA_ROOT/"SC001_C12_D1_SPOT_SEMANTICS"/"sc001_c12_d1_spot_trade_semantics_report_v0_1.json"
OUT_DIR=DATA_ROOT/"SC001_C12_D2_H1_METADATA"; OUT=OUT_DIR/"sc001_c12_d2_h1_archive_metadata_report_v0_1.json"

def fail(m): raise RuntimeError(m)
def load_json(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): fail(f"JSON object expected {p}")
    return x
def atomic_json(p,o):
    p.parent.mkdir(parents=True,exist_ok=True); t=Path(str(p)+".tmp")
    with t.open("w",encoding="utf-8") as f: json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)
def git_blob(p): return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],text=True).strip()
def require():
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_C12_D2_RUN": fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()): fail("runner identity mismatch")
    if fr.get("protocol_git_blob_sha")!=git_blob(PROTOCOL): fail("protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha")!=git_blob(REGISTRY): fail("registry identity mismatch")
    if int(fr.get("required_archive_count",0))!=182: fail("archive count mismatch")
    for k in ("historical_trade_body_authorized","peg_deviation_authorized","reversion_outcome_authorized","threshold_selection_authorized","strategy_signal_authorized","pnl_authorized","promotional_alpha_authorized"):
        if fr.get(k) is not False: fail(f"firewall mismatch {k}")
    d1=load_json(D1)
    if d1.get("status")!="C12_D1_SPOT_TRADE_SEMANTICS_PASS": fail("D1 not PASS")
def walk(n):
    if isinstance(n,dict):
        yield n
        for v in n.values(): yield from walk(v)
    elif isinstance(n,list):
        for v in n: yield from walk(v)
def day_ms(d):
    dt=datetime(d.year,d.month,d.day,tzinfo=timezone.utc); b=int(dt.timestamp()*1000); return b,b+86_400_000
def trusted(u,b):
    p=urllib.parse.urlparse(u); return p.scheme=="https" and (p.hostname or "").lower()==STATIC and Path(p.path).name==b
def resolve(d):
    ds=d.isoformat(); bname=f"{INST}-trades-{ds}.zip"; b,e=day_ms(d)
    payload={"module":"1","instType":"SPOT","instQueryParam":{"instIdList":[INST]},"dateQuery":{"dateAggrType":"daily","begin":str(b),"end":str(e-1)}}
    body=json.dumps(payload,separators=(",",":")).encode(); last=None
    for dom in OKX_DOMAINS:
        try:
            req=urllib.request.Request(dom+"/priapi/v5/broker/public/trade-data/download-link?t="+str(int(time.time()*1000)),data=body,method="POST",headers={"User-Agent":"BotMarketplace-SC001-C12-D2/0.1","Accept":"application/json,*/*","Content-Type":"application/json","Referer":"https://www.okx.com/historical-data"})
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp: raw=resp.read(MAX_JSON+1)
            if len(raw)>MAX_JSON: fail("metadata cap")
            obj=json.loads(raw.decode())
            if str(obj.get("code"))!="0": fail("metadata code")
            found=[]
            for n in walk(obj.get("data")):
                if isinstance(n,dict):
                    fn=n.get("filename") or n.get("fileName"); u=n.get("url")
                    if fn==bname and isinstance(u,str) and trusted(u,bname) and u not in found: found.append(u)
            if len(found)==1: return bname,found[0]
            if len(found)>1: fail(f"multiple exact URLs {ds}")
            last=RuntimeError("exact archive missing")
        except Exception as exc: last=exc
    raise RuntimeError(f"resolve failed {ds}: {last}")
def head(u,b):
    req=urllib.request.Request(u,method="HEAD",headers={"User-Agent":"BotMarketplace-SC001-C12-D2/0.1","Referer":"https://www.okx.com/historical-data"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp: final=resp.geturl(); cl=resp.headers.get("Content-Length")
    if not trusted(final,b) or not cl or not cl.isdigit() or int(cl)<=0: fail(f"HEAD mismatch {b}")
    return int(cl)
def main():
    try:
        require(); OUT_DIR.mkdir(parents=True,exist_ok=True)
        rows=[]; d=START; i=0
        while d<=END:
            i+=1
            if i==1 or i%10==0 or d==END: print(f"C12-D2 [{i}/182] {d.isoformat()}",flush=True)
            b,u=resolve(d); s=head(u,b); rows.append({"date":d.isoformat(),"filename":b,"content_length":s})
            d+=timedelta(days=1)
        rep={"stage":STAGE,"version":"0.1","status":PASS,"target_window":"2025-01-01_to_2025-06-30","source_archive_window":"2025-01-01_to_2025-07-01","archives":rows,"archive_count":len(rows),"combined_head_content_length":sum(x["content_length"] for x in rows),"historical_trade_body_downloaded":False,"historical_trade_body_opened":False,"peg_deviation_calculated":False,"reversion_outcome_calculated":False,"threshold_selected":False,"strategy_signal_calculated":False,"pnl_calculated":False,"promotional_alpha_accessed":False}
        atomic_json(OUT,rep)
        print(PASS); print("archives_verified =",len(rows),"/ 182"); print("combined_HEAD_content_length =",rep["combined_head_content_length"]); print("historical trade body downloaded/opened = False / False"); print("peg deviation/reversion/threshold/signal/PnL = False"); print("promotional alpha accessed = False"); print("report =",OUT)
        return 0
    except Exception as exc:
        print(REVIEW); print("error =",f"{type(exc).__name__}: {exc}"); return 2
if __name__=="__main__": raise SystemExit(main())
