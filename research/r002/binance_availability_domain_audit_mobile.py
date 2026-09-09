"""R002 metadata-only availability/domain audit for Android/Pydroid.

No strategy signals or P&L are calculated.

Purpose:
- compare Binance public archive first bars with official USD-M onboardDate;
- quantify pre-onboard/backfilled archive bars;
- compare archive-based vs onboard-adjusted 200-bar eligibility;
- record official underlyingType / underlyingSubType domain metadata.

Outputs are written into a fresh timestamped folder in Android Download.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

DOWNLOAD = Path("/storage/emulated/0/Download")
CSV = DOWNLOAD / "r002_binance_full_universe_daily.csv"
EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
EXPECTED_ROWS = 637_705
EXPECTED_SYMBOLS = 864
WARMUP = 200


def atomic_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def fetch_exchange_info() -> dict:
    req = Request(
        EXCHANGE_INFO_URL,
        headers={
            "User-Agent": "r002-availability-domain-audit/0.1",
            "Accept": "application/json",
        },
    )
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def prepare_archive() -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.Timestamp]:
    print("Reading archive dataset...")
    raw = pd.read_csv(CSV, usecols=["symbol", "date_utc", "volume"])

    if len(raw) != EXPECTED_ROWS:
        raise ValueError(f"Rows={len(raw)}, expected {EXPECTED_ROWS}")
    if raw["symbol"].nunique() != EXPECTED_SYMBOLS:
        raise ValueError(
            f"Symbols={raw['symbol'].nunique()}, expected {EXPECTED_SYMBOLS}"
        )

    raw["date"] = pd.to_datetime(raw["date_utc"], errors="coerce", utc=True).dt.tz_convert(None)
    raw["volume"] = pd.to_numeric(raw["volume"], errors="coerce")
    if raw[["symbol", "date", "volume"]].isna().any().any():
        raise ValueError("Missing/invalid symbol/date/volume rows")

    global_end = raw["date"].max()
    groups: dict[str, pd.DataFrame] = {}
    meta_rows = []

    for symbol, g in raw.groupby("symbol", sort=True):
        g = g.sort_values("date").drop_duplicates("date", keep="last")
        pos = g[g["volume"] > 0]
        if pos.empty:
            continue
        last_live = pos["date"].max()
        g = g[g["date"] <= last_live][["date", "volume"]].copy()
        g = g.reset_index(drop=True)
        groups[symbol] = g

        archive_elig = g.iloc[WARMUP - 1]["date"] if len(g) >= WARMUP else pd.NaT
        meta_rows.append(
            {
                "symbol": symbol,
                "archive_first_date": g.iloc[0]["date"],
                "archive_last_live_date": g.iloc[-1]["date"],
                "archive_observed_bars": len(g),
                "archive_eligibility_date": archive_elig,
            }
        )

    meta = pd.DataFrame(meta_rows)
    return meta, groups, global_end


def exchange_meta(info: dict) -> pd.DataFrame:
    rows = []
    for item in info.get("symbols", []):
        symbol = str(item.get("symbol", ""))
        onboard_ms = item.get("onboardDate")
        onboard_ts = pd.NaT
        if onboard_ms is not None:
            try:
                onboard_ts = pd.to_datetime(int(onboard_ms), unit="ms", utc=True).tz_convert(None)
            except Exception:
                onboard_ts = pd.NaT

        subtype = item.get("underlyingSubType")
        if isinstance(subtype, list):
            subtype_text = "|".join(str(x) for x in subtype)
        elif subtype is None:
            subtype_text = ""
        else:
            subtype_text = str(subtype)

        rows.append(
            {
                "symbol": symbol,
                "official_onboard_timestamp": onboard_ts,
                "official_onboard_date": onboard_ts.normalize() if pd.notna(onboard_ts) else pd.NaT,
                "status": item.get("status"),
                "contractType": item.get("contractType"),
                "baseAsset": item.get("baseAsset"),
                "quoteAsset": item.get("quoteAsset"),
                "underlyingType": item.get("underlyingType"),
                "underlyingSubType": subtype_text,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    if not CSV.exists():
        raise FileNotFoundError(CSV)

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = DOWNLOAD / f"R002_AVAILABILITY_DOMAIN_AUDIT_{run_id}"
    outdir.mkdir(parents=True, exist_ok=False)

    print("=" * 76)
    print("R002 AVAILABILITY & DOMAIN METADATA AUDIT v0.1")
    print("NO STRATEGY P&L / NO RETUNING")
    print("Output:", outdir)
    print("=" * 76)

    archive_meta, groups, global_end = prepare_archive()
    print("Archive validation PASS:", len(archive_meta), "symbols")

    print("Downloading official Binance USD-M exchangeInfo...")
    try:
        info = fetch_exchange_info()
    except Exception as exc:
        state = {
            "status": "METADATA_DOWNLOAD_FAILED",
            "error": repr(exc),
            "url": EXCHANGE_INFO_URL,
            "archive_symbols": int(len(archive_meta)),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_text(
            outdir / "r002_availability_domain_audit_state.json",
            json.dumps(state, ensure_ascii=False, indent=2, default=str),
        )
        print("Metadata download FAILED:", repr(exc))
        print("Upload the audit state JSON to ChatGPT.")
        input("Press Enter to finish...")
        return

    atomic_text(
        outdir / "r002_exchange_info_snapshot.json",
        json.dumps(info, ensure_ascii=False, indent=2),
    )

    ex = exchange_meta(info)
    print("exchangeInfo symbols:", len(ex))

    out = archive_meta.merge(ex, on="symbol", how="left", indicator=True)
    out["metadata_match"] = out["_merge"].eq("both")
    out = out.drop(columns=["_merge"])

    pre_rows = []
    adjusted_dates = []
    shifts = []
    lead_days = []

    for row in out.itertuples(index=False):
        symbol = row.symbol
        onboard = row.official_onboard_date
        g = groups[symbol]

        if pd.isna(onboard):
            pre_rows.append(pd.NA)
            adjusted_dates.append(pd.NaT)
            shifts.append(pd.NA)
            lead_days.append(pd.NA)
            continue

        before = int((g["date"] < onboard).sum())
        post = g[g["date"] >= onboard].reset_index(drop=True)
        adj = post.iloc[WARMUP - 1]["date"] if len(post) >= WARMUP else pd.NaT

        pre_rows.append(before)
        adjusted_dates.append(adj)
        lead_days.append(int((onboard - row.archive_first_date).days))

        if pd.notna(row.archive_eligibility_date) and pd.notna(adj):
            shifts.append(int((adj - row.archive_eligibility_date).days))
        else:
            shifts.append(pd.NA)

    out["archive_rows_before_official_onboard"] = pre_rows
    out["archive_first_lead_days"] = lead_days
    out["onboard_adjusted_eligibility_date"] = adjusted_dates
    out["eligibility_shift_days"] = shifts

    for c in [
        "archive_first_date",
        "archive_last_live_date",
        "archive_eligibility_date",
        "official_onboard_timestamp",
        "official_onboard_date",
        "onboard_adjusted_eligibility_date",
    ]:
        out[c] = pd.to_datetime(out[c], errors="coerce")

    out = out.sort_values("symbol").reset_index(drop=True)
    out.to_csv(outdir / "r002_availability_domain_audit.csv", index=False)

    matched = out[out["metadata_match"]].copy()
    pre = pd.to_numeric(matched["archive_rows_before_official_onboard"], errors="coerce")
    shift = pd.to_numeric(matched["eligibility_shift_days"], errors="coerce")

    type_counts = (
        matched["underlyingType"].fillna("<MISSING>").value_counts().sort_index()
    )
    subtype_counts = (
        matched["underlyingSubType"].replace("", "<EMPTY>").fillna("<MISSING>")
        .value_counts().head(30)
    )

    archive_eligible = matched[matched["archive_eligibility_date"].notna()]
    type_eligible_counts = (
        archive_eligible["underlyingType"].fillna("<MISSING>").value_counts().sort_index()
    )

    lines = [
        "# R002 Availability & Domain Metadata Audit — Output v0.1",
        "",
        "**No strategy P&L was calculated.**",
        "",
        f"- Archive symbols: **{len(out)}**",
        f"- Archive end: **{global_end.date().isoformat()}**",
        f"- exchangeInfo symbols: **{len(ex)}**",
        f"- Matched archive symbols: **{int(out['metadata_match'].sum())}**",
        f"- Unmatched archive symbols: **{int((~out['metadata_match']).sum())}**",
        f"- Matched symbols with >=1 archive row before official onboard date: **{int((pre > 0).sum())}**",
        f"- Median pre-onboard rows among affected: **{float(pre[pre > 0].median()) if (pre > 0).any() else 0:.1f}**",
        f"- Maximum pre-onboard rows: **{int(pre.max()) if pre.notna().any() else 0}**",
        f"- Symbols with onboard-adjusted eligibility later than archive eligibility: **{int((shift > 0).sum())}**",
        f"- Median positive eligibility shift: **{float(shift[shift > 0].median()) if (shift > 0).any() else 0:.1f} days**",
        f"- Maximum eligibility shift: **{int(shift.max()) if shift.notna().any() else 0} days**",
        "",
        "## underlyingType counts — matched symbols",
        "",
    ]
    for k, v in type_counts.items():
        lines.append(f"- `{k}`: **{int(v)}**")

    lines += ["", "## underlyingType counts — archive-eligible matched symbols", ""]
    for k, v in type_eligible_counts.items():
        lines.append(f"- `{k}`: **{int(v)}**")

    lines += ["", "## Top underlyingSubType values", ""]
    for k, v in subtype_counts.items():
        lines.append(f"- `{k}`: **{int(v)}**")

    xau = out[out["symbol"] == "XAUUSDT"]
    if not xau.empty:
        r = xau.iloc[0]
        lines += [
            "",
            "## XAUUSDT cross-check",
            "",
            f"- archive first date: `{r['archive_first_date'].date().isoformat()}`",
            f"- official onboard date: `{r['official_onboard_date'].date().isoformat() if pd.notna(r['official_onboard_date']) else 'MISSING'}`",
            f"- pre-onboard archive rows: **{r['archive_rows_before_official_onboard']}**",
            f"- archive eligibility: `{r['archive_eligibility_date'].date().isoformat() if pd.notna(r['archive_eligibility_date']) else 'NOT_ELIGIBLE'}`",
            f"- onboard-adjusted eligibility: `{r['onboard_adjusted_eligibility_date'].date().isoformat() if pd.notna(r['onboard_adjusted_eligibility_date']) else 'NOT_ELIGIBLE'}`",
            f"- eligibility shift: **{r['eligibility_shift_days']} days**",
        ]

    affected = matched[(pre > 0)].copy()
    if not affected.empty:
        affected["_pre"] = pd.to_numeric(
            affected["archive_rows_before_official_onboard"], errors="coerce"
        )
        top = affected.sort_values("_pre", ascending=False).head(25)
        lines += [
            "",
            "## Largest pre-onboard archive histories",
            "",
            "| Symbol | Underlying type | Archive first | Official onboard | Pre-onboard rows | Eligibility shift days |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for r in top.itertuples(index=False):
            lines.append(
                f"| {r.symbol} | {r.underlyingType} | {r.archive_first_date.date()} | "
                f"{r.official_onboard_date.date()} | {r.archive_rows_before_official_onboard} | "
                f"{r.eligibility_shift_days} |"
            )

    atomic_text(
        outdir / "r002_availability_domain_audit_summary.md",
        "\n".join(lines) + "\n",
    )

    state = {
        "status": "PASS",
        "version": "0.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_file": str(CSV),
        "archive_rows_expected": EXPECTED_ROWS,
        "archive_symbols": int(len(out)),
        "exchange_info_url": EXCHANGE_INFO_URL,
        "exchange_info_symbols": int(len(ex)),
        "matched_symbols": int(out["metadata_match"].sum()),
        "unmatched_symbols": int((~out["metadata_match"]).sum()),
        "symbols_with_pre_onboard_rows": int((pre > 0).sum()),
        "symbols_with_positive_eligibility_shift": int((shift > 0).sum()),
        "max_eligibility_shift_days": int(shift.max()) if shift.notna().any() else None,
    }
    atomic_text(
        outdir / "r002_availability_domain_audit_state.json",
        json.dumps(state, ensure_ascii=False, indent=2),
    )

    print()
    print("AUDIT FINISHED")
    print("Matched:", state["matched_symbols"])
    print("Pre-onboard archive histories:", state["symbols_with_pre_onboard_rows"])
    print("Positive eligibility shifts:", state["symbols_with_positive_eligibility_shift"])
    print("Results:", outdir)
    print()
    print("Upload every file in that folder to ChatGPT.")
    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
