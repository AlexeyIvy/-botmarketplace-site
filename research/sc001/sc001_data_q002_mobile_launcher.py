"""Pinned Android/Pydroid launcher for SC001-DATA-Q002.

Downloads the exact committed Q002 validator and runs it. The validator itself
has a hard 2,000,000,000-byte session download cap, a 2 GB workspace cap,
a 512 MB per-response cap, and keeps at least 4 GB free-storage reserve.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "1335f0569eed3ffa1e0ccc5491f185d65600b5c4"
ENGINE_PATH = "research/sc001/sc001_data_q002_staged_validator.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q002_staged_validator_v0_1.py"


def main():
    print("=" * 78)
    print("SC001-DATA-Q002 PINNED MOBILE LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Hard session download cap inside engine: 2.00 GB")
    print("Hard Q002 workspace cap inside engine: 2.00 GB")
    print("Per-response cap inside engine: 512 MB")
    print("Minimum free-storage reserve: 4.00 GB")
    print("Bulk OKX L2 download: NO")
    print("Strategy/P&L: NO")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-DATA-Q002-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(2_000_000)

    required = [
        b"SC001-DATA-Q002",
        b"SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000",
        b"WORKSPACE_CAP_BYTES = 2_000_000_000",
        b"Bulk L2 download: NO",
    ]
    if not raw or not all(x in raw for x in required):
        raise RuntimeError("Downloaded file is not the frozen Q002 validator")

    LOCAL_ENGINE.write_bytes(raw)
    print("Validator:", LOCAL_ENGINE)
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
