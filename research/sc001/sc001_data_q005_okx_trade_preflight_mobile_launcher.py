"""Pinned Android/Pydroid launcher for SC001-DATA-Q005 OKX trade preflight v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "fdac05c8b190c731b8374765001475d5e533ab8d"
ENGINE_PATH = "research/sc001/sc001_data_q005_okx_trade_preflight.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q005_okx_trade_preflight_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-Q005 OKX TICK-TRADE PREFLIGHT v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: OKX BTC-USDT-SWAP, five frozen 2024-Q1 dates")
    print("Metadata/HEAD only; archive bodies: NO")
    print("Signal/features: NO | P&L: NO | Validation/Final: NO")
    print("Network/workspace cap: 20 MB | reserve: 4 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-Q005-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("Q005 engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-DATA-Q005-OKX-TRADE-PREFLIGHT"',
        b'MODULE_CANDIDATES = ("1", "2", "3", "4", "5")',
        b'PROBE_DATE = "2024-01-05"',
        b'NETWORK_CAP_BYTES = 20_000_000',
        b'WORKSPACE_CAP_BYTES = 20_000_000',
        b'archive_bodies_downloaded',
        b'strategy_features_calculated',
        b'strategy_pnl_calculated',
        b'validation_or_final_accessed',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen Q005 engine")

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
