from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import statistics
import subprocess
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence

from sc001_selection_causal_utils_v0_1 import Trade, Bar, build_time_bars, return_bps

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))).expanduser().resolve()
FREEZE = ROOT / "docs/research/sc001-c1-c6-sentinel-implementation-freeze-v0.1.json"
GOLDEN = DATA_ROOT / "SC001_SELECTION_CAUSAL_UTILS_GOLDEN" / "sc001_selection_causal_utils_golden_report_v0_1.json"

ASSETS = ("BTC", "ETH", "DOGE", "ORDI", "UNI", "XRP", "OP", "BCH")
JULY_PERF = tuple(f"2024-07-{d:02d}" for d in range(1, 15))
SEP_PERF = tuple(f"2024-09-{d:02d}" for d in range(1, 15))
PERF_DAYS = JULY_PERF + SEP_PERF
WARMUP_BY_WINDOW = {"JULY": "2024-06-30", "SEPTEMBER": "2024-08-31"}
PERF_BY_WINDOW = {"JULY": JULY_PERF, "SEPTEMBER": SEP_PERF}
SWAP_ROOT_BY_WINDOW = {
    "JULY": DATA_ROOT / "SC001_E007R1_TRADE_ACQUISITION" / "archives",
    "SEPTEMBER": DATA_ROOT / "SC001_E009_TRADE_ACQUISITION" / "archives",
}
SPOT_ROOT = DATA_ROOT / "SC001_C1_SPOT_SELECTION_CALIBRATION" / "archives"
HEADER = ["instrument_name", "trade_id", "side", "price", "size", "created_time"]
UTC = timezone.utc
DAY_MS = 86_400_000


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required JSON: {path}")
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_ts_ms(text: str) -> int:
    v = int(str(text).strip())
    av = abs(v)
    if av >= 10**17:
        return v // 1_000_000
    if av >= 10**14:
        return v // 1_000
    if av >= 10**11:
        return v
    if av >= 10**9:
        return v * 1000
    fail(f"unresolved timestamp scale: {text!r}")


def date_ms(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=UTC).timestamp() * 1000)


def next_day(day: str) -> str:
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=UTC) + timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def day_text(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=UTC).strftime("%Y-%m-%d")


def in_performance_day(ts_ms: int) -> bool:
    return day_text(ts_ms) in PERF_DAYS


def require_global_parents() -> dict:
    gold = load_json(GOLDEN)
    if gold.get("status") != "SC001_SELECTION_CAUSAL_UTILS_GOLDEN_PASS":
        fail("shared causal utilities golden report not exact PASS")
    if int(gold.get("check_count", 0)) != 11:
        fail("shared causal utilities golden check count mismatch")
    if any(gold.get(k) is not False for k in (
        "market_data_body_required",
        "strategy_signal_calculated",
        "sentinel_outcome_calculated",
        "pnl_calculated",
        "protected_market_data_accessed",
        "promotional_alpha_accessed",
    )):
        fail("shared causal utilities golden firewall mismatch")

    j = load_json(DATA_ROOT / "SC001_E007R1_TRADE_SEMANTIC_INTEGRITY" / "sc001_e007r1_trade_semantic_integrity_report.json")
    s = load_json(DATA_ROOT / "SC001_E009_TRADE_SEMANTIC_INTEGRITY" / "sc001_e009_trade_semantic_integrity_report.json")
    c1 = load_json(DATA_ROOT / "SC001_C1_SPOT_SELECTION_CALIBRATION" / "sc001_c1_spot_body_integrity_report_v0_1.json")

    if j.get("status") != "E007R1_TRADE_SEMANTIC_INTEGRITY_PASS":
        fail("July semantic parent not PASS")
    if s.get("status") != "E009_TRADE_SEMANTIC_INTEGRITY_PASS":
        fail("September semantic parent not PASS")
    if c1.get("status") != "C1_SPOT_BODY_INTEGRITY_PASS":
        fail("C1 spot parent not PASS")
    if int(j.get("source_files_qualified", 0)) != 128 or int(j.get("reconstructed_utc_days_qualified", 0)) != 120:
        fail("July semantic counts mismatch")
    if int(s.get("source_files_qualified", 0)) != 128 or int(s.get("reconstructed_utc_days_qualified", 0)) != 120:
        fail("September semantic counts mismatch")
    if int(c1.get("archive_files_qualified", 0)) != 256 or int(c1.get("reconstructed_utc_asset_days_qualified", 0)) != 240:
        fail("C1 spot counts mismatch")

    if j.get("asset_holdout_accessed") is not False or j.get("august_confirmation_accessed") is not False:
        fail("July semantic firewall mismatch")
    if j.get("strategy_signal_calculated") is not False or j.get("strategy_pnl_calculated") is not False:
        fail("July semantic alpha firewall mismatch")

    if (
        s.get("asset_holdout_accessed") is not False
        or s.get("october_confirmation_accessed") is not False
        or s.get("august_repurposed") is not False
    ):
        fail("September semantic firewall mismatch")
    if s.get("strategy_signal_calculated") is not False or s.get("strategy_pnl_calculated") is not False:
        fail("September semantic alpha firewall mismatch")

    c1_false = (
        "strategy_signal_calculated",
        "sentinel_outcome_calculated",
        "basis_calculated",
        "returns_calculated",
        "pnl_calculated",
        "promotional_alpha_accessed",
        "protected_holdout_body_accessed",
        "july_gap_body_accessed",
        "august_protected_body_accessed",
        "october_confirmation_body_accessed",
        "legacy_e006_confirmation_body_accessed",
    )
    for key in c1_false:
        if c1.get(key) is not False:
            fail(f"C1 spot firewall mismatch: {key}")

    return {"golden": gold, "july": j, "september": s, "c1_spot": c1}


def require_sentinel_identity(candidate: str, runner_path: Path) -> dict:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_FIRST_SENTINEL_OUTCOME":
        fail("sentinel implementation freeze status mismatch")
    if int(fr.get("total_strategy_variants", 0)) != 11:
        fail("sentinel variant budget mismatch")
    runners = fr.get("runners") or {}
    row = runners.get(candidate)
    if not isinstance(row, dict):
        fail(f"candidate missing from implementation freeze: {candidate}")
    actual = git_blob(runner_path.resolve())
    if row.get("git_blob_sha") != actual:
        fail(f"{candidate} runner identity mismatch {actual} != {row.get('git_blob_sha')}")
    common = Path(__file__).resolve()
    if fr.get("common_helper_git_blob_sha") != git_blob(common):
        fail("common helper identity mismatch")
    causal = ROOT / "research/sc001/sc001_selection_causal_utils_v0_1.py"
    if fr.get("causal_utils_git_blob_sha") != git_blob(causal):
        fail("causal utils identity mismatch")
    return fr


def _read_archive_rows(path: Path, expected_inst: str, lo: int, hi: int) -> Iterable[Trade]:
    if not path.exists():
        fail(f"missing archive: {path}")
    with zipfile.ZipFile(path, "r") as z:
        bad = z.testzip()
        if bad is not None:
            fail(f"ZIP CRC failure {path.name}: {bad}")
        members = [m for m in z.infolist() if not m.is_dir()]
        if len(members) != 1:
            fail(f"unexpected ZIP member count {path.name}: {len(members)}")
        with z.open(members[0], "r") as raw:
            r = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
            if next(r, None) != HEADER:
                fail(f"header mismatch: {path.name}")
            for row in r:
                if not row:
                    continue
                if len(row) != 6 or row[0] != expected_inst:
                    fail(f"bad row/instrument in {path.name}")
                try:
                    tid = int(row[1])
                    side = row[2].lower()
                    price = float(row[3])
                    size = float(row[4])
                    ts = parse_ts_ms(row[5])
                except Exception as exc:
                    raise RuntimeError(f"parse failure {path.name}") from exc
                if side not in {"buy", "sell"} or not math.isfinite(price) or price <= 0 or not math.isfinite(size) or size <= 0:
                    fail(f"invalid trade row in {path.name}")
                if lo <= ts < hi:
                    yield Trade(ts, price, size, side, tid)


def load_day(asset: str, day: str, *, market: str) -> list[Trade]:
    if asset not in ASSETS:
        fail(f"unexpected asset {asset}")
    if day.startswith("2024-07") or day == "2024-06-30":
        window = "JULY"
    elif day.startswith("2024-09") or day == "2024-08-31":
        window = "SEPTEMBER"
    else:
        fail(f"day outside frozen sandbox: {day}")

    d1 = next_day(day)
    allowed = set((WARMUP_BY_WINDOW[window],) + PERF_BY_WINDOW[window] + ((next_day(PERF_BY_WINDOW[window][-1])),))
    if day not in allowed or d1 not in allowed:
        fail(f"D+D1 source outside frozen labels for {asset} {day}")

    if market == "swap":
        root = SWAP_ROOT_BY_WINDOW[window] / asset
        inst = f"{asset}-USDT-SWAP"
    elif market == "spot":
        root = SPOT_ROOT / asset
        inst = f"{asset}-USDT"
    else:
        fail(f"unsupported market {market}")

    lo = date_ms(day)
    hi = lo + DAY_MS
    out: list[Trade] = []
    for label in (day, d1):
        p = root / f"{inst}-trades-{label}.zip"
        out.extend(_read_archive_rows(p, inst, lo, hi))

    if not out:
        fail(f"no admitted trades for {market} {asset} {day}")
    # Preserve qualified source order; fail closed on any reversal/duplicate.
    prev_ts = prev_id = None
    for t in out:
        if prev_ts is not None and t.ts_ms < prev_ts:
            fail(f"stitched timestamp reversal {market} {asset} {day}")
        if prev_id is not None and t.trade_id is not None and t.trade_id <= prev_id:
            fail(f"stitched trade-id duplicate/backward {market} {asset} {day}")
        prev_ts, prev_id = t.ts_ms, t.trade_id
    return out


def build_asset_bars(asset: str, width_ms: int, *, market: str = "swap") -> list[Bar]:
    out: list[Bar] = []
    for window in ("JULY", "SEPTEMBER"):
        days = (WARMUP_BY_WINDOW[window],) + PERF_BY_WINDOW[window]
        for d in days:
            trades = load_day(asset, d, market=market)
            out.extend(build_time_bars(trades, width_ms, origin_ms=date_ms(d)))
    return out


def bars_by_close(bars: Sequence[Bar]) -> dict[int, Bar]:
    return {b.close_ms: b for b in bars}


def values_mean(xs: Sequence[float]) -> float | None:
    return statistics.fmean(xs) if xs else None


def trimmed_mean(xs: Sequence[float], frac: float = 0.10) -> float | None:
    if not xs:
        return None
    vals = sorted(float(x) for x in xs)
    k = math.floor(len(vals) * frac)
    core = vals[k:len(vals)-k] if k else vals
    return statistics.fmean(core) if core else None


def median_or_none(xs: Sequence[float]) -> float | None:
    return statistics.median(xs) if xs else None


def equal_weight_mean(by_asset: dict[str, Sequence[float]], *, require_nonempty: bool = True) -> float | None:
    means = []
    for a in ASSETS:
        vals = list(by_asset.get(a) or [])
        if vals:
            means.append(statistics.fmean(vals))
        elif require_nonempty:
            continue
    return statistics.fmean(means) if means else None


def active_day_count(rows: Sequence[dict], key: str = "date") -> int:
    return len({str(r[key]) for r in rows})


def latest_signal_ms_for_horizon(day: str, horizon_ms: int) -> int:
    return date_ms(day) + DAY_MS - horizon_ms


def signal_day_allowed(ts_ms: int, horizon_ms: int) -> bool:
    d = day_text(ts_ms)
    return d in PERF_DAYS and ts_ms <= latest_signal_ms_for_horizon(d, horizon_ms)


def outcome_close_price(bar_map: dict[int, Bar], decision_ms: int, horizon_ms: int) -> float | None:
    b = bar_map.get(decision_ms + horizon_ms)
    return None if b is None else float(b.close)


def summarize_asset_effects(rows: Sequence[dict], value_key: str) -> dict:
    by: dict[str, list[float]] = {a: [] for a in ASSETS}
    for r in rows:
        a = str(r["asset"])
        v = r.get(value_key)
        if a in by and v is not None:
            by[a].append(float(v))
    means = {a: (statistics.fmean(v) if v else None) for a, v in by.items()}
    active = {a: v for a, v in means.items() if v is not None}
    return {
        "by_asset_values": by,
        "asset_means": means,
        "active_assets": sorted(active),
        "active_asset_count": len(active),
        "equal_weight_asset_mean": statistics.fmean(active.values()) if active else None,
        "median_active_asset_mean": statistics.median(active.values()) if active else None,
        "positive_active_assets": sum(1 for v in active.values() if v > 0),
    }


def ordinary_ols_beta(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 20:
        return None
    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)
    var = sum((x-mx)**2 for x in xs)
    if var <= 0:
        return None
    cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    return cov / var


def one_shot_guard(report: Path, terminal_keys: set[str]) -> None:
    if report.exists():
        old = load_json(report)
        if old.get("status") in terminal_keys:
            fail(f"one-shot guard: terminal report already exists: {old.get('status')}")
