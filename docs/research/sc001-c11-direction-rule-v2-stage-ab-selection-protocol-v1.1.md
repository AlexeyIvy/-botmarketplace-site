# SC001 — C11 Direction Rule v2 + Stage A/B Selection Protocol v1.1

Date: 2026-09-19
Status: **ENGINEERING-ONLY SCHEMA AMENDMENT BEFORE COMPLETE SELECTION VERDICT**
Scope: `SCALPING RESEARCH / SC001`
Supersedes implementation schema semantics only from:
`docs/research/sc001-c11-direction-rule-v2-stage-ab-selection-protocol-v1.0.md`

Parent schema review:

`docs/research/sc001-c11-v2-2026-trade-archive-schema-drift-review-v0.1.md`

## 1. Financial/statistical inheritance

All v1.0 financial/statistical rules remain unchanged:

- exact 24-event chronology;
- pre/+1s/+60s anchor semantics;
- 1000 ms anchor staleness;
- first 1-second impulse direction;
- exact zero -> NO_TRADE;
- 20 bps structural burden;
- data-valid >=22/24, >=11/12 each family;
- Stage A >=12/24 residual >=20 bps;
- Stage A median >=20 bps;
- Stage A family breadth >=5/12 each;
- Stage B actionable >=18/24;
- Stage B actionable breadth >=8/12 each;
- Stage B median signed continuation >=20 bps;
- Stage B scheduled signed >=20 bps >=10/24;
- Stage B family signed >=20 bps >=4/12 each.

No outcome-driven threshold or chronology change is authorized.

## 2. Allowed OKX trade schemas

Exactly two schemas are accepted.

### LEGACY_6

`instrument_name,trade_id,side,price,size,created_time`

### SOURCE_7

`instrument_name,trade_id,side,price,size,created_time,source`

Any other header is an implementation failure.

## 3. Common field semantics

For both schemas require:

- exact instrument `BTC-USDT-SWAP`;
- trade_id parses integer and is strictly increasing within archive;
- side is exactly `buy` or `sell`;
- price finite and >0;
- size finite and >0;
- created_time resolves under the already qualified timestamp-scale parser;
- timestamps nondecreasing.

## 4. SOURCE_7 semantics

Require seventh field:

`source in {"0","1"}`

The field is diagnostic only.

It must not:

- alter event admission;
- alter price anchors;
- alter impulse sign;
- alter Stage A/B calculations;
- become a filter/veto;
- become an execution assumption.

Unknown source values produce:

`C11_V2_SELECTION_IMPLEMENTATION_FAIL`

for schema review only.

## 5. Reporting

Per event record:

- `trade_schema = LEGACY_6 | SOURCE_7`;
- diagnostic counts:
  - `source_0_rows`;
  - `source_1_rows`;

or null for LEGACY_6.

No source-conditioned performance metric may be calculated.

## 6. Rerun

Run all 24 frozen Selection/Calibration events from the beginning under v1.1.

The final report must be produced by v1.1 alone.

Confirmation and execution/PnL remain closed.
