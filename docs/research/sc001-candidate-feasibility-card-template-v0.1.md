# SC001 — Candidate Feasibility Card Template v0.1

Date: 2026-09-17  
Status: **BINDING TEMPLATE BEFORE NEXT PROMOTIONAL ALPHA**

Use one card per candidate family before promotional outcome access.

## 1. Identity

- candidate ID:
- short name:
- relationship to prior SC001 experiments:
- why this is not rescue tuning:
- mechanism family (M1-M7):
- execution archetype (T1-T4):
- Signal Horizon label:
- Position Horizon label:

## 2. Economic mechanism

- who/what pays for the edge:
- why the opportunity may persist after fees:
- expected decay horizon:
- main falsification statement:

## 3. Time architecture

Freeze separately:

- market-data resolution:
- signal lookback/aggregation:
- feature update cadence:
- decision cadence:
- decision timestamp semantics:
- primary latency:
- stress latency:
- expected hold:
- hard max hold:
- overnight/session rule:

For any bar-based input, state the exact bar availability rule and confirm no same-bar look-ahead.

## 4. Risk signature

- directional beta:
- volatility exposure:
- liquidity/adverse-selection exposure:
- inventory duration:
- funding/borrow exposure:
- legging risk:
- stress/liquidation-regime dependence:
- venue/collateral concentration:

## 5. Execution economics

- expected number of fills per completed cycle:
- maker/taker mix:
- conservative fee floor:
- spread/depth cost exposure:
- funding/borrow cost exposure:
- execution-model reserve:
- break-even gross move:
- minimum acceptable economic reserve / edge-to-cost requirement:
- expected opportunities per calendar day/week:
- expected capital-time utilization:
- rough minimum viable capital / capacity concerns:

## 6. Universe and breadth

- venue/product family:
- historical universe-selection rule:
- number of intended Discovery instruments:
- asset holdout rule:
- listing/spec/borrow eligibility constraints:
- why cross-market transfer is economically plausible:

## 7. Data and causality

- required source feeds:
- timestamp semantics:
- signal clock:
- execution clock:
- half-open interval conventions:
- synchronization/alignment rules:
- missing-data treatment:
- historical specs required:
- source identity/hash lineage requirements:

## 8. Selection/Calibration Sandbox

- calibration data roles:
- quantities allowed to inspect:
- quantities forbidden to inspect:
- contamination record:
- parameter/tuning budget:

Anything used here is non-promotional for this implementation.

## 9. Sample design

- economically meaningful effect floor / MDE:
- variance estimate source:
- conservative variance inflation if used:
- primary inference unit:
- minimum independent block target:
- expected event count:
- Discovery chronology:
- asset holdout chronology:
- later untouched Confirmation chronology:
- optional stopping rule:

## 10. Null/matched diagnostic

- pre-registered null or matched control:
- reason it is scientifically relevant:
- interpretation rule:

## 11. Cheapest sentinel falsification

- cheapest data required:
- exact quantity to measure:
- prospectively frozen kill condition:
- why passing sentinel does not yet imply profitability:

## 12. Structural feasibility gates

Candidate may proceed only if all applicable items pass:

- causal observability;
- data availability;
- basic cost headroom plausibility;
- sample feasibility;
- execution identifiability;
- universe/breadth feasibility;
- capital/capacity feasibility;
- untouched evidence availability;
- no forbidden legacy-rescue relationship.

## 13. Engineering plan if sentinel survives

- execution kernel:
- accounting requirements:
- synthetic/golden tests:
- differential/reference checks:
- semantic data qualification:
- promoted outputs:

## 14. Promotion / stop rules

Before promotional run freeze:

- primary economic metrics:
- breadth metrics:
- concentration metrics:
- latency/cost stresses:
- uncertainty/block metrics:
- hard FAIL conditions:
- one-shot run rule:

## 15. Candidate disposition

One of:

- `REJECT_STRUCTURAL`
- `REJECT_SENTINEL`
- `HOLD_INFORMATION_VALUE`
- `ELIGIBLE_FOR_BATCH`
- `SELECTED_FOR_FROZEN_EXPERIMENT`

Disposition must be justified without future promotional PnL.
