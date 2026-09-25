from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/work/run/output")
MANIFEST = OUT / "final_launch_v01_failure_recovery_wrapper_offline_preflight_manifest.json"

WRAPPER = ROOT / "scripts/research/run-b15p1-final-launch-v0.1-failure-recovery-v0.1.sh"
SPEC = ROOT / "docs/research/sc001-b15-p1-final-launch-v0.1-failure-recovery-wrapper-preflight-spec-v0.1.json"
FREEZE = ROOT / "docs/research/sc001-b15-p1-final-launch-v0.1-failure-recovery-wrapper-preflight-freeze-v0.1.json"
DIAGNOSTIC = ROOT / "docs/research/sc001-b15-p1-final-launch-attempt-v0.1-technical-failure-diagnostic.json"

PASS = "B15P1_FINAL_LAUNCH_V01_FAILURE_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_PASS"
REVIEW = "B15P1_FINAL_LAUNCH_V01_FAILURE_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_REVIEW"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(obj):
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    checks = {}
    try:
        fr = load_json(FREEZE)
        if fr.get("status") != "FROZEN_BEFORE_B15P1_FINAL_LAUNCH_V01_FAILURE_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT":
            raise RuntimeError("freeze status mismatch")
        expected = {
            "harness_sha256": sha256_file(Path(__file__).resolve()),
            "wrapper_sha256": sha256_file(WRAPPER),
            "spec_sha256": sha256_file(SPEC),
            "diagnostic_sha256": sha256_file(DIAGNOSTIC),
        }
        for key, actual in expected.items():
            if fr.get(key) != actual:
                raise RuntimeError(f"freeze hash mismatch {key}")

        spec = load_json(SPEC)
        if spec.get("status") != "FROZEN_BEFORE_OFFLINE_PREFLIGHT":
            raise RuntimeError("spec status mismatch")
        if spec.get("expected_pass_status") != PASS:
            raise RuntimeError("expected pass status mismatch")
        if (spec.get("wrapper") or {}).get("sha256") != sha256_file(WRAPPER):
            raise RuntimeError("wrapper SHA mismatch")

        diag = load_json(DIAGNOSTIC)
        req = spec.get("failure_diagnostic") or {}
        if diag.get("status") != req.get("required_status"):
            raise RuntimeError("diagnostic status mismatch")
        if (diag.get("exact_failure") or {}).get("failure_class") != req.get("required_failure_class"):
            raise RuntimeError("diagnostic failure class mismatch")

        text = WRAPPER.read_text(encoding="utf-8")
        bash = shutil.which("bash")
        if not bash:
            raise RuntimeError("bash unavailable")
        p = subprocess.run([bash, "-n", str(WRAPPER)], cwd=str(ROOT), capture_output=True, text=True, check=False)
        checks["bash_syntax_returncode"] = p.returncode
        if p.returncode != 0:
            raise RuntimeError("bash -n failed")

        py_blocks = re.findall(r"<<'PY'\n(.*?)\nPY(?:\n|$)", text, flags=re.DOTALL)
        if len(py_blocks) != 1:
            raise RuntimeError(f"expected one Python heredoc, observed {len(py_blocks)}")
        compile(py_blocks[0], "<recovery-heredoc>", "exec")
        checks["embedded_python_compile"] = True

        required = [
            'systemctl stop "$SERVICE_NAME"',
            'systemctl disable "$SERVICE_NAME"',
            'runtime_authorization_unexpected_sha:',
            'runtime_unit_unexpected_sha:',
            'mv "$AUTH_FILE" "$ATTEMPT_DIR/collector_launch_authorization.json"',
            'cp -a "$RUNTIME_UNIT" "$ATTEMPT_DIR/runtime_unit.service"',
            'rm -f "$RUNTIME_UNIT"',
            'systemctl daemon-reload',
            '"$STATE_FILE"',
            '"$MANIFEST_FILE"',
            '"$SYSTEMD_LOG"',
            '"$OUT_DIR/raw_objects"',
            '"$OUT_DIR/polls"',
            '"$OUT_DIR/normalized"',
            '"$OUT_DIR/events"',
            '"$OUT_DIR/gaps"',
            '"$OUT_DIR/fees"',
            '"$OUT_DIR/invalid"',
            '"$OUT_DIR/daily_manifests"',
            'root.rglob("*")',
            'runtime_unit=ABSENT',
            'runtime_authorization=ABSENT',
            'active_state=ABSENT',
            'active_manifest=ABSENT',
        ]
        missing = [x for x in required if x not in text]
        if missing:
            raise RuntimeError("required recovery marker missing")
        checks["required_marker_count"] = len(required)

        protected = spec.get("protected_files_must_remain_active") or []
        protected_delete_hits = []
        for name in protected:
            for line in text.splitlines():
                s = line.strip()
                if (s.startswith("rm ") or s.startswith("mv ")) and name in s:
                    protected_delete_hits.append((name, s))
        if protected_delete_hits:
            raise RuntimeError("protected evidence mutation detected")
        checks["protected_evidence_mutation_hits"] = []

        systemctl_commands = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#") or s.startswith("for cmd in "):
                continue
            systemctl_commands.extend(re.findall(r"\bsystemctl\s+([A-Za-z-]+)", line))
        allowed = set(spec.get("allowed_systemctl_subcommands") or [])
        disallowed = [c for c in systemctl_commands if c not in allowed]
        if disallowed:
            raise RuntimeError("disallowed systemctl command")
        checks["systemctl_subcommands"] = systemctl_commands

        forbidden = {
            "start": bool(re.search(r"systemctl\s+start", text)),
            "enable": bool(re.search(r"systemctl\s+enable", text)),
            "restart": bool(re.search(r"systemctl\s+restart", text)),
            "mask_unmask": bool(re.search(r"systemctl\s+(?:mask|unmask)", text)),
            "collector_run": "--mode run" in text,
            "curl": bool(re.search(r"(?m)^\s*curl\b", text)),
            "wget": bool(re.search(r"(?m)^\s*wget\b", text)),
            "direct_url": bool(re.search(r"https?://", text)),
            "snapshot_delete": bool(re.search(r'rm\s+-f\s+"\$SNAPSHOT"', text)),
        }
        if any(forbidden.values()):
            raise RuntimeError("forbidden recovery behavior detected")
        checks["forbidden_behavior_hits"] = forbidden

        manifest = {
            "schema": "sc001.b15.p1_final_launch_v01_failure_recovery_wrapper_offline_preflight.v0.1",
            "status": PASS,
            "wrapper_sha256": sha256_file(WRAPPER),
            "spec_sha256": sha256_file(SPEC),
            "freeze_sha256": sha256_file(FREEZE),
            "diagnostic_sha256": sha256_file(DIAGNOSTIC),
            "checks": checks,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "collector_start_performed": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
            "next_state": "AWAIT_EXPLICIT_APPROVAL_FOR_FAILURE_RECOVERY_HOST_WRAPPER",
        }
        write_manifest(manifest)
        print(PASS)
        print("wrapper_sha256 =", manifest["wrapper_sha256"])
        print("systemctl_subcommands =", ",".join(systemctl_commands))
        print("collector_start_performed = False")
        return 0
    except Exception as exc:
        write_manifest({
            "schema": "sc001.b15.p1_final_launch_v01_failure_recovery_wrapper_offline_preflight.v0.1",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "checks": checks,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "collector_start_performed": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
        })
        print(REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
