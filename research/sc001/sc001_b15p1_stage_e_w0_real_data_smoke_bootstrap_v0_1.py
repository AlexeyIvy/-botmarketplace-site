from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "research/sc001/sc001_b15p1_stage_e_pipeline_smoke_v0_1_1.py"
INPUT_ROOT = Path("/work/run/input/b15w0")
OUT = Path("/work/run/output")
ANALYZER_MANIFEST = OUT / "stage_e_pipeline_smoke_manifest.json"
BOOTSTRAP_MANIFEST = OUT / "stage_e_w0_real_data_smoke_bootstrap_manifest.json"

EXPECTED_ANALYZER_SHA256 = "c077503ec29a691fd808cfbf0f7d93b5a7f39137e21b39892efad12f2a2e9df4"
EXPECTED_ANALYZER_PASS = "B15P1_STAGE_E_REAL_DATA_PIPELINE_SMOKE_PASS"
BOOTSTRAP_PASS = "B15P1_STAGE_E_W0_REAL_DATA_SMOKE_BOOTSTRAP_PASS"
BOOTSTRAP_REVIEW = "B15P1_STAGE_E_W0_REAL_DATA_SMOKE_BOOTSTRAP_REVIEW"

REQUIRED_INPUTS = [
    "collector_state.json",
    "collector_manifest.json",
    "polls/2026-09-26.jsonl",
    "fees/bybit/2026-09-26.jsonl",
    "fees/okx/2026-09-26.jsonl",
]


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
    checks: dict = {}
    try:
        analyzer_sha = sha256_file(ANALYZER)
        checks["analyzer_sha256"] = analyzer_sha
        if analyzer_sha != EXPECTED_ANALYZER_SHA256:
            raise RuntimeError("analyzer SHA mismatch")

        source = ANALYZER.read_text(encoding="utf-8")
        compile(source, str(ANALYZER), "exec")
        checks["analyzer_compile"] = True

        input_files: dict[str, dict] = {}
        for rel in REQUIRED_INPUTS:
            p = INPUT_ROOT / rel
            if not p.is_file() or p.is_symlink():
                raise RuntimeError(f"required materialized input missing/invalid: {rel}")
            input_files[rel] = {
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size,
            }
            if p.stat().st_size <= 0:
                raise RuntimeError(f"required materialized input empty: {rel}")
        checks["materialized_inputs"] = input_files

        proc = subprocess.run(
            [
                sys.executable,
                str(ANALYZER),
                "--mode",
                "smoke",
                "--data-root",
                str(INPUT_ROOT),
                "--out-dir",
                str(OUT),
            ],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        checks["analyzer_returncode"] = proc.returncode
        checks["stdout_tail"] = proc.stdout[-12000:]
        checks["stderr_tail"] = proc.stderr[-12000:]

        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")

        if proc.returncode != 0:
            raise RuntimeError(f"real-data smoke analyzer rc={proc.returncode}")
        if EXPECTED_ANALYZER_PASS not in proc.stdout:
            raise RuntimeError("real-data smoke PASS token missing")
        if not ANALYZER_MANIFEST.is_file():
            raise RuntimeError("real-data smoke manifest missing")

        manifest = json.loads(ANALYZER_MANIFEST.read_text(encoding="utf-8"))
        checks["analyzer_manifest_sha256"] = sha256_file(ANALYZER_MANIFEST)
        checks["analyzer_manifest_status"] = manifest.get("status")

        if manifest.get("status") != EXPECTED_ANALYZER_PASS:
            raise RuntimeError("real-data smoke manifest status mismatch")
        for key in (
            "price_data_used",
            "pnl_data_used",
            "opportunity_rate_inference_performed",
            "collector_mutation_performed",
            "network_calls_performed",
        ):
            if manifest.get(key) is not False:
                raise RuntimeError(f"safety boundary mismatch: {key}")

        latest = manifest.get("latest_poll_check") or {}
        if int(latest.get("scheduled_rows") or 0) < 2:
            raise RuntimeError("insufficient scheduled poll rows for W0 smoke")
        if int(latest.get("both_venue_valid_rows") or 0) < 1:
            raise RuntimeError("no fully valid Bybit+OKX poll in W0 snapshot")

        fees = manifest.get("fee_parse") or {}
        if int(fees.get("successful_bybit_instruments") or 0) < 1:
            raise RuntimeError("no successful Bybit fee instrument in W0 snapshot")
        if int(fees.get("successful_okx_instruments") or 0) < 1:
            raise RuntimeError("no successful OKX fee instrument in W0 snapshot")

        write_manifest({
            "schema": "sc001.b15.p1_stage_e_w0_real_data_smoke_bootstrap_result.v0.1",
            "status": BOOTSTRAP_PASS,
            "checks": checks,
            "analyzer_sha256": analyzer_sha,
            "analyzer_manifest_sha256": checks["analyzer_manifest_sha256"],
            "input_snapshot": input_files,
            "price_data_used": False,
            "pnl_data_used": False,
            "opportunity_rate_inference_performed": False,
            "collector_mutation_performed": False,
            "collector_restart_performed": False,
            "network_calls_performed": False,
            "credentials_available": False,
            "next_state": "W0_REAL_DATA_PIPELINE_SMOKE_PASS_WAIT_FOR_W1_COMPLETE_UTC_DAYS",
        })
        print(BOOTSTRAP_PASS)
        return 0
    except Exception as exc:
        write_manifest({
            "schema": "sc001.b15.p1_stage_e_w0_real_data_smoke_bootstrap_result.v0.1",
            "status": BOOTSTRAP_REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "checks": checks,
            "price_data_used": False,
            "pnl_data_used": False,
            "opportunity_rate_inference_performed": False,
            "collector_mutation_performed": False,
            "collector_restart_performed": False,
            "network_calls_performed": False,
            "credentials_available": False,
            "next_state": "STOP_AND_REVIEW_W0_REAL_DATA_PIPELINE_SMOKE",
        })
        print(BOOTSTRAP_REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
