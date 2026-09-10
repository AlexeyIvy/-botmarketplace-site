# R009 / R003 Near-Term Research Roadmap v1.4

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009 forward active; R003-E002 implementation-promising but recent capital efficiency marginal; R003-E003 forward frozen  
**Research posture:** falsification-first, no historical rescue tuning, opportunity-cost aware, common-mode risk aware

## 1. Current research state

R009 and R003 remain active for different roles:

- R009: directional / state-dependent beta candidate, already in true forward paper testing.
- R003: carry candidate with historically real funding economics after implementation realism, but recent return is marginal versus safe-capital alternatives.

Neither is production-approved.

## 2. Technical-review corrections now frozen

### Survival is not antifragility

R003's historical low drawdown and absence of modeled margin failure show resilience inside the simulator. They do not prove real-world bankruptcy immunity or antifragility.

### Inflation is not the primary hurdle

The key opportunity-cost benchmark is short-duration Treasury yield. Inflation remains secondary purchasing-power context.

### Safe hurdle must not be stale

R003 forward therefore tracks both:

- immutable inception Treasury reference: 3.90% annualized;
- immutable Treasury+2pp compensation reference: 5.90%;
- causal dynamic official 13-week Treasury bill opportunity-cost proxy, with each quote usable only from the following day.

### Economic diversification is not operational diversification

R003 and R009 may have distinct return sources but can share Binance/USDT failure modes. Future portfolio construction must retain off-venue safe reserve and explicit common-mode risk analysis.

## 3. R003-E003 forward freeze

Protocol:

`docs/research/r003-e003-forward-paper-protocol-v0.1.md`

Technical review:

`docs/research/r003-post-e002-technical-review-and-plan-v1.0.md`

Safe hurdle snapshot:

`docs/research/safe-sleeve-hurdle-snapshot-2026-09-10.md`

Implementation freeze:

`docs/research/r003-e003-forward-implementation-freeze-v0.2.md`

Frozen engine commit:

`cfc001400008ee4d63a27ad6821dda5cb9354f3e`

Mobile launcher commit:

`8367b239795f345d97b09fc9ab957aa3f3d31e57`

Fixed forward decision boundary:

**2026-09-10 12:00 UTC**.

The initial position is established at the close of the first fully closed common 1h bar after the boundary. Funding before that establishment close is excluded.

## 4. R003 forward evidence gate

No terminal positive promotion before all are satisfied:

- at least 365 elapsed calendar days;
- at least 1,000 forward funding events;
- at least 10 completed month-end rebalance opportunities.

Monthly descriptive reviews are allowed. No rules may change at reviews.

## 5. R009 forward

R009-E002 remains unchanged from its original fixed inception and frozen engine.

Run/re-run the tracker without changing SMA120, sleeve weights, crisis thresholds, reset rules, fees or comparator set.

R003 cannot reset or retune R009.

## 6. Original BTC SMA120 forward control

Continue unchanged and independently.

## 7. Historical tuning prohibitions

Do not rescue R003 by searching leverage, collateral split, funding thresholds, funding moving averages, selective regimes or rebalance frequency.

Do not rescue R009 by changing SMA length, weights, crisis thresholds or reset rules.

Any such change is a new candidate and cannot overwrite the current forward records.

## 8. Carry-funded convexity remains conditional

Do not open a long-option budget merely because historical R003 carry was positive.

Only after R003 demonstrates forward excess carry versus safe capital should a new protocol test:

> accumulated realized carry -> ring-fenced premium reserve -> bounded long-convexity spend

Expected contemporaneous future funding must not finance an open-ended option obligation.

## 9. Immediate execution order

1. Run R009-E002 now; preserve the original forward clock.
2. Run R003-E003 only after at least two fully closed common hourly bars exist after the 2026-09-10 12:00 UTC boundary.
3. Send the first technical snapshots only to verify causal initialization and data plumbing; do not interpret early P&L.
4. Thereafter refresh R003 monthly and R009 quarterly unless a data/operational problem requires earlier technical inspection.
5. Maintain the original BTC SMA120 forward control.
6. No nearby historical rule search while the forward records accumulate.
7. ETH unchanged-rule R009 structural falsification remains secondary, after forward infrastructure is stable.
8. Combined portfolio and true convexity research remain later gates, contingent on forward evidence and off-venue safe-sleeve design.