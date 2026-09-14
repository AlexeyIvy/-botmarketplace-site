"""SC001-E002 OKX Q1 VPS source staging.

Infrastructure/data-staging only. Reacquires only the already-open frozen Q1
trade/L2 archives required by the four-day midquote confirmation, verifies each
file against the already-qualified parent reports, and writes files into the
exact directory layout expected by the frozen confirmation engine.

No alpha, no response metrics, no P&L, no Q2, no Validation, no Final.
Run modes are intentionally split so no single invocation silently exceeds the
historical staged-acquisition discipline:
  preflight -> parent/report checks only, no market-data body download
  trades    -> exact + D+1 trade archives for the four frozen days
  l2-a      -> 2024-01-14 + 2024-01-31 L2
  l2-b      -> 2024-02-12 + 2024-02-13 L2
  verify    -> local size/SHA verification only, no network download
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAGE = "SC001-E002-OKX-Q1-VPS-SOURCE-STAGE"
VERSION = "0.1"
TARGET_INST = "BTC-USDT-SWAP"
INST_TYPE = "SWAP"
INST_FAMILY = "BTC-USDT"
DOMAINS = ("https://www.okx.com", "https://us.okx.com")
DISCOVERY_PATH = "/priapi/v5/broker/public/trade-data/download-link"
REFERER = "https://www.okx.com/historical-data"
USER_AGENT = "BotMarketplace-SC001-E002-VPS-STAGE/0.1"
TIMEOUT = 90
RETRIES = 3
ALLOWED_HOST = "static.okx.com"
MIN_FREE_RESERVE_BYTES = 4_000_000_000
PER_RESPONSE_CAP_BYTES = 4_000_000

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
Q006R_REPORT = DATA_ROOT / "SC001_DATA_Q006R_OKX_UTC_STITCH" / "sc001_data_q006r_okx_utc_stitch_report.json"
Q009A_REPORT = DATA_ROOT / "SC001_DATA_Q009A_OKX_L2_BATCH_A" / "sc001_data_q009a_okx_l2_batch_a_report.json"
Q009B_REPORT = DATA_ROOT / "SC001_DATA_Q009B_OKX_L2_BATCH_B" / "sc001_data_q009b_okx_l2_batch_b_report.json"

DAYS = (
    {"date": "2024-01-14", "next_date": "2024-01-15", "l2_root": "SC001_DATA_Q009A_OKX_L2_BATCH_A", "batch": "A"},
    {"date": "2024-01-31", "next_date": "2024-02-01", "l2_root": "SC001_DATA_Q009A_OKX_L2_BATCH_A", "batch": "A"},
    {"date": "2024-02-12", "next_date": "2024-02-13", "l2_root": "SC001_DATA_Q009B_OKX_L2_BATCH_B", "batch": "B"},
    {"date": "2024-02-13", "next_date": "2024-02-14", "l2_root": "SC001_DATA_Q009B_OKX_L2_BATCH_B", "batch": "B"},
)
FROZEN_DATES = {x["date"] for x in DAYS}


def fail(msg: str) -> None:
    raise SystemExit(f"VPS_STAGE_FAIL: {msg}")


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required parent report: {path}")
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse {path}: {exc!r}")
    if not isinstance(obj, dict):
        fail(f"report is not an object: {path}")
    return obj


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    lo = int(d.timestamp() * 1000)
    hi = int((d + timedelta(days=1) - timedelta(milliseconds=1)).timestamp() * 1000)
    return lo, hi


def discovery_payload(module: str, date_text: str) -> dict:
    lo, hi = date_bounds(date_text)
    return {
        "module": module,
        "instType": INST_TYPE,
        "instQueryParam": {"instFamilyList": [INST_FAMILY]},
        "dateQuery": {"dateAggrType": "daily", "begin": str(lo), "end": str(hi)},
    }


def request_json(domain: str, module: str, date_text: str) -> dict | None:
    payload = discovery_payload(module, date_text)
    url = domain + DISCOVERY_PATH + "?t=" + str(int(time.time() * 1000))
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,*/*",
        "Content-Type": "application/json",
        "Referer": REFERER,
    }
    for attempt in range(1, RETRIES + 1):
        try:
            req = Request(url, data=body, method="POST", headers=headers)
            with urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(PER_RESPONSE_CAP_BYTES + 1)
            if len(raw) > PER_RESPONSE_CAP_BYTES:
                raise RuntimeError("metadata response cap exceeded")
            obj = json.loads(raw.decode("utf-8"))
            if isinstance(obj, dict):
                return obj
        except HTTPError as exc:
            if exc.code == 429 and attempt < RETRIES:
                time.sleep(1.5 * attempt)
                continue
            return None
        except (URLError, TimeoutError, OSError, ValueError, RuntimeError):
            if attempt < RETRIES:
                time.sleep(1.5 * attempt)
                continue
            return None
    return None


def extract_links(obj: dict | None) -> list[dict]:
    out: list[dict] = []
    if not isinstance(obj, dict) or obj.get("code") != "0":
        return out
    data = obj.get("data")
    details = data.get("details") if isinstance(data, dict) else None
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
            if isinstance(fn, str) and isinstance(url, str) and trusted_url(url, fn):
                out.append({"filename": fn, "url": url})
    return out


def discover_exact(module: str, file_date: str, expected_filename: str) -> str:
    # Query the exact file date first; also query the prior UTC date because the
    # historical OKX download grouping used by Q006R can surface a D+1 archive
    # under the D metadata request. Metadata only; archive bodies are not opened.
    d = datetime.strptime(file_date, "%Y-%m-%d")
    query_dates = (file_date, (d - timedelta(days=1)).strftime("%Y-%m-%d"))
    matches: list[str] = []
    for qd in query_dates:
        for domain in DOMAINS:
            for row in extract_links(request_json(domain, module, qd)):
                if row["filename"] == expected_filename and row["url"] not in matches:
                    matches.append(row["url"])
            if matches:
                break
        if matches:
            break
    if len(matches) != 1:
        fail(f"exact source URL not uniquely discovered for {expected_filename}: {len(matches)}")
    return matches[0]


def head_size(url: str, expected_filename: str) -> int:
    if not trusted_url(url, expected_filename):
        fail(f"untrusted source URL for {expected_filename}")
    req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT, "Referer": REFERER})
    with urlopen(req, timeout=TIMEOUT) as resp:
        final = resp.geturl()
        status = int(getattr(resp, "status", 200))
        cl = resp.headers.get("Content-Length")
    if status != 200 or not trusted_url(final, expected_filename) or not cl or not cl.isdigit():
        fail(f"HEAD identity/size failed for {expected_filename}")
    return int(cl)


def verify_firewall(obj: dict, label: str) -> None:
    for key in ("q2_okx_accessed", "validation_or_final_accessed"):
        if obj.get(key) is not False:
            fail(f"{label} firewall mismatch: {key}")


def parent_state() -> tuple[dict, dict[str, dict]]:
    q6 = load_json(Q006R_REPORT)
    q9a = load_json(Q009A_REPORT)
    q9b = load_json(Q009B_REPORT)

    if q6.get("stage") != "SC001-DATA-Q006R-OKX-UTC-STITCH" or q6.get("overall_status") != "PASS":
        fail("Q006R parent is not PASS")
    if q9a.get("stage") != "SC001-DATA-Q009A-OKX-L2-Q1-BATCH-A" or q9a.get("overall_status") != "PASS":
        fail("Q009A parent is not PASS")
    if q9b.get("stage") != "SC001-DATA-Q009B-OKX-L2-Q1-BATCH-B" or q9b.get("overall_status") != "PASS":
        fail("Q009B parent is not PASS")
    verify_firewall(q6, "Q006R")
    verify_firewall(q9a, "Q009A")
    verify_firewall(q9b, "Q009B")
    for label, obj in (("Q009A", q9a), ("Q009B", q9b)):
        for key in ("strategy_features_calculated", "midquote_response_calculated", "strategy_pnl_calculated", "execution_profitability_calculated"):
            if obj.get(key) is not False:
                fail(f"{label} alpha/P&L firewall mismatch: {key}")

    q6_rows = {x.get("date"): x for x in (q6.get("days") or []) if isinstance(x, dict)}
    if not FROZEN_DATES.issubset(q6_rows):
        fail(f"Q006R frozen dates missing: {sorted(FROZEN_DATES - set(q6_rows))}")

    l2_rows: dict[str, dict] = {}
    for source, report in (("Q009A", q9a), ("Q009B", q9b)):
        for row in report.get("days") or []:
            if isinstance(row, dict) and row.get("status") == "FULL_DAY_PASS":
                l2_rows[str(row.get("date"))] = {"source": source, **row}
    if set(l2_rows) != FROZEN_DATES:
        fail(f"L2 parent date set mismatch: {sorted(l2_rows)}")
    return q6_rows, l2_rows


def expected_trade(q6_row: dict, which: str) -> tuple[str, int, str]:
    if which == "exact":
        x = q6_row.get("exact_archive") or {}
        filename = x.get("filename")
        size = x.get("bytes")
        sha = x.get("sha256")
    else:
        x = q6_row.get("neighbor_archive") or {}
        filename = x.get("filename")
        head = x.get("head") or {}
        dl = x.get("download") or {}
        size = dl.get("bytes") or head.get("content_length")
        sha = dl.get("sha256")
    if not isinstance(filename, str) or not isinstance(size, int) or not isinstance(sha, str) or len(sha) != 64:
        fail(f"incomplete Q006R {which} archive identity")
    return filename, size, sha


def expected_l2(row: dict, date: str) -> tuple[str, int, str]:
    filename = f"{TARGET_INST}-L2orderbook-400lv-{date}.tar.gz"
    a = row.get("archive") or {}
    size = a.get("bytes")
    sha = a.get("sha256")
    if not isinstance(size, int) or not isinstance(sha, str) or len(sha) != 64:
        fail(f"incomplete L2 parent identity for {date}")
    return filename, size, sha


def check_existing(path: Path, expected_size: int, expected_sha: str) -> bool:
    if not path.exists():
        return False
    if path.stat().st_size != expected_size:
        return False
    return sha256_file(path) == expected_sha


def download_verified(url: str, dest: Path, expected_size: int, expected_sha: str) -> None:
    if check_existing(dest, expected_size, expected_sha):
        print(f"REUSED VERIFIED: {dest.name}")
        return
    if dest.exists():
        dest.unlink()
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = Path(str(dest) + ".part")
    remote_size = head_size(url, dest.name)
    if remote_size != expected_size:
        fail(f"HEAD size changed for {dest.name}: {remote_size} != {expected_size}")
    if shutil.disk_usage(DATA_ROOT).free - max(0, expected_size - (part.stat().st_size if part.exists() else 0)) < MIN_FREE_RESERVE_BYTES:
        fail("4 GB free-space reserve would be violated")
    cmd = [
        "curl", "-L", "--fail", "--retry", "5", "--retry-delay", "3", "-C", "-",
        "-A", USER_AGENT, "-e", REFERER, "-o", str(part), url,
    ]
    print(f"DOWNLOAD: {dest.name} ({expected_size:,} bytes)")
    cp = subprocess.run(cmd)
    if cp.returncode != 0:
        fail(f"curl failed for {dest.name} rc={cp.returncode}")
    if not part.exists() or part.stat().st_size != expected_size:
        fail(f"download size mismatch for {dest.name}")
    got_sha = sha256_file(part)
    if got_sha != expected_sha:
        bad = Path(str(part) + ".sha_mismatch")
        os.replace(part, bad)
        fail(f"SHA256 mismatch for {dest.name}; preserved as {bad.name}")
    os.replace(part, dest)
    print(f"VERIFIED: {dest.name} SHA256={got_sha}")


def preflight(q6_rows: dict, l2_rows: dict) -> None:
    trade_bytes = 0
    l2_a = 0
    l2_b = 0
    for day in DAYS:
        q6 = q6_rows[day["date"]]
        trade_bytes += expected_trade(q6, "exact")[1]
        trade_bytes += expected_trade(q6, "neighbor")[1]
        size = expected_l2(l2_rows[day["date"]], day["date"])[1]
        if day["batch"] == "A":
            l2_a += size
        else:
            l2_b += size
    if l2_a >= 1_200_000_000 or l2_b >= 1_350_000_000:
        fail("frozen staged L2 batch cap would be exceeded")
    print("VPS_SOURCE_PREFLIGHT_PASS")
    print("frozen dates =", [x["date"] for x in DAYS])
    print("trade expected bytes <=", trade_bytes)
    print("L2-A expected bytes =", l2_a)
    print("L2-B expected bytes =", l2_b)
    print("Q2/Validation/Final = CLOSED")
    print("alpha/P&L calculated = NO")


def stage_trades(q6_rows: dict) -> None:
    for day in DAYS:
        date = day["date"]
        q6 = q6_rows[date]
        ex_name, ex_size, ex_sha = expected_trade(q6, "exact")
        ex_url = discover_exact("1", date, ex_name)
        ex_dest = DATA_ROOT / "SC001_DATA_Q006_OKX_TRADES" / "archives" / ex_name
        download_verified(ex_url, ex_dest, ex_size, ex_sha)

        nb_name, nb_size, nb_sha = expected_trade(q6, "neighbor")
        nb_url = discover_exact("1", day["next_date"], nb_name)
        nb_dest = DATA_ROOT / "SC001_DATA_Q006R_OKX_UTC_STITCH" / "neighbor_archives" / nb_name
        download_verified(nb_url, nb_dest, nb_size, nb_sha)
    print("VPS_TRADE_STAGE_PASS")


def stage_l2(l2_rows: dict, batch: str) -> None:
    selected = [x for x in DAYS if x["batch"] == batch]
    total = sum(expected_l2(l2_rows[x["date"]], x["date"])[1] for x in selected)
    cap = 1_200_000_000 if batch == "A" else 1_350_000_000
    if total >= cap:
        fail(f"L2 batch {batch} exceeds staged cap")
    for day in selected:
        date = day["date"]
        name, size, sha = expected_l2(l2_rows[date], date)
        url = discover_exact("4", date, name)
        dest = DATA_ROOT / day["l2_root"] / date / name
        download_verified(url, dest, size, sha)
    print(f"VPS_L2_{batch}_STAGE_PASS")


def verify_all(q6_rows: dict, l2_rows: dict) -> None:
    missing = []
    for day in DAYS:
        date = day["date"]
        q6 = q6_rows[date]
        ex_name, ex_size, ex_sha = expected_trade(q6, "exact")
        nb_name, nb_size, nb_sha = expected_trade(q6, "neighbor")
        l2_name, l2_size, l2_sha = expected_l2(l2_rows[date], date)
        specs = (
            (DATA_ROOT / "SC001_DATA_Q006_OKX_TRADES" / "archives" / ex_name, ex_size, ex_sha),
            (DATA_ROOT / "SC001_DATA_Q006R_OKX_UTC_STITCH" / "neighbor_archives" / nb_name, nb_size, nb_sha),
            (DATA_ROOT / day["l2_root"] / date / l2_name, l2_size, l2_sha),
        )
        for path, size, sha in specs:
            ok = check_existing(path, size, sha)
            print(("PASS" if ok else "FAIL"), path)
            if not ok:
                missing.append(str(path))
    if missing:
        fail(f"source verification failed for {len(missing)} file(s)")
    print("VPS_ALL_SOURCES_VERIFIED_PASS")
    print("Q2/Validation/Final = CLOSED")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("preflight", "trades", "l2-a", "l2-b", "verify"))
    args = ap.parse_args()
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(DATA_ROOT).free < MIN_FREE_RESERVE_BYTES:
        fail("less than 4 GB free before start")
    q6_rows, l2_rows = parent_state()
    if args.mode == "preflight":
        preflight(q6_rows, l2_rows)
    elif args.mode == "trades":
        preflight(q6_rows, l2_rows)
        stage_trades(q6_rows)
    elif args.mode == "l2-a":
        preflight(q6_rows, l2_rows)
        stage_l2(l2_rows, "A")
    elif args.mode == "l2-b":
        preflight(q6_rows, l2_rows)
        stage_l2(l2_rows, "B")
    else:
        verify_all(q6_rows, l2_rows)


if __name__ == "__main__":
    main()
