from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/work/run/output")
MANIFEST = OUT / "v011_source_invalid_recovery_before_v014_offline_preflight_v012_manifest.json"

WRAPPER = ROOT / "scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.2.sh"
SPEC = ROOT / "docs/research/sc001-b15-p1-v011-source-invalid-recovery-before-v014-preflight-spec-v0.1.2.json"
FREEZE = ROOT / "docs/research/sc001-b15-p1-v011-source-invalid-recovery-before-v014-preflight-freeze-v0.1.2.json"
DIAGNOSTIC = ROOT / "docs/research/sc001-b15-p1-v011-source-invalid-recovery-v0.1.1-host-failure-diagnostic-v0.1.json"
PASS = "B15P1_V011_SOURCE_INVALID_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_V012_PASS"
REVIEW = "B15P1_V011_SOURCE_INVALID_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_V012_REVIEW"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(obj: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def extract_heredocs(text: str) -> list[str]:
    return re.findall(r"<<'PY'\n(.*?)\nPY(?:\n|$)", text, re.S)


def run_snapshot_validator(block: str, generated_utc: str, *, corrupt_safe_sha: bool = False, omit_probe_pass: bool = False) -> subprocess.CompletedProcess[str]:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    anchors = spec["expected_v014_anchors"]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        snapshot = {
            "schema": "sc001.b15.p1_nonprice_source_capability_snapshot.v0.2.2",
            "status": "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS",
            "generated_utc": generated_utc,
            "anchors": {
                "runner_sha256": anchors["runner_sha256"],
                "library_sha256": anchors["library_sha256"],
                "implementation_freeze_sha256": anchors["implementation_freeze_sha256"],
                "service_file_sha256": anchors["service_sha256"],
                "route_graph_sha256": anchors["route_graph_sha256"],
                "admitted_universe_sha256": anchors["admitted_sha256"],
                "capability_probe_sha256": anchors["capability_probe_sha256"],
                "capability_freeze_sha256": anchors["capability_freeze_sha256"],
            },
            "permissions": {
                "bybit_readOnly": 1,
                "bybit_withdraw_token_present": False,
                "bybit_ip_bound": True,
                "okx_permission": "read_only",
                "okx_ip_bound": True,
            },
            "source_endpoints_pass": True,
            "bybit_adapter": {
                "collector_parser_version": "0.1.4",
                "parser_compatible": True,
                "withdrawMax_minus_one_semantics": "UNLIMITED",
                "raw_withdrawMax_minus_one_rows": 1007,
                "normalized_unlimited_rows": 1007,
            },
            "pair_coverage": {
                "frozen_admitted_assets": 192,
                "qualified_bybit_count": 192,
                "qualified_okx_count": 192,
                "both_venues_count": 192,
                "missing_bybit_assets": [],
                "missing_okx_assets": [],
            },
            "fee_endpoint_probe": {"asset": "BTC", "pass": True},
            "security": {
                "secret_values_printed": False,
                "price_endpoints_called": False,
                "order_endpoints_called": False,
                "transfer_endpoints_called": False,
                "withdrawal_endpoints_called": False,
            },
            "price_data_used": False,
            "pnl_data_used": False,
            "collector_launch_authorized": False,
            "live_execution_authorized": False,
        }
        snap_path = root / "source_capability_snapshot.json"
        snap_path.write_text(json.dumps(snapshot, sort_keys=True) + "\n", encoding="utf-8")
        snap_sha = sha256_file(snap_path)

        safe = {
            "schema": "sc001.b15.p1_nonprice_source_capability_safe_summary.v0.2.2",
            "status": "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS",
            "snapshot_sha256": ("0" * 64 if corrupt_safe_sha else snap_sha),
            "bybit_adapter": snapshot["bybit_adapter"],
            "pair_coverage": {
                "frozen_admitted_assets": 192,
                "qualified_bybit_count": 192,
                "qualified_okx_count": 192,
                "both_venues_count": 192,
            },
            "source_endpoints_pass": True,
            "collector_launch_authorized": False,
            "price_data_used": False,
        }
        safe_path = root / "source_capability_safe_summary.json"
        safe_path.write_text(json.dumps(safe, sort_keys=True) + "\n", encoding="utf-8")

        log_path = root / "source_capability_revalidation_v0.2.2_run.log"
        probe_lines = [
            "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS",
            "snapshot_path = /fixture/source_capability_snapshot.json",
            f"snapshot_sha256 = {snap_sha}",
            "Bybit readOnly = 1",
            "Bybit Withdraw token present = False",
            "Bybit IP bound = True",
            "OKX permission = read_only",
            "OKX IP bound = True",
            "Bybit source chain rows = 1036",
            "Bybit parser v0.1.4 compatible = True",
            "Bybit withdrawMax -1 rows = 1007",
            "Bybit normalized UNLIMITED rows = 1007",
            "OKX source chain rows = 591",
            "qualified Bybit USDT pairs = 192",
            "qualified OKX USDT pairs = 192",
            "qualified both-venue assets = 192",
            "fee probe asset = BTC",
            "price endpoints called = False",
            "order/transfer/withdraw endpoints called = False",
            "collector_launch_authorized = False",
        ]
        if omit_probe_pass:
            probe_lines = [
                line for line in probe_lines
                if line != "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS"
            ]
        log_path.write_text("\n".join(probe_lines) + "\n", encoding="utf-8")

        args = [
            sys.executable, "-c", block,
            str(snap_path), str(safe_path), str(log_path), snap_sha,
            anchors["runner_sha256"], anchors["library_sha256"],
            anchors["implementation_freeze_sha256"], anchors["service_sha256"],
            anchors["route_graph_sha256"], anchors["admitted_sha256"],
            anchors["capability_probe_sha256"], anchors["capability_freeze_sha256"],
        ]
        return subprocess.run(args, text=True, capture_output=True, check=False, timeout=10)


def main() -> int:
    checks: dict = {}
    try:
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
        text = WRAPPER.read_text(encoding="utf-8")
        actual_wrapper_sha = sha256_file(WRAPPER)

        if freeze.get("status") != "FROZEN_BEFORE_OFFLINE_PREFLIGHT":
            raise RuntimeError("freeze status mismatch")
        current_harness_sha = sha256_file(Path(__file__).resolve())
        if freeze.get("wrapper_sha256") != actual_wrapper_sha:
            raise RuntimeError("freeze wrapper SHA mismatch")
        if freeze.get("harness_sha256") != current_harness_sha:
            raise RuntimeError("freeze harness SHA mismatch")
        if freeze.get("spec_sha256") != sha256_file(SPEC):
            raise RuntimeError("freeze spec SHA mismatch")
        if freeze.get("failure_diagnostic_sha256") != sha256_file(DIAGNOSTIC):
            raise RuntimeError("freeze diagnostic SHA mismatch")

        bootstrap_spec = spec.get("bootstrap") or {}
        bootstrap_path = ROOT / str(bootstrap_spec.get("path") or "")
        if not bootstrap_path.is_file():
            raise RuntimeError("bootstrap path missing")
        bootstrap_sha = sha256_file(bootstrap_path)
        if bootstrap_spec.get("sha256") != bootstrap_sha:
            raise RuntimeError("spec bootstrap SHA mismatch")
        if freeze.get("bootstrap_sha256") != bootstrap_sha:
            raise RuntimeError("freeze bootstrap SHA mismatch")

        checks["freeze_chain_pass"] = True
        if spec["wrapper"]["sha256"] != actual_wrapper_sha:
            raise RuntimeError("wrapper sha mismatch")

        bash = shutil.which("bash")
        if not bash:
            raise RuntimeError("bash unavailable")
        syntax = subprocess.run([bash, "-n", str(WRAPPER)], text=True, capture_output=True, check=False, timeout=10)
        checks["bash_syntax_returncode"] = syntax.returncode
        if syntax.returncode != 0:
            raise RuntimeError(syntax.stderr or syntax.stdout)

        blocks = extract_heredocs(text)
        expected_blocks = int(spec["expected_embedded_python_block_count"])
        if len(blocks) != expected_blocks:
            raise RuntimeError(f"embedded python count={len(blocks)} expected={expected_blocks}")
        for idx, block in enumerate(blocks, 1):
            compile(block, f"<recovery-v011-heredoc-{idx}>", "exec")
        checks["embedded_python_block_count"] = len(blocks)
        checks["embedded_python_compile"] = True

        if "EXPECTED_SNAPSHOT_SHA=" in text:
            raise RuntimeError("hardcoded snapshot SHA remains in v0.1.2 recovery")
        if "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_V022_PASS" in text:
            raise RuntimeError("wrapper-level COMMAND_V022_PASS incorrectly required in probe tee log")
        if 'assert "security_firewall = PASS" in cap_log' in text:
            raise RuntimeError("wrapper-level security_firewall token incorrectly required in probe tee log")
        for stale in (
            "fc1b4537290451241596e67342a9ab8fa6acd827afd4aeb70b70cee1e24e8e47",
            "01cfa63b6001ec972c4ed87daba5bbd9fba932233b9e8323a49a6a5355e89647",
        ):
            if stale in text:
                raise RuntimeError("specific live snapshot SHA leaked into recovery wrapper")

        semantic_blocks = [b for b in blocks if "v022_snapshot_semantic_contract = PASS" in b]
        if len(semantic_blocks) != 1:
            raise RuntimeError(f"semantic validator block count={len(semantic_blocks)}")
        semantic = semantic_blocks[0]

        first = run_snapshot_validator(semantic, "2026-09-26T09:00:00Z")
        second = run_snapshot_validator(semantic, "2026-09-26T09:01:00Z")
        bad = run_snapshot_validator(semantic, "2026-09-26T09:02:00Z", corrupt_safe_sha=True)
        missing_probe_pass = run_snapshot_validator(
            semantic,
            "2026-09-26T09:03:00Z",
            omit_probe_pass=True,
        )
        if first.returncode != 0 or "v022_snapshot_semantic_contract = PASS" not in first.stdout:
            raise RuntimeError(f"semantic fixture A failed rc={first.returncode} out={first.stdout!r} err={first.stderr!r}")
        if second.returncode != 0 or "v022_snapshot_semantic_contract = PASS" not in second.stdout:
            raise RuntimeError(f"semantic fixture B failed rc={second.returncode} out={second.stdout!r} err={second.stderr!r}")
        if bad.returncode == 0:
            raise RuntimeError("semantic validator accepted mismatched safe-summary snapshot SHA")
        if missing_probe_pass.returncode == 0:
            raise RuntimeError("semantic validator accepted log without probe PASS token")
        checks["dynamic_snapshot_sha_fixture_a_pass"] = True
        checks["dynamic_snapshot_sha_fixture_b_pass"] = True
        checks["safe_summary_sha_mismatch_fail_closed"] = True
        checks["realistic_probe_log_fixture_pass"] = True
        checks["missing_probe_pass_token_fail_closed"] = True

        cmds: list[str] = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#") or s.startswith("for cmd in "):
                continue
            cmds.extend(re.findall(r"\bsystemctl\s+([A-Za-z-]+)", line))
        allowed = set(spec["allowed_systemctl_subcommands"])
        if any(c not in allowed for c in cmds):
            raise RuntimeError(f"disallowed systemctl commands: {cmds}")
        checks["systemctl_subcommands"] = cmds

        forbidden = {
            "start": bool(re.search(r"systemctl\s+start", text)),
            "enable": bool(re.search(r"systemctl\s+enable", text)),
            "restart": bool(re.search(r"systemctl\s+restart", text)),
            "collector_run": "--mode run" in text,
            "snapshot_move": bool(re.search(r"mv\s+[^\n]*\$SNAPSHOT", text)),
            "snapshot_delete": bool(re.search(r"rm\s+[^\n]*\$SNAPSHOT", text)),
            "safe_summary_move": bool(re.search(r"mv\s+[^\n]*\$SAFE_SUMMARY", text)),
            "cap_log_move": bool(re.search(r"mv\s+[^\n]*\$CAP_LOG", text)),
        }
        if any(forbidden.values()):
            raise RuntimeError(f"forbidden behavior: {forbidden}")
        checks["forbidden_behavior_hits"] = forbidden

        required = [
            'flock -n 9',
            'snapshot_before="$(sha256sum "$SNAPSHOT"',
            '[[ "$snapshot_after" == "$snapshot_before" ]]',
            'v022_snapshot_semantic_contract = PASS',
            'collector_parser_version") == "0.1.4"',
            'raw_minus_one == normalized',
            'qualified_bybit_count") == 192',
            'qualified_okx_count") == 192',
            'both_venues_count") == 192',
            'B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS',
            'assert "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_REVIEW" not in cap_log',
            'Bybit parser v0.1.4 compatible = True',
            'price endpoints called = False',
            'order/transfer/withdraw endpoints called = False',
            'collector_launch_authorized = False',
            '"$OUT_DIR/raw_objects"', '"$OUT_DIR/polls"', '"$OUT_DIR/normalized"',
            '"$OUT_DIR/events"', '"$OUT_DIR/gaps"', '"$OUT_DIR/fees"',
            '"$OUT_DIR/invalid"', '"$OUT_DIR/daily_manifests"',
            'B15P1_V011_SOURCE_INVALID_RECOVERY_V012_PASS',
        ]
        missing = [m for m in required if m not in text]
        if missing:
            raise RuntimeError(f"missing required markers: {missing}")
        checks["required_marker_count"] = len(required)

        write({
            "schema": "sc001.b15.p1_v011_source_invalid_recovery_before_v014_offline_preflight.v0.1.2",
            "status": PASS,
            "wrapper_sha256": actual_wrapper_sha,
            "checks": checks,
            "exchange_calls_performed": False,
            "collector_start_performed": False,
            "systemd_start_enable_performed": False,
            "price_pnl_used": False,
            "next_state": "RUN_V011_SOURCE_INVALID_RECOVERY_V012_ON_VPS",
        })
        print(PASS)
        print("dynamic_snapshot_and_probe_log_fixtures = PASS")
        print("collector_start_performed = False")
        return 0
    except Exception as exc:
        write({
            "schema": "sc001.b15.p1_v011_source_invalid_recovery_before_v014_offline_preflight.v0.1.2",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "checks": checks,
            "exchange_calls_performed": False,
            "collector_start_performed": False,
        })
        print(REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
