from __future__ import annotations

import bisect
import csv
import hashlib
import itertools
import json
import math
import os
import shutil
import subprocess
import tarfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C7-D1-MULTI-ASSET-L2-INTEGRITY-NORMALIZATION-V0.1"
PASS = "C7_D1_MULTI_ASSET_L2_INTEGRITY_PASS"
REVIEW = "C7_D1_MULTI_ASSET_L2_INTEGRITY_REVIEW"

FIXED_DATE = "2024-02-12"
DAY_START_MS = 1707696000000
DAY_END_MS = 1707782400000

INSTS = (
    "ETH-USDT-SWAP",
    "DOGE-USDT-SWAP",
    "ORDI-USDT-SWAP",
    "UNI-USDT-SWAP",
    "XRP-USDT-SWAP",
    "OP-USDT-SWAP",
    "BCH-USDT-SWAP",
)

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
DISCOVERY_PATH = "/priapi/v5/broker/public/trade-data/download-link"
REFERER = "https://www.okx.com/historical-data"
ALLOWED_STATIC_PREFIX = "static.okx."

GRID_MS = 1000
STALE_MS = 1000

TIMEOUT = 120
RETRIES = 3
MAX_RESPONSE_BYTES = 4_000_000
MAX_FILE_BYTES = 1024**3
MAX_TOTAL_BYTES = 3 * 1024**3
MIN_FREE_RESERVE = 15 * 1024**3
CHUNK = 1024 * 1024

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c7-d1-multi-asset-l2-body-integrity-normalization-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.14.json"
FREEZE = ROOT / "docs/research/sc001-c7-d1-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D0_REPORT = (
    DATA_ROOT / "SC001_C7_D0_MULTI_ASSET_L2_METADATA"
    / "sc001_c7_d0_multi_asset_l2_metadata_report_v0_1.json"
)

OUT_DIR = DATA_ROOT / "SC001_C7_D1_MULTI_ASSET_L2"
ARCHIVE_DIR = OUT_DIR / "archives"
NORMALIZED_DIR = OUT_DIR / "normalized"
OUT = OUT_DIR / "sc001_c7_d1_multi_asset_l2_integrity_report_v0_1.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        fail(f"JSON object expected: {path}")
    return x


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
        for chunk in iter(lambda: f.read(8 * CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def require_freeze() -> None:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_C7_D1_RUN":
        fail("C7-D1 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C7-D1 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C7-D1 protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("C7-D1 registry identity mismatch")
    if tuple(fr.get("universe") or ()) != INSTS:
        fail("C7-D1 universe mismatch")
    if fr.get("fixed_date") != FIXED_DATE:
        fail("C7-D1 date mismatch")
    if int(fr.get("grid_ms", 0)) != GRID_MS:
        fail("C7-D1 grid mismatch")
    if int(fr.get("stale_limit_ms", 0)) != STALE_MS:
        fail("C7-D1 stale limit mismatch")
    for k in (
        "quoted_spread_authorized",
        "c7_asset_eligibility_authorized",
        "maker_order_simulation_authorized",
        "fill_model_authorized",
        "queue_model_authorized",
        "adverse_selection_outcome_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C7-D1 firewall mismatch: {k}")


def require_registry() -> None:
    reg = load_json(REGISTRY)
    if str(reg.get("version")) != "0.14":
        fail("registry version mismatch")
    row = reg.get("c7_spread_selection_calibration") or {}
    if row.get("classification") != "NONPROMOTIONAL_SELECTION_CALIBRATION":
        fail("C7 calibration classification mismatch")
    if tuple(row.get("universe") or ()) != INSTS:
        fail("C7 registry universe mismatch")
    if row.get("target_utc_date") != FIXED_DATE:
        fail("C7 registry date mismatch")
    if row.get("body_access_authorized") is not True:
        fail("C7 body access not authorized")
    for k in (
        "maker_order_simulation_authorized",
        "fill_model_authorized",
        "queue_model_authorized",
        "pnl_authorized",
        "promotional_evidence_authorized",
    ):
        if row.get(k) is not False:
            fail(f"C7 registry firewall mismatch: {k}")


def require_d0() -> dict:
    rep = load_json(D0_REPORT)
    if rep.get("status") != "C7_D0_MULTI_ASSET_L2_METADATA_PASS":
        fail("C7-D0 parent not exact PASS")
    if int(rep.get("assets_passed", 0)) != len(INSTS):
        fail("C7-D0 assets_passed mismatch")
    if tuple(rep.get("universe") or ()) != INSTS:
        fail("C7-D0 parent universe mismatch")
    for k in (
        "historical_l2_body_downloaded",
        "historical_l2_body_opened",
        "spread_calculated",
        "top_of_book_depth_calculated",
        "maker_order_simulated",
        "fill_model_calculated",
        "queue_model_calculated",
        "adverse_selection_calculated",
        "pnl_calculated",
        "promotional_alpha_accessed",
    ):
        if rep.get(k) is not False:
            fail(f"C7-D0 parent firewall mismatch: {k}")
    return rep


def trusted_static(url: str, expected_basename: str) -> bool:
    try:
        p = urllib.parse.urlparse(url)
        return (
            p.scheme == "https"
            and (p.hostname or "").lower().startswith(ALLOWED_STATIC_PREFIX)
            and Path(p.path).name == expected_basename
        )
    except Exception:
        return False


def walk_nodes(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk_nodes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_nodes(v)


def resolve_l2(inst: str, uly: str, expected_filename: str) -> str:
    payload = {
        "module": "4",
        "instType": "SWAP",
        "instQueryParam": {"instFamilyList": [uly]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(DAY_START_MS),
            "end": str(DAY_END_MS - 1),
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    last = None
    for domain in OKX_DOMAINS:
        url = domain + DISCOVERY_PATH + "?t=" + str(int(time.time() * 1000))
        try:
            req = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C7-D1/0.1",
                    "Accept": "application/json,*/*",
                    "Content-Type": "application/json",
                    "Referer": REFERER,
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_RESPONSE_BYTES + 1)
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()

            if len(raw) > MAX_RESPONSE_BYTES:
                fail(f"{inst} metadata response cap exceeded")
            if status != 200:
                fail(f"{inst} metadata HTTP {status}")
            p = urllib.parse.urlparse(final)
            if p.scheme != "https" or (p.hostname or "").lower() not in {
                "www.okx.com", "us.okx.com"
            }:
                fail(f"{inst} metadata unexpected host: {p.hostname}")

            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                fail(f"{inst} metadata code mismatch")

            found: list[str] = []
            for node in walk_nodes(obj.get("data")):
                if not isinstance(node, dict):
                    continue
                fn = node.get("filename") or node.get("fileName")
                u = node.get("url")
                if (
                    fn == expected_filename
                    and isinstance(u, str)
                    and trusted_static(u, expected_filename)
                    and u not in found
                ):
                    found.append(u)

            if len(found) == 1:
                return found[0]
            if len(found) > 1:
                fail(f"{inst} multiple exact trusted URLs")
            last = RuntimeError(f"{inst} exact file not found")
        except Exception as exc:
            last = exc
            continue

    raise RuntimeError(f"{inst} L2 resolution failed: {type(last).__name__}: {last}")


def head_size(url: str, expected_basename: str) -> int:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C7-D1/0.1",
                    "Referer": REFERER,
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                cl = resp.headers.get("Content-Length")

            if status != 200:
                fail(f"HEAD HTTP {status}: {expected_basename}")
            if not trusted_static(final, expected_basename):
                fail(f"HEAD identity mismatch: {expected_basename}")
            if not cl or not cl.isdigit() or int(cl) <= 0:
                fail(f"invalid Content-Length: {expected_basename}")
            return int(cl)
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))

    raise RuntimeError(
        f"HEAD failed {expected_basename}: {type(last).__name__}: {last}"
    )


def download_exact(url: str, expected_basename: str, expected_size: int) -> tuple[Path, bool]:
    if expected_size <= 0 or expected_size > MAX_FILE_BYTES:
        fail(f"file size outside cap: {expected_basename} {expected_size}")

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    dest = ARCHIVE_DIR / expected_basename

    if dest.exists() and dest.stat().st_size == expected_size:
        return dest, True
    if dest.exists():
        dest.unlink()

    tmp = Path(str(dest) + ".part")
    tmp.unlink(missing_ok=True)

    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "BotMarketplace-SC001-C7-D1/0.1",
            "Referer": REFERER,
        },
    )

    total = 0
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp, tmp.open("wb") as out:
        final = resp.geturl()
        if not trusted_static(final, expected_basename):
            fail(f"GET identity mismatch: {expected_basename}")

        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > expected_size or total > MAX_FILE_BYTES:
                fail(f"download overflow: {expected_basename}")
            out.write(chunk)

        out.flush()
        os.fsync(out.fileno())

    if total != expected_size:
        fail(
            f"download size mismatch {expected_basename}: "
            f"{total} != {expected_size}"
        )

    os.replace(tmp, dest)
    return dest, False


def parse_level(x) -> tuple[float, float, int]:
    if not isinstance(x, list) or len(x) != 3:
        fail("L2 level shape")
    p = float(x[0])
    s = float(x[1])
    oc = float(x[2])
    o = int(round(oc))
    if not (math.isfinite(p) and math.isfinite(s) and math.isfinite(oc)):
        fail("nonfinite L2 level")
    if p <= 0 or s < 0 or o < 0 or abs(oc - o) > 1e-9:
        fail("invalid L2 level")
    if s == 0 and o != 0:
        fail("zero-size delete with nonzero order count")
    return p, s, o


def apply_levels(book: dict, prices: list, levels: list[tuple[float, float, int]]) -> None:
    for p, s, o in levels:
        if s == 0:
            if p not in book:
                fail(f"delete missing L2 level {p}")
            del book[p]
            i = bisect.bisect_left(prices, p)
            if i < len(prices) and prices[i] == p:
                prices.pop(i)
        else:
            if p not in book:
                bisect.insort(prices, p)
            book[p] = (s, o)


def valid_book(asks: dict, bids: dict, ap: list, bp: list) -> bool:
    if not ap or not bp:
        return False
    best_ask = ap[0]
    best_bid = bp[-1]
    if best_bid >= best_ask:
        return False
    return asks[best_ask][0] > 0 and bids[best_bid][0] > 0


def iter_l2(path: Path, inst: str):
    with tarfile.open(path, mode="r|gz") as tf:
        regular = 0
        first = True
        last_ts = None

        for member in tf:
            if not member.isfile():
                continue

            regular += 1
            if regular > 1:
                fail(f"{inst} multiple regular members")

            f = tf.extractfile(member)
            if f is None:
                fail(f"{inst} cannot extract member")

            for raw in f:
                if not raw.strip():
                    continue
                r = json.loads(raw)

                if not isinstance(r, dict) or r.get("instId") != inst:
                    fail(f"{inst} record/instrument mismatch")

                action = r.get("action")
                if action not in {"snapshot", "update"}:
                    fail(f"{inst} invalid action")

                ts = int(r.get("ts"))
                if last_ts is not None and ts < last_ts:
                    fail(f"{inst} timestamp reversal")
                if first and action != "snapshot":
                    fail(f"{inst} first action not snapshot")

                first = False
                last_ts = ts

                aa = r.get("asks")
                bb = r.get("bids")
                if not isinstance(aa, list) or not isinstance(bb, list):
                    fail(f"{inst} invalid sides")

                pa = [parse_level(x) for x in aa]
                pb = [parse_level(x) for x in bb]

                if len({x[0] for x in pa}) != len(pa):
                    fail(f"{inst} duplicate ask price in record")
                if len({x[0] for x in pb}) != len(pb):
                    fail(f"{inst} duplicate bid price in record")

                yield ts, action, pa, pb

        if regular != 1:
            fail(f"{inst} regular member count={regular}")


def normalize_asset(path: Path, inst: str, out_csv: Path) -> dict:
    asks: dict = {}
    bids: dict = {}
    ap: list = []
    bp: list = []

    next_grid = DAY_START_MS
    last_l2_ts = None
    valid_seconds = 0
    stale_seconds = 0
    invalid_seconds = 0
    active_hours = set()
    records = snapshots = updates = 0

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(out_csv) + ".tmp")

    with tmp.open("w", encoding="utf-8", newline="") as out:
        w = csv.writer(out)
        w.writerow([
            "second_id",
            "l2_ts_ms",
            "best_bid",
            "best_ask",
            "best_bid_size",
            "best_ask_size",
        ])

        def emit(boundary_ms: int) -> None:
            nonlocal valid_seconds, stale_seconds, invalid_seconds
            if not (DAY_START_MS <= boundary_ms < DAY_END_MS):
                return

            if last_l2_ts is None or boundary_ms - last_l2_ts > STALE_MS:
                stale_seconds += 1
                return

            if not valid_book(asks, bids, ap, bp):
                invalid_seconds += 1
                return

            best_bid = bp[-1]
            best_ask = ap[0]
            bid_size = float(bids[best_bid][0])
            ask_size = float(asks[best_ask][0])

            if not (
                math.isfinite(best_bid) and best_bid > 0
                and math.isfinite(best_ask) and best_ask > best_bid
                and math.isfinite(bid_size) and bid_size > 0
                and math.isfinite(ask_size) and ask_size > 0
            ):
                fail(f"{inst} invalid normalized top-of-book")

            sec = boundary_ms // 1000
            w.writerow([
                sec,
                last_l2_ts,
                format(best_bid, ".12g"),
                format(best_ask, ".12g"),
                format(bid_size, ".12g"),
                format(ask_size, ".12g"),
            ])
            valid_seconds += 1
            active_hours.add((boundary_ms - DAY_START_MS) // 3_600_000)

        for t, group in itertools.groupby(iter_l2(path, inst), key=lambda x: x[0]):
            t = int(t)

            while next_grid < t and next_grid < DAY_END_MS:
                emit(next_grid)
                next_grid += GRID_MS

            rows = list(group)
            for _ts, action, aa, bb in rows:
                if action == "snapshot":
                    asks.clear()
                    bids.clear()
                    ap.clear()
                    bp.clear()
                    snapshots += 1
                else:
                    updates += 1

                apply_levels(asks, ap, aa)
                apply_levels(bids, bp, bb)
                records += 1

                if not valid_book(asks, bids, ap, bp):
                    fail(f"{inst} invalid reconstructed book at {t}")

            last_l2_ts = t

            if next_grid == t and next_grid < DAY_END_MS:
                emit(next_grid)
                next_grid += GRID_MS

        while next_grid < DAY_END_MS:
            emit(next_grid)
            next_grid += GRID_MS

        out.flush()
        os.fsync(out.fileno())

    os.replace(tmp, out_csv)

    return {
        "records_parsed": records,
        "snapshot_records": snapshots,
        "update_records": updates,
        "valid_sampled_seconds": valid_seconds,
        "stale_sampled_seconds": stale_seconds,
        "invalid_sampled_seconds": invalid_seconds,
        "active_utc_hours": len(active_hours),
        "normalized_file": {
            "path": str(out_csv),
            "bytes": out_csv.stat().st_size,
            "sha256": sha256_file(out_csv),
            "rows": valid_seconds,
        },
    }


def main() -> int:
    try:
        require_freeze()
        require_registry()
        d0 = require_d0()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        by_inst = d0.get("assets") or {}

        expected_total = 0
        expected: dict[str, dict] = {}
        for inst in INSTS:
            row = by_inst.get(inst)
            if not isinstance(row, dict) or row.get("pass") is not True:
                fail(f"D0 asset row invalid: {inst}")
            l2 = row.get("historical_l2") or {}
            meta = row.get("instrument") or {}
            fn = l2.get("filename")
            size = int(l2.get("content_length", 0))
            uly = meta.get("uly")
            if fn != f"{inst}-L2orderbook-400lv-{FIXED_DATE}.tar.gz":
                fail(f"D0 filename mismatch: {inst}")
            if size <= 0:
                fail(f"D0 size missing: {inst}")
            if not isinstance(uly, str) or not uly:
                fail(f"D0 uly missing: {inst}")
            expected_total += size
            expected[inst] = {"filename": fn, "size": size, "uly": uly}

        if expected_total > MAX_TOTAL_BYTES:
            fail(f"combined D0 size exceeds cap: {expected_total}")

        if shutil.disk_usage(DATA_ROOT).free < expected_total + MIN_FREE_RESERVE:
            fail("insufficient free-disk reserve for C7-D1")

        assets = {}
        all_pass = True
        downloaded_files = 0
        reused_files = 0

        for i, inst in enumerate(INSTS, start=1):
            print(f"C7-D1 [{i}/7] {inst}", flush=True)
            meta = expected[inst]

            try:
                print(f"{inst}: resolve exact historical L2 URL", flush=True)
                url = resolve_l2(inst, meta["uly"], meta["filename"])

                size_now = head_size(url, meta["filename"])
                if size_now != meta["size"]:
                    fail(
                        f"{inst} HEAD size changed: "
                        f"{size_now} != {meta['size']}"
                    )

                print(f"{inst}: download/reuse body", flush=True)
                path, reused = download_exact(
                    url,
                    meta["filename"],
                    meta["size"],
                )

                if reused:
                    reused_files += 1
                else:
                    downloaded_files += 1

                digest = sha256_file(path)

                asset = inst.split("-")[0]
                norm_path = NORMALIZED_DIR / f"{asset}_top1_1s.csv"

                print(f"{inst}: replay + normalize causal 1s top-of-book", flush=True)
                norm = normalize_asset(path, inst, norm_path)

                asset_pass = (
                    norm["valid_sampled_seconds"] >= 80_000
                    and norm["active_utc_hours"] == 24
                )

                assets[inst] = {
                    "integrity_pass": asset_pass,
                    "source_archive": {
                        "filename": meta["filename"],
                        "bytes": path.stat().st_size,
                        "sha256": digest,
                        "reused": reused,
                    },
                    "normalization": norm,
                }

                if not asset_pass:
                    all_pass = False

                print(
                    f"{'PASS' if asset_pass else 'REVIEW'} {inst} "
                    f"valid_seconds={norm['valid_sampled_seconds']} "
                    f"hours={norm['active_utc_hours']} "
                    f"reused={reused}",
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

        status = PASS if all_pass and len(assets) == len(INSTS) else REVIEW

        report = {
            "stage": STAGE,
            "version": "0.1",
            "status": status,
            "fixed_date": FIXED_DATE,
            "universe": list(INSTS),
            "assets": assets,
            "assets_passed": sum(
                1 for x in assets.values()
                if x.get("integrity_pass") is True
            ),
            "expected_total_source_bytes": expected_total,
            "downloaded_files": downloaded_files,
            "reused_files": reused_files,
            "historical_l2_bodies_opened": True,
            "per_asset_top_of_book_normalized": True,
            "quoted_spread_calculated": False,
            "c7_asset_eligibility_calculated": False,
            "maker_order_simulated": False,
            "fill_model_calculated": False,
            "queue_model_calculated": False,
            "adverse_selection_outcome_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, report)

        print(status)
        print("assets_passed =", report["assets_passed"], "/", len(INSTS))
        print("downloaded_files =", downloaded_files, "reused_files =", reused_files)
        print("historical L2 bodies opened = True")
        print("per-asset top-of-book normalized = True")
        print("quoted spread / asset eligibility = False / False")
        print("maker/fill/queue/adverse-selection/PnL = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)
        return 0 if status == PASS else 2

    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "version": "0.1",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "historical_l2_bodies_opened": False,
            "per_asset_top_of_book_normalized": False,
            "quoted_spread_calculated": False,
            "c7_asset_eligibility_calculated": False,
            "maker_order_simulated": False,
            "fill_model_calculated": False,
            "queue_model_calculated": False,
            "adverse_selection_outcome_calculated": False,
            "pnl_calculated": False,
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
