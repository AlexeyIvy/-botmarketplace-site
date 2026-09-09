# R008 Near-Term Research Roadmap v1.4

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** post-E003 technical review; E004 methodology audit inserted  
**Research posture:** antifragility-first, falsification-first, no hidden tuning

## 1. Current status

- R008 v0.1: REDESIGN under E002.
- R008 v0.2 symmetric recovery: REDESIGN / DO NOT ADVANCE under E003.
- Those formal experiment decisions remain unchanged.
- BTC SMA120 frozen forward record continues independently.
- R002 broad-universe rescue remains closed.

## 2. Technical-review correction

A post-E003 technical financial review identified two interpretation risks:

1. STATIC10/15/20 in E002/E003 are abstract constant target-weight series whose natural weight drift and maintenance turnover are not charged. This may favor static benchmarks relative to a realizable portfolio.
2. Benefit10 over closed crisis events is measured from breach to the next ATH. Conditioning on eventual recovery plus higher BTC exposure makes positive Benefit10 partly mechanical and can exaggerate the appearance of antifragile timing alpha.

Canonical correction note:

`docs/research/r008-technical-financial-review-correction-v0.1.md`

Therefore the prior statement “crisis deployment robustly works” is replaced with a narrower conclusion:

> crisis deployment improves recovery capture versus low static exposure, but exposure-controlled timing alpha has not yet been demonstrated under self-financing accounting and non-recovery-conditioned event windows.

## 3. Immediate next step — R008-E004

Before opening R009, run a methodology-only audit with **no strategy-rule changes**.

Protocol:

`docs/research/r008-e004-accounting-diagnostic-audit-protocol-v0.1.md`

E004 tests:

- self-financing natural weight drift;
- actual maintenance turnover for constant targets;
- daily and deterministic month-end static rebalance implementations;
- transition-only R008 implementation;
- fixed-horizon 7/30/90/180/365-day shock diagnostics;
- comparisons versus STATIC10/15/20 without waiting for a new ATH.

E004 cannot produce historical PASS. It only determines whether the existing strategic interpretation is stable.

## 4. Decision after E004

### ACCOUNTING_CONCLUSION_STABLE

If self-financing static portfolios still dominate and fixed-horizon timing benefit is weak versus STATIC15/20:

- close R008 crisis-only ladder development on this history;
- do not add hysteresis or tune drawdown levels;
- proceed to R009 as an economically distinct hypothesis.

### ACCOUNTING_CONCLUSION_CHANGED

If realistic accounting materially removes the static domination and/or fixed-horizon deep-shock benefit remains coherent versus STATIC15/20:

- retain the relevant frozen R008 version as a candidate;
- do not tune it further on the same history;
- move only to forward/new-independent validation plus implementation realism.

### MIXED

If accounting and event diagnostics disagree:

- document uncertainty;
- no promotion and no parameter search;
- prefer forward observation or close the branch.

## 5. R009 remains queued, not cancelled

R009 — Antifragile Trend-Gated Dry-Powder Barbell remains the next **new economic hypothesis** if E004 confirms the crisis-only ladder is not enough.

R009 must be specified through ablations before testing:

1. simple practical BTC/cash benchmark;
2. frozen BTC SMA120 trend-only sleeve;
3. frozen crisis-only mechanism;
4. combined trend + dry powder.

The frozen SMA120 lookback must not be retuned.

## 6. Additional later implementation requirements

Any barbell candidate that survives research must explicitly model the safe sleeve rather than call it generic cash:

- fiat / Treasury / custody choice;
- stablecoin and depeg risk if applicable;
- exchange counterparty concentration;
- transfer availability during crisis;
- cash yield/carry;
- execution spread/slippage and next-available execution timing.

A strategy is not antifragile if most capital is exposed to a correlated custody or stablecoin failure during the same market crisis it is supposed to exploit.

## 7. Priority order

1. **R008-E004 accounting & event-diagnostic audit.**
2. Make stable/changed/mixed interpretation decision.
3. If stable-negative, freeze and open R009 protocol.
4. BTC SMA120 forward record continues independently.
5. No further R008 threshold/release tuning on the same history.
6. True option/carry convexity remains a later data-intensive branch.
