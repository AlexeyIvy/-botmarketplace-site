"""Pinned Android/Pydroid launcher for SC001-DATA-A002-B01 v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "7c72f2c27d41c4a546bc87369671bda33e6ab7c5"
ENGINE_PATH = "research/sc001/sc001_data_a002_b01_2023q2.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_a002_b01_2023q2_v0_1.py"
MAX_ENGINE_BYTES = 1_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-A002-B01 PINNED MOBILE LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: Binance USD-M BTCUSDT aggTrades, DEV 2023-Q2 only")
    print("Frozen days: 5")
    print("Expected compressed bytes: 91,819,076")
    print("Strategy/P&L: NO")
    print("Strategy features: NO")
    print("VALIDATION/FINAL: NO")
    print("Session cap: 300 MB | workspace cap: 300 MB | reserve: 4 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-A002-B01-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)

    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("A002-B01 engine exceeds launcher safety limit")

    required = [
        b'STAGE="SC001-DATA-A002-B01"',
        b'BATCH_ID="2023-Q2"',
        b'SESSION_DOWNLOAD_CAP_BYTES=300_000_000',
        b'EXPECTED_BATCH_COMPRESSED_BYTES=91_819_076',
        b'FROZEN_CALENDAR_SHA256="e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b"',
        b"strategy_pnl_calculated",
        b"strategy_features_calculated",
        b"validation_or_final_accessed",
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen A002-B01 engine")

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
