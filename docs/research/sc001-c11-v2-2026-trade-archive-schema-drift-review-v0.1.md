# SC001 — C11 v2 2026 Trade-Archive Schema Drift Review v0.1

Date: 2026-09-19
Status: **ENGINEERING SCHEMA DRIFT CONFIRMED / FINANCIAL RULES UNCHANGED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c11-v2-selection-v1-implementation-fail-review-v0.1.md`;
- `docs/research/sc001-c11-direction-rule-v2-stage-ab-selection-protocol-v1.0.md`.

## 1. Read-only diagnostic

Exact archive:

`BTC-USDT-SWAP-trades-2026-04-03.zip`

Observed:

- archive exists: true;
- compressed bytes: 16,258,455;
- exactly one CSV member;
- member: `BTC-USDT-SWAP-trades-2026-04-03.csv`;
- UTF-8 BOM: false;
- exact header:

`instrument_name,trade_id,side,price,size,created_time,source`

The prior accepted schema was:

`instrument_name,trade_id,side,price,size,created_time`

Therefore the mismatch is genuine additive schema drift, not BOM/whitespace corruption.

## 2. External semantic corroboration

OKX public trade API documentation includes a `source` response field described as order source.

OKX API changelog records addition of `source` to:

- GET / Trades;
- GET / Trades history;
- WS / All trades channel;

on 2025-09-04.

Current documented values include:

- `0` = normal order;
- `1` = special liquidity/RPI-type order source.

The C11 v2 strategy does not use `source`.

## 3. Compatibility conclusion

The first six historical fields remain identical in name and order:

1. instrument_name;
2. trade_id;
3. side;
4. price;
5. size;
6. created_time.

The new field is appended as the seventh field only.

Therefore a versioned schema-aware parser may admit exactly two schemas:

### LEGACY_6

`instrument_name,trade_id,side,price,size,created_time`

### SOURCE_7

`instrument_name,trade_id,side,price,size,created_time,source`

No other header is authorized.

## 4. Row semantics

For LEGACY_6:

- exactly six fields.

For SOURCE_7:

- exactly seven fields;
- fields 0-5 retain all prior validation semantics;
- field 6 must be exactly `0` or `1`;
- `source` is recorded diagnostically only;
- `source` cannot affect signal, direction, event inclusion, headroom, continuation or gates.

Unknown source value => implementation/schema REVIEW, not strategy REJECT.

## 5. Financial/statistical rules unchanged

No changes to:

- 24-event chronology;
- anchor semantics;
- 1-second direction rule;
- zero impulse = NO_TRADE;
- 60-second endpoint;
- 20 bps structural burden;
- data-validity gate;
- Stage A gates;
- Stage B gates;
- prospective Confirmation identities.

## 6. Rerun policy

Create v1.1 Selection runner with the exact two-schema parser.

Rerun all 24 frozen events from the beginning under one implementation version.

Previously downloaded exact-size archives may be reused after:

- exact expected filename;
- exact compressed byte size;
- ZIP CRC;
- exact allowed header;
- row-level semantic checks.

The failed v1.0 run remains implementation evidence only and has no Stage A/B verdict.
