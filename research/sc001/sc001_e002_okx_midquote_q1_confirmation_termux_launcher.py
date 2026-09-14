"""Pinned Termux launcher for SC001-E002 OKX Q1 midquote confirmation v0.1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
ENGINE_COMMIT = "38d3ab050ff64555b0149c31c52e1ab1775ae579"
ENGINE_PATH = "research/sc001/sc001_e002_okx_midquote_q1_confirmation.py"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT + "/" + ENGINE_PATH
)
LOCAL_ENGINE = DOWNLOAD / "sc001_e002_okx_midquote_q1_confirmation_v0_1.py"
MAX_ENGINE_BYTES = 2_000_000


def main() -> None:
    print("=" * 78)
    print("SC001-E002 OKX Q1 MIDQUOTE CONFIRMATION TERMUX LAUNCHER v0.1")
    print("Engine commit:", ENGINE_COMMIT)
    print("Scope: four frozen non-pilot 2024-Q1 OKX days")
    print("Market-data download: NO")
    print("TFI 5s -> L2 midquote 5s @ 100/250/500ms")
    print("Per-day computational checkpoints: YES")
    print("Do not inspect partial checkpoint alpha before final COMPLETE verdict")
    print("Q2 / formal Validation / Final: NO")
    print("=" * 78)

    req = Request(
        ENGINE_URL,
        headers={"User-Agent": "BotMarketplace-SC001-E002-Q1-confirmation-Termux/0.1"},
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(MAX_ENGINE_BYTES + 1)
    if len(raw) > MAX_ENGINE_BYTES:
        raise RuntimeError("confirmation engine exceeds launcher safety cap")

    required = [
        b'STAGE = "SC001-E002-OKX-MIDQUOTE-Q1-CONFIRMATION"',
        b'PROTOCOL_COMMIT = "c6f9f01f7aed9a84786c6bb791ab88707dd1a5d7"',
        b'PILOT_ENGINE_COMMIT = "94c77febc73601c76976da4ab71bedecc69a485a"',
        b'LATENCIES_MS = (100, 250, 500)',
        b'2024-01-14',
        b'2024-01-31',
        b'2024-02-12',
        b'2024-02-13',
        b'MIDQUOTE_CONFIRMATION_PASS',
        b'_checkpoints_do_not_inspect_until_complete',
        b'q2_okx_accessed',
        b'validation_or_final_accessed',
    ]
    if not raw or not all(token in raw for token in required):
        raise RuntimeError("downloaded file is not the frozen confirmation engine")

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
