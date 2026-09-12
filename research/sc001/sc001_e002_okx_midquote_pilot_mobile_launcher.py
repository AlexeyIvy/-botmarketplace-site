"""Pinned Android/Pydroid launcher for SC001-E002 OKX midquote pilot v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "94c77febc73601c76976da4ab71bedecc69a485a"
ENGINE_PATH = "research/sc001/sc001_e002_okx_midquote_pilot.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_e002_okx_midquote_pilot_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-E002 OKX MIDQUOTE PILOT PINNED LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Fixed date: 2024-01-05")
    print("Uses existing Q006/Q006R trades + Q008 full L2; market-data download: NO")
    print("Primary: 5s TFI -> 5s L2 midquote response @ 100ms")
    print("250ms stress / 500ms diagnostic")
    print("P&L: NO | Q2/Validation/Final: NO")
    print("Full replay progress prints every 1,000,000 L2 records")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-E002-MIDQUOTE-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("midquote engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-E002-OKX-MIDQUOTE-PILOT"',
        b'PROTOCOL_COMMIT = "4408d09e9a746804cfe2f65d01c0917100196c03"',
        b'DATE = "2024-01-05"',
        b'GRID_MS = 5_000',
        b'HORIZON_MS = 5_000',
        b'LATENCIES_MS = (100, 250, 500)',
        b'EXPECTED_DECISIONS = 17_109',
        b'EXPECTED_L2_BYTES = 500_060_536',
        b'EXPECTED_L2_SHA256',
        b'midquote_response_calculated',
        b'strategy_pnl_calculated',
        b'q2_okx_accessed',
        b'validation_or_final_accessed',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen midquote pilot engine")

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
