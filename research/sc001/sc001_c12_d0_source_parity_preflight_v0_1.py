from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C12-D0-SOURCE-PARITY-PREFLIGHT-V0.1"
PASS = "C12_D0_SOURCE_PARITY_PREFLIGHT_PASS"
REVIEW = "C12_D0_SOURCE_PARITY_PREFLIGHT_REVIEW"

INST = "USDC-USDT"
FIXED_DATE = "2025-01-15"
BEGIN_MS = 1736899200000
END_MS = 1736985600000
EXPECTED_ARCHIVE = "USDC-USDT-trades-2025-01-15.zip"

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
STATIC_HOST = "static.okx.com"
CIRCLE_URL = "https://www.circle.com/usdc"

TIMEOUT = 60
RETRIES = 3
MAX_JSON_BYTES = 4_000_000

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c12-d0-source-parity-preflight-protocol-v0.1.md"
FREEZE = ROOT / "docs/research/sc001-c12-d0-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_C12_D0_SOURCE_PARITY"
OUT = OUT_DIR / "sc001_c12_d0_source_parity_report_v0_1.json"


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
    if fr.get("status") != "FROZEN_BEFORE_C12_D0_RUN":
        fail("C12-D0 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C12-D0 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C12-D0 protocol identity mismatch")
    if fr.get("fixed_date") != FIXED_DATE:
        fail("C12-D0 fixed date mismatch")
    for k in (
        "historical_trade_body_authorized",
        "peg_deviation_authorized",
        "reversion_outcome_authorized",
        "threshold_selection_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C12-D0 firewall mismatch: {k}")


def request_json(req: urllib.request.Request, label: str) -> tuple[dict, str]:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                raw = resp.read(MAX_JSON_BYTES + 1)
            if status != 200:
                fail(f"{label} HTTP {status}")
            if len(raw) > MAX_JSON_BYTES:
                fail(f"{label} response cap exceeded")
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict):
                fail(f"{label} JSON object expected")
            return obj, final
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} failed: {type(last).__name__}: {last}")


def verify_instrument() -> dict:
    q = urllib.parse.urlencode({"instType": "SPOT", "instId": INST})
    last = None
    for domain in OKX_DOMAINS:
        try:
            req = urllib.request.Request(
                domain + "/api/v5/public/instruments?" + q,
                method="GET",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C12-D0/0.1",
                    "Accept": "application/json",
                },
            )
            obj, final = request_json(req, "USDC-USDT instrument")
            host = (urllib.parse.urlparse(final).hostname or "").lower()
            if host not in {"www.okx.com", "us.okx.com"}:
                fail(f"unexpected instrument host: {host}")
            if str(obj.get("code")) != "0":
                fail(f"instrument code mismatch: {obj.get('code')}")
            rows = obj.get("data") or []
            if len(rows) != 1 or not isinstance(rows[0], dict):
                fail(f"instrument row count={len(rows)}")
            r = rows[0]
            checks = {
                "inst_exact": r.get("instId") == INST,
                "inst_type": r.get("instType") == "SPOT",
                "base_usdc": r.get("baseCcy") == "USDC",
                "quote_usdt": r.get("quoteCcy") == "USDT",
                "live": r.get("state") == "live",
            }
            if not all(checks.values()):
                fail(f"instrument semantics mismatch: {checks}")
            return {"pass": True, "checks": checks, "tickSz": r.get("tickSz"), "lotSz": r.get("lotSz")}
        except Exception as exc:
            last = exc
    raise RuntimeError(f"instrument verification failed: {type(last).__name__}: {last}")


def verify_circle_head() -> dict:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                CIRCLE_URL,
                method="HEAD",
                headers={"User-Agent": "BotMarketplace-SC001-C12-D0/0.1"},
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
            host = (urllib.parse.urlparse(final).hostname or "").lower()
            if status != 200:
                fail(f"Circle HEAD HTTP {status}")
            if host not in {"circle.com", "www.circle.com"}:
                fail(f"unexpected Circle host: {host}")
            return {"pass": True, "final_host": host, "url": CIRCLE_URL}
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"Circle HEAD failed: {type(last).__name__}: {last}")


def walk_nodes(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk_nodes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_nodes(v)


def trusted_archive(url: str) -> bool:
    p = urllib.parse.urlparse(url)
    return (
        p.scheme == "https"
        and (p.hostname or "").lower() == STATIC_HOST
        and Path(p.path).name == EXPECTED_ARCHIVE
    )


def extract_exact(obj: dict) -> list[str]:
    found = []
    for node in walk_nodes(obj.get("data")):
        if not isinstance(node, dict):
            continue
        fn = node.get("filename") or node.get("fileName")
        for key in ("url", "fileUrl", "downloadUrl"):
            u = node.get(key)
            if (
                fn == EXPECTED_ARCHIVE
                and isinstance(u, str)
                and trusted_archive(u)
                and u not in found
            ):
                found.append(u)
    return found


def resolver_a_priapi() -> str | None:
    payload = {
        "module": "1",
        "instType": "SPOT",
        "instQueryParam": {"instIdList": [INST]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(BEGIN_MS),
            "end": str(END_MS - 1),
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    for domain in OKX_DOMAINS:
        try:
            req = urllib.request.Request(
                domain + "/priapi/v5/broker/public/trade-data/download-link?t=" + str(int(time.time()*1000)),
                data=body,
                method="POST",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C12-D0/0.1",
                    "Accept": "application/json,*/*",
                    "Content-Type": "application/json",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )
            obj, final = request_json(req, "C12 priapi resolver")
            host = (urllib.parse.urlparse(final).hostname or "").lower()
            if host not in {"www.okx.com", "us.okx.com"}:
                continue
            if str(obj.get("code")) != "0":
                continue
            found = extract_exact(obj)
            if len(found) == 1:
                return found[0]
            if len(found) > 1:
                fail("multiple exact C12 priapi archive URLs")
        except Exception:
            continue
    return None


def resolver_b_public() -> str | None:
    params = {
        "module": "1",
        "instType": "SPOT",
        "dateAggrType": "daily",
        "begin": str(BEGIN_MS),
        "end": str(END_MS),
        "instIdList": INST,
    }
    q = urllib.parse.urlencode(params)

    for domain in OKX_DOMAINS:
        try:
            req = urllib.request.Request(
                domain + "/api/v5/public/market-data-history?" + q,
                method="GET",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C12-D0/0.1",
                    "Accept": "application/json",
                },
            )
            obj, final = request_json(req, "C12 public resolver")
            host = (urllib.parse.urlparse(final).hostname or "").lower()
            if host not in {"www.okx.com", "us.okx.com"}:
                continue
            if str(obj.get("code")) != "0":
                continue
            found = extract_exact(obj)
            if len(found) == 1:
                return found[0]
            if len(found) > 1:
                fail("multiple exact C12 public archive URLs")
        except Exception:
            continue
    return None


def head_archive(url: str) -> int:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C12-D0/0.1",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                cl = resp.headers.get("Content-Length")
            if status != 200:
                fail(f"archive HEAD HTTP {status}")
            if not trusted_archive(final):
                fail("archive HEAD identity mismatch")
            if not cl or not cl.isdigit() or int(cl) <= 0:
                fail("archive invalid Content-Length")
            return int(cl)
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"archive HEAD failed: {type(last).__name__}: {last}")


def main() -> int:
    try:
        require_freeze()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        print("C12-D0 verify current USDC-USDT spot instrument", flush=True)
        inst = verify_instrument()

        print("C12-D0 verify Circle parity-source availability", flush=True)
        circle = verify_circle_head()

        print("C12-D0 resolve exact historical spot trade archive", flush=True)
        url = resolver_a_priapi()
        resolver = "PRIAPI_INST_ID_LIST"
        if url is None:
            url = resolver_b_public()
            resolver = "PUBLIC_MARKET_DATA_HISTORY"
        if url is None:
            fail("exact historical USDC-USDT archive unresolved by both frozen metadata resolvers")

        size = head_archive(url)

        report = {
            "stage": STAGE,
            "version": "0.1",
            "status": PASS,
            "fixed_date": FIXED_DATE,
            "instrument": inst,
            "parity_source": circle,
            "historical_archive": {
                "filename": EXPECTED_ARCHIVE,
                "content_length": size,
                "host": urllib.parse.urlparse(url).hostname,
                "resolver": resolver,
            },
            "historical_trade_body_downloaded": False,
            "historical_trade_body_opened": False,
            "peg_deviation_calculated": False,
            "reversion_outcome_calculated": False,
            "threshold_selected": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, report)

        print(PASS)
        print("instrument = USDC-USDT SPOT LIVE")
        print("archive =", EXPECTED_ARCHIVE, "bytes =", size, "resolver =", resolver)
        print("historical trade body downloaded/opened = False / False")
        print("peg deviation/reversion/threshold/PnL = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)
        return 0

    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "version": "0.1",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "historical_trade_body_downloaded": False,
            "historical_trade_body_opened": False,
            "peg_deviation_calculated": False,
            "reversion_outcome_calculated": False,
            "threshold_selected": False,
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
