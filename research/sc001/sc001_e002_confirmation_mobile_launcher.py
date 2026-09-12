"""Pinned Android/Pydroid launcher for SC001-E002 DEV-CONFIRMATION v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "2ed18549aa3f6520e8d4c7c5b35ed42ee9a2f460"
ENGINE_PATH = "research/sc001/sc001_e002_confirmation_screen.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_e002_confirmation_screen_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-E002 DEV-CONFIRMATION PINNED LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: exact frozen E002 on 10 DEV-CONFIRMATION days")
    print("Primary: 5s TFI -> next 5s transaction-price response @ 100ms")
    print("Primary sign gate: >=9/10 positive days")
    print("Median retention gate: >=0.06468345784701792")
    print("P&L: NO | VALIDATION/FINAL: NO")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-E002-CONFIRMATION-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("confirmation engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-E002-CONFIRMATION"',
        b'CONFIRMATION_PROTOCOL_COMMIT = "ed0aa3e6f462421c7b057bb1ab57b903dc541f95"',
        b'GRID_MS = 5_000',
        b'HORIZON_MS = 5_000',
        b'LATENCIES_MS = (100, 250, 500)',
        b'EXPECTED_DAYS = 10',
        b'PRIMARY_POSITIVE_DAY_GATE = 9',
        b'MIN_CONFIRMATION_MEDIAN_SPEARMAN_100MS = 0.06468345784701792',
        b'validation_or_final_accessed',
        b'strategy_pnl_calculated',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen confirmation engine")

    LOCAL_ENGINE.write_bytes(raw)
    print("Frozen engine:", LOCAL_ENGINE)
    print("SHA256:", hashlib.sha256(raw).hexdigest())
    print()

    code = compile(raw, str(LOCAL_ENGINE), "exec")
    ns = {
        "__name__": "__main__",
        "__file__": str(LOCAL_ENGINE),
        "__package__": None,
    }
    exec(code, ns, ns)


if __name__ == "__main__":
    main()
