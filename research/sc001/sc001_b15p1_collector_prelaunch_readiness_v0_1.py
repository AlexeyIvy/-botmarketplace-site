from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("/work/run/output")
MANIFEST = OUT / "collector_prelaunch_readiness_manifest.json"

SPEC = ROOT / "docs/research/sc001-b15-p1-collector-prelaunch-readiness-spec-v0.1.json"
FREEZE = ROOT / "docs/research/sc001-b15-p1-collector-prelaunch-readiness-freeze-v0.1.json"
CANDIDATE = ROOT / "docs/research/sc001-b15-p1-collector-launch-authorization-candidate-v0.1.json"
LIVE_RESULT = ROOT / "docs/research/sc001-b15-p1-live-source-capability-revalidation-v0.2.1-result-v0.1.json"
COMBINED_RESULT = ROOT / "docs/research/sc001-b15-p1-adapter-combined-offline-validation-result-v0.1.1.json"
WRAPPER_PREFLIGHT_RESULT = ROOT / "docs/research/sc001-b15-p1-source-capability-live-wrapper-v0.2-offline-preflight-result-v0.1.json"

COLLECTOR = ROOT / "research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_3.py"
LIBRARY = ROOT / "research/sc001/sc001_b15p1_nonprice_transferability_lib_v0_1_3.py"
IMPLEMENTATION_FREEZE = ROOT / "docs/research/sc001-b15-p1-nonprice-collector-implementation-freeze-v0.1.3.json"
CONTRACT = ROOT / "docs/research/sc001-b15-p1-nonprice-collector-implementation-contract-v0.1.3.json"
PROTOCOL = ROOT / "docs/research/sc001-b15-p1-15-second-nonprice-collector-protocol-v0.1.md"
SERVICE = ROOT / "ops/systemd/sc001-b15p1-transferability-v0.1.3.service"
STATUS_HELPER = ROOT / "ops/systemd/sc001_b15p1_transferability_status.sh"

PASS = "B15P1_COLLECTOR_PRELAUNCH_READINESS_OFFLINE_PASS"
REVIEW = "B15P1_COLLECTOR_PRELAUNCH_READINESS_OFFLINE_REVIEW"

EXPECTED_SNAPSHOT_SHA = "14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc"


class PrelaunchError(RuntimeError):
    pass


def fail(msg: str) -> None:
    raise PrelaunchError(msg)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def write_manifest(obj: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def require_prelaunch_freeze() -> dict[str, Any]:
    fr = load_object(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_B15P1_COLLECTOR_PRELAUNCH_READINESS_OFFLINE":
        fail("prelaunch freeze status mismatch")

    expected = {
        "harness_sha256": sha256_file(Path(__file__).resolve()),
        "spec_sha256": sha256_file(SPEC),
        "launch_candidate_sha256": sha256_file(CANDIDATE),
        "live_result_sha256": sha256_file(LIVE_RESULT),
        "combined_result_sha256": sha256_file(COMBINED_RESULT),
        "wrapper_preflight_result_sha256": sha256_file(WRAPPER_PREFLIGHT_RESULT),
        "collector_runner_sha256": sha256_file(COLLECTOR),
        "collector_library_sha256": sha256_file(LIBRARY),
        "implementation_freeze_sha256": sha256_file(IMPLEMENTATION_FREEZE),
        "contract_sha256": sha256_file(CONTRACT),
        "protocol_sha256": sha256_file(PROTOCOL),
        "service_candidate_sha256": sha256_file(SERVICE),
        "status_helper_sha256": sha256_file(STATUS_HELPER),
    }
    for key, actual in expected.items():
        if fr.get(key) != actual:
            fail(f"prelaunch freeze hash mismatch {key}: expected={fr.get(key)} actual={actual}")

    for key in (
        "credentials_available",
        "exchange_calls_allowed",
        "collector_start_allowed",
        "systemd_mutation_allowed",
        "runtime_authorization_creation_allowed",
        "price_data_allowed",
        "pnl_data_allowed",
        "live_execution_allowed",
    ):
        if fr.get(key) is not False:
            fail(f"offline firewall mismatch: {key}")
    return fr


def load_collector_module():
    sys.path.insert(0, str(COLLECTOR.parent))
    spec = importlib.util.spec_from_file_location("b15p1_collector_prelaunch_target", COLLECTOR)
    if spec is None or spec.loader is None:
        fail("collector import spec unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}

    combined = load_object(COMBINED_RESULT)
    combined_req = ((spec.get("prerequisites") or {}).get("combined_offline_result") or {})
    if combined.get("status") != combined_req.get("required_status"):
        fail("combined offline prerequisite status mismatch")
    if sha256_file(COMBINED_RESULT) != combined_req.get("sha256"):
        fail("combined offline prerequisite SHA mismatch")
    if combined.get("package_integrity_ok") is not True or combined.get("exit_code") != 0:
        fail("combined offline prerequisite integrity mismatch")
    checks["combined_offline_pass"] = True

    wrapper = load_object(WRAPPER_PREFLIGHT_RESULT)
    wrapper_req = ((spec.get("prerequisites") or {}).get("live_wrapper_preflight_result") or {})
    if wrapper.get("status") != wrapper_req.get("required_status"):
        fail("live wrapper preflight prerequisite status mismatch")
    if sha256_file(WRAPPER_PREFLIGHT_RESULT) != wrapper_req.get("sha256"):
        fail("live wrapper preflight prerequisite SHA mismatch")
    safety = wrapper.get("safety") or {}
    for key in (
        "credentials_available",
        "exchange_calls_performed",
        "collector_launch_performed",
        "price_data_used",
        "pnl_data_used",
        "live_execution_performed",
    ):
        if safety.get(key) is not False:
            fail(f"live wrapper preflight safety mismatch: {key}")
    checks["live_wrapper_preflight_pass"] = True

    live = load_object(LIVE_RESULT)
    live_req = ((spec.get("prerequisites") or {}).get("live_capability_result") or {})
    if live.get("status") != live_req.get("required_status"):
        fail("live capability result status mismatch")
    if sha256_file(LIVE_RESULT) != live_req.get("sha256"):
        fail("live capability result SHA mismatch")
    snapshot = live.get("snapshot") or {}
    if snapshot.get("sha256") != live_req.get("snapshot_sha256"):
        fail("live capability snapshot SHA mismatch")
    if snapshot.get("sha256") != EXPECTED_SNAPSHOT_SHA:
        fail("live capability snapshot anchor mismatch")
    coverage = live.get("pair_coverage") or {}
    expected_assets = int(live_req.get("required_both_venue_assets", -1))
    if coverage.get("frozen_admitted_assets") != expected_assets:
        fail("live capability admitted asset count mismatch")
    if coverage.get("qualified_bybit_count") != expected_assets:
        fail("live capability Bybit coverage mismatch")
    if coverage.get("qualified_okx_count") != expected_assets:
        fail("live capability OKX coverage mismatch")
    if coverage.get("qualified_both_venues_count") != expected_assets:
        fail("live capability both-venue coverage mismatch")
    permissions = live.get("permissions") or {}
    if permissions.get("bybit_readOnly") != 1:
        fail("Bybit live read-only permission mismatch")
    if permissions.get("bybit_withdraw_token_present") is not False:
        fail("Bybit live Withdraw permission present")
    if permissions.get("bybit_ip_bound") is not True:
        fail("Bybit live IP binding missing")
    if permissions.get("okx_permission") != "read_only":
        fail("OKX live permission mismatch")
    if permissions.get("okx_ip_bound") is not True:
        fail("OKX live IP binding missing")
    live_security = live.get("security") or {}
    for key in (
        "price_endpoints_called",
        "order_transfer_withdraw_endpoints_called",
        "collector_launch_authorized",
        "price_data_used",
        "pnl_data_used",
        "live_execution_authorized",
    ):
        if live_security.get(key) is not False:
            fail(f"live capability security mismatch: {key}")
    if live_security.get("security_firewall") != "PASS":
        fail("live capability security firewall mismatch")
    if live.get("collector_started") is not False:
        fail("collector unexpectedly started during live capability gate")
    checks["live_capability_pass"] = True
    checks["live_snapshot_sha256"] = snapshot.get("sha256")
    checks["live_both_venue_assets"] = expected_assets
    return checks


def validate_service_contract(spec: dict[str, Any]) -> dict[str, Any]:
    text = SERVICE.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    runtime = spec.get("runtime_contract") or {}

    required_exact = (
        "Type=simple",
        "User=botmarket",
        "WorkingDirectory=/home/botmarket/botmarketplace-site",
        "Environment=SC001_DATA_ROOT=/home/botmarket/sc001_data",
        "Environment=B15P1_CAPABILITY_SNAPSHOT=/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/source_capability_snapshot.json",
        "Environment=B15P1_LAUNCH_AUTHORIZATION=/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/collector_launch_authorization.json",
        "Environment=PYTHONUNBUFFERED=1",
        "EnvironmentFile=/home/botmarket/.config/sc001/b15-p1.env",
        "ExecStartPre=/usr/bin/mkdir -p /home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY",
        "ExecStart=/usr/bin/python3 -u /home/botmarket/botmarketplace-site/research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_3.py --mode run",
        "Restart=on-failure",
        "RestartSec=15s",
        "KillSignal=SIGTERM",
        "TimeoutStopSec=30s",
        "NoNewPrivileges=true",
        "PrivateTmp=true",
        "UMask=0027",
        "LimitNOFILE=65536",
        "StandardOutput=append:/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/systemd.log",
        "StandardError=append:/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/systemd.log",
    )
    missing = [fragment for fragment in required_exact if fragment not in lines]
    if missing:
        fail("systemd candidate missing required fragments: " + ",".join(missing))

    exec_start = [line for line in lines if line.startswith("ExecStart=")]
    if len(exec_start) != 1:
        fail(f"systemd candidate ExecStart count={len(exec_start)} expected=1")
    forbidden_prefixes = ("ExecStartPost=", "ExecReload=", "ExecStop=")
    forbidden_units = [line for line in lines if line.startswith(forbidden_prefixes)]
    if forbidden_units:
        fail("systemd candidate contains forbidden lifecycle command")
    forbidden_shell = ("bash -c", "sh -c", "curl ", "wget ", "nc ", "socat ")
    if any(token in text for token in forbidden_shell):
        fail("systemd candidate contains shell/network helper command")

    if runtime.get("stable_unit_name") != "sc001-b15p1-transferability.service":
        fail("stable runtime unit name mismatch")
    if runtime.get("runtime_unit_path") != "/etc/systemd/system/sc001-b15p1-transferability.service":
        fail("runtime unit path mismatch")
    if runtime.get("versioned_candidate_unit") != SERVICE.name:
        fail("versioned candidate unit mapping mismatch")
    if runtime.get("runtime_user") != "botmarket":
        fail("runtime user contract mismatch")

    helper = STATUS_HELPER.read_text(encoding="utf-8")
    if 'SERVICE="sc001-b15p1-transferability.service"' not in helper:
        fail("status helper stable unit name mismatch")
    if 'AUTH="$ROOT/collector_launch_authorization.json"' not in helper:
        fail("status helper launch authorization path mismatch")
    if 'CAP="$ROOT/source_capability_snapshot.json"' not in helper:
        fail("status helper capability path mismatch")

    return {
        "required_fragment_count": len(required_exact),
        "exec_start_count": len(exec_start),
        "stable_runtime_unit_name": runtime.get("stable_unit_name"),
        "status_helper_unit_name_match": True,
        "github_control_or_shell_permission_mutation": False,
    }


def call_name(call: ast.Call) -> str:
    fn = call.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        parts = [fn.attr]
        cur = fn.value
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


def validate_collector_order(source: str) -> dict[str, Any]:
    tree = ast.parse(source)
    target = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "run_collector":
            target = node
            break
    if target is None:
        fail("run_collector function missing")

    positions: dict[str, int] = {}
    all_calls: list[tuple[str, int]] = []
    for node in ast.walk(target):
        if isinstance(node, ast.Call):
            name = call_name(node)
            all_calls.append((name, node.lineno))
            if name and name not in positions:
                positions[name] = node.lineno

    required = (
        "require_freeze",
        "load_mapping",
        "ensure_mapping_invariants",
        "load_capability",
        "require_launch_authorization",
        "require_credentials",
        "install_ipv4_only",
        "ensure_dirs",
        "write_manifest",
    )
    missing = [name for name in required if name not in positions]
    if missing:
        fail("run_collector required call missing: " + ",".join(missing))

    ordered = [positions[name] for name in required]
    if ordered != sorted(ordered):
        fail("run_collector pre-network gate order mismatch")

    auth_line = positions["require_launch_authorization"]
    for name in ("require_credentials", "install_ipv4_only", "ensure_dirs", "write_manifest"):
        if positions[name] <= auth_line:
            fail(f"launch authorization does not precede {name}")

    network_activation_calls = [
        (name, line)
        for name, line in all_calls
        if name.endswith(".submit") or name.endswith(".start")
    ]
    if any(line <= auth_line for _, line in network_activation_calls):
        fail("thread/executor activation occurs before launch authorization")

    return {
        "call_positions": {name: positions[name] for name in required},
        "first_thread_or_executor_activation_line": (
            min(line for _, line in network_activation_calls)
            if network_activation_calls
            else None
        ),
        "authorization_precedes_credentials_network_and_writes": True,
    }


def validate_launch_boundary(module, spec: dict[str, Any]) -> dict[str, Any]:
    candidate = load_object(CANDIDATE)
    cand_spec = spec.get("launch_authorization_candidate") or {}
    if candidate.get("status") != cand_spec.get("top_level_status_must_be"):
        fail("launch candidate top-level status mismatch")
    if candidate.get("runtime_install_authorized") is not False:
        fail("launch candidate unexpectedly runtime-authorized")
    if candidate.get("collector_start_authorized") is not False:
        fail("launch candidate unexpectedly start-authorized")

    payload = candidate.get("proposed_runtime_payload")
    if not isinstance(payload, dict):
        fail("proposed runtime launch payload missing")

    anchors = payload.get("anchors") or {}
    expected_anchors = {
        "runner_sha256": sha256_file(COLLECTOR),
        "implementation_freeze_sha256": sha256_file(IMPLEMENTATION_FREEZE),
        "capability_snapshot_sha256": EXPECTED_SNAPSHOT_SHA,
        "service_file_sha256": sha256_file(SERVICE),
    }
    if anchors != expected_anchors:
        fail("proposed runtime launch payload anchor mismatch")
    if payload.get("status") != cand_spec.get("proposed_payload_status"):
        fail("proposed runtime payload status mismatch")
    if payload.get("launch_pass_token") != cand_spec.get("proposed_launch_pass_token"):
        fail("proposed runtime payload token mismatch")
    if payload.get("price_economic_research_authorized") is not False:
        fail("proposed runtime payload price firewall mismatch")
    if payload.get("live_execution_authorized") is not False:
        fail("proposed runtime payload execution firewall mismatch")

    kwargs = {
        "runner_sha256": expected_anchors["runner_sha256"],
        "freeze_sha256": expected_anchors["implementation_freeze_sha256"],
        "capability_sha256": expected_anchors["capability_snapshot_sha256"],
        "service_sha256": expected_anchors["service_file_sha256"],
    }

    # The intentionally non-authorizing top-level candidate must be rejected.
    try:
        module.validate_launch_authorization(candidate, **kwargs)
    except Exception:
        pass
    else:
        fail("top-level non-active candidate unexpectedly accepted")

    # The nested proposed payload must match the collector's exact validator.
    module.validate_launch_authorization(payload, **kwargs)

    mutations: list[tuple[str, dict[str, Any]]] = []

    x = copy.deepcopy(payload)
    x["status"] = "PENDING"
    mutations.append(("status", x))

    x = copy.deepcopy(payload)
    x["launch_pass_token"] = "WRONG"
    mutations.append(("token", x))

    for anchor_name in expected_anchors:
        x = copy.deepcopy(payload)
        x["anchors"][anchor_name] = "0" * 64
        mutations.append((f"anchor:{anchor_name}", x))

    x = copy.deepcopy(payload)
    x["price_economic_research_authorized"] = True
    mutations.append(("price_firewall", x))

    x = copy.deepcopy(payload)
    x["live_execution_authorized"] = True
    mutations.append(("execution_firewall", x))

    failed_closed = []
    for label, mutated in mutations:
        try:
            module.validate_launch_authorization(mutated, **kwargs)
        except Exception:
            failed_closed.append(label)
        else:
            fail(f"launch authorization mutation unexpectedly accepted: {label}")

    return {
        "candidate_top_level_rejected": True,
        "nested_runtime_payload_accepted": True,
        "failed_closed_mutation_count": len(failed_closed),
        "failed_closed_mutations": failed_closed,
        "runtime_install_authorized": False,
        "collector_start_authorized": False,
    }


def main() -> int:
    checks: dict[str, Any] = {}
    try:
        freeze = require_prelaunch_freeze()
        spec = load_object(SPEC)
        if spec.get("status") != "FROZEN_BEFORE_EXECUTION":
            fail("prelaunch spec status mismatch")
        if spec.get("expected_pass_status") != PASS:
            fail("prelaunch spec expected status mismatch")

        checks["prerequisites"] = validate_prerequisites(spec)

        module = load_collector_module()

        # Re-run the collector's own frozen dependency handshake in this exact package.
        impl_freeze = module.require_freeze()
        checks["collector_full_freeze_handshake"] = True
        checks["collector_freeze_status"] = impl_freeze.get("status")

        mapping = module.load_mapping()
        module.ensure_mapping_invariants(mapping)
        mapping_counts = {
            "base_assets": len(mapping["base_assets"]),
            "overlay_assets": len(mapping["overlay_assets"]),
            "asset_common_representations": len(mapping["asset_common_keys"]),
            "quote_common_representations": len(mapping["quote_common_keys"]),
            "quote_one_sided_representations": (
                len(mapping["quote_one_sided_bybit_keys"])
                + len(mapping["quote_one_sided_okx_keys"])
            ),
        }
        expected_counts = {
            "base_assets": 146,
            "overlay_assets": 46,
            "asset_common_representations": 207,
            "quote_common_representations": 12,
            "quote_one_sided_representations": 14,
        }
        if mapping_counts != expected_counts:
            fail(f"frozen mapping count mismatch: {mapping_counts}")
        checks["mapping_counts"] = mapping_counts

        collector_text = COLLECTOR.read_text(encoding="utf-8")
        library_text = LIBRARY.read_text(encoding="utf-8")
        service_text = SERVICE.read_text(encoding="utf-8")
        module.static_no_price_endpoint_guard([collector_text, library_text, service_text])
        checks["no_price_endpoint_static_guard"] = True

        checks["service_contract"] = validate_service_contract(spec)
        checks["collector_gate_order"] = validate_collector_order(collector_text)
        checks["launch_boundary"] = validate_launch_boundary(module, spec)

        contract = load_object(CONTRACT)
        if contract.get("collector_launch_authorized") is not False:
            fail("implementation contract launch firewall mismatch")
        if contract.get("price_data_authorized") is not False:
            fail("implementation contract price firewall mismatch")
        if contract.get("pnl_data_authorized") is not False:
            fail("implementation contract PnL firewall mismatch")
        if contract.get("live_execution_authorized") is not False:
            fail("implementation contract live execution firewall mismatch")
        mandatory = contract.get("mandatory_offline_self_tests") or []
        if len(mandatory) != 28:
            fail("implementation contract mandatory test count mismatch")
        checks["implementation_contract_mandatory_tests"] = len(mandatory)

        for key, value in (spec.get("offline_firewall") or {}).items():
            if value is not False:
                fail(f"spec offline firewall mismatch: {key}")

        manifest = {
            "schema": "sc001.b15.p1_collector_prelaunch_readiness_offline.v0.1",
            "status": PASS,
            "freeze_sha256": sha256_file(FREEZE),
            "spec_sha256": sha256_file(SPEC),
            "launch_candidate_sha256": sha256_file(CANDIDATE),
            "live_result_sha256": sha256_file(LIVE_RESULT),
            "live_snapshot_sha256": EXPECTED_SNAPSHOT_SHA,
            "collector_runner_sha256": sha256_file(COLLECTOR),
            "collector_library_sha256": sha256_file(LIBRARY),
            "implementation_freeze_sha256": sha256_file(IMPLEMENTATION_FREEZE),
            "service_candidate_sha256": sha256_file(SERVICE),
            "checks": checks,
            "credentials_available": False,
            "exchange_calls_performed": False,
            "collector_start_performed": False,
            "systemd_mutation_performed": False,
            "runtime_authorization_created": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "live_execution_performed": False,
            "next_state": "PREPARE_B15P1_COLLECTOR_HOST_SYSTEMD_DEPLOYMENT_READINESS_WRAPPER",
        }
        write_manifest(manifest)
        print(PASS)
        print("live_snapshot_sha256 =", EXPECTED_SNAPSHOT_SHA)
        print("mapping_asset_common_representations =", mapping_counts["asset_common_representations"])
        print("launch_candidate_top_level_rejected = True")
        print("launch_payload_fail_closed_mutations =", checks["launch_boundary"]["failed_closed_mutation_count"])
        print("collector_start_performed = False")
        print("exchange_calls_performed = False")
        return 0

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        write_manifest(
            {
                "schema": "sc001.b15.p1_collector_prelaunch_readiness_offline.v0.1",
                "status": REVIEW,
                "error": error,
                "checks": checks,
                "credentials_available": False,
                "exchange_calls_performed": False,
                "collector_start_performed": False,
                "systemd_mutation_performed": False,
                "runtime_authorization_created": False,
                "price_data_used": False,
                "pnl_data_used": False,
                "live_execution_performed": False,
                "next_state": "STOP_AND_REVIEW_B15P1_COLLECTOR_PRELAUNCH_READINESS",
            }
        )
        print(REVIEW)
        print("error =", error)
        print("collector_start_performed = False")
        print("exchange_calls_performed = False")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
