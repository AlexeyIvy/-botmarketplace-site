# R009 / R003 / Safe-Sleeve / Capital-Envelope Near-Term Research Roadmap v1.6

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** forward evidence priority; safe-sleeve architecture active; instrument-universe and capital-scalability constraints added  
**Research posture:** falsification-first, anti-cherry-picking, survival + accessibility + opportunity-cost + implementability aware

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

## 3. Safe-Sleeve S001 / S002

S001 architecture result remains:

> **ARCHITECTURE_PREFERRED_FOR_S002: MULTI-DOMAIN LAYERED RESERVE**

Required conceptual buckets:

- off-venue survival reserve;
- execution buffer;
- crisis-deployment bridge;
- derivatives collateral.

S002 must be user-access aware and include actual jurisdiction/account access, bank/broker/custodian availability, transfer/settlement latency, after-tax/fee safe yield and stablecoin/self-custody constraints.

## 4. New cross-strategy requirement: instrument universe

Canonical requirements:

`docs/research/cross-strategy-instrument-universe-and-capital-scalability-requirements-v0.1.md`

Do not restrict research conceptually to spot crypto alone. Maintain an explicit inventory of transparent market primitives available on relevant venues, including:

- spot;
- spot margin/borrow;
- linear/inverse perpetuals;
- dated futures;
- listed options;
- exchange-native spread/RFQ execution tools;
- operational collateral assets.

Availability alone is not a reason to use an instrument. A new primitive must solve a defined return, hedging, convexity, execution or risk-management problem and enter through a separately frozen protocol.

Packaged/structured yield products, copy trading and black-box bots are not treated as primitive strategy components until their embedded payoff/counterparty risk is decomposed.

## 5. New cross-strategy requirement: capital scalability

Every candidate that approaches production must have a **capital implementation envelope**.

The system is not allowed to assume continuous fractional quantities or a six-figure account.

Required later audit must measure:

- minimum mechanically executable capital;
- minimum economically sensible capital after fees;
- actual minQty/minNotional/qtyStep/contract-unit constraints;
- discrete sleeve-weight error after rounding;
- residual delta/hedge mismatch;
- margin headroom;
- skipped trades caused by minimum size;
- expected fees/slippage at multiple account sizes;
- maximum prudent capacity based on liquidity, market impact, open interest and venue risk limits.

Small-account and large-account feasibility are separate problems.

If a small account cannot implement a required component, define a prospectively separate implementation tier rather than silently claiming equivalence to the full strategy.

## 6. Immediate implications for current candidates

### R003

Historical E002 used continuous equal-BTC sizing. That does not prove micro-account implementability. Later capital-granularity testing must round spot and perp quantities to actual venue rules and measure residual hedge error.

Do not change the currently frozen R003 forward to solve this; capital-size variants are later implementation profiles.

### R009

R009 uses 2.5 percentage-point crisis tranches. On a sufficiently small account a tranche can fall below exchange minimum order/notional constraints. Later capital-granularity testing must measure skipped/rounded crisis deployments.

Do not change the currently frozen R009 forward rules.

### Future options / convexity

Option contract and premium granularity may create a substantially higher minimum viable capital than spot/perp strategies. Any future long-convexity branch must therefore publish its minimum viable account size before being described as broadly deployable.

## 7. R003 cross-venue replication

First independent venue remains precommitted to:

> **Bybit**

Sequence remains:

1. Bybit X001 structural funding-premium replication.
2. If structural signal survives, freeze Bybit X002 self-financing implementation replication.

Bybit's documented spread combinations such as FundingRateArb / CarryTrade / FutureSpread / PerpBasis are now flagged as a later **execution-engineering** research item. Do not assume they remove legging risk until venue-specific behavior is tested.

## 8. R009 cross-asset falsification

After forward infrastructure is stable and Bybit R003 replication is underway/completed:

- test unchanged R009 v0.1 on ETH only;
- no broad coin sweep;
- no parameter changes;
- structural falsification only, not temporal OOS.

## 9. Combined portfolio work

Do not optimize R003+R009 weights yet.

Future portfolio assembly additionally requires:

- forward behavior;
- Safe-Sleeve S002 facts;
- economic-correlation and operational/common-mode correlation matrices;
- availability-adjusted capital under joint stress;
- capital implementation envelopes for each component;
- no assumption that R003 collateral is safe reserve.

## 10. Carry-funded convexity

Remain deferred.

Only after forward R003 produces sufficiently attractive excess carry above safe-capital alternatives may a new candidate test:

> accumulated realized carry -> ring-fenced premium reserve -> bounded long-convexity spend

That future branch must also pass an options granularity/minimum-capital audit.

## 11. Execution order

1. **Today:** initialize/check R009-E002 and R003-E003 using the combined forward launcher after the required R003 bars are closed.
2. **Parallel now:** preserve Safe-Sleeve S001 result and prepare S002 user-access-aware due diligence.
3. **Parallel research constraint:** maintain instrument-universe inventory and capital-scalability requirements; do not yet alter frozen strategies.
4. **Then:** run Bybit R003-X001 under the precommitted venue choice.
5. If X001 supports the mechanism, freeze/run Bybit R003-X002.
6. Then perform unchanged-rule ETH R009 structural falsification.
7. Before any production promotion, run a prospectively defined Capital Granularity & Capacity Audit on surviving candidates.
8. Continue monthly R003 and quarterly R009 forward reviews without changing rules.
9. Only after these gates consider combined portfolio sizing and carry-funded convexity.

## 12. Explicitly deferred / prohibited work

Do not currently:

- optimize R003 leverage or funding entry threshold;
- optimize R009 SMA, sleeve weights, crisis thresholds or reset rules;
- add derivatives/options to current candidates merely because the venue offers them;
- search many venues and select the best carry result;
- search many coins and select the best R009 result;
- optimize safe-sleeve APY before survival/access architecture;
- claim a strategy works for a small account without discrete-order feasibility testing;
- claim unlimited scalability without market-impact/capacity testing;
- assign production portfolio percentages before S002 and sufficient forward evidence;
- call any candidate production-safe or antifragile solely because historical MaxDD is low.
