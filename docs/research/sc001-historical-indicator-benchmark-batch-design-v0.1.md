# SC001-H1-001 — Historical Indicator Benchmark Batch Design v0.1

Date: 2026-10-02
Task: SC001-H1-001-CORRECTION
Parent task: SC001-H1-001
Worker: H1_HISTORICAL_INDICATORS
Authorization: DESIGN_ONLY_CORRECTION
Strategy review: PR #425 / comment 5961492007 / H1_PREFREEZE_SURVIVES_SOURCE_REUSE_CORRECTION
Status: HISTORICAL_BENCHMARK_PREFREEZE_READY_FOR_STRATEGY

## 1. Objective

Freeze a small historical indicator benchmark that measures economic primitives rather than brand-name indicators, without opening historical outcomes.

This document authorizes no execution. A new explicit Strategy/User task is required before any historical outcome-bearing run.

Adaptive classification: ADAPTIVE_DISCOVERY_GENERATED. The package was generated after prior SC001 outcomes; independent pre-freezing was not demonstrated. Any future positive Discovery remains adaptive and requires fresh chronological/prospective Confirmation.

Companion artifacts:
- docs/research/sc001-historical-discovery-data-contamination-census-v0.1.md
- docs/research/sc001-historical-indicator-benchmark-variant-ledger-v0.1.json

## 2. Benchmark unit and causal clock

Base candidate granularity: 1-minute completed OHLCV bars.

For bar index t, bar t represents the half-open interval [t_start,t_end). Final O/H/L/C/V values for bar t are unavailable until t_end. Every v0.1 feature may be evaluated only after t_end/source finalization and may use no final value from an open bar.

Define:
- C_t, H_t, L_t = completed close/high/low of bar t;
- Q_t = completed quote-volume field when its source semantics are validated;
- r_t = ln(C_t / C_(t-1));
- TR_t = max(H_t-L_t, abs(H_t-C_(t-1)), abs(L_t-C_(t-1))).

No hidden forward fill is allowed. Missing required inputs make the feature missing for that decision timestamp.

## 3. Frozen primitive families and variants

v0.1 admits exactly eight single-feature variants across five required primitive families.

### P1 — Price-location / oscillator

**H1-BM-P1-LOC20-v0.1**
- formula: 2 * (C_t - min(L_(t-19)..L_t)) / (max(H_(t-19)..H_t) - min(L_(t-19)..L_t)) - 1;
- denominator zero => missing;
- roles: R1 core signal, R2 state descriptor;
- warm-up: 20 completed bars;
- hypothesis: extreme recent location is a short-horizon reversion primitive;
- candidate position horizon: 3 minutes, fixed;
- redundancy: same-family alternative to H1-BM-P1-BAL14-v0.1.

**H1-BM-P1-BAL14-v0.1**
- U = sum(max(r_i,0)) and D = sum(max(-r_i,0)) for i=t-13..t;
- formula: (U-D)/(U+D); U+D=0 => missing;
- roles: R2_STATE_REGIME only in v0.1; any directional BAL14 use requires a new version/task and fresh evidence allocation;
- warm-up: 15 completed bars;
- hypothesis: recent signed movement balance measures directional pressure/location without claiming a standalone edge;
- candidate state observation horizon: 3 minutes, fixed; this is not a directional position test;
- redundancy: deliberately paired with LOC20 as a same-family representation, not an independent discovery.

### P2 — Trend / persistence

**H1-BM-P2-MASPREAD-8-32-v0.1**
- formula: mean(ln C_(t-7)..ln C_t) - mean(ln C_(t-31)..ln C_t);
- roles: R1 core signal, R2 regime descriptor;
- warm-up: 32 completed bars;
- hypothesis: positive/negative local trend persists in the same direction over a bounded fraction of the slow window;
- candidate position horizon: 8 minutes, fixed;
- redundancy: same-family comparator to SIGNPERSIST16.

**H1-BM-P2-SIGNPERSIST16-v0.1**
- formula: mean(sign(r_i)) for i=t-15..t, with sign(0)=0;
- roles: R1 core signal, R2 regime descriptor;
- warm-up: 17 completed bars;
- hypothesis: repeated same-sign one-minute movement is a persistence primitive;
- candidate position horizon: 4 minutes, fixed;
- redundancy: simpler direction-count comparator to MASPREAD-8-32.

### P3 — Volatility / range

**H1-BM-P3-RV20-v0.1**
- formula: sqrt(mean(r_i^2)) for i=t-19..t;
- roles: R2 state, R4 risk/sizing, R6 normalization;
- warm-up: 21 completed bars;
- directional claim: none;
- candidate state validity / position-conditioning horizon: 5 minutes, fixed;
- redundancy: scale-state comparator to RANGEEXP-5-20.

**H1-BM-P3-RANGEEXP-5-20-v0.1**
- formula: mean(TR_(t-4)..TR_t) / mean(TR_(t-19)..TR_t) - 1;
- zero 20-bar mean TR => missing;
- roles: R2 state, R3 filter/veto;
- warm-up: 21 completed bars;
- directional claim: none;
- candidate state validity / position-conditioning horizon: 5 minutes, fixed;
- redundancy: range expansion representation of the same broad volatility primitive as RV20.

### P4 — Volume / activity

**H1-BM-P4-RELACT20-v0.1**
- required field: causally finalized quote volume Q_t; reuse Q001's settled basic qualification, reopening it only for a concrete schema discrepancy; if exact-resource support fails, omit this feature rather than replace it post-hoc;
- formula: ln(Q_t / median(Q_(t-19)..Q_t)); Q_t<=0 or median<=0 => missing;
- roles: R2 state, R3 filter/veto;
- warm-up: 20 completed bars;
- directional claim: none;
- candidate state validity / position-conditioning horizon: 3 minutes, fixed;
- redundancy: no second P4 v0.1 variant; trade-count/activity alternatives are outside this batch budget.

### P7 — Reference / deviation

**H1-BM-P7-MEDDEV20-v0.1**
- formula: ln(C_t / median(C_(t-19)..C_t));
- roles: R1 deviation signal, R6 causal reference/normalization;
- warm-up: 20 completed bars;
- hypothesis: displacement from a robust local reference mean-reverts over a short bounded horizon;
- candidate position horizon: 5 minutes, fixed;
- redundancy: overlaps P1 price-location and P2 local trend by construction; it is not independent evidence from those families.

## 4. Multiplicity budget freeze

The complete v0.1 budget is:
- primitive families: 5;
- admitted feature variants: 8;
- parameterizations: exactly 8, one per admitted variant;
- alternate horizons per variant: 0;
- interaction tests: 0;
- composites: 0;
- symbol-subset alternatives: 0;
- hour/session filters: 0;
- venue winner search: 0;
- post-outcome direction flip: prohibited;
- post-outcome parameter neighborhood search: prohibited.

No variant may be silently replaced if a field is unavailable. Any replacement is a new version/new Strategy task with fresh evidence allocation.

The eight variants are a benchmark panel, not a leaderboard. Discovery does not authorize selecting the top historical performer and discarding the rest while calling the winner clean.

### Pre-outcome family-wise decision gate

The directional R1 set is exactly:
- H1-BM-P1-LOC20-v0.1;
- H1-BM-P2-MASPREAD-8-32-v0.1;
- H1-BM-P2-SIGNPERSIST16-v0.1;
- H1-BM-P7-MEDDEV20-v0.1.

BAL14 is excluded from directional R1 tests in v0.1. Related tests are not independent discoveries.

Gate status: UNRESOLVED_BLOCKS_R1_OUTCOME. Before any R1 outcome-bearing run, freeze the exact family-wise multiplicity decision rule across these frozen directional tests, including the decision procedure, family-wise error level, hypothesis/orientation definitions and dependence-aware inference specification. This correction neither chooses that rule nor authorizes an outcome run. No historical winner-picking is permitted. A separately authorized source-only audit may proceed before this gate is resolved because it opens no outcomes.

## 5. Data and asset prefreeze

Primary source class: Binance USD-M perpetual 1m completed klines, reusing the existing SC001 frozen long-history backbone. Another venue requires a separate future mechanism-specific Strategy decision.

Source-reuse references:
- docs/research/sc001-data-acquisition-protocol-v0.1.md;
- docs/research/sc001-data-q001-qualification-results-v0.1.md;
- docs/research/sc001-data-q002-results-v0.1.md.

BTCUSDT-only Q001/Q002 does NOT prove multi-symbol 120-day coverage. The exact 6-12 instrument universe remains outcome-blind and unresolved. A separate source/prior-use audit must resolve multi-symbol continuous coverage, prior SC001 use/contamination, DATASET_KEY/RESOURCE_ID, local verified reuse and evidence-block allocation. Reuse settled single-day basic bar/quote-volume qualification; do not repeat it absent a concrete schema discrepancy.

Outcome-blind source eligibility:
- >=120 complete UTC days after source/clock validation;
- >=6 eligible instruments and <=12 in v0.1;
- if >12 mechanically eligible instruments, retain the first 12 by normalized lexicographic symbol order;
- no selection by historical return, feature effect, volatility profitability or best hour.

If a concrete schema discrepancy makes exact-resource P4 quote-volume support fail audit, P4 is marked DATA_UNSUPPORTED and the remaining seven variants remain the only admissible v0.1 panel. No substitute P4 proxy is introduced on the same evidence.

## 6. Evidence blocks

No block is opened by this task.

For a future clean eligible interval of D complete UTC days, D>=120:
1. Selection / Calibration: first 40% of complete days, development assets only.
2. Discovery: next 20%, development assets only.
3. Asset Holdout: next 20%, pre-frozen holdout assets only.
4. Chronological Confirmation: final 20%, unchanged implementation on the pre-frozen eligible universe.

Rounding is performed once from the start boundary using whole UTC days; any remainder is assigned to Chronological Confirmation.

Asset split is outcome-blind:
- sort normalized eligible symbols lexicographically;
- positions 5,10,... are holdout assets;
- all other eligible symbols are development assets.

Selection may be used for causal/data validation and predeclared descriptive diagnostics, but no formula, parameter, horizon, direction, asset membership or interaction is changed from this v0.1 freeze based on Selection outcomes. If a change is needed, produce a new version and reallocate untouched evidence.

Discovery, Asset Holdout and Confirmation are opened sequentially under separate explicit authorization. A weak/strong Discovery cannot be used to redesign v0.1 and then reuse the same Discovery block as evidence.

## 7. Evaluation contract for a future authorized run

This task computes none of the following; it only freezes the contract.

For R1 directional variants:
- require the exact family-wise multiplicity decision rule in section 4 to be frozen before any outcome access;
- freeze the sign/orientation before outcome access;
- evaluate the signed forward response only at the single fixed horizon in the ledger;
- use instrument-day/calendar-block inference rather than event rows as IID;
- report breadth and concentration;
- do not convert the benchmark into a best-feature ranking.

For R2/R3/R4/R6-only roles (including BAL14, P3 and P4):
- no standalone directional promotional claim is allowed;
- any incremental evaluation requires a separately frozen base-opportunity denominator under docs/research/sc001-incremental-feature-testing-protocol-v0.1.md;
- freeze the base mechanism, opportunity ledger, comparator, feature role, effect metric, block/inference unit and stop rule in the separate authorized protocol before incremental outcomes;
- filters retain the original opportunity denominator and report retained/rejected counts and effects per base opportunity as well as per executed trade;
- descriptive state associations do not create directional promotion or implicitly authorize incremental evaluation. No base-opportunity denominator is established by this package.

Redundancy diagnostics may use predeclared calibration-only correlation/rank-correlation/opportunity-overlap measures. They do not create promotional evidence.

## 8. Edge-to-Fill screen before expensive PnL

PnL simulation is outside this task and outside the first benchmark gate.

Before any later expensive PnL stage, freeze a fill hurdle:
F_bps = round_trip_fee_bps + crossing_spread_bps + conservative_slippage_buffer_bps.

For a directional R1 candidate, a later clean block must first show that the predeclared signed gross response at its single fixed horizon has a conservative lower uncertainty bound above F_bps, with nontrivial instrument-day breadth and without one-asset/one-day concentration. If not, stop before PnL.

For R2/R3/R4/R6-only use, first separately freeze the base-opportunity denominator under the Incremental Feature Testing Protocol. Any later incremental value or predeclared risk/execution benefit must be assessed on that frozen base; it creates no standalone directional promotional claim. A higher conditional bps/trade caused only by deleting most opportunities is insufficient.

No fill hurdle, uncertainty threshold or cost assumption may be tuned after observing candidate PnL.

## 9. Stop / defer rules

Return HISTORICAL_DISCOVERY_DEFER_DATA rather than changing the benchmark if:
- a clean interval cannot be proven;
- <120 complete UTC days or <6 mechanically eligible instruments remain;
- clock/bar-finalization semantics are ambiguous;
- prior-use status cannot be resolved for any prospective clean block;
- required P4 activity semantics are unsupported and Strategy review requires P4 to remain mandatory.

Return HISTORICAL_DISCOVERY_REJECT_SCOPE if execution would require:
- parameter/horizon/symbol/hour search;
- a new mechanism outside H1;
- protected P1 evidence;
- reuse of terminal/promotional SC001 outcome windows;
- cross-domain research execution rather than a referral.

## 10. Shared-state boundary and next action

This package proposes no roadmap, governance, Strategy State, contamination-registry, reusable-registry or routing-architecture mutation.

PROPOSED_SHARED_STATE_CHANGE: none.

Next allowed action after this correction:
- Strategy Manager revalidates the corrected prefreeze and may merge the reviewed package;
- Strategy Manager may then dispatch one bounded Binance 1m source/prior-use audit, with no outcomes; the worker does not start it in this task;
- before any later R1 outcome-bearing run, separately freeze the unresolved family-wise multiplicity decision rule;
- otherwise return bounded design edits without opening outcomes.

MERGE_AUTHORIZED=false for this worker task. Persist the corrected four-artifact package and terminal receipt, leave PR #425 open, and stop for Strategy Manager review.

No historical outcome-bearing run is authorized by this document.
