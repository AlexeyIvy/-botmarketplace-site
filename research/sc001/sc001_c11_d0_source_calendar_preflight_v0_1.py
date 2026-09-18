from __future__ import annotations

import html
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C11-D0-SOURCE-CALENDAR-PREFLIGHT-V0.1"
PASS = "C11_D0_SOURCE_CALENDAR_PREFLIGHT_PASS"
REVIEW = "C11_D0_SOURCE_CALENDAR_PREFLIGHT_REVIEW"

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
OKX_INST = "BTC-USDT-SWAP"
OKX_FAMILY = "BTC-USDT"
OKX_STATIC_HOST = "static.okx.com"

EVENTS = (
    {
        "kind": "CPI",
        "date": "2025-01-15",
        "utc": "2025-01-15T13:30:00Z",
        "schedule_url": "https://www.bls.gov/schedule/2025/01_sched_list.htm",
        "title": "Consumer Price Index",
        "date_text": "January 15, 2025",
        "archive": "BTC-USDT-SWAP-trades-2025-01-15.zip",
        "begin_ms": 1736899200000,
        "end_ms": 1736985600000,
    },
    {
        "kind": "EMPLOYMENT",
        "date": "2025-02-07",
        "utc": "2025-02-07T13:30:00Z",
        "schedule_url": "https://www.bls.gov/schedule/2025/02_sched_list.htm",
        "title": "Employment Situation",
        "date_text": "February 7, 2025",
        "archive": "BTC-USDT-SWAP-trades-2025-02-07.zip",
        "begin_ms": 1738886400000,
        "end_ms": 1738972800000,
    },
)

TIMEOUT = 60
RETRIES = 3
MAX_TEXT_BYTES = 2_000_000
MAX_JSON_BYTES = 4_000_000

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c11-d0-source-calendar-preflight-protocol-v0.1.md"
FREEZE = ROOT / "docs/research/sc001-c11-d0-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_C11_D0_SOURCE_CALENDAR"
OUT = OUT_DIR / "sc001_c11_d0_source_calendar_report_v0_1.json"


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
    if fr.get("status") != "FROZEN_BEFORE_C11_D0_RUN":
        fail("C11-D0 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C11-D0 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C11-D0 protocol identity mismatch")
    for k in (
        "historical_trade_body_authorized",
        "macro_release_value_authorized",
        "macro_surprise_authorized",
        "post_release_move_authorized",
        "direction_signal_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C11-D0 firewall mismatch: {k}")


def request_bytes(req: urllib.request.Request, cap: int, label: str) -> tuple[bytes, str, int]:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                raw = resp.read(cap + 1)
            if status != 200:
                fail(f"{label} HTTP {status}")
            if len(raw) > cap:
                fail(f"{label} response cap exceeded")
            return raw, final, status
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} failed: {type(last).__name__}: {last}")


def verify_bls_event(event: dict) -> dict:
    req = urllib.request.Request(
        event["schedule_url"],
        method="GET",
        headers={
            "User-Agent": "BotMarketplace-SC001-C11-D0/0.1",
            "Accept": "text/html,*/*",
        },
    )
    raw, final, _ = request_bytes(req, MAX_TEXT_BYTES, event["kind"] + " BLS")
    host = (urllib.parse.urlparse(final).hostname or "").lower()
    if host not in {"www.bls.gov", "bls.gov"}:
        fail(f"{event['kind']} unexpected BLS host: {host}")

    text = html.unescape(raw.decode("utf-8", errors="replace"))
    text = re.sub(r"\s+", " ", text)

    checks = {
        "official_host": True,
        "date_present": event["date_text"].lower() in text.lower(),
        "title_present": event["title"].lower() in text.lower(),
        "0830_present": "08:30 AM".lower() in text.lower(),
    }
    if not all(checks.values()):
        fail(f"{event['kind']} schedule metadata mismatch: {checks}")

    return {
        "pass": True,
        "schedule_url": event["schedule_url"],
        "final_host": host,
        "frozen_utc": event["utc"],
        "checks": checks,
        "response_bytes": len(raw),
    }


def okx_get(path: str, params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    last = None
    for domain in OKX_DOMAINS:
        try:
            req = urllib.request.Request(
                domain + path + "?" + query,
                method="GET",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C11-D0/0.1",
                    "Accept": "application/json",
                },
            )
            raw, final, _ = request_bytes(req, MAX_JSON_BYTES, "OKX GET")
            host = (urllib.parse.urlparse(final).hostname or "").lower()
            if host not in {"www.okx.com", "us.okx.com"}:
                fail(f"unexpected OKX GET host: {host}")
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                fail(f"OKX GET code mismatch: {obj.get('code') if isinstance(obj, dict) else None}")
            return obj
        except Exception as exc:
            last = exc
    raise RuntimeError(f"OKX GET failed: {type(last).__name__}: {last}")


def verify_instrument() -> dict:
    obj = okx_get(
        "/api/v5/public/instruments",
        {"instType": "SWAP", "instId": OKX_INST},
    )
    rows = obj.get("data") or []
    if len(rows) != 1 or not isinstance(rows[0], dict):
        fail(f"BTC swap instrument row count={len(rows)}")
    r = rows[0]
    checks = {
        "inst_exact": r.get("instId") == OKX_INST,
        "inst_type": r.get("instType") == "SWAP",
        "linear": r.get("ctType") == "linear",
        "settle_usdt": r.get("settleCcy") == "USDT",
        "live": r.get("state") == "live",
    }
    if not all(checks.values()):
        fail(f"BTC swap instrument semantics mismatch: {checks}")
    return {"pass": True, "checks": checks, "uly": r.get("uly")}


def walk_nodes(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk_nodes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_nodes(v)


def trusted_archive(url: str, basename: str) -> bool:
    p = urllib.parse.urlparse(url)
    return (
        p.scheme == "https"
        and (p.hostname or "").lower() == OKX_STATIC_HOST
        and Path(p.path).name == basename
    )


def resolve_archive(event: dict) -> str:
    payload = {
        "module": "1",
        "instType": "SWAP",
        "instQueryParam": {"instFamilyList": [OKX_FAMILY]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(event["begin_ms"]),
            "end": str(event["end_ms"] - 1),
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    last = None

    for domain in OKX_DOMAINS:
        try:
            url = domain + "/priapi/v5/broker/public/trade-data/download-link?t=" + str(int(time.time()*1000))
            req = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C11-D0/0.1",
                    "Accept": "application/json,*/*",
                    "Content-Type": "application/json",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )
            raw, final, _ = request_bytes(req, MAX_JSON_BYTES, event["kind"] + " OKX metadata")
            host = (urllib.parse.urlparse(final).hostname or "").lower()
            if host not in {"www.okx.com", "us.okx.com"}:
                fail(f"{event['kind']} unexpected OKX metadata host: {host}")
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                fail(f"{event['kind']} OKX metadata code mismatch")

            found = []
            for node in walk_nodes(obj.get("data")):
                if not isinstance(node, dict):
                    continue
                fn = node.get("filename") or node.get("fileName")
                u = node.get("url")
                if (
                    fn == event["archive"]
                    and isinstance(u, str)
                    and trusted_archive(u, event["archive"])
                    and u not in found
                ):
                    found.append(u)

            if len(found) == 1:
                return found[0]
            if len(found) > 1:
                fail(f"{event['kind']} multiple exact archive URLs")
            last = RuntimeError(f"{event['kind']} exact archive not found")
        except Exception as exc:
            last = exc

    raise RuntimeError(f"{event['kind']} archive resolution failed: {type(last).__name__}: {last}")


def head_archive(url: str, basename: str) -> int:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C11-D0/0.1",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                cl = resp.headers.get("Content-Length")
            if status != 200:
                fail(f"HEAD HTTP {status}: {basename}")
            if not trusted_archive(final, basename):
                fail(f"HEAD identity mismatch: {basename}")
            if not cl or not cl.isdigit() or int(cl) <= 0:
                fail(f"invalid Content-Length: {basename}")
            return int(cl)
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"HEAD failed {basename}: {type(last).__name__}: {last}")


def main() -> int:
    try:
        require_freeze()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        print("C11-D0 verify current BTC swap instrument", flush=True)
        inst = verify_instrument()

        event_rows = []
        for event in EVENTS:
            print(f"C11-D0 verify official BLS schedule: {event['kind']}", flush=True)
            bls = verify_bls_event(event)

            print(f"C11-D0 resolve historical BTC trade archive: {event['date']}", flush=True)
            url = resolve_archive(event)
            size = head_archive(url, event["archive"])

            event_rows.append({
                "kind": event["kind"],
                "date": event["date"],
                "frozen_utc": event["utc"],
                "bls": bls,
                "archive": {
                    "filename": event["archive"],
                    "content_length": size,
                    "host": urllib.parse.urlparse(url).hostname,
                },
            })

        report = {
            "stage": STAGE,
            "version": "0.1",
            "status": PASS,
            "instrument": inst,
            "events": event_rows,
            "historical_trade_body_downloaded": False,
            "historical_trade_body_opened": False,
            "macro_release_value_accessed": False,
            "macro_surprise_calculated": False,
            "post_release_move_calculated": False,
            "direction_signal_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, report)

        print(PASS)
        print("events_verified =", len(event_rows), "/", len(EVENTS))
        for row in event_rows:
            print(row["kind"], row["date"], "archive_bytes =", row["archive"]["content_length"])
        print("historical trade body downloaded/opened = False / False")
        print("macro value/surprise/post-release move/direction/PnL = False")
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
            "macro_release_value_accessed": False,
            "macro_surprise_calculated": False,
            "post_release_move_calculated": False,
            "direction_signal_calculated": False,
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
