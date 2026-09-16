"""SC001 contract structure + historical-spec availability audit v0.1.

Metadata-only. Verifies the provisional top-12 are structurally comparable current
OKX linear USDT SWAP instruments and checks listing-time continuity against the
already-proven historical anchor archives.

IMPORTANT: current tick/lot/min/ctVal values are diagnostics only and are NOT
claimed to be historical 2024 values. No strategy signal/PnL. No L2/trade bodies.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STAGE = "SC001-CONTRACT-STRUCTURE-SPEC-AVAILABILITY-AUDIT"
VERSION = "0.1"
PASS = "SC001_CONTRACT_STRUCTURE_SPEC_AVAILABILITY_AUDIT_PASS"
REVIEW = "SC001_CONTRACT_STRUCTURE_SPEC_AVAILABILITY_AUDIT_REVIEW"
CAL_PASS = "SC001_PREPERIOD_LIQUIDITY_CALIBRATION_PASS"
SEED_PASS = "SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_PASS"

EXPECTED_TOP12 = ["BTC", "ETH", "SOL", "DOGE", "ORDI", "FIL", "UNI", "XRP", "LTC", "OP", "BCH", "SUI"]
EARLY_ANCHOR = "2023-12-30"
EARLY_ANCHOR_END_MS = int(datetime(2023, 12, 31, tzinfo=timezone.utc).timestamp() * 1000)

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
PATH = "/api/v5/public/instruments"
UA = "BotMarketplace-SC001-ContractStructureAudit/0.1"
TIMEOUT = 60
RETRIES = 4
RATE_SLEEP = 0.12

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
CAL = DATA_ROOT / "SC001_PREPERIOD_LIQUIDITY_CALIBRATION" / "sc001_preperiod_liquidity_calibration_report.json"
SEED = DATA_ROOT / "SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE" / "sc001_historical_universe_seeded_probe_report.json"
OUT_DIR = DATA_ROOT / "SC001_CONTRACT_STRUCTURE_SPEC_AVAILABILITY_AUDIT"
OUT = OUT_DIR / "sc001_contract_structure_spec_availability_audit_report.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required report: {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected: {path}")
    return x


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def positive_decimal(value: object) -> tuple[bool, str | None]:
    try:
        d = Decimal(str(value))
        if not d.is_finite() or d <= 0:
            return False, None
        return True, format(d, "f")
    except (InvalidOperation, ValueError, TypeError):
        return False, None


def request_instrument(inst: str) -> tuple[dict | None, str | None]:
    params = urlencode({"instType": "SWAP", "instId": inst})
    errors: list[str] = []
    for domain in DOMAINS:
        url = domain + PATH + "?" + params
        for attempt in range(1, RETRIES + 1):
            try:
                req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
                with urlopen(req, timeout=TIMEOUT) as r:
                    raw = r.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise RuntimeError("response_cap")
                obj = json.loads(raw.decode("utf-8"))
                if not isinstance(obj, dict) or obj.get("code") != "0" or not isinstance(obj.get("data"), list):
                    raise RuntimeError("non_success:" + str(obj.get("code") if isinstance(obj, dict) else "not_dict"))
                rows = [x for x in obj["data"] if isinstance(x, dict) and x.get("instId") == inst]
                if len(rows) != 1:
                    return None, f"exact_row_count:{len(rows)}"
                return rows[0], url
            except HTTPError as exc:
                errors.append(f"{domain}:http:{exc.code}")
                if exc.code == 429 and attempt < RETRIES:
                    time.sleep(1.0 * attempt)
                    continue
                break
            except (URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
                errors.append(f"{domain}:{type(exc).__name__}:{exc}")
                if attempt < RETRIES:
                    time.sleep(0.5 * attempt)
                    continue
                break
    return None, ";".join(errors[-8:]) if errors else "unresolved"


def audit_symbol(symbol: str, both_anchor: set[str]) -> dict:
    inst = f"{symbol}-USDT-SWAP"
    reasons: list[str] = []

    if symbol not in both_anchor:
        reasons.append("not_in_both_anchor_parent_pool")

    row, source = request_instrument(inst)
    if row is None:
        reasons.append("current_exact_instrument_row_unresolved")
        return {
            "symbol": symbol,
            "instrument": inst,
            "status": "REVIEW",
            "review_reasons": reasons,
            "source_or_error": source,
            "historical_exact_tick_lot_min_ctval_verified": False,
        }

    if row.get("instId") != inst:
        reasons.append("instId_mismatch")
    if row.get("instType") != "SWAP":
        reasons.append("instType_not_SWAP")
    if row.get("ctType") != "linear":
        reasons.append("ctType_not_linear")
    if row.get("settleCcy") != "USDT":
        reasons.append("settleCcy_not_USDT")

    normalized: dict[str, str | None] = {}
    for key in ("tickSz", "lotSz", "minSz", "ctVal"):
        ok, text = positive_decimal(row.get(key))
        normalized[key] = text
        if not ok:
            reasons.append(f"invalid_current_{key}")

    ct_val_ccy = str(row.get("ctValCcy") or "").strip()
    if not ct_val_ccy:
        reasons.append("empty_current_ctValCcy")

    list_time_raw = str(row.get("listTime") or "").strip()
    list_time_ms = None
    try:
        list_time_ms = int(list_time_raw)
        if list_time_ms <= 0:
            raise ValueError("nonpositive")
        if list_time_ms >= EARLY_ANCHOR_END_MS:
            reasons.append("current_listTime_conflicts_with_2023_12_30_archive_existence")
    except Exception:
        reasons.append("invalid_current_listTime")

    return {
        "symbol": symbol,
        "instrument": inst,
        "status": "PASS" if not reasons else "REVIEW",
        "review_reasons": reasons,
        "historical_anchor_continuity": symbol in both_anchor,
        "current_metadata_source": source,
        "current_structure": {
            "instType": row.get("instType"),
            "instFamily": row.get("instFamily"),
            "ctType": row.get("ctType"),
            "settleCcy": row.get("settleCcy"),
            "ctValCcy": ct_val_ccy,
            "tickSz": normalized.get("tickSz"),
            "lotSz": normalized.get("lotSz"),
            "minSz": normalized.get("minSz"),
            "ctVal": normalized.get("ctVal"),
            "ctMult": row.get("ctMult"),
            "listTime": list_time_raw,
            "listTime_ms": list_time_ms,
            "state": row.get("state"),
            "expTime": row.get("expTime"),
        },
        "historical_exact_tick_lot_min_ctval_verified": False,
        "historical_spec_values_must_be_resolved_before_promotional_execution": True,
    }


def main() -> int:
    cal = load_json(CAL)
    seed = load_json(SEED)

    if cal.get("status") != CAL_PASS:
        fail("liquidity calibration parent not exact PASS")
    if seed.get("status") != SEED_PASS:
        fail("seeded universe parent not exact PASS")

    proposed = list(cal.get("proposed_top12_symbols") or [])
    if proposed != EXPECTED_TOP12:
        fail(f"parent proposed top-12 mismatch: {proposed}")

    both = set(seed.get("both_anchor_symbols") or [])
    if not set(proposed).issubset(both):
        fail("top-12 not subset of both-anchor parent pool")

    rows = []
    for i, symbol in enumerate(proposed, 1):
        print(f"[{i}/{len(proposed)}] {symbol}-USDT-SWAP")
        r = audit_symbol(symbol, both)
        rows.append(r)
        print(
            symbol,
            r["status"],
            "ctType=", (r.get("current_structure") or {}).get("ctType"),
            "settle=", (r.get("current_structure") or {}).get("settleCcy"),
            "listTime=", (r.get("current_structure") or {}).get("listTime"),
        )
        time.sleep(RATE_SLEEP)

    passed = len(rows) == 12 and all(r.get("status") == "PASS" for r in rows)
    status = PASS if passed else REVIEW
    report = {
        "stage": STAGE,
        "version": VERSION,
        "status": status,
        "parent_liquidity_report": str(CAL),
        "parent_seeded_report": str(SEED),
        "provisional_top12_symbols": proposed,
        "rows": rows,
        "all_12_structurally_comparable": passed,
        "historical_exact_tick_lot_min_ctval_verified": False,
        "historical_spec_resolution_required_before_promotional_execution": True,
        "current_metadata_used_as_historical_spec_values": False,
        "trade_archive_body_downloaded": False,
        "l2_archive_body_downloaded": False,
        "strategy_signal_calculated": False,
        "strategy_pnl_calculated": False,
        "promotional_universe_frozen": False,
        "confirmation_accessed": False,
    }
    atomic_json(OUT, report)

    print(status)
    print("provisional top-12 symbols =", proposed)
    print("all 12 structurally comparable =", passed)
    print("historical exact tick/lot/min/ctVal verified = False")
    print("current metadata used as historical spec values = False")
    print("trade/L2 archive body downloaded = False")
    print("strategy signal/PnL calculated = False")
    print("promotional universe frozen = False")
    print("report =", OUT)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
