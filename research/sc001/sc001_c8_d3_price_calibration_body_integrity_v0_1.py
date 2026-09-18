from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C8-D3-PRICE-CALIBRATION-BODY-INTEGRITY-V0.1"
PASS = "C8_D3_PRICE_BODY_INTEGRITY_PASS"
REVIEW = "C8_D3_PRICE_BODY_INTEGRITY_REVIEW"

FIXED_DATE = "2025-01-20"
DAY_START_MS = 1737331200000
DAY_END_MS = 1737417600000
DAY_START_US = DAY_START_MS * 1000
DAY_END_US = DAY_END_MS * 1000

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
OKX_INST = "BTC-USDT-SWAP"
OKX_FAMILY = "BTC-USDT"
OKX_D = "BTC-USDT-SWAP-trades-2025-01-20.zip"
OKX_D1 = "BTC-USDT-SWAP-trades-2025-01-21.zip"
OKX_HOST = "static.okx.com"
OKX_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]

BYBIT_URL = "https://public.bybit.com/trading/BTCUSDT/BTCUSDT2025-01-20.csv.gz"
BYBIT_FILE = "BTCUSDT2025-01-20.csv.gz"
BYBIT_HOST = "public.bybit.com"

TIMEOUT = 120
RETRIES = 3
MAX_JSON_BYTES = 4_000_000
MAX_FILE_BYTES = 350 * 1024 * 1024
MAX_TOTAL_BYTES = 700 * 1024 * 1024
MIN_FREE_RESERVE = 5 * 1024**3
CHUNK = 1024 * 1024

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c8-d3-price-calibration-body-integrity-protocol-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.12.json"
FREEZE = ROOT / "docs/research/sc001-c8-d3-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D2_REPORT = (
    DATA_ROOT / "SC001_C8_D2_PRICE_CALIBRATION_METADATA"
    / "sc001_c8_d2_price_calibration_metadata_report_v0_1.json"
)

OUT_DIR = DATA_ROOT / "SC001_C8_D3_PRICE_CALIBRATION"
ARCHIVES = OUT_DIR / "archives"
NORMALIZED = OUT_DIR / "normalized"
OUT = OUT_DIR / "sc001_c8_d3_price_body_integrity_report_v0_1.json"

OKX_NORM = NORMALIZED / "okx_last_trade_1s.csv"
BYBIT_NORM = NORMALIZED / "bybit_last_trade_1s.csv"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        text=True,
    ).strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def require_freeze() -> dict:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_C8_D3_RUN":
        fail("C8-D3 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C8-D3 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C8-D3 protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("C8-D3 registry identity mismatch")
    if fr.get("fixed_date") != FIXED_DATE:
        fail("C8-D3 fixed date mismatch")
    if fr.get("okx_normalized_statistic") != "chronologically_last_trade_inside_active_second":
        fail("C8-D3 OKX statistic mismatch")
    if fr.get("bybit_normalized_statistic") != "chronologically_last_trade_inside_active_second":
        fail("C8-D3 Bybit statistic mismatch")
    for k in (
        "cross_venue_price_comparison_authorized",
        "cross_venue_return_authorized",
        "rolling_cross_venue_baseline_authorized",
        "raw_spread_authorized",
        "dislocation_authorized",
        "convergence_outcome_authorized",
        "strategy_signal_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C8-D3 firewall mismatch: {k}")
    return fr


def require_registry() -> dict:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.12":
        fail("registry version mismatch")
    row = reg.get("c8_price_selection_calibration") or {}
    if row.get("classification") != "NONPROMOTIONAL_SELECTION_CALIBRATION":
        fail("C8 price calibration classification mismatch")
    if row.get("target_utc_date") != FIXED_DATE:
        fail("C8 price calibration date mismatch")
    bodies = row.get("authorized_bodies") or []
    if bodies != [OKX_D, OKX_D1, BYBIT_FILE]:
        fail("C8-D3 authorized body list mismatch")
    return reg


def require_d2() -> dict:
    rep = load_json(D2_REPORT)
    if rep.get("status") != "C8_D2_PRICE_CALIBRATION_METADATA_PASS":
        fail("C8-D2 parent not exact PASS")
    if rep.get("fixed_date") != FIXED_DATE:
        fail("C8-D2 parent date mismatch")
    for k in (
        "historical_archive_body_downloaded",
        "historical_archive_body_opened",
        "cross_venue_price_compared",
        "cross_venue_return_calculated",
        "raw_spread_calculated",
        "dislocation_calculated",
        "lag_calculated",
        "strategy_signal_calculated",
        "pnl_calculated",
        "promotional_alpha_accessed",
    ):
        if rep.get(k) is not False:
            fail(f"C8-D2 parent firewall mismatch: {k}")
    files = rep.get("files") or []
    by_name = {x.get("filename"): x for x in files if isinstance(x, dict)}
    if set(by_name) != {OKX_D, OKX_D1, BYBIT_FILE}:
        fail("C8-D2 parent file set mismatch")
    return rep


def trusted_url(url: str, host: str, basename: str) -> bool:
    try:
        p = urllib.parse.urlparse(url)
        return (
            p.scheme == "https"
            and (p.hostname or "").lower() == host
            and Path(p.path).name == basename
        )
    except Exception:
        return False


def walk_nodes(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk_nodes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_nodes(v)


def resolve_okx_files() -> dict[str, str]:
    payload = {
        "module": "1",
        "instType": "SWAP",
        "instQueryParam": {"instFamilyList": [OKX_FAMILY]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(DAY_START_MS),
            "end": str(DAY_END_MS - 1),
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    expected = {OKX_D, OKX_D1}

    last = None
    for domain in OKX_DOMAINS:
        url = domain + "/priapi/v5/broker/public/trade-data/download-link?t=" + str(int(time.time()*1000))
        try:
            req = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C8-D3/0.1",
                    "Accept": "application/json,*/*",
                    "Content-Type": "application/json",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_JSON_BYTES + 1)
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
            if len(raw) > MAX_JSON_BYTES:
                fail("OKX metadata response cap exceeded")
            if status != 200:
                fail(f"OKX metadata HTTP {status}")
            p = urllib.parse.urlparse(final)
            if p.scheme != "https" or (p.hostname or "").lower() not in {"www.okx.com", "us.okx.com"}:
                fail(f"unexpected OKX metadata host: {p.hostname}")

            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                fail(f"OKX metadata code mismatch: {obj.get('code') if isinstance(obj, dict) else None}")

            found: dict[str, str] = {}
            for node in walk_nodes(obj.get("data")):
                if not isinstance(node, dict):
                    continue
                fn = node.get("filename") or node.get("fileName")
                u = node.get("url")
                if (
                    fn in expected
                    and isinstance(u, str)
                    and trusted_url(u, OKX_HOST, str(fn))
                ):
                    prev = found.get(str(fn))
                    if prev is not None and prev != u:
                        fail(f"conflicting OKX URLs for {fn}")
                    found[str(fn)] = u
            if set(found) == expected:
                return found

            last = RuntimeError(f"missing OKX files: {sorted(found)}")
        except Exception as exc:
            last = exc
            continue

    raise RuntimeError(f"OKX exact file resolution failed: {type(last).__name__}: {last}")


def head_size(url: str, host: str, basename: str) -> int:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "BotMarketplace-SC001-C8-D3/0.1"},
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                cl = resp.headers.get("Content-Length")
            if status != 200:
                fail(f"HEAD HTTP {status}: {basename}")
            if not trusted_url(final, host, basename):
                fail(f"HEAD identity mismatch: {basename}")
            if not cl or not cl.isdigit() or int(cl) <= 0:
                fail(f"invalid Content-Length: {basename}")
            return int(cl)
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"HEAD failed {basename}: {type(last).__name__}: {last}")


def download_exact(url: str, host: str, basename: str, expected_size: int) -> tuple[Path, bool]:
    if expected_size <= 0 or expected_size > MAX_FILE_BYTES:
        fail(f"file size outside cap: {basename} {expected_size}")
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    dest = ARCHIVES / basename
    if dest.exists() and dest.stat().st_size == expected_size:
        return dest, True
    if dest.exists():
        dest.unlink()

    tmp = Path(str(dest) + ".part")
    tmp.unlink(missing_ok=True)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "BotMarketplace-SC001-C8-D3/0.1",
            "Referer": "https://www.okx.com/historical-data" if host == OKX_HOST else "https://public.bybit.com/",
        },
    )

    got = 0
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp, tmp.open("wb") as out:
        final = resp.geturl()
        if not trusted_url(final, host, basename):
            fail(f"GET identity mismatch: {basename}")
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            got += len(chunk)
            if got > expected_size or got > MAX_FILE_BYTES:
                fail(f"download overflow: {basename}")
            out.write(chunk)
        out.flush()
        os.fsync(out.fileno())

    if got != expected_size:
        fail(f"download size mismatch {basename}: {got} != {expected_size}")
    os.replace(tmp, dest)
    return dest, False


def normalize_okx_ts_us(text: str) -> tuple[int, str]:
    v = int(str(text).strip())
    a = abs(v)
    if a >= 10**17:
        return v // 1000, "nanoseconds"
    if a >= 10**14:
        return v, "microseconds"
    if a >= 10**11:
        return v * 1000, "milliseconds"
    if a >= 10**9:
        return v * 1_000_000, "seconds"
    fail(f"unresolved OKX timestamp scale: {text}")


def scan_okx(path: Path, expected_filename: str, state: dict) -> dict:
    expected_member = expected_filename[:-4] + ".csv"
    source = {
        "filename": expected_filename,
        "source_rows": 0,
        "invalid_rows": 0,
        "timestamp_reversals": 0,
        "trade_id_nonmonotonic": 0,
        "timestamp_scales": set(),
    }

    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {expected_filename}: {bad}")
        members = [x for x in zf.infolist() if not x.is_dir()]
        if len(members) != 1:
            fail(f"ZIP member count mismatch: {expected_filename}")
        if Path(members[0].filename).name != expected_member:
            fail(f"ZIP member identity mismatch: {members[0].filename}")

        with zf.open(members[0], "r") as raw:
            r = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
            header = next(r, None)
            if header != OKX_HEADER:
                fail(f"OKX header mismatch: {expected_filename}")

            prev_source_ts = None
            prev_source_id = None

            for row in r:
                if not row:
                    continue
                if len(row) != 6:
                    source["invalid_rows"] += 1
                    continue
                try:
                    if row[0] != OKX_INST:
                        raise ValueError("instrument")
                    tid = int(row[1])
                    side = row[2]
                    price = float(row[3])
                    size = float(row[4])
                    ts, scale = normalize_okx_ts_us(row[5])
                    if side not in {"buy", "sell"}:
                        raise ValueError("side")
                    if not (
                        math.isfinite(price) and price > 0
                        and math.isfinite(size) and size > 0
                    ):
                        raise ValueError("price/size")
                except Exception:
                    source["invalid_rows"] += 1
                    continue

                source["source_rows"] += 1
                source["timestamp_scales"].add(scale)

                if prev_source_ts is not None and ts < prev_source_ts:
                    source["timestamp_reversals"] += 1
                if prev_source_id is not None and tid <= prev_source_id:
                    source["trade_id_nonmonotonic"] += 1
                prev_source_ts = ts
                prev_source_id = tid

                if DAY_START_US <= ts < DAY_END_US:
                    if state["prev_ts"] is not None and ts < state["prev_ts"]:
                        state["timestamp_reversals"] += 1
                    if state["prev_id"] is not None:
                        d = tid - state["prev_id"]
                        if d <= 0:
                            state["trade_id_nonmonotonic"] += 1
                        elif d != 1:
                            state["trade_id_gap_count"] += 1

                    sec = ts // 1_000_000
                    state["last_by_second"][sec] = (ts, price)
                    state["minutes"].add((ts - DAY_START_US) // 60_000_000)
                    state["hours"].add((ts - DAY_START_US) // 3_600_000_000)
                    state["sides"].add(side)
                    state["prev_ts"] = ts
                    state["prev_id"] = tid
                    state["admitted_rows"] += 1

    source["timestamp_scales"] = sorted(source["timestamp_scales"])
    return source


def parse_okx(d: Path, d1: Path) -> dict:
    state = {
        "last_by_second": {},
        "minutes": set(),
        "hours": set(),
        "sides": set(),
        "prev_ts": None,
        "prev_id": None,
        "timestamp_reversals": 0,
        "trade_id_nonmonotonic": 0,
        "trade_id_gap_count": 0,
        "admitted_rows": 0,
    }
    a = scan_okx(d, OKX_D, state)
    b = scan_okx(d1, OKX_D1, state)
    return {
        "last_by_second": state["last_by_second"],
        "admitted_rows": state["admitted_rows"],
        "minute_buckets": len(state["minutes"]),
        "active_hours": len(state["hours"]),
        "buy_and_sell": state["sides"] == {"buy", "sell"},
        "timestamp_reversals": state["timestamp_reversals"],
        "trade_id_nonmonotonic": state["trade_id_nonmonotonic"],
        "trade_id_gap_count": state["trade_id_gap_count"],
        "sources": [a, b],
    }


def parse_bybit(path: Path) -> dict:
    last_by_second = {}
    invalid = out_of_day = reversals = 0
    prev_ts = None
    minutes = set()
    hours = set()

    with gzip.open(path, "rt", encoding="utf-8", errors="strict", newline="") as f:
        r = csv.reader(f)
        header = next(r, None)
        if not header or len(header) < 5:
            fail("Bybit header missing/short")
        low = [str(x).strip().lower() for x in header]
        if low[:5] != ["timestamp", "symbol", "side", "size", "price"]:
            fail(f"Bybit header semantics mismatch: {header[:5]}")

        for row in r:
            if not row:
                continue
            if len(row) < 5:
                invalid += 1
                continue
            try:
                ts = int(round(float(row[0]) * 1_000_000))
                if row[1].strip() != "BTCUSDT":
                    raise ValueError("symbol")
                side = row[2].strip()
                size = float(row[3])
                price = float(row[4])
                if side not in {"Buy", "Sell"}:
                    raise ValueError("side")
                if not (
                    math.isfinite(size) and size > 0
                    and math.isfinite(price) and price > 0
                ):
                    raise ValueError("price/size")
            except Exception:
                invalid += 1
                continue

            if not (DAY_START_US <= ts < DAY_END_US):
                out_of_day += 1
                continue
            if prev_ts is not None and ts < prev_ts:
                reversals += 1
            prev_ts = ts

            sec = ts // 1_000_000
            last_by_second[sec] = (ts, price)
            minutes.add((ts - DAY_START_US) // 60_000_000)
            hours.add((ts - DAY_START_US) // 3_600_000_000)

    return {
        "last_by_second": last_by_second,
        "invalid_rows": invalid,
        "out_of_day_rows": out_of_day,
        "timestamp_reversals": reversals,
        "minute_buckets": len(minutes),
        "active_hours": len(hours),
    }


def write_norm(path: Path, rows: dict[int, tuple[int, float]]) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["second_id", "last_trade_ts_us", "last_trade_price"])
        for sec in sorted(rows):
            ts, price = rows[sec]
            w.writerow([sec, ts, format(price, ".12g")])
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    return {
        "path": str(path),
        "rows": len(rows),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def main() -> int:
    try:
        require_freeze()
        require_registry()
        d2 = require_d2()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        by_name = {x["filename"]: x for x in d2["files"]}
        okx_d_expected = int(by_name[OKX_D]["content_length"])
        okx_d1_expected = int(by_name[OKX_D1]["content_length"])
        bybit_expected = int(by_name[BYBIT_FILE]["content_length"])

        total_expected = okx_d_expected + okx_d1_expected + bybit_expected
        if total_expected > MAX_TOTAL_BYTES:
            fail("combined archive cap exceeded")
        if shutil.disk_usage(OUT_DIR).free < total_expected + MIN_FREE_RESERVE:
            fail("insufficient disk reserve")

        print("C8-D3 resolve exact source URLs", flush=True)
        okx_urls = resolve_okx_files()
        if head_size(okx_urls[OKX_D], OKX_HOST, OKX_D) != okx_d_expected:
            fail("OKX D HEAD size changed from D2")
        if head_size(okx_urls[OKX_D1], OKX_HOST, OKX_D1) != okx_d1_expected:
            fail("OKX D+1 HEAD size changed from D2")
        if head_size(BYBIT_URL, BYBIT_HOST, BYBIT_FILE) != bybit_expected:
            fail("Bybit HEAD size changed from D2")

        print("C8-D3 download/reuse OKX D", flush=True)
        p_okx_d, reused_okx_d = download_exact(
            okx_urls[OKX_D], OKX_HOST, OKX_D, okx_d_expected
        )
        print("C8-D3 download/reuse OKX D+1", flush=True)
        p_okx_d1, reused_okx_d1 = download_exact(
            okx_urls[OKX_D1], OKX_HOST, OKX_D1, okx_d1_expected
        )
        print("C8-D3 download/reuse Bybit D", flush=True)
        p_bybit, reused_bybit = download_exact(
            BYBIT_URL, BYBIT_HOST, BYBIT_FILE, bybit_expected
        )

        print("C8-D3 parse/stitch OKX UTC day", flush=True)
        okx = parse_okx(p_okx_d, p_okx_d1)
        print("C8-D3 parse Bybit UTC day", flush=True)
        bybit = parse_bybit(p_bybit)

        okx_norm = write_norm(OKX_NORM, okx["last_by_second"])
        bybit_norm = write_norm(BYBIT_NORM, bybit["last_by_second"])

        gates = {
            "okx_source_integrity": (
                okx["timestamp_reversals"] == 0
                and okx["trade_id_nonmonotonic"] == 0
                and okx["trade_id_gap_count"] == 0
                and okx["minute_buckets"] == 1440
                and okx["active_hours"] == 24
                and okx["buy_and_sell"] is True
                and all(
                    s["invalid_rows"] == 0
                    and s["timestamp_reversals"] == 0
                    and s["trade_id_nonmonotonic"] == 0
                    and len(s["timestamp_scales"]) == 1
                    for s in okx["sources"]
                )
            ),
            "bybit_source_integrity": (
                bybit["invalid_rows"] == 0
                and bybit["out_of_day_rows"] == 0
                and bybit["timestamp_reversals"] == 0
                and bybit["minute_buckets"] == 1440
                and bybit["active_hours"] == 24
            ),
            "okx_active_seconds_gte70000": okx_norm["rows"] >= 70_000,
            "bybit_active_seconds_gte70000": bybit_norm["rows"] >= 70_000,
        }

        status = PASS if all(gates.values()) else REVIEW

        report = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "fixed_date": FIXED_DATE,
            "selection_calibration_role": "NONPROMOTIONAL_SELECTION_CALIBRATION",
            "source_archives": [
                {
                    "filename": OKX_D,
                    "bytes": p_okx_d.stat().st_size,
                    "sha256": sha256_file(p_okx_d),
                    "reused": reused_okx_d,
                },
                {
                    "filename": OKX_D1,
                    "bytes": p_okx_d1.stat().st_size,
                    "sha256": sha256_file(p_okx_d1),
                    "reused": reused_okx_d1,
                },
                {
                    "filename": BYBIT_FILE,
                    "bytes": p_bybit.stat().st_size,
                    "sha256": sha256_file(p_bybit),
                    "reused": reused_bybit,
                },
            ],
            "okx": {
                "admitted_rows": okx["admitted_rows"],
                "active_seconds": okx_norm["rows"],
                "minute_buckets": okx["minute_buckets"],
                "active_hours": okx["active_hours"],
                "normalized_file": okx_norm,
            },
            "bybit": {
                "active_seconds": bybit_norm["rows"],
                "minute_buckets": bybit["minute_buckets"],
                "active_hours": bybit["active_hours"],
                "normalized_file": bybit_norm,
            },
            "gates": gates,
            "failed_gates": [k for k, v in gates.items() if not v],
            "historical_trade_bodies_opened": True,
            "per_venue_prices_normalized": True,
            "cross_venue_price_compared": False,
            "cross_venue_return_calculated": False,
            "rolling_cross_venue_baseline_calculated": False,
            "raw_spread_calculated": False,
            "dislocation_calculated": False,
            "convergence_outcome_calculated": False,
            "strategy_signal_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, report)

        print(status)
        print("OKX active_seconds =", okx_norm["rows"])
        print("Bybit active_seconds =", bybit_norm["rows"])
        print("OKX minutes/hours =", okx["minute_buckets"], "/", okx["active_hours"])
        print("Bybit minutes/hours =", bybit["minute_buckets"], "/", bybit["active_hours"])
        print("failed_gates =", report["failed_gates"])
        print("cross-venue price/return/baseline/spread/dislocation/convergence = False")
        print("signal/PnL/promotional alpha = False")
        print("report =", OUT)
        return 0 if status == PASS else 2

    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "version": "0.1",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "historical_trade_bodies_opened": False,
            "per_venue_prices_normalized": False,
            "cross_venue_price_compared": False,
            "cross_venue_return_calculated": False,
            "rolling_cross_venue_baseline_calculated": False,
            "raw_spread_calculated": False,
            "dislocation_calculated": False,
            "convergence_outcome_calculated": False,
            "strategy_signal_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
        }
        try:
            atomic_json(OUT, fail_rep)
        except Exception:
            pass
        print(REVIEW)
        print("error =", fail_rep["error"])
        print("report =", OUT)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
