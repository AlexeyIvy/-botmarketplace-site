from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_2.py"
LIBRARY = ROOT / "research/sc001/sc001_b15p1_nonprice_transferability_lib_v0_1_2.py"
OUTPUT = Path("/work/run/output")
COMPILE_MANIFEST = OUTPUT / "implementation_compile_guard_manifest.json"
SELFTEST_MANIFEST = OUTPUT / "implementation_self_test_manifest.json"
EXPECTED_TOKEN = "B15P1_NONPRICE_COLLECTOR_V012_SELF_TEST_PASS"


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    compile_checks = {}
    error = None
    try:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            for label, path in (("runner", RUNNER), ("library", LIBRARY)):
                target = td_path / f"{label}.pyc"
                py_compile.compile(
                    str(path),
                    cfile=str(target),
                    doraise=True,
                )
                compile_checks[label] = {
                    "source": str(path.relative_to(ROOT)),
                    "compiled": True,
                    "pyc_created": target.exists(),
                }

        runner_text = RUNNER.read_text(encoding="utf-8")
        compile_checks["runner_eof_guard"] = {
            "passed": runner_text.endswith(
                'if __name__ == "__main__":\n    raise SystemExit(main())\n'
            ),
        }
        compile_checks["runner_main_guard"] = {
            "passed": "def main() -> int:" in runner_text
            and '"ambiguous_row_count": len(ambiguous_rows)' in runner_text,
        }

        if not all(
            x.get("compiled", x.get("passed", False))
            for x in compile_checks.values()
        ):
            raise RuntimeError("compile/EOF guard failed")

        env = dict(os.environ)
        env["B15P1_SELFTEST_OUTPUT"] = str(SELFTEST_MANIFEST)
        proc = subprocess.run(
            [sys.executable, str(RUNNER), "--mode", "self-test"],
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )

        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)

        selftest_obj = None
        if SELFTEST_MANIFEST.exists():
            selftest_obj = json.loads(
                SELFTEST_MANIFEST.read_text(encoding="utf-8")
            )

        pass_ok = (
            proc.returncode == 0
            and EXPECTED_TOKEN in proc.stdout
            and isinstance(selftest_obj, dict)
            and selftest_obj.get("status") == EXPECTED_TOKEN
            and selftest_obj.get("exchange_calls_performed") is False
            and selftest_obj.get("collector_launch_authorized") is False
            and selftest_obj.get("price_data_authorized") is False
        )
        if not pass_ok:
            raise RuntimeError(
                f"collector self-test contract failed rc={proc.returncode}"
            )

        write_json(
            COMPILE_MANIFEST,
            {
                "schema": "sc001.b15.p1_nonprice_collector_compile_guard.v0.1.2",
                "status": "B15P1_NONPRICE_COLLECTOR_V012_COMPILE_AND_SELFTEST_PASS",
                "compile_checks": compile_checks,
                "collector_returncode": proc.returncode,
                "expected_token": EXPECTED_TOKEN,
                "selftest_manifest_present": True,
                "exchange_calls_performed": False,
                "collector_launch_authorized": False,
                "price_data_authorized": False,
            },
        )
        print("B15P1_NONPRICE_COLLECTOR_V012_COMPILE_AND_SELFTEST_PASS")
        return 0

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        write_json(
            COMPILE_MANIFEST,
            {
                "schema": "sc001.b15.p1_nonprice_collector_compile_guard.v0.1.2",
                "status": "B15P1_NONPRICE_COLLECTOR_V012_COMPILE_OR_SELFTEST_REVIEW",
                "compile_checks": compile_checks,
                "error": error,
                "exchange_calls_performed": False,
                "collector_launch_authorized": False,
                "price_data_authorized": False,
            },
        )
        print("B15P1_NONPRICE_COLLECTOR_V012_COMPILE_OR_SELFTEST_REVIEW")
        print("error =", error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
