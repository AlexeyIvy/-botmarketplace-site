# SC001 — N3 Regime-Dependent Execution-Mode Choice Feasibility Card v0.1

Date: 2026-09-18
Status: **NON-ALPHA FEASIBILITY CARD / NO EXPERIMENT ID**
Template: `sc001-candidate-feasibility-card-template-v0.2.md`

## 1. Identity

- candidate ID: **NOT ASSIGNED**
- short name: `N3_EXECUTION_MODE_STATE`
- relationship to prior SC001 experiments: reuses high-validity state/reference blocks, not terminal strategy rules
- why this is not rescue tuning: goal is execution-mode choice on an independent base opportunity
- mechanism family: execution-state optimization
- execution archetype: maker / taker / no-trade mode choice
- Signal Horizon: seconds-to-minutes state
- Position Horizon: inherited from base

## 2. Economic mechanism

Economic thesis:

High-validity state features may reduce execution cost and adverse selection even when they do not predict enough return to support a standalone strategy.

Candidate state blocks:

- RB007 continuous basis state;
- RB009 scheduled funding clock;
- RB014/RB015 depth state/normalization;
- RB017 quoted spread state.

Who pays for edge:

Execution-cost savings, avoided adverse selection and better urgency selection.

Main falsification:

State-dependent mode choice fails to improve net execution versus one fixed predeclared execution mode on the same base opportunities.

## 3. Time architecture

- feature update: seconds/minutes depending block
- decision cadence: same as base opportunity
- execution clock: must be frozen before outcome
- no future interpolation
- no same-bar look-ahead

## 4. Feature inventory

First experiment budget:

- one primary execution-state block only;
- optionally one hard risk veto;
- no multi-feature mode tree.

Preferred first state candidate:

RB017 quoted spread state because it directly links to execution economics and has high measurement validity.

## 5. Risk signature

Primary risk:

Mode choice can change fill probability, latency and opportunity retention.

These must be reported jointly; apparent cost reduction with severe missed-opportunity cost is not success.

## 6. Execution economics

- incremental fills due to mode feature: `0`
- potential benefit: reduce taker use / avoid adverse maker fills / abstain in poor execution states
- state information need not predict return directly
- Edge-to-Fill classification: `PLAUSIBLE_IF_BASE_EXISTS`

## 7. Universe and breadth

Must inherit future base opportunity universe.

No C7 asset subset selection from historical spread outcomes.

## 8. Data and causality

Existing L2/trade/state infrastructure is strong.

Fresh execution/outcome evidence still required after mode rule is defined.

## 9. Selection/Calibration sandbox

Allowed:

- fixed BASE opportunities;
- compare one static mode versus one state-dependent rule;
- opportunity-retention accounting.

Forbidden:

- mode threshold grid;
- multiple state blocks;
- historical venue/asset winner selection.

## 10. Sample design

Use paired opportunities where both policies are evaluable.

Report block/day uncertainty.

## 11. Null/matched diagnostic

Required:

- fixed maker;
- fixed taker;
- random mode with same maker/taker/no-trade proportions where scientifically sensible.

## 12. Cheapest sentinel falsification

Blocked until base opportunity is specified.

Future cheap sentinel should ask whether the state variable materially separates expected execution burden before full PnL simulation.

## 13. Structural feasibility gates

Pass:

- measurement validity;
- zero incremental fill count;
- data availability.

Blocker:

`NO_INDEPENDENT_BASE_OPPORTUNITY_DEFINED`.

## 14. Engineering plan if later selected

- execution policy interface;
- deterministic state-to-mode rule;
- counterfactual paired reporting;
- retained-opportunity accounting;
- execution golden tests.

## 15. Incremental feature test

`FIXED_MODE_BASE vs STATE_DEPENDENT_MODE`

Primary metrics:

- execution cost per original opportunity;
- fill/retention rate;
- adverse-selection metric;
- latency;
- net effect after missed-opportunity accounting.

## 16. Promotion / stop rules

Do not promote on lower fees alone if opportunity loss offsets savings.

## 17. Evidence-registry update

Append scoped execution-role evidence.

## 18. Candidate disposition

`HOLD_INFORMATION_VALUE`

Reason:

Concept is structurally attractive and low-fill, but no independent base opportunity currently exists to optimize.
