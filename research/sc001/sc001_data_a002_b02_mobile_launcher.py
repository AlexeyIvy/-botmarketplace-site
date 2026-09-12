"""Pinned Android/Pydroid launcher for SC001-DATA-A002-B02 v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "b2895a571eab3d4e205e40e629791e8d767b139e"
ENGINE_PATH = "research/sc001/sc001_data_a002_b02_2023q3.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/"
    + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_a002_b02_2023q3_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-A002-B02 PINNED MOBILE LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: Binance USD-M BTCUSDT aggTrades, DEV-DISCOVERY 2023-Q3 only")
    print("Frozen days: 5")
    print("Expected compressed bytes: 53,592,159")
    print("Strategy/P&L: NO")
    print("Strategy features: NO")
    print("VALIDATION/FINAL: NO")
    print("Session cap: 200 MB | workspace cap: 200 MB | reserve: 4 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-A002-B02-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)

    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("A002-B02 engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-DATA-A002-B02"',
        b'BATCH_ID = "2023-Q3"',
        b'SESSION_DOWNLOAD_CAP_BYTES = 200_000_000',
        b'EXPECTED_BATCH_COMPRESSED_BYTES = 53_592_159',
        (
            b'FROZEN_CALENDAR_SHA256 = '
            b'"e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b"'
        ),
        b'strategy_pnl_calculated',
        b'strategy_features_calculated',
        b'validation_or_final_accessed',
        b'DEV_DISCOVERY_ONLY',
    ]

    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen A002-B02 engine")

    LOCAL_ENGINE.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    print("Frozen engine:", LOCAL_ENGINE)
    print("SHA256:", digest)
    print()

    # Mandatory local syntax compilation before any engine execution.
    code = compile(raw, str(LOCAL_ENGINE), "exec")
    ns = {
        "__name__": "__main__",
        "__file__": str(LOCAL_ENGINE),
        "__package__": None,
    }
    exec(code, ns, ns)


if __name__ == "__main__":
    main()
