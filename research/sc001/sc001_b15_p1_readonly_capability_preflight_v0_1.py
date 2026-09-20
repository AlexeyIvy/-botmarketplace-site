from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import shlex
import stat
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAGE="SC001-B15-P1-READONLY-CAPABILITY-PREFLIGHT-V0.1"
PASS="B15_P1_READONLY_CAPABILITY_PASS"
REVIEW="B15_P1_READONLY_CAPABILITY_REVIEW"

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-b15-p1-readonly-capability-preflight-v0.1.md"
SECURITY=ROOT/"docs/research/sc001-b15-p1-read-only-credential-security-contract-v0.1.md"
FREEZE=ROOT/"docs/research/sc001-b15-p1-readonly-capability-implementation-freeze-v0.1.json"
ENV_FILE=Path("/home/botmarket/.config/sc001/b15-p1.env")

TIMEOUT=30
MAX_JSON=12_000_000
RECV_WINDOW="5000"
MAX_CLOCK_SKEW_MS=10_000

def fail(msg:str)->None:
    raise RuntimeError(msg)

def git_blob(path:Path)->str:
    return subprocess.check_output(
        ["git","-C",str(ROOT),"hash-object",str(path.relative_to(ROOT))],
        text=True
    ).strip()

def load_json_file(path:Path)->dict:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail(f"JSON object expected: {path}")
    return obj

def parse_env(path:Path)->dict[str,str]:
    if not path.exists():
        fail(f"credential file missing: {path}")
    mode=stat.S_IMODE(path.stat().st_mode)
    if mode!=0o600:
        fail(f"credential file mode must be 0600, got {oct(mode)}")
    out={}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line=raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            fail("malformed credential env line")
        k,v=line.split("=",1)
        parts=shlex.split(v,posix=True)
        if len(parts)!=1:
            fail(f"malformed credential value for {k}")
        out[k]=parts[0]
    required=(
        "SC001_B15_OKX_API_KEY",
        "SC001_B15_OKX_API_SECRET",
        "SC001_B15_OKX_PASSPHRASE",
        "SC001_B15_OKX_BASE_URL",
        "SC001_B15_BYBIT_API_KEY",
        "SC001_B15_BYBIT_API_SECRET",
        "SC001_B15_BYBIT_BASE_URL",
    )
    for k in required:
        if not out.get(k):
            fail(f"missing credential variable: {k}")
    return out

def require_freeze()->dict:
    fr=load_json_file(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_B15_P1_READONLY_CAPABILITY_PREFLIGHT":
        fail("freeze status mismatch")
    checks={
        "runner_git_blob_sha":git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha":git_blob(PROTOCOL),
        "security_contract_git_blob_sha":git_blob(SECURITY),
    }
    for k,v in checks.items():
        if fr.get(k)!=v:
            fail(f"freeze identity mismatch: {k}")
    return fr

def http_json(url:str,headers:dict[str,str]|None=None)->dict:
    req=urllib.request.Request(url,headers=headers or {
        "User-Agent":"BotMarketplace-SC001-B15-P1/0.1",
        "Accept":"application/json",
    })
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
        raw=resp.read(MAX_JSON+1)
        status=int(getattr(resp,"status",200))
    if status!=200:
        fail(f"HTTP status {status}: {url}")
    if len(raw)>MAX_JSON:
        fail("JSON response cap exceeded")
    obj=json.loads(raw.decode("utf-8"))
    if not isinstance(obj,dict):
        fail("JSON object response expected")
    return obj

def utc_iso_ms()->str:
    now=datetime.now(timezone.utc)
    return now.isoformat(timespec="milliseconds").replace("+00:00","Z")

def okx_private(base,key,secret,passphrase,path)->dict:
    ts=utc_iso_ms()
    prehash=ts+"GET"+path
    sig=base64.b64encode(
        hmac.new(secret.encode(),prehash.encode(),hashlib.sha256).digest()
    ).decode()
    headers={
        "User-Agent":"BotMarketplace-SC001-B15-P1/0.1",
        "Accept":"application/json",
        "OK-ACCESS-KEY":key,
        "OK-ACCESS-SIGN":sig,
        "OK-ACCESS-TIMESTAMP":ts,
        "OK-ACCESS-PASSPHRASE":passphrase,
    }
    return http_json(base+path,headers)

def bybit_private(base,key,secret,path,query="")->dict:
    ts=str(int(time.time()*1000))
    payload=ts+key+RECV_WINDOW+query
    sig=hmac.new(secret.encode(),payload.encode(),hashlib.sha256).hexdigest()
    headers={
        "User-Agent":"BotMarketplace-SC001-B15-P1/0.1",
        "Accept":"application/json",
        "X-BAPI-API-KEY":key,
        "X-BAPI-TIMESTAMP":ts,
        "X-BAPI-RECV-WINDOW":RECV_WINDOW,
        "X-BAPI-SIGN":sig,
    }
    url=base+path+("?" + query if query else "")
    return http_json(url,headers)

def okx_server_time_ms(base)->int:
    obj=http_json(base+"/api/v5/public/time")
    if str(obj.get("code"))!="0":
        fail(f"OKX public time code={obj.get('code')}")
    data=obj.get("data") or []
    if len(data)!=1:
        fail("OKX public time row mismatch")
    return int(str(data[0].get("ts")))

def bybit_server_time_ms(base)->int:
    obj=http_json(base+"/v5/market/time")
    if int(obj.get("retCode",-1))!=0:
        fail(f"Bybit public time retCode={obj.get('retCode')}")
    return int(obj.get("time"))

def check_okx(cfg)->dict:
    base=cfg["SC001_B15_OKX_BASE_URL"].rstrip("/")
    key=cfg["SC001_B15_OKX_API_KEY"]
    secret=cfg["SC001_B15_OKX_API_SECRET"]
    passphrase=cfg["SC001_B15_OKX_PASSPHRASE"]

    local=int(time.time()*1000)
    server=okx_server_time_ms(base)
    skew=local-server

    ac=okx_private(base,key,secret,passphrase,"/api/v5/account/config")
    if str(ac.get("code"))!="0":
        fail(f"OKX account/config code={ac.get('code')} msg={ac.get('msg')}")
    rows=ac.get("data") or []
    if len(rows)!=1:
        fail("OKX account config row mismatch")
    row=rows[0]
    perm=str(row.get("perm") or "")
    perms={x.strip() for x in perm.split(",") if x.strip()}
    if perms!={"read_only"}:
        fail(f"OKX API permission is not exactly read_only: {sorted(perms)}")

    cur=okx_private(base,key,secret,passphrase,"/api/v5/asset/currencies")
    if str(cur.get("code"))!="0":
        fail(f"OKX currencies code={cur.get('code')} msg={cur.get('msg')}")
    data=cur.get("data") or []
    if not data:
        fail("OKX currencies returned empty data")
    required={"ccy","chain","canDep","canWd"}
    bad=0
    for r in data:
        if not isinstance(r,dict) or not required.issubset(r):
            bad+=1
    if bad:
        fail(f"OKX currencies schema missing required fields in {bad} rows")

    return {
        "base_url":base,
        "clock_skew_ms":skew,
        "permission":perm,
        "ip_bound":bool(str(row.get("ip") or "").strip()),
        "currency_chain_rows":len(data),
        "schema_pass":True,
    }

def check_bybit(cfg)->dict:
    base=cfg["SC001_B15_BYBIT_BASE_URL"].rstrip("/")
    key=cfg["SC001_B15_BYBIT_API_KEY"]
    secret=cfg["SC001_B15_BYBIT_API_SECRET"]

    local=int(time.time()*1000)
    server=bybit_server_time_ms(base)
    skew=local-server

    ki=bybit_private(base,key,secret,"/v5/user/query-api")
    if int(ki.get("retCode",-1))!=0:
        fail(f"Bybit query-api retCode={ki.get('retCode')} msg={ki.get('retMsg')}")
    result=ki.get("result") or {}
    readonly=int(result.get("readOnly",-1))
    if readonly!=1:
        fail(f"Bybit API key is not read-only: readOnly={readonly}")

    permissions=result.get("permissions") or {}
    if not isinstance(permissions,dict):
        fail("Bybit permissions object missing")
    wallet=permissions.get("Wallet") or []
    withdraw_token="Withdraw" in wallet

    ci=bybit_private(base,key,secret,"/v5/asset/coin/query-info")
    if int(ci.get("retCode",-1))!=0:
        fail(f"Bybit coin-info retCode={ci.get('retCode')} msg={ci.get('retMsg')}")
    rows=(ci.get("result") or {}).get("rows") or []
    if not rows:
        fail("Bybit coin-info returned empty rows")
    required={"chain","chainType","chainDeposit","chainWithdraw","contractAddress"}
    chain_count=0
    bad=0
    for coin in rows:
        if not isinstance(coin,dict):
            bad+=1
            continue
        chains=coin.get("chains") or []
        for ch in chains:
            chain_count+=1
            if not isinstance(ch,dict) or not required.issubset(ch):
                bad+=1
    if chain_count<=0 or bad:
        fail(f"Bybit coin-info schema invalid: chains={chain_count} bad={bad}")

    return {
        "base_url":base,
        "clock_skew_ms":skew,
        "readOnly":readonly,
        "ip_bound":bool(result.get("ips") or []),
        "permission_categories":sorted(permissions.keys()),
        "wallet_withdraw_permission_token_present":withdraw_token,
        "coin_rows":len(rows),
        "chain_rows":chain_count,
        "schema_pass":True,
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("run",),default="run")
    ap.parse_args()
    try:
        require_freeze()
        cfg=parse_env(ENV_FILE)
        okx=check_okx(cfg)
        bybit=check_bybit(cfg)

        clock_ok=(
            abs(int(okx["clock_skew_ms"]))<=MAX_CLOCK_SKEW_MS
            and abs(int(bybit["clock_skew_ms"]))<=MAX_CLOCK_SKEW_MS
        )
        if not clock_ok:
            fail(f"clock skew exceeds {MAX_CLOCK_SKEW_MS} ms")

        print(PASS)
        print("OKX base_url =",okx["base_url"])
        print("OKX permission =",okx["permission"])
        print("OKX IP bound =",okx["ip_bound"])
        print("OKX currency/chain rows =",okx["currency_chain_rows"])
        print("OKX clock skew ms =",okx["clock_skew_ms"])
        print("Bybit base_url =",bybit["base_url"])
        print("Bybit readOnly =",bybit["readOnly"])
        print("Bybit IP bound =",bybit["ip_bound"])
        print("Bybit wallet Withdraw token present =",bybit["wallet_withdraw_permission_token_present"])
        print("Bybit coin rows =",bybit["coin_rows"],"chain rows =",bybit["chain_rows"])
        print("Bybit clock skew ms =",bybit["clock_skew_ms"])
        print("secret_values_printed = False")
        print("price/order/transfer/withdraw endpoints called = False")
        return 0
    except Exception as exc:
        print(REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        print("secret_values_printed = False")
        return 2

if __name__=="__main__":
    raise SystemExit(main())
