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

STAGE = "SC001-C11-V2-SC-METADATA-PREFLIGHT-V0.2"
PASS = "C11_V2_SC_METADATA_PREFLIGHT_PASS"
REVIEW = "C11_V2_SC_METADATA_PREFLIGHT_REVIEW"

EVENTS = (
    ("EMPLOYMENT","2025-07-03","2025-07-03T12:30:00Z","https://www.bls.gov/schedule/2025/07_sched_list.htm","Employment Situation"),
    ("CPI","2025-07-15","2025-07-15T12:30:00Z","https://www.bls.gov/schedule/2025/07_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2025-08-01","2025-08-01T12:30:00Z","https://www.bls.gov/schedule/2025/08_sched_list.htm","Employment Situation"),
    ("CPI","2025-08-12","2025-08-12T12:30:00Z","https://www.bls.gov/schedule/2025/08_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2025-09-05","2025-09-05T12:30:00Z","https://www.bls.gov/schedule/2025/09_sched_list.htm","Employment Situation"),
    ("CPI","2025-09-11","2025-09-11T12:30:00Z","https://www.bls.gov/schedule/2025/09_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2026-01-09","2026-01-09T13:30:00Z","https://www.bls.gov/schedule/2026/01_sched_list.htm","Employment Situation"),
    ("CPI","2026-01-13","2026-01-13T13:30:00Z","https://www.bls.gov/schedule/2026/01_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2026-02-11","2026-02-11T13:30:00Z","https://www.bls.gov/schedule/2026/02_sched_list.htm","Employment Situation"),
    ("CPI","2026-02-13","2026-02-13T13:30:00Z","https://www.bls.gov/schedule/2026/02_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2026-03-06","2026-03-06T13:30:00Z","https://www.bls.gov/schedule/2026/03_sched_list.htm","Employment Situation"),
    ("CPI","2026-03-11","2026-03-11T12:30:00Z","https://www.bls.gov/schedule/2026/03_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2026-04-03","2026-04-03T12:30:00Z","https://www.bls.gov/schedule/2026/04_sched_list.htm","Employment Situation"),
    ("CPI","2026-04-10","2026-04-10T12:30:00Z","https://www.bls.gov/schedule/2026/04_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2026-05-08","2026-05-08T12:30:00Z","https://www.bls.gov/schedule/2026/05_sched_list.htm","Employment Situation"),
    ("CPI","2026-05-12","2026-05-12T12:30:00Z","https://www.bls.gov/schedule/2026/05_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2026-06-05","2026-06-05T12:30:00Z","https://www.bls.gov/schedule/2026/06_sched_list.htm","Employment Situation"),
    ("CPI","2026-06-10","2026-06-10T12:30:00Z","https://www.bls.gov/schedule/2026/06_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2026-07-02","2026-07-02T12:30:00Z","https://www.bls.gov/schedule/2026/07_sched_list.htm","Employment Situation"),
    ("CPI","2026-07-14","2026-07-14T12:30:00Z","https://www.bls.gov/schedule/2026/07_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2026-08-07","2026-08-07T12:30:00Z","https://www.bls.gov/schedule/2026/08_sched_list.htm","Employment Situation"),
    ("CPI","2026-08-12","2026-08-12T12:30:00Z","https://www.bls.gov/schedule/2026/08_sched_list.htm","Consumer Price Index"),
    ("EMPLOYMENT","2026-09-04","2026-09-04T12:30:00Z","https://www.bls.gov/schedule/2026/09_sched_list.htm","Employment Situation"),
    ("CPI","2026-09-11","2026-09-11T12:30:00Z","https://www.bls.gov/schedule/2026/09_sched_list.htm","Consumer Price Index"),
)

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
OKX_STATIC_HOST = "static.okx.com"
OKX_FAMILY = "BTC-USDT"
TIMEOUT = 60
RETRIES = 3
MAX_TEXT = 2_000_000
MAX_JSON = 4_000_000

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c11-v2-selection-metadata-preflight-protocol-v0.2.md"
FREEZE = ROOT / "docs/research/sc001-c11-v2-selection-metadata-preflight-implementation-freeze-v0.2.json"
CHRONOLOGY = ROOT / "docs/research/sc001-c11-v2-chronology-freeze-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.19.json"
D0 = ROOT / "docs/research/sc001-c11-d0-source-calendar-pass-result-v0.1.md"

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_C11_V2_SC_METADATA"
OUT = OUT_DIR / "sc001_c11_v2_sc_metadata_preflight_report_v0_2.json"

def fail(msg: str) -> None:
    raise RuntimeError(msg)

def load_json(path: Path) -> dict:
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
    if fr.get("status") != "FROZEN_BEFORE_C11_V2_SC_METADATA_V02_RUN":
        fail("freeze status mismatch")
    expected = {
        "runner_git_blob_sha": git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha": git_blob(PROTOCOL),
        "chronology_git_blob_sha": git_blob(CHRONOLOGY),
        "contamination_registry_git_blob_sha": git_blob(REGISTRY),
        "parent_d0_result_git_blob_sha": git_blob(D0),
    }
    for key, value in expected.items():
        if fr.get(key) != value:
            fail(f"freeze identity mismatch: {key}")
    if int(fr.get("event_count", 0)) != 24:
        fail("event count mismatch")
    if int(fr.get("cpi_count", 0)) != 12 or int(fr.get("employment_count", 0)) != 12:
        fail("family count mismatch")
    for key in (
        "historical_trade_body_authorized",
        "macro_release_value_authorized",
        "macro_surprise_authorized",
        "first_impulse_authorized",
        "residual_post_decision_move_authorized",
        "direction_signal_authorized",
        "continuation_outcome_authorized",
        "execution_model_authorized",
        "pnl_authorized",
        "confirmation_outcome_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(key) is not False:
            fail(f"firewall mismatch: {key}")

def request_bytes(req, cap: int, label: str):
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(cap + 1)
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
            if status != 200:
                fail(f"{label} HTTP {status}")
            if len(raw) > cap:
                fail(f"{label} response cap exceeded")
            return raw, final
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} failed: {type(last).__name__}: {last}")

def bls_row_pattern(date: str, title: str) -> re.Pattern:
    dt = datetime.strptime(date, "%Y-%m-%d")
    month = re.escape(dt.strftime("%B"))
    day = str(dt.day)
    year = str(dt.year)
    release = re.escape(title)
    weekdays = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
    return re.compile(
        rf"{weekdays},?\s+{month}\s+0?{day},\s+{year}\s+08:30\s+AM\s+{release}\b",
        re.IGNORECASE,
    )

def verify_bls(kind: str, date: str, url: str, title: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "BotMarketplace-SC001-C11-V2-Metadata/0.2",
            "Accept": "text/html,*/*",
        },
    )
    raw, final = request_bytes(req, MAX_TEXT, f"{kind} BLS {date}")
    host = (urllib.parse.urlparse(final).hostname or "").lower()
    if host not in {"www.bls.gov", "bls.gov"}:
        fail(f"unexpected BLS host: {host}")
    text = re.sub(r"\s+", " ", html.unescape(raw.decode("utf-8", errors="replace")))
    pattern = bls_row_pattern(date, title)
    match = pattern.search(text)
    if match is None:
        fail(f"BLS row metadata mismatch {kind} {date}")
    return {
        "pass": True,
        "url": url,
        "final_url": final,
        "matched_row": match.group(0),
        "response_bytes": len(raw),
    }

def day_ms(date: str):
    d = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    begin = int(d.timestamp() * 1000)
    return begin, begin + 86_400_000

def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)

def trusted(url: str, basename: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return (
        parsed.scheme == "https"
        and (parsed.hostname or "").lower() == OKX_STATIC_HOST
        and Path(parsed.path).name == basename
    )

def resolve(date: str):
    begin, end = day_ms(date)
    basename = f"BTC-USDT-SWAP-trades-{date}.zip"
    payload = {
        "module": "1",
        "instType": "SWAP",
        "instQueryParam": {"instFamilyList": [OKX_FAMILY]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(begin),
            "end": str(end - 1),
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode()
    last = None
    for domain in OKX_DOMAINS:
        try:
            req = urllib.request.Request(
                domain + "/priapi/v5/broker/public/trade-data/download-link?t=" + str(int(time.time() * 1000)),
                data=body,
                method="POST",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C11-V2-Metadata/0.2",
                    "Accept": "application/json,*/*",
                    "Content-Type": "application/json",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )
            raw, final = request_bytes(req, MAX_JSON, f"OKX metadata {date}")
            host = (urllib.parse.urlparse(final).hostname or "").lower()
            if host not in {"www.okx.com", "us.okx.com"}:
                fail(f"bad metadata host {host}")
            obj = json.loads(raw.decode())
            if str(obj.get("code")) != "0":
                fail(f"OKX code mismatch {date}: {obj.get('code')}")
            found = []
            for node in walk(obj.get("data")):
                if isinstance(node, dict):
                    fn = node.get("filename") or node.get("fileName")
                    archive_url = node.get("url")
                    if (
                        fn == basename
                        and isinstance(archive_url, str)
                        and trusted(archive_url, basename)
                        and archive_url not in found
                    ):
                        found.append(archive_url)
            if len(found) == 1:
                return basename, found[0]
            if len(found) > 1:
                fail(f"multiple exact urls {date}")
            last = RuntimeError(f"exact archive missing {date}")
        except Exception as exc:
            last = exc
    raise RuntimeError(f"archive resolution failed {date}: {type(last).__name__}: {last}")

def head(url: str, basename: str) -> int:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C11-V2-Metadata/0.2",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                final = resp.geturl()
                content_length = resp.headers.get("Content-Length")
                status = int(getattr(resp, "status", 200))
            if (
                status != 200
                or not trusted(final, basename)
                or not content_length
                or not content_length.isdigit()
                or int(content_length) <= 0
            ):
                fail(f"HEAD mismatch {basename}")
            return int(content_length)
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"HEAD failed {basename}: {last}")

def main() -> int:
    try:
        require_freeze()

        if len(EVENTS) != 24:
            fail("runner EVENTS length mismatch")
        if sum(1 for row in EVENTS if row[0] == "CPI") != 12:
            fail("runner CPI count mismatch")
        if sum(1 for row in EVENTS if row[0] == "EMPLOYMENT") != 12:
            fail("runner Employment count mismatch")

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        rows = []

        for i, (kind, date, utc, url, title) in enumerate(EVENTS, 1):
            print(f"C11-V2-SC-META-V02 [{i}/24] {kind} {date}", flush=True)
            bls = verify_bls(kind, date, url, title)
            basename, archive_url = resolve(date)
            size = head(archive_url, basename)
            rows.append(
                {
                    "kind": kind,
                    "date": date,
                    "frozen_utc": utc,
                    "bls": bls,
                    "archive": {
                        "filename": basename,
                        "content_length": size,
                    },
                }
            )
            print(f"PASS {kind} {date} archive_bytes={size}", flush=True)

        report = {
            "stage": STAGE,
            "version": "0.2",
            "status": PASS,
            "selection_calibration_role": "NONPROMOTIONAL_SELECTION_CALIBRATION",
            "contamination_qualifier": "C11_MICROSTRUCTURE_OUTCOME_UNOPENED_BUT_SC001_COARSE_PRICE_EXPOSED",
            "events": rows,
            "events_verified": len(rows),
            "cpi_verified": sum(1 for row in rows if row["kind"] == "CPI"),
            "employment_verified": sum(1 for row in rows if row["kind"] == "EMPLOYMENT"),
            "v01_review_reason": "ENGINEERING_BLS_DAY_ZERO_PADDING_PARSER_DEFECT",
            "chronology_changed_from_v01": False,
            "historical_trade_body_downloaded": False,
            "historical_trade_body_opened": False,
            "macro_release_value_accessed": False,
            "macro_surprise_calculated": False,
            "first_impulse_calculated": False,
            "residual_post_decision_move_calculated": False,
            "direction_signal_calculated": False,
            "continuation_outcome_calculated": False,
            "execution_model_calculated": False,
            "pnl_calculated": False,
            "confirmation_outcome_accessed": False,
            "promotional_alpha_accessed": False,
        }
        atomic_json(OUT, report)

        print(PASS)
        print("events_verified =", len(rows), "/ 24")
        print("CPI / Employment =", report["cpi_verified"], "/", report["employment_verified"])
        print("chronology changed from v0.1 = False")
        print("historical trade body downloaded/opened = False / False")
        print("macro value/surprise/impulse/residual/direction/continuation/execution/PnL = False")
        print("confirmation outcome accessed = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)
        return 0

    except Exception as exc:
        print(REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
