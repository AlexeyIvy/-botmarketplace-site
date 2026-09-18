# SC001 — C11 v2 Selection Stage A/B Result v1.1

Date: 2026-09-19
Status: **C11_V2_SC_REJECT_DIRECTION_RETENTION**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c11-direction-rule-v2-stage-ab-selection-protocol-v1.1.md`;
- `docs/research/sc001-c11-v2-stage-ab-selection-implementation-freeze-v1.1.json`;
- `docs/research/sc001-contamination-registry-v0.20.json`.

## 1. Exact terminal state

`C11_V2_SC_REJECT_DIRECTION_RETENTION`

The frozen 24-event Selection/Calibration run completed.

No Confirmation outcome was opened.

No execution model or PnL was calculated.

## 2. Data validity

Observed:

- scheduled events = 24;
- data-valid = 24;
- DATA_INVALID = 0;
- CPI valid = 12/12;
- Employment valid = 12/12.

Schema mix:

- `LEGACY_6` = 13 archives;
- `SOURCE_7` = 11 archives;
- `source` field used in signal = false.

All frozen data-validity gates passed.

## 3. Stage A — residual post-decision headroom

Stage A exact state:

`SURVIVE`

Observed:

- events with abs +1s -> +60s residual >=20 bps = 14/24;
- CPI residual >=20 bps = 9/12;
- Employment residual >=20 bps = 5/12;
- median abs residual = ~24.1114 bps;
- p75 diagnostic = ~40.4446 bps;
- max diagnostic = ~134.5325 bps.

All frozen Stage A gates passed.

Interpretation:

A meaningful amount of macro-event price movement remains after the frozen +1 second causal decision point.

The C11 problem is therefore not simply that the move is already over by +1 second.

## 4. Stage B — Direction Rule v2 + opportunity retention

Direction Rule v2:

- first causal 1-second impulse >0 -> LONG;
- <0 -> SHORT;
- =0 -> NO_TRADE.

Observed opportunity retention:

- actionable = 24/24;
- NO_TRADE = 0;
- LONG = 17;
- SHORT = 7;
- CPI actionable = 12/12;
- Employment actionable = 12/12.

All opportunity-retention gates passed.

Directional/economic observations:

- events with signed continuation >=20 bps = 6/24;
- CPI signed >=20 bps = 3/12;
- Employment signed >=20 bps = 3/12;
- median signed continuation = ~3.6342 bps;
- positive signed continuation count diagnostic = 14/24;
- p75 signed continuation diagnostic = ~14.8142 bps;
- worst signed continuation diagnostic = ~-97.2646 bps;
- best signed continuation diagnostic = ~134.5325 bps.

Failed frozen Stage B gates:

- median signed continuation >=20 bps: FAIL;
- scheduled signed continuation >=20 bps >=10/24: FAIL;
- CPI signed >=20 bps >=4/12: FAIL;
- Employment signed >=20 bps >=4/12: FAIL.

Therefore:

`C11_V2_SC_REJECT_DIRECTION_RETENTION`

## 5. Robust interpretation

The frozen evidence separates two facts:

1. **residual movement exists after +1s**;
2. **the sign of the first 1-second impulse does not capture enough of it**.

This is a directional-extraction failure, not a residual-headroom failure and not a sample/data failure.

The median signed continuation (~3.63 bps) is far below the frozen 20 bps structural burden reference.

Only 6/24 scheduled events clear 20 bps in the chosen direction despite 14/24 events having >=20 bps absolute residual movement.

## 6. What is forbidden now

Do not:

- open prospective Confirmation;
- compute execution/PnL;
- change 1 second to 2/5/10 seconds;
- switch continuation to reversal;
- add an epsilon impulse threshold;
- select CPI-only or Employment-only;
- use macro surprise;
- drop weak events;
- lower the 20 bps burden;
- add C5/C10 vetoes;
- optimize entry delay.

A materially different direction extractor requires a separately designed future candidate/experiment and fresh evidence.

## 7. Permitted next action

A read-only postmortem on the already-produced v1.1 Selection report is permitted.

It may describe why the frozen Direction Rule v2 failed but may not score alternative trading rules.

The postmortem should support a final C11 disposition decision before any C13+ work.
