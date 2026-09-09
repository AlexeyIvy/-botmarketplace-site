# R008-E003 — Symmetric Recovery Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R008 v0.2  
**Experiment:** E003 redesign/mechanism screen  
**Date:** 2026-09-09  
**Status:** frozen before first E003 result  
**Protocol:** `docs/research/r008-v0.2-symmetric-recovery-protocol-v0.1.md`

## 1. Scope

This document removes implementation ambiguity before E003 is run.

E003 changes only R008 release logic. All other architecture and accounting assumptions remain aligned with E002.

## 2. Data

Source endpoint family:

`https://api.blockchain.info/charts/market-price?timespan=all&format=json&sampled=false`

Cleaning:

1. parse UTC timestamps to calendar dates;
2. parse values as numeric USD reference prices;
3. remove non-positive/unparseable observations;
4. sort by date;
5. if duplicate dates occur, keep the last returned value and record duplicate count;
6. no interpolation;
7. state starts from earliest valid positive observation.

Data gate for observations from 2013-01-01 onward:

- one-day gap share >= 98%;
- maximum observed gap <= 7 calendar days;
- no silent fill.

If gate fails, no P&L decision.

## 3. Running peak and drawdown

For observation t:

`peak_t = max(price_0 ... price_t)`

`dd_t = price_t / peak_t - 1`

If `price_t` equals the existing peak, drawdown is zero. A new maximum also produces drawdown zero.

## 4. R008_V02 exact target mapping

Use the following exact inclusive boundaries:

```text
if dd_t <= -0.65: target = 0.20
elif dd_t <= -0.50: target = 0.175
elif dd_t <= -0.35: target = 0.15
elif dd_t <= -0.20: target = 0.125
else: target = 0.10
```

There is no state variable for previously triggered tranches in v0.2.

The same function is evaluated every day. Therefore adverse and recovery crossings are symmetric and repeated crossings are allowed.

## 5. R008_V01 comparator

Reconstruct v0.1 independently on the same price series:

- four boolean tranche states;
- each threshold can trigger once within an ATH-to-ATH episode;
- triggered tranches stay active until a new ATH;
- new ATH clears all tranche states;
- target = 10% + 2.5% times active tranche count.

This comparator is output-only. It does not change any v0.2 decision rule.

## 6. Timing

Target computed from fully observed price at t applies to return from t to t+1 via the existing shifted-target convention.

Implementation convention:

- daily asset return at t = `price_t / price_(t-1) - 1`;
- held portfolio weight at t = target from t-1;
- turnover charged at t = absolute target change decided at t-1;
- first day's held weight and turnover are zero for return accounting;
- initial establishment of benchmark target is charged through the same existing simulator convention used in E001/E002.

No same-observation fill.

## 7. Fees

Fee grid per absolute target-weight change:

- 0.0005;
- 0.0010;
- 0.0025;
- 0.0050.

Baseline = 0.0010.

No funding, cash yield, borrow or leverage.

## 8. Benchmarks

Target series:

- CASH = 0.00;
- STATIC10 = 0.10;
- STATIC15 = 0.15;
- STATIC20 = 0.20;
- BTC100 = 1.00.

## 9. Evaluation slices

- FULL_AVAILABLE: first valid observation through endpoint;
- PRIMARY_LONG: >= 2013-01-01;
- PRE_2020_NEW: 2013-01-01 through 2019-12-31;
- REPLAY_2020: >= 2020-01-01;
- POST_2023: >= 2023-01-01.

Metrics must be recomputed from slice-local compounded returns rather than slicing a pre-normalized equity multiple.

## 10. Crisis-event definition

Event detector is independent from v0.2 target transitions.

An event:

- begins when drawdown first reaches <= -20% after the most recent ATH;
- remains the same event until a later new ATH;
- ends at that new ATH;
- remains OPEN_CENSORED if no later ATH exists by dataset end.

Record first breach dates for -20/-35/-50/-65, maximum drawdown and date, and event status.

Event-return window begins on the first executable day after the first -20% breach and ends on the executable day after ATH reset when available, matching E002 convention. If no later executable reset day exists, use dataset end.

## 11. Transition diagnostics

A target transition is any day where today's target differs from yesterday's target.

For v0.2 classify:

- `UP` when target increases;
- `DOWN` when target decreases.

A multi-level one-day move counts as one target transition for transition count, but absolute turnover uses the full weight change.

Additionally count threshold-unit moves as `abs(delta_target)/0.025`; this reports how many 2.5-point tranche units moved even if multiple levels were crossed in one day.

## 12. 20% spell definition

A 20%-exposure spell is a maximal consecutive sequence of observations where target equals 0.20.

Report:

- number of spells;
- mean length in observations/days;
- median length;
- maximum length;
- start/end dates.

For every crisis event that reaches 20%, measure from first target=20% date to first later date in the same event where target becomes <=17.5%, <=15%, <=12.5%, and <=10%, if observed.

## 13. Metrics

Use the same common formulas as E002 for CAGR, volatility, drawdown, Calmar, worst periods, exposure, turnover and fee drag.

Calmar = CAGR / absolute Max DD when Max DD < 0.

## 14. Concentration diagnostic

For closed crisis events calculate positive Benefit10 amounts.

Largest-event positive-benefit share = largest positive closed-event Benefit10 divided by sum of all positive closed-event Benefit10.

If there are no positive closed-event Benefit10 values, return NaN and fail the relevant decision condition.

## 15. Outputs

Frozen output set:

1. `r008_e003_data_audit.json`
2. `r008_e003_price_clean.csv`
3. `r008_e003_metrics.csv`
4. `r008_e003_yearly_returns.csv`
5. `r008_e003_state_daily.csv`
6. `r008_e003_transitions.csv`
7. `r008_e003_exposure_spells_20.csv`
8. `r008_e003_crisis_events_raw.csv`
9. `r008_e003_crisis_event_diagnostics.csv`
10. `r008_e003_severity_summary.csv`
11. `r008_e003_baseline_daily.csv`
12. `r008_e003_summary.md`
13. `r008_e003_run_state.json`

The engine must not auto-promote the candidate. Formal PROMISING/REDESIGN/FAIL is assigned only after output review against the frozen protocol.