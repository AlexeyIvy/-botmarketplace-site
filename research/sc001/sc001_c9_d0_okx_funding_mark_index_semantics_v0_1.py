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

STAGE = "SC001-C9-D0-OKX-FUNDING-MARK-INDEX-DATA-SEMANTICS-V0.1"
PASS = "C9_D0_DATA_SEMANTICS_PASS"
REVIEW = "C9_D0_DATA_SEMANTICS_REVIEW"

DOMAINS = ("https://www.okx.com", "https://us.okx.com")
ASSETS = ("BTC", "ETH", "DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
SWAPS = tuple(f"{s}-USDT-SWAP" for s in ASSETS)
WINDOWS = (
    ("JULY", "2024-07-01", "2024-07-14"),
    ("SEPTEMBER", "2024-09-01", "2024-09-14"),
)
BAR = "4H"
EXPECTED_4H_ROWS = 84
MIN_4H_ROWS = 80
MIN_FUNDING_ROWS = 30
TIMEOUT = 45
RETRIES = 3
MAX_BYTES = 4_000_000

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c9-d0-okx-funding-mark-index-data-semantics-protocol-v0.1.md"
FREEZE = ROOT / "docs/research/sc001-c9-d0-data-semantics-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_C9_D0_DATA_SEMANTICS"
OUT = OUT_DIR / "sc001_c9_d0_data_semantics_report_v0_1.json"


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
    if fr.get("status") != "FROZEN_BEFORE_C9_D0_RUN":
        fail("C9-D0 implementation freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C9-D0 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C9-D0 protocol identity mismatch")
    if tuple(fr.get("probe_universe") or ()) != SWAPS:
        fail("C9-D0 frozen probe universe mismatch")
    expected_windows = [
        {"label": label, "start": start, "end": end}
        for label, start, end in WINDOWS
    ]
    if fr.get("probe_windows") != expected_windows:
        fail("C9-D0 frozen probe windows mismatch")
    if fr.get("bar") != BAR:
        fail("C9-D0 frozen bar mismatch")
    for key in (
        "returns_authorized",
        "basis_transition_authorized",
        "strategy_signal_authorized",
        "sentinel_outcome_authorized",
        "pnl_authorized",
        "direction_selection_authorized",
        "threshold_selection_authorized",
        "event_window_selection_authorized",
        "protected_data_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(key) is not False:
            fail(f"C9-D0 freeze firewall mismatch: {key}")
    return fr


def date_ms(day: str) -> int:
    return int(
        datetime.strptime(day, "%Y-%m-%d")
        .replace(tzinfo=timezone.utc)
        .timestamp()
        * 1000
    )


def next_day(day: str) -> str:
    d = (
        datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        + timedelta(days=1)
    )
    return d.strftime("%Y-%m-%d")


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
                        "User-Agent": "BotMarketplace-SC001-C9-D0/0.1",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    raw = resp.read(MAX_BYTES + 1)
                    status = int(getattr(resp, "status", 200))
                    final = resp.geturl()

                if len(raw) > MAX_BYTES:
                    fail(f"response cap exceeded: {path}")
                if status != 200:
                    fail(f"HTTP {status}: {path}")

                parsed = urllib.parse.urlparse(final)
                if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {
                    "www.okx.com",
                    "us.okx.com",
                }:
                    fail(f"unexpected final URL identity: {final}")

                obj = json.loads(raw.decode("utf-8"))
                if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                    code = obj.get("code") if isinstance(obj, dict) else None
                    fail(f"OKX code mismatch path={path} code={code}")
                return obj, final, len(raw)

            except Exception as exc:
                last = exc
                if attempt < RETRIES:
                    time.sleep(float(attempt))

    raise RuntimeError(
        f"request failed {path}: {type(last).__name__}: {last}"
    )


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
        "ct_val_ccy": r.get("ctValCcy"),
        "api_final_url_host": urllib.parse.urlparse(final).hostname,
        "response_bytes": nbytes,
    }


def funding_window(inst: str, start: str, end: str) -> dict:
    lo = date_ms(start)
    hi = date_ms(next_day(end))

    # OKX 'after' returns records earlier than the supplied fundingTime.
    # 400 rows covers more than 14 days even at a 1h collection interval.
    obj, final, nbytes = request_json(
        "/api/v5/public/funding-rate-history",
        {"instId": inst, "after": str(hi), "limit": "400"},
    )

    raw_rows = obj.get("data") or []
    rows: list[dict] = []
    for r in raw_rows:
        if not isinstance(r, dict):
            fail(f"funding row non-object: {inst}")
        if r.get("instId") != inst:
            fail(f"funding instrument identity mismatch: {inst}")
        if r.get("instType") not in {"SWAP", "FUTURES"}:
            fail(f"funding instType mismatch: {inst} {r.get('instType')}")

        try:
            ts = int(r.get("fundingTime"))
            fr = float(r.get("fundingRate"))
            rr = float(r.get("realizedRate"))
        except Exception as exc:
            raise RuntimeError(f"funding parse failure {inst}") from exc

        if not (math.isfinite(fr) and math.isfinite(rr)):
            fail(f"nonfinite funding value: {inst} {ts}")

        if lo <= ts < hi:
            rows.append(
                {
                    "ts": ts,
                    "method": r.get("method"),
                    "formula_type": r.get("formulaType"),
                }
            )

    rows.sort(key=lambda x: x["ts"])
    ts = [int(x["ts"]) for x in rows]

    if len(ts) != len(set(ts)):
        fail(f"duplicate fundingTime: {inst} {start}")

    intervals_ms = [b - a for a, b in zip(ts, ts[1:])]
    intervals_h = sorted({round(x / 3_600_000, 6) for x in intervals_ms})
    positive = all(x > 0 for x in intervals_ms)
    max_interval_h = max(intervals_h) if intervals_h else None

    methods = sorted({str(x["method"]) for x in rows})
    formula_types = sorted({str(x["formula_type"]) for x in rows})

    pass_semantics = (
        len(rows) >= MIN_FUNDING_ROWS
        and positive
        and max_interval_h is not None
        and max_interval_h <= 8.0
        and all(x > 0 for x in intervals_h)
    )

    return {
        "row_count": len(rows),
        "first_ts": ts[0] if ts else None,
        "last_ts": ts[-1] if ts else None,
        "observed_interval_hours": intervals_h,
        "method_values": methods,
        "formula_type_values": formula_types,
        "numeric_fields_validated_not_stored": True,
        "response_bytes": nbytes,
        "api_final_url_host": urllib.parse.urlparse(final).hostname,
        "semantics_pass": pass_semantics,
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

    expected = {
        lo + i * 4 * 3_600_000
        for i in range(EXPECTED_4H_ROWS)
    }
    observed = set(ts)
    missing = sorted(expected - observed)

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

    if OUT.exists():
        old = load_json(OUT)
        if old.get("status") in {PASS, REVIEW}:
            fail(f"one-shot guard: terminal C9-D0 report already exists: {old.get('status')}")

    assets: dict[str, dict] = {}
    all_pass = True
    total_response_bytes = 0

    for ai, inst in enumerate(SWAPS, start=1):
        print(f"=== C9-D0 [{ai}/8] {inst} ===", flush=True)

        try:
            meta = instrument_meta(inst)
            uly = str(meta["uly"])
            windows: dict[str, dict] = {}
            asset_pass = True
            total_response_bytes += int(meta["response_bytes"])

            for label, start, end in WINDOWS:
                print(f"{inst} {label}: funding semantics", flush=True)
                funding = funding_window(inst, start, end)

                print(f"{inst} {label}: mark 4H semantics", flush=True)
                mark = candle_window(
                    "/api/v5/market/history-mark-price-candles",
                    inst,
                    start,
                    end,
                )

                print(
                    f"{inst} {label}: index 4H semantics uly={uly}",
                    flush=True,
                )
                index = candle_window(
                    "/api/v5/market/history-index-candles",
                    uly,
                    start,
                    end,
                )

                total_response_bytes += (
                    int(funding["response_bytes"])
                    + int(mark["response_bytes"])
                    + int(index["response_bytes"])
                )

                mark_ts = set(mark.pop("timestamp_set"))
                index_ts = set(index.pop("timestamp_set"))
                aligned = len(mark_ts & index_ts)
                alignment_pass = aligned >= MIN_4H_ROWS

                window_pass = (
                    bool(funding["semantics_pass"])
                    and bool(mark["semantics_pass"])
                    and bool(index["semantics_pass"])
                    and alignment_pass
                )
                asset_pass = asset_pass and window_pass

                windows[label] = {
                    "start": start,
                    "end": end,
                    "funding": funding,
                    "mark_4h": mark,
                    "index_4h": index,
                    "mark_index_aligned_4h_rows": aligned,
                    "mark_index_alignment_pass": alignment_pass,
                    "window_pass": window_pass,
                }

                print(
                    f"C9-D0 {inst} {label} "
                    f"funding={funding['row_count']} "
                    f"intervals={funding['observed_interval_hours']} "
                    f"mark={mark['row_count']} "
                    f"index={index['row_count']} "
                    f"aligned={aligned} "
                    f"pass={window_pass}",
                    flush=True,
                )

            assets[inst] = {
                "instrument": meta,
                "windows": windows,
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
                f"C9-D0 REVIEW {inst}: {type(exc).__name__}: {exc}",
                flush=True,
            )

    status = PASS if all_pass and len(assets) == 8 else REVIEW

    rep = {
        "stage": STAGE,
        "version": "0.1",
        "status": status,
        "venue": "OKX",
        "probe_universe": list(SWAPS),
        "probe_windows": [
            {"label": label, "start": start, "end": end}
            for label, start, end in WINDOWS
        ],
        "probe_windows_role": "ALREADY_CONTAMINATED_SELECTION_CALIBRATION_ONLY",
        "bar_semantics_probe": BAR,
        "assets": assets,
        "assets_passed": sum(
            1 for x in assets.values() if x.get("asset_pass") is True
        ),
        "total_http_response_bytes": total_response_bytes,
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
        "protected_holdout_accessed": False,
        "july_gap_accessed": False,
        "august_protected_accessed": False,
        "october_confirmation_accessed": False,
        "legacy_e006_confirmation_accessed": False,
        "promotional_alpha_accessed": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(OUT, rep)

    print(status)
    print("assets_passed =", rep["assets_passed"], "/ 8")
    print("total_http_response_bytes =", total_response_bytes)
    print("returns/basis-transition/signal/sentinel/PnL = False")
    print("direction/threshold/event-window selected = False")
    print("protected/promotional data accessed = False")
    print("report =", OUT)

    return 0 if status == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
