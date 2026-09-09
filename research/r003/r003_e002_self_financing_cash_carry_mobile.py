"""Android/Pydroid resumable launcher for frozen R003-E002 cash-and-carry study.

Implementation-only revision: the frozen research engine/economic rules are unchanged.
This launcher adds a persistent workspace, atomic page caching, resume after interruption,
a fixed first-run data cutoff, progress logging, and disk-space checks.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
WORKSPACE = DOWNLOAD / "R003_E002_WORKSPACE"
CACHE = WORKSPACE / "_cache"
RESULTS = WORKSPACE / "results"
SNAPSHOT_FILE = WORKSPACE / "snapshot.json"

# Economic/accounting engine remains exactly the pre-result frozen commit.
ENGINE_COMMIT = "84ab935899b22b8610d7184b192a1b5e8e6df36d"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r003/r003_e002_self_financing_cash_carry.py"
)
ENGINE_FILE = WORKSPACE / "r003_e002_self_financing_cash_carry_v0_1.py"

RECOMMENDED_FREE_MB = 250
HARD_MIN_FREE_MB = 100


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_write_json(path: Path, obj: dict) -> None:
    data = json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")
    atomic_write_bytes(path, data)


def safe_label(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", label)


def workspace_size_mb() -> float:
    total = 0
    if WORKSPACE.exists():
        for p in WORKSPACE.rglob("*"):
            if p.is_file():
                try:
                    total += p.stat().st_size
                except OSError:
                    pass
    return total / (1024 * 1024)


def check_disk() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    free_mb = shutil.disk_usage(DOWNLOAD).free / (1024 * 1024)
    print(f"Free storage in Download volume: {free_mb:,.0f} MB")
    print("Expected final workspace is usually well below 100 MB; 250 MB free is recommended.")
    if free_mb < HARD_MIN_FREE_MB:
        raise RuntimeError(
            f"Only {free_mb:.0f} MB free. Please free at least {HARD_MIN_FREE_MB} MB before R003-E002."
        )
    if free_mb < RECOMMENDED_FREE_MB:
        print(
            f"WARNING: less than recommended {RECOMMENDED_FREE_MB} MB free. "
            "The run may still fit, but extra headroom is safer."
        )


def load_or_create_snapshot() -> dict:
    if SNAPSHOT_FILE.exists():
        snap = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
        if snap.get("engine_commit") != ENGINE_COMMIT:
            raise RuntimeError("Workspace belongs to a different frozen engine commit")
        return snap

    now = datetime.now(timezone.utc)
    snap = {
        "created_at_utc": now.isoformat(),
        "cutoff_ms": int(now.timestamp() * 1000),
        "engine_commit": ENGINE_COMMIT,
        "purpose": "fixed first-run snapshot for resumable R003-E002 historical implementation study",
    }
    atomic_write_json(SNAPSHOT_FILE, snap)
    return snap


def download_engine() -> None:
    req = Request(ENGINE_URL, headers={"User-Agent": "r003-research-mobile-resume/0.2"})
    with urlopen(req, timeout=60) as resp:
        raw = resp.read()
    atomic_write_bytes(ENGINE_FILE, raw)


def load_manifest(label: str, source_url: str, cutoff_ms: int, kind: str, interval: str | None, limit: int) -> tuple[Path, dict]:
    folder = CACHE / safe_label(label)
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "manifest.json"
    expected = {
        "format_version": 1,
        "label": label,
        "source_url": source_url,
        "kind": kind,
        "interval": interval,
        "limit": int(limit),
        "cutoff_ms": int(cutoff_ms),
    }
    if manifest_path.exists():
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        for k, v in expected.items():
            if m.get(k) != v:
                raise RuntimeError(f"Cache manifest mismatch for {label}: {k}")
    else:
        m = {**expected, "complete": False, "pages": []}
        atomic_write_json(manifest_path, m)
    return manifest_path, m


def read_page(folder: Path, meta: dict) -> tuple[bytes, object]:
    path = folder / meta["file"]
    raw = gzip.decompress(path.read_bytes())
    sha = hashlib.sha256(raw).hexdigest()
    if sha != meta["sha256"]:
        raise RuntimeError(f"Cached page checksum mismatch: {path}")
    return raw, json.loads(raw.decode("utf-8"))


def cache_page(folder: Path, seq: int, raw: bytes, count: int, first_key: int | None, last_key: int | None) -> dict:
    name = f"page_{seq:04d}.json.gz"
    compressed = gzip.compress(raw, compresslevel=6)
    atomic_write_bytes(folder / name, compressed)
    return {
        "seq": int(seq),
        "file": name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "rows": int(count),
        "first_key": None if first_key is None else int(first_key),
        "last_key": None if last_key is None else int(last_key),
        "compressed_bytes": int(len(compressed)),
    }


def install_resumable_fetchers(ns: dict, cutoff_ms: int) -> None:
    pd = ns["pd"]
    np = ns["np"]
    SYMBOL = ns["SYMBOL"]
    DOWNLOAD_START = ns["DOWNLOAD_START"]
    get_json = ns["get_json"]

    def fetch_klines_cached(url: str, interval: str, limit: int, label: str):
        manifest_path, manifest = load_manifest(
            label, url, cutoff_ms, "kline", interval, limit
        )
        folder = manifest_path.parent
        rows = []
        hashes = []
        start = int(DOWNLOAD_START.timestamp() * 1000)
        last_open = None

        # Replay already downloaded pages from local compressed cache.
        for meta in manifest["pages"]:
            raw, obj = read_page(folder, meta)
            if not isinstance(obj, list):
                raise RuntimeError(f"Cached {label} page is not a list")
            hashes.append(hashlib.sha256(raw).hexdigest())
            valid = [
                r for r in obj
                if isinstance(r, list) and len(r) >= 7 and int(r[6]) < cutoff_ms
            ]
            rows.extend(valid)
            if obj:
                cur = int(obj[-1][0])
                if last_open is not None and cur <= last_open:
                    raise RuntimeError(f"Cached {label} pagination stalled")
                last_open = cur
                start = cur + 1

        if manifest["pages"]:
            print(
                f"{label}: resumed {len(manifest['pages'])} cached pages, "
                f"{len(rows):,} closed rows available locally"
            )

        while not manifest.get("complete", False):
            raw, obj = get_json(
                url,
                {
                    "symbol": SYMBOL,
                    "interval": interval,
                    "startTime": start,
                    "endTime": cutoff_ms,
                    "limit": limit,
                },
            )
            if not isinstance(obj, list):
                raise RuntimeError(f"{label} source error: {obj}")

            seq = len(manifest["pages"])
            first_key = int(obj[0][0]) if obj else None
            last_key = int(obj[-1][0]) if obj else None
            meta = cache_page(folder, seq, raw, len(obj), first_key, last_key)
            manifest["pages"].append(meta)
            atomic_write_json(manifest_path, manifest)
            hashes.append(meta["sha256"])

            if not obj:
                manifest["complete"] = True
                atomic_write_json(manifest_path, manifest)
                break

            valid = [
                r for r in obj
                if isinstance(r, list) and len(r) >= 7 and int(r[6]) < cutoff_ms
            ]
            rows.extend(valid)
            cur = int(obj[-1][0])
            if last_open is not None and cur <= last_open:
                raise RuntimeError(f"{label} pagination stalled")
            last_open = cur
            start = cur + 1

            print(
                f"{label}: downloaded page {seq + 1}, "
                f"{len(rows):,} closed rows cached"
            )

            if len(obj) < limit or cur >= cutoff_ms:
                manifest["complete"] = True
                atomic_write_json(manifest_path, manifest)
                break

        if not rows:
            raise RuntimeError(f"No closed {label} klines returned")

        x = pd.DataFrame(rows)
        out = pd.DataFrame(
            {
                "open_time": pd.to_datetime(pd.to_numeric(x.iloc[:, 0]), unit="ms", utc=True),
                "open": pd.to_numeric(x.iloc[:, 1], errors="coerce"),
                "high": pd.to_numeric(x.iloc[:, 2], errors="coerce"),
                "low": pd.to_numeric(x.iloc[:, 3], errors="coerce"),
                "close": pd.to_numeric(x.iloc[:, 4], errors="coerce"),
                "close_time": pd.to_datetime(pd.to_numeric(x.iloc[:, 6]), unit="ms", utc=True),
            }
        )
        out = (
            out.dropna()
            .sort_values("open_time")
            .drop_duplicates("open_time", keep="last")
            .reset_index(drop=True)
        )
        if (out[["open", "high", "low", "close"]] <= 0).any().any():
            raise RuntimeError(f"{label} contains non-positive retained prices")
        return out, hashes, len(rows)

    def fetch_funding_cached():
        label = "funding"
        url = ns["FUNDING_URL"]
        limit = 1000
        manifest_path, manifest = load_manifest(
            label, url, cutoff_ms, "funding", None, limit
        )
        folder = manifest_path.parent
        rows = []
        hashes = []
        start = int(DOWNLOAD_START.timestamp() * 1000)
        last = None

        for meta in manifest["pages"]:
            raw, obj = read_page(folder, meta)
            if not isinstance(obj, list):
                raise RuntimeError("Cached funding page is not a list")
            hashes.append(hashlib.sha256(raw).hexdigest())
            valid = [
                r for r in obj
                if isinstance(r, dict)
                and "fundingTime" in r
                and int(r["fundingTime"]) <= cutoff_ms
            ]
            rows.extend(valid)
            if obj:
                cur = int(obj[-1]["fundingTime"])
                if last is not None and cur <= last:
                    raise RuntimeError("Cached funding pagination stalled")
                last = cur
                start = cur + 1

        if manifest["pages"]:
            print(
                f"funding: resumed {len(manifest['pages'])} cached pages, "
                f"{len(rows):,} rows available locally"
            )

        while not manifest.get("complete", False):
            raw, obj = get_json(
                url,
                {
                    "symbol": SYMBOL,
                    "startTime": start,
                    "endTime": cutoff_ms,
                    "limit": limit,
                },
            )
            if not isinstance(obj, list):
                raise RuntimeError(f"Funding source error: {obj}")

            seq = len(manifest["pages"])
            first_key = int(obj[0]["fundingTime"]) if obj else None
            last_key = int(obj[-1]["fundingTime"]) if obj else None
            meta = cache_page(folder, seq, raw, len(obj), first_key, last_key)
            manifest["pages"].append(meta)
            atomic_write_json(manifest_path, manifest)
            hashes.append(meta["sha256"])

            if not obj:
                manifest["complete"] = True
                atomic_write_json(manifest_path, manifest)
                break

            valid = [
                r for r in obj
                if isinstance(r, dict)
                and "fundingTime" in r
                and int(r["fundingTime"]) <= cutoff_ms
            ]
            rows.extend(valid)
            cur = int(obj[-1]["fundingTime"])
            if last is not None and cur <= last:
                raise RuntimeError("Funding pagination stalled")
            last = cur
            start = cur + 1

            print(
                f"funding: downloaded page {seq + 1}, "
                f"{len(rows):,} rows cached"
            )

            if len(obj) < limit or cur >= cutoff_ms:
                manifest["complete"] = True
                atomic_write_json(manifest_path, manifest)
                break

        if not rows:
            raise RuntimeError("No funding history returned")

        x = pd.DataFrame(rows)
        x["funding_time"] = pd.to_datetime(
            pd.to_numeric(x["fundingTime"], errors="coerce"), unit="ms", utc=True
        )
        x["funding_rate"] = pd.to_numeric(x["fundingRate"], errors="coerce")
        x["published_mark_price"] = (
            pd.to_numeric(x["markPrice"], errors="coerce")
            if "markPrice" in x else np.nan
        )
        x["rate_type"] = x["rateType"].astype(str) if "rateType" in x else ""
        x = (
            x.dropna(subset=["funding_time", "funding_rate"])
            .sort_values("funding_time")
            .drop_duplicates("funding_time", keep="last")
            [["funding_time", "funding_rate", "published_mark_price", "rate_type"]]
            .reset_index(drop=True)
        )
        return x, hashes, len(rows)

    ns["fetch_klines"] = fetch_klines_cached
    ns["fetch_funding"] = fetch_funding_cached


def main() -> None:
    print("=" * 72)
    print("R003-E002 SELF-FINANCING BTC CASH-AND-CARRY — RESUMABLE MOBILE RUN")
    print("Frozen economic engine commit:", ENGINE_COMMIT)
    print("Persistent workspace:", WORKSPACE)
    print("Results folder:", RESULTS)
    print("=" * 72)

    check_disk()
    CACHE.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    snap = load_or_create_snapshot()
    cutoff = datetime.fromtimestamp(snap["cutoff_ms"] / 1000, tz=timezone.utc)
    print("Fixed data cutoff for this workspace:", cutoff.isoformat())
    print("If Android/Pydroid stops the process, run the same launcher again.")
    print("Already downloaded pages will be reused; completed downloads are not restarted.\n")

    download_engine()
    source = ENGINE_FILE.read_text(encoding="utf-8")

    # Load the frozen engine without invoking its CLI main(), then replace only
    # its source-download functions with resumable equivalents. Research logic stays frozen.
    ns = {
        "__name__": "r003_e002_frozen_engine",
        "__file__": str(ENGINE_FILE),
    }
    exec(compile(source, str(ENGINE_FILE), "exec"), ns)
    install_resumable_fetchers(ns, int(snap["cutoff_ms"]))

    try:
        ns["run"](RESULTS)
    except Exception as exc:
        print("\nRUN INTERRUPTED/FAILED:", type(exc).__name__, str(exc))
        print("Cache has been preserved. Re-run this same launcher to resume downloads.")
        raise

    print()
    print("RUN FINISHED")
    print("Workspace size:", f"{workspace_size_mb():.1f} MB")
    print("Upload the 9 result files from:")
    print(RESULTS)
    print("Do NOT upload the _cache folder or the .py engine copy.")


if __name__ == "__main__":
    main()
