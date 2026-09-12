"""Pinned Android/Pydroid launcher for SC001-DATA-A002-B04B05 v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "e79bd6bee8f470309c9fde33cd8020df54d2ef8e"
ENGINE_PATH = "research/sc001/sc001_data_a002_b04b05_confirmation.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_a002_b04b05_confirmation_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-A002-B04B05 PINNED MOBILE LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: 10 frozen DEV-CONFIRMATION aggTrades days, 2024-Q1 + 2024-Q2")
    print("Expected compressed bytes: 194,145,949")
    print("TFI/features: NO | P&L: NO | confirmation metrics: NO")
    print("VALIDATION/FINAL: NO")
    print("Session/workspace cap: 300 MB | reserve: 4 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-A002-B04B05-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("B04B05 engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-DATA-A002-B04B05"',
        b'EXPECTED_TOTAL_COMPRESSED_BYTES = 194_145_949',
        b'EXPECTED_DAYS = 10',
        b'SESSION_DOWNLOAD_CAP_BYTES = 300_000_000',
        b'WORKSPACE_CAP_BYTES = 300_000_000',
        b'confirmation_metrics_calculated',
        b'strategy_features_calculated',
        b'strategy_pnl_calculated',
        b'DEV_CONFIRMATION_ACQUISITION_ONLY',
        b'validation_or_final_accessed',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen B04B05 engine")

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
