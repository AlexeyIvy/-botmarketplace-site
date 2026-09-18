# SC001 Current Roadmap and Stop Rules v4.72

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — C11 V2 FRESH-CHRONOLOGY AUDIT COMPLETE / CALENDAR FREEZE NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.71.md`

## 1. Binding terminal states

All prior terminal decisions remain immutable.

C1-C10 remain terminal/closed as previously recorded.

C12 remains terminal:

`C12_S0_REJECT_PARITY_REVERSION`

No C12 rescue tuning is authorized.

C11-S0 remains:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

C11-S1 remains:

`C11_S1_DEFER_SAMPLE`

and must not be interpreted as REJECT.

## 2. Fresh-chronology audit completed

Binding audit:

`docs/research/sc001-c11-v2-fresh-chronology-contamination-source-audit-v0.1.md`

Exact audit state:

`C11_V2_FRESH_CHRONOLOGY_AUDIT_PASS`

The audit opened no fresh BTC price outcome.

## 3. Contamination conclusions

H1-2025 remains:

`CONTAMINATED_FOR_C11_V2_DIRECTION_DESIGN`

The old 2025-07 through 2026-08 SC001 micro-calendar reservation is not itself price contamination because its build read no market outcome.

Q4-2025 is not classified as price-contaminated, but official BLS lapse-in-appropriations disruption makes it:

`SOURCE_CALENDAR_IRREGULAR_NOT_PRIMARY_FRESH_CHRONOLOGY`

This is a source/calendar decision, not a BTC-performance filter.

## 4. Preferred candidate fresh chronology

Subject to formal freeze + metadata-only archive verification:

### Selection/Calibration candidate

`2025-Q3 + 2026-Q1`

12 events total:

- 6 CPI;
- 6 Employment Situation.

### Untouched Confirmation candidate

`2026-Q2 + 2026-Q3`

12 events total:

- 6 CPI;
- 6 Employment Situation.

Confirmation remains closed.

## 5. Source state

Existing source semantics remain qualified:

`C11_D0_SOURCE_CALENDAR_PREFLIGHT_PASS`

However, exact OKX archive identity/HEAD for the 24 candidate fresh dates has not yet been verified.

No body GET/open is authorized before the fresh chronology and metadata protocol are frozen.

## 6. C11 v2 design remains unchanged

Preferred minimal-complexity rule remains, subject to formal freeze:

- first causal 1-second post-release impulse >0 -> LONG;
- <0 -> SHORT;
- =0 -> NO_TRADE.

Do not compare alternate impulse windows.

Do not use macro surprise.

Signal states must distinguish:

- DATA_INVALID;
- NO_TRADE;
- LONG;
- SHORT.

Uncomputed metrics remain null / NOT_COMPUTED.

## 7. Required sequence from here

### Stage 1 — formal chronology freeze

Freeze exactly:

- Selection/Calibration event identities;
- untouched Confirmation event identities;
- official event family/time semantics;
- objective source-correction policy.

No price outcome.

### Stage 2 — metadata-only source preflight

For every frozen event:

- official BLS date/time check;
- exact OKX `BTC-USDT-SWAP-trades-YYYY-MM-DD.zip` identity/HEAD;
- no historical body GET/open;
- no macro values/surprise;
- no BTC outcome.

### Stage 3 — freeze Stage A / Stage B design

Only after metadata PASS, freeze:

- Direction Rule v2;
- +1s -> +60s absolute residual-headroom metric and gates;
- actionable-share gate;
- CPI/Employment breadth gates;
- signed-continuation gates;
- opportunity funnel reporting.

### Stage 4 — fresh Selection/Calibration outcome

Only after all above freezes.

### Stage 5 — untouched Confirmation

Open only if Selection/Calibration survives exactly frozen Stage A and Stage B.

No rule changes.

### Stage 6 — execution

Only after Confirmation survives.

Then, and only then, build event slippage/latency/fill/PnL model.

## 8. C13+ gate

Do not create C13+ while C11 remains structurally alive and this fresh v2 program is unresolved.

## 9. Immediate next action

Create the formal C11 v2 fresh chronology freeze for the audited 12-event Selection/Calibration set and 12-event Confirmation reserve, then prepare the metadata-only D1-style source/archive preflight.

No VPS price-bearing run is authorized.
