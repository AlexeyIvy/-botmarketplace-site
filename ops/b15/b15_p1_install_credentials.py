#!/usr/bin/env python3
from __future__ import annotations

import getpass
import os
import shlex
from pathlib import Path

OUT=Path("/home/botmarket/.config/sc001/b15-p1.env")

def ask_secret(label:str)->str:
    v=getpass.getpass(label).strip()
    if not v:
        raise SystemExit(f"ERROR: empty value for {label}")
    if "\n" in v or "\r" in v or "\x00" in v:
        raise SystemExit(f"ERROR: invalid control character in {label}")
    return v

def ask_default(label:str,default:str)->str:
    v=input(f"{label} [{default}]: ").strip()
    return v or default

print("SC001 B15-P1 credential installer")
print("Values are entered locally on VPS and are NOT printed.")
print()

okx_key=ask_secret("OKX API key: ")
okx_secret=ask_secret("OKX API secret: ")
okx_pass=ask_secret("OKX passphrase: ")
okx_base=ask_default("OKX REST base URL","https://openapi.okx.com").rstrip("/")

bybit_key=ask_secret("Bybit API key: ")
bybit_secret=ask_secret("Bybit API secret: ")
bybit_base=ask_default("Bybit REST base URL","https://api.bybit.com").rstrip("/")

vals={
    "SC001_B15_OKX_API_KEY":okx_key,
    "SC001_B15_OKX_API_SECRET":okx_secret,
    "SC001_B15_OKX_PASSPHRASE":okx_pass,
    "SC001_B15_OKX_BASE_URL":okx_base,
    "SC001_B15_BYBIT_API_KEY":bybit_key,
    "SC001_B15_BYBIT_API_SECRET":bybit_secret,
    "SC001_B15_BYBIT_BASE_URL":bybit_base,
}

OUT.parent.mkdir(parents=True,exist_ok=True)
tmp=OUT.with_suffix(".env.tmp")
with tmp.open("w",encoding="utf-8") as f:
    f.write("# SC001 B15-P1 dedicated read-only credentials\n")
    for k,v in vals.items():
        f.write(f"{k}={shlex.quote(v)}\n")
    f.flush()
    os.fsync(f.fileno())
os.chmod(tmp,0o600)
os.replace(tmp,OUT)
os.chmod(OUT,0o600)

st=OUT.stat()
mode=oct(st.st_mode & 0o777)
print()
print("B15_P1_CREDENTIAL_FILE_CREATED")
print("path =",OUT)
print("mode =",mode)
print("secret_values_printed = False")
