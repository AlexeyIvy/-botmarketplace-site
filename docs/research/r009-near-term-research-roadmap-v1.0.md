# R009 Near-Term Research Roadmap v1.0

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** E001 PROMISING_SCREEN; E002 forward paper next  
**Research posture:** antifragility-first, falsification-first, no historical rescue tuning

## 1. Current strategic status

R009 v0.1 becomes the primary active research candidate after passing its frozen in-sample mechanism screen.

Canonical E001 result:

`docs/research/r009-e001-results-v0.1.md`

Formal status:

> **PROMISING_SCREEN / ADVANCE TO FORWARD PAPER**

This is not historical PASS and does not authorize production.

R008 crisis-only ladder development is closed on the inspected BTC history after E004 `ACCOUNTING_CONCLUSION_STABLE`.

The original frozen BTC SMA120 forward record continues independently as a control and must not be reset.

## 2. What R009-E001 established

On PRIMARY_LONG at 10 bps:

- R009 combined CAGR ~15.02%;
- Max DD ~-15.73%;
- Calmar ~0.95;
- average BTC exposure ~12.91%.

STATIC15 daily:

- CAGR ~13.94%;
- Max DD ~-19.95%;
- Calmar ~0.70;
- average BTC exposure 15%.

STATIC15 monthly:

- CAGR ~16.74%;
- Max DD ~-22.30%;
- Calmar ~0.75.

R008 v0.1:

- CAGR ~14.70%;
- Max DD ~-23.11%;
- Calmar ~0.64;
- average BTC exposure ~17.08%.

The main structural result is therefore not raw return maximization. R009 produced a materially better observed growth/drawdown tradeoff than the standalone crisis ladder and was not dominated by simple 15% static allocations.

The result reproduced directionally in both 2013-2019 and 2020-2026, and survived 50 bps cost stress.

## 3. Interpretation discipline

Do not label R009 proven antifragile alpha.

E004 established that the crisis ladder alone is mainly conditional BTC beta allocation. R009's promising property is the interaction of two frozen sleeves:

- ordinary trend beta can disappear when price is below SMA120;
- distressed-risk beta can deploy as drawdown deepens;
- during recovery both may overlap.

On PRIMARY_LONG the crisis sleeve is active ~84% of observations, so “dry powder” is not literally dormant most of the time. More precise language is **state-dependent beta handoff with cash-heavy portfolio limits**.

True convex antifragility remains a later question for option/carry data.

## 4. Immediate next step — R009-E002

Start the frozen forward paper record.

Protocol:

`docs/research/r009-e002-forward-paper-protocol-v0.1.md`

Implementation freeze:

`docs/research/r009-e002-forward-implementation-freeze-v0.1.md`

Frozen engine commit:

`b82b5bb3cd71f6f3ba5efc796684e221c29917e7`

Mobile launcher commit:

`6579bc0720e52ded057607420132640d5a5d49ac`

Forward source:

- Binance Spot BTCUSDT;
- public market-data-only endpoint family;
- fully closed UTC 1d bars only.

Fixed forward inception:

**2026-09-10 00:00:00 UTC**.

The 2026-09-09 fully closed UTC bar determines the first target. Historical Binance bars before inception initialize state only and contribute no forward P&L.

## 5. Forward evidence rules

- run/review the tracker without changing parameters;
- descriptive checkpoints may occur quarterly;
- do not draw a terminal positive/negative conclusion before at least 365 forward daily intervals;
- a strong crisis-component conclusion additionally requires at least one forward -20% drawdown breach;
- if the first year contains no such stress, continue rather than declaring the crisis sleeve validated;
- keep all 5/10/25/50 bps cost tracks.

## 6. No historical tuning after E001

Do not search:

- SMA lengths;
- trend sleeve weights;
- crisis reserve sizes;
- crisis thresholds;
- tranche sizes;
- reset rules;
- interaction overrides;
- rebalancing frequencies chosen for better historical results.

R009 v0.1 is frozen exactly.

## 7. Safe sleeve requirement

Paper cash remains zero-yield USD for continuity only.

Before implementation promotion, the large safe sleeve must become an explicit economic/operational design:

- fiat versus T-bills;
- stablecoin exposure if any;
- depeg risk;
- custody and exchange concentration;
- transfer availability in a crypto crisis;
- cash yield;
- execution spread/slippage.

No strategy should be called antifragile if the supposedly safe majority of NAV is exposed to correlated failure during the same crisis it is supposed to exploit.

## 8. Parallel and later research

While R009 forward evidence accumulates:

1. BTC SMA120 original forward control continues unchanged.
2. Do not create another nearby BTC technical-rule search.
3. The next genuinely distinct antifragility research branch, if pursued in parallel, should prioritize **carry-funded convexity** rather than another drawdown ladder.
4. That branch requires better funding/basis and option-chain data and its protocol must be frozen before testing.

## 9. Priority hierarchy

1. **R009-E002 frozen forward paper record.**
2. **Original BTC SMA120 forward control continues.**
3. Define production-safe sleeve only after sufficient forward support.
4. Carry-funded / true option convexity may be researched as a separate future branch.
5. R008 crisis-only tuning remains closed.
6. R002 broad-universe rescue remains closed.