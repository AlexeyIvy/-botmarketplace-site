from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

STAGE = "SC001-C9-D1-V0.3-SEPTEMBER-FUNDING-ARCHIVE-INTEGRITY"
PASS = "C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_PASS"
REVIEW = "C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_REVIEW"

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
ALLOWED_ARCHIVE_HOST = "static.okx.com"
ASSETS = ("BTC", "ETH", "DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
SWAPS = tuple(f"{s}-USDT-SWAP" for s in ASSETS)

SOURCE_START_MS = 1725120000000  # 2024-08-31T16:00:00Z
SOURCE_END_MS = 1727712000000    # 2024-09-30T16:00:00Z inclusive exact boundary
ARCHIVE_YEAR = 2024
ARCHIVE_MONTH = 9

TIMEOUT = 60
RETRIES = 3
MAX_JSON_BYTES = 4_000_000
MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_TOTAL_ARCHIVE_BYTES = 200 * 1024 * 1024
CHUNK = 1024 * 1024

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c9-d1-september-funding-archive-integrity-protocol-v0.3.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.8.json"
FREEZE = ROOT / "docs/research/sc001-c9-d1-v0.3-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D0_REPORT = (
    DATA_ROOT
    / "SC001_C9_D0_V02_DATA_SEMANTICS"
    / "sc001_c9_d0_v02_data_semantics_report_v0_1.json"
)

# Reuse only the exact September files already downloaded by prior attempts.
# The sibling October files are deliberately never enumerated or opened by v0.3.
ARCHIVE_DIR = DATA_ROOT / "SC001_C9_D1_FUNDING_ARCHIVE" / "archives"

OUT_DIR = DATA_ROOT / "SC001_C9_D1_V03_FUNDING_ARCHIVE"
OUT = OUT_DIR / "sc001_c9_d1_v03_funding_archive_integrity_report_v0_1.json"


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


def exact_september_filename(inst: str) -> str:
    return f"{inst}-fundingrates-2024-09.zip"


def require_freeze() -> dict:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_C9_D1_V03_RUN":
        fail("C9-D1 v0.3 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C9-D1 v0.3 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C9-D1 v0.3 protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("C9-D1 v0.3 contamination registry identity mismatch")
    if tuple(fr.get("probe_universe") or ()) != SWAPS:
        fail("C9-D1 v0.3 frozen universe mismatch")
    if fr.get("source_archive_month") != "2024-09":
        fail("C9-D1 v0.3 source archive month mismatch")
    if fr.get("exact_filename_rule") != "INST-fundingrates-2024-09.zip":
        fail("C9-D1 v0.3 exact filename rule mismatch")

    for key in (
        "mark_index_values_authorized",
        "returns_authorized",
        "basis_transition_authorized",
        "strategy_signal_authorized",
        "sentinel_outcome_authorized",
        "pnl_authorized",
        "direction_selection_authorized",
        "threshold_selection_authorized",
        "event_window_selection_authorized",
        "october_funding_body_authorized_by_v03",
        "promotional_alpha_authorized",
    ):
        if fr.get(key) is not False:
            fail(f"C9-D1 v0.3 freeze firewall mismatch: {key}")

    if fr.get("prior_october_funding_contamination_known") is not True:
        fail("C9-D1 v0.3 freeze must acknowledge prior October funding contamination")

    return fr


def require_registry() -> dict:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.8":
        fail("contamination registry version mismatch")

    c9 = reg.get("c9_d1_selection_calibration") or {}
    sep = c9.get("september_funding_archive") or {}
    octo = c9.get("october_funding_archive") or {}

    if sep.get("classification") != "NONPROMOTIONAL_SELECTION_CALIBRATION":
        fail("September C9 funding classification mismatch")
    if sep.get("source_archive_month") != "2024-09":
        fail("September C9 source month mismatch")
    if sep.get("body_access_authorized") is not True:
        fail("September C9 body access not authorized")

    if octo.get("body_access_occurred") is not True:
        fail("registry must acknowledge prior October funding body access")
    if octo.get("clean_c9_confirmation_eligibility") is not False:
        fail("October C9 funding must not remain clean Confirmation evidence")

    return reg


def require_d0_parent() -> dict:
    rep = load_json(D0_REPORT)
    if rep.get("status") != "C9_D0_V02_DATA_SEMANTICS_PASS":
        fail("C9-D0 v0.2 parent not exact PASS")
    if int(rep.get("assets_passed", 0)) != 8:
        fail("C9-D0 v0.2 assets_passed mismatch")

    for key in (
        "historical_funding_body_downloaded",
        "historical_funding_body_opened",
        "funding_values_used_for_strategy",
        "mark_index_prices_used_for_strategy",
        "returns_calculated",
        "basis_transition_calculated",
        "strategy_signal_calculated",
        "sentinel_outcome_calculated",
        "pnl_calculated",
        "direction_selected",
        "threshold_selected",
        "event_window_selected",
        "protected_market_body_accessed",
        "promotional_alpha_accessed",
    ):
        if rep.get(key) is not False:
            fail(f"C9-D0 v0.2 parent firewall mismatch: {key}")

    return rep


def month_bounds_utc8_ms(year: int, month: int) -> tuple[int, int]:
    tz8 = timezone(timedelta(hours=8))
    start_local = datetime(year, month, 1, tzinfo=tz8)
    if month == 12:
        end_local = datetime(year + 1, 1, 1, tzinfo=tz8)
    else:
        end_local = datetime(year, month + 1, 1, tzinfo=tz8)
    return int(start_local.timestamp() * 1000), int(end_local.timestamp() * 1000)


def request_json(path: str, params: dict[str, str]) -> dict:
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
                        "User-Agent": "BotMarketplace-SC001-C9-D1-v0.3",
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
                return obj

            except Exception as exc:
                last = exc
                if attempt < RETRIES:
                    time.sleep(float(attempt))

    raise RuntimeError(f"request failed {path}: {type(last).__name__}: {last}")


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


def all_metadata_files(uly: str) -> dict[str, dict]:
    begin, end = month_bounds_utc8_ms(ARCHIVE_YEAR, ARCHIVE_MONTH)
    if begin != SOURCE_START_MS or end != SOURCE_END_MS:
        fail("internal September UTC+8 boundary mismatch")

    obj = request_json(
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
            fail(f"untrusted archive URL: {filename} {url}")
        prev = files.get(filename)
        if prev is not None and prev["url"] != url:
            fail(f"conflicting archive URLs: {filename}")
        files[filename] = {"filename": filename, "url": url}

    if not files:
        fail(f"no funding archive metadata returned for {uly}")
    return files


def select_exact_september_current(inst: str, uly: str) -> dict:
    target = exact_september_filename(inst)
    files = all_metadata_files(uly)

    if target not in files:
        fail(f"exact September funding file not returned for {inst}: {target}")

    # Important: do not HEAD/download/open any non-target file.
    return files[target]


def expected_d0_september(parent: dict, inst: str) -> tuple[str, int]:
    asset = (parent.get("assets") or {}).get(inst)
    if not isinstance(asset, dict):
        fail(f"D0 asset missing: {inst}")

    meta = (asset.get("funding_archive_metadata") or {}).get("SEPTEMBER")
    if not isinstance(meta, dict) or meta.get("metadata_pass") is not True:
        fail(f"D0 September metadata not PASS: {inst}")

    target = exact_september_filename(inst)
    matches = []

    for row in meta.get("files") or []:
        if not isinstance(row, dict):
            continue
        if row.get("filename") == target:
            matches.append(row)

    if len(matches) != 1:
        fail(f"D0 exact September file count mismatch {inst}: {len(matches)}")

    row = matches[0]
    size = row.get("content_length")
    host = row.get("host")

    if not isinstance(size, int) or size <= 0:
        fail(f"D0 September Content-Length invalid: {inst}")
    if host != ALLOWED_ARCHIVE_HOST:
        fail(f"D0 September archive host mismatch: {inst} {host}")

    return target, size


def head_size(url: str, filename: str) -> int:
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={
            "User-Agent": "BotMarketplace-SC001-C9-D1-v0.3",
            "Referer": "https://www.okx.com/historical-data",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        status = int(getattr(resp, "status", 200))
        final = resp.geturl()
        cl = resp.headers.get("Content-Length")

    if status != 200:
        fail(f"HEAD HTTP {status}: {filename}")
    if not trusted_archive_url(final, filename):
        fail(f"HEAD archive identity mismatch: {filename}")
    if not cl or not cl.isdigit() or int(cl) <= 0:
        fail(f"invalid Content-Length: {filename}")

    return int(cl)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_or_reuse_exact_september(
    inst: str,
    meta: dict,
    expected_size: int,
) -> tuple[Path, bool]:
    filename = exact_september_filename(inst)

    if meta.get("filename") != filename:
        fail(f"download metadata filename not exact September target: {inst}")

    if expected_size > MAX_ARCHIVE_BYTES:
        fail(f"September archive exceeds per-file cap: {filename} {expected_size}")

    asset_dir = ARCHIVE_DIR / inst.replace("-USDT-SWAP", "")
    asset_dir.mkdir(parents=True, exist_ok=True)
    dest = asset_dir / filename

    if dest.exists() and dest.stat().st_size == expected_size:
        return dest, True

    if dest.exists():
        dest.unlink()

    tmp = Path(str(dest) + ".part")
    tmp.unlink(missing_ok=True)

    req = urllib.request.Request(
        meta["url"],
        method="GET",
        headers={
            "User-Agent": "BotMarketplace-SC001-C9-D1-v0.3",
            "Referer": "https://www.okx.com/historical-data",
        },
    )

    got = 0
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp, tmp.open("wb") as out:
        status = int(getattr(resp, "status", 200))
        final = resp.geturl()

        if status != 200:
            fail(f"GET HTTP {status}: {filename}")
        if not trusted_archive_url(final, filename):
            fail(f"GET exact September archive identity mismatch: {filename}")

        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            got += len(chunk)
            if got > expected_size or got > MAX_ARCHIVE_BYTES:
                fail(f"September archive download size overflow: {filename}")
            out.write(chunk)

        out.flush()
        os.fsync(out.fileno())

    if got != expected_size:
        fail(f"September archive download size mismatch {filename}: {got} != {expected_size}")

    os.replace(tmp, dest)
    return dest, False


def finite_decimal(text: str) -> Decimal:
    try:
        x = Decimal(str(text).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"invalid decimal {text!r}") from exc
    if not x.is_finite():
        raise ValueError(f"nonfinite decimal {text!r}")
    return x


def parse_exact_september_rows(path: Path, inst: str) -> list[tuple[int, str]]:
    if path.name != exact_september_filename(inst):
        fail(f"refusing to open non-September funding body: {path.name}")

    rows: list[tuple[int, str]] = []

    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {path.name}: {bad}")

        members = [x for x in zf.infolist() if not x.is_dir()]
        if not members:
            fail(f"September ZIP has no regular member: {path.name}")

        for info in members:
            if not info.filename.lower().endswith(".csv"):
                fail(f"non-CSV member in September funding ZIP: {path.name} {info.filename}")

            with zf.open(info, "r") as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))

                for fields in reader:
                    if not fields or len(fields) < 3:
                        continue
                    if fields[0] != inst:
                        continue

                    try:
                        rate = finite_decimal(fields[1])
                        ts = int(fields[2].strip())
                    except Exception as exc:
                        raise RuntimeError(
                            f"malformed target funding row {path.name}: {fields!r}"
                        ) from exc

                    if ts <= 0:
                        fail(f"invalid funding timestamp {path.name}: {ts}")
                    if ts < SOURCE_START_MS or ts > SOURCE_END_MS:
                        fail(
                            f"target funding timestamp outside exact September source interval "
                            f"{inst}: {ts}"
                        )

                    rows.append((ts, format(rate, "f")))

    return rows


def qualify_instrument(inst: str, parent: dict) -> dict:
    asset = (parent.get("assets") or {}).get(inst)
    uly = ((asset or {}).get("instrument") or {}).get("uly")

    if not isinstance(uly, str) or not uly:
        fail(f"D0 uly missing: {inst}")

    expected_filename, expected_size = expected_d0_september(parent, inst)
    current_meta = select_exact_september_current(inst, uly)

    if current_meta["filename"] != expected_filename:
        fail(f"current exact September filename mismatch: {inst}")

    size_now = head_size(current_meta["url"], expected_filename)
    if size_now != expected_size:
        fail(
            f"September HEAD size mismatch {inst} {expected_filename}: "
            f"{size_now} != {expected_size}"
        )

    path, reused = download_or_reuse_exact_september(
        inst,
        current_meta,
        expected_size,
    )

    digest = sha256_file(path)
    combined = parse_exact_september_rows(path, inst)

    by_ts: dict[int, str] = {}
    for ts, rate in combined:
        prev = by_ts.get(ts)
        if prev is not None and prev != rate:
            fail(f"conflicting duplicate September funding value {inst} at {ts}")
        by_ts[ts] = rate

    ts = sorted(by_ts)

    if len(ts) < 80:
        fail(f"insufficient unique September funding timestamps {inst}: {len(ts)}")

    intervals_ms = [b - a for a, b in zip(ts, ts[1:])]
    if any(x <= 0 for x in intervals_ms):
        fail(f"nonpositive September funding interval {inst}")

    max_interval_ms = max(intervals_ms) if intervals_ms else None
    if max_interval_ms is None or max_interval_ms > 8 * 3_600_000:
        fail(f"September funding interval gap >8h {inst}: {max_interval_ms}")

    if ts[0] - SOURCE_START_MS > 8 * 3_600_000:
        fail(f"September funding start coverage gap >8h {inst}")

    if SOURCE_END_MS - ts[-1] > 8 * 3_600_000:
        fail(f"September funding end coverage gap >8h {inst}")

    interval_hours = sorted({round(x / 3_600_000, 6) for x in intervals_ms})

    nbytes = path.stat().st_size

    return {
        "instrument": inst,
        "uly": uly,
        "archive_filename": expected_filename,
        "archive_bytes": nbytes,
        "archive_sha256": digest,
        "archive_reused": reused,
        "unique_funding_timestamps": len(ts),
        "first_funding_time_ms": ts[0],
        "last_funding_time_ms": ts[-1],
        "observed_interval_hours": interval_hours,
        "maximum_interval_hours": max(interval_hours) if interval_hours else None,
        "funding_values_validated_not_stored": True,
        "integrity_pass": True,
    }


def main() -> int:
    try:
        require_freeze()
        require_registry()
        parent = require_d0_parent()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        assets = {}
        all_pass = True
        total_bytes = 0
        reused_files = 0
        downloaded_files = 0

        for i, inst in enumerate(SWAPS, start=1):
            print(f"C9-D1-v0.3 [{i}/8] {inst}", flush=True)

            try:
                rep = qualify_instrument(inst, parent)
                assets[inst] = rep
                total_bytes += int(rep["archive_bytes"])
                reused_files += int(bool(rep["archive_reused"]))
                downloaded_files += int(not bool(rep["archive_reused"]))

                print(
                    f"PASS {inst} "
                    f"rows={rep['unique_funding_timestamps']} "
                    f"intervals={rep['observed_interval_hours']} "
                    f"file={rep['archive_filename']} "
                    f"reused={rep['archive_reused']}",
                    flush=True,
                )

            except Exception as exc:
                all_pass = False
                assets[inst] = {
                    "integrity_pass": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print(
                    f"REVIEW {inst}: {type(exc).__name__}: {exc}",
                    flush=True,
                )

        if total_bytes > MAX_TOTAL_ARCHIVE_BYTES:
            fail("total exact-September qualified archive bytes exceed safety cap")

        status = PASS if all_pass and len(assets) == 8 else REVIEW

        rep = {
            "stage": STAGE,
            "version": "0.3",
            "status": status,
            "source_archive_month": "2024-09",
            "source_interval_utc": {
                "start_inclusive_ms": SOURCE_START_MS,
                "end_boundary_inclusive_ms": SOURCE_END_MS,
            },
            "selection_calibration_role": "NONPROMOTIONAL_SELECTION_CALIBRATION",
            "probe_universe": list(SWAPS),
            "assets": assets,
            "assets_passed": sum(
                1 for x in assets.values() if x.get("integrity_pass") is True
            ),
            "qualified_total_bytes": total_bytes,
            "reused_files": reused_files,
            "downloaded_files": downloaded_files,
            "exact_filename_rule": "INST-fundingrates-2024-09.zip",
            "october_funding_body_accessed_by_v03": False,
            "prior_october_funding_contamination_known": True,
            "october_funding_clean_c9_confirmation_eligible": False,
            "mark_index_values_opened_by_v03": False,
            "funding_values_used_for_strategy": False,
            "returns_calculated": False,
            "basis_transition_calculated": False,
            "strategy_signal_calculated": False,
            "sentinel_outcome_calculated": False,
            "pnl_calculated": False,
            "direction_selected": False,
            "threshold_selected": False,
            "event_window_selected": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, rep)

        print(status)
        print("assets_passed =", rep["assets_passed"], "/ 8")
        print("qualified_total_bytes =", total_bytes)
        print("reused_files =", reused_files, "downloaded_files =", downloaded_files)
        print("October funding body accessed by v0.3 = False")
        print("prior October funding contamination known = True")
        print("October funding clean C9 Confirmation eligible = False")
        print("returns/basis-transition/signal/sentinel/PnL = False")
        print("direction/threshold/event-window selected = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)

        return 0 if status == PASS else 2

    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "version": "0.3",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "october_funding_body_accessed_by_v03": False,
            "prior_october_funding_contamination_known": True,
            "october_funding_clean_c9_confirmation_eligible": False,
            "mark_index_values_opened_by_v03": False,
            "funding_values_used_for_strategy": False,
            "returns_calculated": False,
            "basis_transition_calculated": False,
            "strategy_signal_calculated": False,
            "sentinel_outcome_calculated": False,
            "pnl_calculated": False,
            "direction_selected": False,
            "threshold_selected": False,
            "event_window_selected": False,
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
