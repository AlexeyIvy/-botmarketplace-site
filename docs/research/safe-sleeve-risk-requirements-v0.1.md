# Safe-Sleeve Risk Requirements v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** cross-strategy implementation/risk research requirements  
**Scope:** cash-heavy / antifragile portfolio candidates including R009 and future carry/convexity branches

## 1. Purpose

Historical research has so far represented unused capital as zero-yield USD cash. That is a bookkeeping abstraction, not a production asset.

Any strategy that relies on a large safe or dry-powder sleeve must specify where that capital actually sits and whether it remains accessible during the same crisis the strategy is designed to exploit.

The safe sleeve is therefore a first-class risk component, not an afterthought.

## 2. Primary objective hierarchy

For the safe sleeve, optimize in this order:

1. **availability during stress**;
2. **survival / capital preservation**;
3. **independence from the risk asset and trading venue failure mode**;
4. **transfer / settlement reliability**;
5. only then **yield**.

Do not maximize yield before satisfying the first four requirements.

## 3. Failure modes that must be modeled later

At minimum:

- exchange insolvency or withdrawal freeze;
- stablecoin depeg / redemption impairment;
- bank / custodian access interruption;
- broker or Treasury-fund settlement delay;
- blockchain congestion / transfer halt;
- venue maintenance during a crash;
- wrong-way risk where collateral weakens together with BTC;
- inability to move capital quickly enough to execute crisis trades;
- jurisdictional or account-access restrictions;
- concentration in a single custodian or stablecoin issuer.

## 4. Candidate safe-sleeve instruments

Potential implementation choices may include:

- bank USD / insured cash where operationally available;
- short-duration US Treasury bills;
- Treasury money-market or equivalent short-duration government-cash vehicle;
- stablecoins used only where operationally necessary;
- exchange cash balance used only as an execution buffer.

This document does **not** select a production instrument or allocation.

Selection is deferred until a strategy survives forward evidence and concrete platform/venue constraints are known.

## 5. Separation principle

A future production architecture should distinguish at least conceptually:

- **off-venue reserve** — capital whose primary purpose is survival and independence from exchange failure;
- **execution buffer** — capital already at the trading venue for normal rebalancing;
- **crisis-deployment buffer** — capital that can be made executable fast enough during stress;
- **derivatives collateral** — margin capital whose risks are specific to the derivative venue.

These buckets need not have fixed percentages yet. Percentages must not be guessed before execution requirements are known.

## 6. Stablecoin rule

A stablecoin is not automatically equivalent to cash.

If a stablecoin is used, later analysis must explicitly include:

- issuer/redemption risk;
- depeg history and stress scenarios;
- reserve / custody structure;
- venue dependence;
- liquidity during market stress;
- on-chain transfer congestion;
- correlation of failure risk with crypto-market crises.

A portfolio should not be called antifragile if most nominally safe capital can fail in the same scenario that creates the intended investment opportunity.

## 7. Carry interaction

Future funding/basis carry must not consume the entire safe sleeve merely because the trade is approximately delta-neutral.

Derivatives carry introduces collateral, margin and counterparty risks that differ from true safe reserve risk.

Therefore:

- carry capital and safe reserve are not assumed equivalent;
- carry profits may later be transferred into a ring-fenced safe/convexity budget;
- expected future funding must not be treated as guaranteed safe-sleeve yield.

## 8. Convexity financing rule

If future long-option protection is financed by carry, the preferred research architecture is:

> **realized accumulated carry -> ring-fenced premium budget -> bounded option spend**

not:

> expected contemporaneous funding -> open-ended option premium obligation.

This prevents the protection budget from disappearing exactly when funding reverses during stress.

## 9. When to do quantitative instrument selection

Do not run a broad yield/product search now.

Quantitative safe-sleeve implementation research becomes justified when one of the following is true:

1. R009 or another directional candidate accumulates sufficient forward evidence to justify production design;
2. R003 cash-and-carry progresses beyond structural premium audit to a realistic collateral model;
3. a future convexity candidate requires an explicit premium reserve;
4. BotMarketplace platform design needs exact custody/transfer assumptions.

Until then, this document is a requirements freeze, not a product recommendation.

## 10. Research integrity principle

The safe sleeve is judged by joint portfolio resilience, not standalone yield.

A higher-yielding cash substitute that increases correlated failure risk may reduce, rather than improve, the antifragility of the total system.