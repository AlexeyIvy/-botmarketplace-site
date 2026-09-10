# BotMarketplace Strategy-First Research Roadmap v1.8

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** strategy research is the only active product priority; broad platform development frozen  
**Research posture:** falsification-first, forward-aware, anti-overfitting, implementation-realism before real capital

## 1. Primary project objective

The current objective is **not to build the marketplace platform**. It is to discover, falsify, validate and progressively harden a trading system that is both economically attractive and resilient enough to justify later deployment work.

The desired end state may be a single strategy or a portfolio architecture composed of independent sleeves. We do not force the answer to be one indicator or one bot if antifragility is better achieved through complementary return/risk mechanisms.

## 2. What counts as progress

A candidate advances only when the next test attacks a distinct failure mode rather than tuning the same history.

Evidence ladder:

1. exact hypothesis/specification;
2. historical structural test;
3. realistic historical implementation test;
4. cross-venue / cross-asset falsification where relevant;
5. true forward paper record on unseen future data;
6. capital granularity/capacity feasibility;
7. exchange demo execution;
8. tiny live only after explicit approval and sufficient evidence;
9. broad BotMarketplace product implementation only after a leading candidate demonstrates that building around it is justified.

Historical success alone is never called proof of future performance or antifragility.

## 3. Demo timing clarification

Demo execution does **not** need to wait for a full year of forward paper data if a candidate has already passed strong historical/implementation gates and the purpose of demo is execution validation.

However demo is a second forward evidence channel, not a shortcut around forward paper testing.

Allowed sequence for a strong candidate:

- freeze rules;
- start true forward paper;
- after technical initialization and sufficient historical implementation evidence, start a minimal exchange-demo implementation in parallel;
- use demo to test API behavior, order granularity, fills, reconciliation, margin mechanics and execution drift;
- do not infer long-run profitability from a short demo sample.

## 4. Platform-development freeze

Do not resume broad marketplace/platform feature work now.

Allowed engineering only:

- research data collection and validation scripts;
- forward-paper trackers;
- minimal one-strategy demo execution tooling when a candidate becomes demo-eligible;
- small interface/safety contracts only when required to avoid research/deployment dead ends.

Deferred:

- multi-user live execution;
- marketplace UI expansion;
- billing/performance-fee systems;
- broad OAuth/broker rollout;
- smart routing;
- pooled/custodial AUM infrastructure;
- generalized production platform work not required by a validated strategy.

## 5. Active forward records

### R009-E002

- unchanged frozen forward candidate;
- original fixed inception remains untouched;
- first snapshots are technical/plumbing checks only;
- no historical or forward retuning.

### R003-E003

- unchanged frozen carry forward candidate;
- fixed decision boundary remains 2026-09-10 12:00 UTC;
- 50/50 fully funded equal-BTC implementation unchanged;
- safe-capital hurdle tracking unchanged;
- no funding threshold/leverage/rebalance-frequency rescue.

### Original BTC SMA120 control

Continue independently and unchanged.

## 6. Immediate historical falsification priority — Bybit R003-X001

The first independent-venue replication remains prospectively committed to **Bybit**.

Frozen protocol:

`docs/research/r003-bybit-x001-structural-replication-protocol-v0.1.md`

Frozen engine:

`research/r003/r003_x001_bybit_structural_replication.py`

Purpose:

> determine whether the Binance BTCUSDT funding premium is a broader venue-portable mechanism or may be materially Binance-specific.

This directly tests the economic edge and therefore takes priority over broad platform work and over detailed safe-sleeve product selection.

If X001 fails, do not shop for another venue to rescue the result.

If X001 passes, freeze a Bybit-specific X002 implementation replication before inspecting implementation results.

## 7. R009 cross-asset falsification

After the Bybit R003 structural branch is initialized/completed, run unchanged R009 v0.1 on ETH only.

Purpose:

> test whether the mechanism is BTC-specific.

No broad coin sweep and no parameter changes.

## 8. Safe-sleeve work remains required but not the immediate edge bottleneck

Safe-Sleeve S001 architecture result remains valid: multi-domain layered reserve.

Detailed S002 product/access due diligence is deferred behind the immediate edge-falsification work unless a candidate becomes demo-ready and needs explicit custody/collateral assumptions.

Safe-sleeve work is part of antifragility and production realism, but it must not consume the current research bandwidth before the candidate economics themselves survive stronger falsification.

## 9. Capital granularity and capacity gate

Before demo/tiny-live promotion of any surviving candidate, quantify:

- minimum mechanically executable account size;
- minimum economically sensible account size after fees;
- minQty/minNotional/qtyStep effects;
- residual hedge/weight error;
- margin headroom;
- skipped trades due to size;
- slippage/cost sensitivity across small/medium/large account sizes;
- maximum prudent strategy capacity.

A mathematically valid strategy is not considered deployable if a small account cannot reproduce its economics within stated tolerances.

## 10. Antifragility standard

Low historical drawdown or absence of modeled liquidation is **resilience**, not proof of antifragility.

A future candidate may be described as antifragility-oriented only when the combined architecture demonstrates, with pre-specified tests:

- survival under ordinary and severe stress;
- bounded downside / no hidden ruin mechanism within modeled assumptions;
- preserved liquidity/accessibility of required capital;
- non-fragile or beneficial response of at least one sleeve to crisis/volatility;
- positive expected economics after costs and safe-capital opportunity cost;
- no single common-mode venue/collateral failure capable of destroying the whole system without an explicit reserve/failsafe layer.

## 11. Current execution order

1. At the scheduled time, initialize/check the combined R009-E002 + R003-E003 forward run; interpret first outputs only technically.
2. **Now:** run Bybit R003-X001 structural replication under the already frozen venue choice and protocol.
3. If X001 passes, freeze and run Bybit R003-X002 implementation replication.
4. Run unchanged-rule R009-on-ETH structural falsification.
5. Compare surviving candidates/mechanisms; do not optimize a combined portfolio yet.
6. Apply Capital Granularity & Capacity Audit to any candidate approaching demo eligibility.
7. Start minimal exchange-demo execution for the strongest candidate(s) as an execution-validation channel while forward paper continues.
8. Complete Safe-Sleeve S002 when concrete demo/custody implementation requires it.
9. Tiny-live and broad BotMarketplace development remain later explicit gates.

## 12. Explicit prohibitions

Do not currently:

- retune R003 or R009 on inspected history;
- reset forward clocks;
- choose a venue/coin because its result is prettier;
- add leverage simply to raise CAGR;
- start broad platform development;
- equate a short profitable demo period with proof of robustness or antifragility;
- call low drawdown equivalent to absence of tail risk;
- move to real capital before demo/execution mechanics and capital granularity are understood.

## 13. Current project state

The project is now intentionally **strategy-first**.

Platform architecture documents are retained only as future design constraints. They do not authorize or prioritize platform implementation.

The next practical work item is the precommitted Bybit R003-X001 replication while R009/R003 forward clocks accumulate independently.
