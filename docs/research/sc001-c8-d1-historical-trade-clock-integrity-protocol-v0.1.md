# SC001 — C8-D1 Historical Trade Body / Clock Integrity Protocol v0.1

Date: 2026-09-18
Status: **FROZEN ENGINEERING/CLOCK CALIBRATION BEFORE ANY CROSS-VENUE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c8-d0-v0.3-source-clock-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.10.json`;
- `docs/research/sc001-c8-d0-okx-bybit-source-clock-semantics-protocol-v0.3.md`.

## 1. Purpose

Open exactly one historical trade day on OKX and Bybit and determine whether the two event-time streams can be synchronized causally without inspecting any cross-venue price effect.

This stage is engineering/clock calibration only.

## 2. Exact bodies

Only:

- OKX `BTC-USDT-SWAP-trades-2025-01-15.zip`;
- Bybit `BTCUSDT2025-01-15.csv.gz`.

No neighboring date, alternate asset, alternate venue or outcome-selected body is authorized.

## 3. Source identity

### OKX

Re-query the frozen v0.3 `priapi` historical resolver and require the exact filename and current HEAD Content-Length to match the C8-D0 parent report.

Archive host must be trusted `static.okx.com`.

### Bybit

Use exact URL:

`https://public.bybit.com/trading/BTCUSDT/BTCUSDT2025-01-15.csv.gz`

Require current HEAD Content-Length to match the C8-D0 parent report.

Host must be exactly `public.bybit.com`.

## 4. Local integrity

For both files:

- exact byte size;
- SHA256;
- compressed-container integrity;
- no extraction to disk;
- streaming CSV parse.

## 5. OKX schema / clock semantics

Require exact CSV header:

`instrument_name,trade_id,side,price,size,created_time`

For all target rows:

- instrument = `BTC-USDT-SWAP`;
- trade_id integer and strictly increasing;
- side in `buy/sell`;
- price finite >0;
- size finite >0;
- created_time scale inferred by magnitude then normalized to Unix microseconds;
- normalized timestamp within 2025-01-15 UTC;
- normalized timestamps nondecreasing.

Timestamp-scale normalization:

- >=1e17: nanoseconds -> microseconds by integer division by 1000;
- >=1e14: microseconds;
- >=1e11: milliseconds -> multiply by 1000;
- >=1e9: seconds -> multiply by 1,000,000;
- otherwise REVIEW.

## 6. Bybit schema / clock semantics

Require first row to be a header whose first five semantic columns are:

- timestamp;
- symbol/instrument field;
- side;
- size;
- price.

Historical row parsing uses:

- timestamp = column 0, seconds with fractional precision -> Unix microseconds;
- side = column 2, `Buy/Sell`;
- size = column 3 >0;
- price = column 4 >0.

Require normalized timestamps inside 2025-01-15 UTC and nondecreasing.

## 7. Frozen synchronization rule

Before viewing any cross-venue price outcome, freeze:

- synchronization grid = exact UTC 1-second boundaries;
- grid points = `2025-01-15 00:00:01Z` through `23:59:59Z`;
- for each venue and grid point, select the last historical trade whose event timestamp is `<= grid_time`;
- no future interpolation;
- selected trade is usable only if staleness `<= 2.000 seconds`;
- otherwise venue is missing at that grid point.

No price is compared in D1.

## 8. Timestamp-only synchronization diagnostics

For each venue report:

- parsed row count;
- first/last normalized timestamp;
- same-timestamp adjacent count;
- nonmonotonic count;
- maximum adjacent event-time gap;
- fraction of 1-second grid points with a causal trade within 2 seconds;
- median and 99th percentile staleness in milliseconds.

Joint report:

- fraction of 1-second grid points where both venues are usable;
- count of jointly usable grid points.

D1 may use timestamps only for these diagnostics.

## 9. D1 PASS gates

Require:

- both body identities match D0;
- both compressed bodies validate;
- zero malformed target rows;
- zero out-of-day rows;
- zero timestamp reversals;
- OKX trade IDs strictly increasing;
- each venue 1-second usable-grid share >= 0.98;
- joint usable-grid share >= 0.95;
- each venue 99th-percentile staleness <= 1000 ms;
- each venue maximum adjacent event-time gap <= 5 seconds.

If any gate fails:

`C8_D1_HISTORICAL_CLOCK_INTEGRITY_REVIEW`

This is an engineering/clock state, not a C8 strategy rejection.

PASS:

`C8_D1_HISTORICAL_CLOCK_INTEGRITY_PASS`

## 10. Synthetic synchronization golden checks

Before body-derived diagnostics, require:

1. no future trade selected;
2. exact-boundary event is eligible;
3. 2.000s staleness is eligible;
4. >2.000s staleness is missing;
5. missing prior history remains missing;
6. selected timestamp is monotone across increasing grid boundaries.

Exact token:

`C8_D1_SYNC_GOLDEN_PASS`

## 11. Report firewalls

Must state:

- historical_trade_bodies_opened = true;
- historical_price_fields_parsed_for_schema = true;
- cross_venue_price_compared = false;
- cross_venue_return_calculated = false;
- dislocation_calculated = false;
- lag_calculated = false;
- leader_selected = false;
- strategy_signal_calculated = false;
- pnl_calculated = false;
- promotional_alpha_accessed = false.

## 12. Consequence of PASS

D1 PASS establishes only historical event-time compatibility and the frozen causal synchronization rule.

Only after D1 PASS may a separate C8 dislocation/headroom sentinel be designed and frozen.

That later sentinel must choose execution architecture and cost hurdle before any cross-venue price outcome is opened.
