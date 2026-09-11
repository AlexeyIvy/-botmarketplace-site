# SC001-MICRO-CALENDAR-v0.1 — Results

Status: **PASS**

Purpose: freeze the SC001 microstructure acquisition calendar before any bulk tick/L2 download and before strategy P&L.

## Integrity checks

- Manifest SHA256 recomputed independently and matched the supplied `.sha256` file exactly:
  `e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b`.
- Selected CSV contains exactly 70 rows and 70 unique acquisition dates.
- Split counts: DEV 25, VALIDATION 20, FINAL 25.
- Sample composition: 42 event days (14 CPI, 14 NFP, 14 FOMC), 14 ordinary weekdays, 14 ordinary weekend days.
- Every intersecting calendar quarter from 2023-Q2 through 2026-Q3 contains exactly one CPI, one NFP, one FOMC, one ordinary weekday, and one ordinary weekend sample.
- No selected acquisition date overlaps the qualification-only dates:
  `2023-04-15`, `2024-01-15`, `2025-01-15`, `2026-07-15`.
- Ordinary samples do not overlap any canonical CPI/NFP/FOMC date.
- All selected dates fall inside their frozen split boundaries and all quarter labels are internally consistent.
- CSV rows match the manifest `selected_samples` exactly, and acquisition tags match their selected-sample classification.

## Event-time checks

The frozen calendar uses official BLS annual schedules for CPI/NFP and Federal Reserve FOMC statement pages for decision timestamps. UTC conversion is internally consistent with U.S. Eastern daylight/standard time: 08:30 ET maps to 12:30 UTC during EDT and 13:30 UTC during EST; 14:00 ET maps to 18:00 UTC during EDT and 19:00 UTC during EST.

Canonical event counts: CPI 40, NFP 40, FOMC 27. Event-window policy remains primary `[-30,+60]` minutes with diagnostic `[-5,+30]` and `[-60,+180]` windows.

## Safety

- Strategy/P&L calculated: **NO**.
- Bulk tick/L2 download: **NO**.
- Network bytes read: 2,786,850.
- Workspace after outputs: 92,135 bytes.
- Minimum free-storage reserve: 4 GB; free storage remained ~69.1 GB.

## Interpretation

The calendar freeze is valid and can be used as the sole acquisition-day schedule for the first SC001 microstructure experiment. This PASS is a protocol/data-selection result only; it does not imply trading edge or profitability.

The next stage may acquire market data only for these frozen dates, under staged storage limits and full integrity/replay validation. FINAL remains unopened for P&L until a strategy version, signal rules, execution model, fees, latency assumptions, and gates are frozen.
