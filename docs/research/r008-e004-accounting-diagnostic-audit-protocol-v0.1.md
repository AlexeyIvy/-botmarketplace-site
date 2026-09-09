# R008-E004 — Accounting & Event-Diagnostic Audit Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R008 — Antifragile Crisis-Opportunity Barbell  
**Experiment:** E004  
**Date:** 2026-09-09  
**Status:** pre-result frozen diagnostic specification  
**Parent reviews:** `r008-e002-results-v0.1.md`, `r008-e003-results-v0.1.md`, `r008-technical-financial-review-correction-v0.1.md`

## 1. Objective

E004 is not a new strategy version and cannot promote R008 to historical PASS.

It audits two methodological questions discovered after E003:

1. whether the abstract target-weight accounting materially favors constant-weight STATIC benchmarks because natural weight drift and maintenance turnover are omitted;
2. whether ATH-to-recovery crisis windows mechanically overstate Benefit10.

No R008 thresholds, tranche sizes, base weights, or release rules change.

## 2. Frozen strategy targets

Reconstruct on the same Blockchain.com daily reference-price history:

### R008_V01
- 10% BTC base;
- four 2.5pp crisis tranches at -20/-35/-50/-65%;
- sticky until new ATH.

### R008_V02
- 10% BTC base;
- same four 2.5pp levels;
- current-drawdown symmetric mapping;
- no hysteresis/cooldown.

### Static targets
- STATIC10;
- STATIC15;
- STATIC20.

No other portfolio weights are allowed.

## 3. Data

Use the exact same source family as E002/E003:

`https://api.blockchain.info/charts/market-price?timespan=all&format=json&sampled=false`

Repeat the existing daily data gate and record raw/clean SHA256.

This is a methodology audit on already inspected history, not new OOS evidence.

## 4. Accounting models

Run all strategy targets under the following pre-specified accounting variants.

### A — LEGACY_TARGET_WEIGHT

Reproduce the E002/E003 abstraction exactly for reconciliation:

- prior target weight × next daily BTC return;
- cost only on change in target weight.

### B — SELF_FINANCING_DAILY_TARGET

Model BTC and cash as a self-financing portfolio.

At each daily close:

1. the BTC sleeve first drifts naturally with the realized BTC return;
2. compute the pre-trade BTC portfolio weight;
3. rebalance to that day's desired target weight;
4. transaction cost is charged on actual traded portfolio notional needed to move from the drifted pre-trade weight to the desired target;
5. the resulting target is the starting allocation for the next daily return.

This model therefore charges maintenance turnover even when a constant target such as STATIC15 does not numerically change.

Baseline fee = 10 bps; stress = 5/10/25/50 bps.

### C — TRANSITION_ONLY

For R008_V01 and R008_V02 only:

- allow BTC weight to drift naturally while the desired target state is unchanged;
- rebalance to the new target only when the desired target level changes;
- initial allocation is established at the first observation.

This tests a minimal-trading interpretation of the state machine without inventing a rebalance band.

No TRANSITION_ONLY result is interpreted as an equivalent constant-weight STATIC benchmark.

## 5. Static practical benchmarks

Because a constant target needs an explicit maintenance policy, add two practical implementations without optimization:

### STATICxx_DAILY
Self-financing daily rebalance to 10%, 15%, or 20%, with full natural-drift turnover charged.

### STATICxx_MONTHLY
Self-financing calendar-month-end rebalance to 10%, 15%, or 20%; otherwise natural drift.

Month-end is a deterministic operational convention, not selected from a grid.

No weekly/quarterly/annual frequency search is allowed in E004.

## 6. Evaluation slices

Retain:

- PRIMARY_LONG: 2013-01-01 onward;
- PRE_2020_NEW: 2013-01-01 through 2019-12-31 (name retained only for continuity, not independent evidence);
- REPLAY_2020: 2020-01-01 onward;
- POST_2023: 2023-01-01 onward.

## 7. Portfolio metrics

For every accounting variant / strategy / cost / slice report:

- CAGR;
- ending multiple;
- annualized volatility;
- Max DD;
- Calmar;
- worst year/quarter/month;
- worst rolling 12m;
- longest drawdown;
- average realized BTC weight;
- max realized BTC weight;
- total traded notional / turnover;
- fee drag.

Also report daily 1% and 5% VaR/CVaR as diagnostics.

## 8. Fixed-horizon shock diagnostics

Do not use the next ATH as the primary benefit endpoint.

For each mechanically detected first breach of each level -20/-35/-50/-65 within an ATH-defined episode:

- record breach date;
- deepest event level for context;
- calculate portfolio return beginning with the next allowed daily interval over fixed horizons:
  - 7 days;
  - 30 days;
  - 90 days;
  - 180 days;
  - 365 days;
- include every breach with enough future data for the requested horizon;
- do not require eventual ATH recovery;
- open/censored episodes are included whenever the fixed horizon is observable.

For R008_V01 and R008_V02 report benefit versus:

- STATIC10_DAILY;
- STATIC15_DAILY;
- STATIC20_DAILY;
- STATIC15_MONTHLY as an additional practical comparator.

Summarize mean, median, positive fraction and count by trigger level and horizon.

These diagnostics are descriptive because observations overlap and are not independent.

## 9. Interpretation gates

E004 does not return PASS/FAIL for the strategy. It returns one of:

### ACCOUNTING_CONCLUSION_STABLE
The static-benchmark conclusion remains materially unchanged under self-financing daily/monthly accounting, and fixed-horizon evidence does not reveal a robust exposure-controlled crisis timing benefit.

Action: close R008 crisis-only ladder development on this history and proceed to R009 / another economically distinct antifragility branch.

### ACCOUNTING_CONCLUSION_CHANGED
Realistic accounting materially removes the prior STATIC15 domination and/or fixed-horizon deep-shock benefit remains coherent against STATIC15/20 rather than only STATIC10.

Action: preserve the relevant frozen R008 version as a candidate for forward/new-independent testing. Do not tune thresholds or exits on the same history.

### MIXED
Accounting and fixed-horizon diagnostics point in different directions.

Action: no promotion; document uncertainty and decide between forward observation and closing the branch. No new historical parameter search.

## 10. Anti-overfitting freeze

E004 may not change:

- 10% base;
- 10% reserve;
- 2.5% x4 tranches;
- -20/-35/-50/-65 levels;
- v0.1 ATH-sticky release;
- v0.2 symmetric release;
- fee grid;
- evaluation slices;
- fixed horizons;
- monthly benchmark frequency.

No SMA/trend overlay is tested inside E004. R009 remains deferred until this audit is complete.
