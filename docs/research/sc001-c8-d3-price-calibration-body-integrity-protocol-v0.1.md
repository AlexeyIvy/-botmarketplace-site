# SC001 — C8-D3 Price Calibration Body Integrity Protocol v0.1

Date: 2026-09-18
Status: **FROZEN BODY/SCHEMA NORMALIZATION BEFORE FIRST CROSS-VENUE PRICE COMPARISON**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c8-d1e-strict-coactive-1s-pass-result-v0.1.md`;
- `docs/research/sc001-c8-d2-price-calibration-metadata-preflight-protocol-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.12.json`.

## 1. Purpose

Download/open the exact prospectively contaminated 2025-01-20 C8 price-calibration trade bodies, verify source integrity, and normalize **per-venue** strict 1-second last-trade records.

D3 must not compare prices across venues.

## 2. Exact bodies

Only:

- OKX `BTC-USDT-SWAP-trades-2025-01-20.zip`;
- OKX `BTC-USDT-SWAP-trades-2025-01-21.zip` as D+1 source support;
- Bybit `BTCUSDT2025-01-20.csv.gz`.

All exact filenames and Content-Length values must match the D2 metadata parent.

## 3. OKX reconstruction

Apply the already-qualified rule:

`D + D+1 -> retain created_time in UTC [2025-01-20,2025-01-21)`.

Require:

- ZIP CRC;
- exact header;
- exact instrument;
- finite positive price/size;
- side buy/sell;
- consistent timestamp scale;
- source timestamps nondecreasing;
- source trade IDs strictly increasing;
- target UTC trade IDs strictly increasing with zero gaps;
- all 1440 target UTC minutes observed;
- both sides observed.

## 4. Bybit integrity

Require:

- gzip parse;
- first five header semantics exactly `timestamp,symbol,side,size,price`;
- symbol BTCUSDT;
- side Buy/Sell;
- finite positive size/price;
- target UTC date only;
- timestamps nondecreasing;
- all 1440 target UTC minutes observed.

## 5. Frozen per-venue 1-second normalization

For each venue separately:

- `second_id = floor(timestamp_us / 1_000_000)`;
- retain the **chronologically last trade inside each active UTC second**;
- if multiple rows share the same maximal timestamp inside a second, retain the final row in source order;
- no carry-forward;
- no future interpolation.

Normalized columns exactly:

- `second_id`;
- `last_trade_ts_us`;
- `last_trade_price`.

Write:

- `normalized/okx_last_trade_1s.csv`;
- `normalized/bybit_last_trade_1s.csv`.

D3 must not intersect the two normalized files and must not calculate any cross-venue price difference.

## 6. D3 PASS gates

Require:

- both source venues integrity PASS;
- OKX active seconds >=70,000;
- Bybit active seconds >=70,000;
- both venues active in all 24 UTC hours;
- normalized timestamps strictly increasing by second_id;
- all normalized prices finite positive.

These are data-integrity/sample gates only.

## 7. Exact terminal states

PASS:

`C8_D3_PRICE_BODY_INTEGRITY_PASS`

REVIEW:

`C8_D3_PRICE_BODY_INTEGRITY_REVIEW`

REVIEW is data/implementation state only.

## 8. Firewalls

Must state:

- historical_trade_bodies_opened = true;
- per_venue_prices_normalized = true;
- cross_venue_price_compared = false;
- cross_venue_return_calculated = false;
- rolling_cross_venue_baseline_calculated = false;
- raw_spread_calculated = false;
- dislocation_calculated = false;
- convergence_outcome_calculated = false;
- strategy_signal_calculated = false;
- pnl_calculated = false;
- promotional_alpha_accessed = false.

## 9. Consequence of PASS

Only after D3 PASS may the already-frozen C8B-S0 structural headroom protocol be implemented and run.

No C8 price outcome is authorized inside D3 itself.
