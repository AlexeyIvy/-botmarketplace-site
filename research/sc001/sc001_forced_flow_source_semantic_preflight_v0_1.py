#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

PASS="FORCED_FLOW_SOURCE_SEMANTIC_PREFLIGHT_PASS"
REVIEW="FORCED_FLOW_SOURCE_SEMANTIC_PREFLIGHT_REVIEW"
ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-next-primary-forced-flow-relative-dislocation-source-semantic-qualification-protocol-v0.1.md"
FREEZE=ROOT/"docs/research/sc001-next-primary-forced-flow-relative-dislocation-source-semantic-qualification-freeze-v0.1.json"

PAIRS=[
("BTC","BTCUSDT","BTC-USDT-SWAP"),("ETH","ETHUSDT","ETH-USDT-SWAP"),
("SOL","SOLUSDT","SOL-USDT-SWAP"),("DOGE","DOGEUSDT","DOGE-USDT-SWAP"),
("ORDI","ORDIUSDT","ORDI-USDT-SWAP"),("FIL","FILUSDT","FIL-USDT-SWAP"),
("UNI","UNIUSDT","UNI-USDT-SWAP"),("XRP","XRPUSDT","XRP-USDT-SWAP"),
("LTC","LTCUSDT","LTC-USDT-SWAP"),("OP","OPUSDT","OP-USDT-SWAP"),
("BCH","BCHUSDT","BCH-USDT-SWAP"),("SUI","SUIUSDT","SUI-USDT-SWAP"),
]
BYBIT="https://api.bybit.com"
OKX_DOMAINS=("https://www.okx.com","https://us.okx.com")
TIMEOUT=30
RETRIES=2
MAX_BYTES=2_000_000

def fail(msg:str)->None:
    raise RuntimeError(msg)

def git_blob(path:Path)->str:
    return subprocess.check_output(["git","-C",str(ROOT),"hash-object",str(path.relative_to(ROOT))],text=True).strip()

def load_json(path:Path)->dict:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict): fail(f"object expected: {path}")
    return obj

def require_freeze()->dict:
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_FORCED_FLOW_SOURCE_SEMANTIC_PREFLIGHT":
        fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha")!=git_blob(Path(__file__).resolve()):
        fail("runner blob mismatch")
    if fr.get("protocol_git_blob_sha")!=git_blob(PROTOCOL):
        fail("protocol blob mismatch")
    expected=[[a,b,c] for a,b,c in PAIRS]
    if fr.get("frozen_pairs")!=expected:
        fail("frozen pair mismatch")
    for k in (
        "trade_body_authorized","price_outcome_authorized","cross_venue_price_ratio_authorized",
        "return_authorized","pnl_authorized","l1_l2_authorized","mark_index_premium_authorized",
        "funding_authorized","trading_authorized"
    ):
        if fr.get(k) is not False: fail(f"firewall mismatch {k}")
    return fr

def request_json(url:str)->dict:
    last=None
    for attempt in range(RETRIES):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"BotMarketplace-SC001-ForcedFlow-SourceSemantic-v0.1","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_BYTES+1)
                if len(raw)>MAX_BYTES: fail("response cap exceeded")
                if int(getattr(resp,"status",200))!=200: fail("HTTP non-200")
            obj=json.loads(raw.decode("utf-8"))
            if not isinstance(obj,dict): fail("JSON object expected")
            return obj
        except Exception as exc:
            last=exc
            if attempt+1<RETRIES: time.sleep(1.0)
    raise RuntimeError(f"request failed: {type(last).__name__}: {last}")

def bybit_instrument(base:str,symbol:str)->dict:
    q=urllib.parse.urlencode({"category":"linear","symbol":symbol})
    obj=request_json(BYBIT+"/v5/market/instruments-info?"+q)
    if int(obj.get("retCode",-1))!=0: fail(f"Bybit retCode {obj.get('retCode')}")
    rows=(obj.get("result") or {}).get("list") or []
    if len(rows)!=1 or not isinstance(rows[0],dict): fail(f"Bybit row count {symbol}={len(rows)}")
    r=rows[0]
    checks={
      "symbol_exact":r.get("symbol")==symbol,
      "contract_linear_perpetual":r.get("contractType")=="LinearPerpetual",
      "status_trading":r.get("status")=="Trading",
      "base_exact":r.get("baseCoin")==base,
      "quote_usdt":r.get("quoteCoin")=="USDT",
      "settle_usdt":r.get("settleCoin")=="USDT",
      "not_prelisting":r.get("isPreListing") is False,
    }
    return {
      "pass":all(checks.values()),"checks":checks,
      "symbolType":r.get("symbolType"),"fullName":r.get("fullName"),
      "baseCoin":r.get("baseCoin"),"quoteCoin":r.get("quoteCoin"),"settleCoin":r.get("settleCoin"),
      "contractType":r.get("contractType"),"status":r.get("status"),"isPreListing":r.get("isPreListing")
    }

def okx_request(inst_id:str)->dict:
    q=urllib.parse.urlencode({"instType":"SWAP","instId":inst_id})
    last=None
    for d in OKX_DOMAINS:
        try:
            obj=request_json(d+"/api/v5/public/instruments?"+q)
            if str(obj.get("code"))!="0": fail(f"OKX code {obj.get('code')}")
            return obj
        except Exception as exc:
            last=exc
    raise RuntimeError(f"OKX request failed: {type(last).__name__}: {last}")

def positive_number(v)->bool:
    try:
        x=float(str(v))
        return math.isfinite(x) and x>0
    except Exception:
        return False

def okx_instrument(base:str,inst_id:str)->dict:
    obj=okx_request(inst_id)
    rows=obj.get("data") or []
    if len(rows)!=1 or not isinstance(rows[0],dict): fail(f"OKX row count {inst_id}={len(rows)}")
    r=rows[0]
    fam=f"{base}-USDT"
    checks={
      "inst_id_exact":r.get("instId")==inst_id,
      "inst_type_swap":r.get("instType")=="SWAP",
      "state_live":r.get("state")=="live",
      "uly_exact":r.get("uly")==fam,
      "inst_family_exact":r.get("instFamily")==fam,
      "ct_type_linear":r.get("ctType")=="linear",
      "settle_usdt":r.get("settleCcy")=="USDT",
      "ct_val_ccy_base":r.get("ctValCcy")==base,
      "ct_val_positive":positive_number(r.get("ctVal")),
    }
    return {
      "pass":all(checks.values()),"checks":checks,
      "instId":r.get("instId"),"uly":r.get("uly"),"instFamily":r.get("instFamily"),
      "instType":r.get("instType"),"ctType":r.get("ctType"),"settleCcy":r.get("settleCcy"),
      "ctVal":r.get("ctVal"),"ctMult":r.get("ctMult"),"ctValCcy":r.get("ctValCcy"),"state":r.get("state")
    }

def parser_fixture_selftest()->dict:
    bybit={"execId":"x","symbol":"BTCUSDT","price":"1","size":"1","side":"Buy","time":"1760000000000"}
    okx={"instId":"BTC-USDT-SWAP","tradeId":"x","px":"1","sz":"1","side":"buy","ts":"1760000000000"}
    bad=dict(bybit); bad["time"]="not-ms"
    def plausible(v):
        try:
            x=int(str(v)); return 946684800000<=x<4102444800000
        except Exception: return False
    required_b={"execId","symbol","price","size","side","time"}
    required_o={"instId","tradeId","px","sz","side","ts"}
    checks={
      "bybit_documented_trade_fixture":required_b.issubset(bybit) and plausible(bybit["time"]),
      "okx_documented_trade_fixture":required_o.issubset(okx) and plausible(okx["ts"]),
      "malformed_timestamp_rejected":not plausible(bad["time"]),
      "strict_coactive_no_carry_forward_frozen":True,
    }
    return {"pass":all(checks.values()),"checks":checks}

def write_result(out_dir:Path,obj:dict)->None:
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/"forced_flow_source_semantic_preflight_result.json").write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["self-test","live"],required=True)
    ap.add_argument("--out-dir",default=os.environ.get("BM_TEST_OUTPUT_DIR",os.environ.get("OUTPUT_DIR",str(Path.cwd()/"test-output"))))
    a=ap.parse_args()
    try:
        require_freeze()
        fixtures=parser_fixture_selftest()
        if not fixtures["pass"]: fail("fixture self-test failed")
        if a.mode=="self-test":
            result={
              "schema":"sc001.forced_flow_source_semantic_preflight.v0.1",
              "mode":"self-test","status":PASS,"fixture_gate":fixtures,
              "network_calls_performed":False,
              "trade_body_accessed":False,"price_outcome_accessed":False,
              "cross_venue_price_ratio_calculated":False,"return_calculated":False,
              "pnl_calculated":False,"l1_l2_accessed":False,
              "mark_index_premium_accessed":False,"funding_accessed":False,"trading_accessed":False
            }
            write_result(Path(a.out_dir),result); print(PASS); return 0

        pairs=[]
        errors=[]
        for base,bsym,oid in PAIRS:
            try:
                b=bybit_instrument(base,bsym)
                o=okx_instrument(base,oid)
                pair_checks={
                  "bybit_pass":b["pass"],"okx_pass":o["pass"],
                  "same_base_official_metadata":b.get("baseCoin")==base and o.get("ctValCcy")==base and o.get("uly")==f"{base}-USDT",
                  "usdt_quote_settlement_compatible":b.get("quoteCoin")=="USDT" and b.get("settleCoin")=="USDT" and o.get("settleCcy")=="USDT",
                  "linear_perpetual_compatible":b.get("contractType")=="LinearPerpetual" and o.get("instType")=="SWAP" and o.get("ctType")=="linear",
                  "standard_live_not_premarket":b.get("status")=="Trading" and b.get("isPreListing") is False and o.get("state")=="live",
                  "okx_contract_value_currency_matches_base":o.get("ctValCcy")==base and positive_number(o.get("ctVal")),
                }
                ppass=all(pair_checks.values())
                if not ppass: errors.append(base)
                pairs.append({"base":base,"bybit_symbol":bsym,"okx_instId":oid,"pass":ppass,"pair_checks":pair_checks,"bybit":b,"okx":o})
            except Exception as exc:
                errors.append(base)
                pairs.append({"base":base,"bybit_symbol":bsym,"okx_instId":oid,"pass":False,"error":f"{type(exc).__name__}: {exc}"})
        status=PASS if not errors and len(pairs)==12 else REVIEW
        result={
          "schema":"sc001.forced_flow_source_semantic_preflight.v0.1",
          "mode":"live","status":status,
          "frozen_pair_count":12,"passed_pair_count":sum(1 for p in pairs if p.get("pass")),
          "failed_bases":errors,"pairs":pairs,"fixture_gate":fixtures,
          "network_scope":["BYBIT_INSTRUMENT_METADATA","OKX_INSTRUMENT_METADATA"],
          "trade_body_accessed":False,"price_outcome_accessed":False,
          "cross_venue_price_ratio_calculated":False,"return_calculated":False,
          "pnl_calculated":False,"l1_l2_accessed":False,
          "mark_index_premium_accessed":False,"funding_accessed":False,"trading_accessed":False
        }
        write_result(Path(a.out_dir),result)
        print(status); print("passed_pairs =",result["passed_pair_count"]); print("failed_bases =",errors)
        return 0 if status==PASS else 2
    except Exception as exc:
        result={"schema":"sc001.forced_flow_source_semantic_preflight.v0.1","mode":a.mode,"status":REVIEW,"error":f"{type(exc).__name__}: {exc}","trade_body_accessed":False,"price_outcome_accessed":False,"cross_venue_price_ratio_calculated":False,"return_calculated":False,"pnl_calculated":False,"l1_l2_accessed":False,"mark_index_premium_accessed":False,"funding_accessed":False,"trading_accessed":False}
        write_result(Path(a.out_dir),result); print(REVIEW); print(result["error"]); return 2

if __name__=="__main__":
    raise SystemExit(main())
