# R009-G001 — Capital Granularity Results and Technical Audit v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Candidate:** R009 BTC v0.1  
**Purpose:** implementation feasibility only; not a strategy-performance result

## 1. Formal status

**MECHANICAL_ENVELOPE_ESTABLISHED**

This status is limited to current Binance Spot BTCUSDT order granularity under the frozen G001 snapshot. It is not a strategy PASS and does not authorize demo/live trading.

## 2. Frozen current instrument snapshot

- latest fully closed BTCUSDT daily close: **78,306.43 USDT**;
- effective quantity step: **0.00001000 BTC**;
- effective minimum quantity: **0.00001000 BTC**;
- effective market minimum notional: **5.00 USDT**.

The NOTIONAL rule is the binding continuous minimum; minQty at the reference price corresponds to only about 0.7831 USDT.

## 3. Headline capital floors

The G001 engine reports a continuous-rule lower bound of **200 USD** for a 2.5 percentage-point tranche because 5 USDT / 2.5% = 200 USDT.

Important precision note: 200 USD is only the **continuous/notional lower bound**. Once the frozen 0.00001 BTC quantity step and round-down rule are applied, the exact executable 0 -> 2.5% threshold at the frozen reference price is higher:

- minimum rounded quantity that also clears 5 USDT = **0.00007 BTC**;
- notional at 78,306.43 = **5.4814501 USDT**;
- exact step-aware capital threshold = 5.4814501 / 0.025 = **219.258004 USD**.

Therefore the first tested frozen capital-grid point that works, **250 USD**, is correct. The 200 USD headline should be interpreted only as a theoretical continuous lower bound, not the exact executable threshold.

## 4. 250 USD mechanical behavior

At 250 USD:

- every nonzero R009 target state is mechanically representable;
- every pairwise transition among the frozen target states is executable under the frozen minQty/minNotional/step rules;
- the smallest transition notional is about **5.48145 USDT**;
- maximum static target-weight error from quantity rounding is about **0.3074 percentage points**, occurring at the 2.5% target;
- 17.5% target is represented by 0.00055 BTC, about 43.0685 USDT, or ~17.2274% of a 250 USD account.

At 200 USD some 2.5pp transitions remain below the 5 USDT minimum after quantity rounding; the account is not mechanically faithful to the frozen target grid.

## 5. Internal consistency checks

The uploaded result tables were independently checked against the frozen formulas:

- 18 capital levels × 9 target states = **162 target rows**;
- 18 capital levels × 9 × 8 directed transitions = **1,296 transition rows**;
- ideal notionals, rounded quantities and target-feasibility flags reconcile exactly with the frozen reference price and current-rule snapshot;
- transition delta quantities/notionals and feasibility flags reconcile exactly;
- first tested capital with 0 -> 2.5% feasible = **250 USD**;
- first tested capital with all nonzero target states feasible = **250 USD**;
- first tested capital with all directed target-state transitions feasible = **250 USD**.

No arithmetic inconsistency was found in the result package.

## 6. What G001 still does not answer

G001 is only a static snapshot. It does not tell us whether a 250 USD account can track R009 through time once:

- BTC price moves every day;
- portfolio weights drift between rebalances;
- desired corrections become smaller than 5 USDT;
- quantity rounding accumulates;
- a target goes to zero but residual BTC dust is too small to sell;
- fees are charged on actual discrete orders.

Those are exactly the questions for **R009-G002 pathwise discrete replay**.

## 7. Research interpretation

The meaningful current conclusion is:

> R009 is mechanically representable from roughly the low-hundreds of dollars under the frozen Binance rules, but 250 USD is only a static minimum-grid point, not yet a practical minimum account size.

A practical minimum must be determined from pathwise tracking fidelity in G002, not from G001 alone.
