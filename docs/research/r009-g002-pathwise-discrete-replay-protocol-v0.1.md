# R009-G002 — Pathwise Discrete Replay Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Candidate:** R009 BTC v0.1  
**Status:** frozen before G002 result inspection  
**Purpose:** implementation-feasibility / tracking-fidelity research only; not a new strategy-performance validation

## 1. Objective

Measure how the exact frozen R009 BTC target path is altered when a finite-size account must obey the frozen G001 Binance Spot BTCUSDT quantity step, minimum quantity and minimum notional rules.

Primary question:

> How much implementation distortion, skipped trading and residual dust arise across fixed account-size tiers when the already-frozen R009 target path is executed with discrete BTC quantities and real minimum-order constraints?

G002 may not change any R009 signal or portfolio rule.

## 2. Relationship to G001

G001 established the static current-rule envelope. G002 adds the missing time dimension.

G002 uses the exact G001 rule snapshot frozen on 2026-09-10 rather than refetching future exchange filters:

- BTC quantity step = **0.00001000 BTC**;
- effective minimum quantity = **0.00001000 BTC**;
- effective minimum market notional = **5.00 USDT**.

This is intentionally a counterfactual implementation stress using one fixed current-rule regime across the replay. It is not a reconstruction of historical Binance filter changes.

## 3. Frozen R009 target mechanics

Unchanged from R009 v0.1:

- SMA120 on fully closed daily BTCUSDT bars;
- TREND10 = 10% BTC when close > SMA120, otherwise 0%;
- CRISIS10 = four 2.5pp tranches triggered at closing-ATH drawdowns -20/-35/-50/-65%;
- crisis tranches remain sticky until a new closing ATH;
- combined target = TREND10 + CRISIS10;
- target range = 0-20%;
- state at daily close `t` is the desired target for the next daily interval.

No thresholds, weights, reset rules, indicators or rebalance cadence may change.

## 4. Replay market data

Use Binance Spot BTCUSDT daily klines from the same public market-data endpoint family used by R009-E002:

- base: `https://data-api.binance.vision`;
- endpoint: `/api/v3/klines`;
- interval: `1d`;
- only fully closed UTC daily bars.

Warmup/history begins from available Binance BTCUSDT data in 2017. Primary implementation replay begins **2018-01-01** after state warmup.

The historical path is already research-contaminated for strategy efficacy. G002 results therefore cannot be used as independent evidence that R009 is profitable or antifragile.

## 5. Frozen account-size tiers

Replay exactly these initial account sizes:

- **200 USD** — below the step-aware G001 executable threshold, negative-control tier;
- **250 USD** — first frozen G001 grid point with all target states/transitions statically feasible;
- **500 USD**;
- **1,000 USD**;
- **5,000 USD**;
- **10,000 USD**.

Do not add/remove tiers after seeing results.

## 6. Frozen fee tracks

Same R009 research cost tracks, charged on actual executed BTC notional:

- 5 bps;
- **10 bps baseline**;
- 25 bps;
- 50 bps.

No fee-tier optimization.

## 7. Discrete execution algorithm

At the first primary replay close:

1. start with the tier's full NAV in cash;
2. compute desired BTC notional = frozen R009 target × current pre-trade NAV;
3. convert to BTC and round quantity **down** to 0.00001 BTC;
4. compute trade from current BTC quantity to desired rounded quantity;
5. execute only if absolute trade quantity >=0.00001 BTC and absolute trade notional >=5 USDT;
6. if executable, change BTC quantity and deduct fee from cash;
7. otherwise skip the order and keep the prior BTC quantity.

For each later daily close:

1. mark the existing BTC quantity at the new close;
2. compute pre-trade NAV = cash + BTC quantity × close;
3. compute the exact frozen R009 desired target from that fully closed bar;
4. derive desired rounded BTC quantity from target × pre-trade NAV, rounded down by the frozen step;
5. calculate delta quantity from current holding;
6. execute the delta only if both frozen minQty and minNotional are satisfied;
7. otherwise skip and carry the prior position forward;
8. deduct execution fee from cash on executed notional only.

If target is 0% but the residual BTC position is below executable minimum, the residual remains as **dust** until a later executable transition. Do not silently zero it.

No accumulation buffer, deferred-order batching rule, minimum-rebalance threshold, tolerance band or alternate order type may be added.

## 8. Continuous reference

For each fee track, run the frozen frictionless/self-financing continuous-target R009 accounting on the exact same primary dates as a reference.

The continuous reference is not a benchmark-selection exercise. It exists only to measure discrete implementation distortion.

## 9. Required diagnostics

For every account tier and fee track report at minimum:

- ending multiple, discrete and continuous;
- ending-multiple difference;
- Max Drawdown, discrete and continuous;
- average absolute target-weight error in percentage points;
- 95th-percentile and maximum absolute target-weight error;
- number of desired trade attempts;
- executed orders;
- skipped orders;
- skipped-order share;
- sum of skipped desired notional;
- actual turnover;
- execution fee drag;
- number of days with nonzero BTC while desired target = 0% (`dust/exit-blocked days`);
- maximum residual weight on such days;
- negative-cash occurrence, which is a hard implementation error if observed.

Also retain the complete baseline-10bps daily audit path for all six capital tiers.

## 10. Required outputs

Keep the result package <=10 files:

1. `r009_g002_run_state.json`
2. `r009_g002_source_audit.json`
3. `r009_g002_metrics.csv`
4. `r009_g002_daily_baseline_10bps.csv`
5. `r009_g002_summary.md`

## 11. Decision semantics

Maximum status:

> **DISCRETE_IMPLEMENTATION_ENVELOPE_ESTABLISHED**

If source/state/accounting reconciliation fails:

> **DATA_OR_ACCOUNTING_REDESIGN**

G002 does not produce a strategy PASS/FAIL and does not select a deposit size by optimizing historical P&L.

The purpose is to identify whether the static 250 USD G001 floor remains credible through time, and how fidelity improves mechanically as capital increases.

## 12. Anti-overfitting / anti-rescue freeze

During G002 do not change:

- R009 SMA120;
- trend/crisis sleeve sizes;
- drawdown thresholds;
- sticky reset rule;
- account tiers;
- fee tracks;
- current-rule step/minQty/minNotional snapshot;
- round-down convention;
- daily target timing;
- skipped-order rule;
- residual-dust handling.

Any alternative implementation policy (e.g. accumulate deltas until executable, tolerance bands, weekly rebalance, fractional/synthetic execution, another venue) is a separate future implementation candidate and may not overwrite G002.
