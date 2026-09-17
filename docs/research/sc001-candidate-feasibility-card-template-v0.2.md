# SC001 — Candidate Feasibility Card Template v0.2

Date: 2026-09-17  
Status: **BINDING TEMPLATE BEFORE NEXT PROMOTIONAL ALPHA**  
Supersedes: `sc001-candidate-feasibility-card-template-v0.1.md`

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

## 4. Feature / Indicator Inventory

For every feature used or considered in the candidate definition record:

- feature ID/version:
- primitive family (P1-P11):
- exact formula/reference implementation:
- raw inputs:
- role (R1-R6):
- core vs auxiliary:
- causal availability timestamp:
- update cadence:
- warm-up:
- missing-data rule:
- normalization rule:
- prior evidence-registry references:
- likely redundancy with other features:
- feature-family parameter budget:
- interaction/composite budget:
- contamination status:

Also state:

- which feature is the minimum mechanism-defining feature set;
- which features are optional incremental augmentations;
- which popular indicators were deliberately excluded and why, if relevant.

Do not include a feature merely because it is widely used by traders.

## 5. Risk signature

- directional beta:
- volatility exposure:
- liquidity/adverse-selection exposure:
- inventory duration:
- funding/borrow exposure:
- legging risk:
- stress/liquidation-regime dependence:
- venue/collateral concentration:

## 6. Execution economics

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

## 7. Universe and breadth

- venue/product family:
- historical universe-selection rule:
- number of intended Discovery instruments:
- asset holdout rule:
- listing/spec/borrow eligibility constraints:
- why cross-market transfer is economically plausible:

## 8. Data and causality

- required source feeds:
- timestamp semantics:
- signal clock:
- execution clock:
- half-open interval conventions:
- synchronization/alignment rules:
- missing-data treatment:
- historical specs required:
- source identity/hash lineage requirements:

## 9. Selection/Calibration Sandbox

- calibration data roles:
- feature diagnostics allowed to inspect:
- quantities forbidden to inspect:
- parameter/feature variants allowed:
- redundancy diagnostics allowed:
- contamination record:
- strategy tuning budget:
- feature tuning/interaction budget:

Anything used here is non-promotional for this implementation.

## 10. Sample design

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

## 11. Null/matched diagnostic

- pre-registered null or matched control:
- reason it is scientifically relevant:
- interpretation rule:

## 12. Cheapest sentinel falsification

- cheapest data required:
- exact quantity to measure:
- prospectively frozen kill condition:
- minimum feature set used by sentinel:
- why passing sentinel does not yet imply profitability:

## 13. Structural feasibility gates

Candidate may proceed only if all applicable items pass:

- causal observability;
- data availability;
- basic cost headroom plausibility;
- sample feasibility;
- execution identifiability;
- universe/breadth feasibility;
- capital/capacity feasibility;
- untouched evidence availability;
- feature definitions causally valid and versionable;
- feature/interaction budget acceptable;
- no forbidden legacy-rescue relationship.

## 14. Engineering plan if sentinel survives

- execution kernel:
- feature reference implementation:
- feature golden/unit tests:
- accounting requirements:
- synthetic/golden tests:
- differential/reference checks:
- semantic data qualification:
- promoted outputs:

## 15. Pre-registered incremental feature tests

If any auxiliary feature is to be tested, state before promotional evidence:

- base strategy comparator:
- auxiliary feature ID/version:
- incremental test class (signal/filter/state/risk/execution):
- frozen opportunity denominator:
- primary incremental metric:
- block-level pairing rule:
- opportunity-retention metric:
- cost/turnover/risk metrics:
- promotion vocabulary:

If none, state `NO_INCREMENTAL_FEATURE_TEST`.

## 16. Promotion / stop rules

Before promotional run freeze:

- primary economic metrics:
- breadth metrics:
- concentration metrics:
- latency/cost stresses:
- uncertainty/block metrics:
- feature-specific diagnostics allowed:
- hard FAIL conditions:
- one-shot run rule:

## 17. Evidence-registry update rule

After every completed stage append scoped evidence records to:
`docs/research/sc001-feature-evidence-registry-v0.1.md`.

Do not convert a whole-strategy FAIL into a global feature FAIL unless the feature was explicitly isolated.

## 18. Candidate disposition

One of:

- `REJECT_STRUCTURAL`
- `REJECT_SENTINEL`
- `HOLD_INFORMATION_VALUE`
- `ELIGIBLE_FOR_BATCH`
- `SELECTED_FOR_FROZEN_EXPERIMENT`

Disposition must be justified without future promotional PnL.
