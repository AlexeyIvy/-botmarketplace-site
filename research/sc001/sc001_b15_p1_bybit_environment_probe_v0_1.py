from __future__ import annotations

import base64
import hashlib
import hmac
import json
import shlex
import socket
import stat
import time
import urllib.error
import urllib.request
from pathlib import Path

ENV_FILE=Path("/home/botmarket/.config/sc001/b15-p1.env")
RECV_WINDOW="5000"
TIMEOUT=20
MAX_JSON=1_000_000

_ORIG_GETADDRINFO=socket.getaddrinfo
def ipv4_only_getaddrinfo(host,port,family=0,type=0,proto=0,flags=0):
    return _ORIG_GETADDRINFO(host,port,socket.AF_INET,type,proto,flags)
socket.getaddrinfo=ipv4_only_getaddrinfo

def load_env():
    if stat.S_IMODE(ENV_FILE.stat().st_mode)!=0o600:
        raise RuntimeError("credential file mode must be 0600")
    out={}
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line=raw.strip()
        if not line or line.startswith("#"):
            continue
        k,v=line.split("=",1)
        parts=shlex.split(v,posix=True)
        if len(parts)!=1:
            raise RuntimeError(f"bad env value: {k}")
        out[k]=parts[0]
    return out

def request(base,key,secret):
    ts=str(int(time.time()*1000))
    query=""
    payload=ts+key+RECV_WINDOW+query
    sig=hmac.new(secret.encode(),payload.encode(),hashlib.sha256).hexdigest()
    headers={
        "User-Agent":"BotMarketplace-SC001-B15-P1-ENV-PROBE/0.1",
        "Accept":"application/json",
        "X-BAPI-API-KEY":key,
        "X-BAPI-TIMESTAMP":ts,
        "X-BAPI-RECV-WINDOW":RECV_WINDOW,
        "X-BAPI-SIGN":sig,
    }
    req=urllib.request.Request(base+"/v5/user/query-api",headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
            raw=resp.read(MAX_JSON+1)
    except urllib.error.HTTPError as exc:
        raw=exc.read(MAX_JSON+1)
    obj=json.loads(raw.decode("utf-8","replace"))
    if not isinstance(obj,dict):
        raise RuntimeError("unexpected response shape")
    result=obj.get("result") or {}
    return {
        "retCode":obj.get("retCode"),
        "retMsg":obj.get("retMsg"),
        "readOnly":result.get("readOnly"),
    }

cfg=load_env()
key=cfg["SC001_B15_BYBIT_API_KEY"]
secret=cfg["SC001_B15_BYBIT_API_SECRET"]

targets=[
    ("MAINNET","https://api.bybit.com"),
    ("DEMO","https://api-demo.bybit.com"),
    ("TESTNET","https://api-testnet.bybit.com"),
]

winner=None
for label,base in targets:
    try:
        r=request(base,key,secret)
        print(label,"retCode =",r["retCode"],"retMsg =",r["retMsg"])
        if r["retCode"]==0:
            print(label,"readOnly =",r["readOnly"])
            winner=label
    except Exception as exc:
        print(label,"probe_error =",type(exc).__name__)

print("BYBIT_ENVIRONMENT =",winner or "UNRESOLVED")
print("secret_values_printed = False")
print("price/order/transfer/withdraw endpoints called = False")
