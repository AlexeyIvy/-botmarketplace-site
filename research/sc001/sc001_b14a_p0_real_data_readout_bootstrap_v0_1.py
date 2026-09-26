from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "research/sc001/sc001_b14a_p0_headroom_readout_v0_1.py"
INPUT_ROOT = Path("/work/run/input/b14ap0")
OUT = Path("/work/run/output")
READOUT_MANIFEST = OUT / "b14a_p0_headroom_readout_manifest.json"
BOOTSTRAP_MANIFEST = OUT / "b14a_p0_real_data_readout_bootstrap_manifest.json"

EXPECTED_ANALYZER_SHA256 = "919c0d75e3459c0039f63915fd55347eb09590d22b29a10d4070bdcad5622279"
ALLOWED_STATUSES = {
    "B14A_P0_STRONG_HEADROOM_2_OF_2",
    "B14A_P0_MIXED_HEADROOM_1_OF_2",
    "B14A_P0_WEAK_HEADROOM_0_OF_2",
    "B14A_P0_DEFER_DATA",
}
BOOTSTRAP_PASS = "B14A_P0_REAL_DATA_READOUT_BOOTSTRAP_PASS"
BOOTSTRAP_REVIEW = "B14A_P0_REAL_DATA_READOUT_BOOTSTRAP_REVIEW"

REQUIRED_INPUTS = [
    "collector_state.json",
    "raw_trades.jsonl",
    "connection_events.jsonl",
]


def sha256_file(path: Path) -> str:
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
    checks: dict = {}
    try:
        actual = sha256_file(ANALYZER)
        checks["analyzer_sha256"] = actual
        if actual != EXPECTED_ANALYZER_SHA256:
            raise RuntimeError("analyzer SHA mismatch")
        compile(ANALYZER.read_text(encoding="utf-8"), str(ANALYZER), "exec")
        checks["analyzer_compile"] = True

        materialized = {}
        for rel in REQUIRED_INPUTS:
            p = INPUT_ROOT / rel
            if not p.is_file() or p.is_symlink():
                raise RuntimeError(f"required materialized input missing/invalid: {rel}")
            if p.stat().st_size <= 0:
                raise RuntimeError(f"required materialized input empty: {rel}")
            materialized[rel] = {
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size,
            }
        checks["materialized_inputs"] = materialized

        proc = subprocess.run(
            [
                sys.executable,
                str(ANALYZER),
                "--mode",
                "readout",
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
            raise RuntimeError(f"B14-A real-data readout rc={proc.returncode}")
        if not READOUT_MANIFEST.is_file():
            raise RuntimeError("B14-A readout manifest missing")

        manifest = json.loads(READOUT_MANIFEST.read_text(encoding="utf-8"))
        status = manifest.get("status")
        checks["readout_manifest_sha256"] = sha256_file(READOUT_MANIFEST)
        checks["readout_status"] = status
        if status not in ALLOWED_STATUSES:
            raise RuntimeError(f"unexpected B14-A P0 status: {status}")

        for key in (
            "convergence_calculated",
            "settlement_price_analyzed",
            "execution_model_calculated",
            "pnl_calculated",
            "candidate_id_assigned",
            "promotional_claim_made",
        ):
            if manifest.get(key) is not False:
                raise RuntimeError(f"firewall mismatch: {key}")

        write({
            "schema": "sc001.b14a_p0_real_data_readout_bootstrap_result.v0.1",
            "status": BOOTSTRAP_PASS,
            "p0_classification": status,
            "checks": checks,
            "input_snapshot": materialized,
            "readout_manifest_sha256": checks["readout_manifest_sha256"],
            "network_calls_performed": False,
            "credentials_available": False,
            "collector_mutation_performed": False,
            "collector_restart_performed": False,
            "alternative_window_search_performed": False,
            "alternative_expiry_search_performed": False,
            "threshold_tuning_performed": False,
            "convergence_calculated": False,
            "settlement_price_analyzed": False,
            "execution_model_calculated": False,
            "pnl_calculated": False,
            "next_state": "REVIEW_FROZEN_B14A_P0_CLASSIFICATION_AND_FOLLOW_PROTOCOL_CONSEQUENCE",
        })
        print(BOOTSTRAP_PASS)
        return 0

    except Exception as exc:
        write({
            "schema": "sc001.b14a_p0_real_data_readout_bootstrap_result.v0.1",
            "status": BOOTSTRAP_REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "checks": checks,
            "network_calls_performed": False,
            "credentials_available": False,
            "collector_mutation_performed": False,
            "collector_restart_performed": False,
            "alternative_window_search_performed": False,
            "alternative_expiry_search_performed": False,
            "threshold_tuning_performed": False,
            "convergence_calculated": False,
            "settlement_price_analyzed": False,
            "execution_model_calculated": False,
            "pnl_calculated": False,
            "next_state": "STOP_AND_REVIEW_B14A_P0_REAL_DATA_READOUT",
        })
        print(BOOTSTRAP_REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
