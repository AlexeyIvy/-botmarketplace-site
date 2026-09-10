# R009-G001 — Capital Granularity Snapshot Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** frozen before G001 result inspection  
**Candidate:** R009 BTC v0.1  
**Purpose:** implementation-feasibility research only; not a strategy-performance test

## 1. Objective

Establish the current small-account mechanical feasibility envelope for the exact frozen R009 BTC target grid under current Binance Spot BTCUSDT trading constraints.

Primary question:

> At what account sizes can the current R009 2.5pp crisis increments and 0-20% target states be represented mechanically without silently violating minimum order/quantity rules?

G001 does not change R009 rules and does not evaluate profitability.

## 2. Why G001 is split from later audits

Capital scalability has three distinct questions:

- **G001 current mechanical granularity:** current minQty/minNotional/step-size and target-state feasibility;
- **G002 pathwise discrete replay:** effect of skipped micro-rebalances, rounding and daily drift on the frozen R009 path;
- **G003 capacity/liquidity:** large-AUM slippage, market impact, depth and venue concentration.

Do not collapse these into one model prematurely. G001 is the low-cost first gate.

## 3. Frozen venue and instrument

- Venue: Binance Spot.
- Symbol: BTCUSDT.
- Current trading filters: `GET /api/v3/exchangeInfo?symbol=BTCUSDT`.
- Price reference: latest fully closed Binance Spot BTCUSDT daily kline.
- No private account data or API key required.

Current filters are intentionally used because G001 asks about **implementability now**, not what Binance filters were historically.

## 4. Frozen R009 target grid

Exact desired risky-asset targets:

`0%, 2.5%, 5%, 7.5%, 10%, 12.5%, 15%, 17.5%, 20%`.

No target is added or removed after inspection.

## 5. Frozen capital grid

Evaluate exactly:

`$50, $100, $150, $200, $250, $300, $400, $500, $750, $1,000, $1,500, $2,000, $3,000, $5,000, $10,000, $25,000, $50,000, $100,000`.

This grid is diagnostic; it is not an optimized minimum-deposit recommendation.

## 6. Order-rule interpretation

For market-order feasibility, conservatively respect applicable current Binance filters:

- `LOT_SIZE` / `MARKET_LOT_SIZE` minimum quantity;
- positive quantity step sizes;
- `MIN_NOTIONAL` and/or `NOTIONAL` minimum where applicable to market orders.

For target representation, risky quantity is rounded **down** to the effective quantity step so the implementation does not intentionally exceed the frozen risky-asset target.

If the rounded quantity or notional is below an applicable minimum, that target state is marked mechanically infeasible at that account size.

## 7. Transition diagnostics

For every account size, examine transitions between all allowed R009 target states at the current reference price.

Particular attention is paid to the smallest 2.5 percentage-point increment because it is the crisis-tranche granularity bottleneck.

Report:

- ideal target notional;
- rounded BTC quantity;
- rounded notional;
- actual weight after rounding;
- absolute target-weight error;
- transition delta quantity/notional;
- whether the transition is a valid market order under current minimums.

## 8. Required headline floors

Report at minimum:

1. analytic lower bound for a standalone 2.5pp order from current min-notional/min-quantity rules;
2. first tested capital where `0% -> 2.5%` is mechanically feasible;
3. first tested capital where every nonzero R009 target state can be represented mechanically.

These are **mechanical floors only**.

## 9. What G001 explicitly does not prove

G001 does not model:

- daily price drift and the small rebalancing orders required to restore exact target weights;
- skipped micro-rebalances through time;
- historical changes in exchange filters;
- live spread/slippage;
- order-book depth and market impact;
- taxes;
- user-specific fees;
- safe-sleeve implementation;
- strategy profitability or antifragility.

Therefore G001 cannot authorize demo/live trading by itself.

## 10. Required outputs

Keep the result pack compact:

1. `r009_g001_run_state.json`
2. `r009_g001_instrument_snapshot.json`
3. `r009_g001_target_feasibility.csv`
4. `r009_g001_transition_feasibility.csv`
5. `r009_g001_summary.md`

## 11. Decision semantics

Maximum G001 status:

> **MECHANICAL_ENVELOPE_ESTABLISHED**

If Binance filters/source data cannot be interpreted consistently:

> **DATA_OR_RULES_REDESIGN**

There is no strategy PASS/FAIL in G001.

## 12. Next gate

Do not run G002 pathwise discrete replay until the first R009/R003 forward initialization has been checked technically.

After that check, G002 should quantify how actual order discreteness changes the frozen R009 implementation across account-size tiers, without changing SMA120, sleeve weights, crisis thresholds, reset rules or daily-target accounting.
