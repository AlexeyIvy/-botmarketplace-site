from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/work/run/output")
MANIFEST = OUT / "final_launch_v011_wrapper_offline_preflight_manifest.json"

WRAPPER = ROOT / "scripts/research/run-b15p1-final-collector-deployment-launch-v0.1.1.sh"
SPEC = ROOT / "docs/research/sc001-b15-p1-final-launch-v0.1.1-wrapper-offline-preflight-spec-v0.1.1.json"
FREEZE = ROOT / "docs/research/sc001-b15-p1-final-launch-v0.1.1-wrapper-offline-preflight-freeze-v0.1.1.json"
CORRECTION = ROOT / "docs/research/sc001-b15-p1-final-launch-v0.1.1-technical-correction-v0.1.json"
DIAGNOSTIC = ROOT / "docs/research/sc001-b15-p1-final-launch-attempt-v0.1-technical-failure-diagnostic.json"
RECOVERY_HOST = ROOT / "docs/research/sc001-b15-p1-final-launch-v0.1-failure-recovery-host-result-v0.1.json"

PASS = "B15P1_FINAL_LAUNCH_V011_WRAPPER_OFFLINE_PREFLIGHT_PASS"
REVIEW = "B15P1_FINAL_LAUNCH_V011_WRAPPER_OFFLINE_PREFLIGHT_REVIEW"


class PreflightError(RuntimeError):
    pass


def fail(msg: str) -> None:
    raise PreflightError(msg)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def write_manifest(obj: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def require_freeze() -> dict[str, Any]:
    fr = load_object(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_B15P1_FINAL_LAUNCH_V011_WRAPPER_OFFLINE_PREFLIGHT":
        fail("v0.1.1 preflight freeze status mismatch")
    expected = {
        "harness_sha256": sha256_file(Path(__file__).resolve()),
        "wrapper_sha256": sha256_file(WRAPPER),
        "spec_sha256": sha256_file(SPEC),
        "correction_sha256": sha256_file(CORRECTION),
        "failure_diagnostic_sha256": sha256_file(DIAGNOSTIC),
        "recovery_host_result_sha256": sha256_file(RECOVERY_HOST),
    }
    for key, actual in expected.items():
        if fr.get(key) != actual:
            fail(f"freeze hash mismatch {key}: expected={fr.get(key)} actual={actual}")
    for key in (
        "credentials_available",
        "exchange_calls_allowed",
        "systemd_mutation_allowed",
        "runtime_authorization_creation_allowed",
        "collector_start_allowed",
        "price_data_allowed",
        "pnl_data_allowed",
        "live_execution_allowed",
    ):
        if fr.get(key) is not False:
            fail(f"offline firewall mismatch: {key}")
    return fr


def extract_python_heredocs(text: str) -> list[str]:
    return re.findall(r"<<'PY'\n(.*?)\nPY(?:\n|$)", text, flags=re.DOTALL)


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
        raise PreflightError(f"array missing: {name}") from exc
    refs: list[str] = []
    for line in lines[start + 1 :]:
        s = line.strip()
        if s == ")":
            return refs
        if not s:
            continue
        m = re.fullmatch(r'"\$([A-Z][A-Z0-9_]*)"', s)
        if not m:
            fail(f"unexpected array element in {name}: {s}")
        refs.append(m.group(1))
    fail(f"array not terminated: {name}")


def resolve_dependency_pairs(text: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    assignments = parse_simple_assignments(text)
    source_vars = parse_array_var_refs(text, "SOURCE_FILES")
    source_sha_vars = parse_array_var_refs(text, "SOURCE_SHAS")
    deploy_vars = parse_array_var_refs(text, "DEPLOY_FILES")
    deploy_sha_vars = parse_array_var_refs(text, "DEPLOY_SHAS")
    if len(source_vars) != len(source_sha_vars):
        fail("source dependency array length mismatch")
    if len(deploy_vars) != len(deploy_sha_vars):
        fail("deploy dependency array length mismatch")
    source = []
    deploy = []
    for file_var, sha_var in zip(source_vars, source_sha_vars):
        if file_var not in assignments or sha_var not in assignments:
            fail(f"unresolved source vars: {file_var}/{sha_var}")
        source.append((assignments[file_var], assignments[sha_var]))
    for file_var, sha_var in zip(deploy_vars, deploy_sha_vars):
        if file_var not in assignments or sha_var not in assignments:
            fail(f"unresolved deploy vars: {file_var}/{sha_var}")
        deploy.append((assignments[file_var], assignments[sha_var]))
    return source, deploy


def run_verifier_fixture(
    verifier: str,
    *,
    state: dict[str, Any],
    manifest: dict[str, Any],
    out_dir: Path,
    auth_path: Path,
    snapshot_path: Path,
    expected_hashes: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    state_path = out_dir / "fixture_state.json"
    manifest_path = out_dir / "fixture_manifest.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    args = [
        sys.executable,
        "-c",
        verifier,
        str(state_path),
        str(manifest_path),
        str(auth_path),
        str(snapshot_path),
        str(out_dir),
        expected_hashes["auth"],
        expected_hashes["snapshot"],
        expected_hashes["runner"],
        expected_hashes["library"],
        expected_hashes["freeze"],
        expected_hashes["protocol"],
        expected_hashes["design"],
        expected_hashes["design_preflight"],
        expected_hashes["route"],
    ]
    return subprocess.run(args, text=True, capture_output=True, check=False, timeout=10)


def tri_state_fixtures(verifier: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        auth = root / "auth.json"
        snapshot = root / "snapshot.json"
        auth.write_bytes(b'{"fixture":"auth"}\n')
        snapshot.write_bytes(b'{"fixture":"snapshot"}\n')

        hashes = {
            "auth": sha256_file(auth),
            "snapshot": sha256_file(snapshot),
            "runner": "1" * 64,
            "library": "2" * 64,
            "freeze": "3" * 64,
            "protocol": "4" * 64,
            "design": "5" * 64,
            "design_preflight": "6" * 64,
            "route": "7" * 64,
        }

        manifest = {
            "stage": "SC001-B15P1-NONPRICE-TRANSFERABILITY-COLLECTOR-V0.1.3",
            "version": "0.1.3",
            "runner_sha256": hashes["runner"],
            "library_sha256": hashes["library"],
            "implementation_freeze_sha256": hashes["freeze"],
            "protocol_sha256": hashes["protocol"],
            "design_candidate_sha256": hashes["design"],
            "design_preflight_manifest_sha256": hashes["design_preflight"],
            "route_graph_sha256": hashes["route"],
            "capability_snapshot_sha256": hashes["snapshot"],
            "capability_status": "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS",
            "fast_cadence_seconds": 15,
            "request_deadline_seconds": 12,
            "fee_refresh_seconds": 21600,
            "fee_stale_after_seconds": 28800,
            "price_data_authorized": False,
            "pnl_authorized": False,
        }

        now_ms = int(time.time() * 1000)
        base_state = {
            "stage": "SC001-B15P1-NONPRICE-TRANSFERABILITY-COLLECTOR-V0.1.3",
            "version": "0.1.3",
            "status": "B15P1_NONPRICE_COLLECTION_RUNNING",
            "process_epoch": 1,
            "process_restart_count": 0,
            "poll_count": 0,
            "invalid_poll_count": 0,
            "last_heartbeat_ms": now_ms,
            "last_scheduled_slot_ms": None,
            "last_poll_chain_hash": "0" * 64,
            "price_data_collected": False,
            "pnl_calculated": False,
        }

        not_ready_zero = run_verifier_fixture(
            verifier,
            state=base_state,
            manifest=manifest,
            out_dir=root,
            auth_path=auth,
            snapshot_path=snapshot,
            expected_hashes=hashes,
        )
        if not_ready_zero.returncode != 10 or "NOT_READY = poll_count:0" not in not_ready_zero.stdout:
            fail(
                "tri-state poll_count=0 fixture failed: "
                f"rc={not_ready_zero.returncode} stdout={not_ready_zero.stdout!r} stderr={not_ready_zero.stderr!r}"
            )

        no_valid_state = copy.deepcopy(base_state)
        no_valid_state.update(
            {
                "poll_count": 2,
                "invalid_poll_count": 2,
                "last_scheduled_slot_ms": 30000,
                "last_poll_chain_hash": "b" * 64,
            }
        )
        not_ready_valid = run_verifier_fixture(
            verifier,
            state=no_valid_state,
            manifest=manifest,
            out_dir=root,
            auth_path=auth,
            snapshot_path=snapshot,
            expected_hashes=hashes,
        )
        if not_ready_valid.returncode != 10 or "NOT_READY = valid_poll_count:0" not in not_ready_valid.stdout:
            fail("tri-state no-valid-poll fixture failed")

        by_raw = b'{"fixture":"bybit"}'
        ok_raw = b'{"fixture":"okx"}'
        by_sha = sha256_bytes(by_raw)
        ok_sha = sha256_bytes(ok_raw)
        by_path = root / "raw_objects" / "bybit" / by_sha[:2] / f"{by_sha}.bin"
        ok_path = root / "raw_objects" / "okx" / ok_sha[:2] / f"{ok_sha}.bin"
        by_path.parent.mkdir(parents=True, exist_ok=True)
        ok_path.parent.mkdir(parents=True, exist_ok=True)
        by_path.write_bytes(by_raw)
        ok_path.write_bytes(ok_raw)

        poll_dir = root / "polls"
        poll_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        for slot, chain in ((15000, "a" * 64), (30000, "b" * 64)):
            rows.append(
                {
                    "scheduled_slot_ms": slot,
                    "poll_chain_hash": chain,
                    "price_data_collected": False,
                    "venues": {
                        "BYBIT": {"status": "OK", "raw_body_sha256": by_sha},
                        "OKX": {"status": "OK", "raw_body_sha256": ok_sha},
                    },
                }
            )
        (poll_dir / "fixture.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )

        pass_state = copy.deepcopy(base_state)
        pass_state.update(
            {
                "poll_count": 2,
                "invalid_poll_count": 0,
                "last_scheduled_slot_ms": 30000,
                "last_poll_chain_hash": "b" * 64,
                "last_heartbeat_ms": int(time.time() * 1000),
            }
        )
        passed = run_verifier_fixture(
            verifier,
            state=pass_state,
            manifest=manifest,
            out_dir=root,
            auth_path=auth,
            snapshot_path=snapshot,
            expected_hashes=hashes,
        )
        if passed.returncode != 0 or "READY =" not in passed.stdout:
            fail(
                "tri-state PASS fixture failed: "
                f"rc={passed.returncode} stdout={passed.stdout!r} stderr={passed.stderr!r}"
            )

        bad_price = copy.deepcopy(pass_state)
        bad_price["price_data_collected"] = True
        hard_price = run_verifier_fixture(
            verifier,
            state=bad_price,
            manifest=manifest,
            out_dir=root,
            auth_path=auth,
            snapshot_path=snapshot,
            expected_hashes=hashes,
        )
        if hard_price.returncode != 20 or "HARD_FAIL = state_price_firewall_mismatch" not in hard_price.stdout:
            fail("tri-state price-firewall HARD_FAIL fixture failed")

        bad_restart = copy.deepcopy(pass_state)
        bad_restart["process_restart_count"] = 1
        hard_restart = run_verifier_fixture(
            verifier,
            state=bad_restart,
            manifest=manifest,
            out_dir=root,
            auth_path=auth,
            snapshot_path=snapshot,
            expected_hashes=hashes,
        )
        if hard_restart.returncode != 20 or "HARD_FAIL = process_restart_count_nonzero" not in hard_restart.stdout:
            fail("tri-state restart HARD_FAIL fixture failed")

        by_path.write_bytes(b"corrupt")
        hard_raw = run_verifier_fixture(
            verifier,
            state=pass_state,
            manifest=manifest,
            out_dir=root,
            auth_path=auth,
            snapshot_path=snapshot,
            expected_hashes=hashes,
        )
        if hard_raw.returncode != 20 or "HARD_FAIL = BYBIT_raw_object_sha_mismatch" not in hard_raw.stdout:
            fail("tri-state raw-object integrity HARD_FAIL fixture failed")

        return {
            "poll_count_zero_rc": not_ready_zero.returncode,
            "no_valid_poll_rc": not_ready_valid.returncode,
            "pass_rc": passed.returncode,
            "price_firewall_rc": hard_price.returncode,
            "restart_rc": hard_restart.returncode,
            "raw_integrity_rc": hard_raw.returncode,
        }


def main() -> int:
    checks: dict[str, Any] = {}
    try:
        require_freeze()
        spec = load_object(SPEC)
        correction = load_object(CORRECTION)
        diagnostic = load_object(DIAGNOSTIC)
        recovery_host = load_object(RECOVERY_HOST)
        text = WRAPPER.read_text(encoding="utf-8")

        if spec.get("status") != "FROZEN_BEFORE_OFFLINE_PREFLIGHT":
            fail("spec status mismatch")
        if spec.get("expected_pass_status") != PASS:
            fail("spec expected pass mismatch")
        if (spec.get("wrapper") or {}).get("sha256") != sha256_file(WRAPPER):
            fail("wrapper SHA mismatch")
        if (spec.get("technical_correction") or {}).get("sha256") != sha256_file(CORRECTION):
            fail("correction SHA mismatch")
        if correction.get("status") != "TECHNICAL_RETRY_CANDIDATE_READY_FOR_OFFLINE_PREFLIGHT":
            fail("correction status mismatch")
        if correction.get("retry_authorized") is not False:
            fail("correction prematurely authorizes retry")
        if diagnostic.get("status") != "TECHNICAL_WRAPPER_CONTROL_FLOW_FAILURE":
            fail("diagnostic status mismatch")
        if (diagnostic.get("exact_failure") or {}).get("failure_class") != "EXPECTED_NOT_READY_STATE_TRIGGERED_GLOBAL_ERR_TRAP":
            fail("diagnostic failure class mismatch")
        if recovery_host.get("status") != "B15P1_FINAL_LAUNCH_V01_FAILURE_RECOVERY_PASS":
            fail("recovery host status mismatch")
        if recovery_host.get("recovery_report_sha256") != spec.get("recovery_report_sha256"):
            fail("recovery report SHA chain mismatch")
        checks["prerequisite_chain"] = True

        source_pairs, deploy_pairs = resolve_dependency_pairs(text)
        if len(source_pairs) != int(spec.get("source_file_count", -1)):
            fail(f"source dependency count mismatch: {len(source_pairs)}")
        if len(deploy_pairs) != int(spec.get("runtime_deploy_file_count", -1)):
            fail(f"deploy dependency count mismatch: {len(deploy_pairs)}")
        if not set(deploy_pairs).issubset(set(source_pairs)):
            fail("deploy dependencies are not a subset of source dependencies")
        source_hashes: dict[str, str] = {}
        for rel, expected in source_pairs:
            p = ROOT / rel
            if not p.is_file():
                fail(f"source dependency missing: {rel}")
            actual = sha256_file(p)
            if actual != expected:
                fail(f"source dependency SHA mismatch: {rel}")
            source_hashes[rel] = actual
        checks["source_dependency_count"] = len(source_pairs)
        checks["runtime_deploy_dependency_count"] = len(deploy_pairs)
        checks["source_dependency_hashes"] = source_hashes

        bash = shutil.which("bash")
        if not bash:
            fail("bash unavailable")
        syntax = subprocess.run(
            [bash, "-n", str(WRAPPER)],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        checks["bash_syntax_returncode"] = syntax.returncode
        if syntax.returncode != 0:
            fail("bash -n failed: " + (syntax.stderr or syntax.stdout).strip())

        heredocs = extract_python_heredocs(text)
        expected_heredocs = int(spec.get("embedded_python_block_count", -1))
        if len(heredocs) != expected_heredocs:
            fail(f"embedded Python count mismatch: {len(heredocs)}")
        for idx, block in enumerate(heredocs, start=1):
            compile(block, f"<v011-heredoc-{idx}>", "exec")
        checks["embedded_python_block_count"] = len(heredocs)
        checks["embedded_python_compile"] = True

        plus_positions = [m.start() for m in re.finditer(r"(?m)^\s*set \+e\s*$", text)]
        if len(plus_positions) != 1:
            fail(f"set +e count mismatch: {len(plus_positions)}")
        rollback_start = text.find("rollback() {")
        fail_start = text.find("\nfail() {", rollback_start)
        if not (rollback_start >= 0 and fail_start > rollback_start and rollback_start < plus_positions[0] < fail_start):
            fail("set +e is not confined to rollback")
        checks["set_plus_e_count"] = 1
        checks["set_plus_e_only_in_rollback"] = True

        required_markers = (
            'flock -n 9 || fail "another_final_launch_or_recovery_in_progress"',
            "trap 'on_signal HUP 129' HUP",
            "trap 'on_signal INT 130' INT",
            "trap 'on_signal TERM 143' TERM",
            "trap 'on_exit $?' EXIT",
            'if selftest_stdout="$(',
            'if verify_output="$(',
            "NOT_READY_EXIT = 10",
            "HARD_FAIL_EXIT = 20",
            "runtime_file_ledger.tsv",
            ".b15p1.v011.tmp.$$",
            'assert sha(p) == item.get("sha256")',
            'poll_dir = out_dir / "polls"',
            'raw_path = out_dir / "raw_objects"',
            "process_epoch_not_one",
            "process_restart_count_nonzero",
            "final_nrestarts_nonzero",
            'trap - ERR HUP INT TERM EXIT',
            'echo "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_V011_PASS"',
        )
        missing = [m for m in required_markers if m not in text]
        if missing:
            fail("required v0.1.1 marker missing")
        checks["required_marker_count"] = len(required_markers)

        if "max ~90 seconds" in text or "collector_initial_poll_verification_timeout" in text:
            fail("legacy timing-sensitive verifier remains")
        if 'echo "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_PASS"' in text:
            fail("legacy v0.1 pass token remains")
        if text.count('systemctl enable "$SERVICE_NAME"') != 1:
            fail("systemctl enable count mismatch")
        if text.count('systemctl start "$SERVICE_NAME"') != 1:
            fail("systemctl start count mismatch")
        if text.count("--mode self-test") != 1 or "--mode run" in text:
            fail("collector mode invocation mismatch")

        systemctl_commands: list[str] = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#") or s.startswith("for cmd in "):
                continue
            systemctl_commands.extend(re.findall(r"\bsystemctl\s+([A-Za-z-]+)", line))
        allowed = set(spec.get("allowed_systemctl_subcommands") or [])
        disallowed = [c for c in systemctl_commands if c not in allowed]
        if disallowed:
            fail("disallowed systemctl commands: " + ",".join(disallowed))
        if set(systemctl_commands) != allowed:
            fail(f"systemctl command set mismatch: {sorted(set(systemctl_commands))}")
        checks["systemctl_subcommands"] = systemctl_commands

        forbidden = {
            "restart": bool(re.search(r"systemctl\s+restart", text)),
            "mask_unmask": bool(re.search(r"systemctl\s+(?:mask|unmask)", text)),
            "legacy_unit": "ops/systemd/sc001-b15p1-transferability.service" in text,
            "curl": bool(re.search(r"(?m)^\s*curl\b", text)),
            "wget": bool(re.search(r"(?m)^\s*wget\b", text)),
            "nc": bool(re.search(r"(?m)^\s*nc\b", text)),
            "socat": bool(re.search(r"(?m)^\s*socat\b", text)),
            "direct_url": bool(re.search(r"https?://", text)),
            "delete_state": 'rm -f "$STATE_FILE"' in text,
            "delete_manifest": 'rm -f "$MANIFEST_FILE"' in text,
            "delete_systemd_log": 'rm -f "$SYSTEMD_LOG"' in text,
        }
        if any(forbidden.values()):
            fail("forbidden behavior present: " + ",".join(k for k, v in forbidden.items() if v))
        checks["forbidden_behavior_hits"] = forbidden

        rollback_markers = (
            'systemctl stop "$SERVICE_NAME"',
            'systemctl disable "$SERVICE_NAME"',
            "while IFS=$'\\t' read -r rel existed expected",
            'cp -a "$backup" "$dst"',
            'if [[ "$current_sha" == "$expected" ]]',
            'ROLLBACK_INCOMPLETE=1',
            'rm -f "$AUTH_FILE"',
            'rm -f "$RUNTIME_UNIT"',
        )
        if any(m not in text for m in rollback_markers):
            fail("rollback ledger marker missing")
        checks["rollback_marker_count"] = len(rollback_markers)

        # Confirm the exact Bash construct that fixes the v0.1 ERR-trap bug.
        err_fixture = r'''
set -eEuo pipefail
trap 'exit 99' ERR
if output="$(bash -c 'exit 10')"; then
  rc=0
else
  rc="$?"
fi
[[ "$rc" -eq 10 ]]
echo ERR_TRAP_IF_FIXTURE_PASS
'''
        err_run = subprocess.run(
            [bash, "-c", err_fixture],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        if err_run.returncode != 0 or "ERR_TRAP_IF_FIXTURE_PASS" not in err_run.stdout:
            fail(
                "Bash ERR-trap conditional fixture failed: "
                f"rc={err_run.returncode} out={err_run.stdout!r} err={err_run.stderr!r}"
            )
        checks["bash_err_trap_if_condition_fixture"] = True

        verifier_blocks = [b for b in heredocs if "NOT_READY_EXIT = 10" in b and "HARD_FAIL_EXIT = 20" in b]
        if len(verifier_blocks) != 1:
            fail(f"tri-state verifier block count={len(verifier_blocks)}")
        checks["tri_state_fixtures"] = tri_state_fixtures(verifier_blocks[0])

        manifest = {
            "schema": "sc001.b15.p1_final_launch_v011_wrapper_offline_preflight.v0.1.1",
            "status": PASS,
            "wrapper_sha256": sha256_file(WRAPPER),
            "spec_sha256": sha256_file(SPEC),
            "freeze_sha256": sha256_file(FREEZE),
            "correction_sha256": sha256_file(CORRECTION),
            "failure_diagnostic_sha256": sha256_file(DIAGNOSTIC),
            "recovery_host_result_sha256": sha256_file(RECOVERY_HOST),
            "checks": checks,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "systemd_mutation_performed": False,
            "runtime_authorization_created": False,
            "collector_start_performed": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
            "next_state": "PREPARE_SEALED_FINAL_LAUNCH_V011_TECHNICAL_RETRY",
        }
        write_manifest(manifest)
        print(PASS)
        print("wrapper_sha256 =", manifest["wrapper_sha256"])
        print("source_dependency_count =", checks["source_dependency_count"])
        print("runtime_deploy_dependency_count =", checks["runtime_deploy_dependency_count"])
        print("embedded_python_block_count =", checks["embedded_python_block_count"])
        print("bash_err_trap_if_condition_fixture = PASS")
        print("tri_state_fixtures =", json.dumps(checks["tri_state_fixtures"], sort_keys=True))
        print("collector_start_performed = False")
        return 0

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        write_manifest(
            {
                "schema": "sc001.b15.p1_final_launch_v011_wrapper_offline_preflight.v0.1.1",
                "status": REVIEW,
                "error": error,
                "checks": checks,
                "credentials_available": False,
                "exchange_calls_performed": False,
                "systemd_mutation_performed": False,
                "runtime_authorization_created": False,
                "collector_start_performed": False,
                "price_data_used": False,
                "pnl_data_used": False,
                "live_execution_performed": False,
                "next_state": "STOP_AND_REVIEW_FINAL_LAUNCH_V011_WRAPPER",
            }
        )
        print(REVIEW)
        print("error =", error)
        print("collector_start_performed = False")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
