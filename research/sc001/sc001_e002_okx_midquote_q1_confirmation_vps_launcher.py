"""VPS launcher for the frozen SC001-E002 OKX Q1 midquote confirmation.

Infrastructure-only adapter. It executes the exact frozen confirmation engine from
commit 38d3ab050ff64555b0149c31c52e1ab1775ae579 and changes only filesystem
locations from the Android Download root to a VPS data root.

No dates, statistical rules, latencies, gates, feature logic, response logic,
or final-verdict semantics are changed.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

ENGINE_COMMIT = "38d3ab050ff64555b0149c31c52e1ab1775ae579"
ENGINE_PATH = "research/sc001/sc001_e002_okx_midquote_q1_confirmation.py"
EXPECTED_PROTOCOL_COMMIT = "c6f9f01f7aed9a84786c6bb791ab88707dd1a5d7"

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()
WORKSPACE_NAME = "SC001_E002_OKX_MIDQUOTE_Q1_CONFIRMATION"


def fail(msg: str) -> None:
    raise SystemExit(f"VPS_LAUNCHER_FAIL: {msg}")


def frozen_engine_bytes() -> bytes:
    try:
        cp = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show", f"{ENGINE_COMMIT}:{ENGINE_PATH}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        fail(f"cannot read frozen engine from git: {detail}")
    raw = cp.stdout
    required = (
        b'STAGE = "SC001-E002-OKX-MIDQUOTE-Q1-CONFIRMATION"',
        b'PROTOCOL_COMMIT = "c6f9f01f7aed9a84786c6bb791ab88707dd1a5d7"',
        b"def process_day",
        b"def final_summary",
        b"MIDQUOTE_CONFIRMATION_PASS",
        b"q2_okx_accessed",
        b"validation_or_final_accessed",
    )
    if not raw or not all(token in raw for token in required):
        fail("frozen engine identity tokens mismatch")
    return raw


def path_map(ns: dict) -> None:
    ns["DOWNLOAD"] = DATA_ROOT
    workspace = DATA_ROOT / WORKSPACE_NAME
    ns["WORKSPACE"] = workspace
    ns["CHECKPOINT_DIR"] = workspace / "_checkpoints_do_not_inspect_until_complete"
    ns["PROGRESS"] = workspace / "sc001_e002_okx_midquote_q1_confirmation_progress.json"
    ns["REPORT"] = workspace / "sc001_e002_okx_midquote_q1_confirmation_report.json"
    ns["METRICS"] = workspace / "sc001_e002_okx_midquote_q1_confirmation_daily_metrics.csv"
    ns["SUMMARY"] = workspace / "sc001_e002_okx_midquote_q1_confirmation_summary.md"
    ns["SAFETY"] = workspace / "sc001_e002_okx_midquote_q1_confirmation_final_safety.json"
    ns["Q006R_REPORT"] = (
        DATA_ROOT
        / "SC001_DATA_Q006R_OKX_UTC_STITCH"
        / "sc001_data_q006r_okx_utc_stitch_report.json"
    )
    ns["Q009A_REPORT"] = (
        DATA_ROOT
        / "SC001_DATA_Q009A_OKX_L2_BATCH_A"
        / "sc001_data_q009a_okx_l2_batch_a_report.json"
    )
    ns["Q009B_REPORT"] = (
        DATA_ROOT
        / "SC001_DATA_Q009B_OKX_L2_BATCH_B"
        / "sc001_data_q009b_okx_l2_batch_b_report.json"
    )


def preflight(ns: dict) -> None:
    if ns.get("PROTOCOL_COMMIT") != EXPECTED_PROTOCOL_COMMIT:
        fail("protocol commit mismatch inside frozen engine")
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(DATA_ROOT).free
    if free < 4_000_000_000:
        fail(f"less than frozen 4 GB free-space reserve: {free}")
    if ns["REPORT"].exists():
        fail(
            "final confirmation report already exists in VPS workspace; "
            "refusing to overwrite an observed terminal result"
        )
    for label, path in (
        ("Q006R report", ns["Q006R_REPORT"]),
        ("Q009A report", ns["Q009A_REPORT"]),
        ("Q009B report", ns["Q009B_REPORT"]),
    ):
        if not path.exists():
            fail(f"missing {label}: {path}")


def main() -> None:
    raw = frozen_engine_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    ns = {
        "__name__": "sc001_e002_okx_midquote_q1_confirmation_frozen_vps",
        "__file__": f"<git:{ENGINE_COMMIT}:{ENGINE_PATH}>",
        "__package__": None,
    }
    exec(compile(raw, ns["__file__"], "exec"), ns, ns)
    path_map(ns)
    preflight(ns)

    print("=" * 78)
    print("SC001 E002 OKX Q1 MIDQUOTE CONFIRMATION — VPS ADAPTER")
    print("Frozen engine commit:", ENGINE_COMMIT)
    print("Frozen engine SHA256:", digest)
    print("Data root:", DATA_ROOT)
    print("Compute mode: exact frozen engine, sequential four-day execution")
    print("Phone checkpoints/results are not imported or inspected.")
    print("No Q2 / Validation / Final access. No strategy P&L.")
    print("=" * 78)

    ns["main"]()


if __name__ == "__main__":
    main()
