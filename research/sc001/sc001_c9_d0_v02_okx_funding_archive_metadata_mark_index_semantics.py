from __future__ import annotations

import json
import math
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE = "SC001-C9-D0-V0.2-OKX-FUNDING-ARCHIVE-METADATA-MARK-INDEX-SEMANTICS"
PASS = "C9_D0_V02_DATA_SEMANTICS_PASS"
REVIEW = "C9_D0_V02_DATA_SEMANTICS_REVIEW"

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
ALLOWED_ARCHIVE_HOST = "static.okx.com"
ASSETS = ("BTC", "ETH", "DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
SWAPS = tuple(f"{s}-USDT-SWAP" for s in ASSETS)

PERF_WINDOWS = (
    ("JULY", "2024-07-01", "2024-07-14"),
    ("SEPTEMBER", "2024-09-01", "2024-09-14"),
)
ARCHIVE_MONTHS = (
    ("JULY", 2024, 7),
    ("SEPTEMBER", 2024, 9),
)

BAR = "4H"
EXPECTED_4H_ROWS = 84
MIN_4H_ROWS = 80
TIMEOUT = 45
RETRIES = 3
MAX_JSON_BYTES = 4_000_000

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c9-d0-okx-funding-archive-metadata-mark-index-semantics-protocol-v0.2.md"
FREEZE = ROOT / "docs/research/sc001-c9-d0-v0.2-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_C9_D0_V02_DATA_SEMANTICS"
OUT = OUT_DIR / "sc001_c9_d0_v02_data_semantics_report_v0_1.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        text=True,
    ).strip()


def require_freeze() -> dict:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_C9_D0_V02_RUN":
        fail("C9-D0 v0.2 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C9-D0 v0.2 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C9-D0 v0.2 protocol identity mismatch")
    if tuple(fr.get("probe_universe") or ()) != SWAPS:
        fail("C9-D0 v0.2 universe mismatch")
    for key in (
        "funding_body_download_authorized",
        "funding_body_open_authorized",
        "returns_authorized",
        "basis_transition_authorized",
        "strategy_signal_authorized",
        "sentinel_outcome_authorized",
        "pnl_authorized",
        "direction_selection_authorized",
        "threshold_selection_authorized",
        "event_window_selection_authorized",
        "protected_market_body_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(key) is not False:
            fail(f"C9-D0 v0.2 freeze firewall mismatch: {key}")
    return fr


def date_ms(day: str) -> int:
    return int(
        datetime.strptime(day, "%Y-%m-%d")
        .replace(tzinfo=timezone.utc)
        .timestamp()
        * 1000
    )


def next_day(day: str) -> str:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return (d + timedelta(days=1)).strftime("%Y-%m-%d")


def month_bounds_utc8_ms(year: int, month: int) -> tuple[int, int]:
    tz8 = timezone(timedelta(hours=8))
    start_local = datetime(year, month, 1, tzinfo=tz8)
    if month == 12:
        end_local = datetime(year + 1, 1, 1, tzinfo=tz8)
    else:
        end_local = datetime(year, month + 1, 1, tzinfo=tz8)
    return int(start_local.timestamp() * 1000), int(end_local.timestamp() * 1000)


def request_json(path: str, params: dict[str, str]) -> tuple[dict, str, int]:
    query = urllib.parse.urlencode(params)
    last: Exception | None = None

    for domain in DOMAINS:
        url = domain + path + ("?" + query if query else "")
        for attempt in range(1, RETRIES + 1):
            try:
                req = urllib.request.Request(
                    url,
                    method="GET",
                    headers={
                        "User-Agent": "BotMarketplace-SC001-C9-D0-v0.2",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    raw = resp.read(MAX_JSON_BYTES + 1)
                    status = int(getattr(resp, "status", 200))
                    final = resp.geturl()

                if len(raw) > MAX_JSON_BYTES:
                    fail(f"response cap exceeded: {path}")
                if status != 200:
                    fail(f"HTTP {status}: {path}")

                parsed = urllib.parse.urlparse(final)
                if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {
                    "www.okx.com",
                    "us.okx.com",
                }:
                    fail(f"unexpected final API URL identity: {final}")

                obj = json.loads(raw.decode("utf-8"))
                if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                    code = obj.get("code") if isinstance(obj, dict) else None
                    fail(f"OKX code mismatch path={path} code={code}")
                return obj, final, len(raw)

            except Exception as exc:
                last = exc
                if attempt < RETRIES:
                    time.sleep(float(attempt))

    raise RuntimeError(f"request failed {path}: {type(last).__name__}: {last}")


def instrument_meta(inst: str) -> dict:
    obj, final, nbytes = request_json(
        "/api/v5/public/instruments",
        {"instType": "SWAP", "instId": inst},
    )
    rows = obj.get("data") or []
    if len(rows) != 1 or not isinstance(rows[0], dict):
        fail(f"instrument metadata row mismatch: {inst} count={len(rows)}")
    r = rows[0]
    if r.get("instId") != inst or r.get("instType") != "SWAP":
        fail(f"instrument identity mismatch: {inst}")
    uly = r.get("uly")
    if not isinstance(uly, str) or not uly:
        fail(f"missing uly for {inst}")
    return {
        "inst_id": inst,
        "uly": uly,
        "state": r.get("state"),
        "settle_ccy": r.get("settleCcy"),
        "ct_type": r.get("ctType"),
        "api_final_url_host": urllib.parse.urlparse(final).hostname,
        "response_bytes": nbytes,
    }


def walk_file_nodes(node):
    if isinstance(node, dict):
        filename = node.get("filename") or node.get("fileName")
        url = node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
        if isinstance(filename, str) and isinstance(url, str):
            yield node
        for value in node.values():
            yield from walk_file_nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_file_nodes(value)


def trusted_archive_url(url: str, filename: str) -> bool:
    try:
        p = urllib.parse.urlparse(url)
        return (
            p.scheme == "https"
            and (p.hostname or "").lower() == ALLOWED_ARCHIVE_HOST
            and Path(p.path).name == filename
        )
    except Exception:
        return False


def head_archive(url: str, filename: str) -> tuple[int, str]:
    last: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C9-D0-v0.2",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                cl = resp.headers.get("Content-Length")
            if status != 200:
                fail(f"funding archive HEAD HTTP {status}: {filename}")
            if not trusted_archive_url(final, filename):
                fail(f"funding archive HEAD identity mismatch: {filename} -> {final}")
            if not cl or not cl.isdigit() or int(cl) <= 0:
                fail(f"funding archive Content-Length invalid: {filename}")
            return int(cl), final
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(
        f"funding archive HEAD failed {filename}: {type(last).__name__}: {last}"
    )


def funding_archive_metadata(uly: str, year: int, month: int) -> dict:
    begin, end = month_bounds_utc8_ms(year, month)
    obj, final, nbytes = request_json(
        "/api/v5/public/market-data-history",
        {
            "module": "3",
            "instType": "SWAP",
            "instFamilyList": uly,
            "dateAggrType": "monthly",
            "begin": str(begin),
            "end": str(end),
        },
    )

    files: dict[str, dict] = {}
    for node in walk_file_nodes(obj.get("data")):
        filename = node.get("filename") or node.get("fileName")
        url = node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
        if not isinstance(filename, str) or not isinstance(url, str):
            continue
        if not trusted_archive_url(url, filename):
            fail(f"untrusted funding archive URL: {filename} {url}")
        prev = files.get(filename)
        if prev is not None and prev["url"] != url:
            fail(f"conflicting funding archive URLs: {filename}")
        files[filename] = {"filename": filename, "url": url}

    if not files:
        fail(f"no funding archive metadata returned uly={uly} {year}-{month:02d}")

    checked: list[dict] = []
    for filename in sorted(files):
        meta = files[filename]
        size, final_url = head_archive(meta["url"], filename)
        checked.append(
            {
                "filename": filename,
                "host": urllib.parse.urlparse(final_url).hostname,
                "content_length": size,
                "body_downloaded": False,
                "body_opened": False,
            }
        )

    return {
        "archive_month_utc8": f"{year}-{month:02d}",
        "query_begin_ms": begin,
        "query_end_ms": end,
        "file_count": len(checked),
        "files": checked,
        "api_response_bytes": nbytes,
        "api_final_url_host": urllib.parse.urlparse(final).hostname,
        "metadata_pass": bool(checked),
    }


def candle_window(endpoint: str, inst_id: str, start: str, end: str) -> dict:
    lo = date_ms(start)
    hi = date_ms(next_day(end))

    obj, final, nbytes = request_json(
        endpoint,
        {
            "instId": inst_id,
            "after": str(hi),
            "bar": BAR,
            "limit": "100",
        },
    )

    raw_rows = obj.get("data") or []
    ts: list[int] = []
    all_confirmed = True
    numeric_positive = True
    schema_width_valid = True

    for row in raw_rows:
        if not isinstance(row, list) or len(row) < 6:
            schema_width_valid = False
            continue
        try:
            t = int(row[0])
            vals = [float(row[i]) for i in range(1, 5)]
        except Exception:
            numeric_positive = False
            continue
        if not all(math.isfinite(v) and v > 0 for v in vals):
            numeric_positive = False
        if lo <= t < hi:
            ts.append(t)
            if str(row[-1]) != "1":
                all_confirmed = False

    ts = sorted(set(ts))
    utc_4h_alignment = all(t % (4 * 3_600_000) == 0 for t in ts)
    expected = {lo + i * 4 * 3_600_000 for i in range(EXPECTED_4H_ROWS)}
    missing = expected - set(ts)

    pass_semantics = (
        len(ts) >= MIN_4H_ROWS
        and all_confirmed
        and numeric_positive
        and schema_width_valid
        and utc_4h_alignment
    )

    return {
        "row_count": len(ts),
        "expected_4h_rows": EXPECTED_4H_ROWS,
        "missing_4h_rows": len(missing),
        "first_ts": ts[0] if ts else None,
        "last_ts": ts[-1] if ts else None,
        "all_confirmed": all_confirmed,
        "ohlc_numeric_positive_validated_not_stored": numeric_positive,
        "schema_width_valid": schema_width_valid,
        "utc_4h_alignment": utc_4h_alignment,
        "timestamp_set": ts,
        "response_bytes": nbytes,
        "api_final_url_host": urllib.parse.urlparse(final).hostname,
        "semantics_pass": pass_semantics,
    }


def main() -> int:
    require_freeze()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    assets: dict[str, dict] = {}
    all_pass = True
    total_http_response_bytes = 0
    total_archive_bytes_by_head = 0

    for ai, inst in enumerate(SWAPS, start=1):
        print(f"=== C9-D0-v0.2 [{ai}/8] {inst} ===", flush=True)

        try:
            meta = instrument_meta(inst)
            uly = str(meta["uly"])
            total_http_response_bytes += int(meta["response_bytes"])

            funding_meta = {}
            for label, year, month in ARCHIVE_MONTHS:
                print(
                    f"{inst} {label}: funding archive metadata module=3 uly={uly}",
                    flush=True,
                )
                fm = funding_archive_metadata(uly, year, month)
                funding_meta[label] = fm
                total_http_response_bytes += int(fm["api_response_bytes"])
                total_archive_bytes_by_head += sum(
                    int(x["content_length"]) for x in fm["files"]
                )
                print(
                    f"C9-D0-v0.2 {inst} {label} "
                    f"funding_files={fm['file_count']} "
                    f"metadata_pass={fm['metadata_pass']}",
                    flush=True,
                )

            windows = {}
            asset_pass = all(x["metadata_pass"] for x in funding_meta.values())

            for label, start, end in PERF_WINDOWS:
                print(f"{inst} {label}: mark/index 4H semantics", flush=True)
                mark = candle_window(
                    "/api/v5/market/history-mark-price-candles",
                    inst,
                    start,
                    end,
                )
                index = candle_window(
                    "/api/v5/market/history-index-candles",
                    uly,
                    start,
                    end,
                )
                total_http_response_bytes += (
                    int(mark["response_bytes"]) + int(index["response_bytes"])
                )

                mark_ts = set(mark.pop("timestamp_set"))
                index_ts = set(index.pop("timestamp_set"))
                aligned = len(mark_ts & index_ts)
                alignment_pass = aligned >= MIN_4H_ROWS
                window_pass = (
                    bool(mark["semantics_pass"])
                    and bool(index["semantics_pass"])
                    and alignment_pass
                )
                asset_pass = asset_pass and window_pass
                windows[label] = {
                    "start": start,
                    "end": end,
                    "mark_4h": mark,
                    "index_4h": index,
                    "mark_index_aligned_4h_rows": aligned,
                    "mark_index_alignment_pass": alignment_pass,
                    "window_pass": window_pass,
                }

                print(
                    f"C9-D0-v0.2 {inst} {label} "
                    f"mark={mark['row_count']} "
                    f"index={index['row_count']} "
                    f"aligned={aligned} "
                    f"pass={window_pass}",
                    flush=True,
                )

            assets[inst] = {
                "instrument": meta,
                "funding_archive_metadata": funding_meta,
                "mark_index_windows": windows,
                "asset_pass": asset_pass,
            }
            all_pass = all_pass and asset_pass

        except Exception as exc:
            all_pass = False
            assets[inst] = {
                "asset_pass": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
            print(
                f"C9-D0-v0.2 REVIEW {inst}: {type(exc).__name__}: {exc}",
                flush=True,
            )

    status = PASS if all_pass and len(assets) == 8 else REVIEW

    rep = {
        "stage": STAGE,
        "version": "0.2",
        "status": status,
        "venue": "OKX",
        "funding_source": "market-data-history module=3 monthly metadata/HEAD only",
        "mark_index_source": "OKX historical mark/index 4H REST",
        "probe_universe": list(SWAPS),
        "assets": assets,
        "assets_passed": sum(
            1 for x in assets.values() if x.get("asset_pass") is True
        ),
        "total_http_response_bytes": total_http_response_bytes,
        "total_funding_archive_bytes_by_head_not_downloaded": total_archive_bytes_by_head,
        "historical_funding_body_downloaded": False,
        "historical_funding_body_opened": False,
        "funding_values_used_for_strategy": False,
        "mark_index_prices_used_for_strategy": False,
        "returns_calculated": False,
        "basis_transition_calculated": False,
        "strategy_signal_calculated": False,
        "sentinel_outcome_calculated": False,
        "pnl_calculated": False,
        "direction_selected": False,
        "threshold_selected": False,
        "event_window_selected": False,
        "protected_market_body_accessed": False,
        "promotional_alpha_accessed": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(OUT, rep)

    print(status)
    print("assets_passed =", rep["assets_passed"], "/ 8")
    print(
        "funding archive bytes by HEAD (not downloaded) =",
        total_archive_bytes_by_head,
    )
    print("historical funding body downloaded/opened = False / False")
    print("returns/basis-transition/signal/sentinel/PnL = False")
    print("direction/threshold/event-window selected = False")
    print("protected/promotional market body accessed = False")
    print("report =", OUT)
    return 0 if status == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
