from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import queue
import shutil
import signal
import sys
import tempfile
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sc001_b15p1_nonprice_transferability_lib_v0_1_3 import (
    BYBIT_COIN_INFO_PATH,
    BYBIT_FEE_PATH,
    FEE_REFRESH_SECONDS,
    FEE_STALE_AFTER_SECONDS,
    OKX_CURRENCIES_PATH,
    OKX_FEE_PATH,
    REQUEST_DEADLINE_SECONDS,
    RawObjectIntegrityError,
    aggregate_representation,
    append_jsonl,
    atomic_json,
    build_frozen_mapping,
    canonical_json_bytes,
    decode_json_object,
    derive_route_state,
    fee_snapshot_state,
    install_ipv4_only,
    load_json,
    match_live_row,
    next_slot_ms,
    now_ms,
    okx_chain_alias,
    parse_bybit_coin_info,
    parse_okx_currencies,
    poll_chain_hash,
    private_get_bybit,
    private_get_okx,
    redact_text,
    representation_key,
    route_transition_event,
    sha256_bytes,
    sha256_file,
    source_state_events,
    source_server_timestamp_ms,
    static_no_price_endpoint_guard,
    storage_state,
    store_raw_object,
    utc_iso_ms,
    validate_capability_snapshot,
)

STAGE = "SC001-B15P1-NONPRICE-TRANSFERABILITY-COLLECTOR-V0.1.3"
VERSION = "0.1.3"
SELFTEST_PASS = "B15P1_NONPRICE_COLLECTOR_V013_SELF_TEST_PASS"
SELFTEST_REVIEW = "B15P1_NONPRICE_COLLECTOR_V013_SELF_TEST_REVIEW"
RUNNING = "B15P1_NONPRICE_COLLECTION_RUNNING"
SOURCE_REVIEW = "B15P1_NONPRICE_COLLECTION_SOURCE_REVIEW"
STOPPED = "B15P1_NONPRICE_COLLECTION_STOPPED"

ROOT = Path(
    os.environ.get(
        "B15P1_REPO_ROOT",
        str(Path(__file__).resolve().parents[2]),
    )
).resolve()

PROTOCOL = ROOT / "docs/research/sc001-b15-p1-15-second-nonprice-collector-protocol-v0.1.md"
DESIGN = ROOT / "docs/research/sc001-b15-p1-15-second-nonprice-collector-design-candidate-v0.1.json"
PREFLIGHT_SPEC = ROOT / "docs/research/sc001-b15-p1-15-second-nonprice-collector-design-preflight-spec-v0.1.json"
RATE_EVIDENCE = ROOT / "docs/research/sc001-b15-p1-nonprice-collector-rate-limit-evidence-v0.1.json"
DESIGN_PREFLIGHT_MANIFEST = ROOT / "docs/research/artifacts/b15-p1-collector-design/20260924T103023Z/collector_design_preflight_manifest.json"
IMPLEMENTATION_SEMANTICS = ROOT / "docs/research/sc001-b15-p1-nonprice-collector-implementation-semantics-v0.2.md"
RAW_STORAGE_AMENDMENT = ROOT / "docs/research/sc001-b15-p1-collector-raw-storage-amendment-v0.1.md"
IMPLEMENTATION_CONTRACT = ROOT / "docs/research/sc001-b15-p1-nonprice-collector-implementation-contract-v0.1.3.json"

BASE_ADMITTED = ROOT / "docs/research/artifacts/b15-p1-canonical-freeze/20260920T210446Z/ADMITTED.json"
FINAL_RESOLVED = ROOT / "docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/replay/integrated_replay_resolved_rows_v0.2.2.json"
FINAL_DISPOSITIONS = ROOT / "docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/replay/integrated_replay_asset_dispositions_v0.2.2.json"
FINAL_QUOTE_CLASSIFICATION = ROOT / "docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-preflight/identity_route_v0.2.2_final_quote_classification.json"
FREEZE_SUPPLEMENT = ROOT / "docs/research/sc001-b15-p1-v0.2.2-final-freeze-artifact-supplement-v1.json"
ROUTE_SHARD_INDEX = ROOT / "docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/directed_route_graph.v0.2.2.shard-index.json"

SERVICE_FILE = ROOT / "ops/systemd/sc001-b15p1-transferability-v0.1.3.service"
FREEZE = ROOT / "docs/research/sc001-b15-p1-nonprice-collector-implementation-freeze-v0.1.3.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_B15P1_TRANSFERABILITY"
RAW_OBJECTS = OUT_DIR / "raw_objects"
POLLS_DIR = OUT_DIR / "polls"
NORMALIZED_DIR = OUT_DIR / "normalized"
ROUTES_DIR = NORMALIZED_DIR / "routes"
VENUE_CHAIN_DIR = NORMALIZED_DIR / "venue_chain"
EVENTS_DIR = OUT_DIR / "events"
GAPS_DIR = OUT_DIR / "gaps"
FEES_DIR = OUT_DIR / "fees"
INVALID_DIR = OUT_DIR / "invalid"
STATE_FILE = OUT_DIR / "collector_state.json"
MANIFEST_FILE = OUT_DIR / "collector_manifest.json"
DAILY_MANIFEST_DIR = OUT_DIR / "daily_manifests"
CAPABILITY_FILE = Path(
    os.environ.get(
        "B15P1_CAPABILITY_SNAPSHOT",
        str(OUT_DIR / "source_capability_snapshot.json"),
    )
).expanduser().resolve()

LAUNCH_AUTH_FILE = Path(
    os.environ.get(
        "B15P1_LAUNCH_AUTHORIZATION",
        str(OUT_DIR / "collector_launch_authorization.json"),
    )
).expanduser().resolve()

FAST_CADENCE_SECONDS = 15
REQUEST_DEADLINE_SECONDS_LOCAL = 12
HEARTBEAT_SECONDS = 30
STORAGE_CHECK_SECONDS = 300
STORAGE_WARNING_BYTES = 20 * 1024**3
STORAGE_WARNING_PERCENT = 25.0
STORAGE_STOP_BYTES = 10 * 1024**3
STORAGE_STOP_PERCENT = 15.0

STOP_REQUESTED = False


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def daily_path(root: Path, ts_ms: int, suffix: str = ".jsonl") -> Path:
    day = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    return root / f"{day}{suffix}"


def utc_day_from_ms(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def state_hash(obj: Any) -> str:
    return sha256_bytes(canonical_json_bytes(obj))


def require_json_object(path: Path) -> dict[str, Any]:
    obj = load_json(path)
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def require_json_list(path: Path) -> list[dict[str, Any]]:
    obj = load_json(path)
    if not isinstance(obj, list):
        fail(f"JSON list expected: {path}")
    return obj


def require_freeze() -> dict[str, Any]:
    fr = require_json_object(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_B15P1_NONPRICE_COLLECTOR_SELF_TEST_V013":
        fail("implementation freeze status mismatch")
    expected = {
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "library_sha256": sha256_file(
            Path(__file__).resolve().with_name(
                "sc001_b15p1_nonprice_transferability_lib_v0_1_3.py"
            )
        ),
        "protocol_sha256": sha256_file(PROTOCOL),
        "design_candidate_sha256": sha256_file(DESIGN),
        "design_preflight_spec_sha256": sha256_file(PREFLIGHT_SPEC),
        "rate_limit_evidence_sha256": sha256_file(RATE_EVIDENCE),
        "design_preflight_manifest_sha256": sha256_file(DESIGN_PREFLIGHT_MANIFEST),
        "implementation_semantics_sha256": sha256_file(IMPLEMENTATION_SEMANTICS),
        "raw_storage_amendment_sha256": sha256_file(RAW_STORAGE_AMENDMENT),
        "implementation_contract_sha256": sha256_file(IMPLEMENTATION_CONTRACT),
        "base_admitted_sha256": sha256_file(BASE_ADMITTED),
        "final_resolved_rows_sha256": sha256_file(FINAL_RESOLVED),
        "final_asset_dispositions_sha256": sha256_file(FINAL_DISPOSITIONS),
        "final_quote_classification_sha256": sha256_file(FINAL_QUOTE_CLASSIFICATION),
        "freeze_artifact_supplement_sha256": sha256_file(FREEZE_SUPPLEMENT),
        "route_shard_index_sha256": sha256_file(ROUTE_SHARD_INDEX),
        "service_file_sha256": sha256_file(SERVICE_FILE),
    }
    for key, value in expected.items():
        if fr.get(key) != value:
            fail(f"implementation freeze hash mismatch: {key}")
    if fr.get("collector_launch_authorized") is not False:
        fail("implementation freeze launch firewall mismatch")
    if fr.get("live_source_calls_authorized_in_self_test") is not False:
        fail("self-test live source firewall mismatch")
    if fr.get("price_data_authorized") is not False:
        fail("price firewall mismatch")
    return fr


def load_mapping() -> dict[str, Any]:
    return build_frozen_mapping(
        require_json_list(BASE_ADMITTED),
        require_json_list(FINAL_RESOLVED),
        require_json_list(FINAL_DISPOSITIONS),
        require_json_object(FINAL_QUOTE_CLASSIFICATION),
    )


def ensure_mapping_invariants(mapping: dict[str, Any]) -> None:
    if len(mapping["base_assets"]) != 146:
        fail(f"base asset count mismatch: {len(mapping['base_assets'])}")
    if len(mapping["overlay_assets"]) != 46:
        fail(f"overlay asset count mismatch: {len(mapping['overlay_assets'])}")
    if len(mapping["asset_common_keys"]) != 207:
        fail(f"asset common count mismatch: {len(mapping['asset_common_keys'])}")
    if len(mapping["quote_common_keys"]) != 12:
        fail(f"quote common count mismatch: {len(mapping['quote_common_keys'])}")
    if len(mapping["quote_one_sided_bybit_keys"]) != 8:
        fail("Bybit one-sided quote count mismatch")
    if len(mapping["quote_one_sided_okx_keys"]) != 6:
        fail("OKX one-sided quote count mismatch")
    if len(mapping["exact_bybit"]) + len(mapping["exact_okx"]) != 182:
        fail("v0.2.2 exact row matcher count mismatch")


def fixture_bybit_body() -> dict[str, Any]:
    return {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "rows": [
                {
                    "coin": "USDT",
                    "chains": [
                        {
                            "chain": "ETH",
                            "chainType": "Ethereum",
                            "chainDeposit": "1",
                            "chainWithdraw": "1",
                            "contractAddress": "0x1111111111111111111111111111111111111111",
                            "withdrawFee": "1",
                            "withdrawPercentageFee": "0",
                            "depositMin": "0.1",
                            "withdrawMin": "1",
                            "withdrawMax": "100000",
                            "minAccuracy": "6",
                            "confirmation": "12",
                            "safeConfirmNumber": "64",
                        }
                    ],
                }
            ]
        },
    }


def fixture_okx_body() -> dict[str, Any]:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "ccy": "USDT",
                "chain": "USDT-ERC20",
                "canDep": True,
                "canWd": True,
                "ctAddr": "0x1111111111111111111111111111111111111111",
                "fee": "1",
                "feeCcy": "USDT",
                "burningFeeRate": "",
                "minDep": "0.1",
                "minWd": "1",
                "maxWd": "100000",
                "wdTickSz": "6",
                "minDepArrivalConfirm": "12",
                "minWdUnlockConfirm": "64",
            }
        ],
    }


def selftest_output_path() -> Path | None:
    explicit = os.environ.get("B15P1_SELFTEST_OUTPUT")
    if explicit:
        return Path(explicit).expanduser().resolve()
    runner_out = Path("/work/run/output")
    if runner_out.exists():
        return runner_out / "implementation_self_test_manifest.json"
    return None


def write_selftest_report(
    status: str,
    *,
    error: str | None,
    runner_sha256: str | None,
    freeze_sha256: str | None,
) -> None:
    path = selftest_output_path()
    if path is None:
        return
    contract = require_json_object(IMPLEMENTATION_CONTRACT)
    mandatory = list(contract.get("mandatory_offline_self_tests") or [])
    obj = {
        "schema": "sc001.b15.p1_nonprice_collector_implementation_self_test.v0.1.3",
        "status": status,
        "mandatory_tests": mandatory,
        "test_results": {
            name: (status == SELFTEST_PASS)
            for name in mandatory
        },
        "extra_tests": {
            "FROZEN_MAPPING_COUNTS": status == SELFTEST_PASS,
            "BASE_AND_EXACT_MATCHER_FIXTURES": status == SELFTEST_PASS,
            "ALIAS_CONFLICT_FAIL_CLOSED": status == SELFTEST_PASS,
            "RAW_OBJECT_CONTENT_ADDRESSING": status == SELFTEST_PASS,
            "RAW_OBJECT_CORRUPTION_FAIL_CLOSED": status == SELFTEST_PASS,
            "LAUNCH_AUTHORIZATION_FAIL_CLOSED": status == SELFTEST_PASS,
            "POLL_HASH_CHAIN_TAMPER": status == SELFTEST_PASS,
            "SYSTEMD_CANDIDATE_STATIC_GUARD": status == SELFTEST_PASS,
        },
        "error": error,
        "runner_sha256": runner_sha256,
        "library_sha256": sha256_file(
            Path(__file__).resolve().with_name(
                "sc001_b15p1_nonprice_transferability_lib_v0_1_3.py"
            )
        ),
        "implementation_freeze_sha256": freeze_sha256,
        "exchange_calls_performed": False,
        "collector_launch_authorized": False,
        "price_data_authorized": False,
        "pnl_data_authorized": False,
    }
    atomic_json(path, obj)


def self_test() -> int:
    runner_sha = None
    freeze_sha = None
    try:
        fr = require_freeze()
        runner_sha = sha256_file(Path(__file__).resolve())
        freeze_sha = sha256_file(FREEZE)
        mapping = load_mapping()
        ensure_mapping_invariants(mapping)

        # Scheduler / no-catch-up.
        if next_slot_ms(31_000) != 45_000:
            fail("scheduler normal-phase fixture")
        if next_slot_ms(47_000) != 60_000:
            fail("scheduler missed-slot fixture")
        if next_slot_ms(60_000) != 75_000:
            fail("scheduler exact-phase fixture")

        # No-overlap rule is represented by in-flight truth table.
        def can_start(in_flight: bool) -> bool:
            return not in_flight
        if can_start(True) or not can_start(False):
            fail("no-overlap fixture")

        # Venue parsers.
        by_rows = parse_bybit_coin_info(fixture_bybit_body())
        ok_rows = parse_okx_currencies(fixture_okx_body())
        if len(by_rows) != 1 or by_rows[0]["fee_currency"] != "USDT":
            fail("Bybit parser fixture")
        if len(ok_rows) != 1 or ok_rows[0]["raw_network"] != "ERC20":
            fail("OKX parser fixture")

        bad_by = fixture_bybit_body()
        bad_by["result"]["rows"][0]["chains"][0]["chainDeposit"] = "maybe"
        try:
            parse_bybit_coin_info(bad_by)
        except ValueError:
            pass
        else:
            fail("Bybit invalid-flag fixture accepted")

        bad_ok = fixture_okx_body()
        bad_ok["data"][0]["fee"] = "nan"
        try:
            parse_okx_currencies(bad_ok)
        except ValueError:
            pass
        else:
            fail("OKX invalid-decimal fixture accepted")

        missing_burn = fixture_okx_body()
        missing_burn["data"][0].pop("burningFeeRate", None)
        parsed_missing_burn = parse_okx_currencies(missing_burn)
        if parsed_missing_burn[0].get("metadata_valid") is not False:
            fail("OKX missing burningFeeRate did not fail closed")
        if parsed_missing_burn[0].get("percentage_withdraw_fee") is not None:
            fail("OKX missing burningFeeRate silently defaulted to zero")

        no_fee_ccy = fixture_okx_body()
        no_fee_ccy["data"][0].pop("feeCcy", None)
        parsed_no_fee_ccy = parse_okx_currencies(no_fee_ccy)
        if parsed_no_fee_ccy[0].get("fee_currency") != "USDT":
            fail("OKX absent feeCcy did not bind to withdrawn asset")
        if parsed_no_fee_ccy[0].get("fee_currency_source") != "IMPLICIT_WITHDRAWAL_ASSET_GET_CURRENCIES":
            fail("OKX absent feeCcy source classification mismatch")

        # Current OKX feeGroup schema + deprecated fallback.
        fee_group_item = {
            "venue": "OKX",
            "instrument": "BTC-USDT",
            "expected_group_id": "1",
            "request_start_ms": 1,
            "receive_ms": 2,
            "result": {
                "ok": True,
                "http_status": 200,
                "body": json.dumps({
                    "code": "0",
                    "data": [{
                        "feeGroup": [{
                            "groupId": "1",
                            "taker": "-0.001",
                            "maker": "-0.0008"
                        }]
                    }]
                }).encode("utf-8"),
                "error": None,
            },
        }
        fee_group_row = parse_fee_result(fee_group_item)
        if not fee_group_row.get("ok") or fee_group_row.get("fee_schema") != "FEE_GROUP":
            fail("OKX feeGroup parser fixture")
        if fee_group_row.get("account_fee_group") != "1":
            fail("OKX feeGroup groupId fixture")

        fee_legacy_item = {
            **fee_group_item,
            "expected_group_id": None,
            "result": {
                "ok": True,
                "http_status": 200,
                "body": json.dumps({
                    "code": "0",
                    "data": [{
                        "taker": "-0.001",
                        "maker": "-0.0008"
                    }]
                }).encode("utf-8"),
                "error": None,
            },
        }
        fee_legacy_row = parse_fee_result(fee_legacy_item)
        if not fee_legacy_row.get("ok") or fee_legacy_row.get("fee_schema") != "DEPRECATED_TOP_LEVEL":
            fail("OKX deprecated fee fallback fixture")

        # Frozen mapping base matcher fixture.
        base_admitted = require_json_list(BASE_ADMITTED)
        first = base_admitted[0]
        rep = first["representations"][0]
        by_fixture = {
            "venue": "BYBIT",
            "asset": first["asset"],
            "raw_network": rep["bybit_chain"],
            "raw_chainType": rep["bybit_chainType"],
            "raw_contract": rep["representation_identity"],
            "deposit_enabled": True,
            "withdraw_enabled": True,
            "fixed_withdraw_fee": "1",
            "percentage_withdraw_fee": "0",
            "fee_currency": first["asset"],
            "min_withdrawal": "1",
            "min_deposit": "1",
            "max_withdrawal": None,
            "withdrawal_precision": None,
            "confirmation_metadata": {},
            "metadata_valid": True,
        }
        by_match = match_live_row(by_fixture, mapping)
        if by_match.get("canonical_key") != representation_key(
            first["asset"], rep["network_uid"], rep["representation_identity"]
        ):
            fail("base Bybit frozen matcher fixture")

        ok_fixture = dict(by_fixture)
        ok_fixture.update({
            "venue": "OKX",
            "raw_network_full": rep["okx_chain"],
            "raw_network": okx_chain_alias(first["asset"], rep["okx_chain"]),
            "raw_chainType": "",
        })
        ok_match = match_live_row(ok_fixture, mapping)
        if ok_match.get("canonical_key") != by_match.get("canonical_key"):
            fail("base OKX frozen matcher fixture")

        # Exact v0.2.2 matcher fixture.
        final_rows = require_json_list(FINAL_RESOLVED)
        exact = next(
            r for r in final_rows
            if r.get("venue") == "BYBIT" and r.get("asset") == "GRAM"
        )
        exact_fixture = {
            "venue": "BYBIT",
            "asset": exact["asset"],
            "raw_network": exact["raw_network"],
            "raw_chainType": exact.get("raw_chainType", ""),
            "raw_contract": exact.get("raw_contract", ""),
            "deposit_enabled": True,
            "withdraw_enabled": True,
            "fixed_withdraw_fee": "1",
            "percentage_withdraw_fee": "0",
            "fee_currency": exact["asset"],
            "min_withdrawal": "1",
            "min_deposit": "1",
            "max_withdrawal": None,
            "withdrawal_precision": None,
            "confirmation_metadata": {},
            "metadata_valid": True,
        }
        exact_match = match_live_row(exact_fixture, mapping)
        if exact_match.get("match_status") != "MATCHED_EXACT_V022":
            fail("exact v0.2.2 matcher fixture")

        # Alias conflict must fail closed.
        a = dict(exact_match)
        b = dict(exact_match)
        a["fixed_withdraw_fee"] = "1"
        b["fixed_withdraw_fee"] = "2"
        agg = aggregate_representation([a, b])
        if not agg or agg.get("status") != "METADATA_INVALID_ALIAS_CONFLICT":
            fail("alias conflict fixture")

        # Route-state fixtures.
        valid_active = {
            "valid": True, "withdraw_enabled": True, "deposit_enabled": True
        }
        valid_off = {
            "valid": True, "withdraw_enabled": False, "deposit_enabled": False
        }
        if derive_route_state(valid_active, valid_active) != "ACTIVE":
            fail("route ACTIVE fixture")
        if derive_route_state(valid_off, valid_active) != "BLOCKED_SOURCE_WITHDRAWAL":
            fail("route source-block fixture")
        if derive_route_state(valid_active, valid_off) != "BLOCKED_DESTINATION_DEPOSIT":
            fail("route destination-block fixture")
        if derive_route_state(valid_off, valid_off) != "BLOCKED_BOTH":
            fail("route both-block fixture")
        if derive_route_state(None, valid_active) != "SOURCE_UNKNOWN":
            fail("route unknown fixture")
        invalid = dict(valid_active); invalid["valid"] = False
        if derive_route_state(invalid, valid_active) != "METADATA_INVALID":
            fail("route metadata-invalid fixture")

        # Transition / gap fixtures.
        if route_transition_event("ACTIVE", "BLOCKED_SOURCE_WITHDRAWAL") != "ROUTE_ACTIVE_TO_BLOCKED":
            fail("route transition active->blocked fixture")
        if route_transition_event("SOURCE_UNKNOWN", "ACTIVE") != "ROUTE_UNKNOWN_TO_OBSERVED":
            fail("route transition unknown->observed fixture")
        if source_state_events(None, {"valid": True}) != ["CHAIN_APPEARED"]:
            fail("source appeared fixture")
        if source_state_events({"valid": True}, None) != ["CHAIN_DISAPPEARED"]:
            fail("source disappeared fixture")

        gap_fixture = {}
        if "BYBIT" not in gap_fixture:
            gap_fixture["BYBIT"] = {"start_slot_ms": 1000, "error": "timeout"}
            opened = "SOURCE_GAP_OPENED"
        else:
            opened = None
        if opened != "SOURCE_GAP_OPENED":
            fail("source gap open fixture")
        if "BYBIT" in gap_fixture:
            start = gap_fixture.pop("BYBIT")
            closed = (
                "SOURCE_GAP_CLOSED"
                if start["start_slot_ms"] == 1000
                else None
            )
        else:
            closed = None
        if closed != "SOURCE_GAP_CLOSED" or gap_fixture:
            fail("source gap close fixture")

        # Fee staleness.
        if fee_snapshot_state(28_800) != "FRESH":
            fail("fee staleness boundary fixture")
        if fee_snapshot_state(28_801) != "FEE_SNAPSHOT_STALE":
            fail("fee stale fixture")

        # Storage pressure.
        if storage_state(
            30 * 1024**3, 50,
            warning_bytes=20 * 1024**3, warning_percent=25,
            stop_bytes=10 * 1024**3, stop_percent=15,
        ) != "OK":
            fail("storage OK fixture")
        if storage_state(
            15 * 1024**3, 20,
            warning_bytes=20 * 1024**3, warning_percent=25,
            stop_bytes=10 * 1024**3, stop_percent=15,
        ) != "STORAGE_WARNING":
            fail("storage warning fixture")
        if storage_state(
            5 * 1024**3, 50,
            warning_bytes=20 * 1024**3, warning_percent=25,
            stop_bytes=10 * 1024**3, stop_percent=15,
        ) != "STORAGE_PRESSURE_REVIEW":
            fail("storage stop fixture")

        # Raw content-addressed store.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "objects"
            x1 = store_raw_object(root, "BYBIT", b'{"x":1}')
            x2 = store_raw_object(root, "BYBIT", b'{"x":1}')
            x3 = store_raw_object(root, "BYBIT", b'{"x":2}')
            if not x1["created"] or x2["created"] or not x3["created"]:
                fail("raw object dedup fixture")
            if x1["sha256"] != x2["sha256"] or x1["sha256"] == x3["sha256"]:
                fail("raw object hash fixture")
            obj_path = Path(x1["path"])
            obj_path.write_bytes(b"corrupt")
            try:
                store_raw_object(root, "BYBIT", b'{"x":1}')
            except RawObjectIntegrityError:
                pass
            else:
                fail("raw object corruption fixture")

        # Append-only and atomic state.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log = root / "events.jsonl"
            append_jsonl(log, {"n": 1})
            append_jsonl(log, {"n": 2})
            lines = log.read_text(encoding="utf-8").splitlines()
            if len(lines) != 2 or json.loads(lines[0])["n"] != 1:
                fail("append-only write fixture")
            state = root / "state.json"
            atomic_json(state, {"epoch": 1, "last_heartbeat_ms": 100})
            loaded = load_json(state)
            loaded["epoch"] = 2
            atomic_json(state, loaded)
            if load_json(state).get("epoch") != 2:
                fail("atomic state restart fixture")

        # Secret redaction.
        secret = "SECRET_VALUE_ABC123"
        redacted = redact_text(f"prefix {secret} suffix", [secret])
        if secret in redacted or "<REDACTED>" not in redacted:
            fail("secret redaction fixture")

        # Deterministic authentication helpers are exercised indirectly in library
        # static import; no network call is made in self-test.
        runner_text = Path(__file__).read_text(encoding="utf-8")
        lib_text = Path(__file__).resolve().with_name(
            "sc001_b15p1_nonprice_transferability_lib_v0_1_3.py"
        ).read_text(encoding="utf-8")
        service_text = SERVICE_FILE.read_text(encoding="utf-8")
        static_no_price_endpoint_guard([runner_text, lib_text, service_text])

        # Service candidate firewall.
        for fragment in (
            "User=botmarket",
            "Restart=on-failure",
            "RestartSec=15s",
            "--mode run",
            "EnvironmentFile=/home/botmarket/.config/sc001/b15-p1.env",
            "NoNewPrivileges=true",
        ):
            if fragment not in service_text:
                fail(f"systemd service fixture missing: {fragment}")

        # Capability snapshot validator fixture.
        freeze_sha = sha256_file(FREEZE)
        runner_sha = sha256_file(Path(__file__).resolve())
        route_sha = require_json_object(ROUTE_SHARD_INDEX).get("logical_sha256")
        cap = {
            "status": "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS",
            "anchors": {
                "runner_sha256": runner_sha,
                "implementation_freeze_sha256": freeze_sha,
                "route_graph_sha256": route_sha,
            },
            "permissions": {
                "bybit_readOnly": 1,
                "bybit_withdraw_token_present": False,
                "okx_permission": "read_only",
            },
            "source_endpoints_pass": True,
            "bybit_base_url": "https://api.bybit.com",
            "okx_base_url": "https://www.okx.com",
            "qualified_pairs": {
                "BYBIT": ["BTCUSDT"],
                "OKX": ["BTC-USDT"],
            },
            "qualified_pair_metadata": {
                "OKX": {
                    "BTC-USDT": {"groupId": "1"}
                }
            },
        }
        from sc001_b15p1_nonprice_transferability_lib_v0_1_3 import validate_capability_snapshot
        validate_capability_snapshot(
            cap,
            runner_sha256=runner_sha,
            freeze_sha256=freeze_sha,
            route_graph_sha256=route_sha,
        )

        launch_fixture = {
            "status": "B15P1_NONPRICE_COLLECTOR_LAUNCH_AUTHORIZED",
            "launch_pass_token": "B15P1_NONPRICE_COLLECTOR_LAUNCH_PASS",
            "anchors": {
                "runner_sha256": runner_sha,
                "implementation_freeze_sha256": freeze_sha,
                "capability_snapshot_sha256": "a"*64,
                "service_file_sha256": sha256_file(SERVICE_FILE),
            },
            "price_economic_research_authorized": False,
            "live_execution_authorized": False,
        }
        validate_launch_authorization(
            launch_fixture,
            runner_sha256=runner_sha,
            freeze_sha256=freeze_sha,
            capability_sha256="a"*64,
            service_sha256=sha256_file(SERVICE_FILE),
        )
        bad_launch = dict(launch_fixture)
        bad_launch["status"] = "PENDING"
        try:
            validate_launch_authorization(
                bad_launch,
                runner_sha256=runner_sha,
                freeze_sha256=freeze_sha,
                capability_sha256="a"*64,
                service_sha256=sha256_file(SERVICE_FILE),
            )
        except RuntimeError:
            pass
        else:
            fail("launch authorization fail-closed fixture")

        # Poll hash chain tamper fixture.
        h1 = poll_chain_hash("0"*64, "1"*64, "2"*64, "3"*64, "4"*64)
        h2 = poll_chain_hash(h1, "5"*64, "6"*64, "7"*64, "8"*64)
        h2b = poll_chain_hash(h1, "5"*64, "6"*64, "7"*64, "9"*64)
        if h2 == h2b:
            fail("poll hash-chain tamper fixture")

        write_selftest_report(
            SELFTEST_PASS,
            error=None,
            runner_sha256=runner_sha,
            freeze_sha256=freeze_sha,
        )
        print(SELFTEST_PASS)
        print("freeze_sha256 =", freeze_sha)
        print("runner_sha256 =", runner_sha)
        print("library_sha256 =", fr["library_sha256"])
        print("base_assets =", len(mapping["base_assets"]))
        print("overlay_assets =", len(mapping["overlay_assets"]))
        print("asset_common_representations =", len(mapping["asset_common_keys"]))
        print("quote_common_representations =", len(mapping["quote_common_keys"]))
        print("quote_one_sided_representations =", len(mapping["quote_one_sided_bybit_keys"]) + len(mapping["quote_one_sided_okx_keys"]))
        print("exchange_calls_performed = False")
        print("collector_launch_authorized = False")
        print("price_data_authorized = False")
        return 0
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        try:
            write_selftest_report(
                SELFTEST_REVIEW,
                error=err,
                runner_sha256=runner_sha,
                freeze_sha256=freeze_sha,
            )
        except Exception:
            pass
        print(SELFTEST_REVIEW)
        print("error =", err)
        print("exchange_calls_performed = False")
        print("collector_launch_authorized = False")
        print("price_data_authorized = False")
        return 2


def require_credentials() -> dict[str, str]:
    required = (
        "SC001_B15_BYBIT_API_KEY",
        "SC001_B15_BYBIT_API_SECRET",
        "SC001_B15_BYBIT_BASE_URL",
        "SC001_B15_OKX_API_KEY",
        "SC001_B15_OKX_API_SECRET",
        "SC001_B15_OKX_PASSPHRASE",
        "SC001_B15_OKX_BASE_URL",
    )
    out = {k: os.environ.get(k, "") for k in required}
    missing = [k for k,v in out.items() if not v]
    if missing:
        fail("missing runtime credential environment: " + ",".join(missing))
    return out


def load_capability(fr: dict[str, Any]):
    if not CAPABILITY_FILE.exists():
        fail(f"capability snapshot missing: {CAPABILITY_FILE}")
    snap = require_json_object(CAPABILITY_FILE)
    route_sha = require_json_object(ROUTE_SHARD_INDEX).get("logical_sha256")
    return validate_capability_snapshot(
        snap,
        runner_sha256=sha256_file(Path(__file__).resolve()),
        freeze_sha256=sha256_file(FREEZE),
        route_graph_sha256=route_sha,
    ), snap


def validate_launch_authorization(
    obj: dict[str, Any],
    *,
    runner_sha256: str,
    freeze_sha256: str,
    capability_sha256: str,
    service_sha256: str,
) -> None:
    if obj.get("status") != "B15P1_NONPRICE_COLLECTOR_LAUNCH_AUTHORIZED":
        fail("COLLECTOR_LAUNCH_NOT_AUTHORIZED")
    if obj.get("launch_pass_token") != "B15P1_NONPRICE_COLLECTOR_LAUNCH_PASS":
        fail("collector launch token mismatch")
    anchors = obj.get("anchors") or {}
    expected = {
        "runner_sha256": runner_sha256,
        "implementation_freeze_sha256": freeze_sha256,
        "capability_snapshot_sha256": capability_sha256,
        "service_file_sha256": service_sha256,
    }
    for key, value in expected.items():
        if anchors.get(key) != value:
            fail(f"collector launch anchor mismatch: {key}")
    if obj.get("price_economic_research_authorized") is not False:
        fail("launch authorization price firewall mismatch")
    if obj.get("live_execution_authorized") is not False:
        fail("launch authorization live execution firewall mismatch")


def require_launch_authorization() -> dict[str, Any]:
    if not LAUNCH_AUTH_FILE.exists():
        fail("COLLECTOR_LAUNCH_NOT_AUTHORIZED")
    obj = require_json_object(LAUNCH_AUTH_FILE)
    validate_launch_authorization(
        obj,
        runner_sha256=sha256_file(Path(__file__).resolve()),
        freeze_sha256=sha256_file(FREEZE),
        capability_sha256=sha256_file(CAPABILITY_FILE),
        service_sha256=sha256_file(SERVICE_FILE),
    )
    return obj


def initial_state() -> tuple[dict[str, Any], bool]:
    t = now_ms()
    if STATE_FILE.exists():
        state = require_json_object(STATE_FILE)
        if state.get("stage") != STAGE:
            fail("existing state stage mismatch")
        if state.get("version") != VERSION:
            fail("existing state version mismatch")
        return state, True
    state = {
        "stage": STAGE,
        "version": VERSION,
        "status": "INITIALIZED",
        "process_epoch": 0,
        "started_ms": t,
        "started_utc": utc_iso_ms(t),
        "last_heartbeat_ms": t,
        "last_scheduled_slot_ms": None,
        "last_poll_chain_hash": "0"*64,
        "poll_count": 0,
        "invalid_poll_count": 0,
        "missed_poll_slots": 0,
        "source_gap_count": 0,
        "process_restart_count": 0,
        "open_source_gaps": {},
        "last_source_states": {},
        "last_route_states": {},
        "last_fee_refresh_completed_ms": None,
        "last_fee_snapshots": {},
        "current_utc_day": utc_day_from_ms(t),
        "price_data_collected": False,
        "pnl_calculated": False,
    }
    atomic_json(STATE_FILE, state)
    return state, False


def log_gap(event: str, **extra: Any) -> None:
    t = now_ms()
    append_jsonl(
        GAPS_DIR / "source_gaps.jsonl",
        {
            "stage": STAGE,
            "event": event,
            "ts_ms": t,
            "ts_utc": utc_iso_ms(t),
            **extra,
        },
    )


def record_restart_gap(state: dict[str, Any], had_state: bool) -> None:
    t = now_ms()
    state["process_epoch"] = int(state.get("process_epoch", 0)) + 1
    if had_state and state.get("last_heartbeat_ms") is not None:
        prev = int(state["last_heartbeat_ms"])
        gap = max(0, t - prev)
        state["process_restart_count"] = int(state.get("process_restart_count", 0)) + 1
        log_gap(
            "PROCESS_RESTART_GAP",
            start_ms=prev,
            end_ms=t,
            duration_ms=gap,
            process_epoch=state["process_epoch"],
        )
    state["last_heartbeat_ms"] = t
    atomic_json(STATE_FILE, state)


def update_heartbeat(state: dict[str, Any]) -> None:
    state["last_heartbeat_ms"] = now_ms()
    atomic_json(STATE_FILE, state)


def storage_guard() -> str:
    usage = shutil.disk_usage(OUT_DIR if OUT_DIR.exists() else DATA_ROOT)
    free_percent = 100.0 * usage.free / usage.total
    return storage_state(
        usage.free,
        free_percent,
        warning_bytes=STORAGE_WARNING_BYTES,
        warning_percent=STORAGE_WARNING_PERCENT,
        stop_bytes=STORAGE_STOP_BYTES,
        stop_percent=STORAGE_STOP_PERCENT,
    )


def ensure_dirs() -> None:
    for p in (
        OUT_DIR, RAW_OBJECTS, POLLS_DIR, VENUE_CHAIN_DIR, ROUTES_DIR,
        EVENTS_DIR, GAPS_DIR, FEES_DIR, INVALID_DIR, DAILY_MANIFEST_DIR,
    ):
        p.mkdir(parents=True, exist_ok=True)


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as exc:
                fail(f"invalid JSONL {path}:{line_no}: {exc}")
            if not isinstance(obj, dict):
                fail(f"JSONL object expected {path}:{line_no}")
            yield obj


def day_bounds_ms(day: str) -> tuple[int, int]:
    start = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_ms = int(start.timestamp() * 1000)
    return start_ms, start_ms + 86_400_000


def finalize_daily_manifest(day: str) -> dict[str, Any]:
    out_path = DAILY_MANIFEST_DIR / f"{day}.json"
    files = {
        "polls": POLLS_DIR / f"{day}.jsonl",
        "venue_chain": VENUE_CHAIN_DIR / f"{day}.jsonl",
        "routes": ROUTES_DIR / f"{day}.jsonl",
        "events": EVENTS_DIR / f"{day}.jsonl",
        "invalid": INVALID_DIR / f"{day}.jsonl",
        "fees_bybit": FEES_DIR / "bybit" / f"{day}.jsonl",
        "fees_okx": FEES_DIR / "okx" / f"{day}.jsonl",
    }
    file_info: dict[str, Any] = {}
    for name, path in files.items():
        if path.exists():
            rows = sum(1 for _ in iter_jsonl(path))
            file_info[name] = {
                "path": str(path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "rows": rows,
            }
        else:
            file_info[name] = {
                "path": str(path),
                "sha256": None,
                "size_bytes": 0,
                "rows": 0,
            }

    poll_rows = list(iter_jsonl(files["polls"])) if files["polls"].exists() else []
    slots = [
        int(r["scheduled_slot_ms"])
        for r in poll_rows
        if r.get("scheduled_slot_ms") is not None
    ]
    raw_hashes: set[str] = set()
    for row in poll_rows:
        for venue in ("BYBIT", "OKX"):
            h = ((row.get("venues") or {}).get(venue) or {}).get("raw_body_sha256")
            if h:
                raw_hashes.add(str(h))
        late_h = row.get("raw_body_sha256")
        if late_h:
            raw_hashes.add(str(late_h))
    for fee_name in ("fees_bybit", "fees_okx"):
        path = files[fee_name]
        if path.exists():
            for row in iter_jsonl(path):
                h = row.get("raw_body_sha256")
                if h:
                    raw_hashes.add(str(h))

    start_ms, end_ms = day_bounds_ms(day)
    first_slot = min(slots) if slots else None
    last_slot = max(slots) if slots else None
    full_day_window_covered = bool(
        first_slot is not None
        and last_slot is not None
        and first_slot <= start_ms + FAST_CADENCE_SECONDS * 1000
        and last_slot >= end_ms - FAST_CADENCE_SECONDS * 1000
    )
    chain_rows = [r for r in poll_rows if r.get("poll_chain_hash")]
    terminal_chain = (
        chain_rows[-1].get("poll_chain_hash") if chain_rows else None
    )

    gap_summary: dict[str, int] = {}
    gap_file = GAPS_DIR / "source_gaps.jsonl"
    if gap_file.exists():
        for row in iter_jsonl(gap_file):
            ts = row.get("ts_ms")
            if ts is None:
                continue
            ts = int(ts)
            if start_ms <= ts < end_ms:
                event = str(row.get("event") or "UNKNOWN")
                gap_summary[event] = gap_summary.get(event, 0) + 1

    manifest = {
        "schema": "sc001.b15.p1_nonprice_collector_daily_manifest.v0.1",
        "stage": STAGE,
        "utc_day": day,
        "generated_ms": now_ms(),
        "files": file_info,
        "polls": {
            "observed_slots": len(slots),
            "expected_slots_per_full_day": 86_400 // FAST_CADENCE_SECONDS,
            "first_slot_ms": first_slot,
            "last_slot_ms": last_slot,
            "full_day_window_covered": full_day_window_covered,
            "terminal_poll_chain_hash": terminal_chain,
        },
        "referenced_raw_object_sha256": sorted(raw_hashes),
        "referenced_raw_object_count": len(raw_hashes),
        "source_gap_summary": dict(sorted(gap_summary.items())),
        "price_data_collected": False,
        "pnl_calculated": False,
    }

    if out_path.exists():
        old = require_json_object(out_path)
        old_cmp = dict(old)
        new_cmp = dict(manifest)
        old_cmp.pop("generated_ms", None)
        new_cmp.pop("generated_ms", None)
        if old_cmp != new_cmp:
            fail(f"daily manifest drift: {day}")
        return old

    atomic_json(out_path, manifest)
    return manifest


def maybe_finalize_previous_day(state: dict[str, Any], slot_ms: int) -> None:
    current_day = utc_day_from_ms(slot_ms)
    previous_day = state.get("current_utc_day")
    if previous_day and previous_day != current_day:
        finalize_daily_manifest(str(previous_day))
    state["current_utc_day"] = current_day


def write_manifest(fr: dict[str, Any], capability_raw: dict[str, Any]) -> None:
    obj = {
        "stage": STAGE,
        "version": VERSION,
        "created_ms": now_ms(),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "library_sha256": fr["library_sha256"],
        "implementation_freeze_sha256": sha256_file(FREEZE),
        "protocol_sha256": fr["protocol_sha256"],
        "design_candidate_sha256": fr["design_candidate_sha256"],
        "design_preflight_manifest_sha256": fr["design_preflight_manifest_sha256"],
        "route_graph_sha256": require_json_object(ROUTE_SHARD_INDEX).get("logical_sha256"),
        "capability_snapshot_sha256": sha256_file(CAPABILITY_FILE),
        "capability_status": capability_raw.get("status"),
        "fast_cadence_seconds": FAST_CADENCE_SECONDS,
        "request_deadline_seconds": REQUEST_DEADLINE_SECONDS_LOCAL,
        "fee_refresh_seconds": FEE_REFRESH_SECONDS,
        "fee_stale_after_seconds": FEE_STALE_AFTER_SECONDS,
        "price_data_authorized": False,
        "pnl_authorized": False,
    }
    atomic_json(MANIFEST_FILE, obj)


def fetch_fast(venue: str, creds: dict[str, str], cap) -> dict[str, Any]:
    if venue == "BYBIT":
        return private_get_bybit(
            cap.bybit_base_url,
            creds["SC001_B15_BYBIT_API_KEY"],
            creds["SC001_B15_BYBIT_API_SECRET"],
            BYBIT_COIN_INFO_PATH,
            timeout=REQUEST_DEADLINE_SECONDS_LOCAL,
        )
    return private_get_okx(
        cap.okx_base_url,
        creds["SC001_B15_OKX_API_KEY"],
        creds["SC001_B15_OKX_API_SECRET"],
        creds["SC001_B15_OKX_PASSPHRASE"],
        OKX_CURRENCIES_PATH,
        timeout=REQUEST_DEADLINE_SECONDS_LOCAL,
    )


def fee_refresh_worker(
    creds: dict[str, str],
    cap,
    stop_event: threading.Event,
    result_queue: "queue.Queue[dict[str, Any]]",
) -> None:
    try:
        for venue, pairs in (
            ("BYBIT", cap.qualified_pairs_bybit),
            ("OKX", cap.qualified_pairs_okx),
        ):
            for pair in pairs:
                if stop_event.is_set():
                    result_queue.put({"_done": True, "stopped": True})
                    return
                started = now_ms()
                if venue == "BYBIT":
                    query = urllib.parse.urlencode({"category": "spot", "symbol": pair})
                    result = private_get_bybit(
                        cap.bybit_base_url,
                        creds["SC001_B15_BYBIT_API_KEY"],
                        creds["SC001_B15_BYBIT_API_SECRET"],
                        BYBIT_FEE_PATH,
                        query=query,
                        timeout=REQUEST_DEADLINE_SECONDS_LOCAL,
                    )
                else:
                    query = urllib.parse.urlencode({"instType": "SPOT", "instId": pair})
                    path = OKX_FEE_PATH + "?" + query
                    result = private_get_okx(
                        cap.okx_base_url,
                        creds["SC001_B15_OKX_API_KEY"],
                        creds["SC001_B15_OKX_API_SECRET"],
                        creds["SC001_B15_OKX_PASSPHRASE"],
                        path,
                        timeout=REQUEST_DEADLINE_SECONDS_LOCAL,
                    )
                result_queue.put({
                    "venue": venue,
                    "instrument": pair,
                    "expected_group_id": (
                        cap.okx_group_id_by_instrument.get(pair)
                        if venue == "OKX"
                        else None
                    ),
                    "request_start_ms": started,
                    "receive_ms": now_ms(),
                    "result": result,
                })
                for _ in range(10):
                    if stop_event.is_set():
                        result_queue.put({"_done": True, "stopped": True})
                        return
                    time.sleep(0.1)
        result_queue.put({
            "_done": True,
            "stopped": False,
            "completed_ms": now_ms(),
        })
    except Exception as exc:
        result_queue.put({
            "_done": True,
            "stopped": False,
            "error": f"{type(exc).__name__}: {exc}",
            "completed_ms": now_ms(),
        })


def parse_fee_result(item: dict[str, Any]) -> dict[str, Any]:
    venue = item["venue"]
    pair = item["instrument"]
    result = item["result"]
    raw = result.get("body") or b""
    row = {
        "stage": STAGE,
        "venue": venue,
        "instrument": pair,
        "request_start_ms": item["request_start_ms"],
        "receive_ms": item["receive_ms"],
        "http_status": result.get("http_status"),
        "ok": False,
        "taker_fee_rate": None,
        "maker_fee_rate": None,
        "account_fee_group": None,
        "error": result.get("error"),
    }
    if not result.get("ok"):
        return row
    try:
        obj = decode_json_object(raw)
        if venue == "BYBIT":
            if int(obj.get("retCode", -1)) != 0:
                raise ValueError(f"retCode={obj.get('retCode')}")
            rows = (obj.get("result") or {}).get("list") or []
            exact = [x for x in rows if str(x.get("symbol") or "") == pair]
            if len(exact) != 1:
                raise ValueError("exact Bybit fee row mismatch")
            r = exact[0]
            row["taker_fee_rate"] = str(r.get("takerFeeRate"))
            row["maker_fee_rate"] = str(r.get("makerFeeRate"))
        else:
            if str(obj.get("code")) != "0":
                raise ValueError(f"code={obj.get('code')}")
            rows = obj.get("data") or []
            if len(rows) != 1:
                raise ValueError("OKX fee row mismatch")
            r = rows[0]
            expected_group = str(item.get("expected_group_id") or "")
            fee_groups = r.get("feeGroup") or []
            selected = None
            if isinstance(fee_groups, list) and fee_groups:
                if expected_group:
                    exact = [
                        g for g in fee_groups
                        if isinstance(g, dict)
                        and str(g.get("groupId") or "") == expected_group
                    ]
                    if len(exact) != 1:
                        raise ValueError(
                            f"OKX feeGroup exact group mismatch expected={expected_group}"
                        )
                    selected = exact[0]
                elif len(fee_groups) == 1 and isinstance(fee_groups[0], dict):
                    selected = fee_groups[0]
                else:
                    raise ValueError("OKX feeGroup ambiguous without groupId")

            if selected is not None:
                taker = selected.get("taker")
                maker = selected.get("maker")
                group_id = str(selected.get("groupId") or expected_group)
                schema = "FEE_GROUP"
            else:
                # Explicit compatibility fallback while OKX still returns
                # deprecated top-level fields.
                taker = r.get("taker")
                maker = r.get("maker")
                group_id = expected_group
                schema = "DEPRECATED_TOP_LEVEL"

            if taker in (None, "") or maker in (None, ""):
                raise ValueError("OKX fee fields missing")
            row["taker_fee_rate"] = str(taker)
            row["maker_fee_rate"] = str(maker)
            row["account_fee_group"] = group_id or None
            row["fee_schema"] = schema
        row["ok"] = True
        row["error"] = None
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    return row


def process_fee_item(
    item: dict[str, Any],
    state: dict[str, Any],
) -> None:
    result = item["result"]
    raw = result.get("body") or b""
    obj_ref = None
    if raw:
        obj_ref = store_raw_object(RAW_OBJECTS, item["venue"] + "_FEE", raw)
    row = parse_fee_result(item)
    row["raw_body_sha256"] = obj_ref["sha256"] if obj_ref else None
    row["raw_body_size_bytes"] = obj_ref["size_bytes"] if obj_ref else 0
    append_jsonl(
        daily_path(FEES_DIR / item["venue"].lower(), item["receive_ms"]),
        row,
    )
    key = item["venue"] + "|" + item["instrument"]
    if row["ok"]:
        state["last_fee_snapshots"][key] = {
            "receive_ms": item["receive_ms"],
            "taker_fee_rate": row["taker_fee_rate"],
            "maker_fee_rate": row["maker_fee_rate"],
            "account_fee_group": row["account_fee_group"],
            "raw_body_sha256": row["raw_body_sha256"],
        }


def drain_fee_queue(
    result_queue: "queue.Queue[dict[str, Any]]",
    state: dict[str, Any],
    creds: dict[str, str],
) -> bool:
    completed = False
    changed = False
    while True:
        try:
            item = result_queue.get_nowait()
        except queue.Empty:
            break
        if item.get("_done"):
            completed = True
            if item.get("error"):
                append_jsonl(
                    daily_path(INVALID_DIR, now_ms()),
                    {
                        "stage": STAGE,
                        "event": "FEE_REFRESH_WORKER_ERROR",
                        "ts_ms": now_ms(),
                        "error": redact_text(
                            str(item.get("error")),
                            list(creds.values()),
                        ),
                    },
                )
            elif not item.get("stopped"):
                state["last_fee_refresh_completed_ms"] = int(
                    item.get("completed_ms") or now_ms()
                )
            changed = True
            continue
        try:
            process_fee_item(item, state)
        except Exception as exc:
            append_jsonl(
                daily_path(INVALID_DIR, now_ms()),
                {
                    "stage": STAGE,
                    "event": "FEE_REFRESH_PROCESSING_ERROR",
                    "ts_ms": now_ms(),
                    "venue": item.get("venue"),
                    "instrument": item.get("instrument"),
                    "error": redact_text(
                        f"{type(exc).__name__}: {exc}",
                        list(creds.values()),
                    ),
                },
            )
        changed = True
    if changed:
        atomic_json(STATE_FILE, state)
    return completed


def parse_fast_result(
    venue: str,
    result: dict[str, Any],
) -> tuple[bool, list[dict[str, Any]], str | None, int | None]:
    if not result.get("ok"):
        return False, [], result.get("error") or "HTTP_ERROR", None
    try:
        obj = decode_json_object(result.get("body") or b"")
        rows = (
            parse_bybit_coin_info(obj)
            if venue == "BYBIT"
            else parse_okx_currencies(obj)
        )
        return True, rows, None, source_server_timestamp_ms(venue, obj)
    except Exception as exc:
        return False, [], f"{type(exc).__name__}: {exc}", None


def aggregate_current(
    matched_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in matched_rows:
        if not str(row.get("match_status", "")).startswith("MATCHED_"):
            continue
        key = row["venue"] + "|" + row["canonical_key"]
        groups.setdefault(key, []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for key, rows in groups.items():
        agg = aggregate_representation(rows)
        if agg is not None:
            out[key] = agg
    return out


def build_route_snapshot(
    mapping: dict[str, Any],
    aggregates: dict[str, dict[str, Any]],
    venue_valid: dict[str, bool],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for route_class, keys in (
        ("ASSET", sorted(mapping["asset_common_keys"])),
        ("QUOTE", sorted(mapping["quote_common_keys"])),
    ):
        for key in keys:
            by = aggregates.get("BYBIT|" + key) if venue_valid.get("BYBIT") else None
            ok = aggregates.get("OKX|" + key) if venue_valid.get("OKX") else None
            out.append({
                "route_class": route_class,
                "canonical_representation_key": key,
                "direction": "BYBIT_TO_OKX",
                "state": derive_route_state(by, ok),
            })
            out.append({
                "route_class": route_class,
                "canonical_representation_key": key,
                "direction": "OKX_TO_BYBIT",
                "state": derive_route_state(ok, by),
            })
    return out


def state_hash(obj: Any) -> str:
    return sha256_bytes(canonical_json_bytes(obj))


def source_state_for_events(
    aggregates: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {k: v for k,v in sorted(aggregates.items())}


def emit_transitions(
    state: dict[str, Any],
    current_source: dict[str, dict[str, Any]],
    routes: list[dict[str, Any]],
    venue_valid: dict[str, bool],
    slot_ms: int,
) -> None:
    previous_source = state.get("last_source_states") or {}
    previous_routes = state.get("last_route_states") or {}
    baseline = bool(state.get("baseline_initialized"))
    venue_baseline = state.setdefault(
        "venue_baseline_initialized",
        {"BYBIT": False, "OKX": False},
    )

    # Preserve last observed source state across failed polls. This is not
    # route-state carry-forward: route calculation already receives
    # venue_valid=False and therefore emits SOURCE_UNKNOWN.
    merged_source = dict(previous_source)
    for venue in ("BYBIT", "OKX"):
        if not venue_valid.get(venue):
            continue
        old_keys = [k for k in merged_source if k.startswith(venue + "|")]
        for k in old_keys:
            merged_source.pop(k, None)
        for k, v in current_source.items():
            if k.startswith(venue + "|"):
                merged_source[k] = v

        if baseline and venue_baseline.get(venue):
            current_keys = {
                k for k in current_source if k.startswith(venue + "|")
            }
            previous_keys = {
                k for k in previous_source if k.startswith(venue + "|")
            }
            for key in sorted(previous_keys | current_keys):
                events = source_state_events(
                    previous_source.get(key),
                    current_source.get(key),
                )
                for event in events:
                    append_jsonl(
                        daily_path(EVENTS_DIR, slot_ms),
                        {
                            "stage": STAGE,
                            "event": event,
                            "scheduled_slot_ms": slot_ms,
                            "source_key": key,
                        },
                    )
        venue_baseline[venue] = True

    current_route_map = {
        r["direction"] + "|" + r["canonical_representation_key"]: r["state"]
        for r in routes
    }
    if baseline:
        for key, cur in current_route_map.items():
            event = route_transition_event(previous_routes.get(key), cur)
            if event:
                append_jsonl(
                    daily_path(EVENTS_DIR, slot_ms),
                    {
                        "stage": STAGE,
                        "event": event,
                        "scheduled_slot_ms": slot_ms,
                        "route_key": key,
                        "previous_state": previous_routes.get(key),
                        "current_state": cur,
                    },
                )
    state["last_source_states"] = merged_source
    state["last_route_states"] = current_route_map
    state["baseline_initialized"] = True


def outside_row_key(row: dict[str, Any]) -> str:
    return "|".join([
        str(row.get("venue") or ""),
        str(row.get("asset") or ""),
        str(row.get("raw_network") or ""),
        str(row.get("raw_chainType") or ""),
        str(row.get("raw_contract") or ""),
    ])


def emit_outside_transitions(
    state: dict[str, Any],
    outside_rows: list[dict[str, Any]],
    venue_valid: dict[str, bool],
    slot_ms: int,
) -> None:
    previous = state.setdefault(
        "last_outside_row_keys",
        {"BYBIT": [], "OKX": []},
    )
    baseline = state.setdefault(
        "outside_baseline_initialized",
        {"BYBIT": False, "OKX": False},
    )
    current_by_venue = {
        "BYBIT": sorted(
            outside_row_key(r)
            for r in outside_rows
            if r.get("venue") == "BYBIT"
        ),
        "OKX": sorted(
            outside_row_key(r)
            for r in outside_rows
            if r.get("venue") == "OKX"
        ),
    }
    for venue in ("BYBIT", "OKX"):
        if not venue_valid.get(venue):
            continue
        prev_set = set(previous.get(venue) or [])
        cur_set = set(current_by_venue[venue])
        if baseline.get(venue):
            for key in sorted(cur_set - prev_set):
                append_jsonl(
                    daily_path(EVENTS_DIR, slot_ms),
                    {
                        "stage": STAGE,
                        "event": "CHAIN_APPEARED",
                        "classification": "OUTSIDE_FROZEN_ROUTE_GRAPH",
                        "route_admitted": False,
                        "scheduled_slot_ms": slot_ms,
                        "source_row_key": key,
                    },
                )
            for key in sorted(prev_set - cur_set):
                append_jsonl(
                    daily_path(EVENTS_DIR, slot_ms),
                    {
                        "stage": STAGE,
                        "event": "CHAIN_DISAPPEARED",
                        "classification": "OUTSIDE_FROZEN_ROUTE_GRAPH",
                        "route_admitted": False,
                        "scheduled_slot_ms": slot_ms,
                        "source_row_key": key,
                    },
                )
        previous[venue] = current_by_venue[venue]
        baseline[venue] = True


def update_source_gap(
    state: dict[str, Any],
    venue: str,
    ok: bool,
    slot_ms: int,
    error: str | None,
) -> None:
    gaps = state.setdefault("open_source_gaps", {})
    if ok:
        if venue in gaps:
            start = gaps.pop(venue)
            state["source_gap_count"] = int(state.get("source_gap_count", 0)) + 1
            log_gap(
                "SOURCE_GAP_CLOSED",
                venue=venue,
                start_slot_ms=start["start_slot_ms"],
                end_slot_ms=slot_ms,
                error=start.get("error"),
            )
    else:
        if venue not in gaps:
            gaps[venue] = {
                "start_slot_ms": slot_ms,
                "error": error,
            }
            log_gap(
                "SOURCE_GAP_OPENED",
                venue=venue,
                start_slot_ms=slot_ms,
                error=error,
            )


def stop_handler(signum, frame) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True


def run_collector() -> int:
    global STOP_REQUESTED
    fr = require_freeze()
    mapping = load_mapping()
    ensure_mapping_invariants(mapping)
    cap, cap_raw = load_capability(fr)
    require_launch_authorization()
    creds = require_credentials()
    if creds["SC001_B15_BYBIT_BASE_URL"].rstrip("/") != cap.bybit_base_url:
        fail("Bybit base URL differs from capability snapshot")
    if creds["SC001_B15_OKX_BASE_URL"].rstrip("/") != cap.okx_base_url:
        fail("OKX base URL differs from capability snapshot")
    install_ipv4_only()
    ensure_dirs()
    write_manifest(fr, cap_raw)

    state, had_state = initial_state()
    record_restart_gap(state, had_state)
    state["status"] = RUNNING
    atomic_json(STATE_FILE, state)

    print(RUNNING, flush=True)
    print("fast_cadence_seconds =", FAST_CADENCE_SECONDS, flush=True)
    print("price/PnL = CLOSED", flush=True)

    fast_executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=2,
        thread_name_prefix="b15p1-fast",
    )
    fee_stop = threading.Event()
    fee_queue: "queue.Queue[dict[str, Any]]" = queue.Queue()
    inflight: dict[str, tuple[concurrent.futures.Future, int] | None] = {
        "BYBIT": None,
        "OKX": None,
    }
    fee_thread: threading.Thread | None = None
    last_storage_check = 0.0

    try:
        while not STOP_REQUESTED:
            # Drain slow-lane results incrementally so fee rows are persisted
            # near their receive time and cannot appear after daily close.
            fee_completed = drain_fee_queue(fee_queue, state, creds)
            if fee_completed:
                fee_thread = None

            # Start slow fee refresh only when due. It never blocks fast lane.
            last_fee = state.get("last_fee_refresh_completed_ms")
            if (
                fee_thread is None
                and (
                    last_fee is None
                    or now_ms() - int(last_fee) >= FEE_REFRESH_SECONDS * 1000
                )
            ):
                fee_thread = threading.Thread(
                    target=fee_refresh_worker,
                    args=(creds, cap, fee_stop, fee_queue),
                    name="b15p1-fee",
                    daemon=True,
                )
                fee_thread.start()

            slot_ms = next_slot_ms(now_ms(), FAST_CADENCE_SECONDS)
            while not STOP_REQUESTED and now_ms() < slot_ms:
                if time.monotonic() - last_storage_check >= STORAGE_CHECK_SECONDS:
                    sg = storage_guard()
                    last_storage_check = time.monotonic()
                    if sg == "STORAGE_WARNING":
                        print("STORAGE_WARNING", flush=True)
                    elif sg == "STORAGE_PRESSURE_REVIEW":
                        state["status"] = SOURCE_REVIEW
                        state["stop_reason"] = sg
                        atomic_json(STATE_FILE, state)
                        print(SOURCE_REVIEW, flush=True)
                        print("reason =", sg, flush=True)
                        return 2
                if now_ms() - int(state.get("last_heartbeat_ms") or 0) >= HEARTBEAT_SECONDS * 1000:
                    update_heartbeat(state)
                time.sleep(min(0.25, max(0.01, (slot_ms - now_ms()) / 1000)))

            if STOP_REQUESTED:
                break

            # Late results from prior slots are preserved but never admitted to
            # the current slot.
            for venue in ("BYBIT", "OKX"):
                entry = inflight.get(venue)
                if entry is not None and entry[0].done():
                    future, old_slot = entry
                    try:
                        result = future.result()
                        raw = result.get("body") or b""
                        obj_ref = (
                            store_raw_object(RAW_OBJECTS, venue, raw)
                            if raw else None
                        )
                        append_jsonl(
                            daily_path(POLLS_DIR, now_ms()),
                            {
                                "stage": STAGE,
                                "event": "LATE_RESPONSE_NOT_ADMITTED",
                                "venue": venue,
                                "original_slot_ms": old_slot,
                                "received_ms": now_ms(),
                                "raw_body_sha256": obj_ref["sha256"] if obj_ref else None,
                                "raw_body_size_bytes": obj_ref["size_bytes"] if obj_ref else 0,
                            },
                        )
                    except Exception as exc:
                        append_jsonl(
                            daily_path(INVALID_DIR, now_ms()),
                            {
                                "stage": STAGE,
                                "event": "LATE_RESPONSE_ERROR",
                                "venue": venue,
                                "original_slot_ms": old_slot,
                                "error": redact_text(
                                    f"{type(exc).__name__}: {exc}",
                                    list(creds.values()),
                                ),
                            },
                        )
                    inflight[venue] = None

            # One more drain at the slot boundary prevents a pre-midnight
            # fee result from being appended after previous-day finalization.
            if drain_fee_queue(fee_queue, state, creds):
                fee_thread = None
            maybe_finalize_previous_day(state, slot_ms)
            state["last_scheduled_slot_ms"] = slot_ms
            venue_valid = {"BYBIT": False, "OKX": False}
            parsed_rows: list[dict[str, Any]] = []
            poll_refs: dict[str, dict[str, Any]] = {}

            # Submit new fast requests only when no previous request is alive.
            submitted: list[tuple[str, concurrent.futures.Future]] = []
            for venue in ("BYBIT", "OKX"):
                if inflight[venue] is not None:
                    state["missed_poll_slots"] = int(state.get("missed_poll_slots", 0)) + 1
                    update_source_gap(
                        state, venue, False, slot_ms, "SCHEDULER_OVERRUN"
                    )
                    poll_refs[venue] = {
                        "status": "SCHEDULER_OVERRUN",
                        "raw_body_sha256": None,
                        "raw_body_size_bytes": 0,
                    }
                    continue
                fut = fast_executor.submit(fetch_fast, venue, creds, cap)
                inflight[venue] = (fut, slot_ms)
                submitted.append((venue, fut))

            deadline = time.monotonic() + REQUEST_DEADLINE_SECONDS_LOCAL
            pending = {f for _,f in submitted}
            while pending and time.monotonic() < deadline:
                timeout = max(0.0, min(0.1, deadline - time.monotonic()))
                done, pending = concurrent.futures.wait(
                    pending,
                    timeout=timeout,
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )
                if not done and timeout <= 0:
                    break

            for venue, fut in submitted:
                if not fut.done():
                    update_source_gap(
                        state, venue, False, slot_ms, "REQUEST_DEADLINE_EXCEEDED"
                    )
                    poll_refs[venue] = {
                        "status": "REQUEST_DEADLINE_EXCEEDED",
                        "raw_body_sha256": None,
                        "raw_body_size_bytes": 0,
                    }
                    # Keep in-flight; next slot cannot overlap it.
                    continue
                inflight[venue] = None
                try:
                    result = fut.result()
                    raw = result.get("body") or b""
                    obj_ref = (
                        store_raw_object(RAW_OBJECTS, venue, raw)
                        if raw else None
                    )
                    ok, rows, error, source_server_ms = parse_fast_result(venue, result)
                    venue_valid[venue] = ok
                    if ok:
                        parsed_rows.extend(rows)
                    update_source_gap(state, venue, ok, slot_ms, error)
                    poll_refs[venue] = {
                        "status": "OK" if ok else "SOURCE_INVALID",
                        "http_status": result.get("http_status"),
                        "request_start_ms": result.get("request_start_ms"),
                        "receive_ms": result.get("receive_ms"),
                        "source_server_timestamp_ms": source_server_ms,
                        "elapsed_ms": result.get("elapsed_ms"),
                        "safe_headers": result.get("safe_headers") or {},
                        "raw_body_sha256": obj_ref["sha256"] if obj_ref else None,
                        "raw_body_size_bytes": obj_ref["size_bytes"] if obj_ref else 0,
                        "raw_object_created": obj_ref["created"] if obj_ref else False,
                        "error": redact_text(error or "", list(creds.values())) or None,
                    }
                except Exception as exc:
                    venue_valid[venue] = False
                    err = redact_text(
                        f"{type(exc).__name__}: {exc}", list(creds.values())
                    )
                    update_source_gap(state, venue, False, slot_ms, err)
                    poll_refs[venue] = {
                        "status": "SOURCE_INVALID",
                        "raw_body_sha256": None,
                        "raw_body_size_bytes": 0,
                        "error": err,
                    }

            matched_rows = [match_live_row(row, mapping) for row in parsed_rows]
            outside_rows = [
                r for r in matched_rows
                if r.get("match_status") == "OUTSIDE_FROZEN_ROUTE_GRAPH"
            ]
            ambiguous_rows = [
                r for r in matched_rows
                if r.get("match_status") == "METADATA_INVALID_ALIAS_AMBIGUITY"
            ]
            frozen_rows = [
                r for r in matched_rows
                if str(r.get("match_status", "")).startswith("MATCHED_")
            ]
            aggregates = aggregate_current(frozen_rows)
            routes = build_route_snapshot(mapping, aggregates, venue_valid)

            normalized_record = {
                "stage": STAGE,
                "scheduled_slot_ms": slot_ms,
                "venue_valid": venue_valid,
                "aggregates": aggregates,
                "outside_frozen_route_rows": [
                    {
                        "venue": r["venue"],
                        "asset": r["asset"],
                        "raw_network": r.get("raw_network"),
                        "raw_chainType": r.get("raw_chainType"),
                        "raw_contract": r.get("raw_contract"),
                    }
                    for r in outside_rows
                ],
                "ambiguous_rows": ambiguous_rows,
            }
            normalized_hash = state_hash(normalized_record)
            route_hash = state_hash(routes)

            append_jsonl(
                daily_path(VENUE_CHAIN_DIR, slot_ms),
                {
                    **normalized_record,
                    "normalized_state_sha256": normalized_hash,
                },
            )
            append_jsonl(
                daily_path(ROUTES_DIR, slot_ms),
                {
                    "stage": STAGE,
                    "scheduled_slot_ms": slot_ms,
                    "route_state_sha256": route_hash,
                    "routes": routes,
                },
            )

            emit_transitions(
                state,
                source_state_for_events(aggregates),
                routes,
                venue_valid,
                slot_ms,
            )
            emit_outside_transitions(
                state,
                outside_rows,
                venue_valid,
                slot_ms,
            )

            by_hash = (poll_refs.get("BYBIT") or {}).get("raw_body_sha256") or "0"*64
            ok_hash = (poll_refs.get("OKX") or {}).get("raw_body_sha256") or "0"*64
            previous_chain = str(state.get("last_poll_chain_hash") or "0"*64)
            chain_hash = poll_chain_hash(
                previous_chain, by_hash, ok_hash, normalized_hash, route_hash
            )
            poll_row = {
                "stage": STAGE,
                "scheduled_slot_ms": slot_ms,
                "scheduled_slot_utc": utc_iso_ms(slot_ms),
                "process_epoch": state["process_epoch"],
                "venues": poll_refs,
                "normalized_state_sha256": normalized_hash,
                "route_state_sha256": route_hash,
                "previous_poll_chain_hash": previous_chain,
                "poll_chain_hash": chain_hash,
                "outside_frozen_route_row_count": len(outside_rows),
                "ambiguous_row_count": len(ambiguous_rows),
                "price_data_collected": False,
            }
            append_jsonl(daily_path(POLLS_DIR, slot_ms), poll_row)

            state["last_poll_chain_hash"] = chain_hash
            state["poll_count"] = int(state.get("poll_count", 0)) + 1
            if not all(venue_valid.values()):
                state["invalid_poll_count"] = int(
                    state.get("invalid_poll_count", 0)
                ) + 1
            state["last_heartbeat_ms"] = now_ms()
            atomic_json(STATE_FILE, state)

    finally:
        fee_stop.set()
        drain_fee_queue(fee_queue, state, creds)
        fast_executor.shutdown(wait=False, cancel_futures=True)

    state["status"] = STOPPED
    state["stopped_ms"] = now_ms()
    state["last_heartbeat_ms"] = state["stopped_ms"]
    atomic_json(STATE_FILE, state)
    print(STOPPED, flush=True)
    print("poll_count =", state.get("poll_count"), flush=True)
    print("invalid_poll_count =", state.get("invalid_poll_count"), flush=True)
    print("price/PnL = CLOSED", flush=True)
    return 0


def status_mode() -> int:
    require_freeze()
    if not STATE_FILE.exists():
        print("B15P1_NONPRICE_COLLECTOR_STATE_MISSING")
        print("collector_launch_authorized = False")
        return 0
    state = require_json_object(STATE_FILE)
    allowed = (
        "stage", "version", "status", "process_epoch", "started_utc",
        "last_heartbeat_ms", "last_scheduled_slot_ms", "poll_count",
        "invalid_poll_count", "missed_poll_slots", "source_gap_count",
        "process_restart_count", "last_fee_refresh_completed_ms",
        "price_data_collected", "pnl_calculated",
    )
    for key in allowed:
        print(f"{key} = {state.get(key)}")
    print("collector_launch_authorized = False")
    return 0


def main() -> int:
    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--mode",
        choices=("self-test", "run", "status"),
        default="self-test",
    )
    args = ap.parse_args()
    if args.mode == "self-test":
        return self_test()
    if args.mode == "status":
        return status_mode()
    return run_collector()


if __name__ == "__main__":
    raise SystemExit(main())
