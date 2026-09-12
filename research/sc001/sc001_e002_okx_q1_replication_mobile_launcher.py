"""Pinned Android/Pydroid launcher for SC001-E002 OKX Q1 replication v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "b0dbd0fabf7d0bf665282c65a71f37df97b48dbe"
ENGINE_PATH = "research/sc001/sc001_e002_okx_q1_replication.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_e002_okx_q1_replication_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-E002 OKX Q1 REPLICATION PINNED LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: exact frozen E002 mechanism on five Q006R-qualified OKX Q1 UTC days")
    print("Primary: 5s TFI -> next 5s transaction-price response @ 100ms")
    print("Primary sign gate: 5/5 positive days")
    print("250ms stress: >=4/5 positive days")
    print("P&L: NO | L2 economics: NO | Q2 OKX: NO | Validation/Final: NO")
    print("Network market-data download: NO")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-E002-OKX-Q1-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("OKX replication engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-E002-OKX-Q1-REPLICATION"',
        b'PROTOCOL_COMMIT = "dccf2fd4e95996a77b980e1ca0c3ad0c5662416f"',
        b'GRID_MS = 5_000',
        b'LOOKBACK_MS = 5_000',
        b'HORIZON_MS = 5_000',
        b'LATENCIES_MS = (100, 250, 500)',
        b'EXPECTED_DAYS = 5',
        b'PRIMARY_POSITIVE_DAY_GATE = 5',
        b'STRESS_POSITIVE_DAY_GATE = 4',
        b'PRIMARY_EXTREME_SPREAD_POSITIVE_DAY_GATE = 5',
        b'q2_okx_accessed',
        b'strategy_pnl_calculated',
        b'execution_profitability_calculated',
        b'validation_or_final_accessed',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen OKX replication engine")

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
