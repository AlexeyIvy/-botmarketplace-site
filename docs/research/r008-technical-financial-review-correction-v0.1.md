# R008 Technical Financial Review Correction v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** post-E003 technical review  
**Purpose:** correct interpretation risks before opening a new strategy branch.

## 1. What remains formally true

R008 v0.1 remains REDESIGN under frozen E002 rules. R008 v0.2 remains REDESIGN / DO NOT ADVANCE under frozen E003 rules. Those experiment decisions are not retroactively changed.

## 2. Accounting caveat that matters more than previously emphasized

E002/E003 use an architecture-level target-weight simulator. Daily return is prior target weight multiplied by the Bitcoin return; cost is charged when the target weight itself changes.

For a constant target benchmark such as STATIC15, the target never changes after initialization. Therefore the simulator keeps 15% BTC exposure mechanically without charging the turnover that a real self-financing portfolio would need to offset natural BTC-weight drift.

This is useful as an abstract exposure benchmark, but it is not a realistic 15/85 implementation.

Implication: the observed Pareto domination of R008 v0.2 by STATIC15 is a valid result **inside the frozen abstract accounting model**, but it is not yet sufficient evidence that a practical static 15/85 portfolio dominates a practical R008 implementation.

This does not imply that R008 would win under realistic accounting. It means the comparison has not yet been made fairly enough to decide that question.

## 3. Crisis-event Benefit10 interpretation was too strong

The prior event diagnostic defines a crisis event from the first -20% breach until the next new ATH, then summarizes mainly closed events.

This creates a conditioning problem:

- a closed event necessarily ends after a large recovery;
- R008 generally owns more BTC than STATIC10 during part of that recovery;
- deeper drawdowns require larger recoveries to regain the ATH;
- therefore positive and severity-increasing Benefit10 is partly mechanically expected from extra beta plus the recovery-conditioned endpoint.

Accordingly, `18/18 closed events with positive Benefit10` should **not** be treated as proof of antifragile timing alpha.

The stronger comparisons already point in this direction. In E003, v0.2 mean event benefit versus STATIC15 is negative for Levels 1-3 and positive only for Level 4; mean benefit versus STATIC20 remains negative on the all-history Level-4 group. Thus the evidence for crisis timing skill beyond simple higher exposure is materially weaker than Benefit10 alone suggests.

## 4. Revised economic interpretation

The evidence supports three narrower statements:

1. Increasing BTC exposure in large drawdowns can improve recovery capture relative to a low 10% BTC benchmark.
2. ATH-only release is too sticky and violates the intended dry-powder architecture.
3. Symmetric same-threshold release restores dry powder but, under the abstract accounting model, gives up enough recovery participation that STATIC15 still dominates headline CAGR/DD/Calmar.

What remains **unproven**:

> that the drawdown ladder itself produces timing alpha after controlling fairly for exposure, self-financing portfolio mechanics, and non-recovery-conditioned event windows.

## 5. Additional implementation risks to preserve for later stages

Even if an R008-style mechanism survives the next audit, production conclusions still require:

- natural BTC-weight drift and explicit rebalance turnover;
- executable timing rather than reference-price close abstraction;
- spread/slippage, not only nominal fees;
- a concrete definition of the safe cash sleeve;
- custody/stablecoin/counterparty risk;
- cash carry/yield assumptions;
- venue and transfer-liquidity constraints during crises.

For an antifragile portfolio, the supposedly safe 80-90% sleeve cannot be allowed to hide correlated exchange or stablecoin tail risk.

## 6. Correct next step

Do **not** jump directly to R009 yet.

Insert R008-E004 — Accounting & Event-Diagnostic Audit. It changes no R008 v0.1/v0.2 strategy rules and is not another parameter search.

E004 must answer two questions:

1. Does STATIC15 still dominate when portfolio accounting is self-financing and natural weight drift/rebalance turnover are explicitly modeled?
2. Does the apparent crisis benefit survive fixed-horizon, non-ATH-conditioned event diagnostics against STATIC10, STATIC15, and STATIC20?

Only after E004:

- if static allocation still dominates and fixed-horizon timing benefit is weak, close the crisis-only ladder branch and move to R009 / another economically distinct hypothesis;
- if realistic accounting materially changes the comparison or deep-shock benefit remains exposure-adjusted and coherent, preserve R008 as a separate candidate, but do not tune it further on the same history.
