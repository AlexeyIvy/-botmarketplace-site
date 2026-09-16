from __future__ import annotations
import json, os, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

STAGE="SC001-HISTORICAL-EXECUTION-SPEC-INVENTORY"
VERSION="0.1"
PASS="SC001_HISTORICAL_EXECUTION_SPEC_INVENTORY_PASS"
DOMAINS=("https://www.okx.com","https://us.okx.com")
PATH="/api/v5/public/instruments"
UA="BotMarketplace-SC001-HistoricalSpecInventory/0.1"

REPO=Path(__file__).resolve().parents[2]
UNIVERSE=REPO/"docs/research/sc001-first-generation-multi-asset-universe-freeze-v1.0.json"
EVIDENCE=REPO/"docs/research/sc001-historical-execution-spec-known-evidence-v0.1.json"
DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_HISTORICAL_EXECUTION_SPEC_INVENTORY"
OUT=OUT_DIR/"sc001_historical_execution_spec_inventory_report.json"


def fail(s): raise RuntimeError(s)
def load(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): fail(f"object expected: {p}")
    return x

def atomic(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+".tmp")
    with q.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(q,p)

def get_inst(inst):
    qs=urlencode({"instType":"SWAP","instId":inst})
    errs=[]
    for d in DOMAINS:
        for a in range(1,4):
            try:
                req=Request(d+PATH+"?"+qs,headers={"User-Agent":UA,"Accept":"application/json"})
                with urlopen(req,timeout=60) as r: raw=r.read(2_000_001)
                if len(raw)>2_000_000: raise RuntimeError("response cap")
                o=json.loads(raw.decode("utf-8"))
                if o.get("code")!="0" or not isinstance(o.get("data"),list) or len(o["data"])!=1:
                    raise RuntimeError("exact row not returned")
                return o["data"][0], d
            except (HTTPError,URLError,TimeoutError,OSError,ValueError,RuntimeError) as e:
                errs.append(f"{d}:{type(e).__name__}:{e}")
                if a<3: time.sleep(0.5*a)
    fail(f"instrument fetch failed {inst}: {errs[-4:]}")

def main():
    u=load(UNIVERSE); ev=load(EVIDENCE)
    rows=list(u.get("universe_ranked") or [])
    if u.get("status")!="FROZEN" or len(rows)!=12: fail("universe not exact frozen 12")
    insts=[r["instrument"] for r in rows]
    if len(set(insts))!=12: fail("duplicate universe")
    events=list(ev.get("events") or [])
    bad=[x.get("instrument") for x in events if x.get("instrument") not in insts]
    if bad: fail(f"evidence outside universe: {bad}")
    by={i:[] for i in insts}
    for e in events: by[e["instrument"]].append(e)

    out=[]
    for i,inst in enumerate(insts,1):
        print(f"[{i}/12] {inst}")
        r,domain=get_inst(inst)
        required=("tickSz","lotSz","minSz","ctVal")
        if r.get("instId")!=inst or r.get("instType")!="SWAP" or r.get("ctType")!="linear" or r.get("settleCcy")!="USDT":
            fail(f"structure mismatch {inst}")
        for k in required:
            try:
                if float(r.get(k,"0"))<=0: fail(f"nonpositive current {k} {inst}")
            except Exception: fail(f"bad current {k} {inst}")
        states={k:"UNRESOLVED" for k in required}
        if by[inst]:
            for e in by[inst]:
                if e.get("field")=="listing_baseline":
                    if "tickSz" in e: states["tickSz"]="PARTIALLY_BRACKETED"
                    if "ctVal" in e: states["ctVal"]="PARTIALLY_BRACKETED"
                if e.get("field")=="lotSz/minSz":
                    states["lotSz"]="PARTIALLY_BRACKETED"
                    states["minSz"]="PARTIALLY_BRACKETED"
        unresolved=[k for k,v in states.items() if v!="RESOLVED_OFFICIAL_INTERVAL"]
        out.append({
            "instrument":inst,"source_domain":domain,
            "current_reference_only":{k:r.get(k) for k in ("instId","instType","ctType","settleCcy","tickSz","lotSz","minSz","ctVal","listTime","state")},
            "known_official_events":by[inst],"historical_field_states":states,"required_fields_not_yet_resolved":unresolved
        })
        print(inst,"known_events=",len(by[inst]),"historical_resolved=0/4")
        time.sleep(0.08)

    fee=ev.get("fee_reference") or {}
    passed=len(out)==12 and all(len(x["required_fields_not_yet_resolved"])==4 for x in out)
    if not passed: fail("inventory invariant failed")
    rep={
        "stage":STAGE,"version":VERSION,"status":PASS,
        "universe_path":str(UNIVERSE),"evidence_pack_path":str(EVIDENCE),
        "instruments":out,
        "fee_reference":fee,
        "historical_exact_execution_specs_verified":False,
        "current_metadata_used_as_historical_proof":False,
        "july_august_market_data_body_accessed":False,
        "strategy_signal_calculated":False,"promotional_pnl_calculated":False,
        "next_gate":"HISTORICAL_SPEC_RECONSTRUCTION_REQUIRED"
    }
    atomic(OUT,rep)
    print(PASS)
    print("frozen instruments inventoried = 12 / 12")
    print("historical exact execution specs verified = False")
    print("current metadata used as historical proof = False")
    print("July/August market data body accessed = False")
    print("strategy signal/PnL calculated = False")
    print("report =",OUT)
    return 0

if __name__=="__main__": raise SystemExit(main())
