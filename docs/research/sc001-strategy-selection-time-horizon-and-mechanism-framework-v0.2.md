# SC001 — Strategy Selection, Time-Horizon & Mechanism Diversification Framework v0.2

Date: 2026-09-17  
Status: **RED-TEAM STRENGTHENED GOVERNANCE — BINDING BEFORE NEXT ALPHA FAMILY**  
Scope: `SCALPING RESEARCH / SC001`

Supersedes:
`docs/research/sc001-strategy-selection-time-horizon-and-mechanism-framework-v0.1.md`

This version incorporates a second independent review from three roles:

1. financial/economic researcher;
2. trader/programmer / market-microstructure engineer;
3. mathematician/statistician.

The purpose is not to choose the next strategy by intuition. The purpose is to create a prospectively constrained strategy-selection process that reduces research concentration, avoids data-driven strategy shopping, and allocates engineering effort only to mechanisms with plausible economic headroom and testable causal semantics.

---

## 1. Binding starting point

All prior SC001 terminal decisions remain immutable.

- E001-E008 remain terminal/closed;
- E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`;
- E009 remains terminal `E009_GROSS_FEASIBILITY_FAIL`;
- E009 read-only postmortem is complete with exact `E009_READONLY_POSTMORTEM_PASS`.

This framework is not a rescue path for any prior experiment.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

---

## 2. What survived the three-role critique

The following ideas remain valid after red-team review:

1. strategy selection must diversify by time horizon, mechanism and execution structure;
2. original sub-minute SC001 evidence should remain intact, while future search may prospectively expand to approximately 30-minute holding horizons;
3. under-covered H3/H4 regions deserve investigation, but under-coverage is **not** evidence of profitability;
4. future candidates need a causal economic mechanism, not merely an indicator recipe;
5. cheap falsification should precede expensive L2/spec/execution engineering;
6. multi-asset breadth and later chronological confirmation are separate evidence dimensions;
7. failed candidates must not be replaced by nearby parameter variants under the same experiment ID;
8. different execution archetypes require different kernels and cost hurdles;
9. the next candidate must not be selected because a particular symbol was a winner in E007R1/E009.

---

## 3. Important corrections introduced in v0.2

### 3.1 Under-covered does not mean promising

H3/H4 are under-researched, but this only creates **information value**, not expected alpha.

Future candidate priority must separate:

- information-value / coverage benefit;
- economic plausibility;
- implementation complexity;
- data availability;
- expected statistical power.

A candidate may fill a research gap and still be rejected before alpha if its cost floor or data requirements make it structurally unattractive.

### 3.2 No single “timeframe” label

Every candidate must freeze at least these six time dimensions:

1. market-data resolution;
2. signal aggregation/lookback;
3. decision cadence;
4. entry latency budget;
5. expected holding horizon;
6. hard maximum hold.

In addition, record two coarse labels:

- **Signal Horizon band**;
- **Position Horizon band**.

This prevents ambiguous descriptions such as “5-minute strategy” when the signal and holding horizon differ materially.

### 3.3 Signal clock and execution clock are separate

A signal may use only information whose availability timestamp is <= the decision timestamp.

Execution may occur only after:

`decision_ts + frozen latency`.

For bar-based strategies:

- a bar `[t0,t1)` is not available until `t1`;
- no entry may be executed inside the same bar using its final OHLC/VWAP/high/low;
- intrabar event ordering may not be inferred from OHLC;
- if event order matters, higher-frequency source data are required.

This **bar-causality rule** is binding for all future 1m/5m/10m strategies.

### 3.4 Selection evidence is contamination

Any data used to choose:

- the strategy family;
- threshold;
- lookback;
- horizon;
- eligible symbols;
- event definition;
- execution structure;

become **Selection/Calibration Sandbox** data and cannot later be claimed as untouched Discovery or Confirmation evidence for that implementation.

This rule applies even when the result inspected was not labeled “PnL”. Event frequency, conditional move, headroom, correlation and hit-rate can all contaminate strategy selection.

### 3.5 Diversity rules apply only after structural feasibility

Do not promote a weak candidate merely to fill an empty matrix cell.

First require basic structural feasibility. Diversity then determines which feasible candidates should receive scarce research budget.

### 3.6 No single scalar strategy score

Do not collapse candidate quality to an arbitrary weighted 0-100 score.

Use hard eligibility gates first, then compare survivors on a **Pareto basis** across:

- economic headroom;
- information value / research orthogonality;
- data quality;
- execution identifiability;
- sample feasibility;
- engineering cost;
- capital/capacity feasibility.

---

## 4. Horizon architecture

The coarse bands remain useful for coverage, but are not technical definitions.

### Signal Horizon labels

- S0: event / sub-second to ~5 s;
- S1: ~1-30 s;
- S2: ~15 s-2 min;
- S3: ~1-5 min;
- S4: ~5-10 min;
- S5: >10 min, normally outside core SC001 unless explicitly justified.

### Position Horizon labels

- P0: <10 s;
- P1: ~10-60 s;
- P2: ~1-5 min;
- P3: ~5-15 min;
- P4: ~10-30 min;
- P5: >30 min, normally a separate intraday program rather than core scalping.

A candidate may legitimately be `S4/P2` or `S1/P4` if its economic mechanism supports that asymmetry.

---

## 5. Mechanism families

- M1 — order-flow / microstructure prediction;
- M2 — liquidity provision / spread capture;
- M3 — overshoot / mean reversion / exhaustion;
- M4 — continuation / breakout / short trend;
- M5 — relative value / basis / paired convergence;
- M6 — cross-asset information transfer;
- M7 — forced-flow / liquidation / event mechanisms.

Mechanism family is about **why the edge may exist**, not how the signal formula is written.

Every candidate card must answer:

> Who or what economically pays for the edge, why can it persist after fees, and on what time scale should it decay?

A candidate whose explanation is only “indicator X crosses Y” is low priority.

---

## 6. Execution archetypes

- T1 — directional taker, usually two fills per round trip;
- T2 — passive maker;
- T3 — paired/multi-leg;
- T4 — hybrid.

Every candidate must freeze:

- expected number of fills;
- maker/taker mix;
- unavoidable fee floor;
- spread/depth exposure;
- latency sensitivity;
- legging/borrow/funding/queue uncertainty where applicable.

Execution structure is part of the economic hypothesis, not an afterthought.

---

## 7. Risk signature — new mandatory axis

Two different formulas can still be the same economic bet.

Every candidate must state a coarse risk signature covering at least:

- directional market beta;
- volatility exposure;
- liquidity/adverse-selection exposure;
- inventory duration;
- funding/borrow exposure;
- legging risk;
- dependence on stress/liquidation regimes;
- venue/collateral concentration.

Research diversification should avoid repeatedly testing different indicators that share the same underlying risk signature.

---

## 8. Financial/economic gate before alpha

Before outcome-bearing promotional testing, every candidate must document:

### 8.1 Edge payer / persistence thesis

Explain:

- why the opportunity can exist;
- why it is not instantly arbitraged away;
- what participant behavior, constraint or market friction creates it;
- expected decay horizon.

### 8.2 Conservative cost floor

Estimate prospectively:

- fees per cycle;
- spread/depth cost;
- funding/borrow if relevant;
- legging risk reserve;
- execution-model reserve;
- likely operational/latency sensitivity.

### 8.3 Break-even move and edge-to-cost requirement

Define before outcomes:

- break-even gross move;
- minimum acceptable edge/cost ratio or economic reserve;
- expected opportunities per calendar time;
- capital-time utilization;
- rough capacity envelope.

The research question is not only `bps/trade`. It is whether economically meaningful edge can survive costs at sufficient frequency and capital usage.

### 8.4 Tail/risk requirement

Any promoted candidate must eventually report:

- worst instrument-day/calendar block;
- loss clustering;
- exposure duration;
- intraday drawdown or path-risk diagnostics;
- stress-regime behavior.

Average edge alone is insufficient.

---

## 9. Trader/programmer gate before alpha

### 9.1 Minimal sufficient data

Use only the data complexity justified by the mechanism.

Examples:

- multi-minute directional candidate: trades/derived bars first; L2 only after gross/cost feasibility;
- basis candidate: synchronized spot+perp data;
- maker candidate: qualified L2/queue scenarios;
- lead/lag candidate: causally synchronized multi-asset feeds.

### 9.2 Immutable interval semantics

Freeze half-open windows, e.g. `[t-lookback,t)`, and exact decision boundaries.

No same-boundary future row may enter the signal.

### 9.3 Data lineage

Promotional runs must retain:

- source identity;
- hashes where feasible;
- transformation/version identity;
- UTC/session conventions;
- historical instrument/spec interval assumptions.

### 9.4 Reference implementation first

Before optimized promotional code:

- synthetic fixtures;
- golden/manual cases;
- causality tests;
- deterministic ledger/output;
- differential/reference comparison where practical.

Optimization must not change event/fill/accounting semantics.

### 9.5 Fail-closed missing data

Missing bars/buckets/events may not be silently forward-filled unless prospectively justified by the mechanism and protocol.

### 9.6 State-machine boundaries

Warm-up, day boundaries, overnight rules, max-hold exits and pending order states must be explicit and tested.

---

## 10. Mathematical/statistical gate before alpha

### 10.1 Selection Sandbox

A dedicated Selection/Calibration Sandbox may be used for:

- rough variance estimation;
- event-frequency estimation;
- feature calibration;
- candidate feasibility diagnostics.

Anything inspected there is permanently non-promotional for that implementation.

### 10.2 Prospective minimum detectable economic effect

Before Discovery, define an economically meaningful effect floor after considering costs.

Use contaminated/calibration variance estimates conservatively to determine whether the planned number of independent blocks can plausibly distinguish that effect from noise.

If not, lengthen chronology, broaden prospectively, or reject the candidate before alpha.

### 10.3 Effective inference unit

Do not treat cycles/ticks as IID.

Primary uncertainty units should usually be:

- instrument-day;
- calendar-day;
- multi-day block;

with dependence-aware analysis appropriate to the strategy.

### 10.4 Multi-asset same-date dependence

Eight symbols on one date are not eight independent time observations.

Preserve two distinct evidence axes:

1. cross-asset breadth/asset holdout;
2. later untouched chronological Confirmation.

### 10.5 Sequential research multiplicity

Maintain a research ledger recording:

- candidates considered;
- material variants considered by code/human/LLM;
- reasons for rejection;
- Selection Sandbox use;
- promotional experiments actually run.

A strategy family that receives many attempts requires stronger fresh evidence than a first-generation hypothesis.

### 10.6 Optional stopping prohibited

Do not keep extending Discovery until the strategy looks good.

Chronology and stop rules must be frozen before promotional outcome access.

### 10.7 Matched/null diagnostics

Where scientifically meaningful, pre-register at least one null or matched diagnostic, e.g.:

- time-shifted signal;
- matched-volatility opportunity;
- random/sign-symmetric control;
- common-market beta residual control.

These diagnostics cannot be added after seeing a weak result as a rescue.

---

## 11. Candidate-selection pipeline

### Stage A — Strategy Landscape

Maintain a living map of prior and prospective candidates by:

- signal horizon;
- position horizon;
- mechanism;
- execution;
- risk signature;
- evidence status.

### Stage B — Non-alpha Candidate Cards

Prepare standardized cards before promotional data access.

### Stage C — Structural Feasibility

Hard reject candidates failing:

- causal observability;
- basic cost plausibility;
- data availability;
- execution identifiability;
- minimum sample feasibility;
- capital/venue feasibility.

### Stage D — Selection/Calibration Sandbox

Only survivors may use contaminated calibration data for frequency/variance/rough-headroom estimation.

### Stage E — Cheapest Sentinel Falsification

Design the cheapest test that can kill the mechanism without heavy engineering.

Examples:

- basis: event frequency vs four-fill cost floor;
- multi-minute momentum: prospective move distribution vs two-fill cost floor;
- lead/lag: causal predictive relation after common-market control;
- maker: time-weighted spread vs maker/maker or maker/taker fee floor.

### Stage F — Pareto Shortlist

Do not rank with a single arbitrary score.

Select a small research batch of structurally distinct survivors using a Pareto comparison of economic plausibility, information value, cost, data quality and implementation risk.

### Stage G — Batch Freeze

Before the first promotional outcome in the batch, freeze for each selected experiment:

- candidate ID;
- economic hypothesis;
- time dimensions;
- universe rule;
- tuning budget;
- Selection Sandbox contamination;
- Discovery/holdout/Confirmation roles;
- primary metrics/gates;
- stop rule.

The result of candidate A must not retroactively redesign candidate B inside the same frozen batch. Any material redesign creates a new ID and new evidence plan.

### Stage H — Promotional Pipeline

For each frozen experiment:

1. metadata/universe audit;
2. semantic qualification;
3. execution/accounting validation as required;
4. one frozen Discovery;
5. asset holdout if applicable;
6. untouched chronological Confirmation;
7. forward/demo reconciliation.

---

## 12. Portfolio-level diversification rules

Apply these only among **structurally feasible** candidates.

1. Do not run more than two consecutive new promotional experiments from the same mechanism family.
2. Avoid a second candidate in the same `Signal × Position × Mechanism × Execution` cell before sampling a materially different feasible cell, unless the second was pre-registered as a controlled A/B test.
3. A rolling batch of roughly 3-5 promotional families should span multiple horizon/mechanism/risk cells when feasible.
4. Do not force an inferior candidate merely to satisfy diversity.
5. Prefer information value per research cost, but never at the expense of economic plausibility.
6. New results may update the Strategy Landscape, but do not rewrite prior FAILs.

---

## 13. Legacy retest principle

Do **not** rerun all previous strategies under the new framework.

The framework governs new evidence; it does not invalidate correctly executed old terminal experiments.

Legacy families fall into four categories:

1. **terminal mechanism/economics failure** — no same-rule retest;
2. **predictive signal but failed standalone economics** — may be reused only as a prospectively frozen auxiliary feature under a new ID;
3. **scope-limited test where the new design directly addresses the limitation** — strict replication may be justified under a new ID;
4. **simulator uncertainty coexisting with poor economics** — do not rerun same market merely to improve the simulator; a genuinely new eligible universe/mechanism may be studied under a new ID.

The binding classification is maintained in:
`docs/research/sc001-legacy-retest-and-replication-policy-v0.1.md`.

---

## 14. Immediate research objective

No new alpha run is authorized yet.

Immediate work:

1. freeze a Strategy Landscape covering E001-E009 and the current candidate slate;
2. apply the legacy retest policy;
3. prepare standardized non-alpha cards for C1-C6;
4. apply structural feasibility gates;
5. use a Selection Sandbox only where needed;
6. identify a small Pareto-efficient research batch spanning distinct cells;
7. freeze exact experiments before any new promotional outcome.

This is the current governing process for expanded short-horizon SC001 research.
