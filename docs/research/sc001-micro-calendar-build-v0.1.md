# SC001 Micro Calendar Build v0.1

Status: **FROZEN BEFORE CALENDAR BUILD AND BEFORE MICROSTRUCTURE P&L**

Purpose: construct `SC001-MICRO-CALENDAR-v0.1` from official macro calendars and the deterministic date-selection rules frozen in `docs/research/sc001-microstructure-pretest-v0.1.md`.

## Inputs

Canonical macro sources:

- BLS annual release schedules for 2023, 2024, 2025 and 2026;
- Federal Reserve FOMC meeting calendar;
- individual Federal Reserve monetary-policy statement pages for the frozen scheduled FOMC decision dates.

Primary event classes only:

- CPI;
- Employment Situation / NFP;
- scheduled FOMC policy decision.

No price, volatility, volume, spread, return, strategy output or P&L is read by this step.

## Frozen split

- DEV: 2023-04-01 through 2024-06-30
- VALIDATION: 2024-07-01 through 2025-06-30
- FINAL: 2025-07-01 through 2026-08-31

Qualification-only dates permanently excluded:

- 2023-04-15
- 2024-01-15
- 2025-01-15
- 2026-07-15

## Frozen deterministic sampling

Seed:

`SC001-MICRO-v0.1-20260911`

Hash: SHA-256.

For each calendar quarter intersecting a split:

- select one ordinary weekday;
- select one ordinary weekend day;
- select one CPI event;
- select one NFP event;
- select one scheduled FOMC decision.

Ordinary candidates exclude all primary-event days and qualification-only dates.

Selection is hash-based only and must not inspect market outcomes.

## Event timestamps

BLS release times are interpreted as official U.S. Eastern Time and converted deterministically to UTC using U.S. DST rules.

FOMC release time is parsed from the official statement page, including explicit `EDT` / `EST`, then converted to UTC.

## Safety

This step downloads only official HTML pages.

Hard limits:

- total network cap: 50,000,000 bytes;
- per-response cap: 5,000,000 bytes, except FOMC statement pages capped at 2,000,000 bytes;
- minimum free storage reserve: 4,000,000,000 bytes.

No tick/L2 bulk archive is downloaded.

## Required outputs

- `sc001_micro_calendar_manifest_v0_1.json`
- `sc001_micro_calendar_manifest_v0_1.sha256`
- `sc001_micro_calendar_selected_v0_1.csv`
- `sc001_micro_calendar_sources_v0_1.json`
- `sc001_micro_calendar_final_safety_v0_1.json`
- `sc001_micro_calendar_summary_v0_1.md`

The final manifest must validate `PASS` before any staged bulk microstructure acquisition is authorized.

## Anti-rescue

After the manifest is frozen, dates cannot be added, removed, replaced or reclassified because of observed BTC movement, spread, volatility, liquidity or strategy profitability.

Any correction for an objectively documented source/calendar error requires a new version while preserving v0.1.
