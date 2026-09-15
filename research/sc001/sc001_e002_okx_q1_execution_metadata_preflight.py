"""SC001-E002 Q1 execution metadata + funding preflight.

No alpha, no execution P&L, no Q2/Validation/Final.
Pins the already-frozen Q1 contract/fee constants and retrieves the official
OKX historical funding records required by taker-economics protocol v0.2.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STAGE = "SC001-E002-OKX-Q1-EXECUTION-METADATA-PREFLIGHT"
VERSION = "0.1"
INST = "BTC-USDT-SWAP"
DATES = ("2024-01-14", "2024-01-31", "2024-02-12", "2024-02-13")

# Historical values frozen before economics run.
CT_VAL_BTC = "0.01"
CONTRACT_MULTIPLIER = "1"
Q1_MIN_CONTRACTS = "1"
Q1_LOT_CONTRACTS = "1"
TICK_SIZE = "0.1"
TAKER_FEE_RATE = "0.0005"

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
OUTDIR = DATA_ROOT / "SC001_E002_OKX_Q1_EXECUTION_METADATA"
REPORT = OUTDIR / "sc001_e002_okx_q1_execution_metadata_preflight.json"
FUNDING = OUTDIR / "sc001_e002_okx_q1_funding_rates.json"

BASE = "https://www.okx.com"
UA = "BotMarketplace-SC001-E002-ExecutionMetadata/0.1"
TIMEOUT = 30


def utc_ms(text: str) -> int:
    return int(datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def get_json(path: str, params: dict[str, str]) -> dict:
    url = BASE + path + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    last: Exception | None = None
    for attempt in range(3):
        try:
            with urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(4_000_000)
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or obj.get("code") != "0":
                raise RuntimeError(f"OKX API response code mismatch: {obj!r}")
            return obj
        except Exception as exc:
            last = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"OKX request failed: {last!r}")


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def current_instrument_snapshot() -> dict:
    obj = get_json("/api/v5/public/instruments", {"instType": "SWAP", "instId": INST})
    rows = obj.get("data") or []
    if len(rows) != 1 or rows[0].get("instId") != INST:
        raise RuntimeError("current instrument identity mismatch")
    row = rows[0]
    # Current min/lot are intentionally NOT used as historical Q1 values.
    return {
        "instId": row.get("instId"),
        "ctType": row.get("ctType"),
        "ctVal": row.get("ctVal"),
        "ctValCcy": row.get("ctValCcy"),
        "ctMult": row.get("ctMult"),
        "settleCcy": row.get("settleCcy"),
        "tickSz": row.get("tickSz"),
        "current_lotSz_not_used_for_q1": row.get("lotSz"),
        "current_minSz_not_used_for_q1": row.get("minSz"),
        "state": row.get("state"),
    }


def funding_for_day(date_text: str) -> list[dict]:
    lo = utc_ms(date_text)
    hi = lo + 86_400_000
    # Official API semantics: `after` requests older records than cursor.
    # Cursor just after the UTC day makes the target day fall in the returned page.
    obj = get_json(
        "/api/v5/public/funding-rate-history",
        {"instId": INST, "after": str(hi + 1), "limit": "400"},
    )
    rows = []
    for x in obj.get("data") or []:
        try:
            ft = int(x.get("fundingTime"))
        except Exception:
            continue
        if lo <= ft < hi and x.get("instId") == INST:
            realized = x.get("realizedRate")
            rate = realized if isinstance(realized, str) and realized != "" else x.get("fundingRate")
            if not isinstance(rate, str) or rate == "":
                raise RuntimeError(f"missing realized/funding rate for {date_text}: {x!r}")
            rows.append({
                "fundingTime": str(ft),
                "fundingTimeUtc": datetime.fromtimestamp(ft / 1000, tz=timezone.utc).isoformat(),
                "realizedRate": rate,
                "fundingRateRaw": x.get("fundingRate"),
                "realizedRateRaw": x.get("realizedRate"),
                "method": x.get("method"),
                "formulaType": x.get("formulaType"),
                "instId": x.get("instId"),
            })
    rows.sort(key=lambda x: int(x["fundingTime"]))
    if len(rows) != 3:
        raise RuntimeError(
            f"expected exactly 3 BTC-USDT-SWAP funding records on {date_text}, got {len(rows)}; "
            "do not proceed to economics until funding history is resolved"
        )
    hours = [datetime.fromtimestamp(int(x["fundingTime"]) / 1000, tz=timezone.utc).hour for x in rows]
    if hours != [0, 8, 16]:
        raise RuntimeError(f"unexpected funding schedule on {date_text}: hours={hours}")
    return rows


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    current = current_instrument_snapshot()
    if current.get("ctType") != "linear" or current.get("ctValCcy") != "BTC" or current.get("settleCcy") != "USDT":
        raise RuntimeError(f"current instrument family mismatch: {current}")
    if current.get("ctVal") != CT_VAL_BTC or current.get("ctMult") != CONTRACT_MULTIPLIER or current.get("tickSz") != TICK_SIZE:
        raise RuntimeError(f"current ctVal/mult/tick no longer corroborates frozen metadata: {current}")

    funding = {d: funding_for_day(d) for d in DATES}
    atomic_json(FUNDING, {
        "stage": STAGE,
        "source": "OKX GET /api/v5/public/funding-rate-history",
        "instrument": INST,
        "dates": funding,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
    })

    report = {
        "stage": STAGE,
        "version": VERSION,
        "status": "PASS",
        "instrument": INST,
        "historical_q1_freeze": {
            "contract_value_btc": CT_VAL_BTC,
            "contract_multiplier": CONTRACT_MULTIPLIER,
            "minimum_contracts": Q1_MIN_CONTRACTS,
            "lot_step_contracts": Q1_LOT_CONTRACTS,
            "tick_size": TICK_SIZE,
            "primary_taker_fee_rate": TAKER_FEE_RATE,
            "primary_taker_fee_bps_per_fill": 5.0,
            "source_doc": "docs/research/sc001-e002-okx-q1-execution-metadata-fee-freeze-v0.1.md",
        },
        "current_instrument_snapshot_corroboration": current,
        "funding_file": str(FUNDING),
        "funding_records_per_day": {d: len(v) for d, v in funding.items()},
        "alpha_calculated": False,
        "execution_pnl_calculated": False,
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(REPORT, report)

    print("EXECUTION_METADATA_PREFLIGHT_PASS")
    print("instrument =", INST)
    print("Q1 ctVal BTC/contract =", CT_VAL_BTC)
    print("Q1 min/lot contracts =", Q1_MIN_CONTRACTS, "/", Q1_LOT_CONTRACTS)
    print("tick size =", TICK_SIZE)
    print("Lv1 taker fee per fill = 0.05% = 5 bps")
    print("funding records =", {d: len(v) for d, v in funding.items()})
    print("Q2/Validation/Final = CLOSED")
    print("alpha/execution P&L calculated = NO")


if __name__ == "__main__":
    main()
