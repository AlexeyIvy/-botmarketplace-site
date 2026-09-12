"""SC001-E002 DEV-CONFIRMATION screen v0.1.

Runs the unchanged frozen 5s TFI continuation feature on the 10 reserved
DEV-CONFIRMATION days only. Predictive confirmation, not strategy P&L.
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

STAGE = "SC001-E002-CONFIRMATION"
VERSION = "0.1"
PARENT_EXPERIMENT = "SC001-E002"
CONFIRMATION_PROTOCOL_COMMIT = "ed0aa3e6f462421c7b057bb1ab57b903dc541f95"
ACQUISITION_STAGE = "SC001-DATA-A002-B04B05"
ACQUISITION_FOLDER = Path("/storage/emulated/0/Download/SC001_DATA_A002_B04B05_CONFIRMATION")
WORKSPACE = Path("/storage/emulated/0/Download/SC001_E002_CONFIRMATION")

GRID_MS = 5_000
LOOKBACK_MS = 5_000
HORIZON_MS = 5_000
LATENCIES_MS = (100, 250, 500)
PRIMARY_LATENCY_MS = 100
STRESS_LATENCY_MS = 250
DIAGNOSTIC_LATENCY_MS = 500
EXPECTED_DAYS = 10
EXPECTED_QUARTERS = ("2024-Q1", "2024-Q2")
PRIMARY_POSITIVE_DAY_GATE = 9
STRESS_POSITIVE_DAY_GATE = 8
EXTREME_SPREAD_POSITIVE_DAY_GATE = 8
DISCOVERY_MEDIAN_SPEARMAN_100MS = 0.12936691569403583
MIN_CONFIRMATION_MEDIAN_SPEARMAN_100MS = 0.06468345784701792
MIN_FREE_RESERVE_BYTES = 4_000_000_000
WORKSPACE_CAP_BYTES = 100_000_000

EXPECTED_DATES = {
    "2024-01-05", "2024-01-14", "2024-01-31", "2024-02-12", "2024-02-13",
    "2024-04-10", "2024-04-20", "2024-05-01", "2024-06-07", "2024-06-27",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def safety_check() -> None:
    if dir_size(WORKSPACE) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("confirmation workspace cap exceeded")
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
    report_path = ACQUISITION_FOLDER / "sc001_data_a002_b04b05_report.json"
    manifest_path = ACQUISITION_FOLDER / "sc001_data_a002_b04b05_manifest.json"
    if not report_path.exists() or not manifest_path.exists():
        raise RuntimeError("missing qualified B04B05 acquisition metadata")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if report.get("stage") != ACQUISITION_STAGE or report.get("overall_status") != "PASS":
        raise RuntimeError("B04B05 acquisition report is not PASS")
    if manifest.get("stage") != ACQUISITION_STAGE or manifest.get("overall_status") != "PASS":
        raise RuntimeError("B04B05 acquisition manifest is not PASS")
    if report.get("strategy_features_calculated") is not False or report.get("strategy_pnl_calculated") is not False:
        raise RuntimeError("acquisition feature/P&L firewall mismatch")
    if report.get("confirmation_metrics_calculated") is not False:
        raise RuntimeError("confirmation metrics were already calculated during acquisition")
    if report.get("validation_or_final_accessed") is not False:
        raise RuntimeError("formal Validation/Final access mismatch")

    files = manifest.get("files") or []
    if len(files) != EXPECTED_DAYS:
        raise RuntimeError(f"expected {EXPECTED_DAYS} files, got {len(files)}")
    dates = {x.get("date") for x in files}
    if dates != EXPECTED_DATES:
        raise RuntimeError("confirmation date set mismatch")

    sources = []
    for row in files:
        if row.get("status") != "PASS":
            raise RuntimeError(f"non-PASS confirmation file: {row.get('date')}")
        zip_path = ACQUISITION_FOLDER / "archives" / row["filename"]
        if not zip_path.exists():
            raise RuntimeError(f"missing confirmation archive: {zip_path}")
        if zip_path.stat().st_size != row["bytes"]:
            raise RuntimeError(f"archive size mismatch: {zip_path}")
        if sha256_file(zip_path) != row["sha256"]:
            raise RuntimeError(f"archive SHA mismatch: {zip_path}")
        sources.append({
            "date": row["date"],
            "quarter": row["quarter"],
            "sample_type": row["sample_type"],
            "event_class": row.get("event_class"),
            "zip_path": str(zip_path),
            "bytes": row["bytes"],
            "sha256": row["sha256"],
        })
    sources.sort(key=lambda x: x["date"])
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
            raise RuntimeError(f"unexpected ZIP member count: {date_text}")
        with zf.open(members[0], "r") as raw:
            reader = csv.reader((line.decode("utf-8") for line in raw))
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
                    raise RuntimeError(f"timestamp reversal during confirmation parse: {date_text}")
                prev_ts = ts
                if ts < day_start or ts >= day_end:
                    raise RuntimeError(f"out-of-day row during confirmation parse: {date_text}")
                price = float(row[1])
                qty = float(row[2])
                if not (price > 0.0 and qty > 0.0 and math.isfinite(price) and math.isfinite(qty)):
                    raise RuntimeError(f"invalid price/qty: {date_text}")
                maker = row[6].strip().lower()
                if maker not in {"true", "false"}:
                    raise RuntimeError(f"invalid maker flag: {date_text}")
                notional = price * qty
                sign = -1.0 if maker == "true" else 1.0
                bucket = (ts - day_start) // GRID_MS
                signed[bucket] += sign * notional
                total[bucket] += notional
                timestamps.append(ts)
                prices.append(price)
                rows += 1

    scores = []
    returns_by_latency = {lat: [] for lat in LATENCIES_MS}
    for k in range(n_buckets - 2):
        if total[k] <= 0.0:
            continue
        decision_ts = day_start + (k + 1) * GRID_MS
        score = signed[k] / total[k]
        tmp = {}
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
            tmp[lat] = math.log(prices[j] / prices[i]) * 10_000.0
        if not valid_all:
            continue
        scores.append(score)
        for lat in LATENCIES_MS:
            returns_by_latency[lat].append(tmp[lat])

    if len(scores) < 1000:
        raise RuntimeError(f"too few confirmation decisions: {date_text} n={len(scores)}")

    result = {
        "date": date_text,
        "quarter": source["quarter"],
        "sample_type": source["sample_type"],
        "event_class": source["event_class"],
        "source_rows": rows,
        "latencies": {},
    }
    for lat in LATENCIES_MS:
        rets = returns_by_latency[lat]
        result["latencies"][str(lat)] = {
            "n": len(scores),
            "spearman": spearman(scores, rets),
            "mean_return_bps": sum(rets) / len(rets),
            "median_return_bps": median(rets),
            "extreme_decile": extreme_decile_metrics(scores, rets),
        }
    return result


def summarize(daily):
    out = {"latencies": {}}
    for lat in LATENCIES_MS:
        key = str(lat)
        vals = [d["latencies"][key]["spearman"] for d in daily]
        spreads = [d["latencies"][key]["extreme_decile"]["spread_bps"] for d in daily]
        pos = sum(1 for x in vals if x is not None and x > 0.0)
        spread_pos = sum(1 for x in spreads if x is not None and x > 0.0)
        quarter_medians = {
            q: median([d["latencies"][key]["spearman"] for d in daily if d["quarter"] == q])
            for q in EXPECTED_QUARTERS
        }
        event_vals = [d["latencies"][key]["spearman"] for d in daily if d["sample_type"] == "EVENT"]
        ordinary_vals = [d["latencies"][key]["spearman"] for d in daily if d["sample_type"] != "EVENT"]
        out["latencies"][key] = {
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

    p = out["latencies"][str(PRIMARY_LATENCY_MS)]
    s = out["latencies"][str(STRESS_LATENCY_MS)]
    gates = {
        "primary_positive_days_ge_9_of_10": p["positive_days"] >= PRIMARY_POSITIVE_DAY_GATE,
        "primary_median_spearman_positive": p["median_daily_spearman"] is not None and p["median_daily_spearman"] > 0.0,
        "primary_median_spearman_retains_50pct_discovery": p["median_daily_spearman"] is not None and p["median_daily_spearman"] >= MIN_CONFIRMATION_MEDIAN_SPEARMAN_100MS,
        "both_confirmation_quarter_medians_positive": all(v is not None and v > 0.0 for v in p["quarter_median_spearman"].values()),
        "event_day_median_positive": p["event_day_median_spearman"] is not None and p["event_day_median_spearman"] > 0.0,
        "ordinary_day_median_positive": p["ordinary_day_median_spearman"] is not None and p["ordinary_day_median_spearman"] > 0.0,
        "primary_extreme_spread_positive_days_ge_8": p["positive_extreme_spread_days"] >= EXTREME_SPREAD_POSITIVE_DAY_GATE,
        "primary_median_extreme_spread_positive": p["median_daily_extreme_spread_bps"] is not None and p["median_daily_extreme_spread_bps"] > 0.0,
        "stress_250ms_positive_days_ge_8": s["positive_days"] >= STRESS_POSITIVE_DAY_GATE,
        "stress_250ms_median_spearman_positive": s["median_daily_spearman"] is not None and s["median_daily_spearman"] > 0.0,
    }
    out["gates"] = gates
    primary_core_pass = gates["primary_positive_days_ge_9_of_10"] and gates["primary_median_spearman_positive"]
    if all(gates.values()):
        verdict = "CONFIRMATION_PASS"
    elif primary_core_pass:
        verdict = "CONFIRMATION_WEAK"
    else:
        verdict = "CONFIRMATION_FAIL"
    out["confirmation_verdict"] = verdict
    out["parent_status_if_pass"] = "PROMISING_SCREEN"
    return out


def write_outputs(report):
    atomic_json(WORKSPACE / "sc001_e002_confirmation_report.json", report)
    daily_path = WORKSPACE / "sc001_e002_confirmation_daily_metrics.csv"
    with daily_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "date", "quarter", "sample_type", "event_class", "source_rows", "latency_ms", "n",
            "spearman", "mean_return_bps", "median_return_bps", "bottom_decile_mean_bps",
            "top_decile_mean_bps", "extreme_spread_bps", "directional_hit_rate",
        ])
        for d in report.get("daily", []):
            for lat in LATENCIES_MS:
                m = d["latencies"][str(lat)]
                e = m["extreme_decile"]
                w.writerow([
                    d["date"], d["quarter"], d["sample_type"], d.get("event_class") or "", d["source_rows"], lat,
                    m["n"], m["spearman"], m["mean_return_bps"], m["median_return_bps"],
                    e["bottom_mean_bps"], e["top_mean_bps"], e["spread_bps"], e["directional_hit_rate"],
                ])

    s = report.get("summary") or {}
    p = (s.get("latencies") or {}).get("100", {})
    lines = [
        "# SC001-E002 DEV-CONFIRMATION",
        "",
        f"- Verdict: `{s.get('confirmation_verdict')}`",
        "- Strategy P&L calculated: **NO**",
        "- Scope: 10 frozen DEV-CONFIRMATION days",
        f"- Positive daily Spearman at 100ms: {p.get('positive_days')} / 10",
        f"- Median daily Spearman at 100ms: {p.get('median_daily_spearman')}",
        f"- Frozen 50% discovery-retention threshold: {MIN_CONFIRMATION_MEDIAN_SPEARMAN_100MS}",
        f"- One-sided sign-test p: {p.get('one_sided_sign_pvalue')}",
        f"- Positive extreme spread days: {p.get('positive_extreme_spread_days')} / 10",
        f"- Median extreme spread bps: {p.get('median_daily_extreme_spread_bps')}",
        "",
        "## Boundary",
        "Predictive confirmation only. No L2 execution, spread, fee, market-impact, or net-profitability claim.",
        "Formal Validation and Final remain unopened.",
    ]
    (WORKSPACE / "sc001_e002_confirmation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    atomic_json(WORKSPACE / "sc001_e002_confirmation_final_safety.json", {
        "stage": STAGE,
        "network_bytes_read": 0,
        "workspace_bytes_after_outputs": dir_size(WORKSPACE),
        "free_bytes_after_outputs": free_bytes(WORKSPACE),
        "workspace_cap_bytes": WORKSPACE_CAP_BYTES,
        "minimum_free_reserve_bytes": MIN_FREE_RESERVE_BYTES,
    })


def main():
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    safety_check()
    sources = load_sources()
    report = {
        "stage": STAGE,
        "version": VERSION,
        "parent_experiment": PARENT_EXPERIMENT,
        "confirmation_protocol_commit": CONFIRMATION_PROTOCOL_COMMIT,
        "started_at_utc": utc_now(),
        "scope": {
            "dataset": "Binance USD-M BTCUSDT aggTrades",
            "split": "DEV_CONFIRMATION_ONLY",
            "days": EXPECTED_DAYS,
            "quarters": list(EXPECTED_QUARTERS),
            "grid_ms": GRID_MS,
            "lookback_ms": LOOKBACK_MS,
            "horizon_ms": HORIZON_MS,
            "latencies_ms": list(LATENCIES_MS),
            "signal": "same frozen E002 signed-notional TFI",
            "price_response": "same frozen first-trade response construction",
        },
        "discovery_reference": {
            "median_daily_spearman_100ms": DISCOVERY_MEDIAN_SPEARMAN_100MS,
            "frozen_50pct_retention_threshold": MIN_CONFIRMATION_MEDIAN_SPEARMAN_100MS,
        },
        "b04_b05_accessed": True,
        "validation_or_final_accessed": False,
        "strategy_pnl_calculated": False,
        "execution_profitability_calculated": False,
        "daily": [],
        "sources": sources,
    }
    try:
        for src in sources:
            print(f"[{src['date']}] confirmation screen...")
            report["daily"].append(process_day(src))
            safety_check()
        report["summary"] = summarize(report["daily"])
        report["confirmation_verdict"] = report["summary"]["confirmation_verdict"]
        report["finished_at_utc"] = utc_now()
        write_outputs(report)
    except Exception as exc:
        report["status"] = "ERROR"
        report["error"] = repr(exc)
        report["finished_at_utc"] = utc_now()
        write_outputs(report)
        raise

    print(
        "COMPLETE:", report["confirmation_verdict"],
        "| P&L=NO | VALIDATION/FINAL=NO"
    )


if __name__ == "__main__":
    main()
