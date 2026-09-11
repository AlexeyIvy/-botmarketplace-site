# BotMarketplace Strategy-First Research Roadmap v3.0

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** R009/R003/R010 forward records active; R009 G001/G002 complete; next priority is safe-sleeve/access architecture before any real-capital promotion; broad platform development remains frozen

## 1. Active prospective records

### R009-E002 — BTC forward

- initialization technically accepted;
- fixed inception remains 2026-09-10 00:00 UTC;
- exact frozen R009 v0.1 rules unchanged;
- only fully closed future daily bars accumulate evidence.

### R003-E003 — Binance canonical carry forward

- fixed decision boundary remains 2026-09-10 12:00 UTC;
- first establishment snapshot technically accepted;
- funding-timestamp causality hotfix was frozen before any funding event entered the record;
- temporary Binance HTTP 418/source-access failure does not authorize reset or venue substitution;
- resume from original inception when source access permits.

### R003-X003 — Bybit parallel venue forward

- fixed boundary 2026-09-10 16:00 UTC;
- initial establishment and first forward hour technically accepted;
- source coverage, equal-BTC hedge, margin proxy and causal funding eligibility passed initialization audit;
- remains separate from Binance E003 and earlier Bybit X001.

### R010-E001 — BTC prospective shadow-forward

- initialization technically accepted;
- fixed inception remains **2026-09-11 00:00 UTC**;
- 2026-09-10 closed bar is the frozen signal bar;
- realized forward days at initialization = 0;
- signal trend ON, 3 inherited armed tranches, recovery target 7.5%, R010 total target 17.5%;
- inherited pre-inception arming is warmup only and is not prospective mechanism validation;
- mechanism-event gate currently not ready because no post-freeze arming/activation event has occurred.

Initialization audit:

`docs/research/r010-e001-initialization-technical-audit-v0.1.md`

Audit commit:

`341e1089b84665cbf854756528deb97e73897f39`

## 2. R009 implementation granularity

### G001

Status: **MECHANICAL_ENVELOPE_ESTABLISHED**.

- current BTCUSDT step = 0.00001 BTC;
- minQty = 0.00001 BTC;
- minNotional = 5 USDT;
- step-aware 2.5pp threshold about 219.26 USD;
- 250 USD is the first frozen tested tier with all target states/transitions statically feasible.

### G002

Status: **DISCRETE_IMPLEMENTATION_ENVELOPE_ESTABLISHED**.

- 250 USD remains a coarse mechanical floor, not a practical minimum;
- 1,000 USD is the current descriptive small-account demo-engineering candidate on tracking-fidelity grounds, not an optimized universal minimum;
- 5,000 USD+ is near-continuous under the frozen current-rule quantity/min-notional model;
- G003 liquidity/capacity remains deferred until material scaling or multi-user fanout makes it decision-relevant.

## 3. Research posture after R010 launch

Do not add another strategy family immediately. We now have enough simultaneous prospective clocks:

- R009 direction/recovery beta baseline;
- R003 carry on Binance and Bybit;
- R010 state-machine redesign shadow-forward.

Further strategy proliferation before these records mature would dilute falsification discipline.

## 4. Next priority — Safe-Sleeve S002 / access architecture

Before any real-capital promotion or production-like demo, convert the existing safe-sleeve architectural concept into a concrete access-and-instrument due-diligence layer.

Purpose:

- identify realistic off-venue reserve instruments accessible to the actual user/jurisdiction;
- separate survival reserve, execution buffer, crisis bridge and derivatives collateral;
- avoid treating stablecoin balances as equivalent to insured/sovereign cash-like reserve;
- document transfer/settlement delays, custody limits, withdrawal restrictions and counterparty concentration;
- define what portion, if any, can safely earn yield without becoming part of R003 carry risk;
- maintain the principle that realized carry may fund a bounded convexity budget, but carry capital itself is not the safe sleeve.

S002 must not silently assume product access. Actual jurisdiction/account eligibility must be checked before recommending implementation.

## 5. Minimal demo gate

A minimal demo may be considered only after:

1. forward plumbing for R009/R003/R010 remains technically stable;
2. S002 identifies a viable reserve/access architecture;
3. account-size/granularity assumptions are explicit;
4. venue/API failure and reconciliation paths are understood;
5. no real capital is required for the demo.

A demo is an execution/operations test, not evidence of strategy profitability or antifragility.

## 6. Immediate execution order

1. Continue R009-E002 unchanged.
2. Continue R010-E001 unchanged from 2026-09-11 00:00 UTC.
3. Continue Bybit R003-X003 unchanged.
4. Retry Binance R003-E003 only when source access permits, preserving original inception and causality-safe implementation.
5. Open Safe-Sleeve S002 as the next design/due-diligence task.
6. Keep G003 deferred until liquidity/capacity becomes relevant.
7. Consider minimal paper/demo integration only after S002 and forward plumbing checks.
8. Broad BotMarketplace feature development remains frozen until strategy/implementation evidence justifies expansion.

## 7. Explicit prohibitions

Do not:

- retune R009 after G001/G002;
- change R010 thresholds, weights, reset rule or inception after launch;
- treat inherited R010 armed state as validation;
- replace R009 with R010;
- merge Binance and Bybit R003 records;
- move any fixed forward inception;
- choose venues/capital tiers based on prettier historical or early-forward P&L;
- call stablecoin balances a safe reserve by default;
- treat demo operation as proof of strategy efficacy;
- restart broad platform development yet.
