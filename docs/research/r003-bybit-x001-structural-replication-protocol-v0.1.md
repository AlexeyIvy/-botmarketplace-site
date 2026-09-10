# R003-X001 — Bybit Funding-Premium Structural Replication Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R003 — Funding / Basis Carry  
**Experiment:** X001 — first independent-venue structural replication  
**Venue:** Bybit  
**Symbol:** BTCUSDT linear perpetual  
**Date:** 2026-09-10  
**Status:** frozen before result inspection  
**Parent evidence:** Binance R003-E001 / E002  
**Precommit:** `docs/research/r003-cross-venue-replication-precommit-v0.1.md`

## 1. Objective

Test whether the historical short-perpetual funding premium observed on Binance is also structurally present on the **precommitted first independent venue, Bybit**, without selecting a venue after seeing results.

X001 is a structural premium audit only. It cannot become a strategy PASS and does not test executable long-spot/short-perpetual NAV. Basis P&L, execution costs, exact venue margin/liquidation mechanics and two-leg implementation belong to X002 if X001 survives.

## 2. Frozen venue and instrument

- Venue: **Bybit**.
- Product: `linear` BTCUSDT perpetual.
- Public API base: `https://api.bybit.com`.
- Instrument metadata endpoint: `GET /v5/market/instruments-info?category=linear&symbol=BTCUSDT`.
- Funding endpoint: `GET /v5/market/funding/history?category=linear&symbol=BTCUSDT`.
- Stress-price reference: Bybit BTCUSDT **index-price daily kline**, `GET /v5/market/index-price-kline?category=linear&symbol=BTCUSDT&interval=D`.

The current official instrument documentation reports BTCUSDT linear launch timestamp `1585526400000` and funding interval `480` minutes. The engine must still fetch and record live instrument metadata rather than hard-code those fields as evidence.

## 3. Why index price is the stress reference

The Binance E001 stress classifier used spot BTC. For Bybit X001, use the venue-native BTCUSDT index-price series instead of Bybit spot because the linear perpetual launched before Bybit spot history is necessarily guaranteed to cover the full derivatives sample.

This is an explicitly frozen cross-venue implementation difference. It affects only the descriptive crisis-state classifier, not the funding-premium arithmetic.

## 4. Fixed first-run snapshot

The Android runner must create one immutable first-run `cutoff_ms` in a local `snapshot.json`.

If Android/Pydroid stops, subsequent runs resume the same historical snapshot and may not move the endpoint forward.

This avoids changing the sample because of an interrupted download.

## 5. Funding collection

Bybit funding history is requested backward in time using `endTime` and `limit=200`.

Rules:

- begin at the frozen first-run cutoff;
- request pages backward;
- after a page, set the next `endTime` to one millisecond before the oldest timestamp in the page;
- stop when pages are empty or the returned history predates the instrument launch boundary;
- retain observations from instrument launch through cutoff;
- sort ascending after collection;
- remove exact duplicate funding timestamps, keeping the last identical timestamp observation;
- no interpolation and no fabricated funding events.

For a short perpetual, normalized funding carry is defined as:

`short_funding_return = +fundingRate`

This matches the Binance R003-E001 sign convention.

## 6. Funding cadence audit

Record:

- current instrument `fundingInterval` metadata;
- all observed event-to-event gaps;
- median funding gap;
- fraction of gaps within ±5 minutes of the current documented interval;
- maximum gap.

Cadence is a data-quality diagnostic, not an assumption that historical exchange rules could never have changed.

## 7. Full-year rule

Bybit BTCUSDT linear launched during 2020, so calendar 2020 is a partial venue year.

Define the **first full calendar year algorithmically** as the first January 1 strictly after the later of:

- fetched instrument launch timestamp; and
- earliest retained funding timestamp,

unless the retained series begins exactly at January 1 00:00 UTC, in which case that year may qualify.

Expected first full year under current metadata is 2021, but the engine records the value from data/metadata rather than silently assuming it.

Partial launch year and current incomplete year are descriptive only and do not count in completed-year gates.

## 8. Frozen slices

Report:

1. `FULL_AVAILABLE` — all retained Bybit funding data from actual first observation.
2. `PRIMARY_FULL_YEARS` — from the first full calendar year onward.
3. `PRE_2023` — from first full calendar year through 2022-12-31, if non-empty.
4. `POST_2023` — 2023-01-01 onward.

Also report each calendar year separately.

## 9. Funding metrics

For each slice report at minimum:

- observation count;
- simple funding sum;
- descriptive compounded funding product;
- mean and median funding event;
- positive/negative/zero fractions;
- best/worst event;
- longest negative-event streak;
- worst rolling 7d / 30d / 90d daily funding sums;
- median rolling 365d sum;
- share of qualifying rolling 365d windows above zero;
- worst/best rolling 365d sum.

The compounded number is descriptive only and is not executable strategy NAV.

## 10. Structural-signal gate

`STRUCTURAL_SIGNAL_PRESENT` only if all of the following prospectively frozen conditions pass:

1. `FULL_AVAILABLE` simple funding sum > 0;
2. `PRIMARY_FULL_YEARS` simple funding sum > 0;
3. `PRE_2023` simple funding sum > 0 when that slice exists;
4. `POST_2023` simple funding sum > 0;
5. strict majority of completed full calendar years have positive simple funding sum;
6. `FULL_AVAILABLE` median rolling 365d sum > 0;
7. more than 50% of qualifying rolling 365d windows are positive;
8. no single positive completed full year contributes >=50% of the sum of positive completed-year funding.

Classification:

- all pass -> `STRUCTURAL_SIGNAL_PRESENT`;
- full available sum <=0 -> `STRUCTURAL_SIGNAL_ABSENT`;
- otherwise -> `STRUCTURAL_SIGNAL_MIXED`.

No threshold, funding filter, trend filter, leverage, venue switch or parameter search is allowed after inspection.

## 11. Crisis-state classifier

Create causal daily drawdown state from Bybit BTCUSDT index-price closes:

`drawdown_t = close_t / running_ATH_t - 1`

Attach each funding event to the latest fully closed daily index-price bar at or before the funding timestamp.

Frozen buckets:

- `DD_0_TO_10`
- `DD_10_TO_20`
- `DD_20_TO_35`
- `DD_35_TO_50`
- `DD_50_PLUS`
- `NO_INDEX_STATE`

Deep stress = `DD_35_TO_50` + `DD_50_PLUS`.

`CRISIS_FINANCING_COMPATIBLE` only if both:

- observation-weighted mean deep-stress funding rate >=0; and
- median of the two available deep-stress bucket medians >=0.

This is an average historical compatibility classification, **not** a claim that funding will remain positive during every future crash.

## 12. Data gate

Before interpreting the structural result require:

- instrument metadata returns BTCUSDT linear perpetual with positive launch timestamp;
- >=1,000 unique retained funding observations;
- timestamps strictly increasing after deduplication;
- latest funding observation no more than 24 hours before the frozen cutoff;
- daily index-price series starts no later than the first retained funding date + 2 calendar days, or else crisis-state classification is marked insufficient without fabricating history;
- daily index-price coverage over its retained span >=99.0%;
- no index-price gap >3 calendar days;
- all retained index closes are positive.

Funding cadence irregularity is reported but does not automatically fail the structural premium audit unless it indicates pagination/data corruption.

If the data gate fails, return `DATA_REDESIGN` and do not interpret strategy economics.

## 13. Required output package

Keep the user-facing result package <=10 files:

1. `r003_x001_bybit_run_state.json`
2. `r003_x001_bybit_source_audit.json`
3. `r003_x001_bybit_funding_clean.csv`
4. `r003_x001_bybit_index_daily.csv`
5. `r003_x001_bybit_metrics.csv`
6. `r003_x001_bybit_yearly.csv`
7. `r003_x001_bybit_drawdown_buckets.csv`
8. `r003_x001_bybit_summary.md`

Local cache/snapshot/engine files do not need to be uploaded.

## 14. Decision path

### If `STRUCTURAL_SIGNAL_PRESENT`

Advance to a separately frozen **Bybit R003-X002 self-financing cash-and-carry implementation replication**. X002 must use Bybit-specific price, mark, funding, margin, fee, granularity and execution assumptions; it may not copy Binance mechanics blindly.

### If `STRUCTURAL_SIGNAL_MIXED`

Do not rescue with a funding threshold or cherry-picked subperiod. Document the failure modes and decide whether the cross-venue hypothesis remains worth forward observation.

### If `STRUCTURAL_SIGNAL_ABSENT`

Treat this as evidence that the Binance carry result may be venue/regime-specific. Do not choose a different venue because it looks better.

## 15. Research integrity

This protocol is frozen before X001 result inspection.

The purpose is falsification of venue portability, not generation of another attractive backtest.
