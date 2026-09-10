# R009-X002 — Fixed Cross-Asset Breadth Panel Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** frozen before panel result inspection  
**Parent:** R009-X001 ETH unchanged-rule structural falsification  
**Research posture:** breadth falsification only; no winner selection; no parameter tuning

## 1. Objective

After BTC screened positively and ETH returned `UNCHANGED_RULE_MIXED`, test whether the exact frozen R009 v0.1 architecture has useful breadth across a small fixed panel of additional major crypto assets.

This is **not** independent confirmatory evidence because the decision to open this panel occurs after the ETH result was observed. Its purpose is narrower:

> measure how often the exact unchanged R009 architecture remains economically coherent across a fixed pre-existing asset set, and identify recurring structural failure modes without tuning.

## 2. Asset panel frozen before results

Use exactly five additional assets already present in the project's earlier R002 major-asset subset, excluding BTC and ETH:

- BNBUSDT
- LTCUSDT
- XRPUSDT
- ADAUSDT
- SOLUSDT

The panel may not be expanded, contracted, reordered for selection, or replaced after results are seen.

No DOGE, AVAX, LINK or other asset may be added to rescue the conclusion.

## 3. Data source

- Venue/reference: Binance Spot.
- Endpoint: `https://data-api.binance.vision/api/v3/klines`.
- Interval: `1d`.
- Fully closed UTC bars only.
- First-run UTC cutoff stored and reused after restart.
- Positive OHLC only.
- No interpolation.
- Earliest retained history initializes SMA and ATH state.

Per asset data gate:

- at least 1,000 clean daily observations;
- one-day-gap share >= 98%;
- maximum calendar gap <= 7 days;
- duplicate dates deduplicated before simulation and reported.

If any asset fails the data gate, panel status is `DATA_REDESIGN`; do not silently drop that asset.

## 4. Exact unchanged strategy

For every asset reuse R009 v0.1 without any asset-specific change.

### TREND10

- SMA lookback = 120 daily closes including day t;
- ON iff close_t > SMA120_t;
- ON target = 10%; OFF target = 0%;
- before 120 observations target = 0%;
- state at t applies to return t+1.

### CRISIS10

- reserve = 10% NAV;
- four tranches of 2.5 percentage points;
- triggers from running daily closing ATH: -20%, -35%, -50%, -65%;
- once a tranche activates, it remains active until a strictly new ATH;
- target range 0-10%.

### COMBINED

`R009_COMBINED = TREND10 + CRISIS10`

Allowed risky-asset target states:

`0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20%`.

No interaction override, leverage, funding, staking or lending.

## 5. Accounting and fees

Reuse the frozen self-financing daily-target accounting from R009 E001/X001.

Fee grid:

- 5 bps
- 10 bps baseline
- 25 bps
- 50 bps stress

Cash yield = 0%.

## 6. Comparators

Per asset calculate exactly:

- R009_COMBINED_DAILY
- TREND10_DAILY
- CRISIS10_DAILY
- PERMANENT10_PLUS_CRISIS10_REF
- STATIC10_DAILY
- STATIC15_DAILY
- STATIC20_DAILY
- STATIC10_MONTHLY
- STATIC15_MONTHLY
- STATIC20_MONTHLY

No alternative weights.

## 7. Evaluation slices

Per asset:

- `PRIMARY_FULL_YEARS`: from Jan 1 of first full calendar year after source start;
- `PRE_2020`: PRIMARY through 2019-12-31 only if at least 365 observations exist;
- `REPLAY_2020`: 2020-01-01 onward;
- `POST_2023`: 2023-01-01 onward.

State initialization always uses full available pre-slice history.

## 8. Per-asset decision gate

Use the same decision logic as ETH X001.

`SUPPORT` only if all applicable central checks pass, including:

- COMBINED CAGR > STATIC10 on PRIMARY and REPLAY_2020;
- COMBINED CAGR > TREND10 on PRIMARY and REPLAY_2020;
- if PRE_2020 eligible, COMBINED > STATIC10 and TREND10 there;
- no Pareto domination by STATIC15 daily/monthly on PRIMARY;
- COMBINED Max DD better than STATIC20 daily/monthly and permanent10+crisis reference;
- PRIMARY average risky weight < 15%;
- CRISIS10 ending multiple > 1 on PRIMARY;
- 50 bps primary comparisons remain coherent.

`FAIL` if any hard contradiction from ETH X001 occurs.

Otherwise `MIXED`.

## 9. Panel-level decision frozen before results

Let S/M/F be the number of SUPPORT/MIXED/FAIL assets among all five.

- `CROSS_ASSET_BREADTH_SUPPORT` if S >= 4 and F = 0.
- `CROSS_ASSET_BREADTH_REJECTED` if F >= 3.
- otherwise `CROSS_ASSET_BREADTH_MIXED`.

If any source gate fails: `DATA_REDESIGN`.

The panel decision does not choose a winning coin.

## 10. Interpretation discipline

This panel is useful only as a breadth/failure-mode diagnostic.

It must not be used to:

- pick the best-performing coin and call it a new strategy;
- tune SMA120, weights, crisis thresholds or reset logic;
- add another coin because the panel result is disappointing;
- claim statistical independence from BTC/ETH history;
- authorize demo/live trading.

A repeated pattern of crisis-sleeve persistence across assets would be evidence that sticky-to-new-ATH is a structural limitation of R009 outside BTC, not an invitation to optimize a new reset on the same history.

## 11. Output package

Exactly eight user-facing files:

1. `r009_x002_run_state.json`
2. `r009_x002_source_audit.csv`
3. `r009_x002_asset_decisions.csv`
4. `r009_x002_metrics.csv`
5. `r009_x002_state_diagnostics.csv`
6. `r009_x002_state_daily_long.csv`
7. `r009_x002_crisis_events.csv`
8. `r009_x002_summary.md`

Cache/snapshot/engine files are local only.
