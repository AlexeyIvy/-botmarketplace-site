from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

STAGE = "SC001-C9-D1-SEPTEMBER-FUNDING-ARCHIVE-INTEGRITY-V0.1"
PASS = "C9_D1_FUNDING_ARCHIVE_INTEGRITY_PASS"
REVIEW = "C9_D1_FUNDING_ARCHIVE_INTEGRITY_REVIEW"

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
ALLOWED_ARCHIVE_HOST = "static.okx.com"
ASSETS = ("BTC", "ETH", "DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
SWAPS = tuple(f"{s}-USDT-SWAP" for s in ASSETS)

SOURCE_START_MS = 1725120000000  # 2024-08-31T16:00:00Z
SOURCE_END_MS = 1727712000000    # 2024-09-30T16:00:00Z
ARCHIVE_YEAR = 2024
ARCHIVE_MONTH = 9
TIMEOUT = 60
RETRIES = 3
MAX_JSON_BYTES = 4_000_000
MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_TOTAL_ARCHIVE_BYTES = 200 * 1024 * 1024
CHUNK = 1024 * 1024

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c9-d1-september-funding-archive-acquisition-integrity-protocol-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.6.json"
FREEZE = ROOT / "docs/research/sc001-c9-d1-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D0_REPORT = (
    DATA_ROOT
    / "SC001_C9_D0_V02_DATA_SEMANTICS"
    / "sc001_c9_d0_v02_data_semantics_report_v0_1.json"
)

OUT_DIR = DATA_ROOT / "SC001_C9_D1_FUNDING_ARCHIVE"
ARCHIVE_DIR = OUT_DIR / "archives"
OUT = OUT_DIR / "sc001_c9_d1_funding_archive_integrity_report_v0_1.json"


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
        fail(f"missing required JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        text=True,
    ).strip()


def require_freeze() -> dict:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_C9_D1_RUN":
        fail("C9-D1 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C9-D1 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C9-D1 protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("C9-D1 contamination registry identity mismatch")
    if tuple(fr.get("probe_universe") or ()) != SWAPS:
        fail("C9-D1 frozen universe mismatch")
    if fr.get("source_archive_month") != "2024-09 UTC+8":
        fail("C9-D1 source archive month mismatch")
    for key in (
        "mark_index_values_authorized",
        "returns_authorized",
        "basis_transition_authorized",
        "strategy_signal_authorized",
        "sentinel_outcome_authorized",
        "pnl_authorized",
        "direction_selection_authorized",
        "threshold_selection_authorized",
        "event_window_selection_authorized",
        "july_funding_body_authorized",
        "october_funding_body_authorized",
        "protected_market_body_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(key) is not False:
            fail(f"C9-D1 freeze firewall mismatch: {key}")
    return fr


def require_registry() -> dict:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.6":
        fail("contamination registry version mismatch")
    row = reg.get("c9_d1_selection_calibration") or {}
    if row.get("classification") != "NONPROMOTIONAL_SELECTION_CALIBRATION":
        fail("C9-D1 contamination classification mismatch")
    if row.get("source_archive_month") != "2024-09 UTC+8":
        fail("C9-D1 registry archive month mismatch")
    if tuple(row.get("assets") or ()) != ASSETS:
        fail("C9-D1 registry asset set mismatch")
    return reg


def require_d0_parent() -> dict:
    rep = load_json(D0_REPORT)
    if rep.get("status") != "C9_D0_V02_DATA_SEMANTICS_PASS":
        fail("C9-D0 v0.2 parent not exact PASS")
    if int(rep.get("assets_passed", 0)) != 8:
        fail("C9-D0 v0.2 assets_passed mismatch")
    if int(rep.get("total_funding_archive_bytes_by_head_not_downloaded", -1)) != 43930:
        fail("C9-D0 v0.2 funding HEAD-byte total mismatch")
    false_keys = (
        "historical_funding_body_downloaded",
        "historical_funding_body_opened",
        "funding_values_used_for_strategy",
        "mark_index_prices_used_for_strategy",
        "returns_calculated",
        "basis_transition_calculated",
        "strategy_signal_calculated",
        "sentinel_outcome_calculated",
        "pnl_calculated",
        "direction_selected",
        "threshold_selected",
        "event_window_selected",
        "protected_market_body_accessed",
        "promotional_alpha_accessed",
    )
    for key in false_keys:
        if rep.get(key) is not False:
            fail(f"C9-D0 v0.2 parent firewall mismatch: {key}")
    return rep


def month_bounds_utc8_ms(year: int, month: int) -> tuple[int, int]:
    tz8 = timezone(timedelta(hours=8))
    start_local = datetime(year, month, 1, tzinfo=tz8)
    if month == 12:
        end_local = datetime(year + 1, 1, 1, tzinfo=tz8)
    else:
        end_local = datetime(year, month + 1, 1, tzinfo=tz8)
    return int(start_local.timestamp() * 1000), int(end_local.timestamp() * 1000)


def request_json(path: str, params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    last: Exception | None = None

    for domain in DOMAINS:
        url = domain + path + ("?" + query if query else "")
        for attempt in range(1, RETRIES + 1):
            try:
                req = urllib.request.Request(
                    url,
                    method="GET",
                    headers={
                        "User-Agent": "BotMarketplace-SC001-C9-D1/0.1",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    raw = resp.read(MAX_JSON_BYTES + 1)
                    status = int(getattr(resp, "status", 200))
                    final = resp.geturl()

                if len(raw) > MAX_JSON_BYTES:
                    fail(f"response cap exceeded: {path}")
                if status != 200:
                    fail(f"HTTP {status}: {path}")

                parsed = urllib.parse.urlparse(final)
                if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {
                    "www.okx.com",
                    "us.okx.com",
                }:
                    fail(f"unexpected final API URL identity: {final}")

                obj = json.loads(raw.decode("utf-8"))
                if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                    code = obj.get("code") if isinstance(obj, dict) else None
                    fail(f"OKX code mismatch path={path} code={code}")
                return obj
            except Exception as exc:
                last = exc
                if attempt < RETRIES:
                    time.sleep(float(attempt))
    raise RuntimeError(f"request failed {path}: {type(last).__name__}: {last}")


def walk_file_nodes(node):
    if isinstance(node, dict):
        filename = node.get("filename") or node.get("fileName")
        url = node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
        if isinstance(filename, str) and isinstance(url, str):
            yield node
        for value in node.values():
            yield from walk_file_nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_file_nodes(value)


def trusted_archive_url(url: str, filename: str) -> bool:
    try:
        p = urllib.parse.urlparse(url)
        return (
            p.scheme == "https"
            and (p.hostname or "").lower() == ALLOWED_ARCHIVE_HOST
            and Path(p.path).name == filename
        )
    except Exception:
        return False


def metadata_files(uly: str) -> dict[str, dict]:
    begin, end = month_bounds_utc8_ms(ARCHIVE_YEAR, ARCHIVE_MONTH)
    if begin != SOURCE_START_MS or end != SOURCE_END_MS:
        fail("internal September UTC+8 boundary mismatch")

    obj = request_json(
        "/api/v5/public/market-data-history",
        {
            "module": "3",
            "instType": "SWAP",
            "instFamilyList": uly,
            "dateAggrType": "monthly",
            "begin": str(begin),
            "end": str(end),
        },
    )

    files: dict[str, dict] = {}
    for node in walk_file_nodes(obj.get("data")):
        filename = node.get("filename") or node.get("fileName")
        url = node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
        if not isinstance(filename, str) or not isinstance(url, str):
            continue
        if not trusted_archive_url(url, filename):
            fail(f"untrusted archive URL: {filename} {url}")
        prev = files.get(filename)
        if prev is not None and prev["url"] != url:
            fail(f"conflicting archive URLs: {filename}")
        files[filename] = {"filename": filename, "url": url}

    if not files:
        fail(f"no September funding archive files returned for {uly}")
    return files


def head_size(url: str, filename: str) -> int:
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={
            "User-Agent": "BotMarketplace-SC001-C9-D1/0.1",
            "Referer": "https://www.okx.com/historical-data",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        status = int(getattr(resp, "status", 200))
        final = resp.geturl()
        cl = resp.headers.get("Content-Length")
    if status != 200:
        fail(f"HEAD HTTP {status}: {filename}")
    if not trusted_archive_url(final, filename):
        fail(f"HEAD archive identity mismatch: {filename}")
    if not cl or not cl.isdigit() or int(cl) <= 0:
        fail(f"invalid Content-Length: {filename}")
    return int(cl)


def expected_d0_files(parent: dict, inst: str) -> dict[str, int]:
    asset = (parent.get("assets") or {}).get(inst)
    if not isinstance(asset, dict):
        fail(f"D0 asset missing: {inst}")
    meta = (asset.get("funding_archive_metadata") or {}).get("SEPTEMBER")
    if not isinstance(meta, dict) or meta.get("metadata_pass") is not True:
        fail(f"D0 September funding metadata not PASS: {inst}")
    out: dict[str, int] = {}
    for row in meta.get("files") or []:
        fn = row.get("filename")
        size = row.get("content_length")
        host = row.get("host")
        if not isinstance(fn, str) or not isinstance(size, int) or size <= 0:
            fail(f"bad D0 file metadata: {inst}")
        if host != ALLOWED_ARCHIVE_HOST:
            fail(f"D0 archive host mismatch: {inst} {fn} {host}")
        out[fn] = size
    if not out:
        fail(f"D0 file set empty: {inst}")
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_one(inst: str, meta: dict, expected_size: int) -> tuple[Path, bool]:
    if expected_size > MAX_ARCHIVE_BYTES:
        fail(f"archive exceeds per-file cap: {meta['filename']} {expected_size}")

    ddir = ARCHIVE_DIR / inst.replace("-USDT-SWAP", "")
    ddir.mkdir(parents=True, exist_ok=True)
    dest = ddir / meta["filename"]

    if dest.exists() and dest.stat().st_size == expected_size:
        return dest, True

    if dest.exists():
        dest.unlink()

    tmp = Path(str(dest) + ".part")
    tmp.unlink(missing_ok=True)

    req = urllib.request.Request(
        meta["url"],
        method="GET",
        headers={
            "User-Agent": "BotMarketplace-SC001-C9-D1/0.1",
            "Referer": "https://www.okx.com/historical-data",
        },
    )

    got = 0
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp, tmp.open("wb") as out:
        status = int(getattr(resp, "status", 200))
        final = resp.geturl()
        if status != 200:
            fail(f"GET HTTP {status}: {meta['filename']}")
        if not trusted_archive_url(final, meta["filename"]):
            fail(f"GET archive identity mismatch: {meta['filename']}")
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            got += len(chunk)
            if got > expected_size or got > MAX_ARCHIVE_BYTES:
                fail(f"download size overflow: {meta['filename']}")
            out.write(chunk)
        out.flush()
        os.fsync(out.fileno())

    if got != expected_size:
        fail(f"download size mismatch {meta['filename']}: {got} != {expected_size}")

    os.replace(tmp, dest)
    return dest, False


def finite_decimal(text: str) -> Decimal:
    try:
        x = Decimal(str(text).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"invalid decimal {text!r}") from exc
    if not x.is_finite():
        raise ValueError(f"nonfinite decimal {text!r}")
    return x


def parse_target_rows(path: Path, inst: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {path.name}: {bad}")
        members = [x for x in zf.infolist() if not x.is_dir()]
        if not members:
            fail(f"ZIP has no regular member: {path.name}")

        for info in members:
            if not info.filename.lower().endswith(".csv"):
                fail(f"non-CSV regular member in funding ZIP: {path.name} {info.filename}")
            with zf.open(info, "r") as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
                for fields in reader:
                    if not fields or len(fields) < 3:
                        continue
                    if fields[0] != inst:
                        continue
                    try:
                        rate = finite_decimal(fields[1])
                        ts = int(fields[2].strip())
                    except Exception as exc:
                        raise RuntimeError(
                            f"malformed target funding row {path.name}: {fields!r}"
                        ) from exc
                    if ts <= 0:
                        fail(f"invalid funding timestamp {path.name}: {ts}")
                    rows.append((ts, format(rate, "f")))
    return rows


def qualify_instrument(inst: str, parent: dict) -> dict:
    asset = (parent.get("assets") or {}).get(inst)
    uly = ((asset or {}).get("instrument") or {}).get("uly")
    if not isinstance(uly, str) or not uly:
        fail(f"D0 uly missing: {inst}")

    expected = expected_d0_files(parent, inst)
    current = metadata_files(uly)

    if set(current) != set(expected):
        fail(
            f"September funding filename set mismatch {inst}: "
            f"{sorted(current)} != {sorted(expected)}"
        )

    archives = []
    combined: list[tuple[int, str]] = []
    downloaded_bytes = reused_bytes = 0

    for fn in sorted(current):
        meta = current[fn]
        size_now = head_size(meta["url"], fn)
        if size_now != expected[fn]:
            fail(f"HEAD size mismatch {inst} {fn}: {size_now} != {expected[fn]}")

        path, reused = download_one(inst, meta, expected[fn])
        digest = sha256_file(path)
        rows = parse_target_rows(path, inst)
        combined.extend(rows)

        if reused:
            reused_bytes += path.stat().st_size
        else:
            downloaded_bytes += path.stat().st_size

        archives.append(
            {
                "filename": fn,
                "bytes": path.stat().st_size,
                "sha256": digest,
                "reused": reused,
                "target_rows": len(rows),
            }
        )

    by_ts: dict[int, str] = {}
    for ts, rate in combined:
        if ts < SOURCE_START_MS or ts >= SOURCE_END_MS:
            fail(f"target funding timestamp outside authorized source month {inst}: {ts}")
        prev = by_ts.get(ts)
        if prev is not None and prev != rate:
            fail(f"conflicting duplicate funding value {inst} at {ts}")
        by_ts[ts] = rate

    ts = sorted(by_ts)
    if len(ts) < 80:
        fail(f"insufficient unique funding timestamps {inst}: {len(ts)}")

    intervals_ms = [b - a for a, b in zip(ts, ts[1:])]
    if any(x <= 0 for x in intervals_ms):
        fail(f"nonpositive funding interval {inst}")
    max_interval_ms = max(intervals_ms) if intervals_ms else None
    if max_interval_ms is None or max_interval_ms > 8 * 3_600_000:
        fail(f"funding interval gap >8h {inst}: {max_interval_ms}")
    if ts[0] - SOURCE_START_MS > 8 * 3_600_000:
        fail(f"funding start coverage gap >8h {inst}")
    if SOURCE_END_MS - ts[-1] > 8 * 3_600_000:
        fail(f"funding end coverage gap >8h {inst}")

    interval_hours = sorted({round(x / 3_600_000, 6) for x in intervals_ms})

    return {
        "instrument": inst,
        "uly": uly,
        "archive_count": len(archives),
        "archives": archives,
        "unique_funding_timestamps": len(ts),
        "first_funding_time_ms": ts[0],
        "last_funding_time_ms": ts[-1],
        "observed_interval_hours": interval_hours,
        "maximum_interval_hours": max(interval_hours) if interval_hours else None,
        "funding_values_validated_not_stored": True,
        "downloaded_bytes": downloaded_bytes,
        "reused_bytes": reused_bytes,
        "integrity_pass": True,
    }


def main() -> int:
    try:
        require_freeze()
        require_registry()
        parent = require_d0_parent()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        assets = {}
        all_pass = True
        total_downloaded = total_reused = 0

        for i, inst in enumerate(SWAPS, start=1):
            print(f"C9-D1 [{i}/8] {inst}", flush=True)
            try:
                rep = qualify_instrument(inst, parent)
                assets[inst] = rep
                total_downloaded += int(rep["downloaded_bytes"])
                total_reused += int(rep["reused_bytes"])
                print(
                    f"PASS {inst} rows={rep['unique_funding_timestamps']} "
                    f"intervals={rep['observed_interval_hours']} "
                    f"archives={rep['archive_count']}",
                    flush=True,
                )
            except Exception as exc:
                all_pass = False
                assets[inst] = {
                    "integrity_pass": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print(
                    f"REVIEW {inst}: {type(exc).__name__}: {exc}",
                    flush=True,
                )

        if total_downloaded + total_reused > MAX_TOTAL_ARCHIVE_BYTES:
            fail("total qualified funding archive bytes exceed safety cap")

        status = PASS if all_pass and len(assets) == 8 else REVIEW

        rep = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "source_archive_month": "2024-09 UTC+8",
            "source_time_window_utc": {
                "start_inclusive_ms": SOURCE_START_MS,
                "end_exclusive_ms": SOURCE_END_MS,
            },
            "selection_calibration_role": "NONPROMOTIONAL_SELECTION_CALIBRATION",
            "probe_universe": list(SWAPS),
            "assets": assets,
            "assets_passed": sum(
                1 for x in assets.values() if x.get("integrity_pass") is True
            ),
            "downloaded_bytes": total_downloaded,
            "reused_bytes": total_reused,
            "qualified_total_bytes": total_downloaded + total_reused,
            "mark_index_values_opened_for_c9_d1": False,
            "funding_values_used_for_strategy": False,
            "returns_calculated": False,
            "basis_transition_calculated": False,
            "strategy_signal_calculated": False,
            "sentinel_outcome_calculated": False,
            "pnl_calculated": False,
            "direction_selected": False,
            "threshold_selected": False,
            "event_window_selected": False,
            "july_funding_body_accessed": False,
            "october_funding_body_accessed": False,
            "protected_market_body_accessed": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, rep)

        print(status)
        print("assets_passed =", rep["assets_passed"], "/ 8")
        print("qualified_total_bytes =", rep["qualified_total_bytes"])
        print("mark/index values opened for D1 = False")
        print("funding values used for strategy = False")
        print("returns/basis-transition/signal/sentinel/PnL = False")
        print("direction/threshold/event-window selected = False")
        print("July/October/protected/promotional body accessed = False")
        print("report =", OUT)

        return 0 if status == PASS else 2

    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "version": "0.1",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "mark_index_values_opened_for_c9_d1": False,
            "funding_values_used_for_strategy": False,
            "returns_calculated": False,
            "basis_transition_calculated": False,
            "strategy_signal_calculated": False,
            "sentinel_outcome_calculated": False,
            "pnl_calculated": False,
            "direction_selected": False,
            "threshold_selected": False,
            "event_window_selected": False,
            "july_funding_body_accessed": False,
            "october_funding_body_accessed": False,
            "protected_market_body_accessed": False,
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
