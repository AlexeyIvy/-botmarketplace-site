from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/work/run/output")

FREEZE = ROOT / "docs/research/sc001-b15-p1-adapter-combined-offline-validation-freeze-v0.1.1.json"
SPEC = ROOT / "docs/research/sc001-b15-p1-adapter-combined-offline-validation-spec-v0.1.1.json"

COLLECTOR_HARNESS = ROOT / "research/sc001/sc001_b15p1_nonprice_collector_selftest_harness_v0_1_3.py"
COLLECTOR_RUNNER = ROOT / "research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_3.py"
COLLECTOR_LIBRARY = ROOT / "research/sc001/sc001_b15p1_nonprice_transferability_lib_v0_1_3.py"
COLLECTOR_FREEZE = ROOT / "docs/research/sc001-b15-p1-nonprice-collector-implementation-freeze-v0.1.3.json"
COLLECTOR_CONTRACT = ROOT / "docs/research/sc001-b15-p1-nonprice-collector-implementation-contract-v0.1.3.json"

CAP_HARNESS = ROOT / "research/sc001/sc001_b15p1_nonprice_source_capability_selftest_harness_v0_2_1.py"
CAP_PROBE = ROOT / "research/sc001/sc001_b15p1_nonprice_source_capability_revalidation_v0_2_1.py"
CAP_FREEZE = ROOT / "docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-freeze-v0.2.1.json"

ADAPTER_AUDIT = ROOT / "docs/research/sc001-b15-p1-okx-adapter-compatibility-audit-v0.1.md"
SOURCE_SEMANTICS = ROOT / "docs/research/sc001-b15-p1-stage-c-source-semantics-evidence-v0.4.json"
ATTEMPT_DIAGNOSTIC = ROOT / "docs/research/sc001-b15-p1-adapter-combined-offline-validation-attempt-v0.1-diagnostic.json"
CAP_CORRECTION = ROOT / "docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-correction-v0.2.1.json"

COLLECTOR_SELFTEST_MANIFEST = OUT / "implementation_self_test_manifest.json"
COLLECTOR_COMPILE_MANIFEST = OUT / "implementation_compile_guard_manifest.json"
CAP_SELFTEST_MANIFEST = OUT / "capability_revalidation_self_test_manifest.json"
CAP_COMPILE_MANIFEST = OUT / "capability_revalidation_compile_guard_manifest.json"
COMBINED_MANIFEST = OUT / "adapter_combined_offline_validation_manifest.json"

COLLECTOR_TOKEN = "B15P1_NONPRICE_COLLECTOR_V013_SELF_TEST_PASS"
COLLECTOR_HARNESS_TOKEN = "B15P1_NONPRICE_COLLECTOR_V013_COMPILE_AND_SELFTEST_PASS"
CAP_TOKEN = "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_V021_SELF_TEST_PASS"
CAP_HARNESS_TOKEN = "B15P1_NONPRICE_SOURCE_CAPABILITY_V021_COMPILE_AND_SELFTEST_PASS"
PASS = "B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_PASS"
REVIEW = "B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_REVIEW"


class GateError(RuntimeError):
    pass


def fail(msg: str) -> None:
    raise GateError(msg)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require_object(path: Path) -> dict[str, Any]:
    obj = load_json(path)
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sanitized_env() -> dict[str, str]:
    env = dict(os.environ)
    forbidden_prefixes = (
        "SC001_B15_",
        "B15P1_CAPABILITY_",
        "B15P1_LAUNCH_",
    )
    for key in list(env):
        if key.startswith(forbidden_prefixes):
            env.pop(key, None)
    env["B15P1_REPO_ROOT"] = str(ROOT)
    return env


def require_freeze() -> dict[str, Any]:
    fr = require_object(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_V011":
        fail("combined freeze status mismatch")

    expected = {
        "combined_harness_sha256": sha256_file(Path(__file__).resolve()),
        "combined_spec_sha256": sha256_file(SPEC),
        "collector_runner_sha256": sha256_file(COLLECTOR_RUNNER),
        "collector_library_sha256": sha256_file(COLLECTOR_LIBRARY),
        "collector_harness_sha256": sha256_file(COLLECTOR_HARNESS),
        "collector_freeze_sha256": sha256_file(COLLECTOR_FREEZE),
        "collector_contract_sha256": sha256_file(COLLECTOR_CONTRACT),
        "capability_probe_sha256": sha256_file(CAP_PROBE),
        "capability_harness_sha256": sha256_file(CAP_HARNESS),
        "capability_freeze_sha256": sha256_file(CAP_FREEZE),
        "adapter_audit_sha256": sha256_file(ADAPTER_AUDIT),
        "source_semantics_v0_4_sha256": sha256_file(SOURCE_SEMANTICS),
        "attempt_diagnostic_sha256": sha256_file(ATTEMPT_DIAGNOSTIC),
        "capability_correction_sha256": sha256_file(CAP_CORRECTION),
    }
    for key, value in expected.items():
        if fr.get(key) != value:
            fail(
                f"combined freeze hash mismatch {key}: "
                f"expected={fr.get(key)} actual={value}"
            )

    for key in (
        "exchange_calls_authorized",
        "credentials_authorized",
        "collector_launch_authorized",
        "price_data_authorized",
        "pnl_data_authorized",
        "live_execution_authorized",
    ):
        if fr.get(key) is not False:
            fail(f"offline firewall mismatch: {key}")
    return fr


def run_child(path: Path, label: str, timeout: int = 180) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        env=sanitized_env(),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    print(f"===== {label} STDOUT =====")
    if proc.stdout:
        print(proc.stdout, end="")
    print(f"===== {label} STDERR =====", file=sys.stderr)
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc


def verify_collector() -> dict[str, Any]:
    proc = run_child(COLLECTOR_HARNESS, "COLLECTOR_V013")
    if proc.returncode != 0:
        fail(f"collector harness rc={proc.returncode}")
    if COLLECTOR_TOKEN not in proc.stdout:
        fail("collector runner PASS token missing")
    if COLLECTOR_HARNESS_TOKEN not in proc.stdout:
        fail("collector harness PASS token missing")

    selftest = require_object(COLLECTOR_SELFTEST_MANIFEST)
    compile_manifest = require_object(COLLECTOR_COMPILE_MANIFEST)
    contract = require_object(COLLECTOR_CONTRACT)

    if selftest.get("status") != COLLECTOR_TOKEN:
        fail("collector self-test manifest status mismatch")
    if compile_manifest.get("status") != COLLECTOR_HARNESS_TOKEN:
        fail("collector compile manifest status mismatch")

    required = list(contract.get("mandatory_offline_self_tests") or [])
    observed = list(selftest.get("mandatory_tests") or [])
    if len(required) != 28:
        fail(f"collector mandatory test contract count={len(required)} expected=28")
    if observed != required:
        fail("collector self-test mandatory list differs from contract")

    results = selftest.get("test_results") or {}
    missing_or_false = [name for name in required if results.get(name) is not True]
    if missing_or_false:
        fail("collector mandatory tests not PASS: " + ",".join(missing_or_false))

    extra = selftest.get("extra_tests") or {}
    if not extra or not all(value is True for value in extra.values()):
        fail("collector extra self-tests not all PASS")

    for key in (
        "exchange_calls_performed",
        "collector_launch_authorized",
        "price_data_authorized",
        "pnl_data_authorized",
    ):
        if selftest.get(key) is not False:
            fail(f"collector self-test firewall mismatch: {key}")

    return {
        "returncode": proc.returncode,
        "runner_token": COLLECTOR_TOKEN,
        "harness_token": COLLECTOR_HARNESS_TOKEN,
        "mandatory_test_count": len(required),
        "extra_test_count": len(extra),
        "selftest_manifest_sha256": sha256_file(COLLECTOR_SELFTEST_MANIFEST),
        "compile_manifest_sha256": sha256_file(COLLECTOR_COMPILE_MANIFEST),
    }


def verify_capability() -> dict[str, Any]:
    proc = run_child(CAP_HARNESS, "CAPABILITY_V021")
    if proc.returncode != 0:
        fail(f"capability harness rc={proc.returncode}")
    if CAP_TOKEN not in proc.stdout:
        fail("capability probe PASS token missing")
    if CAP_HARNESS_TOKEN not in proc.stdout:
        fail("capability harness PASS token missing")

    selftest = require_object(CAP_SELFTEST_MANIFEST)
    compile_manifest = require_object(CAP_COMPILE_MANIFEST)

    if selftest.get("status") != CAP_TOKEN:
        fail("capability self-test manifest status mismatch")
    if compile_manifest.get("status") != CAP_HARNESS_TOKEN:
        fail("capability compile manifest status mismatch")

    for key in (
        "exchange_calls_performed",
        "credentials_required",
        "output_snapshot_written",
        "price_data_used",
        "pnl_data_used",
        "collector_launch_authorized",
    ):
        if selftest.get(key) is not False:
            fail(f"capability self-test firewall mismatch: {key}")

    return {
        "returncode": proc.returncode,
        "probe_token": CAP_TOKEN,
        "harness_token": CAP_HARNESS_TOKEN,
        "selftest_manifest_sha256": sha256_file(CAP_SELFTEST_MANIFEST),
        "compile_manifest_sha256": sha256_file(CAP_COMPILE_MANIFEST),
    }


def main() -> int:
    try:
        fr = require_freeze()

        for path in (
            COLLECTOR_SELFTEST_MANIFEST,
            COLLECTOR_COMPILE_MANIFEST,
            CAP_SELFTEST_MANIFEST,
            CAP_COMPILE_MANIFEST,
            OUT / "source_capability_snapshot.json",
        ):
            if path.exists():
                path.unlink()

        collector = verify_collector()
        capability = verify_capability()

        forbidden_output = OUT / "source_capability_snapshot.json"
        if forbidden_output.exists():
            fail("offline gate unexpectedly wrote live capability snapshot")

        manifest = {
            "schema": "sc001.b15.p1_adapter_combined_offline_validation.v0.1.1",
            "status": PASS,
            "freeze_sha256": sha256_file(FREEZE),
            "collector": collector,
            "capability": capability,
            "api_adapter_hardening": {
                "okx_feeCcy_optional": True,
                "okx_missing_burningFeeRate_fail_closed": True,
                "okx_maxWd_optional": True,
                "okx_feeGroup_primary": True,
                "okx_deprecated_fee_fallback": True,
                "okx_fee_group_ambiguity_fail_closed": True,
                "bybit_spot_pagination_disabled": True,
            },
            "exchange_calls_performed": False,
            "credentials_used": False,
            "capability_snapshot_written": False,
            "collector_launch_authorized": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_authorized": False,
            "next_state": "PREPARE_B15P1_SOURCE_CAPABILITY_LIVE_RETRY_V021",
        }
        write_json(COMBINED_MANIFEST, manifest)
        print(PASS)
        print("collector_mandatory_tests =", collector["mandatory_test_count"])
        print("collector_extra_tests =", collector["extra_test_count"])
        print("exchange_calls_performed = False")
        print("credentials_used = False")
        print("collector_launch_authorized = False")
        print("price_data_used = False")
        return 0

    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        write_json(
            COMBINED_MANIFEST,
            {
                "schema": "sc001.b15.p1_adapter_combined_offline_validation.v0.1.1",
                "status": REVIEW,
                "error": err,
                "exchange_calls_performed": False,
                "credentials_used": False,
                "capability_snapshot_written": False,
                "collector_launch_authorized": False,
                "price_data_used": False,
                "pnl_data_used": False,
                "live_execution_authorized": False,
                "next_state": "STOP_AND_REVIEW_B15P1_ADAPTER_OFFLINE_VALIDATION",
            },
        )
        print(REVIEW)
        print("error =", err)
        print("exchange_calls_performed = False")
        print("collector_launch_authorized = False")
        print("price_data_used = False")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
