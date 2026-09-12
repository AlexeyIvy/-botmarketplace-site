"""Pinned Android/Pydroid launcher for SC001-DATA-Q005R v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "7d84bd92665b56fb3dde149244c0cb8d10b4d874"
ENGINE_PATH = "research/sc001/sc001_data_q005r_okx_trade_preflight.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q005r_okx_trade_preflight_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-Q005R OKX TICK-TRADE PREFLIGHT REPAIR v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: exact-date metadata/HEAD only, module 1, five frozen 2024-Q1 dates")
    print("Archive bodies: NO | features/P&L: NO | Validation/Final: NO")
    print("Network/workspace cap: 20 MB | reserve: 4 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-Q005R-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("Q005R engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-DATA-Q005R-OKX-TRADE-PREFLIGHT"',
        b'TRADE_MODULE = "1"',
        b'NETWORK_CAP_BYTES = 20_000_000',
        b'WORKSPACE_CAP_BYTES = 20_000_000',
        b'exact_candidate',
        b'archive_bodies_downloaded',
        b'strategy_features_calculated',
        b'strategy_pnl_calculated',
        b'validation_or_final_accessed',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen Q005R engine")

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
