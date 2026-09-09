"""Android/Pydroid full-universe downloader for R002 Binance USD-M daily archive.

Purpose
-------
Build a broad archive-defined point-in-time dataset from the already collected
Binance USD-M monthly 1d manifest.

Important research choice:
- download EVERY symbol present in the manifest, not only current survivors;
- do not filter by future lifetime, months_count, current status, or performance;
- later strategy eligibility is decided strictly point-in-time after enough
  genuinely traded daily observations exist.

Crash safety:
- one atomic CSV shard per symbol;
- completed symbol shards are skipped on restart;
- checkpoint JSON is updated after every completed/failed symbol;
- optionally reuses compatible shards from the earlier 29-symbol subset.

Standard library only; suitable for Pydroid 3.
"""

import csv
import io
import json
import os
import shutil
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DOWNLOAD = "/storage/emulated/0/Download"

MANIFEST = os.path.join(
    DOWNLOAD,
    "r002_binance_um_1d_manifest.csv",
)

WORKDIR = os.path.join(
    DOWNLOAD,
    "r002_binance_full_universe_parts",
)

LEGACY_SUBSET_WORKDIR = os.path.join(
    DOWNLOAD,
    "r002_binance_historical_subset_parts",
)

OUTPUT = os.path.join(
    DOWNLOAD,
    "r002_binance_full_universe_daily.csv",
)

STATE = os.path.join(
    DOWNLOAD,
    "r002_binance_full_universe_state.json",
)

MAX_WORKERS = 8
MAX_RETRIES = 5
RETRY_BASE_SECONDS = 2
REQUEST_TIMEOUT = 60

FIELDS = [
    "symbol",
    "open_time_ms",
    "date_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time_ms",
    "quote_volume",
    "trades",
    "taker_buy_base",
    "taker_buy_quote",
    "source_month",
]


def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def write_csv_atomic(path, fieldnames, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def part_path(symbol):
    return os.path.join(WORKDIR, f"{symbol}.csv")


def legacy_part_path(symbol):
    return os.path.join(LEGACY_SUBSET_WORKDIR, f"{symbol}.csv")


def validate_part_file(path, symbol):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)

            if r.fieldnames != FIELDS:
                return False

            count = 0
            last_ts = None

            for row in r:
                if row.get("symbol") != symbol:
                    return False

                ts = int(row["open_time_ms"])

                if last_ts is not None and ts <= last_ts:
                    return False

                last_ts = ts
                count += 1

            # Full-universe collector intentionally keeps even very short-lived
            # symbols. The strategy engine will later impose its point-in-time
            # warmup requirement.
            return count >= 1

    except Exception:
        return False


def valid_part(symbol):
    return validate_part_file(part_path(symbol), symbol)


def load_manifest():
    if not os.path.exists(MANIFEST):
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST}\n"
            "Put r002_binance_um_1d_manifest.csv in Android Download."
        )

    by_symbol = {}

    with open(MANIFEST, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)

        required = {"symbol", "month", "archive_url"}
        actual = set(r.fieldnames or [])

        if not required.issubset(actual):
            raise ValueError(
                "Manifest missing required columns: "
                f"{sorted(required - actual)}"
            )

        seen_symbol_month = set()

        for row in r:
            symbol = row.get("symbol", "").strip()
            month = row.get("month", "").strip()
            url = row.get("archive_url", "").strip()

            if not symbol or not month or not url:
                continue

            key = (symbol, month)
            if key in seen_symbol_month:
                continue
            seen_symbol_month.add(key)

            by_symbol.setdefault(symbol, []).append(
                {
                    "symbol": symbol,
                    "month": month,
                    "archive_url": url,
                }
            )

    if not by_symbol:
        raise ValueError("Manifest contains no usable symbol-month archives")

    for symbol in by_symbol:
        by_symbol[symbol].sort(key=lambda x: x["month"])

    return dict(sorted(by_symbol.items()))


def seed_from_legacy_subset(symbols):
    if not os.path.isdir(LEGACY_SUBSET_WORKDIR):
        return 0

    reused = 0

    for symbol in symbols:
        dst = part_path(symbol)

        if valid_part(symbol):
            continue

        src = legacy_part_path(symbol)

        if not validate_part_file(src, symbol):
            continue

        tmp = dst + ".tmp"

        try:
            shutil.copy2(src, tmp)

            if not validate_part_file(tmp, symbol):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                continue

            os.replace(tmp, dst)
            reused += 1

        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass

    return reused


def download_bytes(url):
    req = Request(
        url,
        headers={
            "User-Agent": "r002-full-universe-research/0.1",
            "Accept": "*/*",
        },
    )

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return resp.read()

        except (HTTPError, URLError, TimeoutError, OSError) as e:
            last_error = repr(e)

            if attempt < MAX_RETRIES:
                wait = RETRY_BASE_SECONDS * attempt
                time.sleep(wait)

    raise RuntimeError(
        f"Download failed after {MAX_RETRIES} attempts: "
        f"{url} :: {last_error}"
    )


def normalize_timestamp_to_ms(value):
    ts = int(value)

    # Defensive normalization:
    # ordinary ms epoch ~ 1e12
    # us epoch ~ 1e15
    if ts > 10**14:
        ts //= 1000

    return ts


def parse_zip(symbol, month, blob):
    out = []

    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = [
            name
            for name in zf.namelist()
            if name.lower().endswith(".csv")
        ]

        if not names:
            raise ValueError(f"{symbol} {month}: ZIP has no CSV")

        # Binance monthly kline ZIP normally contains one CSV.
        # Parse all CSV members defensively in case archive format changes.
        for name in names:
            with zf.open(name, "r") as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8")
                reader = csv.reader(text)

                for cols in reader:
                    if not cols:
                        continue

                    try:
                        open_ts = normalize_timestamp_to_ms(cols[0])
                    except Exception:
                        # Header row or malformed row.
                        continue

                    if len(cols) < 11:
                        continue

                    try:
                        close_ts = normalize_timestamp_to_ms(cols[6])
                    except Exception:
                        close_ts = None

                    try:
                        dt = datetime.fromtimestamp(
                            open_ts / 1000,
                            tz=timezone.utc,
                        )
                    except Exception:
                        continue

                    out.append(
                        {
                            "symbol": symbol,
                            "open_time_ms": open_ts,
                            "date_utc": dt.date().isoformat(),
                            "open": cols[1],
                            "high": cols[2],
                            "low": cols[3],
                            "close": cols[4],
                            "volume": cols[5],
                            "close_time_ms": close_ts,
                            "quote_volume": cols[7] if len(cols) > 7 else "",
                            "trades": cols[8] if len(cols) > 8 else "",
                            "taker_buy_base": cols[9] if len(cols) > 9 else "",
                            "taker_buy_quote": cols[10] if len(cols) > 10 else "",
                            "source_month": month,
                        }
                    )

    return out


def collect_symbol(symbol, archives):
    dedup = {}

    for idx, item in enumerate(archives, start=1):
        month = item["month"]
        blob = download_bytes(item["archive_url"])
        rows = parse_zip(symbol, month, blob)

        for row in rows:
            dedup[int(row["open_time_ms"])] = row

        if idx % 24 == 0 or idx == len(archives):
            print(
                f"    {symbol}: "
                f"{idx}/{len(archives)} monthly archives downloaded"
            )

    rows = [dedup[k] for k in sorted(dedup)]

    if not rows:
        raise ValueError(f"{symbol}: zero daily rows after parsing")

    return rows


def rebuild_output(symbols):
    total_rows = 0
    included_symbols = 0
    tmp = OUTPUT + ".tmp"

    with open(tmp, "w", encoding="utf-8", newline="") as out:
        w = csv.DictWriter(out, fieldnames=FIELDS)
        w.writeheader()

        for idx, symbol in enumerate(symbols, start=1):
            if not valid_part(symbol):
                continue

            included_symbols += 1

            with open(
                part_path(symbol),
                "r",
                encoding="utf-8",
                newline="",
            ) as f:
                r = csv.DictReader(f)

                for row in r:
                    w.writerow({k: row.get(k, "") for k in FIELDS})
                    total_rows += 1

            if idx % 100 == 0 or idx == len(symbols):
                print(
                    f"  combine: {idx}/{len(symbols)} symbols scanned, "
                    f"{total_rows} rows written"
                )

        out.flush()
        os.fsync(out.fileno())

    os.replace(tmp, OUTPUT)

    return total_rows, included_symbols


def main():
    os.makedirs(DOWNLOAD, exist_ok=True)
    os.makedirs(WORKDIR, exist_ok=True)

    print("=" * 74)
    print("R002 BINANCE FULL ARCHIVE-DEFINED UNIVERSE DOWNLOADER v0.1")
    print("All manifest symbols; no current-survivor or future-lifetime filter")
    print("Crash-safe / resumable: YES")
    print("=" * 74)

    manifest = load_manifest()
    symbols = list(manifest.keys())

    total_archives = sum(len(v) for v in manifest.values())

    print("Manifest symbols:", len(symbols))
    print("Manifest monthly archives:", total_archives)
    print("Workers:", MAX_WORKERS)
    print()

    reused = seed_from_legacy_subset(symbols)

    if reused:
        print("Reused compatible old subset shards:", reused)
        print()

    completed = [s for s in symbols if valid_part(s)]
    pending = [s for s in symbols if not valid_part(s)]

    state = {
        "version": "0.1",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_symbols": len(symbols),
        "manifest_archives": total_archives,
        "completed": completed,
        "failed": {},
        "reused_legacy_shards_this_run": reused,
    }

    write_json_atomic(STATE, state)

    print("Already completed:", len(completed), "/", len(symbols))
    print("Pending:", len(pending))
    print("Parts:", WORKDIR)
    print()

    completed_set = set(completed)

    if pending:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(
                    collect_symbol,
                    symbol,
                    manifest[symbol],
                ): symbol
                for symbol in pending
            }

            for future in as_completed(futures):
                symbol = futures[future]

                try:
                    rows = future.result()

                    write_csv_atomic(
                        part_path(symbol),
                        FIELDS,
                        rows,
                    )

                    if not valid_part(symbol):
                        raise ValueError(
                            "post-write shard validation failed"
                        )

                    completed_set.add(symbol)
                    state["failed"].pop(symbol, None)

                    print(
                        f"[{len(completed_set)}/{len(symbols)}] "
                        f"{symbol}: {len(rows)} daily rows saved"
                    )

                except Exception as e:
                    state["failed"][symbol] = repr(e)
                    print(f"{symbol}: FAILED: {repr(e)}")

                state["completed"] = sorted(completed_set)
                state["updated_at_utc"] = (
                    datetime.now(timezone.utc).isoformat()
                )
                write_json_atomic(STATE, state)

    completed_final = [
        s for s in symbols
        if valid_part(s)
    ]

    missing_final = [
        s for s in symbols
        if not valid_part(s)
    ]

    print()
    print("Rebuilding combined CSV...")

    total_rows, included_symbols = rebuild_output(symbols)

    state["completed"] = completed_final
    state["missing"] = missing_final
    state["combined_rows"] = total_rows
    state["combined_symbols"] = included_symbols
    state["finished_at_utc"] = (
        datetime.now(timezone.utc).isoformat()
    )

    write_json_atomic(STATE, state)

    print()
    print("=" * 74)
    print("FINISHED")
    print("=" * 74)
    print("Completed:", len(completed_final), "/", len(symbols))
    print("Missing/failed:", len(missing_final))
    print("Combined symbols:", included_symbols)
    print("Combined daily rows:", total_rows)
    print("Output:", OUTPUT)
    print("State:", STATE)
    print("Parts:", WORKDIR)

    if missing_final:
        print()
        print("Some symbols failed:")
        print(", ".join(missing_final))
        print()
        print(
            "Run THE SAME SAVED SCRIPT again. "
            "Completed symbol shards will be skipped."
        )
    else:
        print()
        print("All manifest symbols collected successfully.")

    print()
    print(
        "Upload BOTH files to ChatGPT:\n"
        "1) r002_binance_full_universe_daily.csv\n"
        "2) r002_binance_full_universe_state.json"
    )

    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
