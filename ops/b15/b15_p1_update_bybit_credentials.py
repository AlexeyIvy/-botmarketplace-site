#!/usr/bin/env python3
from __future__ import annotations

import getpass
import os
import shlex
from pathlib import Path
from urllib.parse import urlparse

ENV=Path("/home/botmarket/.config/sc001/b15-p1.env")

def fail(msg:str)->None:
    raise SystemExit("ERROR: "+msg)

def load_env(path:Path)->dict[str,str]:
    if not path.exists():
        fail(f"credential file missing: {path}")
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
            fail(f"malformed value for {k}")
        out[k]=parts[0]
    return out

def normalize_bybit_base(value:str)->str:
    raw=(value or "").strip().rstrip("/")
    if not raw:
        raw="https://api.bybit.com"
    parsed=urlparse(raw)
    if parsed.scheme!="https" or not parsed.netloc:
        fail("Bybit REST base URL must be a full https:// URL")
    allowed={"api.bybit.com","api-demo.bybit.com","api-testnet.bybit.com"}
    host=(parsed.hostname or "").lower()
    if host not in allowed:
        fail(f"unexpected Bybit API host: {host}")
    if parsed.path not in ("","/") or parsed.query or parsed.fragment:
        fail("Bybit REST base URL must not include a path/query/fragment")
    return "https://"+host

def ask_secret(label:str)->str:
    value=getpass.getpass(label).strip()
    if not value:
        fail(f"empty value for {label}")
    if "\n" in value or "\r" in value or "\x00" in value:
        fail(f"invalid control character in {label}")
    return value

cfg=load_env(ENV)

required_okx=(
    "SC001_B15_OKX_API_KEY",
    "SC001_B15_OKX_API_SECRET",
    "SC001_B15_OKX_PASSPHRASE",
    "SC001_B15_OKX_BASE_URL",
)
for k in required_okx:
    if not cfg.get(k):
        fail(f"existing OKX credential missing: {k}")

print("SC001 B15-P1 Bybit-only credential updater")
print("Existing OKX credentials will be preserved unchanged.")
print("New Bybit values are entered locally on VPS and are NOT printed.")
print()

bybit_key=ask_secret("NEW Bybit API key: ")
bybit_secret=ask_secret("NEW Bybit API secret: ")

stored_base=cfg.get("SC001_B15_BYBIT_BASE_URL","")
try:
    default_base=normalize_bybit_base(stored_base)
except SystemExit:
    default_base="https://api.bybit.com"

raw=input(f"Bybit REST base URL [{default_base}]: ").strip()
bybit_base=normalize_bybit_base(raw or default_base)

cfg["SC001_B15_BYBIT_API_KEY"]=bybit_key
cfg["SC001_B15_BYBIT_API_SECRET"]=bybit_secret
cfg["SC001_B15_BYBIT_BASE_URL"]=bybit_base

order=(
    "SC001_B15_OKX_API_KEY",
    "SC001_B15_OKX_API_SECRET",
    "SC001_B15_OKX_PASSPHRASE",
    "SC001_B15_OKX_BASE_URL",
    "SC001_B15_BYBIT_API_KEY",
    "SC001_B15_BYBIT_API_SECRET",
    "SC001_B15_BYBIT_BASE_URL",
)

tmp=ENV.with_suffix(".env.tmp")
with tmp.open("w",encoding="utf-8") as f:
    f.write("# SC001 B15-P1 dedicated read-only credentials\n")
    for k in order:
        if not cfg.get(k):
            fail(f"missing value for {k}")
        f.write(f"{k}={shlex.quote(cfg[k])}\n")
    f.flush()
    os.fsync(f.fileno())

os.chmod(tmp,0o600)
os.replace(tmp,ENV)
os.chmod(ENV,0o600)

print()
print("B15_P1_BYBIT_CREDENTIALS_UPDATED")
print("OKX credentials preserved = True")
print("path =",ENV)
print("mode =",oct(ENV.stat().st_mode & 0o777))
print("secret_values_printed = False")
