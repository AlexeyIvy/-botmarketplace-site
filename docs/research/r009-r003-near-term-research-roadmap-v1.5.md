# R009 / R003 / Safe-Sleeve Near-Term Research Roadmap v1.5

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** forward evidence priority; Safe-Sleeve S001 opened/completed at architecture level; first R003 cross-venue replication precommitted to Bybit  
**Research posture:** falsification-first, anti-cherry-picking, survival + accessibility + opportunity-cost aware

## 1. Active evidence clocks

### R009-E002

- true forward directional/state-dependent beta candidate;
- original inception and frozen rules unchanged;
- combined mobile wrapper may launch/refresh it for convenience but cannot alter the R009 engine or clock.

### R003-E003

- true forward carry candidate;
- fixed decision boundary 2026-09-10 12:00 UTC;
- 50/50 fully funded equal-BTC construction unchanged;
- tracked against fixed Treasury references and causal dynamic 13-week Treasury benchmark;
- no funding threshold, leverage or rebalance-frequency tuning.

### Original BTC SMA120 forward

Continue independently and unchanged.

## 2. Core technical conclusions retained

- historical simulator survival is not proof of antifragility or bankruptcy immunity;
- inflation is contextual, while safe-capital opportunity cost is the direct capital-allocation hurdle;
- R003 and R009 may diversify P&L sources but can share catastrophic venue/collateral failure modes;
- no historical rule rescue is allowed while forward evidence accumulates.

## 3. Safe-Sleeve S001 — immediate parallel research

Protocol:

`docs/research/safe-sleeve-s001-architecture-failure-matrix-protocol-v0.1.md`

Initial architecture assessment:

`docs/research/safe-sleeve-s001-initial-architecture-assessment-v0.1.md`

S001 result:

> **ARCHITECTURE_PREFERRED_FOR_S002: MULTI-DOMAIN LAYERED RESERVE**

This is an architecture result, not a product allocation.

Required conceptual buckets:

- off-venue survival reserve;
- execution buffer;
- crisis-deployment bridge;
- derivatives collateral.

Key methodological addition:

Evaluate both nominal capital survival and accessibility at 1h / 24h / 72h horizons under joint stress scenarios.

## 4. Safe-Sleeve S002 — concrete implementation due diligence

Do not begin product allocation until the forward infrastructure has technically initialized and user-specific access facts are known.

S002 must incorporate:

- actual jurisdiction/tax framework;
- accessible banks/brokers/custodians;
- portfolio-size implications for insurance/concentration;
- practical transfer/settlement constraints;
- stablecoin/self-custody acceptability;
- after-tax and after-fee safe yield.

S002 may compare concrete products, but must preserve the S001 survival-first ordering rather than optimize APY.

## 5. R003 cross-venue replication — venue now precommitted

Precommit:

`docs/research/r003-cross-venue-replication-precommit-v0.1.md`

First independent venue:

> **Bybit**

Venue is frozen before result inspection to prevent post-Binance venue shopping.

Sequence:

1. Bybit X001 structural funding-premium replication.
2. Only if structural signal survives, Bybit X002 self-financing cash-and-carry replication with venue-specific mechanics documented before results.

Do not skip directly to leverage/funding filters or a multi-venue winner search.

## 6. Why Bybit is first and OKX is later

Bybit currently exposes public historical endpoints for:

- perpetual funding history;
- spot/linear klines;
- mark-price klines.

This offers close methodological parity with the Binance R003 sequence.

OKX remains useful as a possible later third venue, but current official downloadable archive coverage is shorter for funding/OHLC, so it is not the first parity-replication choice.

## 7. R009 cross-asset falsification

After forward infrastructure is stable and the Bybit R003 replication is underway/completed:

- test unchanged R009 v0.1 rules on ETH only;
- no SMA/weight/threshold changes;
- no broad coin sweep;
- interpret as structural falsification, not temporal OOS.

## 8. Combined portfolio work

Do not optimize R003+R009 weights yet.

A future combined portfolio study requires:

- enough forward evidence to estimate current behavior;
- S002 safe-sleeve implementation facts;
- explicit economic-correlation and operational/common-mode correlation matrices;
- availability-adjusted capital under joint stress;
- no assumption that R003 collateral is safe reserve.

## 9. Carry-funded convexity

Remain deferred.

Only after forward R003 produces sufficiently attractive excess carry above safe-capital alternatives may a separate candidate test:

> accumulated realized carry -> ring-fenced premium reserve -> bounded long-convexity spend

No dependence on contemporaneous crisis funding.

## 10. Execution order

1. **Today:** initialize/check R009-E002 and R003-E003 using the combined forward launcher after the required R003 bars are closed.
2. **Now:** Safe-Sleeve S001 architecture/failure matrix is frozen and initial assessment completed.
3. **After forward technical initialization:** open S002 user-access-aware safe-sleeve due diligence.
4. **Then:** implement Bybit R003-X001 structural replication under the precommitted venue choice.
5. If X001 supports the mechanism, freeze and run Bybit R003-X002 implementation replication.
6. Then perform unchanged-rule ETH R009 structural falsification.
7. Continue monthly R003 and quarterly R009 forward reviews without changing rules.
8. Only after these gates consider combined portfolio sizing and carry-funded convexity.

## 11. Explicitly deferred / prohibited work

Do not currently:

- optimize R003 leverage or funding entry threshold;
- optimize R009 SMA, sleeve weights, crisis thresholds or reset rules;
- search many venues and select the best carry result;
- search many coins and select the best R009 result;
- optimize safe-sleeve APY before survival/access architecture;
- assign portfolio percentages before S002 access facts and sufficient forward evidence;
- call any current candidate production-safe or antifragile solely because historical MaxDD is low.
