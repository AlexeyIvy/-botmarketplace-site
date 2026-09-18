from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

STAGE = "SC001-C9-D2-MARK-INDEX-15M-INTEGRITY-V0.1"
PASS = "C9_D2_MARK_INDEX_15M_INTEGRITY_PASS"
REVIEW = "C9_D2_MARK_INDEX_15M_INTEGRITY_REVIEW"

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
ASSETS = ("BTC", "ETH", "DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
SWAPS = tuple(f"{s}-USDT-SWAP" for s in ASSETS)

BAR = "15m"
BAR_MS = 15 * 60 * 1000
START_MS = 1725062400000   # 2024-08-31T00:00:00Z
END_MS = 1727740800000     # 2024-10-01T00:00:00Z exclusive
EXPECTED_ROWS = 31 * 24 * 4

TIMEOUT = 45
RETRIES = 3
MAX_JSON_BYTES = 4_000_000
MAX_PAGES = 40
PAGE_LIMIT = 100

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c9-d2-mark-index-15m-acquisition-integrity-protocol-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.9.json"
FREEZE = ROOT / "docs/research/sc001-c9-d2-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D0_REPORT = (
    DATA_ROOT
    / "SC001_C9_D0_V02_DATA_SEMANTICS"
    / "sc001_c9_d0_v02_data_semantics_report_v0_1.json"
)
D1_REPORT = (
    DATA_ROOT
    / "SC001_C9_D1_V03_FUNDING_ARCHIVE"
    / "sc001_c9_d1_v03_funding_archive_integrity_report_v0_1.json"
)

OUT_DIR = DATA_ROOT / "SC001_C9_D2_MARK_INDEX_15M"
NORMALIZED_DIR = OUT_DIR / "normalized"
OUT = OUT_DIR / "sc001_c9_d2_mark_index_15m_integrity_report_v0_1.json"


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_freeze() -> dict:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_C9_D2_RUN":
        fail("C9-D2 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C9-D2 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C9-D2 protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("C9-D2 contamination registry identity mismatch")
    if tuple(fr.get("probe_universe") or ()) != SWAPS:
        fail("C9-D2 universe mismatch")
    if fr.get("bar") != BAR:
        fail("C9-D2 bar mismatch")
    if int(fr.get("expected_rows_per_source", 0)) != EXPECTED_ROWS:
        fail("C9-D2 expected row count mismatch")

    for key in (
        "returns_authorized",
        "premium_authorized",
        "state_transition_outcome_authorized",
        "strategy_signal_authorized",
        "sentinel_outcome_authorized",
        "pnl_authorized",
        "direction_selection_authorized",
        "threshold_selection_authorized",
        "event_window_selection_authorized",
        "october_utc_mark_index_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(key) is not False:
            fail(f"C9-D2 freeze firewall mismatch: {key}")
    return fr


def require_registry() -> dict:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.9":
        fail("contamination registry version mismatch")
    row = reg.get("c9_d2_mark_index_selection_calibration") or {}
    if row.get("classification") != "NONPROMOTIONAL_SELECTION_CALIBRATION":
        fail("C9-D2 calibration classification mismatch")
    if tuple(row.get("assets") or ()) != ASSETS:
        fail("C9-D2 registry asset mismatch")
    window = row.get("utc_window") or {}
    if window.get("start_inclusive") != "2024-08-31T00:00:00Z":
        fail("C9-D2 registry start mismatch")
    if window.get("end_exclusive") != "2024-10-01T00:00:00Z":
        fail("C9-D2 registry end mismatch")
    return reg


def require_parents() -> tuple[dict, dict]:
    d0 = load_json(D0_REPORT)
    if d0.get("status") != "C9_D0_V02_DATA_SEMANTICS_PASS":
        fail("C9-D0 parent not exact PASS")
    if int(d0.get("assets_passed", 0)) != 8:
        fail("C9-D0 assets_passed mismatch")

    d1 = load_json(D1_REPORT)
    if d1.get("status") != "C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_PASS":
        fail("C9-D1 v0.3 parent not exact PASS")
    if int(d1.get("assets_passed", 0)) != 8:
        fail("C9-D1 assets_passed mismatch")
    if d1.get("october_funding_body_accessed_by_v03") is not False:
        fail("C9-D1 v0.3 October access firewall mismatch")
    if d1.get("prior_october_funding_contamination_known") is not True:
        fail("C9-D1 prior October incident acknowledgement mismatch")
    if d1.get("october_funding_clean_c9_confirmation_eligible") is not False:
        fail("C9-D1 October confirmation eligibility mismatch")

    for key in (
        "funding_values_used_for_strategy",
        "returns_calculated",
        "basis_transition_calculated",
        "strategy_signal_calculated",
        "sentinel_outcome_calculated",
        "pnl_calculated",
        "direction_selected",
        "threshold_selected",
        "event_window_selected",
        "promotional_alpha_accessed",
    ):
        if d1.get(key) is not False:
            fail(f"C9-D1 parent firewall mismatch: {key}")

    return d0, d1


def request_json(path: str, params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    last: Exception | None = None

    for domain in DOMAINS:
        url = domain + path + "?" + query
        for attempt in range(1, RETRIES + 1):
            try:
                req = urllib.request.Request(
                    url,
                    method="GET",
                    headers={
                        "User-Agent": "BotMarketplace-SC001-C9-D2/0.1",
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


def finite_decimal(text: str) -> Decimal:
    try:
        x = Decimal(str(text).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"invalid decimal {text!r}") from exc
    if not x.is_finite() or x <= 0:
        raise ValueError(f"nonpositive/nonfinite decimal {text!r}")
    return x


def parse_candle_row(row: object, source: str) -> tuple[int, tuple[str, str, str, str]]:
    if not isinstance(row, list) or len(row) < 6:
        fail(f"{source} candle row shape invalid")

    try:
        ts = int(row[0])
        o = finite_decimal(row[1])
        h = finite_decimal(row[2])
        l = finite_decimal(row[3])
        c = finite_decimal(row[4])
    except Exception as exc:
        raise RuntimeError(f"{source} candle parse failure") from exc

    if str(row[-1]) != "1":
        fail(f"{source} unconfirmed historical candle at {ts}")

    if h < o or h < c or h < l:
        fail(f"{source} invalid high at {ts}")
    if l > o or l > c or l > h:
        fail(f"{source} invalid low at {ts}")

    if ts % BAR_MS != 0:
        fail(f"{source} timestamp not UTC 15m aligned: {ts}")

    return ts, (format(o, "f"), format(h, "f"), format(l, "f"), format(c, "f"))


def fetch_source(endpoint: str, inst_id: str, source_name: str) -> dict[int, tuple[str, str, str, str]]:
    out: dict[int, tuple[str, str, str, str]] = {}

    # Start just before the protected October boundary so an inclusive endpoint
    # cannot return the 2024-10-01 00:00 UTC candle.
    anchor = END_MS - 1

    for page_no in range(1, MAX_PAGES + 1):
        obj = request_json(
            endpoint,
            {
                "instId": inst_id,
                "after": str(anchor),
                "bar": BAR,
                "limit": str(PAGE_LIMIT),
            },
        )
        rows = obj.get("data") or []
        if not rows:
            break

        page_ts: list[int] = []

        for raw in rows:
            ts, vals = parse_candle_row(raw, source_name)
            page_ts.append(ts)

            if ts >= END_MS:
                fail(f"{source_name} October UTC candle returned: {ts}")

            if START_MS <= ts < END_MS:
                prev = out.get(ts)
                if prev is not None and prev != vals:
                    fail(f"{source_name} conflicting duplicate candle: {ts}")
                out[ts] = vals

        if not page_ts:
            break

        oldest = min(page_ts)
        if oldest <= START_MS:
            break

        new_anchor = oldest - 1
        if new_anchor >= anchor:
            fail(f"{source_name} pagination did not move backward")

        anchor = new_anchor
    else:
        fail(f"{source_name} exceeded pagination cap")

    return out


def write_normalized(asset: str, mark: dict, index: dict) -> dict:
    common = sorted(set(mark) & set(index))
    if len(common) != EXPECTED_ROWS:
        fail(f"{asset} common row count {len(common)} != {EXPECTED_ROWS}")
    if set(mark) != set(index):
        fail(f"{asset} mark/index timestamp sets differ")

    expected = [START_MS + i * BAR_MS for i in range(EXPECTED_ROWS)]
    if common != expected:
        missing = len(set(expected) - set(common))
        extra = len(set(common) - set(expected))
        fail(f"{asset} 15m grid mismatch missing={missing} extra={extra}")

    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    path = NORMALIZED_DIR / f"{asset}_mark_index_15m.csv"
    tmp = Path(str(path) + ".tmp")

    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "ts_ms",
            "mark_open", "mark_high", "mark_low", "mark_close",
            "index_open", "index_high", "index_low", "index_close",
            "confirmed",
        ])
        for ts in common:
            mo, mh, ml, mc = mark[ts]
            io, ih, il, ic = index[ts]
            w.writerow([ts, mo, mh, ml, mc, io, ih, il, ic, "1"])
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp, path)

    return {
        "path": str(path),
        "rows": len(common),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "first_ts_ms": common[0],
        "last_ts_ms": common[-1],
    }


def main() -> int:
    try:
        require_freeze()
        require_registry()
        d0, _d1 = require_parents()

        OUT_DIR.mkdir(parents=True, exist_ok=True)

        assets = {}
        all_pass = True

        for i, inst in enumerate(SWAPS, start=1):
            asset = inst.split("-")[0]
            print(f"C9-D2 [{i}/8] {inst}", flush=True)

            try:
                d0_asset = (d0.get("assets") or {}).get(inst)
                uly = ((d0_asset or {}).get("instrument") or {}).get("uly")
                if not isinstance(uly, str) or not uly:
                    fail(f"D0 uly missing: {inst}")

                print(f"{inst}: fetch mark {BAR}", flush=True)
                mark = fetch_source(
                    "/api/v5/market/history-mark-price-candles",
                    inst,
                    f"{inst} mark",
                )

                print(f"{inst}: fetch index {BAR} uly={uly}", flush=True)
                index = fetch_source(
                    "/api/v5/market/history-index-candles",
                    uly,
                    f"{inst} index",
                )

                if len(mark) != EXPECTED_ROWS:
                    fail(f"{inst} mark rows {len(mark)} != {EXPECTED_ROWS}")
                if len(index) != EXPECTED_ROWS:
                    fail(f"{inst} index rows {len(index)} != {EXPECTED_ROWS}")

                norm = write_normalized(asset, mark, index)

                assets[inst] = {
                    "uly": uly,
                    "mark_rows": len(mark),
                    "index_rows": len(index),
                    "aligned_rows": norm["rows"],
                    "normalized_file": norm,
                    "integrity_pass": True,
                }

                print(
                    f"PASS {inst} mark={len(mark)} index={len(index)} "
                    f"aligned={norm['rows']} sha256={norm['sha256'][:16]}...",
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

        status = PASS if all_pass and len(assets) == 8 else REVIEW

        rep = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "bar": BAR,
            "utc_window": {
                "start_inclusive_ms": START_MS,
                "end_exclusive_ms": END_MS,
            },
            "expected_rows_per_source": EXPECTED_ROWS,
            "probe_universe": list(SWAPS),
            "assets": assets,
            "assets_passed": sum(
                1 for x in assets.values() if x.get("integrity_pass") is True
            ),
            "selection_calibration_role": "NONPROMOTIONAL_SELECTION_CALIBRATION",
            "mark_index_values_opened_by_d2": True,
            "mark_index_values_used_for_strategy": False,
            "funding_values_opened_by_d2": False,
            "premium_calculated": False,
            "returns_calculated": False,
            "state_transition_outcome_calculated": False,
            "strategy_signal_calculated": False,
            "sentinel_outcome_calculated": False,
            "pnl_calculated": False,
            "direction_selected": False,
            "threshold_selected": False,
            "event_window_selected": False,
            "october_utc_mark_index_accessed": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, rep)

        print(status)
        print("assets_passed =", rep["assets_passed"], "/ 8")
        print("expected_rows_per_source =", EXPECTED_ROWS)
        print("mark/index values opened by D2 = True")
        print("mark/index values used for strategy = False")
        print("funding values opened by D2 = False")
        print("premium/returns/state-transition/signal/sentinel/PnL = False")
        print("direction/threshold/event-window selected = False")
        print("October UTC mark/index accessed = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)

        return 0 if status == PASS else 2

    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "version": "0.1",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "mark_index_values_opened_by_d2": False,
            "mark_index_values_used_for_strategy": False,
            "funding_values_opened_by_d2": False,
            "premium_calculated": False,
            "returns_calculated": False,
            "state_transition_outcome_calculated": False,
            "strategy_signal_calculated": False,
            "sentinel_outcome_calculated": False,
            "pnl_calculated": False,
            "direction_selected": False,
            "threshold_selected": False,
            "event_window_selected": False,
            "october_utc_mark_index_accessed": False,
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
