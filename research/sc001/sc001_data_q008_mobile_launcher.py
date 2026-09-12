"""Pinned Android/Pydroid launcher for SC001-DATA-Q008 v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "d4aa9720e43a39e215af7d866bd273c68340381c"
ENGINE_PATH = "research/sc001/sc001_data_q008_okx_l2_full_day_pilot.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q008_okx_l2_full_day_pilot_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-Q008 OKX FULL-DAY L2 PILOT v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Fixed date: 2024-01-05")
    print("Expected archive: 500,060,536 bytes")
    print("Full streamed replay; no extracted member on disk")
    print("TFI/midquote alpha/P&L: NO | Q2/Validation/Final: NO")
    print("Session/workspace cap: 700 MB | per-file: 650 MB | reserve: 4 GB")
    print("Interrupted .part download can be resumed on rerun")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-Q008-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("Q008 engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-DATA-Q008-OKX-L2-FULL-DAY-PILOT"',
        b'PROTOCOL_COMMIT = "ada4a6d2ef95fca1bb40f37553d6d630afa00579"',
        b'PILOT_DATE = "2024-01-05"',
        b'EXPECTED_BYTES = 500_060_536',
        b'SESSION_DOWNLOAD_CAP_BYTES = 700_000_000',
        b'WORKSPACE_CAP_BYTES = 700_000_000',
        b'PER_FILE_CAP_BYTES = 650_000_000',
        b'midquote_response_calculated',
        b'strategy_pnl_calculated',
        b'q2_okx_accessed',
        b'validation_or_final_accessed',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen Q008 engine")

    LOCAL_ENGINE.write_bytes(raw)
    print("Frozen engine:", LOCAL_ENGINE)
    print("SHA256:", hashlib.sha256(raw).hexdigest())
    print()

    code = compile(raw, str(LOCAL_ENGINE), "exec")
    ns = {"__name__": "__main__", "__file__": str(LOCAL_ENGINE), "__package__": None}
    exec(code, ns, ns)


if __name__ == "__main__":
    main()
