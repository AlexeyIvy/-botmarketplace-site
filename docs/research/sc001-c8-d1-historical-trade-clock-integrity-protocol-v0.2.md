# SC001 — C8-D1 Historical Trade Clock Integrity Protocol v0.2

Date: 2026-09-18
Status: **FROZEN OKX UTC-STITCH REPAIR AFTER D1 v0.1 REVIEW / NO CROSS-VENUE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`
Supersedes: `sc001-c8-d1-historical-trade-clock-integrity-protocol-v0.1.md`

Parents:

- `docs/research/sc001-c8-d1-v0.1-historical-clock-review-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.11.json`;
- `docs/research/sc001-c8-d0-v0.3-source-clock-pass-result-v0.1.md`;
- `docs/research/sc001-data-q006r-results-v0.1.md`.

## 1. Repair scope

D1 v0.1 used one OKX daily archive as if it represented one UTC calendar day.

Previously qualified SC001 Q006R semantics prove this is wrong.

Frozen OKX reconstruction:

`archive D + archive D+1 -> retain created_time in UTC [D,D+1)`.

D1 v0.2 changes only this source reconstruction.

It does not change synchronization thresholds or any C8 economic rule.

## 2. Exact target UTC date

`2025-01-15 UTC`

## 3. Exact historical bodies

Authorized:

- OKX `BTC-USDT-SWAP-trades-2025-01-15.zip`;
- OKX `BTC-USDT-SWAP-trades-2025-01-16.zip`;
- Bybit `BTCUSDT2025-01-15.csv.gz`.

No other body/date is authorized.

## 4. OKX D+1 discovery

Use the same frozen historical resolver as D0 v0.3:

`POST /priapi/v5/broker/public/trade-data/download-link`

with target-day payload for 2025-01-15.

From returned metadata:

- exact D file must remain resolvable;
- exact D+1 filename must resolve uniquely:
  `BTC-USDT-SWAP-trades-2025-01-16.zip`;
- host = `static.okx.com`;
- HEAD Content-Length positive;
- GET identity exact.

The existing D file may be reused after D0/D1 identity checks.

## 5. OKX source integrity

For both D and D+1 archives:

- ZIP CRC;
- exactly one CSV member;
- exact header:
  `instrument_name,trade_id,side,price,size,created_time`;
- target instrument exact;
- side `buy/sell`;
- price/size finite positive;
- one consistent timestamp scale per archive;
- source timestamps nondecreasing;
- source trade IDs strictly increasing;
- zero malformed rows.

Source rows outside the target UTC day are expected and are not a failure.

## 6. OKX target UTC stitch integrity

After scanning D then D+1, retain only timestamps in:

`2025-01-15T00:00:00Z <= ts < 2025-01-16T00:00:00Z`.

Require:

- admitted rows >0;
- zero instrument mismatch;
- timestamps nondecreasing;
- trade IDs strictly increasing;
- trade-ID gaps = 0;
- both buy and sell sides;
- all 1440 UTC minute buckets present.

Only the stitched target timestamps enter synchronization metrics.

## 7. Bybit semantics unchanged

Use only:

`BTCUSDT2025-01-15.csv.gz`.

Require the v0.1 Bybit schema/order checks unchanged.

No neighboring Bybit date is authorized.

## 8. Synchronization rule unchanged

Exactly the D1 v0.1 frozen rule:

- 1-second UTC grid;
- boundaries 00:00:01 through 23:59:59 UTC;
- causal as-of = last event timestamp <= grid boundary;
- no future interpolation;
- staleness limit = 2.000 seconds.

## 9. Synchronization PASS gates unchanged

Require:

- OKX usable-grid share >=0.98;
- Bybit usable-grid share >=0.98;
- joint usable-grid share >=0.95;
- OKX p99 staleness <=1000 ms;
- Bybit p99 staleness <=1000 ms;
- OKX max adjacent target event-time gap <=5 seconds;
- Bybit max adjacent event-time gap <=5 seconds.

These thresholds are deliberately not changed after v0.1 output.

## 10. Golden tests unchanged

Require exact:

`C8_D1_SYNC_GOLDEN_PASS`

before body-derived metrics.

## 11. Exact terminal states

PASS:

`C8_D1_V02_HISTORICAL_CLOCK_INTEGRITY_PASS`

REVIEW:

`C8_D1_V02_HISTORICAL_CLOCK_INTEGRITY_REVIEW`

REVIEW remains an engineering/clock state, not a C8 strategy verdict.

## 12. Firewalls

Must remain false:

- cross_venue_price_compared;
- cross_venue_return_calculated;
- dislocation_calculated;
- lag_calculated;
- leader_selected;
- strategy_signal_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

Historical price fields may be parsed only within each venue for numeric schema validation.

## 13. Consequence of PASS/REVIEW

Only a PASS may authorize design of a cross-venue dislocation/headroom sentinel.

If v0.2 remains REVIEW after correct OKX stitching, do not loosen clock gates automatically. Diagnose whether the fixed 1s/as-of architecture itself is scientifically appropriate before any redesign.
