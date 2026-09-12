"""SC001-DATA-Q006R — OKX trade UTC-day stitch repair.

Data engineering only. Reuses Q006 exact-date archives, downloads only D+1
neighbor archives, proves full source timestamp coverage, and reconstructs the
five frozen UTC target days. No TFI, future returns, P&L, Q2, Validation, Final.
Android/Pydroid; standard library only.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import time
import zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAGE = "SC001-DATA-Q006R-OKX-UTC-STITCH"
VERSION = "0.1"
PROTOCOL_COMMIT = "12f6541067c08d94cede1ba17a714636265c0935"
PARENT_STAGE = "SC001-DATA-Q006-OKX-TRADES"
TRADE_MODULE = "1"
TARGET_INST = "BTC-USDT-SWAP"
INST_TYPE = "SWAP"
INST_FAMILY = "BTC-USDT"

TARGET_DATES = (
    "2024-01-05",
    "2024-01-14",
    "2024-01-31",
    "2024-02-12",
    "2024-02-13",
)

DOWNLOAD = Path("/storage/emulated/0/Download")
PARENT_DIR = DOWNLOAD / "SC001_DATA_Q006_OKX_TRADES"
PARENT_REPORT = PARENT_DIR / "sc001_data_q006_okx_trades_report.json"
PARENT_MANIFEST = PARENT_DIR / "sc001_data_q006_okx_trades_manifest.json"
PARENT_ARCHIVES = PARENT_DIR / "archives"

WORKSPACE = DOWNLOAD / "SC001_DATA_Q006R_OKX_UTC_STITCH"
NEIGHBORS = WORKSPACE / "neighbor_archives"
REPORT = WORKSPACE / "sc001_data_q006r_okx_utc_stitch_report.json"
MANIFEST = WORKSPACE / "sc001_data_q006r_okx_utc_stitch_manifest.json"
SUMMARY = WORKSPACE / "sc001_data_q006r_okx_utc_stitch_summary.md"
SAFETY = WORKSPACE / "sc001_data_q006r_okx_utc_stitch_final_safety.json"

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
DISCOVERY_PATH = "/priapi/v5/broker/public/trade-data/download-link"
REFERER = "https://www.okx.com/historical-data"
USER_AGENT = "BotMarketplace-SC001-Q006R/0.1"
TIMEOUT = 90
RETRIES = 3
ALLOWED_HOST = "static.okx.com"

SESSION_DOWNLOAD_CAP_BYTES = 100_000_000
WORKSPACE_CAP_BYTES = 100_000_000
PER_FILE_CAP_BYTES = 25_000_000
PER_RESPONSE_CAP_BYTES = 4_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000
MAX_UNCOMPRESSED_MEMBER_BYTES = 1_000_000_000

EXPECTED_HEADER = [
    "instrument_name",
    "trade_id",
    "side",
    "price",
    "size",
    "created_time",
]

network_bytes_read = 0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def free_bytes() -> int:
    return shutil.disk_usage(DOWNLOAD).free


def safety_check(extra_workspace: int = 0, extra_network: int = 0) -> None:
    if network_bytes_read + max(0, extra_network) > SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError("Q006R session network cap would be exceeded")
    if dir_size(WORKSPACE) + max(0, extra_workspace) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("Q006R workspace cap would be exceeded")
    if free_bytes() - max(0, extra_workspace) < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("Q006R minimum free-space reserve would be violated")


def atomic_text(path: Path, text: str) -> None:
    raw = text.encode("utf-8")
    safety_check(extra_workspace=len(raw))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path: Path, obj) -> None:
    atomic_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iso_ms(ms: int | None) -> str | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def parse_ts_ms(text: str) -> int:
    s = text.strip()
    v = int(s)
    av = abs(v)
    if av >= 10**17:
        return v // 1_000_000
    if av >= 10**14:
        return v // 1_000
    if av >= 10**11:
        return v
    if av >= 10**9:
        return v * 1000
    raise ValueError("timestamp numeric scale unresolved")


def positive_decimal(text: str) -> Decimal:
    x = Decimal(text.strip())
    if not x.is_finite() or x <= 0:
        raise ValueError("non-positive/non-finite decimal")
    return x


def trusted_url(url: str, expected_filename: str | None = None) -> bool:
    try:
        p = urlparse(url)
        if p.scheme != "https" or (p.hostname or "").lower() != ALLOWED_HOST:
            return False
        if expected_filename is not None and Path(p.path).name != expected_filename:
            return False
        return True
    except Exception:
        return False


def date_bounds(date_text: str) -> tuple[int, int]:
    d = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(d.timestamp() * 1000), int((d + timedelta(days=1)).timestamp() * 1000)


def next_date_text(date_text: str) -> str:
    d = datetime.strptime(date_text, "%Y-%m-%d") + timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def discovery_payload(date_text: str) -> dict:
    lo, hi_exclusive = date_bounds(date_text)
    return {
        "module": TRADE_MODULE,
        "instType": INST_TYPE,
        "instQueryParam": {"instFamilyList": [INST_FAMILY]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(lo),
            "end": str(hi_exclusive - 1),
        },
    }


def request_json(domain: str, payload: dict) -> tuple[object | None, dict]:
    global network_bytes_read
    url = domain + DISCOVERY_PATH + "?t=" + str(int(time.time() * 1000))
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,*/*",
        "Content-Type": "application/json",
        "Referer": REFERER,
    }
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = Request(url, data=body, method="POST", headers=headers)
            with urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(PER_RESPONSE_CAP_BYTES + 1)
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
            if len(raw) > PER_RESPONSE_CAP_BYTES:
                raise RuntimeError("Q006R metadata response cap exceeded")
            network_bytes_read += len(raw)
            safety_check()
            obj = json.loads(raw.decode("utf-8", errors="strict"))
            return obj, {
                "status": status,
                "bytes_read": len(raw),
                "final_url": final,
                "json_ok": True,
            }
        except HTTPError as e:
            raw = e.read(min(PER_RESPONSE_CAP_BYTES, 256_000))
            network_bytes_read += len(raw)
            safety_check()
            obj = None
            try:
                obj = json.loads(raw.decode("utf-8", errors="replace"))
            except Exception:
                pass
            if e.code == 429 and attempt < RETRIES:
                time.sleep(1.5 * attempt)
                continue
            return obj, {
                "status": int(e.code),
                "bytes_read": len(raw),
                "http_error": True,
                "json_ok": obj is not None,
            }
        except (URLError, TimeoutError, OSError, ValueError, RuntimeError) as e:
            last = repr(e)
            if attempt < RETRIES:
                time.sleep(1.5 * attempt)
                continue
    return None, {"status": None, "error": last or "request failed"}


def extract_links(obj) -> list[dict]:
    out = []
    if not isinstance(obj, dict):
        return out
    data = obj.get("data")
    if not isinstance(data, dict):
        return out
    details = data.get("details")
    if not isinstance(details, list):
        return out
    for detail in details:
        groups = detail.get("groupDetails") if isinstance(detail, dict) else None
        if not isinstance(groups, list):
            continue
        for g in groups:
            if not isinstance(g, dict):
                continue
            fn = g.get("filename") or g.get("fileName")
            url = g.get("url")
            out.append({
                "filename": fn,
                "url": url,
                "sizeMB_raw": g.get("sizeMB"),
                "trusted_url": trusted_url(str(url), str(fn)) if url and fn else False,
            })
    return out


def discover(date_text: str) -> dict:
    payload = discovery_payload(date_text)
    attempts = []
    for domain in DOMAINS:
        obj, meta = request_json(domain, payload)
        code = obj.get("code") if isinstance(obj, dict) else None
        links = extract_links(obj)
        attempts.append({
            "domain": domain,
            "code": code,
            "meta": meta,
            "links": links,
        })
        if code == "0" and links:
            return {
                "status": "PASS",
                "date": date_text,
                "payload": payload,
                "selected_domain": domain,
                "links": links,
                "attempts": attempts,
            }
        time.sleep(0.8)
    return {
        "status": "NO_LINKS",
        "date": date_text,
        "payload": payload,
        "links": [],
        "attempts": attempts,
    }


def select_neighbor(links: list[dict], target_date: str) -> tuple[dict | None, str]:
    neighbor_date = next_date_text(target_date)
    expected = f"{TARGET_INST}-trades-{neighbor_date}.zip"
    exact = [x for x in links if x.get("filename") == expected and x.get("trusted_url") is True]
    if len(exact) == 1:
        return exact[0], "EXACT_NEXT_DATE_FILENAME"
    if len(exact) == 0:
        return None, "NO_EXACT_NEXT_DATE_FILENAME"
    return None, "MULTIPLE_EXACT_NEXT_DATE_FILENAMES"


def head_remote(url: str, expected_filename: str) -> dict:
    if not trusted_url(url, expected_filename):
        return {"status": "REJECTED_URL"}
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT, "Referer": REFERER})
        with urlopen(req, timeout=TIMEOUT) as resp:
            final = resp.geturl()
            cl = resp.headers.get("Content-Length")
            size = int(cl) if cl and cl.isdigit() else None
            ok = (
                int(getattr(resp, "status", 200)) == 200
                and trusted_url(final, expected_filename)
                and isinstance(size, int)
                and 0 < size <= PER_FILE_CAP_BYTES
            )
            return {
                "status": "PASS" if ok else "REVIEW",
                "http_status": int(getattr(resp, "status", 200)),
                "final_url": final,
                "content_length": size,
                "content_type": resp.headers.get("Content-Type"),
            }
    except Exception as e:
        return {"status": "ERROR", "error": repr(e)}


def download_archive(url: str, dest: Path, expected_bytes: int) -> dict:
    global network_bytes_read
    if expected_bytes <= 0 or expected_bytes > PER_FILE_CAP_BYTES:
        raise RuntimeError("Q006R neighbor size gate failed")
    if dest.exists() and dest.stat().st_size == expected_bytes:
        return {
            "status": "REUSED",
            "bytes": expected_bytes,
            "sha256": sha256_file(dest),
            "network_bytes": 0,
        }
    if dest.exists():
        dest.unlink()
    part = dest.with_suffix(dest.suffix + ".part")
    if part.exists():
        part.unlink()
    safety_check(extra_workspace=expected_bytes, extra_network=expected_bytes)
    req = Request(url, headers={"User-Agent": USER_AGENT, "Referer": REFERER})
    got = 0
    h = hashlib.sha256()
    try:
        with urlopen(req, timeout=TIMEOUT) as resp, part.open("wb") as out:
            if int(getattr(resp, "status", 200)) != 200 or not trusted_url(resp.geturl(), dest.name):
                raise RuntimeError("Q006R GET identity failed")
            cl = resp.headers.get("Content-Length")
            if cl and cl.isdigit() and int(cl) != expected_bytes:
                raise RuntimeError("Q006R GET Content-Length changed from HEAD")
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                got += len(chunk)
                network_bytes_read += len(chunk)
                if got > expected_bytes or got > PER_FILE_CAP_BYTES or network_bytes_read > SESSION_DOWNLOAD_CAP_BYTES:
                    raise RuntimeError("Q006R download cap/size violation")
                out.write(chunk)
                h.update(chunk)
            out.flush()
            os.fsync(out.fileno())
        if got != expected_bytes:
            raise RuntimeError(f"Q006R archive size mismatch got={got} expected={expected_bytes}")
        os.replace(part, dest)
        return {
            "status": "DOWNLOADED",
            "bytes": got,
            "sha256": h.hexdigest(),
            "network_bytes": got,
        }
    except Exception:
        if part.exists():
            part.unlink()
        raise


def verify_parent() -> tuple[dict, dict, dict[str, dict]]:
    if not PARENT_REPORT.exists() or not PARENT_MANIFEST.exists():
        raise RuntimeError("missing Q006 parent report/manifest")
    report = json.loads(PARENT_REPORT.read_text(encoding="utf-8"))
    manifest = json.loads(PARENT_MANIFEST.read_text(encoding="utf-8"))
    if report.get("stage") != PARENT_STAGE or manifest.get("stage") != PARENT_STAGE:
        raise RuntimeError("Q006 parent stage mismatch")
    if report.get("overall_status") != "SCHEMA_REVIEW" or manifest.get("overall_status") != "SCHEMA_REVIEW":
        raise RuntimeError("Q006 parent must be SCHEMA_REVIEW")
    if report.get("strategy_features_calculated") is not False:
        raise RuntimeError("Q006 parent feature firewall mismatch")
    if report.get("future_returns_calculated") is not False:
        raise RuntimeError("Q006 parent future-return firewall mismatch")
    if report.get("strategy_pnl_calculated") is not False:
        raise RuntimeError("Q006 parent P&L firewall mismatch")
    if report.get("q2_okx_accessed") is not False or report.get("validation_or_final_accessed") is not False:
        raise RuntimeError("Q006 parent split firewall mismatch")
    files = manifest.get("files") or []
    by_date = {x.get("date"): x for x in files}
    if set(by_date) != set(TARGET_DATES):
        raise RuntimeError("Q006 parent target-date set mismatch")
    for date_text, row in by_date.items():
        expected_name = f"{TARGET_INST}-trades-{date_text}.zip"
        if row.get("filename") != expected_name:
            raise RuntimeError(f"Q006 parent filename mismatch: {date_text}")
        p = PARENT_ARCHIVES / expected_name
        if not p.exists():
            raise RuntimeError(f"missing Q006 archive: {p}")
        if p.stat().st_size != row.get("bytes"):
            raise RuntimeError(f"Q006 archive size mismatch: {date_text}")
        if sha256_file(p) != row.get("sha256"):
            raise RuntimeError(f"Q006 archive SHA mismatch: {date_text}")
    return report, manifest, by_date


def scan_archive(
    path: Path,
    archive_label: str,
    target_lo: int,
    target_hi: int,
    stitch: dict,
) -> dict:
    expected_member = f"{TARGET_INST}-trades-{archive_label}.csv"
    source = {
        "archive_label": archive_label,
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "member": None,
        "header": None,
        "source_rows": 0,
        "source_invalid_rows": 0,
        "source_instrument_mismatch": 0,
        "source_timestamp_backwards": 0,
        "source_trade_id_backwards_or_dup": 0,
        "first_ts": None,
        "last_ts": None,
        "first_ts_utc": None,
        "last_ts_utc": None,
        "buy_rows": 0,
        "sell_rows": 0,
    }
    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure: {bad}")
        members = [x for x in zf.infolist() if not x.is_dir()]
        if len(members) != 1:
            raise RuntimeError(f"expected one CSV member in {path.name}, got {len(members)}")
        info = members[0]
        if info.file_size > MAX_UNCOMPRESSED_MEMBER_BYTES:
            raise RuntimeError("Q006R uncompressed member cap exceeded")
        if Path(info.filename).name != expected_member:
            raise RuntimeError(f"Q006R member name mismatch: {info.filename}")
        source["member"] = info.filename

        with zf.open(info, "r") as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
            try:
                header = next(reader)
            except StopIteration:
                raise RuntimeError(f"empty CSV: {path.name}")
            normalized = [x.strip().lower() for x in header]
            source["header"] = normalized
            if normalized != EXPECTED_HEADER:
                raise RuntimeError(f"Q006R header mismatch: {path.name}: {normalized}")

            prev_source_ts = None
            prev_source_tid = None
            for row in reader:
                if not row:
                    continue
                try:
                    if len(row) != 6:
                        raise ValueError("row width != 6")
                    inst = row[0].strip()
                    tid = int(row[1].strip())
                    side = row[2].strip().lower()
                    positive_decimal(row[3])
                    positive_decimal(row[4])
                    ts = parse_ts_ms(row[5])
                    if side not in {"buy", "sell"}:
                        raise ValueError("invalid side")
                except Exception:
                    source["source_invalid_rows"] += 1
                    continue

                source["source_rows"] += 1
                if source["first_ts"] is None:
                    source["first_ts"] = ts
                source["last_ts"] = ts
                if inst != TARGET_INST:
                    source["source_instrument_mismatch"] += 1
                if side == "buy":
                    source["buy_rows"] += 1
                else:
                    source["sell_rows"] += 1
                if prev_source_ts is not None and ts < prev_source_ts:
                    source["source_timestamp_backwards"] += 1
                prev_source_ts = ts
                if prev_source_tid is not None and tid <= prev_source_tid:
                    source["source_trade_id_backwards_or_dup"] += 1
                prev_source_tid = tid

                if target_lo <= ts < target_hi:
                    stitch["admitted_rows"] += 1
                    if inst != TARGET_INST:
                        stitch["instrument_mismatch"] += 1
                    stitch["sides"][side] = stitch["sides"].get(side, 0) + 1
                    stitch["minutes"].add((ts - target_lo) // 60_000)
                    if stitch["first_ts"] is None:
                        stitch["first_ts"] = ts
                        stitch["first_trade_id"] = tid
                    stitch["last_ts"] = ts
                    stitch["last_trade_id"] = tid
                    if stitch["prev_ts"] is not None and ts < stitch["prev_ts"]:
                        stitch["timestamp_backwards"] += 1
                    stitch["prev_ts"] = ts
                    if stitch["prev_tid"] is not None:
                        delta = tid - stitch["prev_tid"]
                        if delta <= 0:
                            stitch["trade_id_backwards_or_dup"] += 1
                        elif delta != 1:
                            stitch["trade_id_gap_count_diagnostic"] += 1
                    stitch["prev_tid"] = tid

    source["first_ts_utc"] = iso_ms(source["first_ts"])
    source["last_ts_utc"] = iso_ms(source["last_ts"])
    return source


def write_outputs(report: dict) -> None:
    atomic_json(REPORT, report)
    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "protocol_commit": PROTOCOL_COMMIT,
        "overall_status": report.get("overall_status"),
        "strategy_features_calculated": False,
        "future_returns_calculated": False,
        "strategy_pnl_calculated": False,
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
        "days": [],
    }
    for d in report.get("days", []):
        manifest["days"].append({
            "date": d.get("date"),
            "status": d.get("status"),
            "admitted_rows": (d.get("stitch") or {}).get("admitted_rows"),
            "minute_buckets_observed": (d.get("stitch") or {}).get("minute_buckets_observed"),
            "first_ts": (d.get("stitch") or {}).get("first_ts"),
            "last_ts": (d.get("stitch") or {}).get("last_ts"),
            "exact_archive": d.get("exact_archive"),
            "neighbor_archive": d.get("neighbor_archive"),
        })
    atomic_json(MANIFEST, manifest)

    lines = [
        "# SC001-DATA-Q006R — OKX UTC-stitch repair",
        "",
        f"- Overall: `{report.get('overall_status')}`",
        "- Strategy features: **NO**",
        "- Future returns: **NO**",
        "- Strategy P&L: **NO**",
        "- 2024-Q2 OKX: **NO**",
        f"- Network bytes read: {report.get('network_bytes_read', 0)}",
        "",
        "## UTC-day reconstruction",
    ]
    for d in report.get("days", []):
        s = d.get("stitch") or {}
        lines.append(
            f"- {d.get('date')}: **{d.get('status')}**; rows={s.get('admitted_rows')}; "
            f"minutes={s.get('minute_buckets_observed')}/1440; "
            f"backwards={s.get('timestamp_backwards')}; "
            f"trade_id_backwards_or_dup={s.get('trade_id_backwards_or_dup')}; "
            f"trade_id_gap_diag={s.get('trade_id_gap_count_diagnostic')}"
        )
    lines += [
        "",
        "## Boundary",
        "Data repair/qualification only. No TFI, no response labels, no P&L, no Q2 OKX, no formal Validation/Final.",
    ]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")

    atomic_json(SAFETY, {
        "stage": STAGE,
        "network_bytes_read": report.get("network_bytes_read", network_bytes_read),
        "workspace_bytes_after_outputs": dir_size(WORKSPACE),
        "free_bytes_after_outputs": free_bytes(),
        "caps": {
            "session_download": SESSION_DOWNLOAD_CAP_BYTES,
            "workspace": WORKSPACE_CAP_BYTES,
            "per_file": PER_FILE_CAP_BYTES,
            "per_response": PER_RESPONSE_CAP_BYTES,
            "reserve": MIN_FREE_RESERVE_BYTES,
        },
        "strategy_features_calculated": False,
        "future_returns_calculated": False,
        "strategy_pnl_calculated": False,
    })


def main() -> None:
    global network_bytes_read
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    NEIGHBORS.mkdir(parents=True, exist_ok=True)
    safety_check()
    parent_report, parent_manifest, parent_by_date = verify_parent()

    report = {
        "stage": STAGE,
        "version": VERSION,
        "protocol_commit": PROTOCOL_COMMIT,
        "started_at_utc": now_iso(),
        "scope": {
            "venue": "OKX",
            "instrument": TARGET_INST,
            "target_utc_dates": list(TARGET_DATES),
            "source_archive_rule": "D plus D+1; filter to UTC [D,D+1)",
            "trade_module": TRADE_MODULE,
        },
        "parent": {
            "report": str(PARENT_REPORT),
            "manifest": str(PARENT_MANIFEST),
            "overall_status": parent_report.get("overall_status"),
        },
        "strategy_features_calculated": False,
        "future_returns_calculated": False,
        "strategy_pnl_calculated": False,
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
        "days": [],
    }

    try:
        for date_text in TARGET_DATES:
            print(f"[{date_text}] discover D+1 neighbor...")
            discovery = discover(date_text)
            candidate, identity_mode = select_neighbor(discovery.get("links", []), date_text)
            if candidate is None:
                report["days"].append({
                    "date": date_text,
                    "status": "REVIEW",
                    "reason": identity_mode,
                    "discovery": discovery,
                })
                report["network_bytes_read"] = network_bytes_read
                write_outputs(report)
                continue

            neighbor_date = next_date_text(date_text)
            neighbor_name = f"{TARGET_INST}-trades-{neighbor_date}.zip"
            print(f"[{date_text}] HEAD {neighbor_name}...")
            head = head_remote(str(candidate["url"]), neighbor_name)
            if head.get("status") != "PASS":
                report["days"].append({
                    "date": date_text,
                    "status": "REVIEW",
                    "reason": "neighbor_head_failed",
                    "identity_mode": identity_mode,
                    "head": head,
                })
                report["network_bytes_read"] = network_bytes_read
                write_outputs(report)
                continue

            expected_bytes = int(head["content_length"])
            print(f"[{date_text}] download/reuse neighbor ({expected_bytes} bytes)...")
            neighbor_path = NEIGHBORS / neighbor_name
            neighbor_dl = download_archive(str(candidate["url"]), neighbor_path, expected_bytes)

            exact_row = parent_by_date[date_text]
            exact_name = exact_row["filename"]
            exact_path = PARENT_ARCHIVES / exact_name
            if exact_path.stat().st_size != exact_row["bytes"] or sha256_file(exact_path) != exact_row["sha256"]:
                raise RuntimeError(f"Q006 exact archive identity changed: {date_text}")

            target_lo, target_hi = date_bounds(date_text)
            stitch = {
                "admitted_rows": 0,
                "instrument_mismatch": 0,
                "sides": {},
                "minutes": set(),
                "first_ts": None,
                "last_ts": None,
                "first_trade_id": None,
                "last_trade_id": None,
                "prev_ts": None,
                "prev_tid": None,
                "timestamp_backwards": 0,
                "trade_id_backwards_or_dup": 0,
                "trade_id_gap_count_diagnostic": 0,
            }

            print(f"[{date_text}] scan exact archive...")
            src_a = scan_archive(exact_path, date_text, target_lo, target_hi, stitch)
            print(f"[{date_text}] scan neighbor archive...")
            src_b = scan_archive(neighbor_path, neighbor_date, target_lo, target_hi, stitch)

            source_integrity = (
                src_a["source_invalid_rows"] == 0
                and src_b["source_invalid_rows"] == 0
                and src_a["source_timestamp_backwards"] == 0
                and src_b["source_timestamp_backwards"] == 0
                and src_a["source_instrument_mismatch"] == 0
                and src_b["source_instrument_mismatch"] == 0
            )
            gates = {
                "exact_archive_identity_verified": True,
                "neighbor_archive_identity_verified": neighbor_dl.get("status") in {"DOWNLOADED", "REUSED"},
                "source_parse_integrity": source_integrity,
                "target_rows_positive": stitch["admitted_rows"] > 0,
                "instrument_mismatch_zero": stitch["instrument_mismatch"] == 0,
                "timestamps_monotonic_nondecreasing": stitch["timestamp_backwards"] == 0,
                "buy_and_sell_observed": stitch["sides"].get("buy", 0) > 0 and stitch["sides"].get("sell", 0) > 0,
                "all_1440_utc_minutes_observed": len(stitch["minutes"]) == 1440,
                "trade_ids_monotonic_increasing": stitch["trade_id_backwards_or_dup"] == 0,
                "first_and_last_inside_target": (
                    stitch["first_ts"] is not None
                    and stitch["last_ts"] is not None
                    and target_lo <= stitch["first_ts"] < target_hi
                    and target_lo <= stitch["last_ts"] < target_hi
                ),
            }
            day_status = "PASS" if all(gates.values()) else "REVIEW"
            stitch_out = {
                "admitted_rows": stitch["admitted_rows"],
                "instrument_mismatch": stitch["instrument_mismatch"],
                "buy_rows": stitch["sides"].get("buy", 0),
                "sell_rows": stitch["sides"].get("sell", 0),
                "minute_buckets_observed": len(stitch["minutes"]),
                "first_ts": stitch["first_ts"],
                "last_ts": stitch["last_ts"],
                "first_ts_utc": iso_ms(stitch["first_ts"]),
                "last_ts_utc": iso_ms(stitch["last_ts"]),
                "first_trade_id": stitch["first_trade_id"],
                "last_trade_id": stitch["last_trade_id"],
                "timestamp_backwards": stitch["timestamp_backwards"],
                "trade_id_backwards_or_dup": stitch["trade_id_backwards_or_dup"],
                "trade_id_gap_count_diagnostic": stitch["trade_id_gap_count_diagnostic"],
                "gates": gates,
            }
            report["days"].append({
                "date": date_text,
                "status": day_status,
                "identity_mode": identity_mode,
                "exact_archive": {
                    "filename": exact_name,
                    "bytes": exact_row["bytes"],
                    "sha256": exact_row["sha256"],
                },
                "neighbor_archive": {
                    "date": neighbor_date,
                    "filename": neighbor_name,
                    "url": candidate["url"],
                    "head": head,
                    "download": neighbor_dl,
                },
                "source_scans": [src_a, src_b],
                "stitch": stitch_out,
            })
            report["network_bytes_read"] = network_bytes_read
            write_outputs(report)
            safety_check()

        report["days_total"] = len(report["days"])
        report["days_passed"] = sum(1 for x in report["days"] if x.get("status") == "PASS")
        report["overall_status"] = (
            "PASS"
            if report["days_total"] == len(TARGET_DATES)
            and report["days_passed"] == len(TARGET_DATES)
            else "REVIEW"
        )
        report["network_bytes_read"] = network_bytes_read
        report["finished_at_utc"] = now_iso()
        write_outputs(report)
        print(
            f"COMPLETE: {report['overall_status']} {report['days_passed']}/{report['days_total']} | "
            f"network={network_bytes_read} | TFI=NO | RETURNS=NO | P&L=NO"
        )
    except Exception as exc:
        report["overall_status"] = "ERROR"
        report["error"] = repr(exc)
        report["network_bytes_read"] = network_bytes_read
        report["finished_at_utc"] = now_iso()
        write_outputs(report)
        raise


if __name__ == "__main__":
    main()
