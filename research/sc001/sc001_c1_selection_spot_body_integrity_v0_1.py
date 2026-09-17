from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import shutil
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE = "SC001-C1-SPOT-SELECTION-BODY-INTEGRITY-V0.1"
PREFLIGHT_PASS = "C1_SPOT_BODY_PREFLIGHT_PASS"
PASS = "C1_SPOT_BODY_INTEGRITY_PASS"
FAIL = "C1_SPOT_BODY_INTEGRITY_FAIL"

ASSETS = ("BTC", "ETH", "DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
INSTRUMENTS = tuple(f"{s}-USDT" for s in ASSETS)
EXPECTED_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]
ALLOWED_HOST = "static.okx.com"
TIMEOUT = 120
RETRIES = 3
CHUNK = 8 * 1024 * 1024
MIN_FREE_RESERVE_BYTES = 20 * 1024**3
DAY_MS = 86_400_000
MIN_MS = 60_000

MANIFEST_SHA256 = "bfa403c5b53b2a95c0df28fd41d3382667fe0c6ced223b65f451e7b99ecd1023"
MANIFEST_BYTES = 118273
EXPECTED_BODY_BYTES = 273358764
EXPECTED_ARCHIVES = 256
EXPECTED_UTC_DAYS = 240

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
ROOT = DATA_ROOT / "SC001_C1_SPOT_SELECTION_CALIBRATION"
ARCHIVES = ROOT / "archives"
META = ROOT / "sc001_c1_spot_metadata_preflight_v0_1.json"
PREFLIGHT_REPORT = ROOT / "sc001_c1_spot_body_preflight_report_v0_1.json"
OUT = ROOT / "sc001_c1_spot_body_integrity_report_v0_1.json"


def iter_days(start: str, end: str) -> list[str]:
    d = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    e = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    out: list[str] = []
    while d <= e:
        out.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return out


JULY_LABELS = tuple(iter_days("2024-06-30", "2024-07-15"))
SEP_LABELS = tuple(iter_days("2024-08-31", "2024-09-15"))
ALLOWED_LABELS = JULY_LABELS + SEP_LABELS
ALLOWED_SET = set(ALLOWED_LABELS)
JULY_TARGETS = tuple(iter_days("2024-06-30", "2024-07-14"))
SEP_TARGETS = tuple(iter_days("2024-08-31", "2024-09-14"))
TARGET_DAYS = JULY_TARGETS + SEP_TARGETS
PERFORMANCE_DAYS = set(iter_days("2024-07-01", "2024-07-14") + iter_days("2024-09-01", "2024-09-14"))
BOUNDARY_WARMUP_DAYS = {"2024-06-30", "2024-08-31"}
BOUNDARY_SOURCE_ONLY_LABELS = {"2024-06-30", "2024-07-15", "2024-08-31", "2024-09-15"}


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
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected: {path}")
    return x


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_ts_ms(text: str) -> int:
    v = int(str(text).strip())
    av = abs(v)
    if av >= 10**17:
        return v // 1_000_000
    if av >= 10**14:
        return v // 1_000
    if av >= 10**11:
        return v
    if av >= 10**9:
        return v * 1000
    fail(f"unresolved timestamp scale: {text!r}")


def day_start_ms(day: str) -> int:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(d.timestamp() * 1000)


def utc_iso(ts_ms: int | None) -> str | None:
    if ts_ms is None:
        return None
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()


def trusted_url(url: str, expected_filename: str) -> bool:
    try:
        p = urllib.parse.urlparse(url)
        return (
            p.scheme == "https"
            and (p.hostname or "").lower() == ALLOWED_HOST
            and Path(p.path).name == expected_filename
        )
    except Exception:
        return False


def next_day(day: str) -> str:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def manifest_rows() -> tuple[dict[tuple[str, str], dict], dict]:
    if not META.exists():
        fail(f"missing manifest: {META}")
    if META.stat().st_size != MANIFEST_BYTES:
        fail(f"manifest byte mismatch {META.stat().st_size} != {MANIFEST_BYTES}")
    actual_sha = sha256_file(META)
    if actual_sha != MANIFEST_SHA256:
        fail(f"manifest SHA256 mismatch {actual_sha} != {MANIFEST_SHA256}")

    rep = load_json(META)
    if rep.get("stage") != "SC001-C1-SPOT-SELECTION-METADATA-PREFLIGHT-V0.1":
        fail("manifest stage mismatch")
    if rep.get("status") != "C1_SPOT_METADATA_PREFLIGHT_PASS":
        fail("manifest status not exact PASS")
    if int(rep.get("complete_asset_count", 0)) != 8:
        fail("manifest complete_asset_count mismatch")
    if tuple(rep.get("complete_assets") or ()) != INSTRUMENTS:
        fail("manifest complete_assets/order mismatch")
    if int(rep.get("expected_complete_asset_body_bytes", -1)) != EXPECTED_BODY_BYTES:
        fail("manifest expected body-byte total mismatch")
    if tuple(rep.get("permitted_archive_labels") or ()) != ALLOWED_LABELS:
        fail("manifest permitted label set/order mismatch")
    if rep.get("metadata_query_days_all_whitelisted") is not True:
        fail("manifest metadata whitelist flag mismatch")
    if rep.get("market_data_body_downloaded") is not False:
        fail("manifest body-download firewall mismatch")

    false_keys = (
        "strategy_signal_calculated",
        "sentinel_outcome_calculated",
        "basis_calculated",
        "returns_calculated",
        "pnl_calculated",
        "promotional_alpha_accessed",
        "protected_holdout_body_accessed",
        "july_gap_body_accessed",
        "august_protected_body_accessed",
        "october_confirmation_body_accessed",
        "legacy_e006_confirmation_body_accessed",
    )
    for k in false_keys:
        if rep.get(k) is not False:
            fail(f"manifest firewall mismatch: {k}")

    rows: dict[tuple[str, str], dict] = {}
    total = 0
    for inst in INSTRUMENTS:
        asset = (rep.get("assets") or {}).get(inst)
        if not isinstance(asset, dict):
            fail(f"missing manifest asset: {inst}")
        if asset.get("state") != "COMPLETE_METADATA":
            fail(f"asset not COMPLETE_METADATA: {inst}")
        ars = asset.get("archives") or []
        if len(ars) != 32:
            fail(f"archive count mismatch for {inst}: {len(ars)}")
        seen_dates: set[str] = set()
        for r in ars:
            if not isinstance(r, dict):
                fail(f"malformed manifest archive row for {inst}")
            d = r.get("date_label")
            if d not in ALLOWED_SET or d in seen_dates:
                fail(f"bad/duplicate label for {inst}: {d}")
            seen_dates.add(d)
            fn = r.get("filename")
            expected_fn = f"{inst}-trades-{d}.zip"
            url = r.get("url")
            size = r.get("expected_bytes")
            if fn != expected_fn:
                fail(f"filename mismatch for {inst} {d}")
            if not isinstance(url, str) or not trusted_url(url, expected_fn):
                fail(f"URL identity mismatch for {inst} {d}")
            if not isinstance(size, int) or size <= 0:
                fail(f"invalid expected size for {inst} {d}")
            role = r.get("role")
            expected_role = "PERFORMANCE" if d in PERFORMANCE_DAYS else "BOUNDARY_SOURCE_ONLY"
            if role != expected_role:
                fail(f"role mismatch for {inst} {d}: {role} != {expected_role}")
            rows[(inst, d)] = {
                "instrument": inst,
                "date_label": d,
                "filename": fn,
                "url": url,
                "expected_bytes": size,
                "role": role,
            }
            total += size
        if seen_dates != ALLOWED_SET:
            fail(f"label coverage mismatch for {inst}")

    if len(rows) != EXPECTED_ARCHIVES:
        fail(f"manifest archive rows mismatch {len(rows)} != {EXPECTED_ARCHIVES}")
    if total != EXPECTED_BODY_BYTES:
        fail(f"manifest recomputed body bytes mismatch {total} != {EXPECTED_BODY_BYTES}")
    return rows, rep


def disk_check() -> dict:
    ROOT.mkdir(parents=True, exist_ok=True)
    disk = shutil.disk_usage(ROOT)
    required = EXPECTED_BODY_BYTES + MIN_FREE_RESERVE_BYTES
    return {
        "disk_free_bytes": disk.free,
        "required_free_bytes": required,
        "disk_pass": disk.free >= required,
    }


def preflight() -> dict:
    rows, rep = manifest_rows()
    disk = disk_check()
    if not disk["disk_pass"]:
        fail("insufficient disk for frozen bodies plus 20 GiB reserve")
    out = {
        "stage": STAGE + "-PREFLIGHT",
        "status": PREFLIGHT_PASS,
        "manifest_sha256": MANIFEST_SHA256,
        "manifest_bytes": MANIFEST_BYTES,
        "manifest_status": rep.get("status"),
        "complete_assets": list(INSTRUMENTS),
        "archive_rows": len(rows),
        "expected_body_bytes": EXPECTED_BODY_BYTES,
        **disk,
        "market_data_body_downloaded": False,
        "strategy_signal_calculated": False,
        "sentinel_outcome_calculated": False,
        "basis_calculated": False,
        "returns_calculated": False,
        "pnl_calculated": False,
        "promotional_alpha_accessed": False,
        "protected_holdout_body_accessed": False,
        "july_gap_body_accessed": False,
        "august_protected_body_accessed": False,
        "october_confirmation_body_accessed": False,
        "legacy_e006_confirmation_body_accessed": False,
    }
    atomic_json(PREFLIGHT_REPORT, out)
    return out


def download_fresh(meta: dict, part: Path) -> None:
    req = urllib.request.Request(
        meta["url"],
        method="GET",
        headers={"User-Agent": "BotMarketplace-SC001-C1-SpotBody/0.1"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        status = int(getattr(resp, "status", 200))
        final = resp.geturl()
        if status != 200:
            fail(f"fresh GET HTTP {status} for {meta['filename']}")
        if not trusted_url(final, meta["filename"]):
            fail(f"fresh GET identity mismatch for {meta['filename']}")
        with part.open("wb") as f:
            while True:
                chunk = resp.read(CHUNK)
                if not chunk:
                    break
                f.write(chunk)
            f.flush()
            os.fsync(f.fileno())
    if part.stat().st_size != int(meta["expected_bytes"]):
        fail(f"fresh GET size mismatch for {meta['filename']}")


def download_one(meta: dict) -> tuple[Path, bool]:
    sym = meta["instrument"].split("-")[0]
    ddir = ARCHIVES / sym
    ddir.mkdir(parents=True, exist_ok=True)
    dest = ddir / meta["filename"]
    part = Path(str(dest) + ".part")
    expected = int(meta["expected_bytes"])

    if dest.exists():
        if dest.stat().st_size == expected:
            return dest, True
        dest.unlink()

    if part.exists() and part.stat().st_size > expected:
        part.unlink()
    if part.exists() and part.stat().st_size == expected:
        os.replace(part, dest)
        return dest, False

    last: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            already = part.stat().st_size if part.exists() else 0
            if already > 0:
                req = urllib.request.Request(
                    meta["url"],
                    method="GET",
                    headers={
                        "User-Agent": "BotMarketplace-SC001-C1-SpotBody/0.1",
                        "Range": f"bytes={already}-",
                    },
                )
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    status = int(getattr(resp, "status", 200))
                    final = resp.geturl()
                    cr = resp.headers.get("Content-Range", "")
                    if not trusted_url(final, meta["filename"]):
                        fail(f"resume GET identity mismatch for {meta['filename']}")
                    if status == 206 and cr.startswith(f"bytes {already}-"):
                        with part.open("ab") as f:
                            while True:
                                chunk = resp.read(CHUNK)
                                if not chunk:
                                    break
                                f.write(chunk)
                            f.flush()
                            os.fsync(f.fileno())
                    elif status == 200:
                        part.unlink(missing_ok=True)
                        download_fresh(meta, part)
                    else:
                        fail(f"ambiguous Range response {status} {cr!r} for {meta['filename']}")
            else:
                download_fresh(meta, part)

            if part.stat().st_size != expected:
                fail(f"partial/final size mismatch for {meta['filename']}")
            os.replace(part, dest)
            return dest, False
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"download failed for {meta['filename']}: {type(last).__name__}: {last}")


def open_reader(path: Path):
    zf = zipfile.ZipFile(path, "r")
    bad = zf.testzip()
    if bad is not None:
        zf.close()
        fail(f"ZIP CRC failure {path.name}: {bad}")
    members = [m for m in zf.infolist() if not m.is_dir()]
    if len(members) != 1:
        zf.close()
        fail(f"unexpected ZIP member count {path.name}: {len(members)}")
    raw = zf.open(members[0], "r")
    text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
    reader = csv.reader(text)
    hdr = next(reader, None)
    if hdr != EXPECTED_HEADER:
        text.close()
        zf.close()
        fail(f"unexpected header {path.name}: {hdr!r}")
    return zf, text, reader, members[0]


def parse_row(row: list[str], expected_inst: str, path_name: str):
    if len(row) != 6:
        fail(f"malformed row width {path_name}: {len(row)}")
    if row[0] != expected_inst:
        fail(f"instrument mismatch {path_name}: {row[0]} != {expected_inst}")
    try:
        tid = int(row[1])
        side = row[2].lower()
        price = float(row[3])
        size = float(row[4])
        ts = parse_ts_ms(row[5])
    except Exception as exc:
        raise RuntimeError(f"parse failure {path_name}: {row!r}") from exc
    if tid < 0:
        fail(f"negative trade id {path_name}")
    if side not in {"buy", "sell"}:
        fail(f"bad side {path_name}: {side}")
    if not math.isfinite(price) or price <= 0 or not math.isfinite(size) or size <= 0:
        fail(f"bad price/size {path_name}")
    return tid, ts, side


def scan_source(path: Path, meta: dict) -> dict:
    zf, text, reader, member = open_reader(path)
    count = 0
    first_ts = last_ts = None
    prev_ts = prev_tid = None
    duplicate_ts = 0
    id_gaps = 0
    buy = sell = 0
    try:
        for row in reader:
            if not row:
                continue
            tid, ts, side = parse_row(row, meta["instrument"], path.name)
            if prev_ts is not None:
                if ts < prev_ts:
                    fail(f"source timestamp reversal {path.name}")
                if ts == prev_ts:
                    duplicate_ts += 1
            if prev_tid is not None:
                if tid <= prev_tid:
                    fail(f"source trade-id duplicate/backward {path.name}: {tid} <= {prev_tid}")
                if tid != prev_tid + 1:
                    id_gaps += 1
            if count == 0:
                first_ts = ts
            last_ts = ts
            prev_ts, prev_tid = ts, tid
            count += 1
            if side == "buy":
                buy += 1
            else:
                sell += 1
    finally:
        text.close()
        zf.close()
    if count <= 0:
        fail(f"empty source archive {path.name}")
    return {
        "instrument": meta["instrument"],
        "date_label": meta["date_label"],
        "role": meta["role"],
        "filename": meta["filename"],
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "zip_member": member.filename,
        "member_uncompressed_bytes": member.file_size,
        "source_rows": count,
        "buy_count": buy,
        "sell_count": sell,
        "first_ts_ms": first_ts,
        "last_ts_ms": last_ts,
        "first_ts_utc": utc_iso(first_ts),
        "last_ts_utc": utc_iso(last_ts),
        "duplicate_timestamp_count": duplicate_ts,
        "trade_id_gap_event_count": id_gaps,
    }


def iter_target_rows(path: Path, inst: str, lo: int, hi: int):
    zf, text, reader, _member = open_reader(path)
    try:
        for row in reader:
            if not row:
                continue
            tid, ts, side = parse_row(row, inst, path.name)
            if lo <= ts < hi:
                yield tid, ts, side
    finally:
        text.close()
        zf.close()


def utc_day_qualification(inst: str, day: str, rows: dict[tuple[str, str], dict]) -> dict:
    d1 = next_day(day)
    if (inst, day) not in rows or (inst, d1) not in rows:
        fail(f"missing stitch sources for {inst} {day}")
    sym = inst.split("-")[0]
    p0 = ARCHIVES / sym / rows[(inst, day)]["filename"]
    p1 = ARCHIVES / sym / rows[(inst, d1)]["filename"]
    lo = day_start_ms(day)
    hi = lo + DAY_MS

    count = 0
    prev_ts = prev_tid = None
    first_ts = last_ts = None
    id_gap_events = 0
    max_gap_ms = 0
    minute_seen: set[int] = set()
    sides: set[str] = set()

    for p in (p0, p1):
        for tid, ts, side in iter_target_rows(p, inst, lo, hi):
            if prev_ts is not None:
                if ts < prev_ts:
                    fail(f"target timestamp reversal {inst} {day}")
                max_gap_ms = max(max_gap_ms, ts - prev_ts)
            if prev_tid is not None:
                if tid <= prev_tid:
                    fail(f"target trade-id duplicate/backward {inst} {day}: {tid} <= {prev_tid}")
                if tid != prev_tid + 1:
                    id_gap_events += 1
            if count == 0:
                first_ts = ts
            last_ts = ts
            prev_ts, prev_tid = ts, tid
            minute_seen.add((ts - lo) // MIN_MS)
            sides.add(side)
            count += 1

    if count <= 0:
        fail(f"no admitted target rows {inst} {day}")
    if sides != {"buy", "sell"}:
        fail(f"target side breadth failure {inst} {day}: {sorted(sides)}")
    if first_ts is None or last_ts is None or not (lo <= first_ts < hi and lo <= last_ts < hi):
        fail(f"target interval failure {inst} {day}")

    missing_minutes = 1440 - len(minute_seen)
    return {
        "instrument": inst,
        "date": day,
        "performance_role": "PERFORMANCE" if day in PERFORMANCE_DAYS else "BOUNDARY_WARMUP_SOURCE_ONLY",
        "rows": count,
        "first_ts_ms": first_ts,
        "last_ts_ms": last_ts,
        "first_ts_utc": utc_iso(first_ts),
        "last_ts_utc": utc_iso(last_ts),
        "trade_id_gap_event_count": id_gap_events,
        "minute_buckets": len(minute_seen),
        "missing_minute_buckets": missing_minutes,
        "max_intertrade_gap_ms": max_gap_ms,
        "both_sides": True,
    }


def run() -> dict:
    pre = preflight()
    rows, _manifest = manifest_rows()
    ARCHIVES.mkdir(parents=True, exist_ok=True)

    source_reports: list[dict] = []
    reused_files = 0
    downloaded_files = 0
    reused_bytes = 0
    downloaded_bytes = 0

    ordered = [(inst, d) for inst in INSTRUMENTS for d in ALLOWED_LABELS]
    for i, key in enumerate(ordered, start=1):
        meta = rows[key]
        print(f"BODY [{i}/{EXPECTED_ARCHIVES}] {meta['filename']}", flush=True)
        p, reused = download_one(meta)
        if p.stat().st_size != int(meta["expected_bytes"]):
            fail(f"local body size mismatch after acquisition: {p}")
        srep = scan_source(p, meta)
        source_reports.append(srep)
        if reused:
            reused_files += 1
            reused_bytes += p.stat().st_size
            mode = "REUSED"
        else:
            downloaded_files += 1
            downloaded_bytes += p.stat().st_size
            mode = "DOWNLOADED"
        print(f"PASS BODY mode={mode} rows={srep['source_rows']} sha256={srep['sha256'][:16]}...", flush=True)

    if len(source_reports) != EXPECTED_ARCHIVES:
        fail(f"source report count mismatch {len(source_reports)}")
    if sum(int(x["bytes"]) for x in source_reports) != EXPECTED_BODY_BYTES:
        fail("qualified body-byte total mismatch")

    day_reports: list[dict] = []
    for ai, inst in enumerate(INSTRUMENTS, start=1):
        for di, day in enumerate(TARGET_DAYS, start=1):
            print(f"UTC [{ai}/8 {di}/30] {inst} {day}", flush=True)
            r = utc_day_qualification(inst, day, rows)
            day_reports.append(r)
            print(
                f"PASS UTC rows={r['rows']} minutes={r['minute_buckets']} "
                f"missing_minutes={r['missing_minute_buckets']} id_gap_events={r['trade_id_gap_event_count']}",
                flush=True,
            )

    if len(day_reports) != EXPECTED_UTC_DAYS:
        fail(f"UTC day qualification count mismatch {len(day_reports)} != {EXPECTED_UTC_DAYS}")

    per_asset_archive_counts = {inst: 0 for inst in INSTRUMENTS}
    for r in source_reports:
        per_asset_archive_counts[r["instrument"]] += 1
    if any(v != 32 for v in per_asset_archive_counts.values()):
        fail(f"per-asset archive count mismatch: {per_asset_archive_counts}")

    performance_asset_days = sum(1 for r in day_reports if r["performance_role"] == "PERFORMANCE")
    boundary_asset_days = sum(1 for r in day_reports if r["performance_role"] == "BOUNDARY_WARMUP_SOURCE_ONLY")
    if performance_asset_days != 224 or boundary_asset_days != 16:
        fail("performance/boundary UTC-day role counts mismatch")

    rep = {
        "stage": STAGE,
        "status": PASS,
        "manifest_sha256": MANIFEST_SHA256,
        "manifest_bytes": MANIFEST_BYTES,
        "expected_body_bytes": EXPECTED_BODY_BYTES,
        "archive_files_qualified": len(source_reports),
        "archive_files_expected": EXPECTED_ARCHIVES,
        "per_asset_archive_counts": per_asset_archive_counts,
        "downloaded_files": downloaded_files,
        "reused_files": reused_files,
        "downloaded_bytes": downloaded_bytes,
        "reused_bytes": reused_bytes,
        "qualified_total_bytes": downloaded_bytes + reused_bytes,
        "reconstructed_utc_asset_days_qualified": len(day_reports),
        "reconstructed_utc_asset_days_expected": EXPECTED_UTC_DAYS,
        "performance_asset_days": performance_asset_days,
        "boundary_warmup_asset_days": boundary_asset_days,
        "source_files": source_reports,
        "utc_days": day_reports,
        "utc_stitch_rule": "archive D + archive D+1; retain created_time in UTC [D,D+1)",
        "minute_coverage_rule": "diagnostic_only",
        "forward_trade_id_gap_rule": "diagnostic_only; duplicate/backward is hard failure",
        "selection_calibration_role": "NONPROMOTIONAL_SELECTION_CALIBRATION",
        "market_data_body_downloaded": downloaded_files > 0,
        "strategy_signal_calculated": False,
        "sentinel_outcome_calculated": False,
        "basis_calculated": False,
        "returns_calculated": False,
        "pnl_calculated": False,
        "promotional_alpha_accessed": False,
        "protected_holdout_body_accessed": False,
        "july_gap_body_accessed": False,
        "august_protected_body_accessed": False,
        "october_confirmation_body_accessed": False,
        "legacy_e006_confirmation_body_accessed": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "preflight_status": pre["status"],
    }
    atomic_json(OUT, rep)
    return rep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preflight", "run"])
    args = ap.parse_args()

    try:
        if args.mode == "preflight":
            rep = preflight()
            print(PREFLIGHT_PASS)
            print("manifest_sha256 =", rep["manifest_sha256"])
            print("manifest_bytes =", rep["manifest_bytes"])
            print("complete_assets = 8")
            print("archive_rows =", rep["archive_rows"])
            print("expected_body_bytes =", rep["expected_body_bytes"])
            print("disk_pass =", rep["disk_pass"])
            print("market_data_body_downloaded = False")
            print("strategy/sentinel/basis/returns/PnL = False")
            print("promotional alpha accessed = False")
            print("report =", PREFLIGHT_REPORT)
            return 0

        rep = run()
        print(PASS)
        print("archive_files_qualified =", rep["archive_files_qualified"], "/", rep["archive_files_expected"])
        print("reconstructed_utc_asset_days_qualified =", rep["reconstructed_utc_asset_days_qualified"], "/", rep["reconstructed_utc_asset_days_expected"])
        print("performance_asset_days =", rep["performance_asset_days"])
        print("boundary_warmup_asset_days =", rep["boundary_warmup_asset_days"])
        print("downloaded_files =", rep["downloaded_files"], "reused_files =", rep["reused_files"])
        print("qualified_total_bytes =", rep["qualified_total_bytes"])
        print("strategy/sentinel/basis/returns/PnL = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)
        return 0
    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "status": FAIL,
            "error": str(exc),
            "strategy_signal_calculated": False,
            "sentinel_outcome_calculated": False,
            "basis_calculated": False,
            "returns_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
        }
        try:
            atomic_json(OUT if args.mode == "run" else PREFLIGHT_REPORT, fail_rep)
        except Exception:
            pass
        print(FAIL)
        print("error =", exc)
        print("report =", OUT if args.mode == "run" else PREFLIGHT_REPORT)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
