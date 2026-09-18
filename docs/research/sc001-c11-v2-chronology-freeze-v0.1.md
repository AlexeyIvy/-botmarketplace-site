# SC001 — C11 v2 Chronology Freeze v0.1

Date: 2026-09-19
Status: **FROZEN BEFORE C11 V2 SELECTION/CALIBRATION PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c11-v2-fresh-chronology-contamination-source-audit-v0.2.md`;
- `docs/research/sc001-c11-direction-rule-v2-research-plan-v0.1.md`;
- `docs/research/sc001-e001-results-v0.1.md`.

## 1. Purpose

Freeze:

1. the historical nonpromotional C11 v2 Selection/Calibration event chronology;
2. the untouched prospective Confirmation event identities;

before any new C11 v2 BTC event outcome is opened.

This document does not freeze the final direction/economic gates and does not authorize price-body access.

## 2. Selection/Calibration role

Classification:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

Contamination qualifier:

`C11_MICROSTRUCTURE_OUTCOME_UNOPENED_BUT_SC001_COARSE_PRICE_EXPOSED`

for events at/before the E001 historical cutoff.

The 2026-09-11 CPI release is after the E001 cutoff but remains in Selection/Calibration under the same calendar block.

No Selection/Calibration event may later be promoted as untouched Confirmation evidence.

## 3. Exact 24 Selection/Calibration events

| # | Family | Release date | Release UTC | BLS release identity |
|---:|---|---|---|---|
| 1 | Employment | 2025-07-03 | 12:30 | Employment Situation for June 2025 |
| 2 | CPI | 2025-07-15 | 12:30 | Consumer Price Index for June 2025 |
| 3 | Employment | 2025-08-01 | 12:30 | Employment Situation for July 2025 |
| 4 | CPI | 2025-08-12 | 12:30 | Consumer Price Index for July 2025 |
| 5 | Employment | 2025-09-05 | 12:30 | Employment Situation for August 2025 |
| 6 | CPI | 2025-09-11 | 12:30 | Consumer Price Index for August 2025 |
| 7 | Employment | 2026-01-09 | 13:30 | Employment Situation for December 2025 |
| 8 | CPI | 2026-01-13 | 13:30 | Consumer Price Index for December 2025 |
| 9 | Employment | 2026-02-11 | 13:30 | Employment Situation for January 2026 |
| 10 | CPI | 2026-02-13 | 13:30 | Consumer Price Index for January 2026 |
| 11 | Employment | 2026-03-06 | 13:30 | Employment Situation for February 2026 |
| 12 | CPI | 2026-03-11 | 12:30 | Consumer Price Index for February 2026 |
| 13 | Employment | 2026-04-03 | 12:30 | Employment Situation for March 2026 |
| 14 | CPI | 2026-04-10 | 12:30 | Consumer Price Index for March 2026 |
| 15 | Employment | 2026-05-08 | 12:30 | Employment Situation for April 2026 |
| 16 | CPI | 2026-05-12 | 12:30 | Consumer Price Index for April 2026 |
| 17 | Employment | 2026-06-05 | 12:30 | Employment Situation for May 2026 |
| 18 | CPI | 2026-06-10 | 12:30 | Consumer Price Index for May 2026 |
| 19 | Employment | 2026-07-02 | 12:30 | Employment Situation for June 2026 |
| 20 | CPI | 2026-07-14 | 12:30 | Consumer Price Index for June 2026 |
| 21 | Employment | 2026-08-07 | 12:30 | Employment Situation for July 2026 |
| 22 | CPI | 2026-08-12 | 12:30 | Consumer Price Index for July 2026 |
| 23 | Employment | 2026-09-04 | 12:30 | Employment Situation for August 2026 |
| 24 | CPI | 2026-09-11 | 12:30 | Consumer Price Index for August 2026 |

Family breadth is fixed:

- Employment = 12;
- CPI = 12.

No date may be removed because first impulse is zero, residual movement is small, direction is wrong, or execution looks expensive.

## 4. Why Q4-2025 is absent

Q4-2025 suffered official BLS lapse-in-appropriations disruption with canceled core CPI/Employment release identities.

Therefore the complete quarter is excluded prospectively for calendar integrity.

No BTC price outcome was used for this exclusion.

## 5. Prospective Confirmation identities

Classification:

`UNTOUCHED_PROSPECTIVE_CONFIRMATION`

Freeze reference months:

- 2026-09;
- 2026-10;
- 2026-11;
- 2026-12;
- 2027-01;
- 2027-02.

For every reference month include exactly:

- Employment Situation;
- Consumer Price Index.

Total frozen Confirmation identities:

`12`

### Currently published future timestamps

- Employment Situation for September 2026 -> 2026-10-02 08:30 ET;
- CPI for September 2026 -> 2026-10-14 08:30 ET;
- Employment Situation for October 2026 -> 2026-11-06 08:30 ET;
- CPI for October 2026 -> 2026-11-10 08:30 ET;
- Employment Situation for November 2026 -> 2026-12-04 08:30 ET;
- CPI for November 2026 -> 2026-12-10 08:30 ET.

For the six 2027 identities, the event identity is already frozen even though the official publication dates are not yet required to be known.

## 6. Calendar-change rule for Confirmation

A frozen Confirmation identity is `family + reference_month`.

If BLS revises its scheduled date/time:

- keep the same identity;
- use the latest official scheduled timestamp available before publication;
- record the revision source;
- do not replace the event.

If BLS cancels a frozen identity:

- mark `CALENDAR_CANCELED`;
- do not replace it;
- keep it in the frozen-slot denominator;
- do not synthesize a signal or price outcome.

## 7. Confirmation firewall

Before Selection/Calibration survives its exact frozen Stage A + Stage B gates:

- no Confirmation BTC trade body may be opened;
- no first impulse may be calculated;
- no residual move may be calculated;
- no direction may be scored;
- no execution/PnL may be calculated.

Metadata/calendar maintenance alone does not authorize outcome access.

## 8. Current research-kernel funnel

For future event research report:

`frozen_slots -> released_events -> data_valid -> actionable -> executed`

For released data-valid events:

`signal_state = NO_TRADE / LONG / SHORT`

For invalid market data:

`signal_state = DATA_INVALID`

For canceled calendar identities:

`event_source_state = CALENDAR_CANCELED`

and signal metrics remain null / NOT_COMPUTED.

## 9. Next allowed action

Prepare and freeze a metadata-only source/archive preflight for the exact 24 Selection/Calibration events.

No price-body access is authorized by this chronology freeze.
