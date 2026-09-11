"""Pinned Android/Pydroid launcher for frozen SC001-DATA-Q001.

Downloads the exact committed qualification collector and runs it.
Q001 intentionally downloads only small fixed-date qualification samples
and does NOT bulk-download OKX L2 history.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "15fced2b76273ed43832b608c957c9e36d152381"
ENGINE_PATH = "research/sc001/sc001_data_q001_multi_venue_qualifier.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q001_multi_venue_qualifier_v0_1.py"


def download_engine() -> bytes:
    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "botmarketplace-sc001-data-q001-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read()

    required = [b"SC001-DATA-Q001", b'QUAL_DATE = "2025-01-15"', b"Bulk OKX L2 download: NO"]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file does not look like the frozen SC001-DATA-Q001 collector")

    LOCAL_ENGINE.write_bytes(raw)
    return raw


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-Q001 PINNED MOBILE LAUNCHER v0.1")
    print("Collector commit:", ENGINE_COMMIT)
    print("Qualification date: 2025-01-15 UTC")
    print("Downloads: small Binance + Bybit samples only")
    print("OKX bulk L2 download: NO")
    print("Strategy/P&L calculations: NO")
    print("=" * 78)

    raw = download_engine()
    print("Frozen collector downloaded:", LOCAL_ENGINE)
    print("Collector SHA256:", hashlib.sha256(raw).hexdigest())
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
