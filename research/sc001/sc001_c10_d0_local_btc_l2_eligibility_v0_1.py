from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C10-D0-LOCAL-BTC-L2-ELIGIBILITY-V0.1"
PASS = "C10_D0_LOCAL_L2_ELIGIBILITY_PASS"
REVIEW = "C10_D0_LOCAL_L2_ELIGIBILITY_REVIEW"

PILOT_DATE = "2024-02-12"
EXPECTED_FILENAME = "BTC-USDT-SWAP-L2orderbook-400lv-2024-02-12.tar.gz"
EXPECTED_BYTES = 601_976_188

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c10-d0-local-btc-l2-eligibility-preflight-v0.1.md"
FREEZE = ROOT / "docs/research/sc001-c10-d0-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

Q009B = (
    DATA_ROOT / "SC001_DATA_Q009B_OKX_L2_BATCH_B"
    / "sc001_data_q009b_okx_l2_batch_b_report.json"
)
E008_INV = (
    DATA_ROOT / "SC001_E008_DATA_INVENTORY"
    / "sc001_e008_data_inventory_report.json"
)
L2_PATH = (
    DATA_ROOT / "SC001_DATA_Q009B_OKX_L2_BATCH_B"
    / PILOT_DATE / EXPECTED_FILENAME
)

OUT_DIR = DATA_ROOT / "SC001_C10_D0_LOCAL_L2_ELIGIBILITY"
OUT = OUT_DIR / "sc001_c10_d0_local_l2_eligibility_report_v0_1.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected: {path}")
    return x


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        text=True,
    ).strip()


def require_freeze() -> None:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_C10_D0_RUN":
        fail("C10-D0 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C10-D0 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C10-D0 protocol identity mismatch")
    if fr.get("pilot_date") != PILOT_DATE:
        fail("C10-D0 pilot date mismatch")
    if fr.get("expected_filename") != EXPECTED_FILENAME:
        fail("C10-D0 filename mismatch")
    if int(fr.get("expected_bytes", 0)) != EXPECTED_BYTES:
        fail("C10-D0 size mismatch")
    for k in (
        "l2_body_open_authorized",
        "l2_body_hash_authorized",
        "book_feature_authorized",
        "liquidity_vacuum_event_authorized",
        "future_move_authorized",
        "strategy_signal_authorized",
        "fill_model_authorized",
        "queue_model_authorized",
        "pnl_authorized",
        "c5_labels_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C10-D0 firewall mismatch: {k}")


def find_q009b_day(rep: dict) -> dict:
    for row in rep.get("days") or []:
        if isinstance(row, dict) and row.get("date") == PILOT_DATE:
            return row
    fail("Q009B pilot date row missing")


def find_e008_day(rep: dict) -> dict:
    for row in rep.get("days") or []:
        if isinstance(row, dict) and row.get("date") == PILOT_DATE:
            return row
    fail("E008 inventory pilot date row missing")


def main() -> int:
    try:
        require_freeze()

        q = load_json(Q009B)
        if q.get("stage") != "SC001-DATA-Q009B-OKX-L2-Q1-BATCH-B":
            fail("Q009B stage mismatch")
        if q.get("overall_status") != "PASS":
            fail("Q009B overall status not PASS")
        qrow = find_q009b_day(q)
        if qrow.get("status") != "FULL_DAY_PASS":
            fail("Q009B pilot day not FULL_DAY_PASS")
        qa = qrow.get("archive") or {}
        if qa.get("bytes") != EXPECTED_BYTES:
            fail("Q009B archive byte identity mismatch")
        qsha = qa.get("sha256")
        if not isinstance(qsha, str) or len(qsha) != 64:
            fail("Q009B archive SHA metadata missing")

        inv = load_json(E008_INV)
        if inv.get("status") != "E008_DATA_INVENTORY_PASS":
            fail("E008 inventory not exact PASS")
        irow = find_e008_day(inv)
        if irow.get("expected_l2_filename") != EXPECTED_FILENAME:
            fail("E008 inventory filename mismatch")
        if int(irow.get("expected_l2_bytes", -1)) != EXPECTED_BYTES:
            fail("E008 inventory expected byte mismatch")
        if irow.get("l2_archive_present_exact_size") is not True:
            fail("E008 inventory exact-size L2 not present")

        if not L2_PATH.exists() or not L2_PATH.is_file():
            fail(f"exact local L2 file missing: {L2_PATH}")
        if L2_PATH.name != EXPECTED_FILENAME:
            fail("local L2 basename mismatch")
        if L2_PATH.stat().st_size != EXPECTED_BYTES:
            fail(
                f"local L2 size mismatch: {L2_PATH.stat().st_size} != {EXPECTED_BYTES}"
            )

        report = {
            "stage": STAGE,
            "version": "0.1",
            "status": PASS,
            "pilot_date": PILOT_DATE,
            "pilot_selection_rule": "ordinary weekday in the already-qualified four-day Q1 BTC L2 set",
            "l2_path": str(L2_PATH),
            "filename": EXPECTED_FILENAME,
            "bytes": EXPECTED_BYTES,
            "parent_q009b_sha256_metadata": qsha,
            "q009b_parent_pass": True,
            "e008_inventory_parent_pass": True,
            "l2_body_opened": False,
            "l2_body_hashed_by_c10_d0": False,
            "book_feature_calculated": False,
            "liquidity_vacuum_event_calculated": False,
            "future_move_calculated": False,
            "strategy_signal_calculated": False,
            "fill_model_calculated": False,
            "queue_model_calculated": False,
            "pnl_calculated": False,
            "c5_labels_used": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, report)

        print(PASS)
        print("pilot_date =", PILOT_DATE)
        print("l2_filename =", EXPECTED_FILENAME)
        print("l2_bytes =", EXPECTED_BYTES)
        print("Q009B/E008 inventory parents = PASS / PASS")
        print("L2 body opened/hashed by C10-D0 = False / False")
        print("book feature/event/future move/signal/fill/queue/PnL = False")
        print("C5 labels used = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)
        return 0

    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "version": "0.1",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "l2_body_opened": False,
            "l2_body_hashed_by_c10_d0": False,
            "book_feature_calculated": False,
            "liquidity_vacuum_event_calculated": False,
            "future_move_calculated": False,
            "strategy_signal_calculated": False,
            "fill_model_calculated": False,
            "queue_model_calculated": False,
            "pnl_calculated": False,
            "c5_labels_used": False,
            "promotional_alpha_accessed": False,
        }
        try:
            atomic_json(OUT, fail_rep)
        except Exception:
            pass
        print(REVIEW)
        print("error =", fail_rep["error"])
        print("report =", OUT)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
