from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/work/run/output")
HARNESS = ROOT / "research/sc001/sc001_b15p1_final_launch_v020_offline_preflight_v0_1.py"
HARNESS_MANIFEST = OUT / "final_launch_v020_offline_preflight_manifest.json"
BOOTSTRAP_MANIFEST = OUT / "final_launch_v020_offline_preflight_bootstrap_manifest.json"

EXPECTED_HARNESS_SHA256 = "385289888dc227caa0e4e0fdc3a720baec9a4e47c6d832cca09881775b1a0176"
EXPECTED_PASS = "B15P1_FINAL_LAUNCH_V020_OFFLINE_PREFLIGHT_PASS"
BOOTSTRAP_PASS = "B15P1_FINAL_LAUNCH_V020_OFFLINE_PREFLIGHT_BOOTSTRAP_PASS"
BOOTSTRAP_REVIEW = "B15P1_FINAL_LAUNCH_V020_OFFLINE_PREFLIGHT_BOOTSTRAP_REVIEW"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(obj: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    BOOTSTRAP_MANIFEST.write_text(
        json.dumps(obj, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    checks: dict = {}
    try:
        actual = sha256_file(HARNESS)
        checks["harness_sha256"] = actual
        if actual != EXPECTED_HARNESS_SHA256:
            raise RuntimeError("harness SHA mismatch")

        source = HARNESS.read_text(encoding="utf-8")
        compile(source, str(HARNESS), "exec")
        checks["harness_compile"] = True

        proc = subprocess.run(
            [sys.executable, str(HARNESS)],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
            timeout=180,
        )
        checks["harness_returncode"] = proc.returncode
        checks["stdout_tail"] = proc.stdout[-12000:]
        checks["stderr_tail"] = proc.stderr[-12000:]
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")

        if not HARNESS_MANIFEST.is_file():
            raise RuntimeError("harness manifest missing")
        manifest = json.loads(HARNESS_MANIFEST.read_text(encoding="utf-8"))
        manifest_sha = sha256_file(HARNESS_MANIFEST)
        checks["harness_manifest_sha256"] = manifest_sha
        checks["harness_manifest_status"] = manifest.get("status")

        if proc.returncode != 0:
            raise RuntimeError(f"harness rc={proc.returncode}")
        if manifest.get("status") != EXPECTED_PASS:
            raise RuntimeError("harness manifest PASS mismatch")
        if EXPECTED_PASS not in proc.stdout:
            raise RuntimeError("harness PASS token missing")

        write({
            "schema": "sc001.b15.p1_final_launch_v020_offline_preflight_bootstrap.v0.1",
            "status": BOOTSTRAP_PASS,
            "checks": checks,
            "harness_sha256": actual,
            "harness_manifest_sha256": manifest_sha,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "systemd_mutation_performed": False,
            "runtime_authorization_created": False,
            "collector_start_performed": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
            "next_state": "FINAL_LAUNCH_V020_OFFLINE_PREFLIGHT_PASS",
        })
        print(BOOTSTRAP_PASS)
        return 0

    except Exception as exc:
        write({
            "schema": "sc001.b15.p1_final_launch_v020_offline_preflight_bootstrap.v0.1",
            "status": BOOTSTRAP_REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "checks": checks,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "systemd_mutation_performed": False,
            "runtime_authorization_created": False,
            "collector_start_performed": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
            "next_state": "STOP_AND_REVIEW_FINAL_LAUNCH_V020_OFFLINE_PREFLIGHT",
        })
        print(BOOTSTRAP_REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
