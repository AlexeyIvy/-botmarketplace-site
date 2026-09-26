from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/work/run/output")
HARNESS = ROOT / "research/sc001/sc001_b15p1_v011_source_invalid_recovery_before_v014_offline_preflight_v0_1_2.py"
HARNESS_MANIFEST = OUT / "v011_source_invalid_recovery_before_v014_offline_preflight_v012_manifest.json"
BOOTSTRAP_MANIFEST = OUT / "v011_source_invalid_recovery_before_v014_offline_preflight_bootstrap_v012_manifest.json"

EXPECTED_HARNESS_SHA256 = "ad0a5ec06920cb77844e1cf6b18e757d75bb4376777d5cec6250ff4767eeedbf"
EXPECTED_PASS = "B15P1_V011_SOURCE_INVALID_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_V012_PASS"
BOOTSTRAP_PASS = "B15P1_V011_SOURCE_INVALID_RECOVERY_BOOTSTRAP_V012_PASS"
BOOTSTRAP_REVIEW = "B15P1_V011_SOURCE_INVALID_RECOVERY_BOOTSTRAP_V012_REVIEW"


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
        actual_sha = sha256_file(HARNESS)
        checks["harness_sha256"] = actual_sha
        if actual_sha != EXPECTED_HARNESS_SHA256:
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
            timeout=120,
        )
        checks["harness_returncode"] = proc.returncode
        checks["stdout_tail"] = proc.stdout[-8192:]
        checks["stderr_tail"] = proc.stderr[-8192:]
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
            "schema": "sc001.b15.p1_v011_source_invalid_recovery_bootstrap.v0.1.2",
            "status": BOOTSTRAP_PASS,
            "checks": checks,
            "harness_sha256": actual_sha,
            "harness_manifest_sha256": manifest_sha,
            "exchange_calls_performed": False,
            "collector_start_performed": False,
            "next_state": "RECOVERY_V012_OFFLINE_PREFLIGHT_PASS",
        })
        print(BOOTSTRAP_PASS)
        return 0
    except Exception as exc:
        write({
            "schema": "sc001.b15.p1_v011_source_invalid_recovery_bootstrap.v0.1.2",
            "status": BOOTSTRAP_REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "checks": checks,
            "exchange_calls_performed": False,
            "collector_start_performed": False,
        })
        print(BOOTSTRAP_REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
