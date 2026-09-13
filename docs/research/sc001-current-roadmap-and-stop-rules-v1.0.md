# SC001 Current Roadmap and Stop Rules v1.0

Date: 2026-09-13  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Scope: independent SCALPING RESEARCH / SC001 branch only.

## 1. Independence from the principal project roadmap

SC001 remains an independent parallel research branch. It must not retrospectively alter R009-E002, R003-E003, R003-X003, R010-E001 or Safe-Sleeve S002. Likewise, those branches do not provide a performance target for SC001.

The project-wide canonical roadmap may continue separately. This document is the current branch-local execution order for SC001.

## 2. Frozen chronological architecture retained

The SC001 microstructure split remains unchanged:

- Development: 2023-04-01 through 2024-06-30;
- formal Validation: 2024-07-01 through 2025-06-30;
- Final: 2025-07-01 through 2026-08-31.

Inside Development, the trade-level firewall remains:

`DEV-DISCOVERY -> candidate freeze -> DEV-CONFIRMATION -> same-venue execution/L2 qualification -> formal Validation -> Final`.

Formal Validation and Final remain unopened.

## 3. Current E002 evidence ledger

### Binance DEV-DISCOVERY

Frozen 5-second signed aggressive trade-flow imbalance (TFI) screen passed on 15/15 preselected days. Classification: `PROMISING_SCREEN` only, not profitability proof.

### Binance DEV-CONFIRMATION

The unchanged E002 mechanism passed the 10-day chronological internal holdout: 10/10 positive daily Spearman at 100 ms, median daily Spearman about 0.0789, with all frozen confirmation gates passing.

### OKX same-venue transaction-price replication

The same economic mechanism replicated on all five preselected 2024-Q1 OKX UTC days: 5/5 positive daily Spearman at 100 ms, median about 0.0623. This reduces the likelihood of a Binance-only data artifact, but does not prove executable alpha.

### OKX L2 midquote pilot

The already-open pilot day 2024-01-05 retained the effect when response was changed from transaction price to causally sampled L2 midquote. At 100 ms, Spearman was about 0.0477 and top-minus-bottom extreme-decile midquote spread about 0.2495 bps.

Important economic warning: the gross magnitude is small. A naive symmetric tail interpretation is only about half the spread, roughly 0.125 bps per side before crossing the spread, taker fees, depth/VWAP impact, slippage, size discreteness and market impact.

### Q009A data state

2024-01-14 and 2024-01-31 L2 archives have passed full-day replay qualification. No alpha was calculated in Q009A.

## 4. Critical interpretation correction

The four-day Q1 midquote stage is a **measurement-robustness confirmation**, not a fresh independent temporal OOS test of the underlying TFI idea.

Reason: those same Q1 calendar days were already opened previously for OKX transaction-price replication. Midquote outcomes on the four remaining days are still unopened, so the test is valid for the narrower question "does the trade-price relationship survive a quote-based response definition?" It must not be described as a new fully independent alpha holdout.

Therefore:

- do not multiply p-values across Binance, OKX transaction-price and OKX midquote tests as if all evidence were independent;
- do not promote E002 to `ROBUST_HISTORICAL_CANDIDATE` from Q1 midquote confirmation alone;
- preserve 2024-Q2 OKX as the next true same-venue temporal holdout for an executable rule, not merely another descriptive signal screen.

## 5. Why the roadmap was refined once

After OKX transaction-price replication, the originally natural next step was executable-rule/economics design. A methodological risk then became material: transaction-price labels were often observed well after the nominal target because the first future trade could arrive hundreds or thousands of milliseconds later, and transaction prices can contain bid/ask-bounce / trade-sign effects.

The roadmap therefore inserted exactly one additional falsification layer: L2 midquote robustness. This was documented and frozen before the remaining Q1 midquote outcomes were opened.

This is a deliberate refinement, not an open-ended license for more diagnostics. **No additional signal-family detours are permitted after the frozen four-day midquote confirmation.** The next surviving branch must move to execution economics.

## 6. Immediate frozen sequence

### Step A — Q009B data-only acquisition/replay

Acquire and full-day replay-qualify only:

- 2024-02-12;
- 2024-02-13.

No TFI, midquote alpha, ranking or P&L may be calculated in the batch.

### Step B — one combined four-day midquote confirmation

Only after Q009A and Q009B both PASS, run one combined frozen confirmation on:

- 2024-01-14;
- 2024-01-31;
- 2024-02-12;
- 2024-02-13.

Use the already frozen protocol `sc001-e002-okx-midquote-q1-confirmation-freeze-v0.1.md`. No partial-batch alpha interpretation is allowed.

### Step C — execution-economics design freeze on already-open Q1 only

If and only if midquote confirmation is `PASS` or an explicitly predeclared survivable status, freeze a new executable-rule/economics experiment before any strategy P&L.

The design must specify at minimum:

- a causal signal threshold/rule available at decision time; full-day ex-post deciles are forbidden as live entry rules;
- non-overlapping position logic and conflict handling;
- taker-only primary execution;
- 100 ms BASE / 250 ms STRESS / 500 ms diagnostic latency;
- fill on the first qualified L2 state at or after order arrival;
- observed spread crossing and visible-book VWAP consumption;
- depth haircuts 0% / 25% / 50%;
- explicit fee assumptions stored separately from book costs;
- period-appropriate contract/lot/tick metadata where required;
- gross edge, spread/depth cost, fee cost and **net edge per trade after all costs**;
- a small predeclared threshold/search budget and multiple-testing ledger.

Before choosing a live threshold, a separately frozen **economic viability bound** may be used on Q1 to ask whether even favorable pre-fee tail response has enough room to cover unavoidable taker costs. Such a bound is diagnostic and must not be mislabeled as executable P&L.

## 7. Economic stop rules

E002 must stop or be materially downgraded if any of the following occurs under its frozen stage:

1. four-day midquote confirmation fails a primary gate;
2. a causal Q1 executable rule has non-positive net edge per trade under the frozen primary taker-cost model;
3. any apparent profitability exists only after post-hoc event exclusion, side selection, latency relaxation or threshold rescue;
4. profitability requires maker fills / queue priority not supported by price-level L2.

If passive/maker execution is ever researched, it is a new experiment family/ID with an explicit queue/fill model. It may not rescue a failed taker E002 under the same ID.

## 8. Q2 holdout rule

2024-Q2 OKX remains unopened for E002 execution economics.

Do **not** open Q2 merely to obtain more attractive statistics. Q2 is reserved for one-shot same-venue confirmation only after the Q1 executable rule, fees, sizes, latency and all promotion gates are frozen.

If Q1 economics fails, Q2 remains unopened and E002 is not rescued by searching Q2.

## 9. Formal Validation / Final / forward

Only a candidate that survives the Q1 execution-economics design and Q2 same-venue holdout may advance toward the already frozen formal SC001 Validation interval.

- Validation: one frozen run; no retuning afterward under the same ID.
- Final: one frozen run only after Validation pass.
- Forward: paper/demo only after historical robustness and implementation checks; no real capital authorized by SC001.

## 10. Current immediate action

Proceed with **Q009B data-only** for 2024-02-12 and 2024-02-13. Then stop acquisition and run the already frozen four-day midquote confirmation exactly once.
