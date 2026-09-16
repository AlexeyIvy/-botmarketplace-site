"""SC001 metadata-only historical universe enumeration probe.

Purpose: determine whether the official OKX historical-data metadata endpoint can
enumerate contemporaneous USDT-margined perpetual SWAP trade archives without
opening any market-data body.

NO trade/L2 body download. NO signal/PnL/strategy calculation.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

STAGE = "SC001-HISTORICAL-UNIVERSE-METADATA-PROBE"
VERSION = "0.1"
PASS = "SC001_HISTORICAL_UNIVERSE_METADATA_PROBE_PASS"
REVIEW = "SC001_HISTORICAL_UNIVERSE_METADATA_PROBE_REVIEW"

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
DISCOVERY_PATH = "/priapi/v5/broker/public/trade-data/download-link"
REFERER = "https://www.okx.com/historical-data"
UA = "BotMarketplace-SC001-UniverseProbe/0.1"
ALLOWED_HOST = "static.okx.com"
TIMEOUT = 90
RETRIES = 3
MAX_META_BYTES = 16_000_000

# Diagnostic metadata-only dates. They are not promotional dates and do not
# authorize any body access.
PROBE_DATES = ("2023-12-31", "2024-02-29", "2024-03-31")

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_HISTORICAL_UNIVERSE_METADATA_PROBE"
OUT_JSON = OUT_DIR / "sc001_historical_universe_metadata_probe_report.json"

TRADE_RE = re.compile(r"^(?P<inst>.+-USDT-SWAP)-trades-(?P<date>\d{4}-\d{2}-\d{2})\.zip$")


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def date_bounds(date_text: str) -> tuple[int, int]:
    d = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    hi = int((d + timedelta(days=1) - timedelta(milliseconds=1)).timestamp() * 1000)
    return lo, hi


def payload_variants(date_text: str) -> list[dict]:
    lo, hi = date_bounds(date_text)
    base = {
        "module": "1",
        "instType": "SWAP",
        "dateQuery": {"dateAggrType": "daily", "begin": str(lo), "end": str(hi)},
    }
    a = dict(base)
    a["instQueryParam"] = {"instFamilyList": []}
    b = dict(base)
    return [a, b]


def walk_file_nodes(node):
    if isinstance(node, dict):
        fn = node.get("filename") or node.get("fileName")
        url = node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
        if isinstance(fn, str):
            yield fn, url if isinstance(url, str) else None
        for v in node.values():
            yield from walk_file_nodes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_file_nodes(v)


def trusted_static_url(url: str | None) -> bool:
    if not isinstance(url, str) or not url.startswith("https://"):
        return False
    try:
        from urllib.parse import urlparse
        return (urlparse(url).hostname or "").lower() == ALLOWED_HOST
    except Exception:
        return False


def request_variant(domain: str, payload: dict) -> tuple[dict | None, str | None]:
    url = domain + DISCOVERY_PATH + "?t=" + str(int(time.time() * 1000))
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {
        "User-Agent": UA,
        "Accept": "application/json,*/*",
        "Content-Type": "application/json",
        "Referer": REFERER,
    }
    for attempt in range(1, RETRIES + 1):
        try:
            req = Request(url, data=body, method="POST", headers=headers)
            with urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_META_BYTES + 1)
            if len(raw) > MAX_META_BYTES:
                return None, "metadata_response_cap_exceeded"
            obj = json.loads(raw.decode("utf-8"))
            if isinstance(obj, dict) and obj.get("code") == "0":
                digest = hashlib.sha256(raw).hexdigest()
                return obj, digest
            return None, f"non_success_code:{obj.get('code') if isinstance(obj, dict) else 'not_dict'}"
        except HTTPError as exc:
            if exc.code == 429 and attempt < RETRIES:
                time.sleep(1.5 * attempt); continue
            return None, f"http:{exc.code}"
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            if attempt < RETRIES:
                time.sleep(1.5 * attempt); continue
            return None, f"{type(exc).__name__}:{exc}"
    return None, "unreachable"


def probe_date(date_text: str) -> dict:
    attempts = []
    found: dict[str, dict] = {}

    # Some historical-data responses associate a daily filename with the exact
    # query date, while prior SC001 acquisition sometimes needed the previous
    # query date to discover the exact file. Probe both but filter filenames to
    # the requested archive date.
    qdates = (date_text, (datetime.strptime(date_text, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d"))

    for qd in qdates:
        for variant_index, payload in enumerate(payload_variants(qd)):
            for domain in DOMAINS:
                obj, digest_or_error = request_variant(domain, payload)
                att = {
                    "query_date": qd,
                    "variant": variant_index,
                    "domain": domain,
                    "success": obj is not None,
                    "response_sha256_or_error": digest_or_error,
                }
                attempts.append(att)
                if obj is None:
                    continue
                for fn, url in walk_file_nodes(obj.get("data")):
                    m = TRADE_RE.match(fn)
                    if not m or m.group("date") != date_text:
                        continue
                    inst = m.group("inst")
                    row = found.setdefault(inst, {"instrument": inst, "filename": fn, "trusted_static_url_seen": False})
                    if trusted_static_url(url):
                        row["trusted_static_url_seen"] = True
                if found:
                    # One successful enumeration response is enough; retain all
                    # instruments from it and stop broadening this query date.
                    break
            if found:
                break
        if found:
            break

    instruments = sorted(found)
    return {
        "date": date_text,
        "status": "PASS" if len(instruments) >= 8 else "REVIEW",
        "instrument_count": len(instruments),
        "instruments": instruments,
        "files": [found[x] for x in instruments],
        "attempts": attempts,
    }


def main() -> int:
    rows = []
    for d in PROBE_DATES:
        print("UNIVERSE METADATA PROBE", d)
        r = probe_date(d)
        rows.append(r)
        print(d, r["status"], "USDT-SWAP instruments =", r["instrument_count"])
        if r["instruments"]:
            print("sample =", r["instruments"][:12])

    passed = all(r["status"] == "PASS" for r in rows)
    status = PASS if passed else REVIEW
    rep = {
        "stage": STAGE,
        "version": VERSION,
        "status": status,
        "probe_dates": list(PROBE_DATES),
        "rows": rows,
        "market_data_body_downloaded": False,
        "trade_rows_opened": False,
        "l2_rows_opened": False,
        "strategy_signal_calculated": False,
        "strategy_pnl_calculated": False,
        "instrument_performance_ranked": False,
        "promotional_universe_frozen": False,
        "confirmation_accessed": False,
        "q2_validation_final_accessed": False,
    }
    atomic_json(OUT_JSON, rep)

    print(status)
    print("market data body downloaded = False")
    print("strategy signal/PnL calculated = False")
    print("promotional universe frozen = False")
    print("report =", OUT_JSON)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
