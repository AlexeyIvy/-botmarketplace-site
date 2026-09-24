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
MANIFEST = OUT / "live_wrapper_offline_preflight_manifest.json"

WRAPPER = ROOT / "scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.2.sh"
SPEC = ROOT / "docs/research/sc001-b15-p1-source-capability-live-wrapper-v0.2-preflight-spec-v0.1.json"
FREEZE = ROOT / "docs/research/sc001-b15-p1-source-capability-live-wrapper-v0.2-preflight-freeze-v0.1.json"
OFFLINE_RESULT = ROOT / "docs/research/sc001-b15-p1-adapter-combined-offline-validation-result-v0.1.1.json"
CAP_PROBE = ROOT / "research/sc001/sc001_b15p1_nonprice_source_capability_revalidation_v0_2_1.py"
CAP_FREEZE = ROOT / "docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-freeze-v0.2.1.json"

PASS = "B15P1_SOURCE_CAPABILITY_LIVE_WRAPPER_V02_OFFLINE_PREFLIGHT_PASS"
REVIEW = "B15P1_SOURCE_CAPABILITY_LIVE_WRAPPER_V02_OFFLINE_PREFLIGHT_REVIEW"


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
    if fr.get("status") != "FROZEN_BEFORE_B15P1_SOURCE_CAPABILITY_LIVE_WRAPPER_V02_OFFLINE_PREFLIGHT":
        fail("wrapper preflight freeze status mismatch")
    expected = {
        "preflight_harness_sha256": sha256_file(Path(__file__).resolve()),
        "wrapper_sha256": sha256_file(WRAPPER),
        "spec_sha256": sha256_file(SPEC),
        "offline_result_sha256": sha256_file(OFFLINE_RESULT),
        "capability_probe_sha256": sha256_file(CAP_PROBE),
        "capability_freeze_sha256": sha256_file(CAP_FREEZE),
    }
    for key, actual in expected.items():
        if fr.get(key) != actual:
            fail(f"freeze hash mismatch {key}: expected={fr.get(key)} actual={actual}")
    for key in (
        "credentials_available",
        "exchange_calls_allowed",
        "collector_launch_allowed",
        "price_data_allowed",
        "pnl_data_allowed",
        "live_execution_allowed",
    ):
        if fr.get(key) is not False:
            fail(f"offline firewall mismatch: {key}")
    return fr


def extract_python_heredocs(text: str) -> list[str]:
    blocks = re.findall(r"<<'PY'\n(.*?)\nPY(?:\n|$)", text, flags=re.DOTALL)
    if len(blocks) != 2:
        fail(f"expected 2 embedded Python heredocs, observed {len(blocks)}")
    return blocks


def main() -> int:
    checks: dict[str, Any] = {}
    try:
        fr = require_freeze()
        spec = load_object(SPEC)
        offline = load_object(OFFLINE_RESULT)
        wrapper_text = WRAPPER.read_text(encoding="utf-8")

        if spec.get("status") != "FROZEN_BEFORE_OFFLINE_PREFLIGHT":
            fail("wrapper preflight spec status mismatch")
        if spec.get("expected_pass_status") != PASS:
            fail("wrapper preflight expected status mismatch")

        wrapper_spec = spec.get("wrapper") or {}
        if wrapper_spec.get("sha256") != sha256_file(WRAPPER):
            fail("wrapper SHA differs from preflight spec")
        if wrapper_spec.get("target_capability_version") != "v0.2.1":
            fail("target capability version mismatch")

        prereq = spec.get("offline_prerequisite") or {}
        if prereq.get("result_sha256") != sha256_file(OFFLINE_RESULT):
            fail("offline prerequisite SHA mismatch")
        if offline.get("status") != "B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_PASS":
            fail("combined offline prerequisite is not PASS")
        if offline.get("job_id") != "job_20260924T170906Z_810905df":
            fail("combined offline prerequisite job mismatch")
        if offline.get("package_integrity_ok") is not True or offline.get("exit_code") != 0:
            fail("combined offline prerequisite integrity/exit mismatch")

        offline_safety = offline.get("safety") or {}
        for key in (
            "credentials_used",
            "exchange_calls_performed",
            "capability_snapshot_written",
            "collector_launch_authorized",
            "price_data_used",
            "pnl_data_used",
            "live_execution_authorized",
        ):
            if offline_safety.get(key) is not False:
                fail(f"combined offline prerequisite safety mismatch: {key}")

        deps = spec.get("staged_dependencies") or []
        if len(deps) != 10:
            fail(f"staged dependency count mismatch: {len(deps)}")
        dep_checks = {}
        for item in deps:
            rel = str(item.get("path") or "")
            expected_sha = str(item.get("sha256") or "")
            if not rel or not expected_sha:
                fail("malformed staged dependency entry")
            p = ROOT / rel
            if not p.is_file():
                fail(f"staged dependency missing: {rel}")
            actual_sha = sha256_file(p)
            if actual_sha != expected_sha:
                fail(f"staged dependency SHA mismatch: {rel}")
            if rel not in wrapper_text:
                fail(f"wrapper does not name staged dependency: {rel}")
            if expected_sha not in wrapper_text:
                fail(f"wrapper does not pin staged dependency SHA: {rel}")
            dep_checks[rel] = actual_sha
        checks["staged_dependency_count"] = len(dep_checks)
        checks["staged_dependency_hashes"] = dep_checks

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
            compile(block, f"<wrapper-heredoc-{idx}>", "exec")
        checks["embedded_python_block_count"] = len(heredocs)
        checks["embedded_python_compile"] = True

        required_markers = {
            "strict_mode": "set -euo pipefail",
            "umask": "umask 027",
            "root_gate": "wrapper_must_run_as_root",
            "env_mode_gate": "credential_env_mode_not_0600",
            "env_readability_gate": "credential_env_not_readable_by_botmarket",
            "source_sha_gate": "source_sha_mismatch:",
            "staged_sha_gate": "staged_sha_mismatch:",
            "staging_symlink_gate": "staging_symlink_detected",
            "staging_count_gate": "unexpected_staging_file_count:",
            "offline_prerequisite": "offline_combined_prerequisite = PASS",
            "run_as_botmarket": "sudo -u botmarket -H",
            "repo_root_stage": 'B15P1_REPO_ROOT="$STAGE"',
            "snapshot_stage": 'B15P1_CAPABILITY_SNAPSHOT="$SNAPSHOT"',
            "stale_output_delete": 'rm -f "$SNAPSHOT" "$SAFE_SUMMARY"',
            "post_security": 'security_firewall = PASS',
            "pass_token": "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_V021_PASS",
        }
        static = {}
        for key, marker in required_markers.items():
            static[key] = marker in wrapper_text
        if not all(static.values()):
            fail("required wrapper static marker missing")
        checks["required_static_markers"] = static

        mode_run_count = wrapper_text.count("--mode run")
        checks["probe_mode_run_count"] = mode_run_count
        if mode_run_count != 1:
            fail(f"expected one --mode run, observed {mode_run_count}")

        direct_network_patterns = [
            r"(?m)^\s*(?:sudo\s+)?curl\b",
            r"(?m)^\s*(?:sudo\s+)?wget\b",
            r"(?m)^\s*(?:sudo\s+)?nc\b",
            r"(?m)^\s*(?:sudo\s+)?socat\b",
            r"https?://",
        ]
        network_hits = [p for p in direct_network_patterns if re.search(p, wrapper_text)]
        checks["direct_network_command_hits"] = network_hits
        if network_hits:
            fail("wrapper contains direct network command/URL")

        service_patterns = [
            r"(?m)^\s*systemctl\s+(?:start|enable|restart)\b",
            r"(?m)^\s*service\s+\S+\s+(?:start|restart)\b",
        ]
        service_hits = [p for p in service_patterns if re.search(p, wrapper_text)]
        checks["service_mutation_hits"] = service_hits
        if service_hits:
            fail("wrapper contains service mutation command")

        forbidden_tokens = (
            "collector_launch_authorization.json",
            "B15P1_LAUNCH_AUTHORIZATION",
            "SC001_B15_OKX_API_KEY",
            "SC001_B15_OKX_API_SECRET",
            "SC001_B15_OKX_PASSPHRASE",
            "SC001_B15_BYBIT_API_KEY",
            "SC001_B15_BYBIT_API_SECRET",
        )
        token_hits = [token for token in forbidden_tokens if token in wrapper_text]
        checks["forbidden_token_hits"] = token_hits
        if token_hits:
            fail("wrapper contains forbidden credential/launch token names")

        permission_mutation_hits = []
        for line in wrapper_text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("chmod ", "chown ")):
                if "$REPO" in stripped or "/var/lib/botmarket-github-control" in stripped:
                    permission_mutation_hits.append(stripped)
        checks["github_control_permission_mutation_hits"] = permission_mutation_hits
        if permission_mutation_hits:
            fail("wrapper mutates GitHub Control clone permissions")

        if wrapper_text.count("rm -rf") != 1 or 'rm -rf "$STAGE"' not in wrapper_text:
            fail("rm -rf scope is not exactly the staging root")
        checks["rm_rf_scoped_to_stage_only"] = True

        for key, value in (spec.get("offline_firewall") or {}).items():
            if value is not False:
                fail(f"spec offline firewall mismatch: {key}")

        manifest = {
            "schema": "sc001.b15.p1_source_capability_live_wrapper_offline_preflight.v0.1",
            "status": PASS,
            "wrapper_sha256": sha256_file(WRAPPER),
            "spec_sha256": sha256_file(SPEC),
            "freeze_sha256": sha256_file(FREEZE),
            "offline_result_sha256": sha256_file(OFFLINE_RESULT),
            "checks": checks,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "collector_launch_performed": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
            "next_state": "AWAIT_EXPLICIT_APPROVAL_FOR_B15P1_LIVE_READ_ONLY_CAPABILITY_REVALIDATION_V021",
        }
        write_manifest(manifest)
        print(PASS)
        print("wrapper_sha256 =", manifest["wrapper_sha256"])
        print("staged_dependency_count =", checks["staged_dependency_count"])
        print("embedded_python_block_count =", checks["embedded_python_block_count"])
        print("exchange_calls_performed = False")
        print("credentials_available = False")
        return 0

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        write_manifest(
            {
                "schema": "sc001.b15.p1_source_capability_live_wrapper_offline_preflight.v0.1",
                "status": REVIEW,
                "error": error,
                "checks": checks,
                "credentials_available": False,
                "exchange_calls_performed": False,
                "collector_launch_performed": False,
                "price_data_used": False,
                "pnl_data_used": False,
                "live_execution_performed": False,
                "next_state": "STOP_AND_REVIEW_B15P1_LIVE_WRAPPER_PREFLIGHT",
            }
        )
        print(REVIEW)
        print("error =", error)
        print("exchange_calls_performed = False")
        print("credentials_available = False")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
