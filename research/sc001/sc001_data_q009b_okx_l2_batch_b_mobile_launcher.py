"""Pinned Android/Pydroid launcher for SC001-DATA-Q009B v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "14deaea9d5638c32e380065855cabe740b6cc61e"
ENGINE_PATH = "research/sc001/sc001_data_q009b_okx_l2_batch_b.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q009b_okx_l2_batch_b_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-Q009B OKX Q1 L2 BATCH B v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Dates: 2024-02-12 + 2024-02-13")
    print("Expected market-data bytes: 1,152,651,597")
    print("Full-day replay qualification only")
    print("TFI/midquote alpha/P&L: NO")
    print("Q2/Validation/Final: NO")
    print("Cap: 1.35 GB | per-file: 650 MB | reserve: 4 GB")
    print("Completed files are reused; .part downloads resume on rerun")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-Q009B-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)

    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("Q009B engine too large")

    required = [
        b'STAGE = "SC001-DATA-Q009B-OKX-L2-Q1-BATCH-B"',
        b'PROTOCOL_COMMIT = "75e5f052014d39601191e1a0f1263d52476d872e"',
        b'EXPECTED_BATCH_BYTES = 1_152_651_597',
        b'SESSION_DOWNLOAD_CAP_BYTES = 1_350_000_000',
        b'WORKSPACE_CAP_BYTES = 1_350_000_000',
        b'PER_FILE_CAP_BYTES = 650_000_000',
        b'midquote_response_calculated',
        b'strategy_pnl_calculated',
        b'q2_okx_accessed',
        b'validation_or_final_accessed',
    ]
    if not raw or not all(x in raw for x in required):
        raise RuntimeError("Frozen Q009B engine identity mismatch")

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
