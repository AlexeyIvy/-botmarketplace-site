"""SC001-DATA-Q006 — OKX Q1 trade archive acquisition/schema qualification.

Data engineering only. No E002 features, no future returns, no P&L, no
Validation/Final. Android/Pydroid; standard library only.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import shutil
import time
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAGE = "SC001-DATA-Q006-OKX-TRADES"
VERSION = "0.1"
PARENT_STAGE = "SC001-DATA-Q005R-OKX-TRADE-PREFLIGHT"
DOWNLOAD = Path("/storage/emulated/0/Download")
PARENT_REPORT = DOWNLOAD / "SC001_DATA_Q005R_OKX_TRADE_PREFLIGHT" / "sc001_data_q005r_okx_trade_preflight_report.json"
WORKSPACE = DOWNLOAD / "SC001_DATA_Q006_OKX_TRADES"
ARCHIVES = WORKSPACE / "archives"
REPORT = WORKSPACE / "sc001_data_q006_okx_trades_report.json"
MANIFEST = WORKSPACE / "sc001_data_q006_okx_trades_manifest.json"
SUMMARY = WORKSPACE / "sc001_data_q006_okx_trades_summary.md"
SAFETY = WORKSPACE / "sc001_data_q006_okx_trades_final_safety.json"

EXPECTED_DATES = (
    "2024-01-05", "2024-01-14", "2024-01-31", "2024-02-12", "2024-02-13",
)
EXPECTED_TOTAL_COMPRESSED_BYTES = 30_080_404
SESSION_DOWNLOAD_CAP_BYTES = 100_000_000
WORKSPACE_CAP_BYTES = 100_000_000
PER_FILE_CAP_BYTES = 25_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000
MAX_UNCOMPRESSED_MEMBER_BYTES = 1_000_000_000
ALLOWED_HOST = "static.okx.com"
USER_AGENT = "BotMarketplace-SC001-Q006/0.1"
REFERER = "https://www.okx.com/historical-data"
TIMEOUT = 90

network_bytes_read = 0

ALIASES = {
    "timestamp": {"ts", "timestamp", "time", "trade_time", "tradetime", "created_at", "createdat"},
    "price": {"px", "price", "trade_price", "tradeprice"},
    "size": {"sz", "size", "qty", "quantity", "volume", "amount"},
    "side": {"side", "taker_side", "takerside", "direction"},
    "trade_id": {"tradeid", "trade_id", "id", "trade-id"},
    "instrument": {"instid", "inst_id", "instrument", "instrument_id", "symbol"},
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def free_bytes() -> int:
    return shutil.disk_usage(DOWNLOAD).free


def safety_check(extra_workspace: int = 0, extra_network: int = 0):
    if network_bytes_read + max(0, extra_network) > SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError("Q006 session network cap would be exceeded")
    if dir_size(WORKSPACE) + max(0, extra_workspace) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("Q006 workspace cap would be exceeded")
    if free_bytes() - max(0, extra_workspace) < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("Q006 free-space reserve would be violated")


def atomic_json(path: Path, obj):
    raw = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    safety_check(extra_workspace=len(raw))
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_text(path: Path, text: str):
    raw = text.encode("utf-8")
    safety_check(extra_workspace=len(raw))
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def valid_url(url: str, filename: str) -> bool:
    p = urlparse(url)
    return p.scheme == "https" and (p.hostname or "").lower() == ALLOWED_HOST and Path(p.path).name == filename


def head_remote(url: str, filename: str) -> dict:
    if not valid_url(url, filename):
        return {"status": "REJECTED_URL"}
    req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT, "Referer": REFERER})
    with urlopen(req, timeout=TIMEOUT) as resp:
        final = resp.geturl()
        size = resp.headers.get("Content-Length")
        return {
            "status": "PASS" if int(getattr(resp, "status", 200)) == 200 and valid_url(final, filename) and size and size.isdigit() else "REVIEW",
            "http_status": int(getattr(resp, "status", 200)),
            "final_url": final,
            "content_length": int(size) if size and size.isdigit() else None,
            "content_type": resp.headers.get("Content-Type"),
        }


def download_archive(url: str, dest: Path, expected_bytes: int) -> dict:
    global network_bytes_read
    if expected_bytes <= 0 or expected_bytes > PER_FILE_CAP_BYTES:
        raise RuntimeError("Q006 per-file size gate failed")
    if dest.exists() and dest.stat().st_size == expected_bytes:
        return {"status": "REUSED", "bytes": expected_bytes, "sha256": sha256_file(dest), "network_bytes": 0}
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
            if int(getattr(resp, "status", 200)) != 200 or not valid_url(resp.geturl(), dest.name):
                raise RuntimeError("Q006 GET identity failed")
            cl = resp.headers.get("Content-Length")
            if cl and cl.isdigit() and int(cl) != expected_bytes:
                raise RuntimeError("Q006 GET Content-Length changed from frozen HEAD")
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                got += len(chunk)
                network_bytes_read += len(chunk)
                if got > expected_bytes or got > PER_FILE_CAP_BYTES or network_bytes_read > SESSION_DOWNLOAD_CAP_BYTES:
                    raise RuntimeError("Q006 download cap/size violation")
                out.write(chunk)
                h.update(chunk)
            out.flush(); os.fsync(out.fileno())
        if got != expected_bytes:
            raise RuntimeError(f"Q006 archive size mismatch got={got} expected={expected_bytes}")
        os.replace(part, dest)
        return {"status": "DOWNLOADED", "bytes": got, "sha256": h.hexdigest(), "network_bytes": got}
    except Exception:
        if part.exists():
            part.unlink()
        raise


def norm(s: str) -> str:
    return s.strip().lower().replace(" ", "_").replace("-", "_")


def resolve_columns(header):
    normalized = [norm(x) for x in header]
    out = {}
    for role, aliases in ALIASES.items():
        hits = [i for i, name in enumerate(normalized) if name in {norm(a) for a in aliases}]
        if len(hits) == 1:
            out[role] = hits[0]
    return normalized, out


def parse_ts_ms(text: str) -> int:
    s = text.strip()
    try:
        v = int(s)
        av = abs(v)
        if av >= 10**17:  # ns
            return v // 1_000_000
        if av >= 10**14:  # us
            return v // 1_000
        if av >= 10**11:  # ms
            return v
        if av >= 10**9:   # seconds
            return v * 1000
    except Exception:
        pass
    z = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(z)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def positive_decimal(text: str):
    x = Decimal(text.strip())
    if not x.is_finite() or x <= 0:
        raise ValueError("non-positive/non-finite decimal")
    return x


def inspect_archive(path: Path, date_text: str) -> dict:
    day_start = int(datetime.fromisoformat(date_text).replace(tzinfo=timezone.utc).timestamp() * 1000)
    day_end = day_start + 86_400_000
    expected_csv = f"BTC-USDT-SWAP-trades-{date_text}.csv"
    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure: {bad}")
        members = [x for x in zf.infolist() if not x.is_dir()]
        if len(members) != 1:
            return {"status": "SCHEMA_REVIEW", "reason": f"member_count={len(members)}", "members": [x.filename for x in members]}
        info = members[0]
        if info.file_size > MAX_UNCOMPRESSED_MEMBER_BYTES:
            raise RuntimeError("uncompressed member cap exceeded")
        if Path(info.filename).name != expected_csv:
            return {"status": "SCHEMA_REVIEW", "reason": "unexpected_member_name", "member": info.filename}

        with zf.open(info, "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            try:
                header = next(reader)
            except StopIteration:
                return {"status": "SCHEMA_REVIEW", "reason": "empty_csv", "member": info.filename}
            normalized, cols = resolve_columns(header)
            required = {"timestamp", "price", "size", "side"}
            if not required.issubset(cols):
                sample = []
                for _ in range(5):
                    try:
                        sample.append(next(reader))
                    except StopIteration:
                        break
                return {
                    "status": "SCHEMA_REVIEW",
                    "reason": "required_columns_unresolved",
                    "member": info.filename,
                    "header": header,
                    "normalized_header": normalized,
                    "resolved_columns": cols,
                    "sample_rows": sample,
                }

            rows = invalid = out_of_day = backwards = 0
            first_ts = last_ts = prev_ts = None
            minute_buckets = set()
            sides = {}
            trade_id_backwards_or_dup = 0
            prev_trade_id = None
            instrument_mismatch = 0

            for row in reader:
                if not row:
                    continue
                try:
                    ts = parse_ts_ms(row[cols["timestamp"]])
                    positive_decimal(row[cols["price"]])
                    positive_decimal(row[cols["size"]])
                    side = row[cols["side"]].strip().lower()
                    if side not in {"buy", "sell"}:
                        raise ValueError("unexpected side")
                    if "instrument" in cols and row[cols["instrument"]].strip() != "BTC-USDT-SWAP":
                        instrument_mismatch += 1
                    tid = None
                    if "trade_id" in cols:
                        raw_tid = row[cols["trade_id"]].strip()
                        if raw_tid:
                            try:
                                tid = int(raw_tid)
                            except Exception:
                                tid = None
                except Exception:
                    invalid += 1
                    continue

                rows += 1
                sides[side] = sides.get(side, 0) + 1
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
                if not (day_start <= ts < day_end):
                    out_of_day += 1
                else:
                    minute_buckets.add((ts - day_start) // 60_000)
                if prev_ts is not None and ts < prev_ts:
                    backwards += 1
                prev_ts = ts
                if tid is not None:
                    if prev_trade_id is not None and tid <= prev_trade_id:
                        trade_id_backwards_or_dup += 1
                    prev_trade_id = tid

        gates = {
            "rows_positive": rows > 0,
            "invalid_rows_zero": invalid == 0,
            "timestamps_monotonic_nondecreasing": backwards == 0,
            "all_rows_inside_target_utc_day": out_of_day == 0,
            "buy_and_sell_observed": sides.get("buy", 0) > 0 and sides.get("sell", 0) > 0,
            "instrument_mismatch_zero": instrument_mismatch == 0,
        }
        status = "PASS" if all(gates.values()) else "REVIEW"
        return {
            "status": status,
            "member": info.filename,
            "compressed_size": info.compress_size,
            "uncompressed_size": info.file_size,
            "header": header,
            "normalized_header": normalized,
            "resolved_columns": cols,
            "rows": rows,
            "invalid_rows": invalid,
            "out_of_day_rows": out_of_day,
            "timestamp_backwards": backwards,
            "first_ts": first_ts,
            "last_ts": last_ts,
            "minute_buckets_observed": len(minute_buckets),
            "side_counts": sides,
            "trade_id_backwards_or_duplicate_diagnostic": trade_id_backwards_or_dup,
            "instrument_mismatch": instrument_mismatch,
            "gates": gates,
        }


def load_parent():
    if not PARENT_REPORT.exists():
        raise RuntimeError(f"missing Q005R parent report: {PARENT_REPORT}")
    obj = json.loads(PARENT_REPORT.read_text(encoding="utf-8"))
    if obj.get("stage") != PARENT_STAGE or obj.get("overall_status") != "PASS":
        raise RuntimeError("Q005R parent is not PASS")
    if obj.get("archive_bodies_downloaded") is not False or obj.get("strategy_features_calculated") is not False or obj.get("strategy_pnl_calculated") is not False:
        raise RuntimeError("Q005R firewall mismatch")
    rows = obj.get("dates") or []
    by_date = {x.get("date"): x for x in rows}
    if set(by_date) != set(EXPECTED_DATES):
        raise RuntimeError("Q005R date set mismatch")
    if sum(int(by_date[d]["head"]["content_length"]) for d in EXPECTED_DATES) != EXPECTED_TOTAL_COMPRESSED_BYTES:
        raise RuntimeError("Q005R total bytes mismatch")
    return by_date


def write_outputs(report):
    atomic_json(REPORT, report)
    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "overall_status": report.get("overall_status"),
        "strategy_features_calculated": False,
        "strategy_pnl_calculated": False,
        "files": [],
    }
    for row in report.get("days", []):
        manifest["files"].append({
            "date": row["date"], "filename": row["filename"], "bytes": row["archive"]["bytes"],
            "sha256": row["archive"]["sha256"], "status": row["status"],
            "rows": (row.get("schema") or {}).get("rows"),
            "header": (row.get("schema") or {}).get("header"),
        })
    atomic_json(MANIFEST, manifest)
    lines = [
        "# SC001-DATA-Q006 — OKX Q1 trade acquisition/schema qualification", "",
        f"- Overall: `{report.get('overall_status')}`",
        "- Strategy features/P&L: **NO**",
        "- Validation/Final: **NO**",
        f"- Network bytes read: {report.get('network_bytes_read', 0)}", "", "## Days",
    ]
    for row in report.get("days", []):
        s = row.get("schema") or {}
        lines.append(f"- {row['date']}: **{row['status']}**; rows={s.get('rows')}; minutes={s.get('minute_buckets_observed')}; invalid={s.get('invalid_rows')}; out_of_day={s.get('out_of_day_rows')}; backwards={s.get('timestamp_backwards')}; header={s.get('header')}")
    lines += ["", "## Boundary", "Data/schema qualification only. No TFI, no response labels, no P&L, no 2024-Q2 OKX, no formal Validation/Final."]
    atomic_text(SUMMARY, "\n".join(lines) + "\n")
    atomic_json(SAFETY, {
        "stage": STAGE, "network_bytes_read": report.get("network_bytes_read", 0),
        "workspace_bytes_after_outputs": dir_size(WORKSPACE), "free_bytes_after_outputs": free_bytes(),
        "caps": {"session_download": SESSION_DOWNLOAD_CAP_BYTES, "workspace": WORKSPACE_CAP_BYTES, "per_file": PER_FILE_CAP_BYTES, "reserve": MIN_FREE_RESERVE_BYTES},
        "strategy_features_calculated": False, "strategy_pnl_calculated": False,
    })


def main():
    global network_bytes_read
    WORKSPACE.mkdir(parents=True, exist_ok=True); ARCHIVES.mkdir(parents=True, exist_ok=True)
    safety_check()
    parent = load_parent()
    report = {
        "stage": STAGE, "version": VERSION, "started_at_utc": now_iso(),
        "scope": {"venue": "OKX", "instrument": "BTC-USDT-SWAP", "dates": list(EXPECTED_DATES), "expected_compressed_bytes": EXPECTED_TOTAL_COMPRESSED_BYTES, "split": "SAME_VENUE_Q1_DATA_ONLY"},
        "strategy_features_calculated": False, "future_returns_calculated": False, "strategy_pnl_calculated": False,
        "q2_okx_accessed": False, "validation_or_final_accessed": False, "days": [],
    }
    try:
        for date_text in EXPECTED_DATES:
            src = parent[date_text]
            filename = src["filename"]
            url = src["url"]
            expected_bytes = int(src["head"]["content_length"])
            print(f"[{date_text}] HEAD...")
            live = head_remote(url, filename)
            if live.get("status") != "PASS" or live.get("content_length") != expected_bytes:
                raise RuntimeError(f"Q006 live identity/size mismatch: {date_text}")
            print(f"[{date_text}] download/reuse...")
            archive = download_archive(url, ARCHIVES / filename, expected_bytes)
            print(f"[{date_text}] schema/integrity...")
            schema = inspect_archive(ARCHIVES / filename, date_text)
            status = "PASS" if schema.get("status") == "PASS" else schema.get("status", "REVIEW")
            report["days"].append({"date": date_text, "filename": filename, "url": url, "expected_bytes": expected_bytes, "live_head": live, "archive": archive, "schema": schema, "status": status})
            report["network_bytes_read"] = network_bytes_read
            write_outputs(report); safety_check()
        statuses = [x["status"] for x in report["days"]]
        report["overall_status"] = "PASS" if statuses == ["PASS"] * len(EXPECTED_DATES) else ("SCHEMA_REVIEW" if "SCHEMA_REVIEW" in statuses else "REVIEW")
        report["days_total"] = len(report["days"])
        report["days_passed"] = sum(1 for x in report["days"] if x["status"] == "PASS")
        report["network_bytes_read"] = network_bytes_read
        report["finished_at_utc"] = now_iso()
        write_outputs(report)
        print(f"COMPLETE: {report['overall_status']} {report['days_passed']}/{report['days_total']} | network={network_bytes_read} | FEATURES=NO | P&L=NO")
    except Exception as exc:
        report["overall_status"] = "ERROR"; report["error"] = repr(exc); report["network_bytes_read"] = network_bytes_read; report["finished_at_utc"] = now_iso(); write_outputs(report); raise


if __name__ == "__main__":
    main()
