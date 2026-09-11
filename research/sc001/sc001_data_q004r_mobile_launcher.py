"""Pinned Android/Pydroid launcher for SC001-DATA-Q004R v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "65a6e3300d590c9f152e58ae4bba7b6dba3a80b7"
ENGINE_PATH = "research/sc001/sc001_data_q004r_semantic_replay.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/"
    + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q004r_semantic_replay_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main():
    print("=" * 78)
    print("SC001-DATA-Q004R PINNED MOBILE LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Full OKX L2 archive download: NO")
    print("Range per epoch: 8 MiB")
    print("Planned network: <= 40 MiB")
    print("Emergency session cap: 2.00 GB")
    print("Minimum free-storage reserve: 4.00 GB")
    print("Strategy/P&L: NO")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-DATA-Q004R-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)

    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("Q004R engine exceeds launcher safety limit")

    required = [
        b"SC001-DATA-Q004R",
        b"RANGE_BYTES = 8 * 1024 * 1024",
        b"SESSION_DOWNLOAD_CAP_BYTES = 2_000_000_000",
        b"semantic_replay",
        b"No strategy/P&L. No full archive download.",
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen Q004R engine")

    LOCAL_ENGINE.write_bytes(raw)
    print("Frozen Q004R engine:", LOCAL_ENGINE)
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
