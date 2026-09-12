"""Pinned Android/Pydroid launcher for SC001-E002 v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "95ab41d5c6db58101ce19ebb56b459927c3a20e2"
ENGINE_PATH = "research/sc001/sc001_e002_tfi_screen.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_e002_tfi_screen_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-E002 PINNED MOBILE LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Experiment: Aggressive Trade-Flow Continuation Screen")
    print("Scope: DEV-DISCOVERY only, B01+B02+B03 = 15 days")
    print("Primary: 5s TFI -> next 5s transaction-price response")
    print("Latencies: 100ms primary / 250ms stress / 500ms diagnostic")
    print("Strategy P&L: NO")
    print("B04/B05: MUST REMAIN UNOPENED")
    print("VALIDATION/FINAL: MUST REMAIN UNOPENED")
    print("Network download: NO")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-E002-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("E002 engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-E002"',
        b'PROTOCOL_COMMIT = "4022da85f5ffb873d558ccda74d20b8c16272ba7"',
        b'GRID_MS = 5_000',
        b'LOOKBACK_MS = 5_000',
        b'HORIZON_MS = 5_000',
        b'LATENCIES_MS = (100, 250, 500)',
        b'POSITIVE_DAY_GATE = 12',
        b'EXPECTED_DAYS = 15',
        b'b04_b05_accessed',
        b'validation_or_final_accessed',
        b'strategy_pnl_calculated',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen SC001-E002 engine")

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
