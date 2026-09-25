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
MANIFEST = OUT / "collector_host_deployment_readiness_wrapper_offline_preflight_manifest.json"

WRAPPER = ROOT / "scripts/research/run-b15p1-collector-host-deployment-readiness-v0.1.sh"
SPEC = ROOT / "docs/research/sc001-b15-p1-collector-host-deployment-readiness-wrapper-preflight-spec-v0.1.json"
FREEZE = ROOT / "docs/research/sc001-b15-p1-collector-host-deployment-readiness-wrapper-preflight-freeze-v0.1.json"
PRELAUNCH_RESULT = ROOT / "docs/research/sc001-b15-p1-collector-prelaunch-readiness-result-v0.1.json"
LIVE_RESULT = ROOT / "docs/research/sc001-b15-p1-live-source-capability-revalidation-v0.2.1-result-v0.1.json"

PASS = "B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_WRAPPER_OFFLINE_PREFLIGHT_PASS"
REVIEW = "B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_WRAPPER_OFFLINE_PREFLIGHT_REVIEW"


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
    if fr.get("status") != "FROZEN_BEFORE_B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_WRAPPER_OFFLINE_PREFLIGHT":
        fail("wrapper preflight freeze status mismatch")
    expected = {
        "harness_sha256": sha256_file(Path(__file__).resolve()),
        "wrapper_sha256": sha256_file(WRAPPER),
        "spec_sha256": sha256_file(SPEC),
        "prelaunch_result_sha256": sha256_file(PRELAUNCH_RESULT),
        "live_result_sha256": sha256_file(LIVE_RESULT),
    }
    for key, actual in expected.items():
        if fr.get(key) != actual:
            fail(f"freeze hash mismatch {key}: expected={fr.get(key)} actual={actual}")
    for key in (
        "credentials_available",
        "exchange_calls_allowed",
        "collector_start_allowed",
        "systemd_mutation_allowed",
        "runtime_authorization_creation_allowed",
        "production_repo_mutation_allowed",
        "price_data_allowed",
        "pnl_data_allowed",
        "live_execution_allowed",
    ):
        if fr.get(key) is not False:
            fail(f"offline firewall mismatch: {key}")
    return fr


def extract_python_heredocs(text: str) -> list[str]:
    blocks = re.findall(r"<<'PY'\n(.*?)\nPY(?:\n|$)", text, flags=re.DOTALL)
    if len(blocks) != 1:
        fail(f"expected 1 embedded Python heredoc, observed {len(blocks)}")
    return blocks


def main() -> int:
    checks: dict[str, Any] = {}
    try:
        require_freeze()
        spec = load_object(SPEC)
        wrapper_text = WRAPPER.read_text(encoding="utf-8")

        if spec.get("status") != "FROZEN_BEFORE_OFFLINE_PREFLIGHT":
            fail("wrapper preflight spec status mismatch")
        if spec.get("expected_pass_status") != PASS:
            fail("wrapper preflight expected status mismatch")

        wrapper_spec = spec.get("wrapper") or {}
        if wrapper_spec.get("sha256") != sha256_file(WRAPPER):
            fail("wrapper SHA differs from spec")

        pre_req = ((spec.get("prerequisites") or {}).get("prelaunch_result") or {})
        pre_obj = load_object(PRELAUNCH_RESULT)
        if pre_obj.get("status") != pre_req.get("required_status"):
            fail("prelaunch result status mismatch")
        if sha256_file(PRELAUNCH_RESULT) != pre_req.get("sha256"):
            fail("prelaunch result SHA mismatch")
        if (pre_obj.get("safety") or {}).get("collector_start_performed") is not False:
            fail("prelaunch result collector start safety mismatch")
        if (pre_obj.get("safety") or {}).get("runtime_authorization_created") is not False:
            fail("prelaunch result runtime authorization safety mismatch")
        checks["prelaunch_result_pass"] = True

        live_req = ((spec.get("prerequisites") or {}).get("live_capability_result") or {})
        live_obj = load_object(LIVE_RESULT)
        if live_obj.get("status") != live_req.get("required_status"):
            fail("live capability result status mismatch")
        if sha256_file(LIVE_RESULT) != live_req.get("sha256"):
            fail("live capability result SHA mismatch")
        if (live_obj.get("snapshot") or {}).get("sha256") != live_req.get("live_snapshot_sha256"):
            fail("live snapshot SHA mismatch")
        checks["live_capability_result_pass"] = True

        deps = spec.get("staged_dependencies") or []
        if len(deps) != 21:
            fail(f"staged dependency count mismatch: {len(deps)}")
        dep_hashes: dict[str, str] = {}
        for item in deps:
            rel = str(item.get("path") or "")
            expected = str(item.get("sha256") or "")
            if not rel or not expected:
                fail("malformed staged dependency entry")
            p = ROOT / rel
            if not p.is_file():
                fail(f"staged dependency missing: {rel}")
            actual = sha256_file(p)
            if actual != expected:
                fail(f"staged dependency SHA mismatch: {rel}")
            if rel not in wrapper_text:
                fail(f"wrapper does not name staged dependency: {rel}")
            if expected not in wrapper_text:
                fail(f"wrapper does not pin staged dependency SHA: {rel}")
            dep_hashes[rel] = actual
        checks["staged_dependency_count"] = len(dep_hashes)
        checks["staged_dependency_hashes"] = dep_hashes

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
        for idx, block in enumerate(heredocs, start=1):
            compile(block, f"<host-readiness-wrapper-heredoc-{idx}>", "exec")
        checks["embedded_python_block_count"] = len(heredocs)
        checks["embedded_python_compile"] = True

        required_markers = {
            "strict_mode": "set -euo pipefail",
            "umask": "umask 027",
            "root_gate": "wrapper_must_run_as_root",
            "snapshot_sha_gate": "live_capability_snapshot_sha_mismatch",
            "env_mode_gate": "credential_env_mode_not_0600",
            "env_owner_gate": "credential_env_owner_mismatch:",
            "runtime_auth_absence": "active_runtime_launch_authorization_already_present",
            "state_absence": "collector_state_already_present",
            "manifest_absence": "collector_manifest_already_present",
            "process_absence": "collector_process_already_running",
            "inactive_gate": "stable_service_not_inactive:",
            "disabled_gate": "stable_service_not_disabled:",
            "runtime_unit_sha_gate": "runtime_unit_sha_mismatch:",
            "dropin_gate": "stable_service_dropins_present",
            "source_sha_gate": "source_sha_mismatch:",
            "staged_sha_gate": "staged_sha_mismatch:",
            "symlink_gate": "staging_symlink_detected",
            "count_gate": "unexpected_staging_file_count:",
            "systemd_verify": "systemd-analyze verify",
            "env_i": "env -i",
            "selftest_pass": "B15P1_NONPRICE_COLLECTOR_V013_SELF_TEST_PASS",
            "host_report": "host_deployment_readiness_manifest.json",
            "final_pass": "B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_PASS",
        }
        marker_results = {key: marker in wrapper_text for key, marker in required_markers.items()}
        if not all(marker_results.values()):
            fail("required static marker missing")
        checks["required_static_markers"] = marker_results

        mode_selftest_count = wrapper_text.count("--mode self-test")
        mode_run_count = wrapper_text.count("--mode run")
        checks["collector_selftest_mode_count"] = mode_selftest_count
        checks["collector_run_mode_count"] = mode_run_count
        if mode_selftest_count != 1:
            fail(f"expected exactly one --mode self-test, observed {mode_selftest_count}")
        if mode_run_count != 0:
            fail(f"collector --mode run unexpectedly present: {mode_run_count}")

        systemctl_commands: list[str] = []
        for line in wrapper_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("for cmd in "):
                continue
            systemctl_commands.extend(
                re.findall(r"\bsystemctl\s+([A-Za-z-]+)", line)
            )
        allowed = set(spec.get("allowed_systemctl_subcommands") or [])
        disallowed = [cmd for cmd in systemctl_commands if cmd not in allowed]
        checks["systemctl_subcommands"] = systemctl_commands
        checks["disallowed_systemctl_subcommands"] = disallowed
        if disallowed:
            fail("disallowed systemctl subcommand: " + ",".join(disallowed))
        if set(systemctl_commands) != {"is-active", "is-enabled", "show"}:
            fail(f"unexpected systemctl command set: {sorted(set(systemctl_commands))}")

        forbidden_patterns = {
            "daemon_reload": r"systemctl\s+daemon-reload",
            "start": r"systemctl\s+start",
            "enable": r"systemctl\s+enable",
            "restart": r"systemctl\s+restart",
            "stop": r"systemctl\s+stop",
            "mask_unmask": r"systemctl\s+(?:mask|unmask)",
            "runtime_unit_install": r"install[^\n]*\$RUNTIME_UNIT",
            "runtime_auth_write": r"(?:>|tee\s+)[^\n]*\$AUTH_FILE",
            "production_repo_write": r"(?:install|cp|mv|rm)[^\n]*\$REPO(?:/|\b)",
            "direct_url": r"https?://",
            "curl": r"(?m)^\s*curl\b",
            "wget": r"(?m)^\s*wget\b",
        }
        forbidden_hits = {
            name: bool(re.search(pattern, wrapper_text))
            for name, pattern in forbidden_patterns.items()
        }
        checks["forbidden_behavior_hits"] = forbidden_hits
        if any(forbidden_hits.values()):
            bad = [k for k, v in forbidden_hits.items() if v]
            fail("forbidden wrapper behavior found: " + ",".join(bad))

        if wrapper_text.count("rm -rf") != 1 or 'rm -rf "$STAGE"' not in wrapper_text:
            fail("rm -rf is not scoped exactly to staging root")
        checks["rm_rf_scoped_to_stage_only"] = True

        if "ops/systemd/sc001-b15p1-transferability.service" in wrapper_text:
            fail("legacy stable repository unit referenced by wrapper")
        if "ops/systemd/sc001-b15p1-transferability-v0.1.3.service" not in wrapper_text:
            fail("versioned v0.1.3 service candidate missing")
        checks["versioned_service_only"] = True

        if 'EXPECTED_SNAPSHOT_SHA="14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc"' not in wrapper_text:
            fail("expected live snapshot SHA pin missing")

        if 'STAGE_FILES=(' not in wrapper_text or 'EXPECTED_SHAS=(' not in wrapper_text:
            fail("stage dependency arrays missing")

        if 'systemd_start_enable_performed=False' not in wrapper_text:
            fail("final systemd non-start assertion missing")
        if 'runtime_authorization_created=False' not in wrapper_text:
            fail("final runtime authorization noncreation assertion missing")

        for key, value in (spec.get("forbidden_host_behavior") or {}).items():
            if value is not True:
                fail(f"spec forbidden behavior declaration mismatch: {key}")

        manifest = {
            "schema": "sc001.b15.p1_collector_host_deployment_readiness_wrapper_offline_preflight.v0.1",
            "status": PASS,
            "wrapper_sha256": sha256_file(WRAPPER),
            "spec_sha256": sha256_file(SPEC),
            "freeze_sha256": sha256_file(FREEZE),
            "prelaunch_result_sha256": sha256_file(PRELAUNCH_RESULT),
            "live_result_sha256": sha256_file(LIVE_RESULT),
            "checks": checks,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "collector_start_performed": False,
            "systemd_mutation_performed": False,
            "runtime_authorization_created": False,
            "production_repo_mutation_performed": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
            "next_state": "AWAIT_EXPLICIT_APPROVAL_FOR_HOST_DEPLOYMENT_READINESS_WRAPPER",
        }
        write_manifest(manifest)
        print(PASS)
        print("wrapper_sha256 =", manifest["wrapper_sha256"])
        print("staged_dependency_count =", checks["staged_dependency_count"])
        print("systemctl_subcommands =", ",".join(systemctl_commands))
        print("collector_selftest_mode_count =", mode_selftest_count)
        print("collector_run_mode_count =", mode_run_count)
        print("collector_start_performed = False")
        print("systemd_mutation_performed = False")
        return 0

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        write_manifest(
            {
                "schema": "sc001.b15.p1_collector_host_deployment_readiness_wrapper_offline_preflight.v0.1",
                "status": REVIEW,
                "error": error,
                "checks": checks,
                "credentials_available": False,
                "exchange_calls_performed": False,
                "collector_start_performed": False,
                "systemd_mutation_performed": False,
                "runtime_authorization_created": False,
                "production_repo_mutation_performed": False,
                "price_data_used": False,
                "pnl_data_used": False,
                "live_execution_performed": False,
                "next_state": "STOP_AND_REVIEW_HOST_DEPLOYMENT_READINESS_WRAPPER",
            }
        )
        print(REVIEW)
        print("error =", error)
        print("collector_start_performed = False")
        print("systemd_mutation_performed = False")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
