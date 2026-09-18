# SC001 Current Roadmap and Stop Rules v4.73

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — C11 V2 CORRECTED CHRONOLOGY FROZEN / METADATA-ONLY PREFLIGHT NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.72.md`

## 1. Binding terminal state

All prior terminal decisions remain immutable.

C1-C10 remain terminal/closed.

C12 remains terminal:

`C12_S0_REJECT_PARITY_REVERSION`

C11-S0 remains:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

C11-S1 remains:

`C11_S1_DEFER_SAMPLE`

and is not a REJECT.

## 2. Corrected chronology audit

Binding corrected audit:

`docs/research/sc001-c11-v2-fresh-chronology-contamination-source-audit-v0.2.md`

Exact state:

`C11_V2_FRESH_CHRONOLOGY_AUDIT_V02_PASS`

Reason for correction:

SC001-E001 had already opened Binance BTC 1-hour outcomes through 2026-09-09 19:00 UTC, including a 2025-2026 Final slice.

Therefore historical later periods cannot be described as globally price-unseen.

## 3. Correct contamination interpretation

Historical later C11 dates may still be used as Selection/Calibration because their C11-specific OKX event outcomes remain unopened.

Classification:

`C11_MICROSTRUCTURE_OUTCOME_UNOPENED_BUT_SC001_COARSE_PRICE_EXPOSED`

They are nonpromotional only.

Untouched Confirmation must not reuse those historical blocks.

## 4. C11 v2 chronology freeze

Binding:

`docs/research/sc001-c11-v2-chronology-freeze-v0.1.md`

### Selection/Calibration

24 exact releases:

- 2025-Q3;
- 2026-Q1;
- 2026-Q2;
- 2026-Q3;

with:

- 12 CPI;
- 12 Employment Situation.

Q4-2025 is excluded for official BLS source/calendar incompleteness after the lapse in appropriations, not because of BTC performance.

### Confirmation

12 exact event identities by reference month:

`2026-09 through 2027-02`

For every reference month:

- Employment Situation;
- Consumer Price Index.

This Confirmation block is fully prospective relative to the 2026-09-19 freeze.

## 5. Calendar revision policy

For future Confirmation:

- identity = family + reference month;
- official BLS date/time revisions do not change the identity;
- use final official scheduled timestamp before release;
- cancellation -> `CALENDAR_CANCELED`;
- no replacement event;
- canceled slot stays in frozen-slot denominator;
- no synthetic outcome.

## 6. Current opportunity funnel

Future C11 event reporting:

`frozen_slots -> released_events -> data_valid -> actionable -> executed`

Signal states for released events:

- DATA_INVALID;
- NO_TRADE;
- LONG;
- SHORT.

Calendar cancellation is a separate source-state, not a signal state.

## 7. Immediate next stage

Prepare/freeze and then run a metadata-only preflight for the exact 24 Selection/Calibration releases.

The preflight may access only:

- official BLS schedule pages;
- OKX archive resolver metadata;
- exact archive HEAD / Content-Length.

It may not:

- GET/open historical trade bodies;
- calculate first impulse;
- calculate +1s -> +60s move;
- score direction;
- calculate execution/PnL;
- access Confirmation outcomes.

## 8. Stage after metadata PASS

Only after 24/24 Selection metadata PASS:

1. freeze Direction Rule v2;
2. freeze Stage A residual-headroom gates;
3. freeze actionable-share and family-breadth gates;
4. freeze signed-continuation gates;
5. freeze null/NOT_COMPUTED semantics;
6. only then authorize Selection/Calibration price-body access.

## 9. Confirmation gate

Confirmation remains closed unless Selection/Calibration survives the exact frozen Stage A + Stage B program.

No parameter, window, direction, family or threshold change after Selection outcome.

## 10. C13+ gate

Do not open C13+ while C11 remains alive and unresolved.

## 11. Current next action

Create the 24-event metadata-only protocol + runner + implementation freeze.

No VPS price-bearing run is authorized.
