"""SC001-E006 data-only OKX BTC-USDT SPOT historical metadata probe.

NO ALPHA. NO BASIS. NO RETURNS. NO PNL. NO MARKET-DATA BODY DOWNLOAD.

Purpose: test whether the official/public OKX historical-market-data endpoint can
identify March-2024 BTC-USDT SPOT trade-history data reproducibly before any
E006 executable protocol is frozen.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-E006-SPOT-METADATA-PROBE"
VERSION = "0.1"
ENDPOINT = "/api/v5/public/market-data-history"
DOMAINS = ("https://www.okx.com", "https://us.okx.com")
TARGET_INST = "BTC-USDT"
TARGET_DAY = "2024-03-01"
MODULE = "1"  # trade history
INST_TYPE = "SPOT"
DATE_AGGR = "daily"
TIMEOUT = 30
MAX_RESPONSE_BYTES = 4_000_000

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_E006_SPOT_FEASIBILITY"
OUT_JSON = OUT_DIR / "sc001_e006_spot_metadata_probe.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def day_bounds_ms(day: str) -> tuple[int, int]:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    hi = lo + 86_400_000
    return lo, hi


def request_json(domain: str) -> dict:
    lo, hi = day_bounds_ms(TARGET_DAY)
    params = {
        "module": MODULE,
        "instType": INST_TYPE,
        "dateAggrType": DATE_AGGR,
        "begin": str(lo),
        "end": str(hi),
        "instIdList": TARGET_INST,
    }
    url = domain + ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "BotMarketplace-SC001-E006-MetadataProbe/0.1",
            "Accept": "application/json,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read(MAX_RESPONSE_BYTES + 1)
        final_url = resp.geturl()
        status = int(getattr(resp, "status", 200))
    if len(raw) > MAX_RESPONSE_BYTES:
        fail("metadata response exceeds cap")
    if status != 200:
        fail(f"HTTP status {status}")
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        fail("JSON object expected")
    return {"domain": domain, "final_url": final_url, "response": obj}


def collect_structure(node, path="root", out=None):
    if out is None:
        out = {"keys": set(), "urls": [], "zip_strings": [], "btc_strings": []}
    if isinstance(node, dict):
        for k, v in node.items():
            out["keys"].add(str(k))
            collect_structure(v, f"{path}.{k}", out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            collect_structure(v, f"{path}[{i}]", out)
    elif isinstance(node, str):
        s = node.strip()
        ls = s.lower()
        if ls.startswith("http://") or ls.startswith("https://"):
            parsed = urllib.parse.urlparse(s)
            out["urls"].append({"path": path, "host": parsed.hostname, "basename": Path(parsed.path).name})
        if ".zip" in ls:
            out["zip_strings"].append({"path": path, "value": Path(urllib.parse.urlparse(s).path).name if "://" in s else s})
        if "btc-usdt" in ls:
            out["btc_strings"].append({"path": path, "value": s[:300]})
    return out


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main() -> int:
    errors = []
    result = None
    for domain in DOMAINS:
        try:
            result = request_json(domain)
            if str(result["response"].get("code")) == "0":
                break
            errors.append(f"{domain}: code={result['response'].get('code')} msg={result['response'].get('msg')}")
            result = None
        except Exception as exc:
            errors.append(f"{domain}: {type(exc).__name__}: {exc}")

    if result is None:
        report = {
            "stage": STAGE,
            "version": VERSION,
            "status": "E006_SPOT_METADATA_PROBE_REVIEW",
            "target_day": TARGET_DAY,
            "instrument": TARGET_INST,
            "module": MODULE,
            "errors": errors,
            "market_data_body_downloaded": False,
            "basis_calculated": False,
            "returns_calculated": False,
            "pnl_calculated": False,
            "q2_accessed": False,
            "validation_or_final_accessed": False,
        }
        atomic_json(OUT_JSON, report)
        print("E006_SPOT_METADATA_PROBE_REVIEW")
        for e in errors:
            print("ERROR", e)
        print("alpha/basis/returns/P&L = NO")
        return 2

    obj = result["response"]
    st = collect_structure(obj)
    data = obj.get("data")
    data_count = len(data) if isinstance(data, list) else None

    report = {
        "stage": STAGE,
        "version": VERSION,
        "status": "E006_SPOT_METADATA_PROBE_PASS",
        "target_day": TARGET_DAY,
        "instrument": TARGET_INST,
        "module": MODULE,
        "inst_type": INST_TYPE,
        "date_aggregation": DATE_AGGR,
        "domain_used": result["domain"],
        "api_code": obj.get("code"),
        "api_msg": obj.get("msg"),
        "data_item_count": data_count,
        "observed_keys": sorted(st["keys"]),
        "url_descriptors": st["urls"],
        "zip_descriptors": st["zip_strings"],
        "btc_usdt_string_descriptors": st["btc_strings"],
        "market_data_body_downloaded": False,
        "basis_calculated": False,
        "returns_calculated": False,
        "pnl_calculated": False,
        "q2_accessed": False,
        "validation_or_final_accessed": False,
    }
    atomic_json(OUT_JSON, report)

    print("E006_SPOT_METADATA_PROBE_PASS")
    print("domain_used =", report["domain_used"])
    print("api_code =", report["api_code"])
    print("api_msg =", report["api_msg"])
    print("data_item_count =", report["data_item_count"])
    print("observed_keys =", ",".join(report["observed_keys"]))
    print("url_count =", len(report["url_descriptors"]))
    for x in report["url_descriptors"][:20]:
        print("URL", x["path"], "host=", x["host"], "basename=", x["basename"])
    print("zip_string_count =", len(report["zip_descriptors"]))
    for x in report["zip_descriptors"][:20]:
        print("ZIP", x["path"], x["value"])
    print("btc_usdt_string_count =", len(report["btc_usdt_string_descriptors"]))
    print("market_data_body_downloaded = False")
    print("basis/returns/P&L calculated = False")
    print("Q2/Validation/Final = CLOSED")
    print("report =", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
