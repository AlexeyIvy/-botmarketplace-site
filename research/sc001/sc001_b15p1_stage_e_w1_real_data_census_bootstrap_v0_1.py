from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "research/sc001/sc001_b15p1_stage_e_w1_input_census_v0_1.py"
INPUT_ROOT = Path("/work/run/input/b15w1")
OUT = Path("/work/run/output")
CENSUS_MANIFEST = OUT / "stage_e_w1_input_census_manifest.json"
BOOTSTRAP_MANIFEST = OUT / "stage_e_w1_real_data_census_bootstrap_manifest.json"

EXPECTED_CENSUS_SHA256 = "5386182a73eb6e0561eb3670223168d3e1ebe7d11640ee9d67ce753569de4aaf"
NOT_BEFORE = datetime(2026, 10, 4, 0, 0, 0, tzinfo=timezone.utc)
EXPECTED_PASS = "B15P1_STAGE_E_W1_INPUT_CENSUS_PASS"
BOOTSTRAP_PASS = "B15P1_STAGE_E_W1_REAL_DATA_CENSUS_BOOTSTRAP_PASS"
BOOTSTRAP_REVIEW = "B15P1_STAGE_E_W1_REAL_DATA_CENSUS_BOOTSTRAP_REVIEW"

DAYS = ["2026-09-27","2026-09-28","2026-09-29","2026-09-30","2026-10-01","2026-10-02","2026-10-03"]
REQUIRED = [
    "collector_state.json",
    "collector_manifest.json",
    "daily_manifests/2026-09-26.json",
    *[f"daily_manifests/{d}.json" for d in DAYS],
    *[f"polls/{d}.jsonl" for d in DAYS],
]


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write(obj: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    BOOTSTRAP_MANIFEST.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    checks = {}
    try:
        now = datetime.now(timezone.utc)
        checks["runner_now_utc"] = now.isoformat()
        checks["not_before_utc"] = NOT_BEFORE.isoformat()
        if now < NOT_BEFORE:
            raise RuntimeError("W1 window not complete yet")

        actual = sha256_file(CENSUS)
        checks["census_sha256"] = actual
        if actual != EXPECTED_CENSUS_SHA256:
            raise RuntimeError("census SHA mismatch")
        compile(CENSUS.read_text(encoding="utf-8"), str(CENSUS), "exec")
        checks["census_compile"] = True

        materialized = {}
        for rel in REQUIRED:
            p = INPUT_ROOT / rel
            if not p.is_file() or p.is_symlink():
                raise RuntimeError(f"required W1 input missing/invalid: {rel}")
            if p.stat().st_size <= 0:
                raise RuntimeError(f"required W1 input empty: {rel}")
            materialized[rel] = {
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size,
            }
        checks["materialized_inputs"] = materialized

        proc = subprocess.run(
            [
                sys.executable, str(CENSUS),
                "--mode", "census",
                "--data-root", str(INPUT_ROOT),
                "--out-dir", str(OUT),
            ],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
        )
        checks["census_returncode"] = proc.returncode
        checks["stdout_tail"] = proc.stdout[-12000:]
        checks["stderr_tail"] = proc.stderr[-12000:]
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")

        if proc.returncode != 0:
            raise RuntimeError(f"W1 census rc={proc.returncode}")
        if EXPECTED_PASS not in proc.stdout:
            raise RuntimeError("W1 census PASS token missing")
        if not CENSUS_MANIFEST.is_file():
            raise RuntimeError("W1 census manifest missing")

        manifest = json.loads(CENSUS_MANIFEST.read_text(encoding="utf-8"))
        checks["census_manifest_sha256"] = sha256_file(CENSUS_MANIFEST)
        checks["census_manifest_status"] = manifest.get("status")
        if manifest.get("status") != EXPECTED_PASS:
            raise RuntimeError("W1 census manifest PASS mismatch")
        if manifest.get("opportunity_rate_inference_performed") is not False:
            raise RuntimeError("W1 census opportunity-rate boundary mismatch")
        if manifest.get("price_data_used") is not False or manifest.get("pnl_data_used") is not False:
            raise RuntimeError("W1 census price/PnL boundary mismatch")
        if (manifest.get("quality") or {}).get("quality_pass") is not True:
            raise RuntimeError("W1 data-quality gate not PASS")

        write({
            "schema":"sc001.b15.p1_stage_e_w1_real_data_census_bootstrap_result.v0.1",
            "status":BOOTSTRAP_PASS,
            "checks":checks,
            "census_manifest_sha256":checks["census_manifest_sha256"],
            "input_snapshot":materialized,
            "price_data_used":False,
            "pnl_data_used":False,
            "opportunity_rate_inference_performed":False,
            "collector_mutation_performed":False,
            "collector_restart_performed":False,
            "network_calls_performed":False,
            "credentials_available":False,
            "next_state":"BUILD_EXACT_W1_SOURCE_ONLY_ANALYSIS_BUNDLE_FROM_CENSUS_MANIFEST",
        })
        print(BOOTSTRAP_PASS)
        return 0
    except Exception as exc:
        write({
            "schema":"sc001.b15.p1_stage_e_w1_real_data_census_bootstrap_result.v0.1",
            "status":BOOTSTRAP_REVIEW,
            "error":f"{type(exc).__name__}: {exc}",
            "checks":checks,
            "price_data_used":False,
            "pnl_data_used":False,
            "opportunity_rate_inference_performed":False,
            "collector_mutation_performed":False,
            "collector_restart_performed":False,
            "network_calls_performed":False,
            "credentials_available":False,
            "next_state":"STOP_AND_REVIEW_W1_REAL_DATA_CENSUS",
        })
        print(BOOTSTRAP_REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
