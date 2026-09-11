"""Pinned Android/Pydroid launcher for SC001-DATA-A001 v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")

ENGINE_COMMIT = "cb421d2a4f55c083d44406e9f8a32b68a88b0f5b"
ENGINE_PATH = "research/sc001/sc001_data_a001_binance_dev_1m.py"

ENGINE_URL = (
    "https://raw.githubusercontent.com/"
    "AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/"
    + ENGINE_PATH
)

LOCAL_ENGINE = DOWNLOAD / "sc001_data_a001_binance_dev_1m_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-A001 PINNED MOBILE LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Venue: Binance USD-M BTCUSDT")
    print("Interval: 1m")
    print("Scope: DEV ONLY (2023-04 through 2024-06)")
    print("VALIDATION/FINAL minute data: NOT DOWNLOADED")
    print("Strategy/P&L: NO")
    print("Session cap: 2.00 GB")
    print("Workspace cap: 2.00 GB")
    print("Per monthly archive cap: 100 MB")
    print("Minimum free-storage reserve: 4.00 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={
            "User-Agent":
            "BotMarketplace-SC001-DATA-A001-launcher/0.1"
        },
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)

    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("A001 engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-DATA-A001"',
        b"START_MONTH = (2023, 4)",
        b"END_MONTH = (2024, 6)",
        b"SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000",
        b"PER_FILE_CAP_BYTES = 100_000_000",
        b"strategy_pnl_calculated",
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen A001 engine")

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
