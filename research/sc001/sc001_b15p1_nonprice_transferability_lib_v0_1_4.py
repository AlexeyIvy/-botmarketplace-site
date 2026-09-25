from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import os
import socket
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

RECV_WINDOW = "5000"
MAX_JSON_BYTES = 20_000_000

BYBIT_COIN_INFO_PATH = "/v5/asset/coin/query-info"
BYBIT_FEE_PATH = "/v5/account/fee-rate"
OKX_CURRENCIES_PATH = "/api/v5/asset/currencies"
OKX_FEE_PATH = "/api/v5/account/trade-fee"

FAST_CADENCE_SECONDS = 15
REQUEST_DEADLINE_SECONDS = 12
FEE_REFRESH_SECONDS = 21600
FEE_STALE_AFTER_SECONDS = 28800

_ORIG_GETADDRINFO = socket.getaddrinfo


class CollectorError(RuntimeError):
    pass


class RawObjectIntegrityError(CollectorError):
    pass


class SafeHTTPError(CollectorError):
    def __init__(self, status: int, url: str, body: bytes):
        self.status = int(status)
        self.url = url
        self.body = bytes(body)
        super().__init__(f"HTTP {status} for {url}")


def fail(msg: str) -> None:
    raise CollectorError(msg)


def now_ms() -> int:
    return time.time_ns() // 1_000_000


def utc_iso_ms(ms: int | None = None) -> str:
    if ms is None:
        dt = datetime.now(timezone.utc)
    else:
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return (
        json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path: Path, obj: Any) -> None:
    atomic_bytes(path, json.dumps(
        obj, ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n")


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (
        json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    with path.open("ab") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())


def store_raw_object(root: Path, venue: str, raw: bytes) -> dict[str, Any]:
    digest = sha256_bytes(raw)
    path = root / venue.lower() / digest[:2] / f"{digest}.bin"
    if path.exists():
        actual = sha256_file(path)
        if actual != digest:
            raise RawObjectIntegrityError(
                f"RAW_OBJECT_INTEGRITY_FAIL venue={venue} expected={digest} actual={actual}"
            )
        return {
            "sha256": digest,
            "size_bytes": len(raw),
            "created": False,
            "path": str(path),
        }
    atomic_bytes(path, raw)
    actual = sha256_file(path)
    if actual != digest:
        raise RawObjectIntegrityError(
            f"RAW_OBJECT_INTEGRITY_FAIL_AFTER_WRITE venue={venue}"
        )
    return {
        "sha256": digest,
        "size_bytes": len(raw),
        "created": True,
        "path": str(path),
    }


def ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    rows = _ORIG_GETADDRINFO(host, port, socket.AF_INET, type, proto, flags)
    if not rows:
        raise CollectorError(f"no IPv4 address resolved for {host}")
    return rows


def install_ipv4_only() -> None:
    socket.getaddrinfo = ipv4_only_getaddrinfo


def decimal_text(value: Any, *, empty_zero: bool = False) -> str | None:
    if value is None or value == "":
        return "0" if empty_zero else None
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal {value!r}") from exc
    if not d.is_finite() or d < 0:
        raise ValueError(f"invalid nonnegative decimal {value!r}")
    out = format(d, "f")
    if "." in out:
        out = out.rstrip("0").rstrip(".")
    return out or "0"


def bybit_withdraw_max_text(value: Any) -> str | None:
    """Normalize Bybit withdrawMax.

    Bybit documents the sentinel -1 as "no limit" for withdrawMax.
    This exception is field-specific. All other negative values remain invalid.
    """
    if value is None or value == "":
        return None
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid Bybit withdrawMax decimal {value!r}") from exc
    if not d.is_finite():
        raise ValueError(f"invalid Bybit withdrawMax decimal {value!r}")
    if d == Decimal("-1"):
        return "UNLIMITED"
    if d < 0:
        raise ValueError(f"invalid Bybit withdrawMax negative value {value!r}")
    return decimal_text(value)


def parse_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"invalid boolean flag {value!r}")


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def safe_header_subset(headers: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in headers.items():
        lk = str(key).lower()
        if any(token in lk for token in ("rate", "limit", "remaining", "reset")):
            out[str(key)] = str(value)
    return out


def http_raw(url: str, headers: dict[str, str], timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=headers)
    request_start_ms = now_ms()
    start = time.monotonic_ns()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_JSON_BYTES + 1)
            status = int(getattr(resp, "status", 200))
            resp_headers = safe_header_subset(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_JSON_BYTES + 1)
        elapsed_ms = (time.monotonic_ns() - start) // 1_000_000
        return {
            "ok": False,
            "request_start_ms": request_start_ms,
            "receive_ms": now_ms(),
            "http_status": int(exc.code),
            "body": raw[: MAX_JSON_BYTES + 1],
            "safe_headers": safe_header_subset(exc.headers or {}),
            "elapsed_ms": int(elapsed_ms),
            "error": f"HTTP_{int(exc.code)}",
        }
    except Exception as exc:
        elapsed_ms = (time.monotonic_ns() - start) // 1_000_000
        return {
            "ok": False,
            "request_start_ms": request_start_ms,
            "receive_ms": now_ms(),
            "http_status": None,
            "body": b"",
            "safe_headers": {},
            "elapsed_ms": int(elapsed_ms),
            "error": f"{type(exc).__name__}: {exc}",
        }
    elapsed_ms = (time.monotonic_ns() - start) // 1_000_000
    if len(raw) > MAX_JSON_BYTES:
        return {
            "ok": False,
            "request_start_ms": request_start_ms,
            "receive_ms": now_ms(),
            "http_status": status,
            "body": raw[:MAX_JSON_BYTES],
            "safe_headers": resp_headers,
            "elapsed_ms": int(elapsed_ms),
            "error": "RESPONSE_CAP_EXCEEDED",
        }
    return {
        "ok": status == 200,
        "request_start_ms": request_start_ms,
        "receive_ms": now_ms(),
        "http_status": status,
        "body": raw,
        "safe_headers": resp_headers,
        "elapsed_ms": int(elapsed_ms),
        "error": None if status == 200 else f"HTTP_{status}",
    }


def decode_json_object(raw: bytes) -> dict[str, Any]:
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("JSON object expected")
    return obj


def source_server_timestamp_ms(venue: str, obj: dict[str, Any]) -> int | None:
    candidates: list[Any] = []
    if venue == "BYBIT":
        candidates.extend([obj.get("time"), obj.get("timeNano")])
    elif venue == "OKX":
        candidates.extend([obj.get("ts")])
    for value in candidates:
        if value in (None, ""):
            continue
        try:
            x = int(str(value))
        except Exception:
            continue
        # Bybit timeNano is nanoseconds; normalize only when clearly ns.
        if x > 10**15:
            x //= 1_000_000
        if x > 0:
            return x
    return None


def bybit_auth_headers(
    api_key: str,
    api_secret: str,
    query: str = "",
    *,
    recv_window: str = RECV_WINDOW,
    timestamp_ms: int | None = None,
) -> dict[str, str]:
    ts = str(timestamp_ms if timestamp_ms is not None else now_ms())
    payload = ts + api_key + recv_window + query
    sig = hmac.new(
        api_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "User-Agent": "BotMarketplace-SC001-B15P1-NonPriceCollector/0.1",
        "Accept": "application/json",
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-TIMESTAMP": ts,
        "X-BAPI-RECV-WINDOW": recv_window,
        "X-BAPI-SIGN": sig,
    }


def okx_auth_headers(
    api_key: str,
    api_secret: str,
    passphrase: str,
    request_path: str,
    *,
    timestamp_iso: str | None = None,
) -> dict[str, str]:
    ts = timestamp_iso or utc_iso_ms()
    prehash = ts + "GET" + request_path
    sig = base64.b64encode(
        hmac.new(
            api_secret.encode("utf-8"),
            prehash.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("ascii")
    return {
        "User-Agent": "BotMarketplace-SC001-B15P1-NonPriceCollector/0.1",
        "Accept": "application/json",
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-SIGN": sig,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": passphrase,
    }


def private_get_bybit(
    base_url: str,
    api_key: str,
    api_secret: str,
    path: str,
    query: str = "",
    timeout: float = REQUEST_DEADLINE_SECONDS,
) -> dict[str, Any]:
    headers = bybit_auth_headers(api_key, api_secret, query)
    url = base_url.rstrip("/") + path + (("?" + query) if query else "")
    return http_raw(url, headers, timeout)


def private_get_okx(
    base_url: str,
    api_key: str,
    api_secret: str,
    passphrase: str,
    path_with_query: str,
    timeout: float = REQUEST_DEADLINE_SECONDS,
) -> dict[str, Any]:
    headers = okx_auth_headers(
        api_key, api_secret, passphrase, path_with_query
    )
    url = base_url.rstrip("/") + path_with_query
    return http_raw(url, headers, timeout)


def parse_bybit_coin_info(obj: dict[str, Any]) -> list[dict[str, Any]]:
    if int(obj.get("retCode", -1)) != 0:
        raise ValueError(
            f"Bybit retCode={obj.get('retCode')} retMsg={obj.get('retMsg')}"
        )
    rows = (obj.get("result") or {}).get("rows") or []
    if not isinstance(rows, list) or not rows:
        raise ValueError("Bybit coin-info rows missing")
    out: list[dict[str, Any]] = []
    required = {
        "chain", "chainType", "chainDeposit", "chainWithdraw", "contractAddress"
    }
    for coin_row in rows:
        if not isinstance(coin_row, dict):
            raise ValueError("Bybit coin row not object")
        asset = clean_text(coin_row.get("coin")).upper()
        if not asset:
            raise ValueError("Bybit coin missing")
        chains = coin_row.get("chains") or []
        if not isinstance(chains, list):
            raise ValueError("Bybit chains not list")
        for ch in chains:
            if not isinstance(ch, dict) or not required.issubset(ch):
                raise ValueError("Bybit chain schema drift")
            dep = parse_flag(ch.get("chainDeposit"))
            wd = parse_flag(ch.get("chainWithdraw"))
            row = {
                "venue": "BYBIT",
                "asset": asset,
                "raw_network": clean_text(ch.get("chain")),
                "raw_chainType": clean_text(ch.get("chainType")),
                "raw_contract": clean_text(ch.get("contractAddress")),
                "deposit_enabled": dep,
                "withdraw_enabled": wd,
                "fixed_withdraw_fee": decimal_text(ch.get("withdrawFee")),
                "percentage_withdraw_fee": decimal_text(
                    ch.get("withdrawPercentageFee"), empty_zero=True
                ),
                "fee_currency": asset,
                "min_withdrawal": decimal_text(ch.get("withdrawMin")),
                "min_deposit": decimal_text(ch.get("depositMin")),
                "max_withdrawal": bybit_withdraw_max_text(ch.get("withdrawMax")),
                "withdrawal_precision": clean_text(ch.get("minAccuracy")) or None,
                "confirmation_metadata": {
                    "confirmation": clean_text(ch.get("confirmation")) or None,
                    "safeConfirmNumber": clean_text(ch.get("safeConfirmNumber")) or None,
                },
                "metadata_valid": True,
            }
            required_cost = (
                row["fixed_withdraw_fee"],
                row["percentage_withdraw_fee"],
                row["min_withdrawal"],
                row["min_deposit"],
            )
            if any(x is None for x in required_cost):
                row["metadata_valid"] = False
            out.append(row)
    return out


def okx_chain_alias(asset: str, chain_full: str) -> str:
    prefix = asset.upper() + "-"
    if chain_full.upper().startswith(prefix):
        return chain_full[len(prefix):]
    return chain_full


def parse_okx_currencies(obj: dict[str, Any]) -> list[dict[str, Any]]:
    if str(obj.get("code")) != "0":
        raise ValueError(f"OKX code={obj.get('code')} msg={obj.get('msg')}")
    rows = obj.get("data") or []
    if not isinstance(rows, list) or not rows:
        raise ValueError("OKX currencies rows missing")

    # Current Get currencies contract: identity/state keys are mandatory.
    # Economic metadata is profiled per row and may fail closed without
    # invalidating the entire source response.
    core_required = {"ccy", "chain", "ctAddr", "canDep", "canWd"}
    profiled_economic_keys = {
        "fee",
        "burningFeeRate",
        "minDep",
        "minWd",
        "maxWd",
        "wdTickSz",
        "minDepArrivalConfirm",
        "minWdUnlockConfirm",
    }
    required_economic_keys = {
        "fee",
        "burningFeeRate",
        "minDep",
        "minWd",
        "wdTickSz",
        "minDepArrivalConfirm",
        "minWdUnlockConfirm",
    }

    out: list[dict[str, Any]] = []
    for src in rows:
        if not isinstance(src, dict) or not core_required.issubset(src):
            raise ValueError("OKX currencies core schema drift")

        asset = clean_text(src.get("ccy")).upper()
        full_chain = clean_text(src.get("chain"))
        if not asset or not full_chain:
            raise ValueError("OKX currencies identity field empty")

        dep = parse_flag(src.get("canDep"))
        wd = parse_flag(src.get("canWd"))

        missing_economic = sorted(
            k for k in required_economic_keys if k not in src
        )

        if "burningFeeRate" not in src:
            burn = None
        else:
            burn_raw = src.get("burningFeeRate")
            if burn_raw == "":
                burn = "0"
            elif burn_raw is None:
                burn = None
            else:
                burn = decimal_text(burn_raw)

        explicit_fee_ccy = clean_text(src.get("feeCcy"))
        fee_ccy = explicit_fee_ccy or asset
        fee_currency_source = (
            "EXPLICIT_FEE_CCY"
            if explicit_fee_ccy
            else "IMPLICIT_WITHDRAWAL_ASSET_GET_CURRENCIES"
        )

        row = {
            "venue": "OKX",
            "asset": asset,
            "raw_network_full": full_chain,
            "raw_network": okx_chain_alias(asset, full_chain),
            "raw_chainType": "",
            "raw_contract": clean_text(src.get("ctAddr")),
            "deposit_enabled": dep,
            "withdraw_enabled": wd,
            "fixed_withdraw_fee": decimal_text(src.get("fee")),
            "percentage_withdraw_fee": burn,
            "fee_currency": fee_ccy,
            "fee_currency_source": fee_currency_source,
            "min_withdrawal": decimal_text(src.get("minWd")),
            "min_deposit": decimal_text(src.get("minDep")),
            "max_withdrawal": decimal_text(src.get("maxWd")),
            "withdrawal_precision": clean_text(src.get("wdTickSz")) or None,
            "confirmation_metadata": {
                "minDepArrivalConfirm": (
                    clean_text(src.get("minDepArrivalConfirm")) or None
                ),
                "minWdUnlockConfirm": (
                    clean_text(src.get("minWdUnlockConfirm")) or None
                ),
            },
            "metadata_missing_fields": missing_economic,
            "metadata_valid": True,
        }

        required_cost_values = (
            row["fixed_withdraw_fee"],
            row["percentage_withdraw_fee"],
            row["min_withdrawal"],
            row["min_deposit"],
            row["withdrawal_precision"],
            row["confirmation_metadata"]["minDepArrivalConfirm"],
            row["confirmation_metadata"]["minWdUnlockConfirm"],
        )
        if missing_economic or any(x is None for x in required_cost_values):
            row["metadata_valid"] = False
            row["metadata_review_status"] = "OKX_ECONOMIC_METADATA_INCOMPLETE"

        if burn not in (None, "0"):
            row["metadata_valid"] = False
            row["metadata_review_status"] = "OKX_BURNING_FEE_FORMULA_REVIEW"

        out.append(row)
    return out

def representation_key(asset: str, network_uid: str, identity: str) -> str:
    return f"{asset}|{network_uid}|{identity}"


def canonicalize_base_contract(
    raw_contract: str, expected_identity: str
) -> str | None:
    raw = clean_text(raw_contract)
    expected = clean_text(expected_identity)
    if expected.startswith("native:"):
        return expected if raw == "" else None
    if (
        len(expected) == 42
        and expected.startswith("0x")
        and all(c in "0123456789abcdefABCDEF" for c in expected[2:])
    ):
        if (
            len(raw) == 42
            and raw.startswith("0x")
            and all(c in "0123456789abcdefABCDEF" for c in raw[2:])
        ):
            return raw.lower()
        return None
    return raw if raw == expected else None


def build_frozen_mapping(
    base_admitted: list[dict[str, Any]],
    final_resolved_rows: list[dict[str, Any]],
    final_asset_dispositions: list[dict[str, Any]],
    final_quote_classification: dict[str, Any],
) -> dict[str, Any]:
    base_assets = {str(x["asset"]) for x in base_admitted}
    overlay_assets = {str(x["asset"]) for x in final_asset_dispositions}
    if base_assets & overlay_assets:
        raise ValueError("base/overlay asset overlap")

    base_bybit: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    base_okx: dict[tuple[str, str], list[dict[str, Any]]] = {}
    base_common: set[str] = set()
    for item in base_admitted:
        asset = str(item["asset"])
        for rep in item.get("representations", []):
            key = representation_key(
                asset, rep["network_uid"], rep["representation_identity"]
            )
            base_common.add(key)
            matcher = {
                "asset": asset,
                "network_uid": rep["network_uid"],
                "representation_identity": rep["representation_identity"],
                "canonical_key": key,
                "identity_kind": rep.get("kind"),
                "scope": "BASE_V0.1",
            }
            bk = (
                asset,
                clean_text(rep.get("bybit_chain")),
                clean_text(rep.get("bybit_chainType")),
            )
            base_bybit.setdefault(bk, []).append(dict(matcher))
            ok = (asset, clean_text(rep.get("okx_chain")))
            base_okx.setdefault(ok, []).append(dict(matcher))

    exact_bybit: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    exact_okx: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in final_resolved_rows:
        asset = str(row.get("asset") or "")
        if asset not in overlay_assets and asset != "USDT":
            continue
        key = representation_key(
            asset, row["network_uid"], row["representation_identity"]
        )
        val = {
            "asset": asset,
            "network_uid": row["network_uid"],
            "representation_identity": row["representation_identity"],
            "canonical_key": key,
            "identity_kind": row.get("identity_kind"),
            "source_rule": row.get("source_rule"),
            "scope": "V0.2.2_EXACT",
        }
        if row.get("venue") == "BYBIT":
            k = (
                asset,
                clean_text(row.get("raw_network")),
                clean_text(row.get("raw_chainType")),
                clean_text(row.get("raw_contract")),
            )
            if k in exact_bybit and exact_bybit[k]["canonical_key"] != key:
                raise ValueError(f"Bybit exact matcher collision: {k}")
            exact_bybit[k] = val
        elif row.get("venue") == "OKX":
            k = (
                asset,
                clean_text(row.get("raw_network")),
                clean_text(row.get("raw_contract")),
            )
            if k in exact_okx and exact_okx[k]["canonical_key"] != key:
                raise ValueError(f"OKX exact matcher collision: {k}")
            exact_okx[k] = val

    overlay_common = {
        k
        for item in final_asset_dispositions
        for k in item.get("common_keys", [])
    }
    asset_common = base_common | overlay_common
    quote_common = set(final_quote_classification.get("common_keys", []))
    quote_one_by = set(
        final_quote_classification.get("known_one_sided_bybit_keys", [])
    )
    quote_one_ok = set(
        final_quote_classification.get("known_one_sided_okx_keys", [])
    )
    if asset_common & quote_common:
        raise ValueError("asset/quote common overlap")
    if quote_common & quote_one_by or quote_common & quote_one_ok:
        raise ValueError("quote common/one-sided overlap")

    return {
        "base_bybit": base_bybit,
        "base_okx": base_okx,
        "exact_bybit": exact_bybit,
        "exact_okx": exact_okx,
        "base_assets": base_assets,
        "overlay_assets": overlay_assets,
        "asset_common_keys": asset_common,
        "quote_common_keys": quote_common,
        "quote_one_sided_bybit_keys": quote_one_by,
        "quote_one_sided_okx_keys": quote_one_ok,
    }


def match_live_row(
    row: dict[str, Any], mapping: dict[str, Any]
) -> dict[str, Any]:
    venue = row["venue"]
    asset = row["asset"]
    if venue == "BYBIT":
        ek = (
            asset,
            row["raw_network"],
            row["raw_chainType"],
            row["raw_contract"],
        )
        exact = mapping["exact_bybit"].get(ek)
        if exact is not None:
            out = dict(row)
            out.update(exact)
            out["match_status"] = "MATCHED_EXACT_V022"
            return out
        bk = (asset, row["raw_network"], row["raw_chainType"])
        candidates = mapping["base_bybit"].get(bk, [])
    else:
        ek = (asset, row["raw_network"], row["raw_contract"])
        exact = mapping["exact_okx"].get(ek)
        if exact is not None:
            out = dict(row)
            out.update(exact)
            out["match_status"] = "MATCHED_EXACT_V022"
            return out
        bk = (asset, row.get("raw_network_full", ""))
        candidates = mapping["base_okx"].get(bk, [])

    matched: list[dict[str, Any]] = []
    for cand in candidates:
        normalized = canonicalize_base_contract(
            row["raw_contract"], cand["representation_identity"]
        )
        if normalized == cand["representation_identity"]:
            matched.append(cand)
    keys = {x["canonical_key"] for x in matched}
    if len(keys) == 1 and matched:
        out = dict(row)
        out.update(matched[0])
        out["match_status"] = "MATCHED_BASE_V01"
        return out
    if len(keys) > 1:
        out = dict(row)
        out["match_status"] = "METADATA_INVALID_ALIAS_AMBIGUITY"
        out["candidate_keys"] = sorted(keys)
        return out
    out = dict(row)
    out["match_status"] = "OUTSIDE_FROZEN_ROUTE_GRAPH"
    return out


def economic_signature(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("deposit_enabled"),
        row.get("withdraw_enabled"),
        row.get("fixed_withdraw_fee"),
        row.get("percentage_withdraw_fee"),
        row.get("fee_currency"),
        row.get("min_withdrawal"),
        row.get("min_deposit"),
        row.get("max_withdrawal"),
        row.get("withdrawal_precision"),
        json.dumps(
            row.get("confirmation_metadata") or {},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        bool(row.get("metadata_valid")),
        row.get("metadata_review_status"),
    )


def aggregate_representation(
    rows: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if not rows:
        return None
    sigs = {economic_signature(r) for r in rows}
    if len(sigs) != 1:
        return {
            "valid": False,
            "status": "METADATA_INVALID_ALIAS_CONFLICT",
            "observation_count": len(rows),
            "raw_networks": sorted(
                {r.get("raw_network_full") or r.get("raw_network") for r in rows}
            ),
        }
    r = rows[0]
    return {
        "valid": bool(r.get("metadata_valid")),
        "status": "OK" if r.get("metadata_valid") else (
            r.get("metadata_review_status") or "METADATA_INVALID"
        ),
        "deposit_enabled": r.get("deposit_enabled"),
        "withdraw_enabled": r.get("withdraw_enabled"),
        "fixed_withdraw_fee": r.get("fixed_withdraw_fee"),
        "percentage_withdraw_fee": r.get("percentage_withdraw_fee"),
        "fee_currency": r.get("fee_currency"),
        "min_withdrawal": r.get("min_withdrawal"),
        "min_deposit": r.get("min_deposit"),
        "max_withdrawal": r.get("max_withdrawal"),
        "withdrawal_precision": r.get("withdrawal_precision"),
        "confirmation_metadata": r.get("confirmation_metadata"),
        "observation_count": len(rows),
        "raw_networks": sorted(
            {r.get("raw_network_full") or r.get("raw_network") for r in rows}
        ),
    }


def derive_route_state(
    source: dict[str, Any] | None,
    destination: dict[str, Any] | None,
) -> str:
    if source is None or destination is None:
        return "SOURCE_UNKNOWN"
    if not source.get("valid") or not destination.get("valid"):
        return "METADATA_INVALID"
    sw = bool(source.get("withdraw_enabled"))
    dd = bool(destination.get("deposit_enabled"))
    if sw and dd:
        return "ACTIVE"
    if not sw and not dd:
        return "BLOCKED_BOTH"
    if not sw:
        return "BLOCKED_SOURCE_WITHDRAWAL"
    return "BLOCKED_DESTINATION_DEPOSIT"


def next_slot_ms(now_ms_value: int, cadence_seconds: int = 15) -> int:
    period = cadence_seconds * 1000
    return (int(now_ms_value) // period + 1) * period


def fee_snapshot_state(age_seconds: int, stale_after_seconds: int = 28800) -> str:
    return "FRESH" if age_seconds <= stale_after_seconds else "FEE_SNAPSHOT_STALE"


def storage_state(
    free_bytes: int,
    free_percent: float,
    *,
    warning_bytes: int,
    warning_percent: float,
    stop_bytes: int,
    stop_percent: float,
) -> str:
    if free_bytes < stop_bytes or free_percent < stop_percent:
        return "STORAGE_PRESSURE_REVIEW"
    if free_bytes < warning_bytes or free_percent < warning_percent:
        return "STORAGE_WARNING"
    return "OK"


def route_transition_event(previous: str | None, current: str) -> str | None:
    if previous is None:
        return None
    if previous == current:
        return None
    if current == "SOURCE_UNKNOWN":
        return "ROUTE_TO_UNKNOWN"
    if previous == "SOURCE_UNKNOWN":
        return "ROUTE_UNKNOWN_TO_OBSERVED"
    if previous == "ACTIVE" and current != "ACTIVE":
        return "ROUTE_ACTIVE_TO_BLOCKED"
    if previous != "ACTIVE" and current == "ACTIVE":
        return "ROUTE_BLOCKED_TO_ACTIVE"
    return None


def source_state_events(
    previous: dict[str, Any] | None,
    current: dict[str, Any] | None,
) -> list[str]:
    if previous is None and current is None:
        return []
    if previous is None and current is not None:
        return ["CHAIN_APPEARED"]
    if previous is not None and current is None:
        return ["CHAIN_DISAPPEARED"]
    assert previous is not None and current is not None
    out: list[str] = []
    for field, off, on in (
        ("deposit_enabled", "DEP_OFF", "DEP_ON"),
        ("withdraw_enabled", "WD_OFF", "WD_ON"),
    ):
        pv = previous.get(field)
        cv = current.get(field)
        if pv is not cv:
            out.append(on if cv else off)
    if previous.get("valid") and not current.get("valid"):
        out.append("SOURCE_INVALID")
    elif not previous.get("valid") and current.get("valid"):
        out.append("SOURCE_RECOVERED")
    for field, event in (
        ("fixed_withdraw_fee", "WITHDRAW_FIXED_FEE_CHANGED"),
        ("percentage_withdraw_fee", "WITHDRAW_PERCENTAGE_FEE_CHANGED"),
        ("min_withdrawal", "MIN_WITHDRAW_CHANGED"),
        ("min_deposit", "MIN_DEPOSIT_CHANGED"),
        ("max_withdrawal", "MAX_WITHDRAW_CHANGED"),
        ("fee_currency", "FEE_CURRENCY_CHANGED"),
        ("confirmation_metadata", "CONFIRMATION_METADATA_CHANGED"),
    ):
        if previous.get(field) != current.get(field):
            out.append(event)
    return out


def poll_chain_hash(
    previous_hash: str,
    bybit_raw_hash: str,
    okx_raw_hash: str,
    normalized_hash: str,
    route_hash: str,
) -> str:
    payload = "|".join(
        [previous_hash, bybit_raw_hash, okx_raw_hash, normalized_hash, route_hash]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def redact_text(text: str, secret_values: list[str]) -> str:
    out = str(text)
    for secret in sorted(
        {x for x in secret_values if x}, key=len, reverse=True
    ):
        out = out.replace(secret, "<REDACTED>")
    return out


def forbidden_price_endpoint_fragments() -> list[str]:
    return [
        "/v5/" + "market/tickers",
        "/v5/" + "market/orderbook",
        "/api/v5/" + "market/tickers",
        "/api/v5/" + "market/books",
        "/api/v5/" + "market/candles",
    ]


def static_no_price_endpoint_guard(source_texts: list[str]) -> None:
    merged = "\n".join(source_texts)
    for fragment in forbidden_price_endpoint_fragments():
        if fragment in merged:
            raise CollectorError(f"forbidden endpoint present: {fragment}")
    websocket_prefix = "wss" + "://"
    if websocket_prefix in merged:
        raise CollectorError("unexpected websocket endpoint in non-price REST collector")


@dataclass
class CapabilitySnapshot:
    bybit_base_url: str
    okx_base_url: str
    qualified_pairs_bybit: list[str]
    qualified_pairs_okx: list[str]
    okx_group_id_by_instrument: dict[str, str]


def validate_capability_snapshot(
    snapshot: dict[str, Any],
    *,
    runner_sha256: str,
    freeze_sha256: str,
    route_graph_sha256: str,
) -> CapabilitySnapshot:
    if snapshot.get("status") != "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS":
        raise CollectorError("capability snapshot status mismatch")
    anchors = snapshot.get("anchors") or {}
    expected = {
        "runner_sha256": runner_sha256,
        "implementation_freeze_sha256": freeze_sha256,
        "route_graph_sha256": route_graph_sha256,
    }
    for key, value in expected.items():
        if anchors.get(key) != value:
            raise CollectorError(f"capability anchor mismatch: {key}")

    perms = snapshot.get("permissions") or {}
    if perms.get("bybit_readOnly") != 1:
        raise CollectorError("Bybit capability not read-only")
    if perms.get("bybit_withdraw_token_present") is not False:
        raise CollectorError("Bybit Withdraw permission present")
    if perms.get("okx_permission") != "read_only":
        raise CollectorError("OKX capability not exactly read_only")
    if snapshot.get("source_endpoints_pass") is not True:
        raise CollectorError("source endpoint capability not PASS")

    pairs = snapshot.get("qualified_pairs") or {}
    bybit_pairs = [str(x) for x in pairs.get("BYBIT", [])]
    okx_pairs = [str(x) for x in pairs.get("OKX", [])]
    if not bybit_pairs or not okx_pairs:
        raise CollectorError("qualified pair list empty")

    metadata = snapshot.get("qualified_pair_metadata") or {}
    okx_meta = metadata.get("OKX") or {}
    group_map: dict[str, str] = {}
    for inst in okx_pairs:
        row = okx_meta.get(inst) or {}
        gid = str(row.get("groupId") or "")
        if gid:
            group_map[inst] = gid

    return CapabilitySnapshot(
        bybit_base_url=str(snapshot.get("bybit_base_url") or "").rstrip("/"),
        okx_base_url=str(snapshot.get("okx_base_url") or "").rstrip("/"),
        qualified_pairs_bybit=bybit_pairs,
        qualified_pairs_okx=okx_pairs,
        okx_group_id_by_instrument=group_map,
    )

