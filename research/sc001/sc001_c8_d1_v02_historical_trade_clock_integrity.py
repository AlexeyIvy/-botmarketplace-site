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

STAGE = "SC001-C8-D1-V0.2-HISTORICAL-TRADE-CLOCK-INTEGRITY"
PASS = "C8_D1_V02_HISTORICAL_CLOCK_INTEGRITY_PASS"
REVIEW = "C8_D1_V02_HISTORICAL_CLOCK_INTEGRITY_REVIEW"
GOLDEN_PASS = "C8_D1_SYNC_GOLDEN_PASS"

FIXED_DATE = "2025-01-15"
DAY_START_US = 1736899200000 * 1000
DAY_END_US = 1736985600000 * 1000

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
OKX_INST = "BTC-USDT-SWAP"
OKX_FAMILY = "BTC-USDT"
OKX_FILENAME = "BTC-USDT-SWAP-trades-2025-01-15.zip"
OKX_NEIGHBOR_FILENAME = "BTC-USDT-SWAP-trades-2025-01-16.zip"
OKX_HOST = "static.okx.com"
OKX_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]

BYBIT_URL = "https://public.bybit.com/trading/BTCUSDT/BTCUSDT2025-01-15.csv.gz"
BYBIT_FILENAME = "BTCUSDT2025-01-15.csv.gz"
BYBIT_HOST = "public.bybit.com"

GRID_US = 1_000_000
STALE_US = 2_000_000
GRID_START_US = DAY_START_US + GRID_US
GRID_END_US = DAY_END_US  # exclusive
EXPECTED_GRID = 86_399

TIMEOUT = 120
RETRIES = 3
MAX_RESPONSE_BYTES = 4_000_000
MAX_FILE_BYTES = 350 * 1024 * 1024
MAX_TOTAL_BYTES = 700 * 1024 * 1024
MIN_FREE_RESERVE = 5 * 1024**3
CHUNK = 1024 * 1024

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c8-d1-historical-trade-clock-integrity-protocol-v0.2.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.11.json"
FREEZE = ROOT / "docs/research/sc001-c8-d1-v0.2-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D0_REPORT = (
    DATA_ROOT / "SC001_C8_D0_V03_SOURCE_CLOCK"
    / "sc001_c8_d0_v03_source_clock_preflight_v0_1.json"
)

OUT_DIR = DATA_ROOT / "SC001_C8_D1_V02_HISTORICAL_CLOCK"
ARCHIVES = DATA_ROOT / "SC001_C8_D1_HISTORICAL_CLOCK" / "archives"
OUT = OUT_DIR / "sc001_c8_d1_v02_historical_clock_integrity_report_v0_1.json"


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
    if fr.get("status") != "FROZEN_BEFORE_C8_D1_V02_RUN":
        fail("C8-D1 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C8-D1 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C8-D1 protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("C8-D1 registry identity mismatch")
    if fr.get("fixed_date") != FIXED_DATE:
        fail("C8-D1 fixed date mismatch")
    if int(fr.get("sync_grid_ms", 0)) != 1000:
        fail("C8-D1 sync grid mismatch")
    if int(fr.get("staleness_limit_ms", 0)) != 2000:
        fail("C8-D1 staleness mismatch")
    for k in (
        "cross_venue_price_comparison_authorized",
        "cross_venue_return_authorized",
        "dislocation_authorized",
        "lag_authorized",
        "leader_selection_authorized",
        "strategy_signal_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C8-D1 firewall mismatch: {k}")
    return fr


def require_registry() -> dict:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.11":
        fail("registry version mismatch")
    row = reg.get("c8_d1_v02_engineering_clock_calibration") or {}
    if row.get("classification") != "NONPROMOTIONAL_ENGINEERING_CLOCK_CALIBRATION":
        fail("C8-D1 registry classification mismatch")
    if row.get("target_utc_date") != FIXED_DATE:
        fail("C8-D1 registry date mismatch")
    bodies = row.get("authorized_bodies") or []
    if bodies != [OKX_FILENAME, OKX_NEIGHBOR_FILENAME, BYBIT_FILENAME]:
        fail("C8-D1 authorized body list mismatch")
    return reg


def require_d0() -> dict:
    d0 = load_json(D0_REPORT)
    if d0.get("status") != "C8_D0_V03_SOURCE_CLOCK_PREFLIGHT_PASS":
        fail("C8-D0 parent not exact PASS")
    if sum(1 for x in (d0.get("checks") or {}).values() if x.get("pass") is True) != 6:
        fail("C8-D0 parent check count mismatch")
    for k in (
        "historical_archive_body_downloaded",
        "historical_archive_body_opened",
        "cross_venue_price_compared",
        "cross_venue_return_calculated",
        "dislocation_calculated",
        "lag_calculated",
        "leader_selected",
        "strategy_signal_calculated",
        "pnl_calculated",
        "promotional_alpha_accessed",
    ):
        if d0.get(k) is not False:
            fail(f"C8-D0 parent firewall mismatch: {k}")
    return d0


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


def resolve_okx_urls() -> dict[str, str]:
    payload = {
        "module": "1",
        "instType": "SWAP",
        "instQueryParam": {"instFamilyList": [OKX_FAMILY]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": "1736899200000",
            "end": "1736985599999",
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    expected = {OKX_FILENAME, OKX_NEIGHBOR_FILENAME}

    last = None
    for domain in OKX_DOMAINS:
        url = domain + "/priapi/v5/broker/public/trade-data/download-link?t=" + str(int(time.time()*1000))
        try:
            req = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C8-D1-v0.2",
                    "Accept": "application/json,*/*",
                    "Content-Type": "application/json",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                fail("OKX resolver response cap exceeded")
            obj = json.loads(raw.decode("utf-8"))
            if str(obj.get("code")) != "0":
                fail(f"OKX resolver code={obj.get('code')}")

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
        except Exception as exc:
            last = exc
            continue

    raise RuntimeError(
        f"OKX D/D+1 resolver failed: {type(last).__name__}: {last}"
    )


def head_size(url: str, host: str, basename: str) -> int:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "BotMarketplace-SC001-C8-D1/0.1"},
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
    if expected_size > MAX_FILE_BYTES:
        fail(f"file exceeds cap: {basename} {expected_size}")
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
        headers={"User-Agent": "BotMarketplace-SC001-C8-D1/0.1"},
    )
    total = 0
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp, tmp.open("wb") as out:
        final = resp.geturl()
        if not trusted_url(final, host, basename):
            fail(f"GET identity mismatch: {basename}")
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > expected_size or total > MAX_FILE_BYTES:
                fail(f"download overflow: {basename}")
            out.write(chunk)
        out.flush()
        os.fsync(out.fileno())
    if total != expected_size:
        fail(f"download size mismatch {basename}: {total} != {expected_size}")
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


def scan_okx_archive(path: Path, expected_filename: str, stitch: dict) -> dict:
    expected_member = expected_filename[:-4] + ".csv"
    source = {
        "filename": expected_filename,
        "row_count": 0,
        "invalid_rows": 0,
        "timestamp_reversals": 0,
        "trade_id_nonmonotonic": 0,
        "same_timestamp_adjacent": 0,
        "timestamp_scales": [],
        "first_ts_us": None,
        "last_ts_us": None,
    }
    scales = set()

    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"OKX ZIP CRC failure {expected_filename}: {bad}")
        members = [x for x in zf.infolist() if not x.is_dir()]
        if len(members) != 1:
            fail(f"OKX ZIP member count {len(members)} != 1: {expected_filename}")
        if Path(members[0].filename).name != expected_member:
            fail(f"OKX member mismatch {members[0].filename} != {expected_member}")

        with zf.open(members[0], "r") as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
            header = next(reader, None)
            if header != OKX_HEADER:
                fail(f"OKX header mismatch {expected_filename}: {header}")

            prev_source_ts = None
            prev_source_id = None

            for row in reader:
                if not row:
                    continue
                if len(row) != 6:
                    source["invalid_rows"] += 1
                    continue
                try:
                    inst = row[0]
                    tid = int(row[1])
                    side = row[2]
                    price = float(row[3])
                    size = float(row[4])
                    ts, scale = normalize_okx_ts_us(row[5])
                    if inst != OKX_INST:
                        raise ValueError("instrument")
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

                source["row_count"] += 1
                scales.add(scale)
                if source["first_ts_us"] is None:
                    source["first_ts_us"] = ts
                source["last_ts_us"] = ts

                if prev_source_ts is not None:
                    if ts < prev_source_ts:
                        source["timestamp_reversals"] += 1
                    elif ts == prev_source_ts:
                        source["same_timestamp_adjacent"] += 1
                if prev_source_id is not None and tid <= prev_source_id:
                    source["trade_id_nonmonotonic"] += 1
                prev_source_ts = ts
                prev_source_id = tid

                if DAY_START_US <= ts < DAY_END_US:
                    if stitch["prev_ts"] is not None:
                        if ts < stitch["prev_ts"]:
                            stitch["timestamp_reversals"] += 1
                        elif ts == stitch["prev_ts"]:
                            stitch["same_timestamp_adjacent"] += 1
                    if stitch["prev_id"] is not None:
                        delta = tid - stitch["prev_id"]
                        if delta <= 0:
                            stitch["trade_id_nonmonotonic"] += 1
                        elif delta != 1:
                            stitch["trade_id_gap_count"] += 1

                    stitch["timestamps"].append(ts)
                    stitch["prev_ts"] = ts
                    stitch["prev_id"] = tid
                    stitch["minutes"].add((ts - DAY_START_US) // 60_000_000)
                    stitch["sides"].add(side)
                    stitch["admitted_rows"] += 1

    source["timestamp_scales"] = sorted(scales)
    return source


def parse_okx_stitched(path_d: Path, path_d1: Path) -> dict:
    stitch = {
        "timestamps": [],
        "prev_ts": None,
        "prev_id": None,
        "timestamp_reversals": 0,
        "same_timestamp_adjacent": 0,
        "trade_id_nonmonotonic": 0,
        "trade_id_gap_count": 0,
        "minutes": set(),
        "sides": set(),
        "admitted_rows": 0,
    }

    source_d = scan_okx_archive(path_d, OKX_FILENAME, stitch)
    source_d1 = scan_okx_archive(path_d1, OKX_NEIGHBOR_FILENAME, stitch)

    scale_union = sorted(
        set(source_d["timestamp_scales"]) | set(source_d1["timestamp_scales"])
    )

    return {
        "timestamps": stitch["timestamps"],
        "row_count": stitch["admitted_rows"],
        "invalid_rows": source_d["invalid_rows"] + source_d1["invalid_rows"],
        "timestamp_reversals": stitch["timestamp_reversals"],
        "same_timestamp_adjacent": stitch["same_timestamp_adjacent"],
        "trade_id_nonmonotonic": stitch["trade_id_nonmonotonic"],
        "trade_id_gap_count": stitch["trade_id_gap_count"],
        "minute_buckets_observed": len(stitch["minutes"]),
        "buy_and_sell_observed": stitch["sides"] == {"buy", "sell"},
        "timestamp_scales": scale_union,
        "sources": [source_d, source_d1],
    }


def parse_bybit(path: Path) -> dict:
    timestamps = []
    invalid = out_of_day = reversals = same_ts = 0
    header = None

    with gzip.open(path, "rt", encoding="utf-8", errors="strict", newline="") as f:
        r = csv.reader(f)
        header = next(r, None)
        if not header or len(header) < 5:
            fail("Bybit header missing/short")
        low = [str(x).strip().lower() for x in header]
        if (
            low[0] != "timestamp"
            or low[1] != "symbol"
            or low[2] != "side"
            or low[3] != "size"
            or low[4] != "price"
        ):
            fail(f"Bybit first-five header semantics mismatch: {header[:5]}")
        prev_ts = None
        for row in r:
            if not row:
                continue
            if len(row) < 5:
                invalid += 1
                continue
            try:
                ts = int(round(float(row[0]) * 1_000_000))
                symbol = row[1].strip()
                side = row[2].strip()
                size = float(row[3]); price = float(row[4])
                if symbol != "BTCUSDT":
                    raise ValueError("symbol")
                if side not in {"Buy", "Sell"}:
                    raise ValueError("side")
                if not (math.isfinite(size) and size > 0 and math.isfinite(price) and price > 0):
                    raise ValueError("price/size")
            except Exception:
                invalid += 1
                continue
            if not (DAY_START_US <= ts < DAY_END_US):
                out_of_day += 1
            if prev_ts is not None:
                if ts < prev_ts:
                    reversals += 1
                elif ts == prev_ts:
                    same_ts += 1
            prev_ts = ts
            timestamps.append(ts)

    return {
        "timestamps": timestamps,
        "row_count": len(timestamps),
        "invalid_rows": invalid,
        "out_of_day_rows": out_of_day,
        "timestamp_reversals": reversals,
        "same_timestamp_adjacent": same_ts,
        "header": header,
        "timestamp_scale": "seconds_fractional_to_microseconds",
    }


def percentile_nearest(values: list[int], q: float) -> int | None:
    if not values:
        return None
    vals = sorted(values)
    idx = max(0, min(len(vals)-1, int(math.ceil(q * len(vals))) - 1))
    return vals[idx]


def max_gap_us(ts: list[int]) -> int | None:
    if len(ts) < 2:
        return None
    return max(b-a for a,b in zip(ts, ts[1:]))


def asof_staleness(ts: list[int], boundary: int) -> int | None:
    import bisect
    i = bisect.bisect_right(ts, boundary) - 1
    if i < 0:
        return None
    age = boundary - ts[i]
    return age if age <= STALE_US else None


def sync_metrics(ts: list[int]) -> dict:
    stale = []
    usable = 0
    for boundary in range(GRID_START_US, GRID_END_US, GRID_US):
        age = asof_staleness(ts, boundary)
        if age is not None:
            usable += 1
            stale.append(age)
    if usable + (EXPECTED_GRID - usable) != EXPECTED_GRID:
        fail("grid accounting error")
    return {
        "grid_points": EXPECTED_GRID,
        "usable_grid_points": usable,
        "usable_share": usable / EXPECTED_GRID,
        "median_staleness_ms": (
            statistics_median_int(stale) / 1000.0 if stale else None
        ),
        "p99_staleness_ms": (
            percentile_nearest(stale, 0.99) / 1000.0 if stale else None
        ),
    }


def statistics_median_int(values: list[int]) -> float:
    vals = sorted(values)
    n = len(vals)
    if n == 0:
        raise ValueError("empty")
    m = n // 2
    return float(vals[m]) if n % 2 else (vals[m-1] + vals[m]) / 2.0


def joint_sync_metrics(a: list[int], b: list[int]) -> dict:
    joint = 0
    for boundary in range(GRID_START_US, GRID_END_US, GRID_US):
        if asof_staleness(a, boundary) is not None and asof_staleness(b, boundary) is not None:
            joint += 1
    return {
        "grid_points": EXPECTED_GRID,
        "joint_usable_grid_points": joint,
        "joint_usable_share": joint / EXPECTED_GRID,
    }


def asof_selected_ts(ts: list[int], boundary: int) -> int | None:
    import bisect
    i = bisect.bisect_right(ts, boundary) - 1
    if i < 0:
        return None
    selected = ts[i]
    return selected if boundary - selected <= STALE_US else None


def golden_tests() -> None:
    sample = [1_000_000, 2_000_000, 4_000_000]
    selected_seq = [
        asof_selected_ts(sample, b)
        for b in (1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000)
    ]
    finite_selected = [x for x in selected_seq if x is not None]
    checks = [
        asof_staleness(sample, 500_000) is None,
        asof_staleness(sample, 2_000_000) == 0,
        asof_staleness(sample, 6_000_000) == 2_000_000,
        asof_staleness(sample, 6_000_001) is None,
        asof_selected_ts(sample, 2_000_000) == 2_000_000,
        finite_selected == sorted(finite_selected),
    ]
    if not all(checks):
        fail("C8-D1 synchronization golden check failed")
    print(GOLDEN_PASS)


def main() -> int:
    try:
        require_freeze()
        require_registry()
        d0 = require_d0()
        golden_tests()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        checks = d0.get("checks") or {}
        okx_parent = checks.get("okx_historical_archive") or {}
        bybit_parent = checks.get("bybit_historical_archive") or {}
        okx_expected = int(okx_parent.get("content_length", 0))
        bybit_expected = int(bybit_parent.get("content_length", 0))
        if okx_expected <= 0 or bybit_expected <= 0:
            fail("D0 content length missing")
        okx_urls = resolve_okx_urls()
        okx_url = okx_urls[OKX_FILENAME]
        neighbor_url = okx_urls[OKX_NEIGHBOR_FILENAME]

        if head_size(okx_url, OKX_HOST, OKX_FILENAME) != okx_expected:
            fail("OKX D HEAD size changed from D0")
        neighbor_expected = head_size(
            neighbor_url, OKX_HOST, OKX_NEIGHBOR_FILENAME
        )
        if head_size(BYBIT_URL, BYBIT_HOST, BYBIT_FILENAME) != bybit_expected:
            fail("Bybit HEAD size changed from D0")

        total_expected = okx_expected + neighbor_expected + bybit_expected
        if total_expected > MAX_TOTAL_BYTES:
            fail("combined archive sizes exceed D1 v0.2 cap")
        if shutil.disk_usage(OUT_DIR).free < total_expected + MIN_FREE_RESERVE:
            fail("insufficient disk reserve")

        print("C8-D1-v0.2 download/reuse OKX D body", flush=True)
        okx_path, okx_reused = download_exact(
            okx_url, OKX_HOST, OKX_FILENAME, okx_expected
        )
        print("C8-D1-v0.2 download/reuse OKX D+1 body", flush=True)
        neighbor_path, neighbor_reused = download_exact(
            neighbor_url, OKX_HOST, OKX_NEIGHBOR_FILENAME, neighbor_expected
        )
        print("C8-D1-v0.2 download/reuse Bybit body", flush=True)
        bybit_path, bybit_reused = download_exact(
            BYBIT_URL, BYBIT_HOST, BYBIT_FILENAME, bybit_expected
        )

        print("C8-D1-v0.2 parse/stitch OKX UTC day", flush=True)
        okx = parse_okx_stitched(okx_path, neighbor_path)
        print("C8-D1 parse Bybit timestamps/schema", flush=True)
        bybit = parse_bybit(bybit_path)

        okx_sync = sync_metrics(okx["timestamps"])
        bybit_sync = sync_metrics(bybit["timestamps"])
        joint = joint_sync_metrics(okx["timestamps"], bybit["timestamps"])

        okx_gap = max_gap_us(okx["timestamps"])
        bybit_gap = max_gap_us(bybit["timestamps"])

        gates = {
            "okx_zero_invalid": okx["invalid_rows"] == 0,
            "bybit_zero_invalid": bybit["invalid_rows"] == 0,
            "bybit_zero_out_of_day": bybit["out_of_day_rows"] == 0,
            "okx_zero_timestamp_reversals": okx["timestamp_reversals"] == 0,
            "bybit_zero_timestamp_reversals": bybit["timestamp_reversals"] == 0,
            "okx_trade_id_strict": okx["trade_id_nonmonotonic"] == 0,
            "okx_trade_id_gaps_zero": okx["trade_id_gap_count"] == 0,
            "okx_all_1440_minutes": okx["minute_buckets_observed"] == 1440,
            "okx_buy_and_sell": okx["buy_and_sell_observed"] is True,
            "okx_single_timestamp_scale": len(okx["timestamp_scales"]) == 1,
            "okx_source_integrity": all(
                s["invalid_rows"] == 0
                and s["timestamp_reversals"] == 0
                and s["trade_id_nonmonotonic"] == 0
                and len(s["timestamp_scales"]) == 1
                for s in okx["sources"]
            ),
            "okx_grid_share_gte098": okx_sync["usable_share"] >= 0.98,
            "bybit_grid_share_gte098": bybit_sync["usable_share"] >= 0.98,
            "joint_grid_share_gte095": joint["joint_usable_share"] >= 0.95,
            "okx_p99_staleness_lte1000ms": (
                okx_sync["p99_staleness_ms"] is not None
                and okx_sync["p99_staleness_ms"] <= 1000.0
            ),
            "bybit_p99_staleness_lte1000ms": (
                bybit_sync["p99_staleness_ms"] is not None
                and bybit_sync["p99_staleness_ms"] <= 1000.0
            ),
            "okx_max_gap_lte5s": okx_gap is not None and okx_gap <= 5_000_000,
            "bybit_max_gap_lte5s": bybit_gap is not None and bybit_gap <= 5_000_000,
        }

        status = PASS if all(gates.values()) else REVIEW

        # Remove raw timestamp arrays before reporting.
        okx_report = {k:v for k,v in okx.items() if k != "timestamps"}
        bybit_report = {k:v for k,v in bybit.items() if k != "timestamps"}
        okx_report["max_adjacent_gap_ms"] = okx_gap / 1000.0 if okx_gap is not None else None
        bybit_report["max_adjacent_gap_ms"] = bybit_gap / 1000.0 if bybit_gap is not None else None
        okx_report["sync"] = okx_sync
        bybit_report["sync"] = bybit_sync

        report = {
            "stage": STAGE,
            "version": "0.2",
            "status": status,
            "fixed_date": FIXED_DATE,
            "sync_rule": {
                "grid_ms": 1000,
                "causal_asof": "last event timestamp <= grid boundary",
                "staleness_limit_ms": 2000,
                "future_interpolation": False,
            },
            "okx": {
                "archives": [
                    {
                        "filename": OKX_FILENAME,
                        "bytes": okx_path.stat().st_size,
                        "sha256": sha256_file(okx_path),
                        "reused": okx_reused,
                    },
                    {
                        "filename": OKX_NEIGHBOR_FILENAME,
                        "bytes": neighbor_path.stat().st_size,
                        "sha256": sha256_file(neighbor_path),
                        "reused": neighbor_reused,
                    },
                ],
                "utc_stitch_rule": "D + D+1; retain UTC [D,D+1)",
                "semantic": okx_report,
            },
            "bybit": {
                "archive": {
                    "filename": BYBIT_FILENAME,
                    "bytes": bybit_path.stat().st_size,
                    "sha256": sha256_file(bybit_path),
                    "reused": bybit_reused,
                },
                "semantic": bybit_report,
            },
            "joint_sync": joint,
            "gates": gates,
            "failed_gates": [k for k,v in gates.items() if not v],
            "historical_trade_bodies_opened": True,
            "historical_price_fields_parsed_for_schema": True,
            "cross_venue_price_compared": False,
            "cross_venue_return_calculated": False,
            "dislocation_calculated": False,
            "lag_calculated": False,
            "leader_selected": False,
            "strategy_signal_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, report)

        print(status)
        print("OKX rows =", okx_report["row_count"], "grid_share =", okx_sync["usable_share"], "p99_ms =", okx_sync["p99_staleness_ms"])
        print("Bybit rows =", bybit_report["row_count"], "grid_share =", bybit_sync["usable_share"], "p99_ms =", bybit_sync["p99_staleness_ms"])
        print("joint_usable_share =", joint["joint_usable_share"])
        print("failed_gates =", report["failed_gates"])
        print("cross-venue price/return/dislocation/lag = False")
        print("leader/signal/PnL = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)
        return 0 if status == PASS else 2

    except Exception as exc:
        print("C8_D1_V02_HISTORICAL_CLOCK_INTEGRITY_REVIEW")
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
