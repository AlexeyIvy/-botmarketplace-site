"""R002 metadata-only listing-episode audit for Android/Pydroid.

No strategy P&L is calculated.

A new listing episode is flagged when adjacent observed daily rows for the same
symbol are separated by more than 7 calendar days. This threshold is frozen in
`docs/research/r002-listing-episode-audit-protocol-v0.1.md` before any corrected
strategy rerun.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DOWNLOAD = Path("/storage/emulated/0/Download")
INPUT = DOWNLOAD / "r002_binance_full_universe_daily.csv"
EXPECTED_SYMBOLS = 864
EXPECTED_ROWS = 637_705
WARMUP = 200
MAX_CONTINUOUS_GAP_DAYS = 7


def iso_or_blank(x):
    if pd.isna(x):
        return ""
    return pd.Timestamp(x).date().isoformat()


def main():
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = DOWNLOAD / f"R002_LISTING_EPISODE_AUDIT_{run_id}"
    outdir.mkdir(parents=True, exist_ok=False)

    print("=" * 76)
    print("R002 LISTING-EPISODE METADATA AUDIT v0.1")
    print("NO STRATEGY P&L / NO RETUNING")
    print("Episode split if adjacent observed bars are > 7 calendar days apart")
    print("Output:", outdir)
    print("=" * 76)
    print()

    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    print("Reading archive dataset...")
    usecols = ["symbol", "date_utc", "volume"]
    raw = pd.read_csv(INPUT, usecols=usecols)

    if len(raw) != EXPECTED_ROWS:
        raise ValueError(f"Rows={len(raw)}, expected {EXPECTED_ROWS}")
    if raw["symbol"].nunique() != EXPECTED_SYMBOLS:
        raise ValueError(
            f"Symbols={raw['symbol'].nunique()}, expected {EXPECTED_SYMBOLS}"
        )

    raw["date"] = pd.to_datetime(raw["date_utc"], errors="coerce")
    raw["volume"] = pd.to_numeric(raw["volume"], errors="coerce")
    if raw[["symbol", "date", "volume"]].isna().any().any():
        raise ValueError("Missing/invalid core audit values")

    episode_rows = []
    gap_rows = []
    symbol_rows = []

    for symbol, g in raw.groupby("symbol", sort=True):
        g = g.sort_values("date").drop_duplicates("date", keep="last").copy()

        positive = g[g["volume"] > 0]
        if positive.empty:
            continue

        last_live = positive["date"].max()
        g = g[g["date"] <= last_live].copy()

        g["delta_days"] = g["date"].diff().dt.days
        g["new_episode"] = g["delta_days"].fillna(0) > MAX_CONTINUOUS_GAP_DAYS
        g["episode_no"] = g["new_episode"].cumsum().astype(int) + 1

        long_gaps = g[g["new_episode"]]
        for _, row in long_gaps.iterrows():
            next_date = row["date"]
            prev_date = next_date - pd.Timedelta(days=int(row["delta_days"]))
            gap_rows.append(
                {
                    "symbol": symbol,
                    "previous_observed_date": prev_date.date().isoformat(),
                    "next_observed_date": next_date.date().isoformat(),
                    "delta_days": int(row["delta_days"]),
                    "missing_calendar_days": int(row["delta_days"] - 1),
                    "new_episode_no": int(row["episode_no"]),
                }
            )

        episode_meta = []
        for episode_no, e in g.groupby("episode_no", sort=True):
            e = e.sort_values("date")
            bars = len(e)
            positive_bars = int((e["volume"] > 0).sum())
            eligible = bars >= WARMUP
            eligibility_date = e.iloc[WARMUP - 1]["date"] if eligible else pd.NaT
            prev_gap = None
            if int(episode_no) > 1:
                first = e.iloc[0]
                prev_gap = int(first["delta_days"])

            row = {
                "symbol": symbol,
                "episode_no": int(episode_no),
                "episode_start": e["date"].min().date().isoformat(),
                "episode_end": e["date"].max().date().isoformat(),
                "observed_bars": int(bars),
                "positive_volume_bars": positive_bars,
                "gap_from_prior_episode_days": prev_gap,
                "reaches_200_observed_bars": bool(eligible),
                "episode_eligibility_date": iso_or_blank(eligibility_date),
            }
            episode_rows.append(row)
            episode_meta.append(row)

        naive_eligibility = (
            g.iloc[WARMUP - 1]["date"] if len(g) >= WARMUP else pd.NaT
        )
        eligible_episodes = [
            x for x in episode_meta if x["reaches_200_observed_bars"]
        ]
        first_episode_eligibility = (
            pd.Timestamp(eligible_episodes[0]["episode_eligibility_date"])
            if eligible_episodes else pd.NaT
        )

        symbol_rows.append(
            {
                "symbol": symbol,
                "episodes": int(g["episode_no"].max()),
                "trimmed_observed_bars": int(len(g)),
                "archive_first_date": g["date"].min().date().isoformat(),
                "archive_last_live_date": g["date"].max().date().isoformat(),
                "naive_symbol_eligibility_date": iso_or_blank(naive_eligibility),
                "episode_aware_first_eligibility_date": iso_or_blank(
                    first_episode_eligibility
                ),
                "eligibility_date_changed": bool(
                    pd.notna(naive_eligibility)
                    and (
                        pd.isna(first_episode_eligibility)
                        or naive_eligibility != first_episode_eligibility
                    )
                ),
                "eligible_episode_count": int(len(eligible_episodes)),
                "max_adjacent_gap_days": int(g["delta_days"].dropna().max())
                if len(g) > 1 else 0,
            }
        )

    episodes = pd.DataFrame(episode_rows)
    gaps = pd.DataFrame(gap_rows)
    symbols = pd.DataFrame(symbol_rows)

    episodes_path = outdir / "r002_listing_episode_audit_episodes.csv"
    gaps_path = outdir / "r002_listing_episode_audit_gaps.csv"
    symbols_path = outdir / "r002_listing_episode_audit_symbols.csv"
    summary_path = outdir / "r002_listing_episode_audit_summary.md"
    state_path = outdir / "r002_listing_episode_audit_state.json"

    episodes.to_csv(episodes_path, index=False)
    gaps.to_csv(gaps_path, index=False)
    symbols.to_csv(symbols_path, index=False)

    multi = symbols[symbols["episodes"] > 1]
    changed = symbols[symbols["eligibility_date_changed"]]

    largest = gaps.sort_values("delta_days", ascending=False).head(25) if not gaps.empty else gaps

    lines = [
        "# R002 Listing-Episode Metadata Audit — Output v0.1",
        "",
        "**No strategy P&L was calculated.**",
        "",
        f"- Archive symbols: **{len(symbols)}**",
        f"- Total listing episodes: **{len(episodes)}**",
        f"- Symbols with >1 episode: **{len(multi)}**",
        f"- Long-gap events (> {MAX_CONTINUOUS_GAP_DAYS} days between observed bars): **{len(gaps)}**",
        f"- Symbols whose naive 200-bar eligibility changes under episode segmentation: **{len(changed)}**",
        f"- Total episodes independently reaching 200 bars: **{int(episodes['reaches_200_observed_bars'].sum())}**",
        "",
        "## Largest gap events",
        "",
        "| Symbol | Previous observed | Next observed | Delta days | Missing days |",
        "|---|---:|---:|---:|---:|",
    ]

    for row in largest.itertuples(index=False):
        lines.append(
            f"| {row.symbol} | {row.previous_observed_date} | {row.next_observed_date} | "
            f"{row.delta_days} | {row.missing_calendar_days} |"
        )

    lines += [
        "",
        "## Interpretation rule",
        "",
        "This audit does not decide strategy performance. If multi-episode symbols are material, the strategy engine must reset history, warmup and signal state at every episode before the frozen wide-universe test is rerun.",
        "",
    ]
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    state = {
        "status": "PASS",
        "version": "0.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_file": str(INPUT),
        "archive_rows": int(len(raw)),
        "archive_symbols": int(raw["symbol"].nunique()),
        "max_continuous_gap_days": MAX_CONTINUOUS_GAP_DAYS,
        "warmup": WARMUP,
        "total_episodes": int(len(episodes)),
        "multi_episode_symbols": int(len(multi)),
        "long_gap_events": int(len(gaps)),
        "symbols_with_changed_eligibility": int(len(changed)),
        "eligible_episodes": int(episodes["reaches_200_observed_bars"].sum()),
        "outputs": [
            episodes_path.name,
            gaps_path.name,
            symbols_path.name,
            summary_path.name,
            state_path.name,
        ],
    }
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print()
    print("AUDIT FINISHED")
    print("Total episodes:", len(episodes))
    print("Multi-episode symbols:", len(multi))
    print("Long-gap events:", len(gaps))
    print("Eligibility changed:", len(changed))
    print("Results:", outdir)
    print()
    print("Upload every file in that folder to ChatGPT.")
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
