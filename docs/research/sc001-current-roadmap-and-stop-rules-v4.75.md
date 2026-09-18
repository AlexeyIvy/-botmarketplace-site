# SC001 Current Roadmap and Stop Rules v4.75

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — C11 V2 METADATA V0.1 REVIEW / V0.2 ENGINEERING FIX FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.74.md`

## 1. Binding prior state

All prior terminal decisions remain unchanged.

C11-S0:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

C11-S1:

`C11_S1_DEFER_SAMPLE`

C12 remains terminal.

## 2. Metadata preflight v0.1 result

The first 24-event metadata-only run returned:

`C11_V2_SC_METADATA_PREFLIGHT_REVIEW`

at:

`EMPLOYMENT 2026-06-05`

Observed reason:

`BLS metadata mismatch ... date=False, title=True, time=True`

No historical trade body was opened.

No macro value/surprise, first impulse, residual move, direction, continuation, execution or PnL was calculated.

## 3. Objective diagnosis

Official BLS confirms:

- Friday, June 05, 2026;
- 08:30 AM;
- Employment Situation for May 2026.

The v0.1 runner expected a literal unpadded day string equivalent to:

`June 5, 2026`

while the official BLS list page used:

`June 05, 2026`

Classification:

`ENGINEERING_BLS_DAY_ZERO_PADDING_PARSER_DEFECT`

This is not a calendar defect, data-quality failure, or strategy verdict.

## 4. v0.2 parser amendment

Binding protocol:

`docs/research/sc001-c11-v2-selection-metadata-preflight-protocol-v0.2.md`

Runner:

`research/sc001/sc001_c11_v2_sc_metadata_preflight_v0_2.py`

Implementation freeze:

`docs/research/sc001-c11-v2-selection-metadata-preflight-implementation-freeze-v0.2.json`

The new BLS check requires one row-level pattern containing together:

- weekday;
- exact month;
- exact day, allowing zero-padded or unpadded formatting only;
- exact year;
- exact 08:30 AM;
- exact release family.

No economic or chronology rule changed.

## 5. Rerun rule

Run all 24 events again under v0.2.

Do not resume at event 17.

Reason:

one complete report under one parser implementation is cleaner than combining partial v0.1 and v0.2 evidence.

## 6. Allowed operations remain metadata-only

Authorized:

- BLS schedule GET;
- OKX archive resolver metadata;
- exact archive HEAD.

Forbidden:

- archive body GET/open;
- macro values/surprise;
- first impulse;
- residual move;
- direction;
- continuation;
- execution;
- PnL;
- Confirmation outcome.

## 7. Next state

Expected exact outputs remain:

- `C11_V2_SC_METADATA_PREFLIGHT_PASS`;
- `C11_V2_SC_METADATA_PREFLIGHT_REVIEW`.

If PASS:

freeze Direction Rule v2 + Stage A/B gates before any price-body access.

If REVIEW:

inspect only the objective source/engineering reason. No date substitution or strategy redesign.

## 8. Immediate next action

Syntax-check and run v0.2 once across all 24 frozen Selection/Calibration events.

No price-bearing run is authorized.
