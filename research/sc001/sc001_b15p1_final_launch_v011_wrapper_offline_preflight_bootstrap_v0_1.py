from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/work/run/output")
HARNESS = ROOT / "research/sc001/sc001_b15p1_final_launch_v011_wrapper_offline_preflight_v0_1_1.py"
HARNESS_MANIFEST = OUT / "final_launch_v011_wrapper_offline_preflight_manifest.json"
BOOTSTRAP_MANIFEST = OUT / "final_launch_v011_wrapper_offline_preflight_bootstrap_manifest.json"

EXPECTED_HARNESS_SHA256 = "133f8ccc8e515727feee11fddf8718964a18bda754fe22a74aaceb6509869108"
EXPECTED_HARNESS_PASS = "B15P1_FINAL_LAUNCH_V011_WRAPPER_OFFLINE_PREFLIGHT_PASS"
BOOTSTRAP_PASS = "B15P1_FINAL_LAUNCH_V011_PREFLIGHT_BOOTSTRAP_PASS"
BOOTSTRAP_REVIEW = "B15P1_FINAL_LAUNCH_V011_PREFLIGHT_BOOTSTRAP_REVIEW"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(obj: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    BOOTSTRAP_MANIFEST.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    checks: dict[str, object] = {}
    try:
        if not HARNESS.is_file():
            raise RuntimeError("corrected harness missing")
        actual_sha = sha256_file(HARNESS)
        checks["harness_sha256"] = actual_sha
        if actual_sha != EXPECTED_HARNESS_SHA256:
            raise RuntimeError(
                f"harness SHA mismatch: expected={EXPECTED_HARNESS_SHA256} actual={actual_sha}"
            )

        source = HARNESS.read_text(encoding="utf-8")
        compile(source, str(HARNESS), "exec")
        checks["harness_compile"] = True

        proc = subprocess.run(
            [sys.executable, str(HARNESS)],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        checks["harness_returncode"] = proc.returncode
        checks["harness_stdout_tail"] = proc.stdout[-8192:]
        checks["harness_stderr_tail"] = proc.stderr[-8192:]

        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")

        if not HARNESS_MANIFEST.is_file():
            raise RuntimeError("harness manifest missing after execution")
        harness_manifest_sha = sha256_file(HARNESS_MANIFEST)
        checks["harness_manifest_sha256"] = harness_manifest_sha
        harness_manifest = json.loads(HARNESS_MANIFEST.read_text(encoding="utf-8"))
        checks["harness_manifest_status"] = harness_manifest.get("status")

        if proc.returncode != 0:
            raise RuntimeError(f"harness returned rc={proc.returncode}")
        if harness_manifest.get("status") != EXPECTED_HARNESS_PASS:
            raise RuntimeError(
                f"harness manifest status mismatch: {harness_manifest.get('status')}"
            )
        if EXPECTED_HARNESS_PASS not in proc.stdout:
            raise RuntimeError("harness PASS token missing from stdout")

        manifest = {
            "schema": "sc001.b15.p1_final_launch_v011_preflight_bootstrap.v0.1",
            "status": BOOTSTRAP_PASS,
            "checks": checks,
            "harness_sha256": actual_sha,
            "harness_manifest_sha256": harness_manifest_sha,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "systemd_mutation_performed": False,
            "runtime_authorization_created": False,
            "collector_start_performed": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
            "next_state": "V011_WRAPPER_OFFLINE_PREFLIGHT_PASS",
        }
        write_manifest(manifest)
        print(BOOTSTRAP_PASS)
        print("harness_sha256 =", actual_sha)
        print("harness_manifest_sha256 =", harness_manifest_sha)
        return 0

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        write_manifest(
            {
                "schema": "sc001.b15.p1_final_launch_v011_preflight_bootstrap.v0.1",
                "status": BOOTSTRAP_REVIEW,
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
                "next_state": "STOP_AND_REVIEW_V011_PREFLIGHT_BOOTSTRAP",
            }
        )
        print(BOOTSTRAP_REVIEW)
        print("error =", error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
