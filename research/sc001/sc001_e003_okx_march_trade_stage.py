"""SC001-E003 March 2024 OKX trade acquisition stage.

Data-only. No E003 feature calculation, response statistics, P&L, L2, Q2,
Validation or Final access.

Modes:
  preflight  discover exact official archive identities and HEAD sizes only
  download   download March 1-31 Q1 trade archives, hash and ZIP/header validate
  verify     recompute local identity/integrity from the frozen download manifest

Target experiment UTC days are March 1-30. March 31 is acquired only as the
D+1 neighbor needed to construct March 30 under the already-qualified Q006R
UTC-stitch semantics. No April/Q2 archive is requested.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAGE = "SC001-E003-OKX-MARCH-TRADE-STAGE"
VERSION = "0.1"
TARGET_INST = "BTC-USDT-SWAP"
INST_TYPE = "SWAP"
INST_FAMILY = "BTC-USDT"
TRADE_MODULE = "1"
EXPECTED_HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]
DOMAINS = ("https://www.okx.com", "https://us.okx.com")
DISCOVERY_PATH = "/priapi/v5/broker/public/trade-data/download-link"
REFERER = "https://www.okx.com/historical-data"
UA = "BotMarketplace-SC001-E003-MarchTrades/0.1"
TIMEOUT = 90
RETRIES = 3
ALLOWED_HOST = "static.okx.com"
MAX_META_BYTES = 4_000_000
MAX_TOTAL_BYTES = 1_000_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
ROOT = DATA_ROOT / "SC001_E003_OKX_MARCH_TRADES"
ARCHIVES = ROOT / "archives"
PREFLIGHT = ROOT / "sc001_e003_okx_march_trade_preflight.json"
REPORT = ROOT / "sc001_e003_okx_march_trade_stage_report.json"

TARGET_DAYS = tuple(f"2024-03-{d:02d}" for d in range(1, 31))
ARCHIVE_DAYS = tuple(f"2024-03-{d:02d}" for d in range(1, 32))


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def date_bounds(date_text: str) -> tuple[int, int]:
    d = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    hi = int((d + timedelta(days=1) - timedelta(milliseconds=1)).timestamp() * 1000)
    return lo, hi


def payload(date_text: str) -> dict:
    lo, hi = date_bounds(date_text)
    return {
        "module": TRADE_MODULE,
        "instType": INST_TYPE,
        "instQueryParam": {"instFamilyList": [INST_FAMILY]},
        "dateQuery": {"dateAggrType": "daily", "begin": str(lo), "end": str(hi)},
    }


def request_json(domain: str, date_text: str) -> dict | None:
    url = domain + DISCOVERY_PATH + "?t=" + str(int(time.time() * 1000))
    body = json.dumps(payload(date_text), separators=(",", ":")).encode("utf-8")
    headers = {"User-Agent": UA, "Accept": "application/json,*/*", "Content-Type": "application/json", "Referer": REFERER}
    for attempt in range(1, RETRIES + 1):
        try:
            req = Request(url, data=body, method="POST", headers=headers)
            with urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_META_BYTES + 1)
            if len(raw) > MAX_META_BYTES:
                fail("metadata response cap exceeded")
            obj = json.loads(raw.decode("utf-8"))
            if isinstance(obj, dict) and obj.get("code") == "0":
                return obj
        except HTTPError as exc:
            if exc.code == 429 and attempt < RETRIES:
                time.sleep(1.5 * attempt); continue
            return None
        except (URLError, TimeoutError, OSError, ValueError, RuntimeError):
            if attempt < RETRIES:
                time.sleep(1.5 * attempt); continue
            return None
    return None


def trusted_url(url: str, expected_filename: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme == "https" and (p.hostname or "").lower() == ALLOWED_HOST and Path(p.path).name == expected_filename
    except Exception:
        return False


def walk_file_nodes(node):
    if isinstance(node, dict):
        fn = node.get("filename") or node.get("fileName")
        url = node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
        if isinstance(fn, str) and isinstance(url, str):
            yield fn, url
        for v in node.values():
            yield from walk_file_nodes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_file_nodes(v)


def discover_exact(file_date: str) -> str:
    expected = f"{TARGET_INST}-trades-{file_date}.zip"
    d = datetime.strptime(file_date, "%Y-%m-%d")
    query_dates = (file_date, (d - timedelta(days=1)).strftime("%Y-%m-%d"))
    found = []
    for qd in query_dates:
        for domain in DOMAINS:
            obj = request_json(domain, qd)
            if obj is None:
                continue
            for fn, url in walk_file_nodes(obj.get("data")):
                if fn == expected and trusted_url(url, expected) and url not in found:
                    found.append(url)
            if found:
                break
        if found:
            break
    if len(found) != 1:
        fail(f"exact archive not uniquely discovered for {expected}: {len(found)}")
    return found[0]


def head_size(url: str, filename: str) -> int:
    req = Request(url, method="HEAD", headers={"User-Agent": UA, "Referer": REFERER})
    with urlopen(req, timeout=TIMEOUT) as resp:
        final = resp.geturl(); status = int(getattr(resp, "status", 200)); cl = resp.headers.get("Content-Length")
    if status != 200 or not trusted_url(final, filename) or not cl or not cl.isdigit():
        fail(f"HEAD identity/size failure for {filename}")
    return int(cl)


def zip_integrity(path: Path) -> dict:
    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {path.name}: {bad}")
        members = [x for x in zf.infolist() if not x.is_dir()]
        if len(members) != 1:
            fail(f"unexpected ZIP member count {path.name}: {len(members)}")
        info = members[0]
        with zf.open(info, "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            header = next(reader, None)
            if header != EXPECTED_HEADER:
                fail(f"unexpected trade header in {path.name}: {header!r}")
            target_rows = 0; first_ts = None; last_ts = None
            for row in reader:
                if not row:
                    continue
                if len(row) != 6:
                    fail(f"malformed trade row in {path.name}")
                if row[0] != TARGET_INST:
                    continue
                try:
                    ts = int(row[5])
                except Exception as exc:
                    raise RuntimeError(f"bad timestamp in {path.name}: {row!r}") from exc
                target_rows += 1
                first_ts = ts if first_ts is None else min(first_ts, ts)
                last_ts = ts if last_ts is None else max(last_ts, ts)
            if target_rows <= 0:
                fail(f"no {TARGET_INST} rows in {path.name}")
    return {"member": info.filename, "member_uncompressed_bytes": info.file_size, "target_rows": target_rows, "first_target_ts": first_ts, "last_target_ts": last_ts}


def load_obj(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required file {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected {path}")
    return x


def mode_preflight() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    rows = []
    total = 0
    for d in ARCHIVE_DAYS:
        fn = f"{TARGET_INST}-trades-{d}.zip"
        url = discover_exact(d)
        size = head_size(url, fn)
        total += size
        if total > MAX_TOTAL_BYTES:
            fail(f"preflight total exceeds {MAX_TOTAL_BYTES} bytes")
        rows.append({"date": d, "filename": fn, "url": url, "expected_bytes": size})
        print(f"PREFLIGHT {d} {size:,} bytes")
    atomic_json(PREFLIGHT, {
        "stage": STAGE, "version": VERSION, "status": "PASS",
        "target_utc_days": list(TARGET_DAYS), "required_archive_days": list(ARCHIVE_DAYS),
        "archives": rows, "expected_total_bytes": total,
        "q2_market_data_body_accessed": False, "validation_or_final_accessed": False,
        "alpha_calculated": False, "pnl_calculated": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    print("E003_MARCH_TRADE_PREFLIGHT_PASS")
    print("archive_count =", len(rows))
    print("expected_total_bytes =", total)
    print("last_archive_date =", ARCHIVE_DAYS[-1])
    print("Q2/Validation/Final = CLOSED")
    print("alpha/P&L calculated = NO")


def download_one(meta: dict) -> dict:
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    fn = meta["filename"]; expected = int(meta["expected_bytes"]); url = meta["url"]
    dest = ARCHIVES / fn
    if dest.exists() and dest.stat().st_size == expected:
        integrity = zip_integrity(dest)
        return {**meta, "path": str(dest), "bytes": expected, "sha256": sha256_file(dest), "reused": True, "integrity": integrity}
    if dest.exists():
        dest.unlink()
    part = Path(str(dest) + ".part")
    already = part.stat().st_size if part.exists() else 0
    if shutil.disk_usage(DATA_ROOT).free - max(0, expected - already) < MIN_FREE_RESERVE_BYTES:
        fail("4 GB free-space reserve would be violated")
    cmd = ["curl", "-L", "--fail", "--retry", "5", "--retry-delay", "3", "-C", "-", "-A", UA, "-e", REFERER, "-o", str(part), url]
    print(f"DOWNLOAD {fn} ({expected:,} bytes)")
    cp = subprocess.run(cmd)
    if cp.returncode != 0:
        fail(f"curl failed {fn} rc={cp.returncode}")
    if not part.exists() or part.stat().st_size != expected:
        fail(f"download size mismatch {fn}")
    os.replace(part, dest)
    integrity = zip_integrity(dest)
    digest = sha256_file(dest)
    print(f"VERIFIED {fn} SHA256={digest}")
    return {**meta, "path": str(dest), "bytes": expected, "sha256": digest, "reused": False, "integrity": integrity}


def mode_download() -> None:
    pf = load_obj(PREFLIGHT)
    if pf.get("status") != "PASS" or pf.get("q2_market_data_body_accessed") is not False:
        fail("preflight not qualified")
    rows = pf.get("archives") or []
    if len(rows) != len(ARCHIVE_DAYS):
        fail("preflight archive count mismatch")
    downloaded = [download_one(x) for x in rows]
    atomic_json(REPORT, {
        "stage": STAGE, "version": VERSION, "status": "PASS",
        "target_utc_days": list(TARGET_DAYS), "required_archive_days": list(ARCHIVE_DAYS),
        "archives": downloaded, "total_bytes": sum(int(x["bytes"]) for x in downloaded),
        "q2_market_data_body_accessed": False, "validation_or_final_accessed": False,
        "alpha_calculated": False, "pnl_calculated": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    print("E003_MARCH_TRADE_DOWNLOAD_PASS")
    print("archives =", len(downloaded))
    print("Q2/Validation/Final = CLOSED")
    print("alpha/P&L calculated = NO")


def mode_verify() -> None:
    rep = load_obj(REPORT)
    if rep.get("status") != "PASS" or rep.get("q2_market_data_body_accessed") is not False:
        fail("download report not qualified")
    rows = rep.get("archives") or []
    if len(rows) != len(ARCHIVE_DAYS):
        fail("download manifest count mismatch")
    for x in rows:
        p = Path(x["path"])
        if not p.exists() or p.stat().st_size != int(x["bytes"]):
            fail(f"local size/existence mismatch {p}")
        got = sha256_file(p)
        if got != x["sha256"]:
            fail(f"local SHA mismatch {p.name}")
        zip_integrity(p)
        print(f"PASS {p.name} {got}")
    print("E003_MARCH_TRADE_VERIFY_PASS")
    print("archive_count =", len(rows))
    print("Q2/Validation/Final = CLOSED")
    print("alpha/P&L calculated = NO")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("preflight", "download", "verify"))
    args = ap.parse_args()
    if args.mode == "preflight": mode_preflight()
    elif args.mode == "download": mode_download()
    else: mode_verify()


if __name__ == "__main__":
    main()
