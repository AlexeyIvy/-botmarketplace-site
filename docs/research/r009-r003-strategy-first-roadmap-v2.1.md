# BotMarketplace Strategy-First Research Roadmap v2.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009 ETH X001 completed MIXED; R003 Bybit X001 MIXED; BTC forward clocks unchanged  
**Research posture:** falsification-first, forward-aware, no historical rescue tuning

## 1. Active forward clocks

- R009-E002 BTC forward remains unchanged from its fixed inception.
- R003-E003 Binance carry forward remains unchanged from its fixed 2026-09-10 12:00 UTC boundary.
- Original BTC SMA120 forward control continues independently.

First forward snapshots are technical causality/plumbing checks only.

## 2. R003 independent-venue state

Bybit R003-X001 is formally **STRUCTURAL_SIGNAL_MIXED**. Aggregate funding portability is qualitatively supported, but the prospectively frozen completed-year concentration gate failed. Do not open Bybit X002 and do not rescue with another venue or funding filter.

## 3. R009 cross-asset state

Canonical ETH result:

`docs/research/r009-x001-eth-results-v0.1.md`

Formal decision:

> **UNCHANGED_RULE_MIXED**

Canonical BTC/ETH comparison:

`docs/research/r009-btc-eth-structural-comparison-v0.1.md`

The only applicable ETH central check that failed is PRE_2020 COMBINED CAGR > TREND10 CAGR. All hard contradiction checks pass.

Interpretation:

- R009 has partial cross-asset mechanism support;
- risk efficiency is materially stronger on BTC;
- sticky crisis exposure is excessively persistent on ETH;
- R009 must not be described as a universal crypto architecture or true convex strategy;
- BTC remains the leading R009 instance and remains in genuine forward testing.

## 4. No rescue rules

Do not:

- change SMA120;
- change 10% trend / 10% crisis weights;
- change -20/-35/-50/-65 thresholds;
- change sticky-to-new-ATH reset;
- search SOL/XRP/other coins to find a positive R009 result;
- open new R003 historical threshold/leverage variants;
- reset forward clocks.

## 5. Immediate execution today

At the scheduled time run the combined R009-E002 + R003-E003 forward tracker.

Inspect the first output only for:

- exact inception reconstruction;
- closed-bar causality;
- funding mapping;
- state persistence;
- data integrity;
- deterministic rerun behavior.

Do not infer strategy quality from first-day P&L.

## 6. Next gate after forward technical initialization

R009 remains the strongest currently surviving directional candidate, but ETH MIXED prevents broad portability promotion.

Therefore the next practical gate is **Capital Granularity & Capacity Audit for the exact BTC R009 v0.1 implementation**, because this directly tests whether the historical target weights can be reproduced on the small account sizes relevant to an eventual demo/tiny-live pilot.

The audit must not change strategy economics. It must only quantify:

- Binance/selected-demo-venue minQty/minNotional/qtyStep constraints;
- rounding and skipped 2.5pp crisis tranches;
- target-weight error at small deposits;
- fees/slippage sensitivity by account tier;
- minimum mechanically executable capital;
- minimum economically sensible capital;
- capacity/market-impact ceiling at large AUM.

If exact R009 cannot be reproduced at small capital, define a separately versioned implementation tier rather than silently changing the strategy.

## 7. Demo gate

Minimal exchange demo can be prepared only after:

1. the combined forward infrastructure initializes correctly;
2. Capital Granularity & Capacity Audit shows a feasible account-size envelope;
3. no strategy rule is changed to fit the demo venue.

Demo is execution validation, not proof of profitability. Forward paper continues independently.

## 8. Safe sleeve

Safe-Sleeve S002 remains mandatory before real-capital promotion, but detailed product selection stays behind the immediate capital-granularity and demo-feasibility gate.

## 9. Orthogonal research fallback

Do not open another historical R009/R003 rescue branch.

If BTC R009 forward or implementation feasibility weakens materially, the next research branch must come from a genuinely different edge family. Priority should favor positively convex/trend-expansion structures over mean-reversion or short-volatility structures that introduce hidden crash fragility.

## 10. Current order

1. Today: initialize/check combined R009 + R003 forward.
2. Record first forward output as technical evidence only.
3. Run Capital Granularity & Capacity Audit for exact BTC R009 v0.1.
4. If feasible, prepare minimal one-venue demo execution for R009 while forward paper continues.
5. Continue R003 forward independently; no Bybit X002.
6. Complete Safe-Sleeve S002 before any real-capital step.
7. If R009 weakens, open a new orthogonal strategy family rather than tune R009.
8. Broad BotMarketplace platform development remains frozen until a leading strategy justifies it.
