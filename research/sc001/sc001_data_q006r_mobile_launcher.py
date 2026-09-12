"""Pinned Android/Pydroid launcher for SC001-DATA-Q006R v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "f1e7bf4071b63ad466f490d09d990afc3e01fc34"
ENGINE_PATH = "research/sc001/sc001_data_q006r_okx_utc_stitch.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q006r_okx_utc_stitch_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-Q006R OKX UTC-STITCH REPAIR v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: five frozen 2024-Q1 UTC target days")
    print("Source rule: existing D archive + downloaded D+1 neighbor, filter to UTC day")
    print("Schema mapping includes created_time + instrument_name")
    print("TFI/returns/P&L: NO | Q2 OKX: NO | Validation/Final: NO")
    print("Session/workspace cap: 100 MB | per-file: 25 MB | reserve: 4 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-Q006R-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("Q006R engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-DATA-Q006R-OKX-UTC-STITCH"',
        b'PROTOCOL_COMMIT = "12f6541067c08d94cede1ba17a714636265c0935"',
        b'TRADE_MODULE = "1"',
        b'EXPECTED_HEADER = [',
        b'"created_time"',
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
        raise RuntimeError("Downloaded file is not the frozen Q006R engine")

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
