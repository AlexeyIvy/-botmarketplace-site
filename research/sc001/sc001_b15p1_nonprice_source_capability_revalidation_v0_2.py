from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import shlex
import socket
import stat
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE = "SC001-B15P1-NONPRICE-SOURCE-CAPABILITY-REVALIDATION-V0.2"
PASS = "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS"
REVIEW = "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_REVIEW"
SELFTEST_PASS = "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_V02_SELF_TEST_PASS"
SELFTEST_REVIEW = "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_V02_SELF_TEST_REVIEW"

ROOT = Path(
    os.environ.get(
        "B15P1_REPO_ROOT",
        str(Path(__file__).resolve().parents[2]),
    )
).resolve()

PROTOCOL = ROOT / "docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-v0.2.md"
SPEC = ROOT / "docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-spec-v0.2.json"
FREEZE = ROOT / "docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-freeze-v0.2.json"

RUNNER = ROOT / "research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_3.py"
IMPLEMENTATION_FREEZE = ROOT / "docs/research/sc001-b15-p1-nonprice-collector-implementation-freeze-v0.1.3.json"
SERVICE = ROOT / "ops/systemd/sc001-b15p1-transferability-v0.1.3.service"
ROUTE_SHARD_INDEX = ROOT / "docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/directed_route_graph.v0.2.2.shard-index.json"
ADMITTED = ROOT / "docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/ADMITTED.v0.2.2.json"

ENV_FILE = Path("/home/botmarket/.config/sc001/b15-p1.env")
OUTPUT_FILE = Path(
    os.environ.get(
        "B15P1_CAPABILITY_SNAPSHOT",
        "/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/source_capability_snapshot.json",
    )
).expanduser().resolve()
SAFE_SUMMARY_FILE = OUTPUT_FILE.with_name("source_capability_safe_summary.json")

RECV_WINDOW = "5000"
TIMEOUT = 30
MAX_JSON = 20_000_000
MAX_CLOCK_SKEW_MS = 10_000
EXPECTED_ADMITTED = 192

BYBIT_PUBLIC_TIME = "/v5/market/time"
BYBIT_PUBLIC_INSTRUMENTS = "/v5/market/instruments-info"
BYBIT_PERMISSION = "/v5/user/query-api"
BYBIT_COIN_INFO = "/v5/asset/coin/query-info"
BYBIT_FEE = "/v5/account/fee-rate"

OKX_PUBLIC_TIME = "/api/v5/public/time"
OKX_PUBLIC_INSTRUMENTS = "/api/v5/public/instruments"
OKX_PERMISSION = "/api/v5/account/config"
OKX_CURRENCIES = "/api/v5/asset/currencies"
OKX_FEE = "/api/v5/account/trade-fee"

_ORIG_GETADDRINFO = socket.getaddrinfo


class CapabilityError(RuntimeError):
    pass


def fail(msg: str) -> None:
    raise CapabilityError(msg)


def now_ms() -> int:
    return time.time_ns() // 1_000_000


def utc_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require_object(path: Path) -> dict[str, Any]:
    obj = load_json(path)
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def require_list(path: Path) -> list[Any]:
    obj = load_json(path)
    if not isinstance(obj, list):
        fail(f"JSON list expected: {path}")
    return obj


def atomic_json(path: Path, obj: Any, mode: int = 0o640) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    raw = (
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def parse_env(path: Path) -> dict[str, str]:
    if not path.exists():
        fail(f"credential file missing: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o600:
        fail(f"credential file mode must be 0600, got {oct(mode)}")
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            fail("malformed credential env line")
        k, v = line.split("=", 1)
        parts = shlex.split(v, posix=True)
        if len(parts) != 1:
            fail(f"malformed credential value for {k}")
        out[k] = parts[0]
    required = (
        "SC001_B15_OKX_API_KEY",
        "SC001_B15_OKX_API_SECRET",
        "SC001_B15_OKX_PASSPHRASE",
        "SC001_B15_OKX_BASE_URL",
        "SC001_B15_BYBIT_API_KEY",
        "SC001_B15_BYBIT_API_SECRET",
        "SC001_B15_BYBIT_BASE_URL",
    )
    missing = [k for k in required if not out.get(k)]
    if missing:
        fail("missing credential variables: " + ",".join(missing))
    return out


def ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    rows = _ORIG_GETADDRINFO(
        host, port, socket.AF_INET, type, proto, flags
    )
    if not rows:
        fail(f"no IPv4 address resolved for {host}")
    return rows


def install_ipv4_only() -> None:
    socket.getaddrinfo = ipv4_only_getaddrinfo


def safe_header_subset(headers: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in headers.items():
        lk = str(key).lower()
        if any(x in lk for x in ("rate", "limit", "remaining", "reset")):
            out[str(key)] = str(value)
    return out


def http_raw(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = TIMEOUT,
) -> dict[str, Any]:
    request_start_ms = now_ms()
    req = urllib.request.Request(
        url,
        headers=headers or {
            "User-Agent": "BotMarketplace-SC001-B15P1-Capability/0.1",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_JSON + 1)
            status = int(getattr(resp, "status", 200))
            hdr = safe_header_subset(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_JSON + 1)
        return {
            "ok": False,
            "http_status": int(exc.code),
            "body": raw[:MAX_JSON],
            "safe_headers": safe_header_subset(exc.headers or {}),
            "request_start_ms": request_start_ms,
            "receive_ms": now_ms(),
            "error": f"HTTP_{int(exc.code)}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "http_status": None,
            "body": b"",
            "safe_headers": {},
            "request_start_ms": request_start_ms,
            "receive_ms": now_ms(),
            "error": f"{type(exc).__name__}: {exc}",
        }
    if len(raw) > MAX_JSON:
        return {
            "ok": False,
            "http_status": status,
            "body": raw[:MAX_JSON],
            "safe_headers": hdr,
            "request_start_ms": request_start_ms,
            "receive_ms": now_ms(),
            "error": "RESPONSE_CAP_EXCEEDED",
        }
    return {
        "ok": status == 200,
        "http_status": status,
        "body": raw,
        "safe_headers": hdr,
        "request_start_ms": request_start_ms,
        "receive_ms": now_ms(),
        "error": None if status == 200 else f"HTTP_{status}",
    }


def decode_json_object(result: dict[str, Any], label: str) -> dict[str, Any]:
    if not result.get("ok"):
        fail(f"{label} HTTP/API transport failed: {result.get('error')}")
    try:
        obj = json.loads((result.get("body") or b"").decode("utf-8"))
    except Exception as exc:
        fail(f"{label} invalid JSON: {exc}")
    if not isinstance(obj, dict):
        fail(f"{label} JSON object expected")
    return obj


def public_get(base: str, path_with_query: str) -> dict[str, Any]:
    return http_raw(
        base.rstrip("/") + path_with_query,
        headers={
            "User-Agent": "BotMarketplace-SC001-B15P1-Capability/0.1",
            "Accept": "application/json",
        },
    )


def bybit_headers(
    api_key: str,
    api_secret: str,
    query: str = "",
    *,
    timestamp_ms: int | None = None,
) -> dict[str, str]:
    ts = str(timestamp_ms if timestamp_ms is not None else now_ms())
    payload = ts + api_key + RECV_WINDOW + query
    sig = hmac.new(
        api_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "User-Agent": "BotMarketplace-SC001-B15P1-Capability/0.1",
        "Accept": "application/json",
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-TIMESTAMP": ts,
        "X-BAPI-RECV-WINDOW": RECV_WINDOW,
        "X-BAPI-SIGN": sig,
    }


def okx_headers(
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
        "User-Agent": "BotMarketplace-SC001-B15P1-Capability/0.1",
        "Accept": "application/json",
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-SIGN": sig,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": passphrase,
    }


def bybit_private(
    base: str,
    key: str,
    secret: str,
    path: str,
    query: str = "",
) -> dict[str, Any]:
    url = base.rstrip("/") + path + (("?" + query) if query else "")
    return http_raw(url, bybit_headers(key, secret, query))


def okx_private(
    base: str,
    key: str,
    secret: str,
    passphrase: str,
    path_with_query: str,
) -> dict[str, Any]:
    url = base.rstrip("/") + path_with_query
    return http_raw(
        url,
        okx_headers(key, secret, passphrase, path_with_query),
    )


def require_freeze() -> dict[str, Any]:
    fr = require_object(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_V02":
        fail("capability freeze status mismatch")
    expected = {
        "probe_sha256": sha256_file(Path(__file__).resolve()),
        "protocol_sha256": sha256_file(PROTOCOL),
        "spec_sha256": sha256_file(SPEC),
        "collector_runner_sha256": sha256_file(RUNNER),
        "collector_implementation_freeze_sha256": sha256_file(IMPLEMENTATION_FREEZE),
        "collector_service_file_sha256": sha256_file(SERVICE),
        "route_shard_index_sha256": sha256_file(ROUTE_SHARD_INDEX),
        "admitted_universe_sha256": sha256_file(ADMITTED),
    }
    for key, value in expected.items():
        if fr.get(key) != value:
            fail(f"capability freeze hash mismatch: {key}")
    if fr.get("collector_launch_authorized") is not False:
        fail("capability freeze launch firewall mismatch")
    if fr.get("price_data_authorized") is not False:
        fail("capability freeze price firewall mismatch")
    return fr


def admitted_assets() -> list[str]:
    rows = require_list(ADMITTED)
    assets = sorted({str(x.get("asset") or "") for x in rows if x.get("asset")})
    if len(assets) != EXPECTED_ADMITTED:
        fail(f"admitted asset count mismatch: {len(assets)}")
    return assets


def bybit_server_time_ms(base: str) -> int:
    obj = decode_json_object(
        public_get(base, BYBIT_PUBLIC_TIME),
        "Bybit public time",
    )
    if int(obj.get("retCode", -1)) != 0:
        fail(f"Bybit public time retCode={obj.get('retCode')}")
    return int(obj.get("time"))


def okx_server_time_ms(base: str) -> int:
    obj = decode_json_object(
        public_get(base, OKX_PUBLIC_TIME),
        "OKX public time",
    )
    if str(obj.get("code")) != "0":
        fail(f"OKX public time code={obj.get('code')}")
    data = obj.get("data") or []
    if len(data) != 1:
        fail("OKX public time row mismatch")
    return int(str(data[0].get("ts")))


def validate_bybit_permission(obj: dict[str, Any]) -> dict[str, Any]:
    if int(obj.get("retCode", -1)) != 0:
        fail(f"Bybit query-api retCode={obj.get('retCode')} msg={obj.get('retMsg')}")
    result = obj.get("result") or {}
    readonly = int(result.get("readOnly", -1))
    if readonly != 1:
        fail(f"Bybit key is not read-only: readOnly={readonly}")
    permissions = result.get("permissions") or {}
    if not isinstance(permissions, dict):
        fail("Bybit permissions object missing")
    wallet = permissions.get("Wallet") or []
    withdraw_present = "Withdraw" in wallet
    if withdraw_present:
        fail("Bybit Withdraw permission token present")
    ip_bound = bool(result.get("ips") or [])
    if not ip_bound:
        fail("Bybit key is not IP-bound")
    return {
        "readOnly": readonly,
        "withdraw_token_present": False,
        "ip_bound": True,
        "permission_categories": sorted(str(x) for x in permissions.keys()),
    }


def validate_okx_permission(obj: dict[str, Any]) -> dict[str, Any]:
    if str(obj.get("code")) != "0":
        fail(f"OKX account/config code={obj.get('code')} msg={obj.get('msg')}")
    data = obj.get("data") or []
    if len(data) != 1:
        fail("OKX account config row mismatch")
    row = data[0]
    perm_text = str(row.get("perm") or "")
    perms = {x.strip() for x in perm_text.split(",") if x.strip()}
    if perms != {"read_only"}:
        fail(f"OKX permission is not exactly read_only: {sorted(perms)}")
    ip_bound = bool(str(row.get("ip") or "").strip())
    if not ip_bound:
        fail("OKX key is not IP-bound")
    return {
        "permission": "read_only",
        "ip_bound": True,
    }


def validate_bybit_coin_info(obj: dict[str, Any]) -> dict[str, int]:
    if int(obj.get("retCode", -1)) != 0:
        fail(f"Bybit coin-info retCode={obj.get('retCode')} msg={obj.get('retMsg')}")
    rows = (obj.get("result") or {}).get("rows") or []
    if not isinstance(rows, list) or not rows:
        fail("Bybit coin-info rows missing")
    required = {
        "chain",
        "chainType",
        "chainDeposit",
        "chainWithdraw",
        "contractAddress",
        "withdrawFee",
        "withdrawPercentageFee",
        "depositMin",
        "withdrawMin",
        "withdrawMax",
        "minAccuracy",
        "confirmation",
        "safeConfirmNumber",
    }
    chain_rows = 0
    bad = 0
    for coin in rows:
        if not isinstance(coin, dict) or not str(coin.get("coin") or ""):
            bad += 1
            continue
        chains = coin.get("chains") or []
        if not isinstance(chains, list):
            bad += 1
            continue
        for ch in chains:
            chain_rows += 1
            if not isinstance(ch, dict) or not required.issubset(ch.keys()):
                bad += 1
    if chain_rows <= 0 or bad:
        fail(f"Bybit coin-info schema invalid: chain_rows={chain_rows} bad={bad}")
    return {"coin_rows": len(rows), "chain_rows": chain_rows}


def validate_okx_currencies(obj: dict[str, Any]) -> dict[str, Any]:
    if str(obj.get("code")) != "0":
        fail(f"OKX currencies code={obj.get('code')} msg={obj.get('msg')}")
    rows = obj.get("data") or []
    if not isinstance(rows, list) or not rows:
        fail("OKX currencies rows missing")

    core_required = {"ccy", "chain", "ctAddr", "canDep", "canWd"}
    profiled_fields = [
        "fee",
        "feeCcy",
        "burningFeeRate",
        "minDep",
        "minWd",
        "maxWd",
        "wdTickSz",
        "minDepArrivalConfirm",
        "minWdUnlockConfirm",
    ]
    economic_required = {
        "fee",
        "burningFeeRate",
        "minDep",
        "minWd",
        "wdTickSz",
        "minDepArrivalConfirm",
        "minWdUnlockConfirm",
    }

    core_bad = 0
    economic_complete = 0
    present_counts = {field: 0 for field in profiled_fields}

    for row in rows:
        if not isinstance(row, dict):
            core_bad += 1
            continue
        if not core_required.issubset(row.keys()):
            core_bad += 1
            continue
        if not str(row.get("ccy") or "").strip():
            core_bad += 1
            continue
        if not str(row.get("chain") or "").strip():
            core_bad += 1
            continue

        for field in profiled_fields:
            if field in row:
                present_counts[field] += 1
        if economic_required.issubset(row.keys()):
            economic_complete += 1

    if core_bad:
        fail(f"OKX currencies core schema invalid in {core_bad} rows")
    if economic_complete <= 0:
        fail("OKX currencies has no economically complete source row")

    return {
        "currency_chain_rows": len(rows),
        "core_valid_rows": len(rows),
        "economic_complete_rows": economic_complete,
        "field_presence_counts": present_counts,
        "feeCcy_presence_mode": (
            "NONE"
            if present_counts["feeCcy"] == 0
            else "ALL"
            if present_counts["feeCcy"] == len(rows)
            else "PARTIAL"
        ),
    }

def bybit_live_usdt_spot_pairs(base: str) -> dict[str, str]:
    query = urllib.parse.urlencode({"category": "spot"})
    obj = decode_json_object(
        public_get(base, BYBIT_PUBLIC_INSTRUMENTS + "?" + query),
        "Bybit spot instruments",
    )
    if int(obj.get("retCode", -1)) != 0:
        fail(f"Bybit instruments retCode={obj.get('retCode')}")
    result = obj.get("result") or {}
    rows = result.get("list") or []
    if not isinstance(rows, list):
        fail("Bybit instruments list missing")

    mapping: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("quoteCoin") or "") != "USDT":
            continue
        if str(row.get("status") or "") != "Trading":
            continue
        asset = str(row.get("baseCoin") or "")
        symbol = str(row.get("symbol") or "")
        if not asset or not symbol:
            continue
        if asset in mapping and mapping[asset] != symbol:
            fail(f"Bybit duplicate live USDT pair for {asset}")
        mapping[asset] = symbol
    return mapping

def okx_live_usdt_spot_pairs(base: str) -> dict[str, dict[str, str]]:
    query = urllib.parse.urlencode({"instType": "SPOT"})
    obj = decode_json_object(
        public_get(base, OKX_PUBLIC_INSTRUMENTS + "?" + query),
        "OKX spot instruments",
    )
    if str(obj.get("code")) != "0":
        fail(f"OKX instruments code={obj.get('code')} msg={obj.get('msg')}")
    rows = obj.get("data") or []
    if not isinstance(rows, list):
        fail("OKX instruments data missing")

    mapping: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("quoteCcy") or "") != "USDT":
            continue
        if str(row.get("state") or "") != "live":
            continue
        asset = str(row.get("baseCcy") or "")
        inst = str(row.get("instId") or "")
        group_id = str(row.get("groupId") or "")
        if not asset or not inst:
            continue
        current = {"instId": inst, "groupId": group_id}
        if asset in mapping and mapping[asset] != current:
            fail(f"OKX duplicate live USDT pair for {asset}")
        mapping[asset] = current
    return mapping

def qualify_pairs(
    assets: list[str],
    bybit_map: dict[str, str],
    okx_map: dict[str, dict[str, str]],
) -> dict[str, Any]:
    frozen = set(assets)
    by = {a: bybit_map[a] for a in sorted(frozen & set(bybit_map))}
    ok = {a: okx_map[a] for a in sorted(frozen & set(okx_map))}
    both_assets = sorted(set(by) & set(ok))
    if not both_assets:
        fail("no frozen admitted asset has a live USDT spot pair on both venues")

    ok_pairs = [ok[a]["instId"] for a in sorted(ok)]
    ok_meta = {
        ok[a]["instId"]: {
            "asset": a,
            "groupId": ok[a].get("groupId", ""),
        }
        for a in sorted(ok)
    }

    return {
        "BYBIT": [by[a] for a in sorted(by)],
        "OKX": ok_pairs,
        "bybit_by_asset": by,
        "okx_by_asset": {a: ok[a]["instId"] for a in sorted(ok)},
        "okx_metadata_by_instrument": ok_meta,
        "both_assets": both_assets,
        "missing_bybit_assets": sorted(frozen - set(by)),
        "missing_okx_assets": sorted(frozen - set(ok)),
    }

def bybit_fee_probe(
    base: str,
    key: str,
    secret: str,
    symbol: str,
) -> dict[str, Any]:
    query = urllib.parse.urlencode({"category": "spot", "symbol": symbol})
    obj = decode_json_object(
        bybit_private(base, key, secret, BYBIT_FEE, query),
        "Bybit fee probe",
    )
    if int(obj.get("retCode", -1)) != 0:
        fail(f"Bybit fee probe retCode={obj.get('retCode')} msg={obj.get('retMsg')}")
    rows = (obj.get("result") or {}).get("list") or []
    exact = [r for r in rows if str(r.get("symbol") or "") == symbol]
    if len(exact) != 1:
        fail("Bybit exact fee row mismatch")
    row = exact[0]
    if row.get("takerFeeRate") in (None, "") or row.get("makerFeeRate") in (None, ""):
        fail("Bybit fee fields missing")
    return {
        "instrument": symbol,
        "taker_fee_field_present": True,
        "maker_fee_field_present": True,
    }


def parse_okx_fee_response(
    obj: dict[str, Any],
    inst_id: str,
    expected_group_id: str,
) -> dict[str, Any]:
    if str(obj.get("code")) != "0":
        fail(f"OKX fee probe code={obj.get('code')} msg={obj.get('msg')}")
    rows = obj.get("data") or []
    if len(rows) != 1:
        fail("OKX fee probe row mismatch")

    row = rows[0]
    fee_groups = row.get("feeGroup") or []
    selected = None

    if isinstance(fee_groups, list) and fee_groups:
        if expected_group_id:
            exact = [
                g for g in fee_groups
                if isinstance(g, dict)
                and str(g.get("groupId") or "") == expected_group_id
            ]
            if len(exact) != 1:
                fail(
                    "OKX feeGroup exact group mismatch "
                    f"expected={expected_group_id}"
                )
            selected = exact[0]
        elif len(fee_groups) == 1 and isinstance(fee_groups[0], dict):
            selected = fee_groups[0]
        else:
            fail("OKX feeGroup ambiguous without instrument groupId")
        schema = "FEE_GROUP"
        taker = selected.get("taker")
        maker = selected.get("maker")
        group_id = str(selected.get("groupId") or expected_group_id)
    else:
        taker = row.get("taker")
        maker = row.get("maker")
        group_id = expected_group_id
        schema = "DEPRECATED_TOP_LEVEL"

    if taker in (None, "") or maker in (None, ""):
        fail("OKX fee fields missing")

    return {
        "instrument": inst_id,
        "groupId": group_id,
        "fee_schema": schema,
        "taker_fee_field_present": True,
        "maker_fee_field_present": True,
    }


def okx_fee_probe(
    base: str,
    key: str,
    secret: str,
    passphrase: str,
    inst_id: str,
    expected_group_id: str,
) -> dict[str, Any]:
    query = urllib.parse.urlencode({"instType": "SPOT", "instId": inst_id})
    obj = decode_json_object(
        okx_private(base, key, secret, passphrase, OKX_FEE + "?" + query),
        "OKX fee probe",
    )
    return parse_okx_fee_response(obj, inst_id, expected_group_id)

def forbidden_endpoint_markers() -> list[str]:
    return [
        "/v5/" + "market/tickers",
        "/v5/" + "market/orderbook",
        "/v5/" + "market/kline",
        "/api/v5/" + "market/tickers",
        "/api/v5/" + "market/books",
        "/api/v5/" + "market/candles",
        "/v5/" + "order/create",
        "/api/v5/" + "trade/order",
        "/v5/" + "asset/withdraw/create",
        "/api/v5/" + "asset/withdrawal",
    ]


def static_firewall_guard() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    for marker in forbidden_endpoint_markers():
        if marker in text:
            fail(f"forbidden endpoint literal present: {marker}")


def build_snapshot_fixture(
    runner_sha: str,
    implementation_freeze_sha: str,
    route_graph_sha: str,
) -> dict[str, Any]:
    return {
        "schema": "sc001.b15.p1_nonprice_source_capability_snapshot.v0.2",
        "status": PASS,
        "generated_utc": utc_iso_ms(),
        "anchors": {
            "runner_sha256": runner_sha,
            "implementation_freeze_sha256": implementation_freeze_sha,
            "route_graph_sha256": route_graph_sha,
        },
        "permissions": {
            "bybit_readOnly": 1,
            "bybit_withdraw_token_present": False,
            "bybit_ip_bound": True,
            "okx_permission": "read_only",
            "okx_ip_bound": True,
        },
        "source_endpoints_pass": True,
        "bybit_base_url": "https://api.bybit.com",
        "okx_base_url": "https://openapi.okx.com",
        "qualified_pairs": {
            "BYBIT": ["BTCUSDT"],
            "OKX": ["BTC-USDT"],
        },
        "qualified_pair_metadata": {
            "OKX": {
                "BTC-USDT": {"asset": "BTC", "groupId": "1"}
            }
        },
        "pair_coverage": {
            "frozen_admitted_assets": EXPECTED_ADMITTED,
            "both_venues_assets": ["BTC"],
        },
        "price_data_used": False,
        "pnl_data_used": False,
        "collector_launch_authorized": False,
        "live_execution_authorized": False,
    }


def validate_snapshot_contract(obj: dict[str, Any]) -> None:
    if obj.get("status") != PASS:
        fail("snapshot status mismatch")
    anchors = obj.get("anchors") or {}
    for key in (
        "runner_sha256",
        "implementation_freeze_sha256",
        "route_graph_sha256",
    ):
        value = str(anchors.get(key) or "")
        if len(value) != 64:
            fail(f"snapshot anchor invalid: {key}")
    perms = obj.get("permissions") or {}
    if perms.get("bybit_readOnly") != 1:
        fail("snapshot Bybit readOnly mismatch")
    if perms.get("bybit_withdraw_token_present") is not False:
        fail("snapshot Bybit Withdraw mismatch")
    if perms.get("okx_permission") != "read_only":
        fail("snapshot OKX permission mismatch")
    if obj.get("source_endpoints_pass") is not True:
        fail("snapshot source endpoint mismatch")
    pairs = obj.get("qualified_pairs") or {}
    if not pairs.get("BYBIT") or not pairs.get("OKX"):
        fail("snapshot qualified pairs empty")
    metadata = obj.get("qualified_pair_metadata") or {}
    okx_meta = metadata.get("OKX") or {}
    missing_meta = [
        inst for inst in pairs.get("OKX", [])
        if inst not in okx_meta
    ]
    if missing_meta:
        fail(
            "snapshot OKX pair metadata missing for: "
            + ",".join(missing_meta[:10])
        )
    if obj.get("price_data_used") is not False:
        fail("snapshot price firewall mismatch")
    if obj.get("collector_launch_authorized") is not False:
        fail("snapshot launch firewall mismatch")


def write_selftest_manifest(status: str, error: str | None = None) -> None:
    out_dir = Path("/work/run/output")
    if not out_dir.exists():
        return
    atomic_json(
        out_dir / "capability_revalidation_self_test_manifest.json",
        {
            "schema": "sc001.b15.p1_nonprice_source_capability_revalidation_self_test.v0.2",
            "status": status,
            "error": error,
            "exchange_calls_performed": False,
            "credentials_required": False,
            "output_snapshot_written": False,
            "price_data_used": False,
            "pnl_data_used": False,
            "collector_launch_authorized": False,
        },
        mode=0o640,
    )


def self_test() -> int:
    try:
        require_freeze()
        static_firewall_guard()
        assets = admitted_assets()

        with tempfile.TemporaryDirectory() as td:
            env = Path(td) / "b15.env"
            env.write_text(
                "\n".join(
                    [
                        "SC001_B15_OKX_API_KEY=okx_key",
                        "SC001_B15_OKX_API_SECRET=okx_secret",
                        "SC001_B15_OKX_PASSPHRASE=okx_pass",
                        "SC001_B15_OKX_BASE_URL=https://openapi.okx.com",
                        "SC001_B15_BYBIT_API_KEY=bybit_key",
                        "SC001_B15_BYBIT_API_SECRET=bybit_secret",
                        "SC001_B15_BYBIT_BASE_URL=https://api.bybit.com",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            os.chmod(env, 0o600)
            cfg = parse_env(env)
            if len(cfg) != 7:
                fail("env parser fixture")

        by_perm = validate_bybit_permission(
            {
                "retCode": 0,
                "result": {
                    "readOnly": 1,
                    "ips": ["203.0.113.1"],
                    "permissions": {"Wallet": ["AccountTransfer"]},
                },
            }
        )
        ok_perm = validate_okx_permission(
            {
                "code": "0",
                "data": [{"perm": "read_only", "ip": "203.0.113.1"}],
            }
        )
        if not by_perm["ip_bound"] or not ok_perm["ip_bound"]:
            fail("permission fixture")

        by_schema = validate_bybit_coin_info(
            {
                "retCode": 0,
                "result": {
                    "rows": [
                        {
                            "coin": "BTC",
                            "chains": [
                                {
                                    "chain": "BTC",
                                    "chainType": "Bitcoin",
                                    "chainDeposit": "1",
                                    "chainWithdraw": "1",
                                    "contractAddress": "",
                                    "withdrawFee": "0.0001",
                                    "withdrawPercentageFee": "0",
                                    "depositMin": "0.00001",
                                    "withdrawMin": "0.0002",
                                    "withdrawMax": "10",
                                    "minAccuracy": "8",
                                    "confirmation": "1",
                                    "safeConfirmNumber": "2",
                                }
                            ],
                        }
                    ]
                },
            }
        )
        ok_schema = validate_okx_currencies(
            {
                "code": "0",
                "data": [
                    {
                        "ccy": "BTC",
                        "chain": "BTC-Bitcoin",
                        "ctAddr": "",
                        "canDep": True,
                        "canWd": True,
                        "fee": "0.0001",
                        "burningFeeRate": "",
                        "minDep": "0.00001",
                        "minWd": "0.0002",
                        "maxWd": "10",
                        "wdTickSz": "8",
                        "minDepArrivalConfirm": "1",
                        "minWdUnlockConfirm": "2",
                    }
                ],
            }
        )
        if by_schema["chain_rows"] != 1 or ok_schema["currency_chain_rows"] != 1:
            fail("source schema fixture")
        if ok_schema["feeCcy_presence_mode"] != "NONE":
            fail("OKX feeCcy optional-schema fixture")

        fee_group_fixture = parse_okx_fee_response(
            {
                "code": "0",
                "data": [{
                    "feeGroup": [
                        {"groupId": "1", "taker": "-0.001", "maker": "-0.0008"},
                        {"groupId": "2", "taker": "-0.0012", "maker": "-0.0010"}
                    ]
                }]
            },
            "BTC-USDT",
            "1",
        )
        if fee_group_fixture.get("fee_schema") != "FEE_GROUP":
            fail("OKX feeGroup schema fixture")
        if fee_group_fixture.get("groupId") != "1":
            fail("OKX feeGroup exact selection fixture")

        deprecated_fixture = parse_okx_fee_response(
            {
                "code": "0",
                "data": [{
                    "taker": "-0.001",
                    "maker": "-0.0008"
                }]
            },
            "BTC-USDT",
            "",
        )
        if deprecated_fixture.get("fee_schema") != "DEPRECATED_TOP_LEVEL":
            fail("OKX deprecated fee fallback fixture")

        try:
            parse_okx_fee_response(
                {
                    "code": "0",
                    "data": [{
                        "feeGroup": [
                            {"groupId": "1", "taker": "-0.001", "maker": "-0.0008"},
                            {"groupId": "2", "taker": "-0.0012", "maker": "-0.0010"}
                        ]
                    }]
                },
                "BTC-USDT",
                "",
            )
        except CapabilityError:
            pass
        else:
            fail("OKX ambiguous feeGroup fixture did not fail closed")

        source_text = Path(__file__).read_text(encoding="utf-8")
        if "nextPageCursor" in source_text or '"limit": "1000"' in source_text:
            fail("Bybit Spot pagination logic unexpectedly present")

        q = qualify_pairs(
            assets,
            {"BTC": "BTCUSDT", "ETH": "ETHUSDT"},
            {
                "BTC": {"instId": "BTC-USDT", "groupId": "1"},
                "ETH": {"instId": "ETH-USDT", "groupId": "1"},
            },
        )
        if "BTC" not in q["both_assets"]:
            fail("pair qualification fixture")

        route_sha = require_object(ROUTE_SHARD_INDEX).get("logical_sha256")
        snap = build_snapshot_fixture(
            sha256_file(RUNNER),
            sha256_file(IMPLEMENTATION_FREEZE),
            str(route_sha),
        )
        validate_snapshot_contract(snap)

        print(SELFTEST_PASS)
        print("frozen_admitted_assets =", len(assets))
        print("exchange_calls_performed = False")
        print("collector_launch_authorized = False")
        print("price_data_used = False")
        write_selftest_manifest(SELFTEST_PASS)
        return 0
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        print(SELFTEST_REVIEW)
        print("error =", err)
        print("exchange_calls_performed = False")
        print("collector_launch_authorized = False")
        print("price_data_used = False")
        try:
            write_selftest_manifest(SELFTEST_REVIEW, err)
        except Exception:
            pass
        return 2


def live_run() -> int:
    try:
        require_freeze()
        static_firewall_guard()
        cfg = parse_env(ENV_FILE)
        install_ipv4_only()
        assets = admitted_assets()

        by_base = cfg["SC001_B15_BYBIT_BASE_URL"].rstrip("/")
        ok_base = cfg["SC001_B15_OKX_BASE_URL"].rstrip("/")

        local_ms = now_ms()
        by_skew = local_ms - bybit_server_time_ms(by_base)
        ok_skew = local_ms - okx_server_time_ms(ok_base)
        if abs(by_skew) > MAX_CLOCK_SKEW_MS:
            fail(f"Bybit clock skew exceeds {MAX_CLOCK_SKEW_MS} ms")
        if abs(ok_skew) > MAX_CLOCK_SKEW_MS:
            fail(f"OKX clock skew exceeds {MAX_CLOCK_SKEW_MS} ms")

        by_perm_obj = decode_json_object(
            bybit_private(
                by_base,
                cfg["SC001_B15_BYBIT_API_KEY"],
                cfg["SC001_B15_BYBIT_API_SECRET"],
                BYBIT_PERMISSION,
            ),
            "Bybit permission",
        )
        by_perm = validate_bybit_permission(by_perm_obj)

        ok_perm_obj = decode_json_object(
            okx_private(
                ok_base,
                cfg["SC001_B15_OKX_API_KEY"],
                cfg["SC001_B15_OKX_API_SECRET"],
                cfg["SC001_B15_OKX_PASSPHRASE"],
                OKX_PERMISSION,
            ),
            "OKX permission",
        )
        ok_perm = validate_okx_permission(ok_perm_obj)

        by_coin_obj = decode_json_object(
            bybit_private(
                by_base,
                cfg["SC001_B15_BYBIT_API_KEY"],
                cfg["SC001_B15_BYBIT_API_SECRET"],
                BYBIT_COIN_INFO,
            ),
            "Bybit coin-info",
        )
        by_source = validate_bybit_coin_info(by_coin_obj)

        ok_cur_obj = decode_json_object(
            okx_private(
                ok_base,
                cfg["SC001_B15_OKX_API_KEY"],
                cfg["SC001_B15_OKX_API_SECRET"],
                cfg["SC001_B15_OKX_PASSPHRASE"],
                OKX_CURRENCIES,
            ),
            "OKX currencies",
        )
        ok_source = validate_okx_currencies(ok_cur_obj)

        by_live = bybit_live_usdt_spot_pairs(by_base)
        ok_live = okx_live_usdt_spot_pairs(ok_base)
        q = qualify_pairs(assets, by_live, ok_live)

        preferred = "BTC" if "BTC" in q["both_assets"] else q["both_assets"][0]
        by_symbol = q["bybit_by_asset"][preferred]
        ok_inst = q["okx_by_asset"][preferred]

        by_fee = bybit_fee_probe(
            by_base,
            cfg["SC001_B15_BYBIT_API_KEY"],
            cfg["SC001_B15_BYBIT_API_SECRET"],
            by_symbol,
        )
        ok_group = str(
            q["okx_metadata_by_instrument"]
            .get(ok_inst, {})
            .get("groupId") or ""
        )
        ok_fee = okx_fee_probe(
            ok_base,
            cfg["SC001_B15_OKX_API_KEY"],
            cfg["SC001_B15_OKX_API_SECRET"],
            cfg["SC001_B15_OKX_PASSPHRASE"],
            ok_inst,
            ok_group,
        )

        route_sha = str(require_object(ROUTE_SHARD_INDEX).get("logical_sha256"))
        snapshot = {
            "schema": "sc001.b15.p1_nonprice_source_capability_snapshot.v0.2",
            "status": PASS,
            "generated_utc": utc_iso_ms(),
            "anchors": {
                "runner_sha256": sha256_file(RUNNER),
                "implementation_freeze_sha256": sha256_file(IMPLEMENTATION_FREEZE),
                "route_graph_sha256": route_sha,
                "service_file_sha256": sha256_file(SERVICE),
                "admitted_universe_sha256": sha256_file(ADMITTED),
                "capability_probe_sha256": sha256_file(Path(__file__).resolve()),
                "capability_freeze_sha256": sha256_file(FREEZE),
            },
            "permissions": {
                "bybit_readOnly": by_perm["readOnly"],
                "bybit_withdraw_token_present": by_perm["withdraw_token_present"],
                "bybit_ip_bound": by_perm["ip_bound"],
                "okx_permission": ok_perm["permission"],
                "okx_ip_bound": ok_perm["ip_bound"],
            },
            "source_endpoints_pass": True,
            "bybit_base_url": by_base,
            "okx_base_url": ok_base,
            "clock_skew_ms": {
                "BYBIT": by_skew,
                "OKX": ok_skew,
            },
            "source_schema": {
                "BYBIT": by_source,
                "OKX": ok_source,
            },
            "okx_adapter": {
                "get_currencies_feeCcy_optional": True,
                "fee_currency_default_when_feeCcy_absent": "WITHDRAWN_CCY",
                "trade_fee_primary_schema": "feeGroup[]",
                "deprecated_top_level_fee_fields_fallback": True,
            },
            "qualified_pairs": {
                "BYBIT": q["BYBIT"],
                "OKX": q["OKX"],
            },
            "qualified_pair_metadata": {
                "OKX": q["okx_metadata_by_instrument"],
            },
            "pair_coverage": {
                "frozen_admitted_assets": len(assets),
                "qualified_bybit_count": len(q["BYBIT"]),
                "qualified_okx_count": len(q["OKX"]),
                "both_venues_count": len(q["both_assets"]),
                "both_venues_assets": q["both_assets"],
                "missing_bybit_assets": q["missing_bybit_assets"],
                "missing_okx_assets": q["missing_okx_assets"],
            },
            "fee_endpoint_probe": {
                "asset": preferred,
                "BYBIT": by_fee,
                "OKX": ok_fee,
                "pass": True,
            },
            "transport_family": "IPv4-only",
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
        validate_snapshot_contract(snapshot)
        atomic_json(OUTPUT_FILE, snapshot, mode=0o640)

        safe_summary = {
            "schema": "sc001.b15.p1_nonprice_source_capability_safe_summary.v0.2",
            "status": PASS,
            "generated_utc": snapshot["generated_utc"],
            "snapshot_path": str(OUTPUT_FILE),
            "snapshot_sha256": sha256_file(OUTPUT_FILE),
            "permissions": snapshot["permissions"],
            "source_schema": snapshot["source_schema"],
            "clock_skew_ms": snapshot["clock_skew_ms"],
            "pair_coverage": {
                "frozen_admitted_assets": len(assets),
                "qualified_bybit_count": len(q["BYBIT"]),
                "qualified_okx_count": len(q["OKX"]),
                "both_venues_count": len(q["both_assets"]),
            },
            "fee_probe_asset": preferred,
            "source_endpoints_pass": True,
            "collector_launch_authorized": False,
            "price_data_used": False,
        }
        atomic_json(SAFE_SUMMARY_FILE, safe_summary, mode=0o640)

        print(PASS)
        print("snapshot_path =", OUTPUT_FILE)
        print("snapshot_sha256 =", sha256_file(OUTPUT_FILE))
        print("Bybit readOnly =", by_perm["readOnly"])
        print("Bybit Withdraw token present =", by_perm["withdraw_token_present"])
        print("Bybit IP bound =", by_perm["ip_bound"])
        print("OKX permission =", ok_perm["permission"])
        print("OKX IP bound =", ok_perm["ip_bound"])
        print("Bybit source chain rows =", by_source["chain_rows"])
        print("OKX source chain rows =", ok_source["currency_chain_rows"])
        print("qualified Bybit USDT pairs =", len(q["BYBIT"]))
        print("qualified OKX USDT pairs =", len(q["OKX"]))
        print("qualified both-venue assets =", len(q["both_assets"]))
        print("fee probe asset =", preferred)
        print("price endpoints called = False")
        print("order/transfer/withdraw endpoints called = False")
        print("collector_launch_authorized = False")
        return 0

    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        print(REVIEW)
        print("error =", err)
        print("secret_values_printed = False")
        print("collector_launch_authorized = False")
        print("price_data_used = False")
        return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--mode",
        choices=("self-test", "run"),
        default="self-test",
    )
    args = ap.parse_args()
    if args.mode == "self-test":
        return self_test()
    return live_run()


if __name__ == "__main__":
    raise SystemExit(main())
