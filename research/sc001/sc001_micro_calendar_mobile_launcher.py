"""Pinned Android/Pydroid launcher for SC001-MICRO-CALENDAR-v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")

ENGINE_COMMIT = "f413ab66e4ac6ab9ba083e222fd3262537548067"
ENGINE_PATH = "research/sc001/sc001_micro_calendar_v0_1.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/"
    "AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/"
    + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_micro_calendar_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-MICRO-CALENDAR PINNED MOBILE LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Strategy/P&L: NO")
    print("Bulk tick/L2 download: NO")
    print("Official macro HTML only")
    print("Network cap inside engine: 50 MB")
    print("Minimum free-storage reserve: 4 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={
            "User-Agent": "BotMarketplace-SC001-MICRO-CALENDAR-launcher/0.1"
        },
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)

    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("Calendar engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-MICRO-CALENDAR-v0.1"',
        b'SEED = "SC001-MICRO-v0.1-20260911"',
        b"SESSION_DOWNLOAD_CAP_BYTES = 50_000_000",
        b'"FINAL": ("2025-07-01", "2026-08-31")',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen calendar engine")

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
