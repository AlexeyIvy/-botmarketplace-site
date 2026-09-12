"""Pinned Android/Pydroid launcher for SC001-DATA-Q007 v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "47b156d28ab6bbf8aef98ea14b21833860b4566e"
ENGINE_PATH = "research/sc001/sc001_data_q007_okx_l2_q1_preflight.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_data_q007_okx_l2_q1_preflight_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-DATA-Q007 OKX Q1 L2 PREFLIGHT v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: five frozen 2024-Q1 OKX BTC-USDT-SWAP L2 dates")
    print("Metadata/HEAD only | archive bodies: NO")
    print("TFI/midquote/P&L: NO | Q2/Validation/Final: NO")
    print("Network/workspace cap: 20 MB | reserve: 4 GB")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-Q007-launcher/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("Q007 engine exceeds launcher safety limit")

    required = [
        b'STAGE = "SC001-DATA-Q007-OKX-L2-Q1-PREFLIGHT"',
        b'PROTOCOL_COMMIT = "448c29985811044b2717bdb592a5eb4810461bc5"',
        b'TRADE_MODULE = "4"',
        b'NETWORK_CAP_BYTES = 20_000_000',
        b'WORKSPACE_CAP_BYTES = 20_000_000',
        b'archive_bodies_downloaded',
        b'midquote_response_calculated',
        b'q2_okx_accessed',
        b'validation_or_final_accessed',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("Downloaded file is not the frozen Q007 engine")

    LOCAL_ENGINE.write_bytes(raw)
    print("Frozen engine:", LOCAL_ENGINE)
    print("SHA256:", hashlib.sha256(raw).hexdigest())
    print()

    code = compile(raw, str(LOCAL_ENGINE), "exec")
    ns = {"__name__": "__main__", "__file__": str(LOCAL_ENGINE), "__package__": None}
    exec(code, ns, ns)


if __name__ == "__main__":
    main()
