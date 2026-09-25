from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "research/sc001/sc001_b15p1_nonprice_source_capability_revalidation_v0_2_2.py"
OUTPUT = Path("/work/run/output")
COMPILE_MANIFEST = OUTPUT / "capability_revalidation_compile_guard_manifest.json"
SELFTEST_MANIFEST = OUTPUT / "capability_revalidation_self_test_manifest.json"
EXPECTED = "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_V022_SELF_TEST_PASS"


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    checks = {}
    try:
        with tempfile.TemporaryDirectory() as td:
            pyc = Path(td) / "probe.pyc"
            py_compile.compile(str(PROBE), cfile=str(pyc), doraise=True)
            checks["probe_compile"] = bool(pyc.exists())

        source = PROBE.read_text(encoding="utf-8")
        checks["eof_main_guard"] = source.endswith(
            'if __name__ == "__main__":\n    raise SystemExit(main())\n'
        )
        checks["run_mode_present"] = 'choices=("self-test", "run")' in source
        checks["snapshot_contract_present"] = (
            "source_capability_snapshot.json" in source
            and "validate_snapshot_contract" in source
        )
        checks["collector_v014_binding_present"] = (
            "sc001_b15p1_nonprice_transferability_collector_v0_1_4.py" in source
            and "sc001_b15p1_nonprice_transferability_lib_v0_1_4.py" in source
            and "sc001-b15-p1-nonprice-collector-implementation-freeze-v0.1.4.json" in source
            and "sc001-b15p1-transferability-v0.1.4.service" in source
        )
        checks["bybit_v014_parser_proof_present"] = (
            "validate_bybit_collector_v014_parser" in source
            and "parse_bybit_coin_info" in source
            and "withdrawMax_minus_one_semantics" in source
            and "UNLIMITED" in source
        )
        checks["bybit_spot_pagination_guard_scoped"] = (
            "def bybit_spot_no_pagination_static_guard() -> None:" in source
            and "inspect.getsource(bybit_live_usdt_spot_pairs)" in source
        )
        if not all(checks.values()):
            raise RuntimeError("compile/static completeness guard failed")

        proc = subprocess.run(
            [sys.executable, str(PROBE), "--mode", "self-test"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)

        selftest = None
        if SELFTEST_MANIFEST.exists():
            selftest = json.loads(
                SELFTEST_MANIFEST.read_text(encoding="utf-8")
            )

        passed = (
            proc.returncode == 0
            and EXPECTED in proc.stdout
            and isinstance(selftest, dict)
            and selftest.get("status") == EXPECTED
            and selftest.get("exchange_calls_performed") is False
            and selftest.get("credentials_required") is False
            and selftest.get("output_snapshot_written") is False
            and selftest.get("price_data_used") is False
            and selftest.get("collector_launch_authorized") is False
        )
        if not passed:
            raise RuntimeError(
                f"capability offline self-test contract failed rc={proc.returncode}"
            )

        write_json(
            COMPILE_MANIFEST,
            {
                "schema": "sc001.b15.p1_nonprice_source_capability_compile_guard.v0.2.2",
                "status": "B15P1_NONPRICE_SOURCE_CAPABILITY_V022_COMPILE_AND_SELFTEST_PASS",
                "checks": checks,
                "probe_returncode": proc.returncode,
                "expected_token": EXPECTED,
                "selftest_manifest_present": True,
                "exchange_calls_performed": False,
                "credentials_required": False,
                "collector_launch_authorized": False,
                "price_data_used": False,
            },
        )
        print("B15P1_NONPRICE_SOURCE_CAPABILITY_V022_COMPILE_AND_SELFTEST_PASS")
        return 0

    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        write_json(
            COMPILE_MANIFEST,
            {
                "schema": "sc001.b15.p1_nonprice_source_capability_compile_guard.v0.2.2",
                "status": "B15P1_NONPRICE_SOURCE_CAPABILITY_V022_COMPILE_OR_SELFTEST_REVIEW",
                "checks": checks,
                "error": err,
                "exchange_calls_performed": False,
                "credentials_required": False,
                "collector_launch_authorized": False,
                "price_data_used": False,
            },
        )
        print("B15P1_NONPRICE_SOURCE_CAPABILITY_V022_COMPILE_OR_SELFTEST_REVIEW")
        print("error =", err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
