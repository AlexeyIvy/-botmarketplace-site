# R009 / R003 Near-Term Research Roadmap v1.3

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009 forward frozen; R003-E002 IMPLEMENTATION_PROMISING but recent capital efficiency MARGINAL; R003-E003 forward frozen  
**Research posture:** falsification-first, no historical rescue tuning, opportunity-cost aware, common-mode risk aware

## 1. Primary strategic interpretation

R009 and R003 are both worth carrying forward, but for different reasons:

- **R009** is the primary directional/portfolio candidate and already has a fixed forward clock.
- **R003** has a historically real funding-carry mechanism after implementation realism, but its recent return is only marginal relative to safer capital alternatives.

Neither candidate is authorized for production or real-money scaling.

## 2. Correct interpretation of R003-E002

R003-E002 showed low historical model drawdown and no modeled margin failure under the frozen 50/50 construction.

This means the strategy was resilient **inside the simulator**, not that it is antifragile or bankruptcy-proof in the real world.

Unmodeled tail risks still include exchange failure, USDT impairment, exact liquidation rules, execution gaps, API/legging failure and access constraints.

Do not use the phrase “anti-fragile R003” unless a later design contains a demonstrated stress-benefit mechanism beyond simple survival.

## 3. Safe-capital hurdle now becomes explicit

The latest available U.S. Treasury bill snapshot before forward freeze is recorded in:

`docs/research/safe-sleeve-hurdle-snapshot-2026-09-10.md`

Frozen primary inception reference:

- 13-week Treasury bill coupon-equivalent yield: **3.90% annualized**.

Frozen research compensation floor:

- Treasury +2pp: **5.90% annualized**.

Inflation remains secondary context, not the primary opportunity-cost benchmark.

## 4. R003-E003 forward paper

Protocol:

`docs/research/r003-e003-forward-paper-protocol-v0.1.md`

Implementation freeze:

`docs/research/r003-e003-forward-implementation-freeze-v0.1.md`

Frozen engine commit:

`a0bbdb4a5deff9854f162ed7ad2a3c6f848cd5cc`

Mobile launcher commit:

`9f65aa4426aa3123b2914724e1f9bc24ab4b7ccd`

Immutable forward boundary:

**2026-09-10 12:00 UTC**.

First paper position is established only at the close of the first fully closed common 1h bar after that boundary; funding before that actual establishment close is excluded.

No terminal positive promotion before 365 days + 1,000 funding events + 10 completed month-end rebalance opportunities.

## 5. R009 forward remains unchanged

R009-E002 continues from its already frozen inception.

Do not change SMA120, sleeve sizes, drawdown levels, costs, reset logic or benchmark set.

R003 results do not alter R009.

## 6. Original BTC SMA120 forward remains unchanged

The original frozen BTC SMA120 forward control continues independently and must not be reset by either R009 or R003 research.

## 7. Common-mode operational risk rule

Do not count R003 and R009 as fully diversified merely because their economic return sources differ.

If both depend on Binance/USDT, they share failure modes.

Future portfolio construction must separate:

- economic alpha/carry diversification;
- venue/custody/collateral diversification.

A material off-venue safe reserve remains mandatory before any antifragile production claim.

## 8. No profit rescue on inspected history

Forbidden for R003 v0.1:

- leverage increase;
- lower collateral fraction;
- funding-entry thresholds;
- funding forecasts;
- funding moving averages;
- rebalance-frequency search;
- selective regime activation;
- venue shopping after results.

Forbidden for R009 v0.1:

- SMA retuning;
- sleeve-weight search;
- drawdown-threshold search;
- recovery/reset tuning;
- added technical filters.

## 9. Carry-funded convexity remains later

Do not start a long-option program merely because R003 historical carry was positive.

Only if forward R003 produces sufficiently persistent excess return versus safe capital should a new candidate test:

> realized carry transferred to ring-fenced reserve -> bounded option-premium budget -> long convexity

Funding must not be assumed to remain positive in the same crisis where protection is needed.

## 10. Immediate execution order

1. Run R009-E002 now that its forward inception has passed; retain its fixed original clock.
2. Run R003-E003 after the first two fully closed common hourly bars exist after the 2026-09-10 12:00 UTC boundary.
3. Re-run both forward trackers periodically without parameter changes.
4. Use monthly R003 descriptive checks and quarterly R009 descriptive checks; do not infer terminal edge from short samples.
5. Maintain the original BTC SMA120 forward control.
6. Do not start another nearby historical BTC price-rule search while these forward records accumulate.
7. Later secondary structural falsification: unchanged-rule ETH test for R009, only after forward infrastructure is stable.
8. Only after forward support, analyze a combined portfolio with explicit off-venue safe reserve and common-mode stress scenarios.