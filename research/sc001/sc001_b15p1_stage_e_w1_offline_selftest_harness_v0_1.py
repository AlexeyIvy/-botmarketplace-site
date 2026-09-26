from __future__ import annotations

import hashlib
import json
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "research/sc001/sc001_b15p1_stage_e_w1_input_census_v0_1.py"
ANALYZER = ROOT / "research/sc001/sc001_b15p1_stage_e_w1_source_only_analyzer_v0_1.py"
OUT = Path("/work/run/output")
MANIFEST = OUT / "stage_e_w1_offline_selftest_manifest.json"

EXPECTED_CENSUS_SHA = "5386182a73eb6e0561eb3670223168d3e1ebe7d11640ee9d67ce753569de4aaf"
EXPECTED_ANALYZER_SHA = "da4a218e7b624775e44e8403a1acf6ee1bff581ec1a7ddaa59eb42fd0f2330ce"
CENSUS_TOKEN = "B15P1_STAGE_E_W1_INPUT_CENSUS_V01_SELF_TEST_PASS"
ANALYZER_TOKEN = "B15P1_STAGE_E_W1_SOURCE_ONLY_ANALYZER_V01_SELF_TEST_PASS"
PASS = "B15P1_STAGE_E_W1_OFFLINE_SELFTEST_PASS"
REVIEW = "B15P1_STAGE_E_W1_OFFLINE_SELFTEST_REVIEW"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(obj: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(path: Path, token: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(path), "--mode", "self-test"],
        cwd=str(ROOT), text=True, capture_output=True, check=False, timeout=120,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    if proc.returncode != 0 or token not in proc.stdout:
        raise RuntimeError(f"self-test failed path={path.name} rc={proc.returncode}")
    return {"returncode": proc.returncode, "stdout_tail": proc.stdout[-4000:], "stderr_tail": proc.stderr[-4000:]}


def main() -> int:
    checks = {}
    try:
        if sha(CENSUS) != EXPECTED_CENSUS_SHA:
            raise RuntimeError("census SHA mismatch")
        if sha(ANALYZER) != EXPECTED_ANALYZER_SHA:
            raise RuntimeError("analyzer SHA mismatch")
        checks["census_sha256"] = EXPECTED_CENSUS_SHA
        checks["analyzer_sha256"] = EXPECTED_ANALYZER_SHA
        with tempfile.TemporaryDirectory() as td:
            for label, path in (("census", CENSUS), ("analyzer", ANALYZER)):
                pyc = Path(td) / f"{label}.pyc"
                py_compile.compile(str(path), cfile=str(pyc), doraise=True)
                if not pyc.is_file():
                    raise RuntimeError(f"py_compile output missing: {label}")
                checks[f"{label}_compile"] = True
        checks["census_selftest"] = run(CENSUS, CENSUS_TOKEN)
        checks["analyzer_selftest"] = run(ANALYZER, ANALYZER_TOKEN)
        write({
            "schema":"sc001.b15.p1_stage_e_w1_offline_selftest_result.v0.1",
            "status":PASS,
            "checks":checks,
            "window_days":["2026-09-27","2026-09-28","2026-09-29","2026-09-30","2026-10-01","2026-10-02","2026-10-03"],
            "price_data_used":False,"pnl_data_used":False,
            "opportunity_rate_inference_performed":False,
            "network_calls_performed":False,"credentials_available":False,
            "collector_mutation_performed":False,"collector_restart_performed":False,
            "next_state":"PREPARE_W1_INPUT_CENSUS_REAL_DATA_BUNDLE_FOR_AFTER_2026_10_04T00_00Z",
        })
        print(PASS)
        return 0
    except Exception as exc:
        write({
            "schema":"sc001.b15.p1_stage_e_w1_offline_selftest_result.v0.1",
            "status":REVIEW,"error":f"{type(exc).__name__}: {exc}","checks":checks,
            "price_data_used":False,"pnl_data_used":False,
            "opportunity_rate_inference_performed":False,
            "network_calls_performed":False,"credentials_available":False,
            "collector_mutation_performed":False,"collector_restart_performed":False,
            "next_state":"STOP_AND_REVIEW_W1_OFFLINE_SELFTEST",
        })
        print(REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
