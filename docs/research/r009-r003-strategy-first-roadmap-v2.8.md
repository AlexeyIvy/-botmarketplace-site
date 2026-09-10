# BotMarketplace Strategy-First Research Roadmap v2.8

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009/R003 forward records active; R009 G001/G002 implementation-granularity branch complete; next priority is prospective R010 shadow-forward design; broad platform development remains frozen

## 1. Active forward records

### R009-E002 — BTC forward

- technically accepted initialization;
- fixed inception remains 2026-09-10 00:00 UTC;
- exact frozen R009 v0.1 rules unchanged;
- only fully closed future daily bars accumulate evidence.

### R003-E003 — Binance canonical forward

- fixed decision boundary remains 2026-09-10 12:00 UTC;
- first establishment snapshot technically accepted;
- funding-timestamp causality hotfix was frozen before any funding event entered the record;
- temporary Binance HTTP 418/source-access failure does not authorize reset or venue substitution;
- continue from original inception when access permits.

### R003-X003 — Bybit parallel venue forward

- fixed boundary 2026-09-10 16:00 UTC;
- initial establishment and first forward hour technically accepted;
- source coverage, equal-BTC hedge, margin proxy and causal funding eligibility passed initialization audit;
- remains separate from Binance E003 and earlier Bybit X001.

## 2. R009-G001 result

Status: **MECHANICAL_ENVELOPE_ESTABLISHED**.

Current-rule Binance BTCUSDT snapshot:

- step 0.00001 BTC;
- minQty 0.00001 BTC;
- minNotional 5 USDT;
- step-aware 2.5pp executable threshold about 219.26 USD;
- first frozen tested grid tier with all target states/transitions statically feasible: 250 USD.

250 USD was explicitly classified as a static mechanical floor only.

## 3. R009-G002 result

Status: **DISCRETE_IMPLEMENTATION_ENVELOPE_ESTABLISHED**.

Result/audit:

`docs/research/r009-g002-results-and-technical-audit-v0.1.md`

Result commit:

`c21861f1459541e5d08f78c6d582ffc4ac4d41d5`

Primary replay: 2018-01-01 through 2026-09-09, 3,174 observations, frozen current Binance execution rules, capital tiers 200/250/500/1,000/5,000/10,000 USD, cost tracks 5/10/25/50 bps.

Key implementation findings at baseline 10 bps:

- $250: mechanically survives, no negative cash or trapped exit dust, but coarse daily fidelity; avg target error 0.448 pp, P95 1.227 pp, max 2.153 pp;
- $500: avg 0.238 pp, P95 0.658 pp;
- $1,000: avg 0.114 pp, P95 0.327 pp, max 0.542 pp;
- $5,000: avg 0.012 pp, P95 0.057 pp;
- $10,000: avg 0.004 pp, P95 0.023 pp.

Independent audit found all 105 observed baseline target-change order attempts executed for every tested capital tier; the high raw skipped-order share at small capital is dominated by tiny daily drift corrections rather than missed signal-state changes.

Do not select any capital tier by historical ending return. Positive discrete-vs-continuous ending differences at small tiers are path-dependent implementation noise, not evidence of a better strategy.

Interpretation:

- $250 remains a mechanical/coarse-fidelity floor, not a practical minimum recommendation;
- $1,000 is a reasonable small-account demo-engineering candidate tier on descriptive tracking-error grounds, not a universal optimized minimum;
- $5,000+ is near-continuous with respect to current quantity/min-notional granularity.

## 4. G003 decision

A dedicated G003 liquidity/capacity/order-book study is **deferred, not cancelled**.

Reason:

- current research priority is identifying strategy robustness and forward behavior, not large-AUM deployment;
- G001/G002 already answer the immediate small-account quantity/min-notional question;
- G003 becomes mandatory before material real-capital scaling or multi-user fanout, where slippage, depth and venue concentration matter.

Do not infer that G003 is unnecessary for production.

## 5. Next priority — R010 prospective shadow-forward

The already documented hypothesis is:

`docs/research/r010-drawdown-armed-recovery-hypothesis-v0.1.md`

Core idea:

> drawdown arms recovery capital; recovery confirmation permits deployment.

R010 must remain a distinct new candidate and may not alter R009-E002.

Next step is to freeze exactly one low-degree-of-freedom state machine using only already-inspected primitives where possible:

- SMA120 trend state;
- existing -20/-35/-50/-65 drawdown arming thresholds;
- four 2.5pp tranches;
- maximum 10% recovery sleeve;
- 10% trend sleeve;
- no leverage;
- no parameter grid;
- exact prospective reset semantics frozen before any R010 forward result.

Old BTC/ETH/BNB/LTC/XRP/ADA/SOL histories remain contaminated for confirmation. Any old-data use is diagnostic only. Actual new evidence must come from a post-freeze shadow-forward record.

## 6. Immediate execution order

1. Freeze R010 v0.1 exact state-machine/reset semantics before seeing any prospective result.
2. Implement and initialize R010 shadow-forward from a post-freeze boundary; do not replace or pause R009-E002.
3. Continue R009-E002 unchanged.
4. Continue Bybit R003-X003 unchanged.
5. Retry Binance R003-E003 only after source access permits, preserving original inception.
6. Defer G003 until demo/real-capital sizing requires liquidity/capacity evidence.
7. Open Safe-Sleeve S002 before any real-capital promotion.
8. Broad BotMarketplace platform feature development remains frozen until strategy/implementation gates justify it.

## 7. Explicit prohibitions

Do not:

- call $250 a practical minimum deposit;
- select $200/$250/$500/$1,000 by whichever had the best historical ending multiple;
- retune R009 after G002;
- add batching/tolerance-band rules into G002 retrospectively;
- merge Binance and Bybit R003 histories;
- move any fixed forward inception;
- backfit R010 reset semantics on the already inspected seven-asset history;
- treat R010 as proven antifragility even if forward behavior is favorable;
- restart broad platform development yet.
