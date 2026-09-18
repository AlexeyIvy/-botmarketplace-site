from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C7-D0-MULTI-ASSET-L2-METADATA-PREFLIGHT-V0.1"
PASS = "C7_D0_MULTI_ASSET_L2_METADATA_PASS"
REVIEW = "C7_D0_MULTI_ASSET_L2_METADATA_REVIEW"

FIXED_DATE = "2024-02-12"
DAY_START_MS = 1707696000000
DAY_END_MS = 1707782400000

INSTS = (
    "ETH-USDT-SWAP",
    "DOGE-USDT-SWAP",
    "ORDI-USDT-SWAP",
    "UNI-USDT-SWAP",
    "XRP-USDT-SWAP",
    "OP-USDT-SWAP",
    "BCH-USDT-SWAP",
)

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
DISCOVERY_PATH = "/priapi/v5/broker/public/trade-data/download-link"
REFERER = "https://www.okx.com/historical-data"
ALLOWED_STATIC_PREFIX = "static.okx."
TIMEOUT = 60
RETRIES = 3
MAX_RESPONSE_BYTES = 4_000_000

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c7-d0-multi-asset-l2-metadata-preflight-v0.1.md"
FREEZE = ROOT / "docs/research/sc001-c7-d0-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_C7_D0_MULTI_ASSET_L2_METADATA"
OUT = OUT_DIR / "sc001_c7_d0_multi_asset_l2_metadata_report_v0_1.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        text=True,
    ).strip()


def require_freeze() -> None:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_C7_D0_RUN":
        fail("C7-D0 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C7-D0 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C7-D0 protocol identity mismatch")
    if tuple(fr.get("universe") or ()) != INSTS:
        fail("C7-D0 universe mismatch")
    if fr.get("fixed_date") != FIXED_DATE:
        fail("C7-D0 fixed date mismatch")
    for k in (
        "historical_l2_body_authorized",
        "spread_authorized",
        "top_of_book_depth_authorized",
        "maker_order_simulation_authorized",
        "fill_model_authorized",
        "queue_model_authorized",
        "adverse_selection_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C7-D0 firewall mismatch: {k}")


def trusted_static(url: str, expected_basename: str) -> bool:
    try:
        p = urllib.parse.urlparse(url)
        return (
            p.scheme == "https"
            and (p.hostname or "").lower().startswith(ALLOWED_STATIC_PREFIX)
            and Path(p.path).name == expected_basename
        )
    except Exception:
        return False


def walk_nodes(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk_nodes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_nodes(v)


def get_json(url: str, label: str) -> dict:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C7-D0/0.1",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_RESPONSE_BYTES + 1)
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
            if len(raw) > MAX_RESPONSE_BYTES:
                fail(f"{label} response cap exceeded")
            if status != 200:
                fail(f"{label} HTTP {status}")
            p = urllib.parse.urlparse(final)
            if p.scheme != "https" or (p.hostname or "").lower() not in {
                "www.okx.com", "us.okx.com"
            }:
                fail(f"{label} unexpected final host: {p.hostname}")
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                fail(f"{label} OKX code mismatch")
            return obj
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} request failed: {type(last).__name__}: {last}")


def instrument_meta(inst: str) -> dict:
    q = urllib.parse.urlencode({"instType": "SWAP", "instId": inst})
    last = None
    for domain in OKX_DOMAINS:
        try:
            obj = get_json(domain + "/api/v5/public/instruments?" + q, f"{inst} instrument")
            rows = obj.get("data") or []
            if len(rows) != 1 or not isinstance(rows[0], dict):
                fail(f"{inst} instrument row count={len(rows)}")
            r = rows[0]
            checks = {
                "inst_exact": r.get("instId") == inst,
                "inst_type_swap": r.get("instType") == "SWAP",
                "ct_type_linear": r.get("ctType") == "linear",
                "settle_usdt": r.get("settleCcy") == "USDT",
                "state_live": r.get("state") == "live",
                "uly_present": isinstance(r.get("uly"), str) and bool(r.get("uly")),
            }
            return {
                "pass": all(checks.values()),
                "checks": checks,
                "uly": r.get("uly"),
                "tickSz": r.get("tickSz"),
                "lotSz": r.get("lotSz"),
                "ctVal": r.get("ctVal"),
                "ctValCcy": r.get("ctValCcy"),
            }
        except Exception as exc:
            last = exc
            continue
    raise RuntimeError(f"{inst} instrument failed: {type(last).__name__}: {last}")


def resolve_l2(inst: str, uly: str) -> tuple[str, str]:
    expected = f"{inst}-L2orderbook-400lv-{FIXED_DATE}.tar.gz"
    payload = {
        "module": "4",
        "instType": "SWAP",
        "instQueryParam": {"instFamilyList": [uly]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(DAY_START_MS),
            "end": str(DAY_END_MS - 1),
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    last = None
    for domain in OKX_DOMAINS:
        url = domain + DISCOVERY_PATH + "?t=" + str(int(time.time() * 1000))
        try:
            req = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C7-D0/0.1",
                    "Accept": "application/json,*/*",
                    "Content-Type": "application/json",
                    "Referer": REFERER,
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_RESPONSE_BYTES + 1)
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()

            if len(raw) > MAX_RESPONSE_BYTES:
                fail(f"{inst} metadata response cap exceeded")
            if status != 200:
                fail(f"{inst} metadata HTTP {status}")
            p = urllib.parse.urlparse(final)
            if p.scheme != "https" or (p.hostname or "").lower() not in {
                "www.okx.com", "us.okx.com"
            }:
                fail(f"{inst} metadata unexpected host: {p.hostname}")

            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                fail(f"{inst} metadata code mismatch")

            found = []
            for node in walk_nodes(obj.get("data")):
                if not isinstance(node, dict):
                    continue
                fn = node.get("filename") or node.get("fileName")
                u = node.get("url")
                if (
                    fn == expected
                    and isinstance(u, str)
                    and trusted_static(u, expected)
                    and u not in found
                ):
                    found.append(u)

            if len(found) == 1:
                return expected, found[0]
            if len(found) > 1:
                fail(f"{inst} multiple exact trusted L2 URLs")

            last = RuntimeError(f"{inst} exact L2 file not found")
        except Exception as exc:
            last = exc
            continue

    raise RuntimeError(f"{inst} L2 resolution failed: {type(last).__name__}: {last}")


def head_size(url: str, expected_basename: str) -> int:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C7-D0/0.1",
                    "Referer": REFERER,
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                cl = resp.headers.get("Content-Length")
            if status != 200:
                fail(f"HEAD HTTP {status}: {expected_basename}")
            if not trusted_static(final, expected_basename):
                fail(f"HEAD identity mismatch: {expected_basename}")
            if not cl or not cl.isdigit() or int(cl) <= 0:
                fail(f"invalid Content-Length: {expected_basename}")
            return int(cl)
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(
        f"HEAD failed {expected_basename}: {type(last).__name__}: {last}"
    )


def main() -> int:
    try:
        require_freeze()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        assets = {}
        all_pass = True
        combined = 0

        for i, inst in enumerate(INSTS, start=1):
            print(f"C7-D0 [{i}/7] {inst}", flush=True)
            try:
                meta = instrument_meta(inst)
                if meta.get("pass") is not True:
                    fail(f"{inst} current instrument semantics REVIEW")
                uly = str(meta["uly"])

                print(f"{inst}: resolve exact 400lv L2 metadata", flush=True)
                filename, url = resolve_l2(inst, uly)
                size = head_size(url, filename)
                combined += size

                assets[inst] = {
                    "pass": True,
                    "instrument": meta,
                    "historical_l2": {
                        "filename": filename,
                        "content_length": size,
                        "trusted_host": urllib.parse.urlparse(url).hostname,
                    },
                }
                print(
                    f"PASS {inst} l2_bytes={size} filename={filename}",
                    flush=True,
                )
            except Exception as exc:
                all_pass = False
                assets[inst] = {
                    "pass": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print(
                    f"REVIEW {inst}: {type(exc).__name__}: {exc}",
                    flush=True,
                )

        status = PASS if all_pass and len(assets) == len(INSTS) else REVIEW

        report = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "fixed_date": FIXED_DATE,
            "universe": list(INSTS),
            "assets": assets,
            "assets_passed": sum(1 for x in assets.values() if x.get("pass") is True),
            "combined_head_content_length": combined,
            "historical_l2_body_downloaded": False,
            "historical_l2_body_opened": False,
            "spread_calculated": False,
            "top_of_book_depth_calculated": False,
            "maker_order_simulated": False,
            "fill_model_calculated": False,
            "queue_model_calculated": False,
            "adverse_selection_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, report)

        print(status)
        print("assets_passed =", report["assets_passed"], "/", len(INSTS))
        print("combined_HEAD_content_length =", combined)
        print("historical L2 body downloaded/opened = False / False")
        print("spread/depth/maker/fill/queue/adverse-selection/PnL = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)
        return 0 if status == PASS else 2

    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "version": "0.1",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "historical_l2_body_downloaded": False,
            "historical_l2_body_opened": False,
            "spread_calculated": False,
            "top_of_book_depth_calculated": False,
            "maker_order_simulated": False,
            "fill_model_calculated": False,
            "queue_model_calculated": False,
            "adverse_selection_calculated": False,
            "pnl_calculated": False,
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
