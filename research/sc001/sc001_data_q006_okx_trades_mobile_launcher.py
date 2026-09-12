"""Pinned Android/Pydroid launcher for SC001-DATA-Q006 v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "64897957fcae86ece5e8385080e1e2469e447903"
ENGINE_PATH = "research/sc001/sc001_data_q006_okx_trades_acquire.py"
ENGINE_URL = "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/" + ENGINE_COMMIT + "/" + ENGINE_PATH
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q006_okx_trades_acquire_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-Q006 OKX Q1 TRADE ACQUISITION v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: 5 frozen 2024-Q1 OKX BTC-USDT-SWAP trade archives")
    print("Expected compressed total: 30,080,404 bytes")
    print("Data/schema qualification only; TFI/returns/P&L: NO")
    print("2024-Q2 OKX: NO | Validation/Final: NO")
    print("Session/workspace cap: 100 MB | per-file: 25 MB | reserve: 4 GB")
    print("=" * 78)

    req = Request(ENGINE_URL, headers={"User-Agent": "BotMarketplace-SC001-Q006-launcher/0.1"})
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("Q006 engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-DATA-Q006-OKX-TRADES"',
        b'EXPECTED_TOTAL_COMPRESSED_BYTES = 30_080_404',
        b'SESSION_DOWNLOAD_CAP_BYTES = 100_000_000',
        b'WORKSPACE_CAP_BYTES = 100_000_000',
        b'PER_FILE_CAP_BYTES = 25_000_000',
        b'strategy_features_calculated',
        b'future_returns_calculated',
        b'strategy_pnl_calculated',
        b'q2_okx_accessed',
        b'validation_or_final_accessed',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen Q006 engine")

    LOCAL_ENGINE.write_bytes(raw)
    print("Frozen engine:", LOCAL_ENGINE)
    print("SHA256:", hashlib.sha256(raw).hexdigest())
    print()

    code = compile(raw, str(LOCAL_ENGINE), "exec")
    ns = {"__name__": "__main__", "__file__": str(LOCAL_ENGINE), "__package__": None}
    exec(code, ns, ns)


if __name__ == "__main__":
    main()
