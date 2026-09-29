#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path
from typing import Any, Callable

getcontext().prec = 40

STAGE = "SC001-B15P2-P0-BASIS-CONVERGENCE-V0.1"
SELFTEST_PASS = "B15P2_P0_BASIS_CONVERGENCE_V01_SELF_TEST_PASS"

EXPECTED_SPEC_SHA = "1dc79403307177c1f9785090fa6f31aac0322ccb10864c509846e8da415856a7"
EXPECTED_CLOCK_SHA = "9e4f6db4ce173cf9d5fa590a1acd1a56fa6a9f465c001c88de47b2542a172d70"
EXPECTED_EVENT_SET_SHA = "1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2"

SPEC_REL = Path("docs/research/sc001-b15p2-pre-registered-price-experiment-spec-v0.1.json")
CLOCK_REL = Path("docs/research/sc001-b15p2-causal-event-clock-freeze-v0.1.json")
APPROVAL_REL = Path("docs/research/sc001-b15p2-p0-price-index-basis-execution-approval-v0.1.json")
EXPECTED_APPROVAL_SHA = "27a4f094767f19a9c992e3b777ceea9b2b1eb5cf12d9b5e6a3230f81e007b7fc"

REPO = Path(os.environ.get("B15P2_REPO_ROOT", str(Path(__file__).resolve().parents[2]))).resolve()
DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_B15P2_P0_BASIS_CONVERGENCE"
OUT = OUT_DIR / "sc001_b15p2_p0_basis_convergence_v0_1.json"

BYBIT_BASE = "https://api.bybit.com"
ALLOWED_HOST = "api.bybit.com"
CONTRACT_ENDPOINT = "/v5/market/kline"
INDEX_ENDPOINT = "/v5/market/index-price-kline"
INTERVAL = "1"
OFFSETS_MIN = (-55, -30, -5)
REQUEST_TIMEOUT = 20
REQUEST_RETRIES = 3
REQUEST_SLEEP = 0.15
MAX_JSON = 1_000_000
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 1502

def fail(msg: str) -> None:
    raise RuntimeError(msg)

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def load_json_exact(path: Path, expected_sha: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        fail(f"MISSING_OR_SYMLINK:{path}")
    raw = path.read_bytes()
    actual = sha256_bytes(raw)
    if actual != expected_sha:
        fail(f"SHA_MISMATCH:{path}:{actual}")
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON_OBJECT_REQUIRED:{path}")
    return obj

def atomic_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def dec(value: Any, label: str) -> Decimal:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise RuntimeError(f"{label}:DECIMAL_PARSE") from exc
    if not d.is_finite() or d <= 0:
        fail(f"{label}:NONPOSITIVE_OR_NONFINITE")
    return d

def dec_nonnegative(value: Any, label: str) -> Decimal:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise RuntimeError(f"{label}:DECIMAL_PARSE") from exc
    if not d.is_finite() or d < 0:
        fail(f"{label}:NEGATIVE_OR_NONFINITE")
    return d

def qfloat(d: Decimal, places: str = "0.00000001") -> float:
    return float(d.quantize(Decimal(places)))

def target_candle_start(delivery_ms: int, offset_min: int) -> int:
    target_end = int(delivery_ms) + int(offset_min) * 60_000
    if target_end % 60_000 != 0:
        fail("TARGET_END_NOT_MINUTE_ALIGNED")
    return target_end - 60_000

def validate_frozen_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    spec = load_json_exact(REPO / SPEC_REL, EXPECTED_SPEC_SHA)
    clocks = load_json_exact(REPO / CLOCK_REL, EXPECTED_CLOCK_SHA)

    if spec.get("status") != "FROZEN_DESIGN_PRICE_FIREWALL_NOT_AUTHORIZED":
        fail("SPEC_STATUS")
    if (spec.get("lineage") or {}).get("frozen_event_set_sha256") != EXPECTED_EVENT_SET_SHA:
        fail("SPEC_EVENT_SET_SHA")
    if tuple((spec.get("sampling") or {}).get("registered_target_offsets_minutes") or ()) != OFFSETS_MIN:
        fail("SPEC_OFFSETS")
    if ((spec.get("data_sources") or {}).get("affected_contract") or {}).get("endpoint") != CONTRACT_ENDPOINT:
        fail("SPEC_CONTRACT_ENDPOINT")
    if ((spec.get("data_sources") or {}).get("official_index") or {}).get("endpoint") != INDEX_ENDPOINT:
        fail("SPEC_INDEX_ENDPOINT")
    auth = spec.get("current_authorization") or {}
    if any(auth.get(k) is not False for k in ("price_access", "index_value_access", "basis_calculation", "returns", "pnl", "trading")):
        fail("SPEC_PREAUTH_FIREWALL_MUTATED")

    if clocks.get("status") != "FROZEN_PRE_PRICE_SOURCE_ONLY":
        fail("CLOCK_STATUS")
    if clocks.get("frozen_event_set_sha256") != EXPECTED_EVENT_SET_SHA:
        fail("CLOCK_EVENT_SET_SHA")
    rows = clocks.get("clocks") or []
    if len(rows) != 94 or clocks.get("unique_delivery_timestamp_count") != 37:
        fail("CLOCK_COUNTS")
    for row in rows:
        if not isinstance(row, dict):
            fail("CLOCK_ROW")
        if int(row["delivery_ms"]) <= int(row["first_notice_ms"]):
            fail(f"CLOCK_NONCAUSAL:{row.get('symbol')}")
        for off in OFFSETS_MIN:
            obs_end = int(row["delivery_ms"]) + off * 60_000
            if obs_end < int(row["first_notice_ms"]):
                fail(f"OBSERVATION_BEFORE_NOTICE:{row.get('symbol')}:{off}")
    return spec, clocks

def validate_execution_approval() -> dict[str, Any]:
    approval = load_json_exact(REPO / APPROVAL_REL, EXPECTED_APPROVAL_SHA)
    if approval.get("status") != "AUTHORIZED_LIMITED_P0_SCOPE":
        fail("APPROVAL_STATUS")
    auth = set(str(x) for x in (approval.get("authorized") or []))
    required = {
        "AFFECTED_CONTRACT_1M_KLINE_CLOSE_VOLUME_TURNOVER_AT_REGISTERED_SNAPSHOTS",
        "OFFICIAL_BYBIT_INDEX_1M_KLINE_CLOSE_AT_REGISTERED_SNAPSHOTS",
        "DERIVED_PERPETUAL_MINUS_INDEX_BASIS_AT_REGISTERED_SNAPSHOTS",
        "PRE_REGISTERED_P0_CLUSTER_AND_MONTH_AGGREGATION",
    }
    if not required.issubset(auth):
        fail("APPROVAL_SCOPE_MISSING")
    forbidden = set(str(x) for x in (approval.get("still_forbidden") or []))
    for item in ("RETURNS", "PNL", "ORDER_BOOK_L1_L2", "INDIVIDUAL_TRADE_BODY", "TRADING_OR_ORDER_EXECUTION"):
        if item not in forbidden:
            fail(f"APPROVAL_FORBIDDEN_SCOPE_MISSING:{item}")
    return approval

def no_proxy_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))

def request_json(path: str, params: dict[str, str], label: str) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    url = BYBIT_BASE + path + "?" + query
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        fail(f"{label}:URL_POLICY")
    last: Exception | None = None
    opener = no_proxy_opener()
    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "User-Agent": "BotMarketplace-SC001-B15P2-P0/0.1",
                    "Accept": "application/json",
                },
            )
            with opener.open(req, timeout=REQUEST_TIMEOUT) as resp:
                raw = resp.read(MAX_JSON + 1)
                final = resp.geturl()
                status = int(getattr(resp, "status", 200))
            if len(raw) > MAX_JSON:
                fail(f"{label}:RESPONSE_CAP")
            fp = urllib.parse.urlparse(final)
            if fp.scheme != "https" or fp.hostname != ALLOWED_HOST:
                fail(f"{label}:FINAL_URL_POLICY")
            if status != 200:
                fail(f"{label}:HTTP_{status}")
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict):
                fail(f"{label}:JSON_OBJECT")
            if int(obj.get("retCode", -1)) != 0:
                fail(f"{label}:RETCODE:{obj.get('retCode')}:{obj.get('retMsg')}")
            return obj
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in {408, 425, 429, 500, 502, 503, 504} and attempt < REQUEST_RETRIES:
                time.sleep(0.75 * attempt)
                continue
            raise RuntimeError(f"{label}:HTTPERROR:{exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last = exc
            if attempt < REQUEST_RETRIES:
                time.sleep(0.75 * attempt)
                continue
            raise RuntimeError(f"{label}:NETWORK_OR_JSON:{type(exc).__name__}:{exc}") from exc
    raise RuntimeError(f"{label}:REQUEST_FAILED:{type(last).__name__}:{last}")

def bybit_candle(
    endpoint: str,
    symbol: str,
    candle_start_ms: int,
    *,
    require_volume: bool,
) -> dict[str, Any]:
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": INTERVAL,
        "start": str(candle_start_ms),
        "end": str(candle_start_ms + 59_999),
        "limit": "2",
    }
    obj = request_json(endpoint, params, f"{symbol}:{endpoint}:{candle_start_ms}")
    result = obj.get("result") or {}
    if str(result.get("symbol") or "") != symbol:
        fail(f"{symbol}:{endpoint}:RESULT_SYMBOL")
    category = str(result.get("category") or "linear")
    if category not in {"", "linear"}:
        fail(f"{symbol}:{endpoint}:RESULT_CATEGORY:{category}")
    rows = result.get("list") or []
    if not isinstance(rows, list):
        fail(f"{symbol}:{endpoint}:LIST_TYPE")

    exact = []
    for row in rows:
        if not isinstance(row, list) or len(row) < (7 if require_volume else 5):
            continue
        try:
            ts = int(str(row[0]))
        except Exception:
            continue
        if ts == candle_start_ms:
            exact.append(row)
    if len(exact) != 1:
        raise LookupError(f"EXACT_CANDLE_COUNT:{len(exact)}")

    row = exact[0]
    close = dec(row[4], f"{symbol}:{endpoint}:CLOSE")
    out = {
        "start_ms": candle_start_ms,
        "close": close,
    }
    if require_volume:
        volume = dec_nonnegative(row[5], f"{symbol}:{endpoint}:VOLUME")
        turnover = dec_nonnegative(row[6], f"{symbol}:{endpoint}:TURNOVER")
        out["volume"] = volume
        out["turnover"] = turnover
    return out

def basis_bps(contract_close: Decimal, index_close: Decimal) -> Decimal:
    return Decimal(10_000) * (contract_close / index_close - Decimal(1))

def median_float(values: list[float]) -> float:
    if not values:
        fail("MEDIAN_EMPTY")
    return float(statistics.median(values))

def percentile_sorted(xs: list[float], p: float) -> float:
    if not xs:
        fail("PERCENTILE_EMPTY")
    if not 0 <= p <= 1:
        fail("PERCENTILE_P")
    if len(xs) == 1:
        return float(xs[0])
    ys = sorted(float(x) for x in xs)
    h = (len(ys) - 1) * p
    lo = math.floor(h)
    hi = math.ceil(h)
    if lo == hi:
        return ys[lo]
    return ys[lo] + (h - lo) * (ys[hi] - ys[lo])

def bootstrap_median_interval(values: list[float]) -> dict[str, Any]:
    if not values:
        fail("BOOTSTRAP_EMPTY")
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(values)
    stats = []
    for _ in range(BOOTSTRAP_REPS):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        stats.append(median_float(sample))
    return {
        "replications": BOOTSTRAP_REPS,
        "seed": BOOTSTRAP_SEED,
        "p05": percentile_sorted(stats, 0.05),
        "p95": percentile_sorted(stats, 0.95),
    }

def summarize_numeric(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "p25": None, "median": None, "p75": None, "max": None}
    return {
        "count": len(values),
        "min": min(values),
        "p25": percentile_sorted(values, 0.25),
        "median": median_float(values),
        "p75": percentile_sorted(values, 0.75),
        "max": max(values),
    }

def aggregate(
    clocks: dict[str, Any],
    event_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    eligible = [r for r in event_rows if r.get("eligible") is True]
    ineligible = [r for r in event_rows if r.get("eligible") is not True]

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in eligible:
        groups[str(r["delivery_cluster_id"])].append(r)

    cluster_rows = []
    for cid in sorted(groups):
        rows = groups[cid]
        delivery_ms_values = {int(r["delivery_ms"]) for r in rows}
        months = {str(r["delivery_month"]) for r in rows}
        if len(delivery_ms_values) != 1 or len(months) != 1:
            fail(f"CLUSTER_IDENTITY:{cid}")
        cluster_rows.append({
            "delivery_cluster_id": cid,
            "delivery_ms": next(iter(delivery_ms_values)),
            "delivery_month": next(iter(months)),
            "eligible_event_count": len(rows),
            "event_symbols": [r["symbol"] for r in rows],
            "a_minus55_median_bps": median_float([r["a_minus55_bps"] for r in rows]),
            "a_minus30_median_bps": median_float([r["a_minus30_bps"] for r in rows]),
            "a_minus5_median_bps": median_float([r["a_minus5_bps"] for r in rows]),
            "c_control_median_bps": median_float([r["c_control_bps"] for r in rows]),
            "c_event_median_bps": median_float([r["c_event_bps"] for r in rows]),
            "d_median_bps": median_float([r["d_bps"] for r in rows]),
        })

    d_cluster = [r["d_median_bps"] for r in cluster_rows]
    c_event_cluster = [r["c_event_median_bps"] for r in cluster_rows]
    bootstrap = bootstrap_median_interval(d_cluster) if d_cluster else {
        "replications": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED, "p05": None, "p95": None
    }

    by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in cluster_rows:
        by_month[r["delivery_month"]].append(r)
    month_rows = []
    for month in sorted(by_month):
        rows = by_month[month]
        ds = [r["d_median_bps"] for r in rows]
        month_rows.append({
            "delivery_month": month,
            "eligible_cluster_count": len(rows),
            "d_median_bps": median_float(ds),
            "positive_d_cluster_count": sum(1 for x in ds if x > 0),
        })

    expected_months = [str(x) for x in (clocks.get("delivery_months") or [])]
    eligible_months = {r["delivery_month"] for r in month_rows}
    source_gate = (
        len(eligible) >= 90
        and len(cluster_rows) >= 35
        and all(m in eligible_months for m in expected_months)
    )

    median_d = median_float(d_cluster) if d_cluster else None
    positive_share = (
        sum(1 for x in d_cluster if x > 0) / len(d_cluster)
        if d_cluster else None
    )
    positive_months = sum(1 for r in month_rows if r["d_median_bps"] > 0)
    timing_gate = bool(
        source_gate
        and median_d is not None and median_d > 0
        and bootstrap["p05"] is not None and bootstrap["p05"] > 0
        and positive_share is not None and positive_share >= 0.60
        and positive_months >= 6
    )
    median_c_event = median_float(c_event_cluster) if c_event_cluster else None

    if not source_gate:
        verdict = "DEFER_SOURCE_COVERAGE"
    elif not timing_gate:
        verdict = "REJECT_MECHANISM_TIMING_SPECIFICITY"
    elif median_c_event is None:
        verdict = "DEFER_SOURCE_COVERAGE"
    elif median_c_event <= 11:
        verdict = "REJECT_STRUCTURAL_ECONOMIC_SCALE"
    elif median_c_event < 30:
        verdict = "DEFER_COST_HEADROOM"
    else:
        verdict = "PASS_TO_P1_EXECUTION_FEASIBILITY"

    return {
        "eligible_event_count": len(eligible),
        "ineligible_event_count": len(ineligible),
        "eligible_delivery_cluster_count": len(cluster_rows),
        "eligible_month_count": len(eligible_months),
        "expected_months": expected_months,
        "source_gate_pass": source_gate,
        "timing_specificity_gate_pass": timing_gate,
        "cluster_median_d_bps": median_d,
        "cluster_positive_d_share": positive_share,
        "positive_month_median_d_count": positive_months,
        "cluster_median_c_event_bps": median_c_event,
        "bootstrap_cluster_median_d_90pct": bootstrap,
        "a_minus55_summary_bps": summarize_numeric([r["a_minus55_bps"] for r in cluster_rows]),
        "a_minus30_summary_bps": summarize_numeric([r["a_minus30_bps"] for r in cluster_rows]),
        "a_minus5_summary_bps": summarize_numeric([r["a_minus5_bps"] for r in cluster_rows]),
        "c_control_summary_bps": summarize_numeric([r["c_control_median_bps"] for r in cluster_rows]),
        "c_event_summary_bps": summarize_numeric(c_event_cluster),
        "d_summary_bps": summarize_numeric(d_cluster),
        "cluster_ledger": cluster_rows,
        "month_summary": month_rows,
        "source_missing_ledger": [
            {
                "symbol": r.get("symbol"),
                "delivery_ms": r.get("delivery_ms"),
                "delivery_cluster_id": r.get("delivery_cluster_id"),
                "reason": r.get("ineligible_reason"),
                "snapshot_errors": r.get("snapshot_errors"),
            }
            for r in ineligible
        ],
        "verdict": verdict,
    }

def collect_event(
    row: dict[str, Any],
    fetch_contract: Callable[[str, int], dict[str, Any]],
    fetch_index: Callable[[str, int], dict[str, Any]],
) -> dict[str, Any]:
    symbol = str(row["symbol"])
    delivery_ms = int(row["delivery_ms"])
    delivery_month = datetime.fromtimestamp(delivery_ms / 1000, tz=timezone.utc).strftime("%Y-%m")

    points: dict[int, dict[str, Any]] = {}
    errors = []
    for off in OFFSETS_MIN:
        start = target_candle_start(delivery_ms, off)
        try:
            c = fetch_contract(symbol, start)
            time.sleep(REQUEST_SLEEP)
            idx = fetch_index(symbol, start)
            time.sleep(REQUEST_SLEEP)
            if int(c["start_ms"]) != start or int(idx["start_ms"]) != start:
                fail("SNAPSHOT_START_MISMATCH")
            if dec_nonnegative(c["volume"], "VOLUME") <= 0 or dec_nonnegative(c["turnover"], "TURNOVER") <= 0:
                raise LookupError("CONTRACT_ZERO_ACTIVITY")
            b = basis_bps(dec(c["close"], "CONTRACT_CLOSE"), dec(idx["close"], "INDEX_CLOSE"))
            points[off] = {
                "candle_start_ms": start,
                "contract_close": dec(c["close"], "CONTRACT_CLOSE"),
                "index_close": dec(idx["close"], "INDEX_CLOSE"),
                "volume": dec_nonnegative(c["volume"], "VOLUME"),
                "turnover": dec_nonnegative(c["turnover"], "TURNOVER"),
                "basis_bps": b,
            }
        except Exception as exc:
            errors.append({
                "offset_min": off,
                "candle_start_ms": start,
                "error": f"{type(exc).__name__}:{exc}",
            })

    base = {
        "symbol": symbol,
        "delivery_ms": delivery_ms,
        "delivery_month": delivery_month,
        "first_notice_ms": int(row["first_notice_ms"]),
        "delivery_cluster_id": str(row["delivery_cluster_id"]),
        "simultaneous_event_count": int(row["simultaneous_event_count"]),
        "snapshot_errors": errors,
    }
    if errors or len(points) != 3:
        return {
            **base,
            "eligible": False,
            "ineligible_reason": "SOURCE_MISSING_OR_INVALID_REGISTERED_SNAPSHOT",
            "snapshots": {
                str(off): {
                    "candle_start_ms": target_candle_start(delivery_ms, off),
                    "present": off in points,
                }
                for off in OFFSETS_MIN
            },
        }

    p55, p30, p5 = points[-55], points[-30], points[-5]
    a55 = abs(p55["basis_bps"])
    a30 = abs(p30["basis_bps"])
    a5 = abs(p5["basis_bps"])
    c_control = a55 - a30
    c_event = a30 - a5
    d = c_event - c_control
    b30 = p30["basis_bps"]
    side = "SHORT_PERPETUAL" if b30 > 0 else ("LONG_PERPETUAL" if b30 < 0 else "NO_DIRECTION")

    def point_out(p: dict[str, Any]) -> dict[str, Any]:
        return {
            "candle_start_ms": int(p["candle_start_ms"]),
            "contract_close": str(p["contract_close"]),
            "index_close": str(p["index_close"]),
            "contract_volume": str(p["volume"]),
            "contract_turnover": str(p["turnover"]),
            "basis_bps": qfloat(p["basis_bps"]),
            "absolute_basis_bps": qfloat(abs(p["basis_bps"])),
        }

    return {
        **base,
        "eligible": True,
        "ineligible_reason": None,
        "snapshots": {
            "-55": point_out(p55),
            "-30": point_out(p30),
            "-5": point_out(p5),
        },
        "a_minus55_bps": qfloat(a55),
        "a_minus30_bps": qfloat(a30),
        "a_minus5_bps": qfloat(a5),
        "c_control_bps": qfloat(c_control),
        "c_event_bps": qfloat(c_event),
        "d_bps": qfloat(d),
        "future_execution_side": side,
    }

def run_live() -> int:
    spec, clocks = validate_frozen_inputs()
    validate_execution_approval()
    events = clocks["clocks"]
    rows = []

    def fetch_contract(symbol: str, start: int) -> dict[str, Any]:
        return bybit_candle(CONTRACT_ENDPOINT, symbol, start, require_volume=True)

    def fetch_index(symbol: str, start: int) -> dict[str, Any]:
        return bybit_candle(INDEX_ENDPOINT, symbol, start, require_volume=False)

    for i, row in enumerate(events, start=1):
        symbol = row["symbol"]
        print(f"P0_EVENT_START {i:03d}/094 symbol={symbol}", flush=True)
        out = collect_event(row, fetch_contract, fetch_index)
        rows.append(out)
        print(
            f"P0_EVENT_DONE {i:03d}/094 symbol={symbol} "
            f"eligible={out['eligible']} errors={len(out['snapshot_errors'])}",
            flush=True,
        )

    agg = aggregate(clocks, rows)
    report = {
        "schema": "sc001.b15p2_p0_basis_convergence_result.v0.1",
        "date": "2026-09-29",
        "stage": STAGE,
        "status": agg["verdict"],
        "frozen_event_set_sha256": EXPECTED_EVENT_SET_SHA,
        "pre_registered_spec_sha256": EXPECTED_SPEC_SHA,
        "causal_clock_freeze_sha256": EXPECTED_CLOCK_SHA,
        "network_source": {
            "host": ALLOWED_HOST,
            "contract_endpoint": CONTRACT_ENDPOINT,
            "index_endpoint": INDEX_ENDPOINT,
            "category": "linear",
            "interval": INTERVAL,
            "registered_offsets_minutes": list(OFFSETS_MIN),
            "source_substitution_used": False,
        },
        "event_ledger": rows,
        **agg,
        "firewalls": {
            "affected_contract_price_accessed": True,
            "official_bybit_index_value_accessed": True,
            "basis_calculated": True,
            "returns_calculated": False,
            "pnl_calculated": False,
            "l1_l2_accessed": False,
            "individual_trade_body_accessed": False,
            "funding_value_accessed": False,
            "mark_price_accessed": False,
            "premium_index_accessed": False,
            "spot_price_accessed": False,
            "external_venue_price_accessed": False,
            "event_ranked_by_outcome": False,
            "trading": False,
        },
        "next_state": {
            "DEFER_SOURCE_COVERAGE": "REVIEW_OFFICIAL_SOURCE_COVERAGE_WITHOUT_SOURCE_SUBSTITUTION",
            "REJECT_MECHANISM_TIMING_SPECIFICITY": "TERMINAL_REJECT_P0_TIMING_SPECIFICITY_NO_RESCUE_ON_SAME_EVIDENCE",
            "REJECT_STRUCTURAL_ECONOMIC_SCALE": "TERMINAL_REJECT_P0_ECONOMIC_SCALE_NO_RESCUE_ON_SAME_EVIDENCE",
            "DEFER_COST_HEADROOM": "DEFER_BEFORE_P1_EXECUTION_MODEL",
            "PASS_TO_P1_EXECUTION_FEASIBILITY": "DESIGN_P1_EXECUTION_FEASIBILITY_SPEC_BEFORE_L1_RETURNS_PNL",
        }[agg["verdict"]],
    }
    atomic_json(OUT, report)

    print("B15P2_P0_RESULT", agg["verdict"])
    print("eligible_events =", agg["eligible_event_count"])
    print("eligible_clusters =", agg["eligible_delivery_cluster_count"])
    print("cluster_median_D_bps =", agg["cluster_median_d_bps"])
    print("cluster_D_positive_share =", agg["cluster_positive_d_share"])
    print("bootstrap_D_p05_p95 =", agg["bootstrap_cluster_median_d_90pct"])
    print("positive_months =", agg["positive_month_median_d_count"])
    print("cluster_median_C_event_bps =", agg["cluster_median_c_event_bps"])
    print("returns/PnL/L1/L2/trades/trading = CLOSED")
    print("report =", OUT)
    return 0

def selftest() -> int:
    spec, clocks = validate_frozen_inputs()
    validate_execution_approval()
    assert len(clocks["clocks"]) == 94
    assert clocks["unique_delivery_timestamp_count"] == 37
    assert tuple(spec["sampling"]["registered_target_offsets_minutes"]) == OFFSETS_MIN

    t = 1_800_000_000_000
    assert target_candle_start(t, -30) == t - 31 * 60_000

    c = {"start_ms": t, "close": Decimal("101"), "volume": Decimal("5"), "turnover": Decimal("505")}
    idx = {"start_ms": t, "close": Decimal("100")}
    assert basis_bps(c["close"], idx["close"]) == Decimal("100")

    fixture_rows = []
    for i in range(94):
        cluster_idx = i % 37
        cluster = f"C{cluster_idx + 1:02d}"
        month = f"2026-{(cluster_idx % 9) + 1:02d}"
        fixture_rows.append({
            "symbol": f"T{i:03d}USDT",
            "delivery_ms": 1_700_000_000_000 + cluster_idx * 86_400_000,
            "delivery_month": month,
            "first_notice_ms": 1_699_000_000_000,
            "delivery_cluster_id": cluster,
            "simultaneous_event_count": 1,
            "snapshot_errors": [],
            "eligible": True,
            "ineligible_reason": None,
            "a_minus55_bps": 40.0,
            "a_minus30_bps": 35.0,
            "a_minus5_bps": 2.0,
            "c_control_bps": 5.0,
            "c_event_bps": 33.0,
            "d_bps": 28.0,
        })
    fixture_clocks = {
        "delivery_months": [f"2026-{m:02d}" for m in range(1, 10)]
    }
    a = aggregate(fixture_clocks, fixture_rows)
    assert a["source_gate_pass"] is True
    assert a["timing_specificity_gate_pass"] is True
    assert a["verdict"] == "PASS_TO_P1_EXECUTION_FEASIBILITY"
    assert a["cluster_median_c_event_bps"] == 33.0
    assert a["cluster_median_d_bps"] == 28.0
    assert a["bootstrap_cluster_median_d_90pct"]["p05"] == 28.0

    low = [dict(x, c_event_bps=8.0, d_bps=3.0) for x in fixture_rows]
    alow = aggregate(fixture_clocks, low)
    assert alow["timing_specificity_gate_pass"] is True
    assert alow["verdict"] == "REJECT_STRUCTURAL_ECONOMIC_SCALE"

    timing = [dict(x, d_bps=-2.0) for x in fixture_rows]
    at = aggregate(fixture_clocks, timing)
    assert at["timing_specificity_gate_pass"] is False
    assert at["verdict"] == "REJECT_MECHANISM_TIMING_SPECIFICITY"

    missing = [dict(x, eligible=False, ineligible_reason="SOURCE_MISSING") if int(str(x["delivery_cluster_id"])[1:]) <= 5 else x for x in fixture_rows]
    am = aggregate(fixture_clocks, missing)
    assert am["source_gate_pass"] is False
    assert am["verdict"] == "DEFER_SOURCE_COVERAGE"

    print(SELFTEST_PASS)
    return 0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("self-test", "live"), default="self-test")
    args = ap.parse_args()
    if args.mode == "self-test":
        return selftest()
    return run_live()

if __name__ == "__main__":
    raise SystemExit(main())
