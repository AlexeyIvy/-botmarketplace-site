# SC001 Current Roadmap and Stop Rules v4.79

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — C11 V2 SELECTION V1.1 DUAL-SCHEMA IMPLEMENTATION FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.78.md`

## 1. Binding research state

All prior terminal decisions remain unchanged.

C11 remains active and unresolved.

No Stage A or Stage B verdict exists yet for C11 v2 Selection.

## 2. v1.0 implementation failure reviewed

The first price-bearing v1.0 Selection attempt stopped at event 13:

`EMPLOYMENT 2026-04-03`

with:

`C11_V2_SELECTION_IMPLEMENTATION_FAIL`

Reason:

`header mismatch`

Read-only diagnostic established exact schema drift:

legacy:
`instrument_name,trade_id,side,price,size,created_time`

new:
`instrument_name,trade_id,side,price,size,created_time,source`

No BOM.

## 3. Official semantic corroboration

OKX public trade API documentation defines `source` as order source.

The strategy does not use this field.

Therefore the parser amendment is engineering-only.

## 4. v1.1 allowed schemas

Exactly two headers:

### LEGACY_6
`instrument_name,trade_id,side,price,size,created_time`

### SOURCE_7
`instrument_name,trade_id,side,price,size,created_time,source`

SOURCE_7 requires:

`source in {"0","1"}`

Any other header or source value:

`C11_V2_SELECTION_IMPLEMENTATION_FAIL`

No arbitrary permissive column handling.

## 5. Financial/statistical rules unchanged

All v1.0 frozen rules remain binding:

- 24 Selection events;
- 12 CPI / 12 Employment;
- +1s Direction Rule v2;
- exact zero = NO_TRADE;
- +60s endpoint;
- 20 bps burden;
- data-validity gate;
- Stage A gates;
- Stage B retention/breadth/economic gates.

No threshold or chronology change.

## 6. v1.1 frozen implementation

Protocol:

`docs/research/sc001-c11-direction-rule-v2-stage-ab-selection-protocol-v1.1.md`

Runner:

`research/sc001/sc001_c11_v2_selection_stage_ab_v1_1.py`

Freeze:

`docs/research/sc001-c11-v2-stage-ab-selection-implementation-freeze-v1.1.json`

## 7. Rerun rule

Rerun all 24 events from the beginning under v1.1.

Exact-size already downloaded archives may be reused after the full v1.1 integrity/schema checks.

Do not combine partial v1.0 and v1.1 calculations into a final verdict.

## 8. Possible terminal states

Only:

- `C11_V2_SC_DEFER_DATA_QUALITY`;
- `C11_V2_SC_REJECT_RESIDUAL_HEADROOM`;
- `C11_V2_SC_REJECT_DIRECTION_RETENTION`;
- `C11_V2_SC_SURVIVE_TO_PROSPECTIVE_CONFIRMATION`.

Implementation failure remains a non-verdict engineering state.

## 9. Confirmation and execution

Prospective Confirmation remains closed.

Execution/PnL remains closed.

No C13+.

## 10. Immediate next action

Syntax-check and run the frozen v1.1 Selection runner across all 24 events.

Do not interpret partial output.
