#!/usr/bin/env python3
"""Fail-closed, metadata-only PIT universe resolver for SC001-X1-002B.

This module never fetches data. It accepts a pre-captured official metadata ledger,
validates its lineage contract, and deterministically builds the frozen pool.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse


SCHEMA = "sc001.x1_pit_universe_metadata_ledger.v0.1"
ATTESTATION = "OFFICIAL_IMMUTABLE_OR_AUDITABLE_COMPLETE"
HASH_PREFIX = "SC001-X1-ATLAS-v0.1|"
CUTOFF = datetime(2026, 10, 1, tzinfo=timezone.utc)
ANCHORS = ("BTCUSDT", "ETHUSDT")
ALLOWED_CLASS = "ORDINARY_CRYPTO"
EXCLUDED_CLASSES = {
    "STABLECOIN_UNDERLYING",
    "LEVERAGED_TOKEN",
    "INDEX_BASKET",
    "DATED_CONTRACT",
    "AMBIGUOUS",
}
TERMINAL_STATES = {"DELIVERED", "CLOSE"}
OFFICIAL_HOSTS = {"www.binance.com", "developers.binance.com"}


class LedgerError(ValueError):
    """A deterministic source or identity gate failed."""


@dataclass(frozen=True)
class Contract:
    symbol: str
    identity: str
    onboard_ms: int
    delist_effective_ms: int | None
    classification: str

    @property
    def order_hash(self) -> str:
        return hashlib.sha256((HASH_PREFIX + self.identity).encode("utf-8")).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LedgerError(message)


def _sha256(value: Any, field: str) -> str:
    _require(isinstance(value, str) and len(value) == 64, f"{field}: invalid SHA256")
    _require(all(c in "0123456789abcdef" for c in value), f"{field}: SHA256 must be lowercase hex")
    return value


def _official_url(value: Any, field: str) -> str:
    _require(isinstance(value, str), f"{field}: URL must be a string")
    parsed = urlparse(value)
    _require(parsed.scheme == "https" and parsed.hostname in OFFICIAL_HOSTS, f"{field}: non-official URL")
    _require(not parsed.username and not parsed.password and not parsed.fragment, f"{field}: unsafe URL")
    return value


def _utc_ms(value: Any, field: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"{field}: invalid epoch ms")
    return value


def _parse_capture(value: Any) -> datetime:
    _require(isinstance(value, str) and value.endswith("Z"), "captured_at_utc: exact UTC string required")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise LedgerError("captured_at_utc: invalid timestamp") from exc
    _require(parsed.tzinfo == timezone.utc, "captured_at_utc: UTC required")
    return parsed


def _contract(record: dict[str, Any]) -> Contract:
    _require(isinstance(record, dict), "record must be an object")
    for key in (
        "venue", "market_type", "contract_type", "symbol", "pair", "base_asset",
        "quote_asset", "margin_asset", "onboard_ms", "multiplier_version",
        "classification", "classification_source_url", "listing_notice_url",
        "listing_notice_sha256", "capture_sha256", "captured_at_utc",
    ):
        _require(key in record, f"record missing {key}")

    _require(record["venue"] == "BINANCE", "venue must be BINANCE")
    _require(record["market_type"] == "USD_M", "market_type must be USD_M")
    _require(record["contract_type"] == "PERPETUAL", "contract_type must be PERPETUAL")
    _require(record["quote_asset"] == "USDT" and record["margin_asset"] == "USDT", "USDT quote/margin required")

    symbol = record["symbol"]
    pair = record["pair"]
    base = record["base_asset"]
    multiplier = record["multiplier_version"]
    for value, field in ((symbol, "symbol"), (pair, "pair"), (base, "base_asset"), (multiplier, "multiplier_version")):
        _require(isinstance(value, str) and value and value == value.upper(), f"{field}: non-empty uppercase required")
    _require(symbol == pair, "symbol/pair mismatch is ambiguous")

    classification = record["classification"]
    _require(classification == ALLOWED_CLASS or classification in EXCLUDED_CLASSES, "unknown classification")
    _official_url(record["classification_source_url"], "classification_source_url")
    _official_url(record["listing_notice_url"], "listing_notice_url")
    _sha256(record["listing_notice_sha256"], "listing_notice_sha256")
    _sha256(record["capture_sha256"], "capture_sha256")
    _parse_capture(record["captured_at_utc"])

    onboard_ms = _utc_ms(record["onboard_ms"], "onboard_ms")
    _require(onboard_ms < int(CUTOFF.timestamp() * 1000), "listing is not before cutoff")

    delist = record.get("delist_effective_ms")
    terminal = record.get("terminal_status")
    if delist is None:
        _require(terminal is None, "terminal status without delist time")
        _require(record.get("delisting_notice_url") is None, "delisting URL without delist time")
        _require(record.get("delisting_notice_sha256") is None, "delisting hash without delist time")
    else:
        delist = _utc_ms(delist, "delist_effective_ms")
        _require(delist > onboard_ms, "delist must follow listing")
        _require(terminal in TERMINAL_STATES, "unqualified terminal state")
        _official_url(record.get("delisting_notice_url"), "delisting_notice_url")
        _sha256(record.get("delisting_notice_sha256"), "delisting_notice_sha256")

    identity = "|".join((
        "BINANCE", "USD_M", "PERPETUAL", symbol, str(onboard_ms), base,
        "USDT", "USDT", multiplier,
    ))
    return Contract(symbol, identity, onboard_ms, delist, classification)


def validate_ledger(payload: dict[str, Any]) -> list[Contract]:
    _require(payload.get("schema") == SCHEMA, "wrong ledger schema")
    _require(payload.get("cutoff_exclusive_utc") == "2026-10-01T00:00:00Z", "wrong cutoff")
    _require(payload.get("completeness_attestation") == ATTESTATION, "SOURCE_STRATEGY_ATTENTION_REQUIRED")
    records = payload.get("records")
    _require(isinstance(records, list) and records, "records must be non-empty")
    contracts = [_contract(record) for record in records]

    identities: set[str] = set()
    by_symbol: dict[str, list[Contract]] = {}
    for contract in contracts:
        _require(contract.identity not in identities, "duplicate contract identity")
        identities.add(contract.identity)
        by_symbol.setdefault(contract.symbol, []).append(contract)

    for symbol, versions in by_symbol.items():
        versions.sort(key=lambda item: item.onboard_ms)
        for prior, current in zip(versions, versions[1:]):
            _require(prior.delist_effective_ms is not None, f"{symbol}: relisting without terminal predecessor")
            _require(prior.delist_effective_ms <= current.onboard_ms, f"{symbol}: overlapping identity epochs")
    return contracts


def build_pool(contracts: list[Contract]) -> dict[str, Any]:
    eligible = [item for item in contracts if item.classification == ALLOWED_CLASS]
    anchors: list[Contract] = []
    cutoff_ms = int(CUTOFF.timestamp() * 1000)
    for symbol in ANCHORS:
        matches = [
            item for item in eligible
            if item.symbol == symbol
            and (item.delist_effective_ms is None or item.delist_effective_ms >= cutoff_ms)
        ]
        _require(len(matches) == 1, f"anchor {symbol}: exactly one cutoff-active qualified identity required")
        anchors.append(matches[0])

    anchor_ids = {item.identity for item in anchors}
    nonanchors = sorted(
        (item for item in eligible if item.identity not in anchor_ids),
        key=lambda item: (item.order_hash, item.identity.encode("utf-8")),
    )[:24]
    _require(len(nonanchors) >= 8, "fewer than eight qualified non-anchors")
    reserve_count = math.ceil(len(nonanchors) / 4)
    discovery = nonanchors[:-reserve_count]
    reserve = nonanchors[-reserve_count:]
    return {
        "anchors": [item.identity for item in anchors],
        "non_anchor_order": [item.identity for item in nonanchors],
        "discovery_pool": [item.identity for item in discovery],
        "node_reserve": [item.identity for item in reserve],
    }


def _month_start(value: str) -> datetime:
    _require(isinstance(value, str) and len(value) == 7 and value[4] == "-", "month must be YYYY-MM")
    year, month = (int(part) for part in value.split("-"))
    _require(1 <= month <= 12, "invalid month")
    return datetime(year, month, 1, tzinfo=timezone.utc)


def month_membership(contracts: list[Contract], pool: dict[str, Any], month: str) -> dict[str, Any]:
    start = _month_start(month)
    _require(start < CUTOFF, "month is not before cutoff")
    by_identity = {item.identity: item for item in contracts}

    def active(identity: str) -> bool:
        item = by_identity[identity]
        listed = datetime.fromtimestamp(item.onboard_ms / 1000, tz=timezone.utc)
        old_enough = listed <= start - timedelta(days=180)
        not_delisted = item.delist_effective_ms is None or item.delist_effective_ms > int(start.timestamp() * 1000)
        return old_enough and not_delisted

    anchors = [identity for identity in pool["anchors"] if active(identity)]
    _require(len(anchors) == 2, f"{month}: both anchors must be eligible")
    discovery = [identity for identity in pool["discovery_pool"] if active(identity)][:10]
    return {"month": month, "anchors": anchors, "discovery": discovery, "active": anchors + discovery}


def resolve(payload: dict[str, Any]) -> dict[str, Any]:
    contracts = validate_ledger(payload)
    pool = build_pool(contracts)
    months = payload.get("months", [])
    _require(isinstance(months, list), "months must be a list")
    memberships = [month_membership(contracts, pool, month) for month in months]
    return {
        "schema": "sc001.x1_pit_universe_resolution.v0.1",
        "status": "PIT_METADATA_RESOLVED",
        "cutoff_exclusive_utc": "2026-10-01T00:00:00Z",
        "pool": pool,
        "memberships": memberships,
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = resolve(payload)
    except (LedgerError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "SOURCE_STRATEGY_ATTENTION_REQUIRED", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

