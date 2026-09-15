"""SC001-E002 Q1 execution metadata + historical funding archive preflight v0.2.

No alpha, no execution P&L, no Q2/Validation/Final.

The v0.1 preflight failed closed because OKX's recent funding-rate REST endpoint
no longer returned the frozen 2024-Q1 dates in September 2026. This version uses
the official OKX historical market-data archive path already permitted by the
frozen economics protocol and documented by the funding-source amendment.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import time
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

STAGE = "SC001-E002-OKX-Q1-EXECUTION-METADATA-PREFLIGHT"
VERSION = "0.2"
INST = "BTC-USDT-SWAP"
INST_FAMILY = "BTC-USDT"
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
ARCHIVE_DIR = OUTDIR / "funding_archives_v0_2"
REPORT = OUTDIR / "sc001_e002_okx_q1_execution_metadata_preflight_v0_2.json"
FUNDING = OUTDIR / "sc001_e002_okx_q1_funding_rates_v0_2.json"

BASE = "https://www.okx.com"
UA = "BotMarketplace-SC001-E002-ExecutionMetadata/0.2"
TIMEOUT = 60
MAX_JSON_BYTES = 4_000_000
MAX_ARCHIVE_BYTES = 50_000_000
MAX_TOTAL_ARCHIVE_BYTES = 100_000_000
ALLOWED_HOST = "static.okx.com"

# OKX historical archive months are cut on UTC+8 month boundaries. This query
# covers the January and February 2024 monthly funding files only.
ARCHIVE_BEGIN_MS = 1704038400000  # 2023-12-31 16:00:00 UTC = 2024-01-01 00:00 UTC+8
ARCHIVE_END_MS = 1709308800000    # 2024-03-01 16:00:00 UTC


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def get_json(path: str, params: dict[str, str]) -> dict:
    url = BASE + path + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    last: Exception | None = None
    for attempt in range(3):
        try:
            with urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_JSON_BYTES + 1)
            if len(raw) > MAX_JSON_BYTES:
                raise RuntimeError("OKX JSON response exceeds safety cap")
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or obj.get("code") != "0":
                raise RuntimeError(f"OKX API response code mismatch: {obj!r}")
            return obj
        except Exception as exc:
            last = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"OKX request failed: {last!r}")


def current_instrument_snapshot() -> dict:
    obj = get_json("/api/v5/public/instruments", {"instType": "SWAP", "instId": INST})
    rows = obj.get("data") or []
    if len(rows) != 1 or rows[0].get("instId") != INST:
        raise RuntimeError("current instrument identity mismatch")
    row = rows[0]
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


def trusted_archive_url(url: str, filename: str) -> bool:
    try:
        p = urlparse(url)
        return (
            p.scheme == "https"
            and (p.hostname or "").lower() == ALLOWED_HOST
            and Path(p.path).name == filename
        )
    except Exception:
        return False


def historical_funding_files() -> list[dict]:
    obj = get_json(
        "/api/v5/public/market-data-history",
        {
            "module": "3",
            "instType": "SWAP",
            "instFamilyList": INST_FAMILY,
            "dateAggrType": "monthly",
            "begin": str(ARCHIVE_BEGIN_MS),
            "end": str(ARCHIVE_END_MS),
        },
    )
    data = obj.get("data")
    details = data.get("details") if isinstance(data, dict) else None
    if not isinstance(details, list):
        raise RuntimeError("market-data-history response missing data.details")

    files: dict[str, dict] = {}
    for detail in details:
        groups = detail.get("groupDetails") if isinstance(detail, dict) else None
        if not isinstance(groups, list):
            continue
        for g in groups:
            if not isinstance(g, dict):
                continue
            filename = g.get("filename") or g.get("fileName")
            url = g.get("url")
            if not isinstance(filename, str) or not isinstance(url, str):
                continue
            if not trusted_archive_url(url, filename):
                raise RuntimeError(f"untrusted historical funding archive URL: {filename} {url}")
            prev = files.get(filename)
            if prev is not None and prev.get("url") != url:
                raise RuntimeError(f"same funding filename returned with multiple URLs: {filename}")
            files[filename] = {
                "filename": filename,
                "url": url,
                "sizeMB_raw": g.get("sizeMB"),
            }

    if not files:
        raise RuntimeError("no official OKX historical funding archive files returned")
    return [files[k] for k in sorted(files)]


def download_archive(meta: dict) -> dict:
    filename = meta["filename"]
    url = meta["url"]
    dest = ARCHIVE_DIR / filename
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    if dest.exists() and 0 < dest.stat().st_size <= MAX_ARCHIVE_BYTES:
        return {**meta, "path": str(dest), "bytes": dest.stat().st_size, "sha256": sha256_file(dest), "reused": True}

    tmp = Path(str(dest) + ".part")
    if tmp.exists():
        tmp.unlink()
    req = Request(url, headers={"User-Agent": UA, "Referer": "https://www.okx.com/historical-data"})
    got = 0
    h = hashlib.sha256()
    with urlopen(req, timeout=TIMEOUT) as resp, tmp.open("wb") as out:
        final = resp.geturl()
        if not trusted_archive_url(final, filename):
            raise RuntimeError(f"funding archive redirected to untrusted identity: {final}")
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            got += len(chunk)
            if got > MAX_ARCHIVE_BYTES:
                raise RuntimeError(f"funding archive exceeds per-file safety cap: {filename}")
            out.write(chunk)
            h.update(chunk)
        out.flush()
        os.fsync(out.fileno())
    if got <= 0:
        raise RuntimeError(f"empty historical funding archive: {filename}")
    os.replace(tmp, dest)
    return {**meta, "path": str(dest), "bytes": got, "sha256": h.hexdigest(), "reused": False}


def finite_decimal(text: str) -> Decimal:
    try:
        x = Decimal(text.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"invalid decimal {text!r}") from exc
    if not x.is_finite():
        raise ValueError(f"non-finite decimal {text!r}")
    return x


def parse_archive(meta: dict) -> list[dict]:
    path = Path(meta["path"])
    rows: list[dict] = []
    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure in {path.name}: {bad}")
        members = [x for x in zf.infolist() if not x.is_dir()]
        if not members:
            raise RuntimeError(f"historical funding ZIP has no regular member: {path.name}")
        for info in members:
            if info.file_size > 100_000_000:
                raise RuntimeError(f"funding CSV member exceeds safety cap: {info.filename}")
            with zf.open(info, "r") as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
                reader = csv.reader(text)
                for fields in reader:
                    if not fields or len(fields) < 3:
                        continue
                    if fields[0] != INST:
                        continue
                    try:
                        rate = finite_decimal(fields[1])
                        ft = int(fields[2].strip())
                    except Exception:
                        # Header or malformed non-target row: fail only when it claims target instrument.
                        raise RuntimeError(f"malformed {INST} funding row in {path.name}: {fields!r}")
                    if ft <= 0:
                        raise RuntimeError(f"invalid funding timestamp in {path.name}: {ft}")
                    rows.append({
                        "instId": INST,
                        "fundingRate": format(rate, "f"),
                        "fundingTime": str(ft),
                        "fundingTimeUtc": datetime.fromtimestamp(ft / 1000, tz=timezone.utc).isoformat(),
                        "sourceArchive": path.name,
                        "sourceArchiveSha256": meta["sha256"],
                        "sourceMember": info.filename,
                    })
    return rows


def select_frozen_days(all_rows: list[dict]) -> dict[str, list[dict]]:
    by_ts: dict[int, dict] = {}
    for row in all_rows:
        ft = int(row["fundingTime"])
        prev = by_ts.get(ft)
        if prev is not None:
            if prev["fundingRate"] != row["fundingRate"]:
                raise RuntimeError(f"conflicting duplicate funding rate at {ft}")
            continue
        by_ts[ft] = row

    out: dict[str, list[dict]] = {d: [] for d in DATES}
    for ft, row in sorted(by_ts.items()):
        date_text = datetime.fromtimestamp(ft / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        if date_text in out:
            out[date_text].append(row)

    for d, rows in out.items():
        rows.sort(key=lambda x: int(x["fundingTime"]))
        if len(rows) != 3:
            raise RuntimeError(f"expected exactly 3 archived BTC-USDT-SWAP funding records on {d}, got {len(rows)}")
        hours = [datetime.fromtimestamp(int(x["fundingTime"]) / 1000, tz=timezone.utc).hour for x in rows]
        if hours != [0, 8, 16]:
            raise RuntimeError(f"unexpected archived funding schedule on {d}: hours={hours}")
    return out


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    current = current_instrument_snapshot()
    if current.get("ctType") != "linear" or current.get("ctValCcy") != "BTC" or current.get("settleCcy") != "USDT":
        raise RuntimeError(f"current instrument family mismatch: {current}")
    if current.get("ctVal") != CT_VAL_BTC or current.get("ctMult") != CONTRACT_MULTIPLIER or current.get("tickSz") != TICK_SIZE:
        raise RuntimeError(f"current ctVal/mult/tick no longer corroborates frozen metadata: {current}")

    listed = historical_funding_files()
    downloaded = [download_archive(x) for x in listed]
    total_bytes = sum(int(x["bytes"]) for x in downloaded)
    if total_bytes > MAX_TOTAL_ARCHIVE_BYTES:
        raise RuntimeError(f"historical funding downloads exceed total safety cap: {total_bytes}")

    all_rows: list[dict] = []
    for meta in downloaded:
        all_rows.extend(parse_archive(meta))
    funding = select_frozen_days(all_rows)

    atomic_json(FUNDING, {
        "stage": STAGE,
        "version": VERSION,
        "source": "OKX GET /api/v5/public/market-data-history module=3 monthly funding archives",
        "instrument": INST,
        "instrument_family": INST_FAMILY,
        "archive_query": {
            "module": "3",
            "instType": "SWAP",
            "instFamilyList": INST_FAMILY,
            "dateAggrType": "monthly",
            "begin": str(ARCHIVE_BEGIN_MS),
            "end": str(ARCHIVE_END_MS),
        },
        "archives": downloaded,
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
        "funding_source_amendment": "docs/research/sc001-e002-okx-q1-funding-source-amendment-v0.1.md",
        "current_instrument_snapshot_corroboration": current,
        "funding_file": str(FUNDING),
        "funding_archive_files": [x["filename"] for x in downloaded],
        "funding_archive_total_bytes": total_bytes,
        "funding_records_per_day": {d: len(v) for d, v in funding.items()},
        "alpha_calculated": False,
        "execution_pnl_calculated": False,
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(REPORT, report)

    print("EXECUTION_METADATA_PREFLIGHT_V0_2_PASS")
    print("instrument =", INST)
    print("Q1 ctVal BTC/contract =", CT_VAL_BTC)
    print("Q1 min/lot contracts =", Q1_MIN_CONTRACTS, "/", Q1_LOT_CONTRACTS)
    print("tick size =", TICK_SIZE)
    print("Lv1 taker fee per fill = 0.05% = 5 bps")
    print("funding source = OKX historical monthly archive, module 3")
    print("funding archive files =", [x["filename"] for x in downloaded])
    print("funding records =", {d: len(v) for d, v in funding.items()})
    print("Q2/Validation/Final = CLOSED")
    print("alpha/execution P&L calculated = NO")


if __name__ == "__main__":
    main()
