"""Pinned Android/Pydroid launcher for SC001-DATA-Q003 v0.2."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "0689ee93a36028aa19208ffcfc7882caf8107681"
ENGINE_PATH = "research/sc001/sc001_data_q003_okx_l2_qualifier.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q003_okx_l2_qualifier_v0_2.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-Q003 PINNED MOBILE LAUNCHER v0.2")
    print("Engine commit:", ENGINE_COMMIT)
    print("Strategy/P&L: NO")
    print("Multi-year/bulk L2 download: NO")
    print("Hard session cap inside engine: 2.00 GB")
    print("Hard workspace cap inside engine: 2.00 GB")
    print("Single archive cap inside engine: 512 MB")
    print("Minimum free-storage reserve: 4.00 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-DATA-Q003-launcher/0.2"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)

    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("Q003 engine unexpectedly exceeds launcher safety limit")

    required = [
        b"SC001-DATA-Q003",
        b"SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000",
        b"WORKSPACE_CAP_BYTES = 2_000_000_000",
        b"PER_FILE_CAP_BYTES = 512_000_000",
        b'PRIMARY_DOWNLOAD_DATE = "2025-01-15"',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen Q003 engine")

    LOCAL_ENGINE.write_bytes(raw)
    print("Frozen Q003 engine:", LOCAL_ENGINE)
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
