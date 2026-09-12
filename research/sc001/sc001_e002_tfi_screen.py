"""SC001-E002 — Aggressive Trade-Flow Continuation Screen.

DEV-DISCOVERY only (B01+B02+B03). Predictive screen, not strategy P&L.
Standard library only; Android/Pydroid compatible.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import statistics
import zipfile
from array import array
from bisect import bisect_left
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-E002"
VERSION = "0.1"
EXPERIMENT_NAME = "Aggressive Trade-Flow Continuation Screen"
PROTOCOL_COMMIT = "4022da85f5ffb873d558ccda74d20b8c16272ba7"
FROZEN_CALENDAR_SHA256 = "e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b"

GRID_MS = 5_000
LOOKBACK_MS = 5_000
HORIZON_MS = 5_000
LATENCIES_MS = (100, 250, 500)
PRIMARY_LATENCY_MS = 100
STRESS_LATENCY_MS = 250
DIAGNOSTIC_LATENCY_MS = 500
POSITIVE_DAY_GATE = 12
STRESS_POSITIVE_DAY_GATE = 10
EXTREME_SPREAD_POSITIVE_DAY_GATE = 10
EXPECTED_DAYS = 15
EXPECTED_QUARTERS = ("2023-Q2", "2023-Q3", "2023-Q4")
MIN_FREE_RESERVE_BYTES = 4_000_000_000
WORKSPACE_CAP_BYTES = 100_000_000

WORKSPACE = Path("/storage/emulated/0/Download/SC001_E002_TFI_SCREEN")

BATCHES = [
    ("2023-Q2", Path("/storage/emulated/0/Download/SC001_DATA_A002_B01_2023Q2"), "b01"),
    ("2023-Q3", Path("/storage/emulated/0/Download/SC001_DATA_A002_B02_2023Q3"), "b02"),
    ("2023-Q4", Path("/storage/emulated/0/Download/SC001_DATA_A002_B03_2023Q4"), "b03"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except FileNotFoundError:
                pass
    return total


def safety_check() -> None:
    if dir_size(WORKSPACE) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("E002 workspace cap exceeded")
    if free_bytes(WORKSPACE) < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("minimum free-space reserve violated")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def median(values):
    return statistics.median(values) if values else None


def rankdata(values):
    n = len(values)
    order = sorted(range(n), key=values.__getitem__)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i + 1
        vi = values[order[i]]
        while j < n and values[order[j]] == vi:
            j += 1
        r = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = r
        i = j
    return ranks


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx = sum(x) / n
    my = sum(y) / n
    sxx = syy = sxy = 0.0
    for a, b in zip(x, y):
        dx = a - mx
        dy = b - my
        sxx += dx * dx
        syy += dy * dy
        sxy += dx * dy
    if sxx <= 0.0 or syy <= 0.0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def spearman(x, y):
    if len(x) != len(y) or len(x) < 3:
        return None
    return pearson(rankdata(x), rankdata(y))


def extreme_decile_metrics(scores, returns_bps):
    n = len(scores)
    if n < 20:
        return {"n_each": 0, "bottom_mean_bps": None, "top_mean_bps": None, "spread_bps": None, "directional_hit_rate": None}
    order = sorted(range(n), key=scores.__getitem__)
    m = max(1, n // 10)
    bot = order[:m]
    top = order[-m:]
    bottom_mean = sum(returns_bps[i] for i in bot) / m
    top_mean = sum(returns_bps[i] for i in top) / m
    hits = sum(1 for i in top if returns_bps[i] > 0.0) + sum(1 for i in bot if returns_bps[i] < 0.0)
    return {
        "n_each": m,
        "bottom_mean_bps": bottom_mean,
        "top_mean_bps": top_mean,
        "spread_bps": top_mean - bottom_mean,
        "directional_hit_rate": hits / (2 * m),
    }


def one_sided_sign_pvalue(k_positive: int, n: int) -> float:
    return sum(math.comb(n, k) for k in range(k_positive, n + 1)) / (2 ** n)


def load_sources():
    sources = []
    for quarter, folder, tag in BATCHES:
        report_path = folder / f"sc001_data_a002_{tag}_report.json"
        manifest_path = folder / f"sc001_data_a002_{tag}_manifest.json"
        if not report_path.exists() or not manifest_path.exists():
            raise RuntimeError(f"missing qualified batch metadata: {folder}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if report.get("overall_status") != "PASS" or manifest.get("overall_status") != "PASS":
            raise RuntimeError(f"batch is not PASS: {quarter}")
        if report.get("strategy_pnl_calculated") is not False or report.get("validation_or_final_accessed") is not False:
            raise RuntimeError(f"batch boundary mismatch: {quarter}")
        scope = report.get("scope") or {}
        if scope.get("frozen_calendar_sha256") != FROZEN_CALENDAR_SHA256:
            raise RuntimeError(f"calendar SHA mismatch: {quarter}")
        if scope.get("split") not in {"DEV_ONLY", "DEV_DISCOVERY_ONLY"}:
            raise RuntimeError(f"split mismatch: {quarter}")
        files = manifest.get("files") or []
        if len(files) != 5:
            raise RuntimeError(f"expected 5 files in {quarter}")
        for row in files:
            if row.get("status") != "PASS":
                raise RuntimeError(f"non-PASS file in {quarter}: {row.get('date')}")
            zip_path = folder / "archives" / row["filename"]
            if not zip_path.exists():
                raise RuntimeError(f"missing archive: {zip_path}")
            if zip_path.stat().st_size != row["bytes"]:
                raise RuntimeError(f"archive size mismatch: {zip_path}")
            if sha256_file(zip_path) != row["sha256"]:
                raise RuntimeError(f"archive SHA mismatch: {zip_path}")
            sources.append({
                "quarter": quarter,
                "folder": str(folder),
                "zip_path": str(zip_path),
                "date": row["date"],
                "sample_type": row["sample_type"],
                "event_class": row.get("event_class"),
                "sha256": row["sha256"],
                "bytes": row["bytes"],
            })
    sources.sort(key=lambda x: x["date"])
    if len(sources) != EXPECTED_DAYS:
        raise RuntimeError(f"expected {EXPECTED_DAYS} discovery days, got {len(sources)}")
    return sources


def process_day(source):
    date_text = source["date"]
    day_start = int(datetime.fromisoformat(date_text).replace(tzinfo=timezone.utc).timestamp() * 1000)
    day_end = day_start + 86_400_000
    n_buckets = 86_400_000 // GRID_MS
    signed = array("d", [0.0]) * n_buckets
    total = array("d", [0.0]) * n_buckets
    timestamps = array("q")
    prices = array("d")
    rows = 0
    prev_ts = None

    path = Path(source["zip_path"])
    with zipfile.ZipFile(path, "r") as zf:
        members = [x for x in zf.infolist() if not x.is_dir()]
        if len(members) != 1:
            raise RuntimeError(f"unexpected member count: {date_text}")
        with zf.open(members[0], "r") as raw:
            text = (line.decode("utf-8") for line in raw)
            reader = csv.reader(text)
            first_nonempty = True
            for row in reader:
                if not row:
                    continue
                if first_nonempty:
                    first_nonempty = False
                    try:
                        int(row[0].strip())
                    except Exception:
                        continue
                if len(row) != 7:
                    raise RuntimeError(f"invalid row width in qualified archive: {date_text}")
                ts = int(row[5])
                if prev_ts is not None and ts < prev_ts:
                    raise RuntimeError(f"timestamp reversal during E002 parse: {date_text}")
                prev_ts = ts
                if ts < day_start or ts >= day_end:
                    raise RuntimeError(f"out-of-day row during E002 parse: {date_text}")
                price = float(row[1])
                qty = float(row[2])
                if not (price > 0.0 and qty > 0.0 and math.isfinite(price) and math.isfinite(qty)):
                    raise RuntimeError(f"invalid price/qty during E002 parse: {date_text}")
                maker = row[6].strip().lower()
                if maker not in {"true", "false"}:
                    raise RuntimeError(f"invalid maker flag during E002 parse: {date_text}")
                notional = price * qty
                sgn = -1.0 if maker == "true" else 1.0
                bi = (ts - day_start) // GRID_MS
                signed[bi] += sgn * notional
                total[bi] += notional
                timestamps.append(ts)
                prices.append(price)
                rows += 1

    result = {
        "date": date_text,
        "quarter": source["quarter"],
        "sample_type": source["sample_type"],
        "event_class": source["event_class"],
        "source_rows": rows,
        "latencies": {},
    }

    scores = []
    return_map = {lat: [] for lat in LATENCIES_MS}
    for k in range(n_buckets - 2):
        if total[k] <= 0.0:
            continue
        decision_ts = day_start + (k + 1) * GRID_MS
        score = signed[k] / total[k]
        lat_returns = {}
        valid_all = True
        for lat in LATENCIES_MS:
            entry_target = decision_ts + lat
            exit_target = entry_target + HORIZON_MS
            if exit_target >= day_end:
                valid_all = False
                break
            i = bisect_left(timestamps, entry_target)
            j = bisect_left(timestamps, exit_target)
            if i >= len(timestamps) or j >= len(timestamps):
                valid_all = False
                break
            entry_price = prices[i]
            exit_price = prices[j]
            lat_returns[lat] = math.log(exit_price / entry_price) * 10_000.0
        if not valid_all:
            continue
        scores.append(score)
        for lat in LATENCIES_MS:
            return_map[lat].append(lat_returns[lat])

    if len(scores) < 1000:
        raise RuntimeError(f"too few E002 decisions: {date_text} n={len(scores)}")

    for lat in LATENCIES_MS:
        rets = return_map[lat]
        rho = spearman(scores, rets)
        ext = extreme_decile_metrics(scores, rets)
        result["latencies"][str(lat)] = {
            "n": len(scores),
            "spearman": rho,
            "mean_return_bps": sum(rets) / len(rets),
            "median_return_bps": median(rets),
            "extreme_decile": ext,
        }
    return result


def summarize(daily):
    summary = {"latencies": {}}
    for lat in LATENCIES_MS:
        key = str(lat)
        vals = [d["latencies"][key]["spearman"] for d in daily]
        spreads = [d["latencies"][key]["extreme_decile"]["spread_bps"] for d in daily]
        pos = sum(1 for x in vals if x is not None and x > 0.0)
        spread_pos = sum(1 for x in spreads if x is not None and x > 0.0)
        quarter_medians = {}
        for q in EXPECTED_QUARTERS:
            qvals = [d["latencies"][key]["spearman"] for d in daily if d["quarter"] == q]
            quarter_medians[q] = median(qvals)
        event_vals = [d["latencies"][key]["spearman"] for d in daily if d["sample_type"] == "EVENT"]
        ordinary_vals = [d["latencies"][key]["spearman"] for d in daily if d["sample_type"] != "EVENT"]
        summary["latencies"][key] = {
            "positive_days": pos,
            "negative_or_zero_days": len(vals) - pos,
            "median_daily_spearman": median(vals),
            "mean_daily_spearman": sum(vals) / len(vals),
            "one_sided_sign_pvalue": one_sided_sign_pvalue(pos, len(vals)),
            "positive_extreme_spread_days": spread_pos,
            "median_daily_extreme_spread_bps": median(spreads),
            "quarter_median_spearman": quarter_medians,
            "event_day_median_spearman": median(event_vals),
            "ordinary_day_median_spearman": median(ordinary_vals),
        }

    p = summary["latencies"][str(PRIMARY_LATENCY_MS)]
    s = summary["latencies"][str(STRESS_LATENCY_MS)]
    gates = {
        "primary_positive_days_ge_12_of_15": p["positive_days"] >= POSITIVE_DAY_GATE,
        "primary_median_spearman_positive": p["median_daily_spearman"] is not None and p["median_daily_spearman"] > 0.0,
        "all_three_quarter_medians_positive": all((v is not None and v > 0.0) for v in p["quarter_median_spearman"].values()),
        "event_day_median_positive": p["event_day_median_spearman"] is not None and p["event_day_median_spearman"] > 0.0,
        "ordinary_day_median_positive": p["ordinary_day_median_spearman"] is not None and p["ordinary_day_median_spearman"] > 0.0,
        "primary_extreme_spread_positive_days_ge_10": p["positive_extreme_spread_days"] >= EXTREME_SPREAD_POSITIVE_DAY_GATE,
        "primary_median_extreme_spread_positive": p["median_daily_extreme_spread_bps"] is not None and p["median_daily_extreme_spread_bps"] > 0.0,
        "stress_250ms_positive_days_ge_10": s["positive_days"] >= STRESS_POSITIVE_DAY_GATE,
        "stress_250ms_median_spearman_positive": s["median_daily_spearman"] is not None and s["median_daily_spearman"] > 0.0,
    }
    primary_assoc = all(gates[k] for k in [
        "primary_positive_days_ge_12_of_15",
        "primary_median_spearman_positive",
        "all_three_quarter_medians_positive",
        "event_day_median_positive",
        "ordinary_day_median_positive",
        "primary_extreme_spread_positive_days_ge_10",
        "primary_median_extreme_spread_positive",
    ])
    stress_ok = gates["stress_250ms_positive_days_ge_10"] and gates["stress_250ms_median_spearman_positive"]
    if primary_assoc and stress_ok:
        status = "PROMISING_SCREEN"
    elif primary_assoc:
        status = "WEAK"
    else:
        status = "FAIL"
    summary["gates"] = gates
    summary["status"] = status
    return summary


def write_outputs(report):
    atomic_json(WORKSPACE / "sc001_e002_report.json", report)
    with (WORKSPACE / "sc001_e002_daily_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "date", "quarter", "sample_type", "event_class", "source_rows",
            "latency_ms", "n", "spearman", "mean_return_bps", "median_return_bps",
            "extreme_bottom_mean_bps", "extreme_top_mean_bps", "extreme_spread_bps", "extreme_hit_rate",
        ])
        for d in report.get("daily", []):
            for lat in LATENCIES_MS:
                m = d["latencies"][str(lat)]
                e = m["extreme_decile"]
                w.writerow([
                    d["date"], d["quarter"], d["sample_type"], d["event_class"] or "", d["source_rows"],
                    lat, m["n"], m["spearman"], m["mean_return_bps"], m["median_return_bps"],
                    e["bottom_mean_bps"], e["top_mean_bps"], e["spread_bps"], e["directional_hit_rate"],
                ])
    lines = [
        "# SC001-E002 — Aggressive Trade-Flow Continuation Screen",
        "",
        f"- Status: `{report.get('status')}`",
        "- Strategy P&L calculated: **NO**",
        "- Execution/L2 profitability claim: **NO**",
        "- Scope: DEV-DISCOVERY only (B01+B02+B03 = 15 days)",
        "- Primary: 5s signed-notional trade-flow imbalance -> next 5s transaction-price response after 100ms latency",
        "",
        "## Primary summary",
    ]
    s = report.get("summary", {}).get("latencies", {}).get("100", {})
    lines += [
        f"- Positive daily Spearman: {s.get('positive_days')} / 15",
        f"- Median daily Spearman: {s.get('median_daily_spearman')}",
        f"- One-sided sign-test p: {s.get('one_sided_sign_pvalue')}",
        f"- Positive extreme-decile spread days: {s.get('positive_extreme_spread_days')} / 15",
        f"- Median daily extreme spread (bps): {s.get('median_daily_extreme_spread_bps')}",
        "",
        "## Boundary",
        "This is a predictive feature screen, not a backtest and not evidence of net profitability. No spread, L2 depth, historical fee, or maker-queue model is used here.",
        "B04/B05 remain unopened DEV-CONFIRMATION holdout. VALIDATION and FINAL remain unopened.",
    ]
    (WORKSPACE / "sc001_e002_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    atomic_json(WORKSPACE / "sc001_e002_final_safety.json", {
        "stage": STAGE,
        "workspace_bytes_after_outputs": dir_size(WORKSPACE),
        "free_bytes_after_outputs": free_bytes(WORKSPACE),
        "workspace_cap_bytes": WORKSPACE_CAP_BYTES,
        "minimum_free_reserve_bytes": MIN_FREE_RESERVE_BYTES,
        "network_bytes_read": 0,
    })


def main():
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    safety_check()
    sources = load_sources()
    report = {
        "stage": STAGE,
        "version": VERSION,
        "experiment_name": EXPERIMENT_NAME,
        "protocol_commit": PROTOCOL_COMMIT,
        "started_at_utc": utc_now(),
        "strategy_pnl_calculated": False,
        "execution_profitability_calculated": False,
        "validation_or_final_accessed": False,
        "b04_b05_accessed": False,
        "scope": {
            "days": EXPECTED_DAYS,
            "quarters": list(EXPECTED_QUARTERS),
            "dataset": "Binance USD-M BTCUSDT aggTrades",
            "split": "DEV_DISCOVERY_ONLY",
            "grid_ms": GRID_MS,
            "lookback_ms": LOOKBACK_MS,
            "horizon_ms": HORIZON_MS,
            "latencies_ms": list(LATENCIES_MS),
            "signal": "signed_notional_imbalance = sum(sign*price*qty)/sum(price*qty), buyer-taker positive",
            "price_response": "first transaction price at or after t+latency to first transaction price at or after t+latency+5s",
        },
        "sources": sources,
        "daily": [],
    }
    try:
        for i, src in enumerate(sources, 1):
            print(f"[{i}/{EXPECTED_DAYS}] {src['date']} {src['sample_type']} {src['event_class'] or ''}")
            report["daily"].append(process_day(src))
            report["days_processed"] = len(report["daily"])
            write_outputs(report)
            safety_check()
        report["summary"] = summarize(report["daily"])
        report["status"] = report["summary"]["status"]
        report["finished_at_utc"] = utc_now()
        write_outputs(report)
        print(f"COMPLETE: {report['status']} | P&L=NO | B04/B05=UNOPENED | VALIDATION/FINAL=UNOPENED")
    except Exception as exc:
        report["status"] = "ERROR"
        report["error"] = repr(exc)
        report["finished_at_utc"] = utc_now()
        write_outputs(report)
        raise


if __name__ == "__main__":
    main()
