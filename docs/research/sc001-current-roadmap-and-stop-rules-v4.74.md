# SC001 Current Roadmap and Stop Rules v4.74

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — C11 V2 CHRONOLOGY + METADATA PREFLIGHT IMPLEMENTATION FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.73.md`

## 1. Binding prior state

All terminal C1-C10 and C12 decisions remain immutable.

C11 remains the only active structural survivor.

C11-S0:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

C11-S1:

`C11_S1_DEFER_SAMPLE`

No rescue interpretation.

## 2. Corrected audit is binding

Use:

`docs/research/sc001-c11-v2-fresh-chronology-contamination-source-audit-v0.2.md`

Do not use v0.1 as the current contamination conclusion.

Key correction:

SC001-E001 consumed Binance BTC 1h outcomes through 2026-09-09 19:00 UTC.

Therefore historical 2025-2026 later periods are not globally price-unseen.

## 3. Chronology is now frozen

Binding:

`docs/research/sc001-c11-v2-chronology-freeze-v0.1.md`

Selection/Calibration:

- 24 releases;
- 12 CPI;
- 12 Employment;
- 2025-Q3 + 2026-Q1/Q2/Q3;
- nonpromotional only.

Confirmation:

- 12 future event identities;
- reference months 2026-09 through 2027-02;
- CPI + Employment for each month;
- fully prospective relative to the 2026-09-19 freeze.

## 4. Metadata preflight protocol and runner frozen

Protocol:

`docs/research/sc001-c11-v2-selection-metadata-preflight-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c11_v2_sc_metadata_preflight_v0_1.py`

Implementation freeze:

`docs/research/sc001-c11-v2-selection-metadata-preflight-implementation-freeze-v0.1.json`

Exact allowed operations:

- GET official BLS schedule pages;
- query OKX metadata resolver;
- HEAD exact archive;
- record positive Content-Length.

Exact forbidden operations:

- archive body GET/open;
- macro value/surprise;
- first impulse;
- residual move;
- direction;
- continuation;
- execution;
- PnL;
- Confirmation outcome.

## 5. Exact next state machine

Run the metadata-only preflight once.

Possible terminal outputs:

- `C11_V2_SC_METADATA_PREFLIGHT_PASS`;
- `C11_V2_SC_METADATA_PREFLIGHT_REVIEW`.

REVIEW is source/engineering-only and must not be converted into a strategy verdict.

No missing date or archive may be replaced post hoc.

## 6. If metadata PASS

Then and only then freeze:

### Direction Rule v2

Preferred rule remains:

- 1-second causal impulse > 0 -> LONG;
- < 0 -> SHORT;
- = 0 -> NO_TRADE.

No alternate-window grid.

### Stage A

Freeze +1s -> +60s absolute residual-headroom metric and gates.

### Stage B

Freeze:

- actionable share;
- CPI breadth;
- Employment breadth;
- signed continuation count/economics;
- median signed continuation;
- full denominator handling.

No price body may be opened until all these are frozen.

## 7. If metadata REVIEW

Fix only objectively identified source/engineering defects without changing:

- event identities;
- chronology;
- direction rule concept;
- future Confirmation identities.

No substitution based on price or archive convenience.

## 8. Confirmation remains closed

No Confirmation market outcome before historical Selection/Calibration survives the exact frozen v2 program.

Future calendar-date revisions may update official timestamps for the same frozen event identity only.

Canceled release identity:

`CALENDAR_CANCELED`

No replacement.

## 9. C13+ gate

Do not open C13+.

## 10. Immediate next action

Syntax-check and execute the frozen 24-event metadata-only preflight.

This is not a price-bearing run and does not authorize any C11 outcome.
