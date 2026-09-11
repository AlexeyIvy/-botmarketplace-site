from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import shutil
import time
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

STAGE = "SC001-MICRO-CALENDAR-v0.1"
SEED = "SC001-MICRO-v0.1-20260911"

DOWNLOAD = Path("/storage/emulated/0/Download")
WORKSPACE = DOWNLOAD / "SC001_MICRO_CALENDAR_V0_1"

MIN_FREE_BYTES = 4_000_000_000
SESSION_DOWNLOAD_CAP_BYTES = 50_000_000
PER_RESPONSE_CAP_BYTES = 5_000_000

SPLITS = {
    "DEV": ("2023-04-01", "2024-06-30"),
    "VALIDATION": ("2024-07-01", "2025-06-30"),
    "FINAL": ("2025-07-01", "2026-08-31"),
}

QUALIFICATION_ONLY_DATES = {
    "2023-04-15",
    "2024-01-15",
    "2025-01-15",
    "2026-07-15",
}

BLS_YEARS = [2023, 2024, 2025, 2026]
BLS_URLS = {
    y: f"https://www.bls.gov/schedule/{y}/home.htm"
    for y in BLS_YEARS
}

FED_CALENDAR_URL = (
    "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
)

FOMC_DECISION_DATES = [
    "2023-05-03", "2023-06-14", "2023-07-26",
    "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01",
    "2024-06-12", "2024-07-31", "2024-09-18",
    "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07",
    "2025-06-18", "2025-07-30", "2025-09-17",
    "2025-10-29", "2025-12-10",
    "2026-01-28", "2026-03-18", "2026-04-29",
    "2026-06-17", "2026-07-29",
]

REQUIRED_EVENT_CLASSES = ("CPI", "NFP", "FOMC")

network_bytes_read = 0


def ensure_storage() -> int:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(DOWNLOAD).free
    if free < MIN_FREE_BYTES:
        raise RuntimeError(
            f"Free storage {free:,} < required reserve {MIN_FREE_BYTES:,}"
        )
    return free


def fetch_bytes(url: str, max_bytes: int = PER_RESPONSE_CAP_BYTES) -> bytes:
    global network_bytes_read
    if network_bytes_read >= SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError("Session download cap already reached")

    req = Request(
        url,
        headers={
            "User-Agent": "BotMarketplace-SC001-MICRO-CALENDAR/0.1"
        },
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read(max_bytes + 1)

    if len(raw) > max_bytes:
        raise RuntimeError(f"Response too large: {url}")

    network_bytes_read += len(raw)
    if network_bytes_read > SESSION_DOWNLOAD_CAP_BYTES:
        raise RuntimeError("Session download cap exceeded")

    return raw


class TableRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tr = False
        self.current: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "tr":
            self.in_tr = True
            self.current = []

    def handle_data(self, data: str) -> None:
        if self.in_tr:
            text = " ".join(data.split())
            if text:
                self.current.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "tr" and self.in_tr:
            if self.current:
                self.rows.append(self.current)
            self.current = []
            self.in_tr = False


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        t = " ".join(data.split())
        if t:
            self.parts.append(t)


MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

BLS_ROW_RE = re.compile(
    r"(?P<weekday>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+"
    r"(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(?P<day>\d{1,2}),\s+(?P<year>\d{4})\s+"
    r"(?P<hour>\d{1,2}):(?P<minute>\d{2})\s+(?P<ampm>AM|PM)\s+"
    r"(?P<release>.+)$",
    re.IGNORECASE,
)

FED_TIME_RE = re.compile(
    r"For release at\s+"
    r"(?P<hour>\d{1,2}):(?P<minute>\d{2})\s*"
    r"(?P<ampm>a\.m\.|p\.m\.|AM|PM)\s*"
    r"(?P<zone>EDT|EST)",
    re.IGNORECASE,
)


def first_sunday(year: int, month: int) -> date:
    d = date(year, month, 1)
    return d + timedelta(days=(6 - d.weekday()) % 7)


def second_sunday(year: int, month: int) -> date:
    return first_sunday(year, month) + timedelta(days=7)


def is_us_eastern_dst(d: date) -> bool:
    start = second_sunday(d.year, 3)
    end = first_sunday(d.year, 11)
    return start <= d < end


def local_clock_to_utc(
    d: date,
    hour: int,
    minute: int,
    ampm: str,
    explicit_zone: str | None = None,
) -> datetime:
    a = ampm.lower().replace(".", "")
    if a == "pm" and hour != 12:
        hour += 12
    elif a == "am" and hour == 12:
        hour = 0

    if explicit_zone is not None:
        z = explicit_zone.upper()
        offset_hours = -4 if z == "EDT" else -5
    else:
        offset_hours = -4 if is_us_eastern_dst(d) else -5

    local_naive = datetime(d.year, d.month, d.day, hour, minute)
    utc_dt = local_naive - timedelta(hours=offset_hours)
    return utc_dt.replace(tzinfo=timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def split_for_day(day: date) -> str | None:
    ds = day.isoformat()
    for name, (start, end) in SPLITS.items():
        if start <= ds <= end:
            return name
    return None


def quarter_label(day: date) -> str:
    q = (day.month - 1) // 3 + 1
    return f"{day.year}-Q{q}"


def quarter_bounds(label: str) -> tuple[date, date]:
    year_s, q_s = label.split("-Q")
    y = int(year_s)
    q = int(q_s)
    start_month = (q - 1) * 3 + 1
    end_month = start_month + 2
    start = date(y, start_month, 1)
    end = date(y, end_month, monthrange(y, end_month)[1])
    return start, end


def all_quarters_for_split(start_s: str, end_s: str) -> list[str]:
    start = date.fromisoformat(start_s)
    end = date.fromisoformat(end_s)
    out: list[str] = []
    cur = date(start.year, ((start.month - 1) // 3) * 3 + 1, 1)
    while cur <= end:
        q = quarter_label(cur)
        out.append(q)
        _, q_end = quarter_bounds(q)
        cur = q_end + timedelta(days=1)
    return out


def hash_pick(items: list, key: str):
    if not items:
        raise RuntimeError(f"No eligible items for {key}")
    idx = int.from_bytes(
        hashlib.sha256(key.encode("utf-8")).digest(), "big"
    ) % len(items)
    return items[idx]


def parse_bls() -> tuple[list[dict], list[dict]]:
    events: list[dict] = []
    sources: list[dict] = []

    for year in BLS_YEARS:
        url = BLS_URLS[year]
        raw = fetch_bytes(url)
        parser = TableRowParser()
        parser.feed(raw.decode("utf-8", errors="replace"))

        matched = 0
        for cells in parser.rows:
            row = " ".join(cells)
            row = html.unescape(" ".join(row.split()))
            m = BLS_ROW_RE.search(row)
            if not m:
                continue

            rel = m.group("release")
            if rel.startswith("Consumer Price Index for"):
                event_class = "CPI"
            elif rel.startswith("Employment Situation for"):
                event_class = "NFP"
            else:
                continue

            d = date(
                int(m.group("year")),
                MONTHS[m.group("month").title()],
                int(m.group("day")),
            )
            hour = int(m.group("hour"))
            minute = int(m.group("minute"))
            ampm = m.group("ampm").upper()
            anchor = local_clock_to_utc(d, hour, minute, ampm)

            events.append(
                {
                    "event_class": event_class,
                    "date": d.isoformat(),
                    "anchor_utc": iso_z(anchor),
                    "official_local_time": f"{hour:02d}:{minute:02d} {ampm} ET",
                    "source_url": url,
                    "source_row": row,
                }
            )
            matched += 1

        sources.append(
            {
                "kind": "BLS_ANNUAL_SCHEDULE",
                "year": year,
                "url": url,
                "bytes": len(raw),
                "sha256": sha256_hex(raw),
                "matched_primary_events": matched,
            }
        )

        time.sleep(0.4)

    return events, sources


def parse_fomc() -> tuple[list[dict], list[dict]]:
    events: list[dict] = []
    sources: list[dict] = []

    calendar_raw = fetch_bytes(FED_CALENDAR_URL)
    sources.append(
        {
            "kind": "FED_FOMC_CALENDAR",
            "url": FED_CALENDAR_URL,
            "bytes": len(calendar_raw),
            "sha256": sha256_hex(calendar_raw),
        }
    )

    for ds in FOMC_DECISION_DATES:
        d = date.fromisoformat(ds)
        url = (
            "https://www.federalreserve.gov/newsevents/pressreleases/"
            f"monetary{d.strftime('%Y%m%d')}a.htm"
        )
        raw = fetch_bytes(url, max_bytes=2_000_000)
        tp = TextParser()
        tp.feed(raw.decode("utf-8", errors="replace"))
        text = " ".join(tp.parts)

        m = FED_TIME_RE.search(text)
        if not m:
            raise RuntimeError(
                f"Could not parse official FOMC release time: {url}"
            )

        hour = int(m.group("hour"))
        minute = int(m.group("minute"))
        ampm = m.group("ampm")
        zone = m.group("zone").upper()
        anchor = local_clock_to_utc(
            d, hour, minute, ampm, explicit_zone=zone
        )

        events.append(
            {
                "event_class": "FOMC",
                "date": ds,
                "anchor_utc": iso_z(anchor),
                "official_local_time": (
                    f"{hour:02d}:{minute:02d} {ampm} {zone}"
                ),
                "source_url": url,
            }
        )
        sources.append(
            {
                "kind": "FED_FOMC_STATEMENT",
                "date": ds,
                "url": url,
                "bytes": len(raw),
                "sha256": sha256_hex(raw),
                "parsed_zone": zone,
                "anchor_utc": iso_z(anchor),
            }
        )

        time.sleep(0.4)

    return events, sources


def dedupe_sort_events(events: list[dict]) -> list[dict]:
    by_key = {}
    for e in events:
        key = (e["event_class"], e["anchor_utc"])
        by_key[key] = e
    out = list(by_key.values())
    out.sort(key=lambda x: (x["anchor_utc"], x["event_class"]))
    return out


def eligible_split_events(events: list[dict]) -> list[dict]:
    out = []
    for e in events:
        d = date.fromisoformat(e["date"])
        split = split_for_day(d)
        if split is None:
            continue
        x = dict(e)
        x["split"] = split
        x["quarter"] = quarter_label(d)
        out.append(x)
    return out


def build_selected_samples(events: list[dict]) -> list[dict]:
    primary_event_days = {e["date"] for e in events}
    selected: list[dict] = []

    for split_name, (start_s, end_s) in SPLITS.items():
        start = date.fromisoformat(start_s)
        end = date.fromisoformat(end_s)

        for q in all_quarters_for_split(start_s, end_s):
            q_start, q_end = quarter_bounds(q)
            lo = max(start, q_start)
            hi = min(end, q_end)

            all_days = []
            d = lo
            while d <= hi:
                all_days.append(d)
                d += timedelta(days=1)

            for stratum in ("WEEKDAY", "WEEKEND"):
                candidates = []
                for d in all_days:
                    ds = d.isoformat()
                    is_weekend = d.weekday() >= 5
                    if stratum == "WEEKDAY" and is_weekend:
                        continue
                    if stratum == "WEEKEND" and not is_weekend:
                        continue
                    if ds in QUALIFICATION_ONLY_DATES:
                        continue
                    if ds in primary_event_days:
                        continue
                    candidates.append(d)

                picked = hash_pick(
                    sorted(candidates),
                    f"{SEED}|{q}|{stratum}",
                )
                selected.append(
                    {
                        "sample_type": f"ORDINARY_{stratum}",
                        "event_class": None,
                        "date": picked.isoformat(),
                        "anchor_utc": None,
                        "split": split_name,
                        "quarter": q,
                        "selection_key": f"{SEED}|{q}|{stratum}",
                    }
                )

            for event_class in REQUIRED_EVENT_CLASSES:
                candidates = [
                    e for e in events
                    if e["split"] == split_name
                    and e["quarter"] == q
                    and e["event_class"] == event_class
                    and e["date"] not in QUALIFICATION_ONLY_DATES
                ]
                candidates.sort(key=lambda x: x["anchor_utc"])

                picked = hash_pick(
                    candidates,
                    f"{SEED}|{q}|{event_class}",
                )
                selected.append(
                    {
                        "sample_type": "EVENT",
                        "event_class": event_class,
                        "date": picked["date"],
                        "anchor_utc": picked["anchor_utc"],
                        "split": split_name,
                        "quarter": q,
                        "selection_key": f"{SEED}|{q}|{event_class}",
                        "source_url": picked["source_url"],
                    }
                )

    selected.sort(
        key=lambda x: (
            x["date"],
            x["sample_type"],
            x["event_class"] or "",
        )
    )
    return selected


def build_acquisition_days(selected: list[dict]) -> list[dict]:
    by_date: dict[str, dict] = {}
    for row in selected:
        d = row["date"]
        rec = by_date.setdefault(
            d,
            {
                "date": d,
                "split": row["split"],
                "quarter": row["quarter"],
                "sample_tags": [],
                "event_anchors_utc": [],
            },
        )
        tag = row["sample_type"]
        if row["event_class"]:
            tag += ":" + row["event_class"]
        rec["sample_tags"].append(tag)
        if row["anchor_utc"]:
            rec["event_anchors_utc"].append(row["anchor_utc"])

    out = []
    for d in sorted(by_date):
        rec = by_date[d]
        rec["sample_tags"] = sorted(set(rec["sample_tags"]))
        rec["event_anchors_utc"] = sorted(
            set(rec["event_anchors_utc"])
        )
        out.append(rec)
    return out


def validate_manifest(
    events: list[dict],
    selected: list[dict],
    acquisition_days: list[dict],
) -> dict:
    errors: list[str] = []

    for qd in QUALIFICATION_ONLY_DATES:
        if any(x["date"] == qd for x in selected):
            errors.append(f"Qualification-only date selected: {qd}")

    event_days = {e["date"] for e in events}
    for x in selected:
        if x["sample_type"].startswith("ORDINARY_"):
            if x["date"] in event_days:
                errors.append(
                    f"Ordinary sample falls on primary event day: {x['date']}"
                )

    for split_name, (start_s, end_s) in SPLITS.items():
        for q in all_quarters_for_split(start_s, end_s):
            subset = [
                x for x in selected
                if x["split"] == split_name and x["quarter"] == q
            ]
            for st in ("ORDINARY_WEEKDAY", "ORDINARY_WEEKEND"):
                if sum(x["sample_type"] == st for x in subset) != 1:
                    errors.append(f"{split_name} {q}: expected one {st}")

            for ev in REQUIRED_EVENT_CLASSES:
                if sum(
                    x["sample_type"] == "EVENT"
                    and x["event_class"] == ev
                    for x in subset
                ) != 1:
                    errors.append(
                        f"{split_name} {q}: expected one EVENT {ev}"
                    )

    if not acquisition_days:
        errors.append("No acquisition days")

    class_counts = {
        cls: sum(e["event_class"] == cls for e in events)
        for cls in REQUIRED_EVENT_CLASSES
    }

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "canonical_event_counts": class_counts,
        "selected_sample_rows": len(selected),
        "unique_acquisition_days": len(acquisition_days),
    }


def write_outputs(
    events: list[dict],
    sources: list[dict],
    selected: list[dict],
    acquisition_days: list[dict],
    validation: dict,
    free_start: int,
) -> None:
    manifest = {
        "stage": STAGE,
        "status": validation["status"],
        "seed": SEED,
        "hash_function": "SHA-256",
        "splits": SPLITS,
        "qualification_only_dates": sorted(QUALIFICATION_ONLY_DATES),
        "primary_event_classes": list(REQUIRED_EVENT_CLASSES),
        "event_window_primary_minutes": [-30, 60],
        "event_windows_diagnostic_minutes": [[-5, 30], [-60, 180]],
        "ordinary_sampling": (
            "one weekday and one weekend day per intersecting calendar "
            "quarter, deterministic SHA-256 selection after exclusions"
        ),
        "event_sampling": (
            "one CPI, one NFP, and one scheduled FOMC decision per "
            "intersecting calendar quarter, deterministic SHA-256 selection"
        ),
        "canonical_events": events,
        "selected_samples": selected,
        "acquisition_days": acquisition_days,
        "validation": validation,
    }

    manifest_path = (
        WORKSPACE / "sc001_micro_calendar_manifest_v0_1.json"
    )
    manifest_raw = json.dumps(
        manifest, indent=2, sort_keys=True, ensure_ascii=False
    ).encode("utf-8")
    manifest_path.write_bytes(manifest_raw)
    manifest_sha = sha256_hex(manifest_raw)

    (WORKSPACE / "sc001_micro_calendar_manifest_v0_1.sha256").write_text(
        manifest_sha + "  " + manifest_path.name + "\n",
        encoding="utf-8",
    )

    with (
        WORKSPACE / "sc001_micro_calendar_selected_v0_1.csv"
    ).open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "date", "split", "quarter", "sample_type",
            "event_class", "anchor_utc", "selection_key",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in selected:
            w.writerow({k: row.get(k) for k in fieldnames})

    sources_payload = {
        "stage": STAGE,
        "retrieved_at_utc": iso_z(datetime.now(timezone.utc)),
        "network_bytes_read": network_bytes_read,
        "sources": sources,
    }
    (
        WORKSPACE / "sc001_micro_calendar_sources_v0_1.json"
    ).write_text(
        json.dumps(
            sources_payload, indent=2, sort_keys=True, ensure_ascii=False
        ),
        encoding="utf-8",
    )

    free_after = shutil.disk_usage(DOWNLOAD).free
    workspace_bytes = sum(
        p.stat().st_size
        for p in WORKSPACE.rglob("*")
        if p.is_file()
    )
    safety = {
        "stage": STAGE,
        "network_bytes_read": network_bytes_read,
        "workspace_bytes_after_outputs": workspace_bytes,
        "free_bytes_start": free_start,
        "free_bytes_after_outputs": free_after,
        "caps": {
            "session_download_cap_bytes": SESSION_DOWNLOAD_CAP_BYTES,
            "per_response_cap_bytes": PER_RESPONSE_CAP_BYTES,
            "minimum_free_reserve_bytes": MIN_FREE_BYTES,
        },
    }
    (
        WORKSPACE / "sc001_micro_calendar_final_safety_v0_1.json"
    ).write_text(
        json.dumps(safety, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    split_counts = {}
    for split in SPLITS:
        split_counts[split] = {
            "selected_rows": sum(x["split"] == split for x in selected),
            "unique_days": len({
                x["date"] for x in selected if x["split"] == split
            }),
        }

    lines = [
        "# SC001-MICRO-CALENDAR-v0.1",
        "",
        f"- Status: `{validation['status']}`",
        f"- Manifest SHA256: `{manifest_sha}`",
        f"- Canonical events: {len(events)}",
        f"- Selected sample rows: {len(selected)}",
        f"- Unique acquisition days: {len(acquisition_days)}",
        f"- Network bytes read: {network_bytes_read:,}",
        "- Strategy/P&L calculated: **NO**",
        "",
        "## Split counts",
    ]
    for split, vals in split_counts.items():
        lines.append(
            f"- {split}: rows={vals['selected_rows']}; "
            f"unique_days={vals['unique_days']}"
        )

    lines.extend([
        "",
        "## Validation",
        f"- Errors: {len(validation['errors'])}",
    ])
    for e in validation["errors"]:
        lines.append(f"- ERROR: {e}")

    (
        WORKSPACE / "sc001_micro_calendar_summary_v0_1.md"
    ).write_text("\n".join(lines) + "\n", encoding="utf-8")

    if validation["status"] != "PASS":
        raise RuntimeError(
            "Calendar manifest validation failed. Inspect output files."
        )

    print("=" * 78)
    print("SC001-MICRO-CALENDAR-v0.1 COMPLETE")
    print("Status: PASS")
    print("Manifest SHA256:", manifest_sha)
    print("Canonical events:", len(events))
    print("Selected sample rows:", len(selected))
    print("Unique acquisition days:", len(acquisition_days))
    print("Network bytes:", f"{network_bytes_read:,}")
    print("Workspace:", WORKSPACE)
    print("=" * 78)


def main() -> None:
    free_start = ensure_storage()

    bls_events, bls_sources = parse_bls()
    fomc_events, fomc_sources = parse_fomc()

    events = dedupe_sort_events(bls_events + fomc_events)
    events = eligible_split_events(events)

    selected = build_selected_samples(events)
    acquisition_days = build_acquisition_days(selected)
    validation = validate_manifest(events, selected, acquisition_days)

    write_outputs(
        events,
        bls_sources + fomc_sources,
        selected,
        acquisition_days,
        validation,
        free_start,
    )


if __name__ == "__main__":
    main()
