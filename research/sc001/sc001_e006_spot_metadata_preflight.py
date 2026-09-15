"""SC001-E006 full-label BTC-USDT SPOT metadata-only preflight.

NO MARKET-DATA BODY DOWNLOAD.
NO BASIS / RETURNS / PNL / L2 / Q2 / VALIDATION / FINAL.

Checks exact public historical trade archive identities and HEAD sizes for
2024-03-01..2024-03-21. March 21 is boundary-neighbor only.
"""
from __future__ import annotations

import json
import os
import shutil
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE = "SC001-E006-SPOT-METADATA-PREFLIGHT"
VERSION = "0.1"
ENDPOINT = "/api/v5/public/market-data-history"
DOMAINS = ("https://www.okx.com", "https://us.okx.com")
TARGET_INST = "BTC-USDT"
MODULE = "1"
INST_TYPE = "SPOT"
DATE_AGGR = "daily"
ALLOWED_HOST = "static.okx.com"
TIMEOUT = 45
RETRIES = 3
MAX_RESPONSE_BYTES = 4_000_000
MIN_FREE_RESERVE_BYTES = 20 * 1024**3

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_E006_SPOT_FEASIBILITY"
OUT_JSON = OUT_DIR / "sc001_e006_spot_metadata_preflight.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def iter_days(start: str, end: str):
    d = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    e = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    while d <= e:
        yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)


def shift_day(day: str, delta: int) -> str:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=delta)
    return d.strftime("%Y-%m-%d")


def day_bounds_ms(day: str) -> tuple[int, int]:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    return lo, lo + 86_400_000


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def request_metadata(domain: str, query_day: str) -> dict:
    lo, hi = day_bounds_ms(query_day)
    params = {
        "module": MODULE,
        "instType": INST_TYPE,
        "dateAggrType": DATE_AGGR,
        "begin": str(lo),
        "end": str(hi),
        "instIdList": TARGET_INST,
    }
    url = domain + ENDPOINT + "?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "User-Agent": "BotMarketplace-SC001-E006-MetadataPreflight/0.1",
                    "Accept": "application/json,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_RESPONSE_BYTES + 1)
                status = int(getattr(resp, "status", 200))
            if len(raw) > MAX_RESPONSE_BYTES:
                fail("metadata response cap exceeded")
            if status != 200:
                fail(f"metadata HTTP {status}")
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                fail(f"metadata API failure code={obj.get('code') if isinstance(obj, dict) else None}")
            return obj
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(1.0 * attempt)
    raise RuntimeError(f"metadata request failed for {query_day}: {type(last).__name__}: {last}")


def walk_nodes(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk_nodes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_nodes(v)


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


def exact_urls_from_obj(obj: dict, expected_filename: str) -> list[str]:
    found: list[str] = []
    for node in walk_nodes(obj.get("data")):
        if not isinstance(node, dict):
            continue
        fn = node.get("filename") or node.get("fileName")
        candidates = [node.get("url"), node.get("fileUrl"), node.get("downloadUrl")]
        for u in candidates:
            if isinstance(u, str) and trusted_url(u, expected_filename):
                if fn is None or fn == expected_filename:
                    if u not in found:
                        found.append(u)
    return found


def discover_exact(label_day: str, cache: dict[tuple[str, str], dict]) -> tuple[str, str]:
    expected = f"{TARGET_INST}-trades-{label_day}.zip"
    found: list[tuple[str, str]] = []
    for query_day in (label_day, shift_day(label_day, -1)):
        for domain in DOMAINS:
            key = (domain, query_day)
            if key not in cache:
                try:
                    cache[key] = request_metadata(domain, query_day)
                except Exception:
                    continue
            for u in exact_urls_from_obj(cache[key], expected):
                pair = (domain, u)
                if pair not in found:
                    found.append(pair)
        if found:
            break
    urls = []
    for domain, u in found:
        if u not in [x[1] for x in urls]:
            urls.append((domain, u))
    unique_urls = []
    for domain, u in found:
        if u not in [x[1] for x in unique_urls]:
            unique_urls.append((domain, u))
    if len(unique_urls) != 1:
        fail(f"archive {expected} not uniquely resolved: {len(unique_urls)} trusted URLs")
    return unique_urls[0]


def head_size(url: str, expected_filename: str) -> tuple[int, str]:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "BotMarketplace-SC001-E006-MetadataPreflight/0.1"},
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final_url = resp.geturl()
                cl = resp.headers.get("Content-Length")
            if status != 200:
                fail(f"HEAD HTTP {status} for {expected_filename}")
            if not trusted_url(final_url, expected_filename):
                fail(f"HEAD redirect identity mismatch for {expected_filename}")
            if not cl or not cl.isdigit() or int(cl) <= 0:
                fail(f"missing/invalid Content-Length for {expected_filename}")
            return int(cl), final_url
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(1.0 * attempt)
    raise RuntimeError(f"HEAD failed for {expected_filename}: {type(last).__name__}: {last}")


def main() -> int:
    labels = list(iter_days("2024-03-01", "2024-03-21"))
    cache: dict[tuple[str, str], dict] = {}
    rows = []
    errors = []
    total = 0

    for d in labels:
        expected = f"{TARGET_INST}-trades-{d}.zip"
        try:
            domain, url = discover_exact(d, cache)
            size, final_url = head_size(url, expected)
            total += size
            rows.append({
                "date_label": d,
                "filename": expected,
                "metadata_domain": domain,
                "host": urllib.parse.urlparse(final_url).hostname,
                "url": final_url,
                "expected_bytes": size,
                "boundary_neighbor_only": d == "2024-03-21",
            })
            print(f"META PASS {d} bytes={size}")
        except Exception as exc:
            errors.append(f"{d}: {type(exc).__name__}: {exc}")
            print(f"META REVIEW {d}: {exc}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    disk = shutil.disk_usage(OUT_DIR)
    disk_ok = disk.free >= total + MIN_FREE_RESERVE_BYTES
    if not disk_ok:
        errors.append("insufficient free disk for expected bodies plus 20 GiB reserve")

    status = "E006_SPOT_METADATA_PREFLIGHT_PASS" if len(rows) == len(labels) and not errors else "E006_SPOT_METADATA_PREFLIGHT_REVIEW"
    report = {
        "stage": STAGE,
        "version": VERSION,
        "status": status,
        "instrument": TARGET_INST,
        "inst_type": INST_TYPE,
        "module": MODULE,
        "required_archive_labels": labels,
        "discovery_performance_days": list(iter_days("2024-03-01", "2024-03-20")),
        "boundary_neighbor_label": "2024-03-21",
        "future_confirmation_candidate_days": list(iter_days("2024-03-22", "2024-03-30")),
        "archives": rows,
        "expected_total_bytes": total,
        "disk_free_bytes": disk.free,
        "required_free_bytes": total + MIN_FREE_RESERVE_BYTES,
        "disk_pass": disk_ok,
        "errors": errors,
        "market_data_body_downloaded": False,
        "basis_calculated": False,
        "returns_calculated": False,
        "pnl_calculated": False,
        "l2_accessed": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(OUT_JSON, report)

    print(status)
    print("archive_count =", len(rows))
    print("expected_total_bytes =", total)
    print("disk_free_bytes =", disk.free)
    print("disk_pass =", disk_ok)
    print("boundary_neighbor_label = 2024-03-21 (performance excluded)")
    print("market_data_body_downloaded = False")
    print("basis/returns/P&L calculated = False")
    print("L2/Q2/Validation/Final = CLOSED")
    print("report =", OUT_JSON)
    return 0 if status.endswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
