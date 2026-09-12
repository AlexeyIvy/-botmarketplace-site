"""SC001-E002 OKX Q1 same-formula replication v0.1.

Uses only Q006R-qualified 2024-Q1 BTC-USDT-SWAP trades.
Predictive feature replication only: no L2 execution P&L, no Q2 OKX,
no formal Validation/Final. Android/Pydroid, standard library only.
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

STAGE = "SC001-E002-OKX-Q1-REPLICATION"
VERSION = "0.1"
PROTOCOL_COMMIT = "dccf2fd4e95996a77b980e1ca0c3ad0c5662416f"
PARENT_STAGE = "SC001-DATA-Q006R-OKX-UTC-STITCH"

GRID_MS = 5_000
LOOKBACK_MS = 5_000
HORIZON_MS = 5_000
LATENCIES_MS = (100, 250, 500)
PRIMARY_LATENCY_MS = 100
STRESS_LATENCY_MS = 250
DIAGNOSTIC_LATENCY_MS = 500
EXPECTED_DAYS = 5
PRIMARY_POSITIVE_DAY_GATE = 5
STRESS_POSITIVE_DAY_GATE = 4
PRIMARY_EXTREME_SPREAD_POSITIVE_DAY_GATE = 5

BINANCE_Q1_MEDIAN_SPEARMAN_100MS = 0.086705639006201
BINANCE_Q1_DAILY_SPEARMAN_100MS = {
    "2024-01-05": 0.05057067200728686,
    "2024-01-14": 0.09822750280748929,
    "2024-01-31": 0.0710990051202889,
    "2024-02-12": 0.09688457662733974,
    "2024-02-13": 0.086705639006201,
}

EVENT_META = {
    "2024-01-05": ("EVENT", "NFP"),
    "2024-01-14": ("ORDINARY_WEEKEND", None),
    "2024-01-31": ("EVENT", "FOMC"),
    "2024-02-12": ("ORDINARY_WEEKDAY", None),
    "2024-02-13": ("EVENT", "CPI"),
}

EXPECTED_HEADER = [
    "instrument_name", "trade_id", "side", "price", "size", "created_time"
]
TARGET_INSTRUMENT = "BTC-USDT-SWAP"

DOWNLOAD = Path("/storage/emulated/0/Download")
PARENT_REPORT = (
    DOWNLOAD / "SC001_DATA_Q006R_OKX_UTC_STITCH" /
    "sc001_data_q006r_okx_utc_stitch_report.json"
)
WORKSPACE = DOWNLOAD / "SC001_E002_OKX_Q1_REPLICATION"
REPORT = WORKSPACE / "sc001_e002_okx_q1_replication_report.json"
DAILY_CSV = WORKSPACE / "sc001_e002_okx_q1_replication_daily_metrics.csv"
SUMMARY = WORKSPACE / "sc001_e002_okx_q1_replication_summary.md"
SAFETY = WORKSPACE / "sc001_e002_okx_q1_replication_final_safety.json"

WORKSPACE_CAP_BYTES = 100_000_000
MIN_FREE_RESERVE_BYTES = 4_000_000_000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def free_bytes() -> int:
    return shutil.disk_usage(DOWNLOAD).free


def safety_check() -> None:
    if dir_size(WORKSPACE) > WORKSPACE_CAP_BYTES:
        raise RuntimeError("OKX replication workspace cap exceeded")
    if free_bytes() < MIN_FREE_RESERVE_BYTES:
        raise RuntimeError("minimum free-space reserve violated")


def atomic_json(path: Path, obj) -> None:
    raw = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(raw)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def median(values):
    return statistics.median(values) if values else None


def quantile(values, q: float):
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return float(xs[0])
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(xs[lo])
    w = pos - lo
    return float(xs[lo] * (1.0 - w) + xs[hi] * w)


def rankdata(values):
    n = len(values)
    order = sorted(range(n), key=values.__getitem__)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i + 1
        v = values[order[i]]
        while j < n and values[order[j]] == v:
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
        return {
            "n_each": 0, "bottom_mean_bps": None, "top_mean_bps": None,
            "spread_bps": None, "directional_hit_rate": None,
        }
    order = sorted(range(n), key=scores.__getitem__)
    m = max(1, n // 10)
    bot = order[:m]
    top = order[-m:]
    bottom_mean = sum(returns_bps[i] for i in bot) / m
    top_mean = sum(returns_bps[i] for i in top) / m
    hits = (
        sum(1 for i in top if returns_bps[i] > 0.0)
        + sum(1 for i in bot if returns_bps[i] < 0.0)
    )
    return {
        "n_each": m,
        "bottom_mean_bps": bottom_mean,
        "top_mean_bps": top_mean,
        "spread_bps": top_mean - bottom_mean,
        "directional_hit_rate": hits / (2 * m),
    }


def lag_metrics(values):
    return {
        "median_ms": median(values),
        "p95_ms": quantile(values, 0.95),
        "p99_ms": quantile(values, 0.99),
        "max_ms": max(values) if values else None,
    }


def one_sided_sign_pvalue(k_positive: int, n: int) -> float:
    return sum(math.comb(n, k) for k in range(k_positive, n + 1)) / (2 ** n)


def load_parent_days():
    if not PARENT_REPORT.exists():
        raise RuntimeError(f"missing Q006R parent report: {PARENT_REPORT}")
    obj = json.loads(PARENT_REPORT.read_text(encoding="utf-8"))
    if obj.get("stage") != PARENT_STAGE or obj.get("overall_status") != "PASS":
        raise RuntimeError("Q006R parent is not PASS")
    if obj.get("strategy_features_calculated") is not False:
        raise RuntimeError("Q006R feature firewall mismatch")
    if obj.get("future_returns_calculated") is not False:
        raise RuntimeError("Q006R return firewall mismatch")
    if obj.get("strategy_pnl_calculated") is not False:
        raise RuntimeError("Q006R P&L firewall mismatch")
    if obj.get("q2_okx_accessed") is not False:
        raise RuntimeError("Q006R Q2 firewall mismatch")
    if obj.get("validation_or_final_accessed") is not False:
        raise RuntimeError("Q006R Validation/Final firewall mismatch")

    days = obj.get("days") or []
    if len(days) != EXPECTED_DAYS:
        raise RuntimeError(f"expected {EXPECTED_DAYS} Q006R days")
    expected_dates = set(EVENT_META)
    if {d.get("date") for d in days} != expected_dates:
        raise RuntimeError("Q006R date set mismatch")

    for day in days:
        if day.get("status") != "PASS":
            raise RuntimeError(f"non-PASS Q006R day: {day.get('date')}")
        stitch = day.get("stitch") or {}
        gates = stitch.get("gates") or {}
        if not gates or not all(gates.values()):
            raise RuntimeError(f"Q006R stitch gates not all PASS: {day.get('date')}")
        for scan in day.get("source_scans") or []:
            path = Path(scan["path"])
            if not path.exists():
                raise RuntimeError(f"missing source archive: {path}")
            if path.stat().st_size != scan["bytes"]:
                raise RuntimeError(f"source archive size mismatch: {path}")
            if sha256_file(path) != scan["sha256"]:
                raise RuntimeError(f"source archive SHA mismatch: {path}")
    return sorted(days, key=lambda x: x["date"])


def load_target_day(day):
    date_text = day["date"]
    day_start = int(datetime.fromisoformat(date_text).replace(tzinfo=timezone.utc).timestamp() * 1000)
    day_end = day_start + 86_400_000
    n_buckets = 86_400_000 // GRID_MS

    signed = array("d", [0.0]) * n_buckets
    total = array("d", [0.0]) * n_buckets
    timestamps = array("q")
    prices = array("d")
    trade_ids = array("q")

    rows = 0
    previous_ts = None
    previous_tid = None

    scans = sorted(day["source_scans"], key=lambda x: x["first_ts"])
    for scan in scans:
        path = Path(scan["path"])
        with zipfile.ZipFile(path, "r") as zf:
            members = [x for x in zf.infolist() if not x.is_dir()]
            if len(members) != 1:
                raise RuntimeError(f"unexpected member count: {path}")
            with zf.open(members[0], "r") as raw:
                reader = csv.reader((line.decode("utf-8") for line in raw))
                header = next(reader)
                if header != EXPECTED_HEADER:
                    raise RuntimeError(f"header mismatch: {path} -> {header}")
                for row in reader:
                    if not row:
                        continue
                    inst, tid_s, side, price_s, size_s, ts_s = row
                    if inst != TARGET_INSTRUMENT:
                        raise RuntimeError(f"instrument mismatch in {path}")
                    ts = int(ts_s)
                    if ts < day_start or ts >= day_end:
                        continue
                    tid = int(tid_s)
                    price = float(price_s)
                    size = float(size_s)
                    side = side.strip().lower()
                    if side not in {"buy", "sell"}:
                        raise RuntimeError(f"side mismatch in {path}")
                    if not (price > 0.0 and size > 0.0 and math.isfinite(price) and math.isfinite(size)):
                        raise RuntimeError(f"invalid price/size in {path}")
                    if previous_ts is not None and ts < previous_ts:
                        raise RuntimeError(f"target timestamp reversal: {date_text}")
                    if previous_tid is not None and tid <= previous_tid:
                        raise RuntimeError(f"target trade ID duplicate/backward: {date_text}")
                    previous_ts = ts
                    previous_tid = tid
                    notional_proxy = price * size
                    sign = 1.0 if side == "buy" else -1.0
                    bucket = (ts - day_start) // GRID_MS
                    signed[bucket] += sign * notional_proxy
                    total[bucket] += notional_proxy
                    timestamps.append(ts)
                    prices.append(price)
                    trade_ids.append(tid)
                    rows += 1

    expected_rows = (day.get("stitch") or {}).get("admitted_rows")
    if rows != expected_rows:
        raise RuntimeError(
            f"reconstructed row count mismatch {date_text}: got={rows} expected={expected_rows}"
        )
    if rows < 1:
        raise RuntimeError(f"no target rows: {date_text}")
    return day_start, day_end, signed, total, timestamps, prices, trade_ids, rows


def process_day(day):
    date_text = day["date"]
    day_start, day_end, signed, total, timestamps, prices, trade_ids, rows = load_target_day(day)
    n_buckets = len(total)

    scores = []
    returns_by_latency = {lat: [] for lat in LATENCIES_MS}
    entry_lags = {lat: [] for lat in LATENCIES_MS}
    exit_lags = {lat: [] for lat in LATENCIES_MS}

    for k in range(n_buckets - 2):
        if total[k] <= 0.0:
            continue
        decision_ts = day_start + (k + 1) * GRID_MS
        score = signed[k] / total[k]
        tmp_returns = {}
        tmp_entry_lag = {}
        tmp_exit_lag = {}
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
            tmp_returns[lat] = math.log(prices[j] / prices[i]) * 10_000.0
            tmp_entry_lag[lat] = timestamps[i] - entry_target
            tmp_exit_lag[lat] = timestamps[j] - exit_target
        if not valid_all:
            continue
        scores.append(score)
        for lat in LATENCIES_MS:
            returns_by_latency[lat].append(tmp_returns[lat])
            entry_lags[lat].append(tmp_entry_lag[lat])
            exit_lags[lat].append(tmp_exit_lag[lat])

    if len(scores) < 1000:
        raise RuntimeError(f"too few valid 5s decisions: {date_text} n={len(scores)}")

    sample_type, event_class = EVENT_META[date_text]
    result = {
        "date": date_text,
        "sample_type": sample_type,
        "event_class": event_class,
        "source_rows": rows,
        "binance_reference_spearman_100ms": BINANCE_Q1_DAILY_SPEARMAN_100MS[date_text],
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
            "entry_target_to_trade_lag": lag_metrics(entry_lags[lat]),
            "exit_target_to_trade_lag": lag_metrics(exit_lags[lat]),
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
            "event_day_median_spearman": median(event_vals),
            "ordinary_day_median_spearman": median(ordinary_vals),
        }

    primary = out["latencies"][str(PRIMARY_LATENCY_MS)]
    stress = out["latencies"][str(STRESS_LATENCY_MS)]
    gates = {
        "primary_positive_days_eq_5_of_5": primary["positive_days"] == PRIMARY_POSITIVE_DAY_GATE,
        "primary_median_spearman_positive": primary["median_daily_spearman"] is not None and primary["median_daily_spearman"] > 0.0,
        "event_day_median_positive": primary["event_day_median_spearman"] is not None and primary["event_day_median_spearman"] > 0.0,
        "ordinary_day_median_positive": primary["ordinary_day_median_spearman"] is not None and primary["ordinary_day_median_spearman"] > 0.0,
        "primary_extreme_spread_positive_days_eq_5": primary["positive_extreme_spread_days"] == PRIMARY_EXTREME_SPREAD_POSITIVE_DAY_GATE,
        "primary_median_extreme_spread_positive": primary["median_daily_extreme_spread_bps"] is not None and primary["median_daily_extreme_spread_bps"] > 0.0,
        "stress_250ms_positive_days_ge_4": stress["positive_days"] >= STRESS_POSITIVE_DAY_GATE,
        "stress_250ms_median_spearman_positive": stress["median_daily_spearman"] is not None and stress["median_daily_spearman"] > 0.0,
    }
    out["gates"] = gates
    primary_core = all(gates[k] for k in (
        "primary_positive_days_eq_5_of_5",
        "primary_median_spearman_positive",
        "event_day_median_positive",
        "ordinary_day_median_positive",
        "primary_extreme_spread_positive_days_eq_5",
        "primary_median_extreme_spread_positive",
    ))
    if all(gates.values()):
        verdict = "OKX_REPLICATION_PASS"
    elif primary_core:
        verdict = "OKX_REPLICATION_WEAK"
    else:
        verdict = "OKX_REPLICATION_FAIL"
    out["verdict"] = verdict
    out["binance_q1_reference"] = {
        "median_daily_spearman_100ms": BINANCE_Q1_MEDIAN_SPEARMAN_100MS,
        "okx_to_binance_median_spearman_ratio": (
            primary["median_daily_spearman"] / BINANCE_Q1_MEDIAN_SPEARMAN_100MS
            if primary["median_daily_spearman"] is not None else None
        ),
    }
    return out


def write_outputs(report):
    atomic_json(REPORT, report)

    with DAILY_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "date", "sample_type", "event_class", "source_rows", "latency_ms", "n",
            "spearman", "mean_return_bps", "median_return_bps",
            "bottom_decile_mean_bps", "top_decile_mean_bps", "extreme_spread_bps",
            "directional_hit_rate", "entry_lag_median_ms", "entry_lag_p95_ms",
            "entry_lag_p99_ms", "entry_lag_max_ms", "exit_lag_median_ms",
            "exit_lag_p95_ms", "exit_lag_p99_ms", "exit_lag_max_ms",
            "binance_reference_spearman_100ms",
        ])
        for d in report.get("daily", []):
            for lat in LATENCIES_MS:
                m = d["latencies"][str(lat)]
                ext = m["extreme_decile"]
                en = m["entry_target_to_trade_lag"]
                ex = m["exit_target_to_trade_lag"]
                w.writerow([
                    d["date"], d["sample_type"], d["event_class"], d["source_rows"], lat,
                    m["n"], m["spearman"], m["mean_return_bps"], m["median_return_bps"],
                    ext["bottom_mean_bps"], ext["top_mean_bps"], ext["spread_bps"],
                    ext["directional_hit_rate"], en["median_ms"], en["p95_ms"], en["p99_ms"],
                    en["max_ms"], ex["median_ms"], ex["p95_ms"], ex["p99_ms"], ex["max_ms"],
                    d["binance_reference_spearman_100ms"],
                ])

    s = report.get("summary") or {}
    p = (s.get("latencies") or {}).get("100") or {}
    t = (s.get("latencies") or {}).get("250") or {}
    lines = [
        "# SC001-E002 OKX Q1 Replication",
        "",
        f"- Verdict: `{report.get('verdict')}`",
        "- Scope: five frozen 2024-Q1 OKX UTC days",
        "- Feature: exact E002 economic mechanism, 5s signed trade-flow continuation",
        "- Strategy P&L: **NO**",
        "- L2 execution profitability: **NO**",
        "- 2024-Q2 OKX accessed: **NO**",
        "- Validation/Final accessed: **NO**",
        "",
        "## Primary 100 ms",
        f"- Positive daily Spearman: {p.get('positive_days')} / 5",
        f"- Median daily Spearman: {p.get('median_daily_spearman')}",
        f"- Sign-test p: {p.get('one_sided_sign_pvalue')}",
        f"- Positive extreme spread days: {p.get('positive_extreme_spread_days')} / 5",
        f"- Median extreme spread bps: {p.get('median_daily_extreme_spread_bps')}",
        "",
        "## Stress 250 ms",
        f"- Positive daily Spearman: {t.get('positive_days')} / 5",
        f"- Median daily Spearman: {t.get('median_daily_spearman')}",
        "",
        "## Boundary",
        "Predictive same-venue feature replication only. No spread/depth/fee/capital P&L claim.",
    ]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")

    atomic_json(SAFETY, {
        "stage": STAGE,
        "workspace_bytes_after_outputs": dir_size(WORKSPACE),
        "free_bytes_after_outputs": free_bytes(),
        "workspace_cap_bytes": WORKSPACE_CAP_BYTES,
        "minimum_free_reserve_bytes": MIN_FREE_RESERVE_BYTES,
        "network_bytes_read": 0,
        "q2_okx_accessed": False,
        "strategy_pnl_calculated": False,
        "execution_profitability_calculated": False,
        "validation_or_final_accessed": False,
    })


def main():
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    safety_check()
    parent_days = load_parent_days()

    report = {
        "stage": STAGE,
        "version": VERSION,
        "protocol_commit": PROTOCOL_COMMIT,
        "started_at_utc": now_iso(),
        "scope": {
            "venue": "OKX",
            "instrument": TARGET_INSTRUMENT,
            "dates": sorted(EVENT_META),
            "grid_ms": GRID_MS,
            "lookback_ms": LOOKBACK_MS,
            "horizon_ms": HORIZON_MS,
            "latencies_ms": list(LATENCIES_MS),
            "signal": "signed price*size imbalance; OKX side=trade side of taker",
            "source_rule": "Q006R-qualified D+D+1 filtered to UTC [D,D+1)",
        },
        "strategy_features_calculated": True,
        "future_returns_calculated": True,
        "strategy_pnl_calculated": False,
        "execution_profitability_calculated": False,
        "q2_okx_accessed": False,
        "validation_or_final_accessed": False,
        "daily": [],
    }

    try:
        for day in parent_days:
            print(f"[{day['date']}] OKX E002 replication...")
            result = process_day(day)
            report["daily"].append(result)
            report["days_processed"] = len(report["daily"])
            write_outputs(report)
            safety_check()

        report["summary"] = summarize(report["daily"])
        report["verdict"] = report["summary"]["verdict"]
        report["finished_at_utc"] = now_iso()
        write_outputs(report)
        print(
            f"COMPLETE: {report['verdict']} | days={len(report['daily'])} | "
            "P&L=NO | Q2_OKX=NO | VALIDATION_FINAL=NO"
        )
    except Exception as exc:
        report["verdict"] = "ERROR"
        report["error"] = repr(exc)
        report["finished_at_utc"] = now_iso()
        write_outputs(report)
        raise


if __name__ == "__main__":
    main()
