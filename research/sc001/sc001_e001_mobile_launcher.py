"""Pinned Android/Pydroid launcher for frozen SC001-E001.

Downloads the exact frozen engine commit and runs it against the existing
R003_E002_WORKSPACE cache. It does not download market data and does not
modify any R003/R009/R010/S002 artifact.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "a0a18910ee7518164ad14cc3d88bdcac36e8d3c0"
ENGINE_PATH = "research/sc001/sc001_e001_extreme_move_mean_reversion.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_e001_extreme_move_mean_reversion_v0_1.py"
R003_WS = DOWNLOAD / "R003_E002_WORKSPACE"


def download_engine() -> bytes:
    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "botmarketplace-sc001-e001-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read()
    if not raw or b"SC001-E001" not in raw or b"K_PRIMARY = 2.00" not in raw:
        raise RuntimeError("Downloaded file does not look like the frozen SC001-E001 engine")
    LOCAL_ENGINE.write_bytes(raw)
    return raw


def main() -> None:
    print("=" * 76)
    print("SC001-E001 FROZEN MOBILE LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Market-data download: NO")
    print("Uses existing R003_E002_WORKSPACE cache only")
    print("=" * 76)

    if not R003_WS.exists():
        raise FileNotFoundError(
            "Missing /storage/emulated/0/Download/R003_E002_WORKSPACE. "
            "Do not redownload market data yet; first restore/use the existing workspace."
        )

    cache_dir = R003_WS / "_cache"
    cache_zip = R003_WS / "_cache_bundle.zip"
    if not cache_dir.exists() and not cache_zip.exists():
        raise FileNotFoundError(
            "R003 workspace exists, but neither _cache nor _cache_bundle.zip was found."
        )

    raw = download_engine()
    print("Frozen engine downloaded:", LOCAL_ENGINE)
    print("Engine SHA256:", hashlib.sha256(raw).hexdigest())
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
