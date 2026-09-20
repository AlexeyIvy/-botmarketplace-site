#!/usr/bin/env python3
from __future__ import annotations

import os
import shlex
from pathlib import Path

ENV=Path("/home/botmarket/.config/sc001/b15-p1.env")
TARGET="https://api.bybit.com"

if not ENV.exists():
    raise SystemExit(f"ERROR: missing {ENV}")

rows=[]
seen=False
for raw in ENV.read_text(encoding="utf-8").splitlines():
    if raw.startswith("SC001_B15_BYBIT_BASE_URL="):
        rows.append("SC001_B15_BYBIT_BASE_URL="+shlex.quote(TARGET))
        seen=True
    else:
        rows.append(raw)

if not seen:
    rows.append("SC001_B15_BYBIT_BASE_URL="+shlex.quote(TARGET))

tmp=ENV.with_suffix(".env.tmp")
with tmp.open("w",encoding="utf-8") as f:
    f.write("\n".join(rows)+"\n")
    f.flush()
    os.fsync(f.fileno())

os.chmod(tmp,0o600)
os.replace(tmp,ENV)
os.chmod(ENV,0o600)

print("B15_P1_BYBIT_BASE_URL_FIXED")
print("Bybit base URL =",TARGET)
print("credentials changed = False")
print("mode =",oct(ENV.stat().st_mode & 0o777))
