"""SC001 C1 contaminated-date-only multi-asset SPOT metadata preflight v0.1.

DATA ENGINEERING ONLY.
NO MARKET-DATA BODY GET.
NO BASIS / RETURNS / PNL / SENTINEL OUTCOME / PROMOTIONAL ALPHA.

Whitelisted archive labels only:
  2024-06-30..2024-07-15
  2024-08-31..2024-09-15
for the eight already-contaminated C1 candidate assets.
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

STAGE = "SC001-C1-SPOT-SELECTION-METADATA-PREFLIGHT-V0.1"
PASS = "C1_SPOT_METADATA_PREFLIGHT_PASS"
REVIEW = "C1_SPOT_METADATA_PREFLIGHT_REVIEW"
ENDPOINT = "/api/v5/public/market-data-history"
DOMAINS = ("https://www.okx.com", "https://us.okx.com")
ASSETS = ("BTC", "ETH", "DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
INSTRUMENTS = tuple(f"{s}-USDT" for s in ASSETS)
MODULE = "1"
INST_TYPE = "SPOT"
DATE_AGGR = "daily"
ALLOWED_HOST = "static.okx.com"
TIMEOUT = 45
RETRIES = 3
MAX_RESPONSE_BYTES = 4_000_000
MIN_FREE_RESERVE_BYTES = 20 * 1024**3
MIN_COMPLETE_ASSETS = 4

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_C1_SPOT_SELECTION_CALIBRATION"
OUT_JSON = OUT_DIR / "sc001_c1_spot_metadata_preflight_v0_1.json"


def iter_days(start: str, end: str) -> list[str]:
    d = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    e = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    out: list[str] = []
    while d <= e:
        out.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return out


JULY_LABELS = tuple(iter_days("2024-06-30", "2024-07-15"))
SEPTEMBER_LABELS = tuple(iter_days("2024-08-31", "2024-09-15"))
ALLOWED_LABELS = JULY_LABELS + SEPTEMBER_LABELS
ALLOWED_LABEL_SET = set(ALLOWED_LABELS)
PERFORMANCE_LABELS = set(iter_days("2024-07-01", "2024-07-14") + iter_days("2024-09-01", "2024-09-14"))
BOUNDARY_LABELS = {"2024-06-30", "2024-07-15", "2024-08-31", "2024-09-15"}


def fail(msg: str) -> None:
    raise RuntimeError(msg)


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


def request_metadata(domain: str, query_day: str, inst_id: str) -> dict:
    if query_day not in ALLOWED_LABEL_SET:
        fail(f"metadata query date outside whitelist: {query_day}")
    if inst_id not in INSTRUMENTS:
        fail(f"instrument outside whitelist: {inst_id}")

    lo, hi = day_bounds_ms(query_day)
    params = {
        "module": MODULE,
        "instType": INST_TYPE,
        "dateAggrType": DATE_AGGR,
        "begin": str(lo),
        "end": str(hi),
        "instIdList": inst_id,
    }
    url = domain + ENDPOINT + "?" + urllib.parse.urlencode(params)
    last: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C1-SPOT-MetadataPreflight/0.1",
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
                code = obj.get("code") if isinstance(obj, dict) else None
                fail(f"metadata API failure code={code}")
            return obj
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"metadata request failed {inst_id} {query_day}: {type(last).__name__}: {last}")


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
        candidates = (node.get("url"), node.get("fileUrl"), node.get("downloadUrl"))
        for u in candidates:
            if isinstance(u, str) and trusted_url(u, expected_filename):
                if fn is None or fn == expected_filename:
                    if u not in found:
                        found.append(u)
    return found


def discovery_query_days(label_day: str) -> tuple[str, ...]:
    days = [label_day]
    prev = shift_day(label_day, -1)
    if prev in ALLOWED_LABEL_SET:
        days.append(prev)
    return tuple(days)


def discover_exact(
    inst_id: str,
    label_day: str,
    cache: dict[tuple[str, str, str], dict],
    queried_days: set[str],
) -> tuple[str, str, str]:
    if label_day not in ALLOWED_LABEL_SET:
        fail(f"archive label outside whitelist: {label_day}")
    expected = f"{inst_id}-trades-{label_day}.zip"
    found: list[tuple[str, str, str]] = []

    for query_day in discovery_query_days(label_day):
        for domain in DOMAINS:
            key = (domain, query_day, inst_id)
            queried_days.add(query_day)
            if key not in cache:
                try:
                    cache[key] = request_metadata(domain, query_day, inst_id)
                except Exception:
                    continue
            for u in exact_urls_from_obj(cache[key], expected):
                row = (domain, query_day, u)
                if row not in found:
                    found.append(row)
        if found:
            break

    unique_urls: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for domain, query_day, u in found:
        if u not in seen:
            seen.add(u)
            unique_urls.append((domain, query_day, u))

    if len(unique_urls) != 1:
        fail(f"archive {expected} not uniquely resolved: {len(unique_urls)} trusted URLs")
    return unique_urls[0]


def head_size(url: str, expected_filename: str) -> tuple[int, str]:
    last: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "BotMarketplace-SC001-C1-SPOT-MetadataPreflight/0.1"},
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
                time.sleep(float(attempt))
    raise RuntimeError(f"HEAD failed for {expected_filename}: {type(last).__name__}: {last}")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cache: dict[tuple[str, str, str], dict] = {}
    queried_days: set[str] = set()
    assets: dict[str, dict] = {}
    complete_assets: list[str] = []

    for inst_id in INSTRUMENTS:
        rows: list[dict] = []
        errors: list[str] = []
        total = 0
        print(f"=== {inst_id} ===", flush=True)

        for label_day in ALLOWED_LABELS:
            expected = f"{inst_id}-trades-{label_day}.zip"
            try:
                domain, query_day, url = discover_exact(inst_id, label_day, cache, queried_days)
                size, final_url = head_size(url, expected)
                total += size
                rows.append({
                    "date_label": label_day,
                    "role": "PERFORMANCE" if label_day in PERFORMANCE_LABELS else "BOUNDARY_SOURCE_ONLY",
                    "filename": expected,
                    "metadata_domain": domain,
                    "metadata_query_day": query_day,
                    "host": urllib.parse.urlparse(final_url).hostname,
                    "url": final_url,
                    "expected_bytes": size,
                })
                print(f"META PASS {inst_id} {label_day} bytes={size}", flush=True)
            except Exception as exc:
                msg = f"{label_day}: {type(exc).__name__}: {exc}"
                errors.append(msg)
                print(f"META REVIEW {inst_id} {label_day}: {exc}", flush=True)

        complete = len(rows) == len(ALLOWED_LABELS) and not errors
        if complete:
            complete_assets.append(inst_id)
        assets[inst_id] = {
            "state": "COMPLETE_METADATA" if complete else "PARTIAL_OR_UNAVAILABLE",
            "resolved_archive_count": len(rows),
            "required_archive_count": len(ALLOWED_LABELS),
            "expected_total_bytes": total,
            "archives": rows,
            "errors": errors,
        }
        print(
            f"ASSET SUMMARY {inst_id}: state={assets[inst_id]['state']} "
            f"archives={len(rows)}/{len(ALLOWED_LABELS)} bytes={total}",
            flush=True,
        )

    if not queried_days.issubset(ALLOWED_LABEL_SET):
        fail(f"internal firewall error: queried non-whitelisted metadata dates {sorted(queried_days - ALLOWED_LABEL_SET)}")

    expected_complete_bytes = sum(int(assets[x]["expected_total_bytes"]) for x in complete_assets)
    disk = shutil.disk_usage(OUT_DIR)
    required_free = expected_complete_bytes + MIN_FREE_RESERVE_BYTES
    disk_ok = len(complete_assets) >= MIN_COMPLETE_ASSETS and disk.free >= required_free
    enough_assets = len(complete_assets) >= MIN_COMPLETE_ASSETS
    status = PASS if enough_assets and disk_ok else REVIEW

    report = {
        "stage": STAGE,
        "version": "0.1",
        "status": status,
        "venue": "OKX",
        "inst_type": INST_TYPE,
        "module": MODULE,
        "candidate_instruments": list(INSTRUMENTS),
        "permitted_archive_labels": list(ALLOWED_LABELS),
        "performance_labels": sorted(PERFORMANCE_LABELS),
        "boundary_source_only_labels": sorted(BOUNDARY_LABELS),
        "metadata_query_days_observed": sorted(queried_days),
        "metadata_query_days_all_whitelisted": queried_days.issubset(ALLOWED_LABEL_SET),
        "assets": assets,
        "complete_assets": complete_assets,
        "complete_asset_count": len(complete_assets),
        "minimum_complete_assets_required": MIN_COMPLETE_ASSETS,
        "expected_complete_asset_body_bytes": expected_complete_bytes,
        "disk_free_bytes": disk.free,
        "required_free_bytes_with_20gib_reserve": required_free,
        "disk_pass": disk_ok,
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
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(OUT_JSON, report)

    print(status)
    print("complete_assets =", ",".join(complete_assets) if complete_assets else "NONE")
    print("complete_asset_count =", len(complete_assets))
    print("expected_complete_asset_body_bytes =", expected_complete_bytes)
    print("disk_free_bytes =", disk.free)
    print("disk_pass =", disk_ok)
    print("metadata_query_days_all_whitelisted = True")
    print("market_data_body_downloaded = False")
    print("strategy signal / sentinel outcome / basis / returns / PnL = False")
    print("promotional alpha accessed = False")
    print("report =", OUT_JSON)
    return 0 if status == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
