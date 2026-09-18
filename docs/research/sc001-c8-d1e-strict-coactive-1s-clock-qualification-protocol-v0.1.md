# SC001 — C8-D1E Strict Coactive 1s Clock Qualification Protocol v0.1

Date: 2026-09-18
Status: **FROZEN TIMESTAMP-ONLY ENGINEERING STAGE / NO CROSS-VENUE PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c8-d1-v0.2-clock-architecture-review-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.11.json`;
- `docs/research/sc001-c8-d1-historical-trade-clock-integrity-protocol-v0.2.md`.

## 1. Purpose

Qualify a strict same-second coactivity representation for C8 without carrying transaction prices through inactive seconds.

No cross-venue price is compared.

## 2. Source bodies

Reuse only the already authorized engineering bodies:

- OKX `BTC-USDT-SWAP-trades-2025-01-15.zip`;
- OKX `BTC-USDT-SWAP-trades-2025-01-16.zip`;
- Bybit `BTCUSDT2025-01-15.csv.gz`.

OKX target UTC day remains reconstructed as:

`D + D+1 -> retain UTC [D,D+1)`.

## 3. Strict coactive representation

For each target trade timestamp:

`second_id = floor(timestamp_us / 1_000_000)`.

A venue-active second is a target UTC second containing at least one trade on that venue.

A synchronized second exists only when both venues are active in the same `second_id`.

No carry-forward.

No last observation from a previous second.

No future interpolation.

No price comparison.

## 4. Timestamp-only diagnostics

Report:

- OKX active seconds;
- Bybit active seconds;
- joint coactive seconds;
- joint coactive share of 86,400 UTC seconds;
- joint-active seconds per UTC hour;
- number of UTC hours with any joint coactivity;
- minimum joint-active seconds in any UTC hour;
- for each joint second, timestamp of the last OKX trade in that second and last Bybit trade in that second;
- absolute last-event timestamp skew distribution;
- median and p99 skew in milliseconds.

No price values enter these metrics.

## 5. PASS gates

Require all:

- source/body integrity from D1 v0.2 reconstruction passes on re-parse;
- OKX all 1440 UTC minute buckets present;
- both venues have active seconds in all 24 UTC hours;
- joint coactive seconds >= `50,000`;
- joint coactive hours = `24`;
- minimum joint-active seconds in any UTC hour >= `600`;
- p99 absolute last-event timestamp skew within a coactive second <= `1000 ms`.

These are engineering sample/clock gates, not economic gates.

## 6. Exact terminal states

PASS:

`C8_D1E_STRICT_COACTIVE_1S_PASS`

REVIEW:

`C8_D1E_STRICT_COACTIVE_1S_REVIEW`

REVIEW is still not a C8 strategy verdict.

## 7. Firewalls

Must remain false:

- cross_venue_price_compared;
- cross_venue_return_calculated;
- dislocation_calculated;
- lag_calculated;
- leader_selected;
- strategy_signal_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

Historical price fields may be parsed only for per-venue schema validation inherited from D1.

## 8. Consequence of PASS

If D1E passes, C8 may use strict coactive 1-second buckets as the frozen temporal representation for a later **separate** nonpromotional price/headroom sentinel.

That later sentinel must:

1. use a newly declared Selection/Calibration period;
2. freeze the within-second price statistic before outcome;
3. freeze execution architecture and cost hurdle before outcome;
4. preserve 2025-01-15 as engineering-only evidence.

No price outcome is authorized by D1E.
