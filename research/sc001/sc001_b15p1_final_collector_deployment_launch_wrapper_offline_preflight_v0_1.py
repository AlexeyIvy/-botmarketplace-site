from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/work/run/output")
MANIFEST = OUT / "final_collector_deployment_launch_wrapper_offline_preflight_manifest.json"

WRAPPER = ROOT / "scripts/research/run-b15p1-final-collector-deployment-launch-v0.1.sh"
SPEC = ROOT / "docs/research/sc001-b15-p1-final-collector-deployment-launch-wrapper-preflight-spec-v0.1.json"
FREEZE = ROOT / "docs/research/sc001-b15-p1-final-collector-deployment-launch-wrapper-preflight-freeze-v0.1.json"
PRELAUNCH_RESULT = ROOT / "docs/research/sc001-b15-p1-collector-prelaunch-readiness-result-v0.1.json"
POST_REBOOT_RESULT = ROOT / "docs/research/sc001-b15-p1-collector-host-deployment-readiness-post-reboot-result-v0.1.json"
CANDIDATE = ROOT / "docs/research/sc001-b15-p1-collector-launch-authorization-candidate-v0.1.json"

PASS = "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_WRAPPER_OFFLINE_PREFLIGHT_PASS"
REVIEW = "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_WRAPPER_OFFLINE_PREFLIGHT_REVIEW"


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
    if fr.get("status") != "FROZEN_BEFORE_B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_WRAPPER_OFFLINE_PREFLIGHT":
        fail("final launch wrapper preflight freeze status mismatch")
    expected = {
        "harness_sha256": sha256_file(Path(__file__).resolve()),
        "wrapper_sha256": sha256_file(WRAPPER),
        "spec_sha256": sha256_file(SPEC),
        "prelaunch_result_sha256": sha256_file(PRELAUNCH_RESULT),
        "post_reboot_result_sha256": sha256_file(POST_REBOOT_RESULT),
        "launch_candidate_sha256": sha256_file(CANDIDATE),
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
    m = re.search(rf"(?ms)^{re.escape(name)}=\(\n(.*?)^\)", text)
    if not m:
        fail(f"array missing: {name}")
    refs: list[str] = []
    for raw in m.group(1).splitlines():
        line = raw.strip()
        if not line:
            continue
        q = re.fullmatch(r'"\$([A-Z][A-Z0-9_]*)"', line)
        if not q:
            fail(f"unexpected array element {name}: {line}")
        refs.append(q.group(1))
    return refs


def resolve_dependency_pairs(wrapper_text: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    assignments = parse_simple_assignments(wrapper_text)
    source_vars = parse_array_var_refs(wrapper_text, "SOURCE_FILES")
    source_sha_vars = parse_array_var_refs(wrapper_text, "SOURCE_SHAS")
    deploy_vars = parse_array_var_refs(wrapper_text, "DEPLOY_FILES")
    deploy_sha_vars = parse_array_var_refs(wrapper_text, "DEPLOY_SHAS")
    if len(source_vars) != len(source_sha_vars):
        fail("source dependency array length mismatch")
    if len(deploy_vars) != len(deploy_sha_vars):
        fail("deploy dependency array length mismatch")
    source: list[tuple[str, str]] = []
    deploy: list[tuple[str, str]] = []
    for file_var, sha_var in zip(source_vars, source_sha_vars):
        if file_var not in assignments or sha_var not in assignments:
            fail(f"unresolved source dependency vars: {file_var}/{sha_var}")
        source.append((assignments[file_var], assignments[sha_var]))
    for file_var, sha_var in zip(deploy_vars, deploy_sha_vars):
        if file_var not in assignments or sha_var not in assignments:
            fail(f"unresolved deploy dependency vars: {file_var}/{sha_var}")
        deploy.append((assignments[file_var], assignments[sha_var]))
    return source, deploy


def require_order(text: str, markers: list[tuple[str, str]]) -> dict[str, int]:
    positions: dict[str, int] = {}
    start = 0
    for label, marker in markers:
        pos = text.find(marker, start)
        if pos < 0:
            fail(f"required order marker missing: {label}")
        positions[label] = pos
        start = pos + len(marker)
    return positions


def main() -> int:
    checks: dict[str, Any] = {}
    try:
        require_freeze()
        spec = load_object(SPEC)
        wrapper_text = WRAPPER.read_text(encoding="utf-8")
        if spec.get("status") != "FROZEN_BEFORE_OFFLINE_PREFLIGHT":
            fail("preflight spec status mismatch")
        if spec.get("expected_pass_status") != PASS:
            fail("preflight expected pass status mismatch")
        if (spec.get("wrapper") or {}).get("sha256") != sha256_file(WRAPPER):
            fail("wrapper SHA mismatch against spec")

        pre_req = ((spec.get("prerequisites") or {}).get("prelaunch_result") or {})
        pre = load_object(PRELAUNCH_RESULT)
        if pre.get("status") != pre_req.get("required_status"):
            fail("prelaunch prerequisite status mismatch")
        if sha256_file(PRELAUNCH_RESULT) != pre_req.get("sha256"):
            fail("prelaunch prerequisite SHA mismatch")
        if (pre.get("safety") or {}).get("collector_start_performed") is not False:
            fail("prelaunch prerequisite collector-start mismatch")
        if (pre.get("safety") or {}).get("runtime_authorization_created") is not False:
            fail("prelaunch prerequisite authorization mismatch")
        checks["prelaunch_result_pass"] = True

        post_req = ((spec.get("prerequisites") or {}).get("post_reboot_host_result") or {})
        post = load_object(POST_REBOOT_RESULT)
        if post.get("status") != post_req.get("required_status"):
            fail("post-reboot prerequisite status mismatch")
        if sha256_file(POST_REBOOT_RESULT) != post_req.get("sha256"):
            fail("post-reboot prerequisite SHA mismatch")
        if post.get("host_report_sha256") != post_req.get("host_report_sha256"):
            fail("post-reboot host-report SHA mismatch")
        if post.get("reboot_hold_cleared") is not True:
            fail("reboot hold not cleared")
        host = post.get("host_state") or {}
        if host.get("stable_service_active") != "inactive":
            fail("post-reboot stable service not inactive")
        if host.get("stable_service_enabled") != "not-found":
            fail("post-reboot stable service enabled state mismatch")
        if host.get("runtime_unit_sha256_or_absent") != "ABSENT":
            fail("post-reboot runtime unit should be absent")
        if host.get("runtime_launch_authorization_present") is not False:
            fail("post-reboot runtime authorization present")
        checks["post_reboot_host_result_pass"] = True

        anchors = spec.get("anchors") or {}
        assignments = parse_simple_assignments(wrapper_text)
        required_anchor_literals = {
            "EXPECTED_RUNNER_SHA": anchors.get("collector_runner_sha256"),
            "EXPECTED_LIBRARY_SHA": anchors.get("collector_library_sha256"),
            "EXPECTED_FREEZE_SHA": anchors.get("implementation_freeze_sha256"),
            "EXPECTED_SNAPSHOT_SHA": anchors.get("live_snapshot_sha256"),
            "EXPECTED_SERVICE_SHA": anchors.get("service_candidate_sha256"),
            "EXPECTED_CANDIDATE_SHA": anchors.get("launch_candidate_sha256"),
            "EXPECTED_AUTH_SHA": anchors.get("runtime_launch_authorization_sha256"),
            "EXPECTED_ROUTE_GRAPH_SHA": anchors.get("route_graph_sha256"),
        }
        for var, expected in required_anchor_literals.items():
            if not expected or assignments.get(var) != expected:
                fail(f"wrapper anchor mismatch: {var}")
        checks["anchor_count"] = len(required_anchor_literals)

        candidate = load_object(CANDIDATE)
        if candidate.get("status") != "CANDIDATE_NOT_ACTIVE":
            fail("launch candidate top-level status mismatch")
        if candidate.get("runtime_install_authorized") is not False:
            fail("launch candidate unexpectedly runtime-authorized")
        payload = candidate.get("proposed_runtime_payload")
        if not isinstance(payload, dict):
            fail("launch candidate nested runtime payload missing")
        raw_auth = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        auth_sha = hashlib.sha256(raw_auth).hexdigest()
        if auth_sha != anchors.get("runtime_launch_authorization_sha256"):
            fail("runtime launch authorization canonical SHA mismatch")
        checks["canonical_runtime_authorization_sha256"] = auth_sha

        source_pairs, deploy_pairs = resolve_dependency_pairs(wrapper_text)
        if len(source_pairs) != int(spec.get("source_file_count", -1)):
            fail(f"source file count mismatch: {len(source_pairs)}")
        if len(deploy_pairs) != int(spec.get("runtime_deploy_file_count", -1)):
            fail(f"deploy file count mismatch: {len(deploy_pairs)}")
        source_hashes: dict[str, str] = {}
        for rel, expected in source_pairs:
            p = ROOT / rel
            if not p.is_file():
                fail(f"source dependency missing: {rel}")
            actual = sha256_file(p)
            if actual != expected:
                fail(f"source dependency SHA mismatch: {rel}")
            source_hashes[rel] = actual
        if not set(deploy_pairs).issubset(set(source_pairs)):
            fail("runtime deploy dependencies are not a subset of source dependencies")
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

        heredocs = extract_python_heredocs(wrapper_text)
        if len(heredocs) != 5:
            fail(f"embedded Python heredoc count={len(heredocs)} expected=5")
        for idx, block in enumerate(heredocs, start=1):
            compile(block, f"<final-launch-heredoc-{idx}>", "exec")
        checks["embedded_python_block_count"] = len(heredocs)
        checks["embedded_python_compile"] = True

        selftest_count = wrapper_text.count("--mode self-test")
        run_count = wrapper_text.count("--mode run")
        if selftest_count != 1:
            fail(f"collector self-test mode count={selftest_count} expected=1")
        if run_count != 0:
            fail(f"direct collector run mode unexpectedly present: {run_count}")
        checks["collector_selftest_mode_count"] = selftest_count
        checks["direct_collector_run_mode_count"] = run_count

        systemctl_commands: list[str] = []
        for line in wrapper_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("for cmd in "):
                continue
            systemctl_commands.extend(re.findall(r"\bsystemctl\s+([A-Za-z-]+)", line))
        allowed = set(spec.get("allowed_systemctl_subcommands") or [])
        disallowed = [cmd for cmd in systemctl_commands if cmd not in allowed]
        if disallowed:
            fail("disallowed systemctl subcommands: " + ",".join(disallowed))
        required_commands = {"is-active", "is-enabled", "show", "daemon-reload", "enable", "start", "stop", "disable"}
        if set(systemctl_commands) != required_commands:
            fail(f"unexpected systemctl command set: {sorted(set(systemctl_commands))}")
        checks["systemctl_subcommands"] = systemctl_commands

        forbidden_hits = {
            "restart": bool(re.search(r"systemctl\s+restart", wrapper_text)),
            "mask_unmask": bool(re.search(r"systemctl\s+(?:mask|unmask)", wrapper_text)),
            "legacy_stable_repo_unit": "ops/systemd/sc001-b15p1-transferability.service" in wrapper_text,
            "curl": bool(re.search(r"(?m)^\s*curl\b", wrapper_text)),
            "wget": bool(re.search(r"(?m)^\s*wget\b", wrapper_text)),
            "nc": bool(re.search(r"(?m)^\s*nc\b", wrapper_text)),
            "socat": bool(re.search(r"(?m)^\s*socat\b", wrapper_text)),
            "direct_url": bool(re.search(r"https?://", wrapper_text)),
            "remove_state": 'rm -f "$STATE_FILE"' in wrapper_text,
            "remove_manifest": 'rm -f "$MANIFEST_FILE"' in wrapper_text,
            "remove_systemd_log": 'rm -f "$SYSTEMD_LOG"' in wrapper_text,
            "remove_out_dir": 'rm -rf "$OUT_DIR"' in wrapper_text,
        }
        if any(forbidden_hits.values()):
            bad = [k for k, v in forbidden_hits.items() if v]
            fail("forbidden final-wrapper behavior: " + ",".join(bad))
        checks["forbidden_behavior_hits"] = forbidden_hits

        if wrapper_text.count('rm -rf "$STAGE"') != 1:
            fail("staging rm -rf scope/count mismatch")
        checks["staging_rm_rf_scoped"] = True

        required_rollback_markers = (
            'systemctl stop "$SERVICE_NAME"',
            'systemctl disable "$SERVICE_NAME"',
            'if [[ "$auth_sha_now" == "$EXPECTED_AUTH_SHA" ]]',
            'rm -f "$AUTH_FILE"',
            'if [[ "$UNIT_INSTALLED" -eq 1 && "$UNIT_WAS_PRESENT" -eq 0',
            'if [[ "$unit_sha_now" == "$EXPECTED_SERVICE_SHA" ]]',
            'rm -f "$RUNTIME_UNIT"',
            'systemctl daemon-reload',
        )
        missing_rollback = [m for m in required_rollback_markers if m not in wrapper_text]
        if missing_rollback:
            fail("rollback marker missing")
        checks["rollback_marker_count"] = len(required_rollback_markers)

        order = require_order(
            wrapper_text,
            [
                ("host_preconditions", '[[ -f "$SNAPSHOT" ]] || fail "live_capability_snapshot_missing"'),
                ("source_hash_validation", 'for i in "${!SOURCE_FILES[@]}"; do'),
                ("isolated_staging", 'rm -rf "$STAGE"'),
                ("staged_selftest", '"$STAGED_RUNNER" --mode self-test'),
                ("staged_auth_validation", 'print("staged_launch_authorization_validator = PASS")'),
                ("frozen_prerequisites", 'print("final_launch_prerequisites = PASS")'),
                ("mutation_boundary", "MUTATION_STARTED=1"),
                ("runtime_deploy", "# Deploy only the exact B15-P1 frozen runtime files"),
                ("stable_unit_install", 'install -m 0644 -o root -g root "$RUNTIME_ROOT/$SERVICE_REL" "$RUNTIME_UNIT"'),
                ("runtime_unit_verify", 'systemd-analyze verify "$RUNTIME_UNIT"'),
                ("main_daemon_reload", 'systemctl daemon-reload\n\ninstall -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"'),
                ("runtime_auth_install", 'install -m 0640 -o botmarket -g botmarket "$STAGED_AUTH" "$AUTH_FILE"'),
                ("runtime_prestart", 'print("runtime_prestart_freeze_capability_authorization = PASS")'),
                ("enable", 'systemctl enable "$SERVICE_NAME"'),
                ("start", 'systemctl start "$SERVICE_NAME"'),
                ("initial_poll_validation", "# Wait for at least two completed polls"),
                ("launch_report", '"schema": "sc001.b15.p1_collector_final_launch_verification.v0.1"'),
                ("terminal_pass", 'echo "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_PASS"'),
            ],
        )
        checks["ordered_stage_positions"] = order

        verification_markers = (
            "assert poll_count >= 2",
            "assert poll_count - invalid >= 1",
            "assert int(time.time() * 1000) - heartbeat <= 60000",
            'assert len(chain) == 64 and chain != "0" * 64',
            'assert manifest.get("fast_cadence_seconds") == 15',
            'assert manifest.get("request_deadline_seconds") == 12',
            'assert manifest.get("fee_refresh_seconds") == 21600',
            'assert manifest.get("fee_stale_after_seconds") == 28800',
            'assert state.get("price_data_collected") is False',
            'assert state.get("pnl_calculated") is False',
            'assert manifest.get("price_data_authorized") is False',
            'assert manifest.get("pnl_authorized") is False',
        )
        missing_verification = [m for m in verification_markers if m not in wrapper_text]
        if missing_verification:
            fail("runtime verification marker missing")
        checks["runtime_verification_marker_count"] = len(verification_markers)

        if assignments.get("EXPECTED_HOST_REPORT_SHA") != "e249f824a4b10f19a81aa6e01f1f5d7beee5088997880b146378f73f676d7aee":
            fail("post-reboot host-report SHA pin missing")
        if assignments.get("EXPECTED_AUTH_SHA") != "fd5b9a6c683bd15df2dfc26c4ba6497d8e8e152d9b70ed1dc1edeab5107f13be":
            fail("runtime authorization SHA pin missing")

        for key, value in (spec.get("offline_firewall") or {}).items():
            if value is not False:
                fail(f"offline firewall spec mismatch: {key}")

        manifest = {
            "schema": "sc001.b15.p1_final_collector_deployment_launch_wrapper_offline_preflight.v0.1",
            "status": PASS,
            "wrapper_sha256": sha256_file(WRAPPER),
            "spec_sha256": sha256_file(SPEC),
            "freeze_sha256": sha256_file(FREEZE),
            "prelaunch_result_sha256": sha256_file(PRELAUNCH_RESULT),
            "post_reboot_result_sha256": sha256_file(POST_REBOOT_RESULT),
            "launch_candidate_sha256": sha256_file(CANDIDATE),
            "checks": checks,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "systemd_mutation_performed": False,
            "runtime_authorization_created": False,
            "collector_start_performed": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
            "next_state": "AWAIT_EXPLICIT_APPROVAL_FOR_FINAL_B15P1_COLLECTOR_DEPLOYMENT_AND_START",
        }
        write_manifest(manifest)
        print(PASS)
        print("wrapper_sha256 =", manifest["wrapper_sha256"])
        print("source_dependency_count =", checks["source_dependency_count"])
        print("runtime_deploy_dependency_count =", checks["runtime_deploy_dependency_count"])
        print("embedded_python_block_count =", checks["embedded_python_block_count"])
        print("collector_selftest_mode_count =", checks["collector_selftest_mode_count"])
        print("direct_collector_run_mode_count =", checks["direct_collector_run_mode_count"])
        print("systemd_mutation_performed = False")
        print("collector_start_performed = False")
        return 0

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        write_manifest(
            {
                "schema": "sc001.b15.p1_final_collector_deployment_launch_wrapper_offline_preflight.v0.1",
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
                "next_state": "STOP_AND_REVIEW_FINAL_B15P1_COLLECTOR_LAUNCH_WRAPPER",
            }
        )
        print(REVIEW)
        print("error =", error)
        print("systemd_mutation_performed = False")
        print("collector_start_performed = False")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
