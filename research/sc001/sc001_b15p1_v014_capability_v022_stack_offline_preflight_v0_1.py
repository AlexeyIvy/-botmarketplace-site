from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/work/run/output")

SPEC = ROOT / "docs/research/sc001-b15-p1-v014-capability-v022-stack-offline-preflight-spec-v0.1.json"
FREEZE = ROOT / "docs/research/sc001-b15-p1-v014-capability-v022-stack-offline-preflight-freeze-v0.1.json"

PROBE = ROOT / "research/sc001/sc001_b15p1_nonprice_source_capability_revalidation_v0_2_2.py"
CAP_HARNESS = ROOT / "research/sc001/sc001_b15p1_nonprice_source_capability_selftest_harness_v0_2_2.py"
CAP_FREEZE = ROOT / "docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-freeze-v0.2.2.json"
CAP_SPEC = ROOT / "docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-spec-v0.2.2.json"
LIVE_WRAPPER = ROOT / "scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.3.sh"

CAP_COMPILE_MANIFEST = OUT / "capability_revalidation_compile_guard_manifest.json"
CAP_SELFTEST_MANIFEST = OUT / "capability_revalidation_self_test_manifest.json"
STACK_MANIFEST = OUT / "v014_capability_v022_stack_offline_preflight_manifest.json"

PASS = "B15P1_V014_CAPABILITY_V022_STACK_OFFLINE_PREFLIGHT_PASS"
REVIEW = "B15P1_V014_CAPABILITY_V022_STACK_OFFLINE_PREFLIGHT_REVIEW"
CAP_HARNESS_PASS = "B15P1_NONPRICE_SOURCE_CAPABILITY_V022_COMPILE_AND_SELFTEST_PASS"
CAP_SELFTEST_PASS = "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_V022_SELF_TEST_PASS"


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


def load_object(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def write_manifest(obj: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    STACK_MANIFEST.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_simple_assignments(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = re.fullmatch(r'([A-Z][A-Z0-9_]*)="([^"]*)"', line.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out


def parse_array_var_refs(text: str, name: str) -> list[str]:
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == f"{name}=(")
    except StopIteration as exc:
        raise GateError(f"array missing: {name}") from exc

    refs: list[str] = []
    for line in lines[start + 1 :]:
        s = line.strip()
        if s == ")":
            return refs
        if not s:
            continue
        m = re.fullmatch(r'"\$([A-Z][A-Z0-9_]*)"', s)
        if not m:
            fail(f"unexpected array item in {name}: {s}")
        refs.append(m.group(1))
    fail(f"array not terminated: {name}")


def resolve_wrapper_stage_pairs(text: str) -> list[tuple[str, str]]:
    assignments = parse_simple_assignments(text)
    file_vars = parse_array_var_refs(text, "STAGE_FILES")
    sha_vars = parse_array_var_refs(text, "EXPECTED_SHAS")
    if len(file_vars) != len(sha_vars):
        fail("wrapper stage/hash array length mismatch")

    pairs: list[tuple[str, str]] = []
    for fv, sv in zip(file_vars, sha_vars):
        if fv not in assignments:
            fail(f"wrapper unresolved stage file variable: {fv}")
        if sv not in assignments:
            fail(f"wrapper unresolved expected SHA variable: {sv}")
        rel = assignments[fv]
        expected = assignments[sv]
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            fail(f"wrapper invalid expected SHA for {sv}")
        pairs.append((rel, expected))
    return pairs


def extract_python_heredocs(text: str) -> list[str]:
    return re.findall(r"<<'PY'\n(.*?)\nPY(?:\n|$)", text, flags=re.DOTALL)


def require_stack_freeze() -> dict[str, Any]:
    fr = load_object(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_B15P1_V014_CAPABILITY_V022_STACK_OFFLINE_PREFLIGHT":
        fail("stack freeze status mismatch")
    expected = {
        "harness_sha256": sha256_file(Path(__file__).resolve()),
        "spec_sha256": sha256_file(SPEC),
        "capability_probe_sha256": sha256_file(PROBE),
        "capability_harness_sha256": sha256_file(CAP_HARNESS),
        "capability_freeze_sha256": sha256_file(CAP_FREEZE),
        "capability_spec_sha256": sha256_file(CAP_SPEC),
        "live_wrapper_sha256": sha256_file(LIVE_WRAPPER),
    }
    for key, actual in expected.items():
        if fr.get(key) != actual:
            fail(f"stack freeze hash mismatch {key}: expected={fr.get(key)} actual={actual}")

    for key in (
        "credentials_available",
        "exchange_calls_allowed",
        "systemd_mutation_allowed",
        "collector_start_allowed",
        "runtime_authorization_creation_allowed",
        "price_data_allowed",
        "pnl_data_allowed",
        "live_execution_allowed",
    ):
        if fr.get(key) is not False:
            fail(f"stack offline firewall mismatch: {key}")
    return fr


def run_capability_harness() -> dict[str, Any]:
    for p in (CAP_COMPILE_MANIFEST, CAP_SELFTEST_MANIFEST):
        p.unlink(missing_ok=True)

    proc = subprocess.run(
        [sys.executable, str(CAP_HARNESS)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)

    if proc.returncode != 0:
        fail(f"capability harness rc={proc.returncode}")
    if CAP_HARNESS_PASS not in proc.stdout:
        fail("capability harness PASS token missing")
    if not CAP_COMPILE_MANIFEST.is_file():
        fail("capability compile manifest missing")
    if not CAP_SELFTEST_MANIFEST.is_file():
        fail("capability self-test manifest missing")

    compile_obj = load_object(CAP_COMPILE_MANIFEST)
    selftest_obj = load_object(CAP_SELFTEST_MANIFEST)

    if compile_obj.get("status") != CAP_HARNESS_PASS:
        fail("capability compile manifest status mismatch")
    if selftest_obj.get("status") != CAP_SELFTEST_PASS:
        fail("capability self-test manifest status mismatch")

    for obj_name, obj in (
        ("compile", compile_obj),
        ("selftest", selftest_obj),
    ):
        for key in (
            "exchange_calls_performed",
            "collector_launch_authorized",
            "price_data_used",
        ):
            if obj.get(key) is not False:
                fail(f"capability {obj_name} firewall mismatch: {key}")

    if selftest_obj.get("credentials_required") is not False:
        fail("capability self-test unexpectedly requires credentials")
    if selftest_obj.get("output_snapshot_written") is not False:
        fail("capability self-test unexpectedly wrote snapshot")
    if selftest_obj.get("pnl_data_used") is not False:
        fail("capability self-test PnL firewall mismatch")

    checks = compile_obj.get("checks") or {}
    if checks.get("collector_v014_binding_present") is not True:
        fail("capability compile guard v0.1.4 binding missing")
    if checks.get("bybit_v014_parser_proof_present") is not True:
        fail("capability compile guard Bybit v0.1.4 parser proof missing")
    if checks.get("bybit_spot_pagination_guard_scoped") is not True:
        fail("capability Bybit pagination guard mismatch")

    return {
        "returncode": proc.returncode,
        "compile_manifest_sha256": sha256_file(CAP_COMPILE_MANIFEST),
        "selftest_manifest_sha256": sha256_file(CAP_SELFTEST_MANIFEST),
        "compile_checks": checks,
    }


def validate_live_wrapper() -> dict[str, Any]:
    text = LIVE_WRAPPER.read_text(encoding="utf-8")
    bash = shutil.which("bash")
    if not bash:
        fail("bash unavailable")

    syntax = subprocess.run(
        [bash, "-n", str(LIVE_WRAPPER)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    if syntax.returncode != 0:
        fail("live wrapper bash -n failed: " + (syntax.stderr or syntax.stdout).strip())

    pairs = resolve_wrapper_stage_pairs(text)
    if len(pairs) != 15:
        fail(f"live wrapper staged dependency count={len(pairs)} expected=15")

    resolved: dict[str, str] = {}
    for rel, expected in pairs:
        p = ROOT / rel
        if not p.is_file():
            fail(f"live wrapper staged dependency missing: {rel}")
        actual = sha256_file(p)
        if actual != expected:
            fail(
                f"live wrapper staged dependency SHA mismatch {rel}: "
                f"expected={expected} actual={actual}"
            )
        resolved[rel] = actual

    heredocs = extract_python_heredocs(text)
    if len(heredocs) != 2:
        fail(f"live wrapper embedded Python count={len(heredocs)} expected=2")
    for idx, block in enumerate(heredocs, start=1):
        compile(block, f"<capability-live-wrapper-heredoc-{idx}>", "exec")

    selftest_count = text.count("--mode self-test")
    run_count = text.count("--mode run")
    if selftest_count != 1:
        fail(f"live wrapper self-test mode count={selftest_count} expected=1")
    if run_count != 1:
        fail(f"live wrapper run mode count={run_count} expected=1")

    selftest_pos = text.find("--mode self-test")
    run_pos = text.find("--mode run")
    if selftest_pos < 0 or run_pos < 0 or selftest_pos >= run_pos:
        fail("live wrapper offline self-test does not precede live run")

    forbidden = {
        "curl": bool(re.search(r"(?m)^\s*curl\b", text)),
        "wget": bool(re.search(r"(?m)^\s*wget\b", text)),
        "nc": bool(re.search(r"(?m)^\s*nc\b", text)),
        "socat": bool(re.search(r"(?m)^\s*socat\b", text)),
        "systemctl": bool(re.search(r"(?m)^\s*systemctl\b", text)),
        "collector_service_start": bool(re.search(r"(?m)^\s*(?:service|systemctl).*\bstart\b", text)),
        "runtime_authorization_creation": "collector_launch_authorization.json" in text,
        "direct_price_url": bool(re.search(r"https?://[^\s\"']*(?:market/tickers|market/books|market/candles|market/orderbook)", text)),
    }
    bad = [k for k, v in forbidden.items() if v]
    if bad:
        fail("live wrapper forbidden behavior present: " + ",".join(bad))

    required = (
        '[[ "$env_mode" == "600" ]]',
        'B15P1_REPO_ROOT="$STAGE"',
        'B15P1_CAPABILITY_SNAPSHOT="$SNAPSHOT"',
        "collector_v014_offline_prerequisite = PASS",
        "staged_capability_v022_selftest = PASS",
        "sc001.b15.p1_nonprice_source_capability_snapshot.v0.2.2",
        '"library_sha256": expected_library',
        'bybit_adapter.get("collector_parser_version") == "0.1.4"',
        'bybit_adapter.get("parser_compatible") is True',
        'bybit_adapter.get("withdrawMax_minus_one_semantics") == "UNLIMITED"',
        'B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_V022_PASS',
        "collector_launch_authorized=False",
        "price_data_used=False",
        "pnl_data_used=False",
        "live_execution_authorized=False",
    )
    missing = [m for m in required if m not in text]
    if missing:
        fail("live wrapper required marker missing: " + repr(missing))

    if text.count("set +e") != 1:
        fail("live wrapper set +e count mismatch")
    if "trap " in text:
        fail("live wrapper unexpectedly installs shell traps")

    return {
        "bash_syntax_returncode": syntax.returncode,
        "staged_dependency_count": len(pairs),
        "staged_dependency_hashes": resolved,
        "embedded_python_block_count": len(heredocs),
        "embedded_python_compile": True,
        "selftest_mode_count": selftest_count,
        "run_mode_count": run_count,
        "selftest_precedes_live_run": True,
        "forbidden_behavior_hits": forbidden,
        "set_plus_e_count": text.count("set +e"),
    }


def main() -> int:
    checks: dict[str, Any] = {}
    try:
        require_stack_freeze()
        spec = load_object(SPEC)
        if spec.get("status") != "FROZEN_BEFORE_EXECUTION":
            fail("stack spec status mismatch")
        if spec.get("expected_pass_status") != PASS:
            fail("stack spec expected PASS token mismatch")

        checks["capability"] = run_capability_harness()
        checks["live_wrapper"] = validate_live_wrapper()

        manifest = {
            "schema": "sc001.b15.p1_v014_capability_v022_stack_offline_preflight.v0.1",
            "status": PASS,
            "harness_sha256": sha256_file(Path(__file__).resolve()),
            "spec_sha256": sha256_file(SPEC),
            "freeze_sha256": sha256_file(FREEZE),
            "capability_probe_sha256": sha256_file(PROBE),
            "capability_harness_sha256": sha256_file(CAP_HARNESS),
            "capability_freeze_sha256": sha256_file(CAP_FREEZE),
            "capability_spec_sha256": sha256_file(CAP_SPEC),
            "live_wrapper_sha256": sha256_file(LIVE_WRAPPER),
            "checks": checks,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "systemd_mutation_performed": False,
            "collector_start_performed": False,
            "runtime_authorization_created": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
            "next_state": "V014_CAPABILITY_V022_STACK_OFFLINE_PASS_PREPARE_LIVE_HOST_REVALIDATION",
        }
        write_manifest(manifest)
        print(PASS)
        print("capability_probe_sha256 =", manifest["capability_probe_sha256"])
        print("live_wrapper_sha256 =", manifest["live_wrapper_sha256"])
        print("staged_dependency_count =", checks["live_wrapper"]["staged_dependency_count"])
        print("embedded_python_block_count =", checks["live_wrapper"]["embedded_python_block_count"])
        print("exchange_calls_performed = False")
        print("collector_start_performed = False")
        return 0

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        write_manifest(
            {
                "schema": "sc001.b15.p1_v014_capability_v022_stack_offline_preflight.v0.1",
                "status": REVIEW,
                "error": error,
                "checks": checks,
                "credentials_available": False,
                "exchange_calls_performed": False,
                "systemd_mutation_performed": False,
                "collector_start_performed": False,
                "runtime_authorization_created": False,
                "price_data_used": False,
                "pnl_data_used": False,
                "live_execution_performed": False,
                "next_state": "STOP_AND_REVIEW_V014_CAPABILITY_V022_STACK",
            }
        )
        print(REVIEW)
        print("error =", error)
        print("exchange_calls_performed = False")
        print("collector_start_performed = False")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
