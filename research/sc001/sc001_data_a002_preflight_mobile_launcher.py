"""Pinned Android/Pydroid launcher for SC001-DATA-A002-PREFLIGHT v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "426ba1df7089eaf9cb1826087febf101a647c8f9"
ENGINE_PATH = "research/sc001/sc001_data_a002_preflight.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/"
    "AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/"
    + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_a002_preflight_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-A002-PREFLIGHT PINNED MOBILE LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: frozen 25 DEV aggTrades dates only")
    print("Archive bodies: NOT DOWNLOADED")
    print("Strategy/P&L: NO")
    print("Preflight network cap: 50 MB")
    print("Later single archive cap: 256 MB")
    print("Later quarter batch cap: 1.0 GB")
    print("Later session cap: 2.0 GB")
    print("Minimum free-storage reserve: 4.0 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={
            "User-Agent":
            "BotMarketplace-SC001-DATA-A002-PREFLIGHT-launcher/0.1"
        },
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)

    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("A002 preflight engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-DATA-A002-PREFLIGHT"',
        b'EXPECTED_DEV_DAYS = 25',
        b'FROZEN_CALENDAR_SHA256 = "e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b"',
        b'SESSION_NETWORK_CAP_BYTES = 50_000_000',
        b'LATER_SINGLE_ARCHIVE_CAP_BYTES = 256_000_000',
        b'LATER_QUARTER_BATCH_CAP_BYTES = 1_000_000_000',
        b'LATER_SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000',
        b'archive_bodies_downloaded',
        b'strategy_pnl_calculated',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen A002 preflight engine")

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
