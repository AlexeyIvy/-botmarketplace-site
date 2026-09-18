from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()

PROTOCOL = ROOT / "docs/research/sc001-c1-c6-sentinel-batch-execution-protocol-v0.1.md"
SENTINEL_FREEZE = ROOT / "docs/research/sc001-c1-c6-sentinel-implementation-freeze-v0.1.json"
BATCH_FREEZE = ROOT / "docs/research/sc001-c1-c6-sentinel-batch-implementation-freeze-v0.1.json"
MASTER_REPORT = DATA_ROOT / "SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT" / "sc001_c1c6_sentinel_implementation_preflight_v0_1.json"

OUT_DIR = DATA_ROOT / "SC001_C1C6_SENTINEL_BATCH"
PREFLIGHT_REPORT = OUT_DIR / "sc001_c1c6_sentinel_batch_preflight_v0_1.json"
REPORT = OUT_DIR / "sc001_c1c6_sentinel_batch_report_v0_1.json"

PREFLIGHT_PASS = "SC001_C1C6_SENTINEL_BATCH_PREFLIGHT_PASS"
COMPLETE = "SC001_C1C6_SENTINEL_BATCH_COMPLETE"
EXEC_FAIL = "SC001_C1C6_SENTINEL_BATCH_EXECUTION_FAIL"

ORDER = ("C1","C2","C3","C4","C5","C6")

RECOGNIZED = {
    "C1": {"C1_SENTINEL_SURVIVE","C1_DEFER_SAMPLE_INSUFFICIENT","C1_REJECT_SENTINEL"},
    "C2": {"C2_SENTINEL_SURVIVE","C2_REJECT_SENTINEL"},
    "C3": {"C3_SENTINEL_SURVIVE","C3_REJECT_SENTINEL"},
    "C4": {"C4_SENTINEL_SURVIVE","C4_REJECT_SENTINEL"},
    "C5": {"C5_SENTINEL_SURVIVE","C5_DEFER_SAMPLE_INSUFFICIENT","C5_REJECT_SENTINEL"},
    "C6": {"C6_SENTINEL_SURVIVE","C6_REJECT_SENTINEL"},
}

REPORT_PATHS = {
    "C1": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C1" / "c1_sentinel_report_v0_1.json",
    "C2": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C2" / "c2_sentinel_report_v0_1.json",
    "C3": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C3" / "c3_sentinel_report_v0_1.json",
    "C4": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C4" / "c4_sentinel_report_v0_1.json",
    "C5": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C5" / "c5_sentinel_report_v0_1.json",
    "C6": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C6" / "c6_sentinel_report_v0_1.json",
}


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


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


def master_ok() -> dict:
    rep = load_json(MASTER_REPORT)
    if rep.get("status") != "SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT_PASS":
        fail("master implementation preflight not exact PASS")
    if int(rep.get("total_strategy_variants", 0)) != 11:
        fail("master variant budget mismatch")
    cps = rep.get("candidate_preflights") or {}
    if set(cps) != set(ORDER):
        fail("master candidate preflight set mismatch")
    for c in ORDER:
        row = cps.get(c)
        if not isinstance(row, dict):
            fail(f"master preflight row missing: {c}")
        if int(row.get("returncode", -1)) != 0 or row.get("token_found_exact_line") is not True:
            fail(f"master candidate preflight not clean: {c}")
    for k in (
        "sentinel_outcome_calculated",
        "strategy_pnl_calculated",
        "protected_data_accessed",
        "promotional_alpha_accessed",
    ):
        if rep.get(k) is not False:
            fail(f"master firewall mismatch: {k}")
    return rep


def frozen_identities() -> dict:
    batch = load_json(BATCH_FREEZE)
    if batch.get("status") != "FROZEN_BEFORE_FIRST_SENTINEL_OUTCOME":
        fail("batch freeze status mismatch")
    if int(batch.get("total_strategy_variants", 0)) != 11:
        fail("batch freeze variant budget mismatch")

    sentinel = load_json(SENTINEL_FREEZE)
    if sentinel.get("status") != "FROZEN_BEFORE_FIRST_SENTINEL_OUTCOME":
        fail("sentinel freeze status mismatch")

    actual = {
        "batch_protocol_git_blob_sha": git_blob(PROTOCOL),
        "sentinel_freeze_git_blob_sha": git_blob(SENTINEL_FREEZE),
        "batch_runner_git_blob_sha": git_blob(Path(__file__).resolve()),
    }
    for key, value in actual.items():
        if batch.get(key) != value:
            fail(f"{key} mismatch {value} != {batch.get(key)}")

    if batch.get("sentinel_freeze_expected_blob_sha") != actual["sentinel_freeze_git_blob_sha"]:
        fail("sentinel freeze expected blob mismatch")

    runners = sentinel.get("runners") or {}
    if set(runners) != set(ORDER):
        fail("sentinel freeze runner set mismatch")
    for c in ORDER:
        row = runners[c]
        p = ROOT / row["path"]
        actual_sha = git_blob(p)
        if actual_sha != row.get("git_blob_sha"):
            fail(f"{c} frozen runner identity mismatch")
    return actual


def ensure_one_shot_clean() -> None:
    if REPORT.exists():
        old = load_json(REPORT)
        if old.get("status") in {COMPLETE, EXEC_FAIL}:
            fail(f"terminal batch report already exists: {old.get('status')}")
    for c, p in REPORT_PATHS.items():
        if not p.exists():
            continue
        old = load_json(p)
        status = str(old.get("status", ""))
        if status in RECOGNIZED[c]:
            fail(f"terminal candidate report already exists before batch: {c} {status}")


def preflight() -> dict:
    master = master_ok()
    ids = frozen_identities()
    ensure_one_shot_clean()
    rep = {
        "stage": "SC001-C1C6-SENTINEL-BATCH-PREFLIGHT-V0.1",
        "status": PREFLIGHT_PASS,
        "execution_order": list(ORDER),
        "master_status": master.get("status"),
        "total_strategy_variants": 11,
        "identities": ids,
        "candidate_terminal_report_exists": False,
        "sentinel_outcome_calculated": False,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
    }
    atomic_json(PREFLIGHT_REPORT, rep)
    return rep


def runner_map() -> dict[str, Path]:
    fr = load_json(SENTINEL_FREEZE)
    return {c: ROOT / fr["runners"][c]["path"] for c in ORDER}


def terminal_status(candidate: str) -> str | None:
    p = REPORT_PATHS[candidate]
    if not p.exists():
        return None
    rep = load_json(p)
    status = rep.get("status")
    return status if isinstance(status, str) else None


def run_batch() -> dict:
    preflight()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    runners = runner_map()
    env = os.environ.copy()
    env["SC001_DATA_ROOT"] = str(DATA_ROOT)

    execution = {}
    any_execution_error = False

    for i, c in enumerate(ORDER, start=1):
        stdout_path = OUT_DIR / f"{c.lower()}_stdout.log"
        stderr_path = OUT_DIR / f"{c.lower()}_stderr.log"

        print(f"BATCH [{i}/6] {c} START", flush=True)

        cp = subprocess.run(
            [sys.executable, str(runners[c]), "run"],
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
        )

        stdout_path.write_text(cp.stdout or "", encoding="utf-8")
        stderr_path.write_text(cp.stderr or "", encoding="utf-8")

        status = None
        error = None
        try:
            status = terminal_status(c)
        except Exception as exc:
            error = f"report_read_error: {type(exc).__name__}: {exc}"

        recognized = status in RECOGNIZED[c]
        if cp.returncode != 0 or not recognized or error is not None:
            any_execution_error = True

        execution[c] = {
            "runner_returncode": cp.returncode,
            "terminal_status": status,
            "recognized_terminal_status": recognized,
            "stdout_log": str(stdout_path),
            "stderr_log": str(stderr_path),
            "report_path": str(REPORT_PATHS[c]),
            "error": error,
        }

        # Deliberately withhold candidate outcome from console until all six attempts finish.
        print(f"BATCH [{i}/6] {c} DONE (outcome withheld)", flush=True)

    status = EXEC_FAIL if any_execution_error else COMPLETE

    rep = {
        "stage": "SC001-C1C6-SENTINEL-BATCH-V0.1",
        "status": status,
        "execution_order": list(ORDER),
        "execution": execution,
        "all_six_attempted": len(execution) == 6,
        "all_six_recognized_terminal_reports": all(x["recognized_terminal_status"] for x in execution.values()),
        "total_strategy_variants": 11,
        "selection_calibration_only": True,
        "between_result_adaptation_performed": False,
        "protected_data_accessed": False,
        "promotional_alpha_accessed": False,
        "live_trading_authorized": False,
    }
    atomic_json(REPORT, rep)

    print(status)
    print("all_six_attempted =", rep["all_six_attempted"])
    print("all_six_recognized_terminal_reports =", rep["all_six_recognized_terminal_reports"])
    print("total_strategy_variants = 11")
    print("between_result_adaptation_performed = False")
    print("protected_data_accessed = False")
    print("promotional_alpha_accessed = False")
    print("=== TERMINAL CANDIDATE STATUSES ===")
    for c in ORDER:
        print(c, "=", execution[c]["terminal_status"], "rc =", execution[c]["runner_returncode"])
    print("report =", REPORT)
    return rep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preflight", "run"])
    args = ap.parse_args()

    try:
        if args.mode == "preflight":
            rep = preflight()
            print(PREFLIGHT_PASS)
            print("execution_order =", ",".join(rep["execution_order"]))
            print("total_strategy_variants = 11")
            print("sentinel outcome calculated = False")
            print("protected data accessed = False")
            print("promotional alpha accessed = False")
            print("report =", PREFLIGHT_REPORT)
            return 0

        rep = run_batch()
        return 0 if rep["status"] == COMPLETE else 2

    except Exception as exc:
        target = REPORT if args.mode == "run" else PREFLIGHT_REPORT
        rep = {
            "stage": "SC001-C1C6-SENTINEL-BATCH-V0.1",
            "status": EXEC_FAIL,
            "error": f"{type(exc).__name__}: {exc}",
            "selection_calibration_only": True,
            "protected_data_accessed": False,
            "promotional_alpha_accessed": False,
        }
        try:
            atomic_json(target, rep)
        except Exception:
            pass
        print(EXEC_FAIL)
        print("error =", rep["error"])
        print("report =", target)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
