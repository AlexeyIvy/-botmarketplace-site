"""SC001-E006 BTC-USDT SPOT body download/integrity stage.

DATA ENGINEERING ONLY.
NO BASIS / RETURNS / PNL / SWAP PRICE COMPARISON / L2 / Q2 / VALIDATION / FINAL.

Uses only the exact 2024-03-01..21 archive identities frozen by the successful
E006 SPOT metadata preflight. March 21 is boundary-neighbor only.
"""
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

STAGE = "SC001-E006-SPOT-BODY-INTEGRITY"
VERSION = "0.1"
TARGET_INST = "BTC-USDT"
EXPECTED_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]
ALLOWED_HOST = "static.okx.com"
TIMEOUT = 120
RETRIES = 3
CHUNK = 8 * 1024 * 1024
MIN_FREE_RESERVE_BYTES = 20 * 1024**3
DAY_MS = 86_400_000
MIN_MS = 60_000
SEC_MS = 1_000

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
ROOT = DATA_ROOT / "SC001_E006_SPOT_FEASIBILITY"
ARCHIVES = ROOT / "archives"
META_REPORT = ROOT / "sc001_e006_spot_metadata_preflight.json"
OUT_REPORT = ROOT / "sc001_e006_spot_body_integrity_report.json"

LABELS = tuple(f"2024-03-{d:02d}" for d in range(1, 22))
TARGET_DAYS = tuple(f"2024-03-{d:02d}" for d in range(1, 21))
BOUNDARY_LABEL = "2024-03-21"


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required JSON: {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected: {path}")
    return x


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


def utc_day_text(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def trusted_url(url: str, expected_filename: str) -> bool:
    try:
        p = urllib.parse.urlparse(url)
        return p.scheme == "https" and (p.hostname or "").lower() == ALLOWED_HOST and Path(p.path).name == expected_filename
    except Exception:
        return False


def frozen_manifest() -> tuple[dict[str, dict], dict]:
    rep = load_json(META_REPORT)
    if rep.get("stage") != "SC001-E006-SPOT-METADATA-PREFLIGHT":
        fail("wrong metadata-preflight stage")
    if rep.get("status") != "E006_SPOT_METADATA_PREFLIGHT_PASS":
        fail("metadata preflight is not PASS")
    if rep.get("market_data_body_downloaded") is not False:
        fail("metadata report body-download firewall mismatch")
    if any(rep.get(k) is not False for k in ("basis_calculated", "returns_calculated", "pnl_calculated", "l2_accessed", "q2_accessed", "validation_or_final_accessed")):
        fail("metadata report firewall mismatch")
    if tuple(rep.get("required_archive_labels") or ()) != LABELS:
        fail("metadata label set/order mismatch")
    if rep.get("boundary_neighbor_label") != BOUNDARY_LABEL:
        fail("metadata boundary label mismatch")
    rows = rep.get("archives") or []
    if len(rows) != len(LABELS):
        fail(f"metadata archive count mismatch: {len(rows)}")
    out: dict[str, dict] = {}
    total = 0
    for row in rows:
        if not isinstance(row, dict):
            fail("metadata archive row is not object")
        d = row.get("date_label")
        if d not in LABELS or d in out:
            fail(f"unexpected/duplicate metadata date label: {d}")
        fn = row.get("filename")
        expected = f"{TARGET_INST}-trades-{d}.zip"
        url = row.get("url")
        size = row.get("expected_bytes")
        if fn != expected or not isinstance(url, str) or not trusted_url(url, expected):
            fail(f"metadata identity mismatch for {d}")
        if not isinstance(size, int) or size <= 0:
            fail(f"metadata size mismatch for {d}")
        if bool(row.get("boundary_neighbor_only")) != (d == BOUNDARY_LABEL):
            fail(f"boundary-neighbor flag mismatch for {d}")
        out[d] = {"date_label": d, "filename": fn, "url": url, "expected_bytes": size}
        total += size
    if set(out) != set(LABELS):
        fail("metadata archive label set mismatch")
    if rep.get("expected_total_bytes") != total:
        fail("metadata expected-total mismatch")
    return out, rep


def _download_fresh(url: str, dest_part: Path, expected: int) -> None:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "BotMarketplace-SC001-E006-SpotBody/0.1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        status = int(getattr(resp, "status", 200))
        final = resp.geturl()
        if status != 200:
            fail(f"fresh GET HTTP {status}")
        if not trusted_url(final, Path(dest_part).name.removesuffix(".part")):
            fail("fresh GET final URL identity mismatch")
        with dest_part.open("wb") as f:
            while True:
                chunk = resp.read(CHUNK)
                if not chunk:
                    break
                f.write(chunk)
            f.flush(); os.fsync(f.fileno())
    if dest_part.stat().st_size != expected:
        fail(f"fresh GET size mismatch: {dest_part.stat().st_size} != {expected}")


def download_one(meta: dict) -> tuple[Path, bool]:
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    dest = ARCHIVES / meta["filename"]
    expected = int(meta["expected_bytes"])
    url = meta["url"]
    if not trusted_url(url, meta["filename"]):
        fail(f"untrusted frozen URL for {meta['filename']}")

    if dest.exists():
        if dest.stat().st_size == expected:
            return dest, True
        dest.unlink()

    part = Path(str(dest) + ".part")
    if part.exists() and part.stat().st_size > expected:
        part.unlink()

    already = part.stat().st_size if part.exists() else 0
    if already == expected:
        os.replace(part, dest)
        return dest, False

    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            already = part.stat().st_size if part.exists() else 0
            if already > 0:
                req = urllib.request.Request(
                    url, method="GET",
                    headers={"User-Agent": "BotMarketplace-SC001-E006-SpotBody/0.1", "Range": f"bytes={already}-"},
                )
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    status = int(getattr(resp, "status", 200))
                    final = resp.geturl()
                    cr = resp.headers.get("Content-Range", "")
                    if not trusted_url(final, meta["filename"]):
                        fail("resume GET final URL identity mismatch")
                    if status == 206 and cr.startswith(f"bytes {already}-"):
                        with part.open("ab") as f:
                            while True:
                                chunk = resp.read(CHUNK)
                                if not chunk:
                                    break
                                f.write(chunk)
                            f.flush(); os.fsync(f.fileno())
                    elif status == 200:
                        part.unlink(missing_ok=True)
                        _download_fresh(url, part, expected)
                    else:
                        fail(f"ambiguous Range response status={status} content-range={cr!r}")
            else:
                _download_fresh(url, part, expected)

            if part.stat().st_size != expected:
                fail(f"partial/final size mismatch: {part.stat().st_size} != {expected}")
            os.replace(part, dest)
            return dest, False
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(1.5 * attempt)
                continue
    raise RuntimeError(f"download failed for {meta['filename']}: {type(last).__name__}: {last}")


def new_day_state(day: str) -> dict:
    return {
        "date": day,
        "start_ms": day_start_ms(day),
        "rows": 0,
        "buy_count": 0,
        "sell_count": 0,
        "first_ts": None,
        "last_ts": None,
        "last_trade_id": None,
        "timestamp_backward_count": 0,
        "trade_id_duplicate_backward_count": 0,
        "trade_id_gap_count": 0,
        "minute_seen": bytearray(1440),
        "second_seen": bytearray(86400),
        "max_intertrade_gap_ms": 0,
    }


def update_target_state(state: dict, ts: int, tid: int, side: str) -> None:
    lo = state["start_ms"]
    hi = lo + DAY_MS
    if not (lo <= ts < hi):
        fail(f"target-day routing error for {state['date']}")
    prev_ts = state["last_ts"]
    prev_id = state["last_trade_id"]
    if prev_ts is not None:
        if ts < prev_ts:
            state["timestamp_backward_count"] += 1
        gap = ts - prev_ts
        if gap > state["max_intertrade_gap_ms"]:
            state["max_intertrade_gap_ms"] = gap
    if prev_id is not None:
        if tid <= prev_id:
            state["trade_id_duplicate_backward_count"] += 1
        elif tid != prev_id + 1:
            state["trade_id_gap_count"] += 1
    state["last_ts"] = ts
    state["last_trade_id"] = tid
    if state["first_ts"] is None:
        state["first_ts"] = ts
    state["rows"] += 1
    if side == "buy": state["buy_count"] += 1
    else: state["sell_count"] += 1
    state["minute_seen"][(ts - lo) // MIN_MS] = 1
    state["second_seen"][(ts - lo) // SEC_MS] = 1


def scan_archive(path: Path, meta: dict, target_states: dict[str, dict]) -> dict:
    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {path.name}: {bad}")
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) != 1:
            fail(f"unexpected ZIP member count {path.name}: {len(members)}")
        member = members[0]
        source_rows = 0
        buy = sell = 0
        first_ts = last_ts = None
        prev_ts = prev_tid = None
        duplicate_ts = 0
        id_gaps = 0
        with zf.open(member, "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            header = next(reader, None)
            if header != EXPECTED_HEADER:
                fail(f"unexpected header in {path.name}: {header!r}")
            for rownum, row in enumerate(reader, start=2):
                if not row:
                    continue
                if len(row) != 6:
                    fail(f"malformed row in {path.name}:{rownum}")
                inst, tid_txt, side, ptxt, stxt, ttxt = row
                if inst != TARGET_INST:
                    fail(f"instrument mismatch in {path.name}:{rownum}: {inst}")
                try:
                    tid = int(tid_txt)
                    px = float(ptxt)
                    sz = float(stxt)
                    ts = parse_ts_ms(ttxt)
                except Exception as exc:
                    raise RuntimeError(f"parse failure in {path.name}:{rownum}") from exc
                if side not in {"buy", "sell"}:
                    fail(f"side mismatch in {path.name}:{rownum}")
                if not math.isfinite(px) or px <= 0 or not math.isfinite(sz) or sz <= 0:
                    fail(f"price/size failure in {path.name}:{rownum}")
                if prev_ts is not None:
                    if ts < prev_ts:
                        fail(f"source timestamp reversal in {path.name}:{rownum}")
                    if ts == prev_ts:
                        duplicate_ts += 1
                if prev_tid is not None:
                    if tid <= prev_tid:
                        fail(f"source trade-id duplicate/backward in {path.name}:{rownum}")
                    if tid != prev_tid + 1:
                        id_gaps += 1
                prev_ts = ts; prev_tid = tid
                first_ts = ts if first_ts is None else first_ts
                last_ts = ts
                source_rows += 1
                if side == "buy": buy += 1
                else: sell += 1

                d = utc_day_text(ts)
                if d in target_states:
                    update_target_state(target_states[d], ts, tid, side)

    if source_rows <= 0:
        fail(f"no target rows in {path.name}")
    return {
        "date_label": meta["date_label"],
        "filename": meta["filename"],
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "zip_member": member.filename,
        "member_uncompressed_bytes": member.file_size,
        "source_rows": source_rows,
        "buy_count": buy,
        "sell_count": sell,
        "first_ts_ms": first_ts,
        "last_ts_ms": last_ts,
        "first_ts_utc": utc_iso(first_ts),
        "last_ts_utc": utc_iso(last_ts),
        "duplicate_timestamp_count": duplicate_ts,
        "trade_id_gap_count": id_gaps,
        "boundary_neighbor_only": meta["date_label"] == BOUNDARY_LABEL,
    }


def finalize_day_states(states: dict[str, dict]) -> list[dict]:
    out = []
    for d in TARGET_DAYS:
        s = states[d]
        minute_count = sum(s["minute_seen"])
        second_count = sum(s["second_seen"])
        passed = (
            s["rows"] > 0
            and s["buy_count"] > 0
            and s["sell_count"] > 0
            and s["timestamp_backward_count"] == 0
            and s["trade_id_duplicate_backward_count"] == 0
            and minute_count == 1440
            and s["first_ts"] is not None
            and s["last_ts"] is not None
            and s["start_ms"] <= s["first_ts"] < s["start_ms"] + DAY_MS
            and s["start_ms"] <= s["last_ts"] < s["start_ms"] + DAY_MS
        )
        out.append({
            "date": d,
            "status": "PASS" if passed else "REVIEW",
            "admitted_rows": s["rows"],
            "buy_count": s["buy_count"],
            "sell_count": s["sell_count"],
            "first_ts_ms": s["first_ts"],
            "last_ts_ms": s["last_ts"],
            "first_ts_utc": utc_iso(s["first_ts"]),
            "last_ts_utc": utc_iso(s["last_ts"]),
            "timestamp_backward_count": s["timestamp_backward_count"],
            "trade_id_duplicate_backward_count": s["trade_id_duplicate_backward_count"],
            "trade_id_gap_count": s["trade_id_gap_count"],
            "occupied_minute_count": minute_count,
            "occupied_second_count": second_count,
            "occupied_second_share": second_count / 86400.0,
            "max_intertrade_gap_ms": s["max_intertrade_gap_ms"],
        })
    return out


def run(mode: str) -> int:
    manifest, meta_rep = frozen_manifest()
    ROOT.mkdir(parents=True, exist_ok=True)
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    expected_total = sum(int(x["expected_bytes"]) for x in manifest.values())
    disk = shutil.disk_usage(ROOT)
    disk_ok = disk.free >= expected_total + MIN_FREE_RESERVE_BYTES
    if not disk_ok:
        fail("insufficient free disk for frozen bodies plus 20 GiB reserve")

    paths: dict[str, Path] = {}
    reused_count = 0
    downloaded_count = 0
    if mode == "download":
        for d in LABELS:
            p, reused = download_one(manifest[d])
            paths[d] = p
            if reused: reused_count += 1
            else: downloaded_count += 1
            print(f"BODY {'REUSE' if reused else 'DOWNLOADED'} {d} bytes={p.stat().st_size}")
    elif mode == "verify":
        for d in LABELS:
            p = ARCHIVES / manifest[d]["filename"]
            if not p.exists() or p.stat().st_size != manifest[d]["expected_bytes"]:
                fail(f"missing/size-mismatch local archive for verify: {p}")
            paths[d] = p
            reused_count += 1
            print(f"BODY LOCAL {d} bytes={p.stat().st_size}")
    else:
        fail(f"bad mode: {mode}")

    target_states = {d: new_day_state(d) for d in TARGET_DAYS}
    archive_rows = []
    for d in LABELS:
        print(f"AUDIT {d}")
        row = scan_archive(paths[d], manifest[d], target_states)
        if row["bytes"] != manifest[d]["expected_bytes"]:
            fail(f"post-audit byte mismatch for {d}")
        archive_rows.append(row)

    day_rows = finalize_day_states(target_states)
    day_pass = all(x["status"] == "PASS" for x in day_rows)
    archive_pass = len(archive_rows) == len(LABELS)
    status = "E006_SPOT_BODY_INTEGRITY_PASS" if archive_pass and day_pass else "E006_SPOT_BODY_INTEGRITY_REVIEW"

    report = {
        "stage": STAGE,
        "version": VERSION,
        "status": status,
        "mode": mode,
        "metadata_preflight_path": str(META_REPORT),
        "metadata_preflight_sha256": sha256_file(META_REPORT),
        "metadata_preflight_status": meta_rep.get("status"),
        "instrument": TARGET_INST,
        "archive_labels": list(LABELS),
        "discovery_performance_days": list(TARGET_DAYS),
        "boundary_neighbor_label": BOUNDARY_LABEL,
        "boundary_neighbor_performance_excluded": True,
        "archives": archive_rows,
        "utc_reconstruction_days": day_rows,
        "expected_total_bytes": expected_total,
        "local_total_bytes": sum(x["bytes"] for x in archive_rows),
        "reused_archive_count": reused_count,
        "downloaded_archive_count": downloaded_count,
        "disk_free_bytes_before": disk.free,
        "disk_pass": disk_ok,
        "basis_calculated": False,
        "returns_calculated": False,
        "pnl_calculated": False,
        "swap_prices_compared": False,
        "l2_accessed": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(OUT_REPORT, report)

    print(status)
    print("archive_count =", len(archive_rows))
    print("utc_day_pass_count =", sum(1 for x in day_rows if x["status"] == "PASS"), "/", len(day_rows))
    print("expected_total_bytes =", expected_total)
    print("local_total_bytes =", report["local_total_bytes"])
    print("reused_archive_count =", reused_count)
    print("downloaded_archive_count =", downloaded_count)
    print("boundary_neighbor_label = 2024-03-21 (performance excluded)")
    print("basis/returns/P&L calculated = False")
    print("swap_prices_compared = False")
    print("L2/Q2/Validation/Final = CLOSED")
    print("report =", OUT_REPORT)
    return 0 if status.endswith("PASS") else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["download", "verify"])
    args = ap.parse_args()
    return run(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
