# SC001 — C12-D1 USDC-USDT Spot Trade Archive Semantics v0.1

Date: 2026-09-18
Status: **FROZEN ENGINEERING SOURCE-SEMANTICS STAGE / NO PEG OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c12-d0-source-parity-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.15.json`.

## 1. Purpose

Qualify historical OKX SPOT trade archive schema, timestamps and UTC stitching semantics for C12 without calculating any peg deviation.

## 2. Exact bodies

Authorized engineering bodies:

- `USDC-USDT-trades-2025-01-15.zip`;
- `USDC-USDT-trades-2025-01-16.zip`.

No other date/body is authorized.

## 3. Source retrieval

Use the same exact SPOT priapi metadata contract qualified by C12-D0.

Require:

- exact filename;
- trusted `static.okx.com` URL;
- positive HEAD Content-Length;
- D archive size equals C12-D0 parent metadata;
- D+1 exact archive resolves.

## 4. Body/schema integrity

For each ZIP:

- ZIP CRC PASS;
- exactly one regular CSV member;
- exact header:
  `instrument_name,trade_id,side,price,size,created_time`;
- exact instrument = `USDC-USDT`;
- side in `buy/sell`;
- price finite >0;
- size finite >0;
- timestamp scale resolved causally;
- source timestamps nondecreasing;
- source trade IDs strictly increasing;
- zero malformed rows.

Price is validated numerically only.

It must not be compared to 1.0 or any parity reference.

## 5. UTC target-day stitch

Construct engineering target day:

`2025-01-15 UTC`

from D + D+1 by retaining rows with:

`2025-01-15T00:00:00Z <= created_time < 2025-01-16T00:00:00Z`.

Require:

- target rows >0;
- timestamps nondecreasing;
- trade IDs strictly increasing;
- both D and D+1 contribute at least one target row;
- target rows include both buy and sell sides.

No minimum minute coverage is imposed because spot trade activity may be sparse.

## 6. Exact states

PASS:

`C12_D1_SPOT_TRADE_SEMANTICS_PASS`

REVIEW:

`C12_D1_SPOT_TRADE_SEMANTICS_REVIEW`

## 7. Firewalls

Must remain false:

- peg_deviation_calculated;
- parity_threshold_selected;
- reversion_outcome_calculated;
- strategy_signal_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 8. Consequence of PASS

Only after D1 PASS may C12 prospectively freeze a calendar Selection/Calibration batch and a peg-dislocation headroom/reversion sentinel.
