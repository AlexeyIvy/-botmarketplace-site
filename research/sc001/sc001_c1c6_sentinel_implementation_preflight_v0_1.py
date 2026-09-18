from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from sc001_selection_sentinel_common_v0_1 import (
    DATA_ROOT, ROOT, atomic_json, fail, git_blob, load_json, require_global_parents
)

PASS = "SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT_PASS"
FAIL = "SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT_FAIL"
FREEZE = ROOT / "docs/research/sc001-c1-c6-sentinel-implementation-freeze-v0.1.json"
RUN_MANIFEST = ROOT / "docs/research/sc001-c1-c6-sentinel-run-manifest-v0.1.json"
LEDGER = ROOT / "docs/research/sc001-selection-research-ledger-v0.1.json"
OUT_DIR = DATA_ROOT / "SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT"
OUT = OUT_DIR / "sc001_c1c6_sentinel_implementation_preflight_v0_1.json"

CANDIDATES = ("C1","C2","C3","C4","C5","C6")
TOKENS = {
    "C1": "C1_SENTINEL_PREFLIGHT_PASS",
    "C2": "C2_SENTINEL_PREFLIGHT_PASS",
    "C3": "C3_SENTINEL_PREFLIGHT_PASS",
    "C4": "C4_SENTINEL_PREFLIGHT_PASS",
    "C5": "C5_SENTINEL_PREFLIGHT_PASS",
    "C6": "C6_SENTINEL_PREFLIGHT_PASS",
}
REPORTS = {
    "C1": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C1" / "c1_sentinel_report_v0_1.json",
    "C2": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C2" / "c2_sentinel_report_v0_1.json",
    "C3": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C3" / "c3_sentinel_report_v0_1.json",
    "C4": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C4" / "c4_sentinel_report_v0_1.json",
    "C5": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C5" / "c5_sentinel_report_v0_1.json",
    "C6": DATA_ROOT / "SC001_C1C6_SENTINELS" / "C6" / "c6_sentinel_report_v0_1.json",
}


def check_identities() -> dict:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_FIRST_SENTINEL_OUTCOME":
        fail("freeze status mismatch")
    if int(fr.get("total_strategy_variants", 0)) != 11:
        fail("freeze total variant budget mismatch")

    expected = {
        "executable_protocol": ROOT / fr["executable_protocol_path"],
        "run_manifest": ROOT / fr["run_manifest_path"],
        "parent_plan": ROOT / fr["parent_plan_path"],
        "selection_ledger": ROOT / fr["selection_ledger_path"],
        "common_helper": ROOT / fr["common_helper_path"],
        "causal_utils": ROOT / fr["causal_utils_path"],
    }
    actual = {}
    for key, path in expected.items():
        sha = git_blob(path)
        actual[key] = sha
        if fr.get(f"{key}_git_blob_sha") != sha:
            fail(f"{key} identity mismatch {sha} != {fr.get(f'{key}_git_blob_sha')}")

    runners = fr.get("runners") or {}
    for c in CANDIDATES:
        row = runners.get(c)
        if not isinstance(row, dict):
            fail(f"freeze missing runner {c}")
        path = ROOT / row["path"]
        sha = git_blob(path)
        actual[f"runner_{c}"] = sha
        if row.get("git_blob_sha") != sha:
            fail(f"{c} runner identity mismatch")

    master_sha = git_blob(Path(__file__).resolve())
    actual["master_preflight"] = master_sha
    if fr.get("master_preflight_git_blob_sha") != master_sha:
        fail("master preflight identity mismatch")

    manifest = load_json(RUN_MANIFEST)
    if manifest.get("status") != "FROZEN_BEFORE_FIRST_SENTINEL_OUTCOME":
        fail("run manifest status mismatch")
    if int(manifest.get("total_strategy_variants", 0)) != 11:
        fail("run manifest variant budget mismatch")
    counts_by_candidate = {
        c: int((manifest.get("candidates") or {}).get(c, {}).get("count", 0))
        for c in CANDIDATES
    }
    if counts_by_candidate != {"C1": 1, "C2": 2, "C3": 2, "C4": 4, "C5": 1, "C6": 1}:
        fail(f"run manifest candidate counts mismatch: {counts_by_candidate}")
    if sum(counts_by_candidate.values()) != 11:
        fail("run manifest candidate counts do not sum to 11")

    ledger = load_json(LEDGER)
    if ledger.get("status") != "FROZEN_BEFORE_SENTINEL_OUTCOMES":
        fail("selection ledger status mismatch")
    if int(ledger.get("total_strategy_variants", 0)) != 11:
        fail("selection ledger total mismatch")
    ledger_counts = {
        str(row.get("candidate")): int(row.get("count", 0))
        for row in (ledger.get("candidate_variants") or [])
    }
    if ledger_counts != counts_by_candidate:
        fail(f"selection ledger/run-manifest count mismatch: {ledger_counts} != {counts_by_candidate}")

    return actual


def ensure_no_outcomes() -> None:
    terminal_prefixes = {
        "C1_","C2_","C3_","C4_","C5_","C6_"
    }
    for c, p in REPORTS.items():
        if not p.exists():
            continue
        old = load_json(p)
        status = str(old.get("status", ""))
        if any(status.startswith(prefix) for prefix in terminal_prefixes):
            fail(f"terminal sentinel report already exists before master preflight: {c} {status}")


def run_candidate_preflights() -> dict:
    fr = load_json(FREEZE)
    runners = fr["runners"]
    results = {}
    env = os.environ.copy()
    env["SC001_DATA_ROOT"] = str(DATA_ROOT)
    for c in CANDIDATES:
        path = ROOT / runners[c]["path"]
        print(f"=== {c} PREFLIGHT ===", flush=True)
        cp = subprocess.run(
            [sys.executable, str(path), "preflight"],
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
        )
        stdout = cp.stdout or ""
        stderr = cp.stderr or ""
        print(stdout, end="", flush=True)
        if stderr:
            print(stderr, end="", file=sys.stderr, flush=True)
        token = TOKENS[c]
        exact_lines = [x.strip() for x in stdout.splitlines()]
        if cp.returncode != 0 or token not in exact_lines:
            fail(f"{c} preflight failed rc={cp.returncode} token_found={token in exact_lines}")
        results[c] = {
            "returncode": cp.returncode,
            "token": token,
            "token_found_exact_line": True,
        }
    return results


def main() -> int:
    try:
        parents = require_global_parents()
        identities = check_identities()
        ensure_no_outcomes()
        candidate_results = run_candidate_preflights()
        rep = {
            "stage": "SC001-C1C6-SENTINEL-IMPLEMENTATION-PREFLIGHT-V0.1",
            "status": PASS,
            "identities": identities,
            "candidate_preflights": candidate_results,
            "golden_status": parents["golden"].get("status"),
            "total_strategy_variants": 11,
            "sentinel_outcome_calculated": False,
            "strategy_pnl_calculated": False,
            "protected_data_accessed": False,
            "promotional_alpha_accessed": False,
        }
        atomic_json(OUT, rep)
        print(PASS)
        print("candidate_preflights = 6 / 6")
        print("total_strategy_variants = 11")
        print("sentinel outcome calculated = False")
        print("protected data accessed = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)
        return 0
    except Exception as exc:
        rep = {
            "stage": "SC001-C1C6-SENTINEL-IMPLEMENTATION-PREFLIGHT-V0.1",
            "status": FAIL,
            "error": f"{type(exc).__name__}: {exc}",
            "sentinel_outcome_calculated": False,
            "strategy_pnl_calculated": False,
            "protected_data_accessed": False,
            "promotional_alpha_accessed": False,
        }
        try:
            atomic_json(OUT, rep)
        except Exception:
            pass
        print(FAIL)
        print("error =", rep["error"])
        print("report =", OUT)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
