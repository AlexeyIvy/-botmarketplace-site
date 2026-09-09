"""Pydroid launcher for the R002 episode-corrected wide-universe rerun v0.1.

Only data-identity is corrected:
- a gap > 7 calendar days starts a new listing episode;
- every episode receives a unique temporary symbol identity;
- the exact frozen wide-universe engine commit is then executed unchanged.

No signal parameters, costs, disappearance assumptions or universe filters are
changed.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
INPUT = DOWNLOAD / "r002_binance_full_universe_daily.csv"
INPUT_STATE = DOWNLOAD / "r002_binance_full_universe_state.json"

ENGINE_COMMIT = "9275d50e321dd24f5eabe83cc20dd340cfda6350"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r002/wide_universe_point_in_time_finalists.py"
)

MAX_CONTINUOUS_GAP_DAYS = 7
EXPECTED_ROWS = 637_705
EXPECTED_BASE_SYMBOLS = 864
EXPECTED_EPISODES = 867
EXPECTED_GAPS = {
    ("BNXUSDT", "2023-01-31", "2023-02-22", 22),
    ("ICPUSDT", "2022-08-31", "2022-09-27", 27),
    ("TLMUSDT", "2023-02-28", "2023-03-30", 30),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_day(text: str) -> date:
    return date.fromisoformat(text[:10])


def transform_to_episode_identities(src: Path, dst: Path):
    gap_events = []
    episode_records = []
    base_symbols = set()
    pseudo_symbols = set()
    completed_symbols = set()

    current_symbol = None
    episode_no = 0
    prev_day = None
    row_count = 0
    current_record = None

    with src.open("r", encoding="utf-8", newline="") as fi:
        r = csv.DictReader(fi)
        if not r.fieldnames or "symbol" not in r.fieldnames or "date_utc" not in r.fieldnames:
            raise ValueError("Input CSV lacks symbol/date_utc columns")

        with dst.open("w", encoding="utf-8", newline="") as fo:
            w = csv.DictWriter(fo, fieldnames=r.fieldnames)
            w.writeheader()

            for row in r:
                symbol = row["symbol"]
                d = parse_day(row["date_utc"])

                if symbol != current_symbol:
                    if current_symbol is not None:
                        completed_symbols.add(current_symbol)
                        episode_records.append(current_record)
                    if symbol in completed_symbols:
                        raise ValueError(f"Input symbol blocks are not contiguous: {symbol}")
                    current_symbol = symbol
                    base_symbols.add(symbol)
                    episode_no = 1
                    prev_day = None
                    current_record = {
                        "base_symbol": symbol,
                        "episode_no": episode_no,
                        "episode_symbol": f"{symbol}@@E{episode_no:02d}",
                        "episode_start": d.isoformat(),
                        "episode_end": d.isoformat(),
                        "observed_rows": 0,
                    }
                else:
                    if prev_day is not None and d <= prev_day:
                        raise ValueError(f"Non-increasing date for {symbol}: {d} after {prev_day}")

                    if prev_day is not None:
                        delta = (d - prev_day).days
                        if delta > MAX_CONTINUOUS_GAP_DAYS:
                            episode_records.append(current_record)
                            old_episode = episode_no
                            episode_no += 1
                            gap_events.append({
                                "base_symbol": symbol,
                                "prior_episode_no": old_episode,
                                "new_episode_no": episode_no,
                                "previous_observed_date": prev_day.isoformat(),
                                "next_observed_date": d.isoformat(),
                                "delta_days": delta,
                                "missing_calendar_days": delta - 1,
                            })
                            current_record = {
                                "base_symbol": symbol,
                                "episode_no": episode_no,
                                "episode_symbol": f"{symbol}@@E{episode_no:02d}",
                                "episode_start": d.isoformat(),
                                "episode_end": d.isoformat(),
                                "observed_rows": 0,
                            }

                pseudo = f"{symbol}@@E{episode_no:02d}"
                pseudo_symbols.add(pseudo)
                current_record["episode_end"] = d.isoformat()
                current_record["observed_rows"] += 1

                out = dict(row)
                out["symbol"] = pseudo
                w.writerow(out)
                row_count += 1
                prev_day = d

    if current_symbol is not None:
        episode_records.append(current_record)

    observed_gap_set = {
        (
            x["base_symbol"],
            x["previous_observed_date"],
            x["next_observed_date"],
            int(x["delta_days"]),
        )
        for x in gap_events
    }

    if row_count != EXPECTED_ROWS:
        raise ValueError(f"Transformed rows={row_count}, expected {EXPECTED_ROWS}")
    if len(base_symbols) != EXPECTED_BASE_SYMBOLS:
        raise ValueError(f"Base symbols={len(base_symbols)}, expected {EXPECTED_BASE_SYMBOLS}")
    if len(pseudo_symbols) != EXPECTED_EPISODES:
        raise ValueError(f"Episodes={len(pseudo_symbols)}, expected {EXPECTED_EPISODES}")
    if observed_gap_set != EXPECTED_GAPS:
        raise ValueError(
            "Observed long-gap set differs from frozen audit.\n"
            f"Observed: {sorted(observed_gap_set)}\n"
            f"Expected: {sorted(EXPECTED_GAPS)}"
        )

    return episode_records, gap_events


def write_csv(path: Path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing dataset: {INPUT}")
    if not INPUT_STATE.exists():
        raise FileNotFoundError(f"Missing state file: {INPUT_STATE}")

    state = json.loads(INPUT_STATE.read_text(encoding="utf-8"))
    if int(state.get("combined_rows", -1)) != EXPECTED_ROWS:
        raise ValueError("Input state row count mismatch")
    if int(state.get("combined_symbols", -1)) != EXPECTED_BASE_SYMBOLS:
        raise ValueError("Input state symbol count mismatch")

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = DOWNLOAD / f"R002_WIDE_UNIVERSE_EPISODE_CORRECTED_RUN_{run_id}"
    outdir.mkdir(parents=True, exist_ok=False)

    temp_csv = outdir / "_episode_corrected_input_tmp.csv"
    engine = outdir / "r002_wide_universe_point_in_time_finalists_frozen_v0_1.py"
    episode_map = outdir / "r002_episode_correction_episodes.csv"
    gap_map = outdir / "r002_episode_correction_gaps.csv"
    launcher_state = outdir / "r002_episode_correction_launcher_state.json"

    print("=" * 76)
    print("R002 WIDE-UNIVERSE EPISODE-CORRECTED RERUN v0.1")
    print("Frozen strategy engine:", ENGINE_COMMIT)
    print("Only correction: gap > 7 days resets listing episode/state")
    print("Output:", outdir)
    print("=" * 76)
    print()

    print("[1/4] Hashing frozen input...")
    input_sha = sha256_file(INPUT)
    print("      SHA256:", input_sha)

    print("[2/4] Building temporary episode-aware dataset...")
    episodes, gaps = transform_to_episode_identities(INPUT, temp_csv)
    write_csv(
        episode_map,
        episodes,
        ["base_symbol", "episode_no", "episode_symbol", "episode_start", "episode_end", "observed_rows"],
    )
    write_csv(
        gap_map,
        gaps,
        [
            "base_symbol", "prior_episode_no", "new_episode_no",
            "previous_observed_date", "next_observed_date",
            "delta_days", "missing_calendar_days",
        ],
    )
    print("      PASS: 864 base symbols -> 867 episode identities")
    print("      Long gaps:", len(gaps))

    print("[3/4] Downloading exact frozen strategy engine...")
    req = Request(ENGINE_URL, headers={"User-Agent": "r002-episode-corrected/0.1"})
    with urlopen(req, timeout=60) as resp:
        engine.write_bytes(resp.read())

    launcher_info = {
        "status": "PREPARED",
        "version": "0.1",
        "created_at_local": datetime.now().isoformat(),
        "input": str(INPUT),
        "input_sha256": input_sha,
        "input_rows": EXPECTED_ROWS,
        "input_base_symbols": EXPECTED_BASE_SYMBOLS,
        "episode_rule_max_continuous_gap_days": MAX_CONTINUOUS_GAP_DAYS,
        "transformed_episode_identities": EXPECTED_EPISODES,
        "long_gap_events": gaps,
        "frozen_engine_commit": ENGINE_COMMIT,
    }
    launcher_state.write_text(json.dumps(launcher_info, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[4/4] Running unchanged frozen wide-universe engine...")
    source = engine.read_text(encoding="utf-8")
    old_argv = sys.argv[:]
    try:
        sys.argv = [
            str(engine),
            str(temp_csv),
            "--outdir",
            str(outdir),
            "--skip-known-invariants",
        ]
        namespace = {"__name__": "__main__", "__file__": str(engine)}
        exec(compile(source, str(engine), "exec"), namespace)
    finally:
        sys.argv = old_argv

    launcher_info["status"] = "PASS"
    launcher_info["finished_at_local"] = datetime.now().isoformat()
    launcher_info["temporary_transformed_csv_deleted"] = True
    launcher_state.write_text(json.dumps(launcher_info, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        temp_csv.unlink()
    except OSError:
        launcher_info["temporary_transformed_csv_deleted"] = False
        launcher_state.write_text(json.dumps(launcher_info, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print("=" * 76)
    print("CORRECTED RERUN FINISHED")
    print("Upload every result file in:")
    print(outdir)
    print("The temporary transformed full CSV is deleted after a successful run.")
    print("=" * 76)
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
