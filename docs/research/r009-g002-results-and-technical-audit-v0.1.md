# R009-G002 — Pathwise Discrete Replay Results & Technical Audit v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Experiment:** R009-G002  
**Protocol:** `docs/research/r009-g002-pathwise-discrete-replay-protocol-v0.1.md`  
**Protocol commit:** `cde4d52e071b623588ce3583901aea25cff1f13e`  
**Frozen engine commit:** `ea713a8899673733692659a44ce397b96cd3d4c5`  
**Status:** `DISCRETE_IMPLEMENTATION_ENVELOPE_ESTABLISHED`  
**Interpretation restriction:** implementation fidelity only; not strategy validation

## 1. Source and accounting audit

Uploaded G002 package was independently reconciled against the baseline daily audit path.

Source gate:

- Binance Spot BTCUSDT daily;
- retained closed rows: 3,311;
- primary replay: 2018-01-01 through 2026-09-09;
- primary observations: 3,174;
- duplicate dates: 0;
- maximum primary gap: 1 day;
- missing primary calendar days: 0;
- frozen current-rule execution constraints: 0.00001 BTC step, 0.00001 BTC minQty, 5 USDT minNotional.

Technical reconciliation checks passed:

- 6 capital tiers × 3,174 days = 19,044 baseline daily rows;
- all target weights are members of the frozen R009 grid 0/2.5/.../20%;
- continuous and discrete paths use the same frozen target series;
- every executed order satisfies frozen minQty and minNotional;
- all retained BTC quantities lie on the 0.00001 BTC quantity grid;
- skipped/executed flags reconcile exactly;
- executed post-trade quantity equals desired rounded quantity;
- skipped orders preserve the prior BTC quantity;
- NAV identity `cash + BTC_qty × close` reconciles to machine precision;
- 10 bps execution fee identity reconciles to machine precision;
- stored target-weight error reconciles to independently recomputed actual-vs-desired weight error;
- no negative-cash days;
- no blocked residual-dust exits.

All 24 capital-tier × fee-track headline rows were independently recomputed from the uploaded path inputs and matched the stored metrics to floating-point precision.

## 2. Frozen baseline 10 bps result

| Initial capital | Ending delta vs continuous | Avg abs target error | P95 abs error | Max abs error | Skipped order share | Executed orders |
|---:|---:|---:|---:|---:|---:|---:|
| $200 | +0.019883 | 0.5503 pp | 1.6780 pp | 2.7585 pp | 94.01% | 171 |
| $250 | +0.015340 | 0.4484 pp | 1.2266 pp | 2.1534 pp | 93.20% | 197 |
| $500 | +0.011188 | 0.2379 pp | 0.6578 pp | 1.0951 pp | 87.22% | 377 |
| $1,000 | +0.015226 | 0.1141 pp | 0.3274 pp | 0.5416 pp | 74.34% | 778 |
| $5,000 | -0.000781 | 0.0120 pp | 0.0570 pp | 0.1047 pp | 29.94% | 2,167 |
| $10,000 | -0.000382 | 0.0040 pp | 0.0234 pp | 0.0554 pp | 16.57% | 2,599 |

Continuous baseline ending multiple: 2.0339883. Continuous baseline MaxDD: -15.6064%.

## 3. Critical interpretation of skipped orders

The raw skipped-order percentage is dominated by tiny daily drift corrections, not by missed changes in the frozen signal state.

On the baseline 10 bps path there are 105 days where the desired R009 target changes from the prior day and an order is attempted. For every tested capital tier, including $200, all 105 such target-change attempts execute; none are skipped.

The high skip shares at small capital therefore mainly mean that small accounts cannot continuously trim tiny post-return weight drift back to the exact target every day. They do **not** mean that 93-94% of major R009 state changes are missed in this replay.

This distinction is important for implementation interpretation.

## 4. Tracking-fidelity gradient

The static G001 floor and the dynamic G002 fidelity question are different.

### $250

- remains mechanically viable through the replay;
- no negative cash and no trapped exit dust;
- all observed target-change attempts execute;
- however exact daily tracking is coarse: average absolute error 0.448 pp, P95 1.227 pp, maximum 2.153 pp;
- relative to one 2.5 pp crisis tranche, the P95 error is about 49% of one tranche and the maximum error about 86% of one tranche.

Therefore $250 remains a **mechanical / coarse-fidelity floor**, not a practical-minimum recommendation.

### $500

- average error 0.238 pp;
- P95 0.658 pp;
- maximum 1.095 pp;
- materially better but still visibly discrete.

### $1,000

- average error 0.114 pp;
- P95 0.327 pp;
- maximum 0.542 pp;
- all signal-state transitions execute in the baseline path;
- discrete tracking is substantially closer to the frozen target path, although most tiny daily drift corrections are still uneconomic under the 5 USDT minimum.

This is a reasonable **small-account implementation candidate tier for later demo engineering**, not a pre-declared universal minimum.

### $5,000-$10,000

- pathwise target tracking becomes very close to the continuous reference;
- $5,000: average error 0.012 pp, P95 0.057 pp;
- $10,000: average error 0.004 pp, P95 0.023 pp.

These tiers demonstrate that current Binance granularity ceases to be a material tracking limitation well before large account sizes.

## 5. Do not misread the positive ending-multiple delta

Small tiers sometimes finish above the continuous reference in this already-inspected historical path.

This is **not evidence that discreteness improves R009**. Skipped micro-rebalances and rounding alter realized exposure; on this particular historical sequence those deviations can accidentally help or hurt. Selecting a capital tier because it produced the highest historical ending multiple would violate the frozen anti-overfitting rule.

Implementation selection should be based on fidelity, operational simplicity, and forward/demo behavior, not on the sign of the historical ending-multiple difference.

## 6. Decision

Formal G002 status:

> **DISCRETE_IMPLEMENTATION_ENVELOPE_ESTABLISHED**

Research conclusions:

1. G001's $250 static floor survives a full pathwise replay mechanically.
2. $250 is too coarse to label a robust practical minimum from G001/G002 alone.
3. $500 improves fidelity substantially.
4. $1,000 is the first tested tier that is reasonably close for small-account demo engineering on target-error grounds, but this is descriptive rather than an optimized threshold.
5. $5,000+ is near-continuous from a quantity/min-notional tracking perspective.
6. No change to R009 signals, weights, thresholds, reset rule or forward record is authorized.

## 7. Remaining limitations

G002 deliberately does not reconstruct historical Binance filter changes and does not model:

- bid/ask spread;
- slippage;
- order-book depth / market impact;
- latency / rejected orders;
- venue outage risk;
- tax/account-specific fee tiers;
- safe-sleeve implementation.

The current-rule snapshot is applied counterfactually across the entire historical replay.

## 8. Next research implication

A separate G003 liquidity/capacity study remains useful before material real-capital or multi-user scaling, but it is not the highest-value immediate step for the current small-account research branch.

With R009/R003 forward plumbing initialized and G001/G002 complete, the next high-information research action is to convert the already documented R010 drawdown-armed recovery hypothesis into one prospectively frozen shadow-forward protocol while leaving R009-E002 unchanged.
