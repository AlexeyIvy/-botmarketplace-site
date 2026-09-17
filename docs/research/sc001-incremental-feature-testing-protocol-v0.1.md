# SC001 — Incremental Feature Testing Protocol v0.1

Date: 2026-09-17  
Status: **BINDING FEATURE-INCREMENT PROTOCOL BEFORE NEXT PROMOTIONAL FEATURE CLAIM**

## 1. Purpose

Determine whether a feature adds useful information or economic value to a frozen base mechanism without confusing:

- standalone predictiveness;
- filter selection;
- risk reduction;
- execution improvement;
- strategy redesign.

This protocol is not permission to search arbitrary indicator combinations.

## 2. Preconditions

Before any incremental test freeze:

- base strategy/mechanism definition;
- feature ID/version and exact formula;
- feature role;
- parameter/interaction budget;
- calibration/promotional chronology roles;
- baseline comparator;
- primary effect metric;
- block/inference unit;
- stop rule.

If the feature was chosen using a period, that period is non-promotional for the resulting implementation.

## 3. Test classes

### A — Signal augmentation

Feature changes expected-return estimate/ranking while the underlying opportunity definition remains fixed.

Preferred comparison: same opportunity set, paired outcomes.

### B — Filter / veto

Feature accepts/rejects frozen base opportunities.

Must report:
- base opportunities;
- retained opportunities;
- rejected opportunities;
- retention rate;
- economics per executed trade;
- economics per base opportunity;
- total block contribution;
- turnover/cost change;
- tail/risk change.

### C — State / regime interaction

Feature partitions a predeclared state relevant to mechanism persistence.

State definitions must be frozen before promotional outcomes. Do not search many state cuts and keep the best.

### D — Risk / sizing augmentation

Feature changes exposure or exit/risk budget.

Compare not only return but risk, capital use, tail loss and turnover.

### E — Execution augmentation

Feature changes order timing/type/aggressiveness/depth handling.

Signal opportunities remain frozen where possible. Measure fill/cost/latency/adverse-selection changes separately from alpha.

## 4. New strategy boundary

A feature augmentation becomes a **new strategy experiment**, not an incremental feature test, if it materially changes any of:

- core economic mechanism;
- signal event definition;
- universe eligibility based on outcomes;
- target/exit family;
- expected holding horizon;
- number/type of legs;
- opportunity set so extensively that paired comparison is no longer meaningful.

Then assign a new experiment ID and preserve fresh evidence.

## 5. Statistical design

Prefer paired differences at the instrument-day/calendar-block level.

Do not treat event-level observations as IID when clustered within day/market.

Report:
- paired block count;
- distribution of block-level incremental effect;
- mean/median/trimmed incremental effect as prospectively defined;
- positive-block breadth;
- concentration;
- relevant block bootstrap or other predeclared dependent-data uncertainty;
- asset breadth where applicable.

If multiple feature variants are considered, the ledger and inference must acknowledge the selection budget.

## 6. Economic metrics

Incremental value should distinguish:

- predictive effect;
- gross edge change;
- cost change;
- net edge change when executable accounting is available;
- trade/opportunity count change;
- turnover;
- exposure time;
- tail/worst-block effect;
- capacity implications.

A feature is not useful merely because conditional mean bps/trade rises.

## 7. Baseline opportunity denominator

For filters and rankers, maintain a frozen baseline-opportunity ledger.

Primary reports should include both:

`incremental economics per retained/executed trade`

and

`incremental economics per original base opportunity`.

This prevents a feature from appearing good only because it removes most observations.

## 8. Parameter search

Parameter variants may be explored only in Selection/Calibration Sandbox under a predeclared budget.

After choosing a parameterization:
- freeze it;
- record all variants considered;
- do not use the same calibration period as clean Discovery/Confirmation for the selected feature implementation.

A parameter neighborhood discovered after promotional output is a new experiment/version.

## 9. Redundancy test

Before promoting a more complex feature, compare it to a simpler same-family baseline where scientifically appropriate.

Possible calibration diagnostics:
- correlation/rank correlation;
- residual predictive association;
- nested incremental effect;
- opportunity overlap;
- regime overlap.

If the complex feature adds no meaningful residual information/economics, classify `REDUNDANT_WITH_EXISTING_FEATURE`.

## 10. Feature interaction/composite rule

Two or more features may be combined only when:
- the interaction has an economic rationale frozen first;
- parent features/roles are declared;
- interaction count is in the search budget;
- simpler additive/single-feature baselines are retained where meaningful.

Combinatorial subset search is prohibited in ordinary SC001 feature testing.

Automated/high-dimensional feature selection requires a separate protocol with nested blocked validation and larger untouched evidence.

## 11. Promotion vocabulary

Possible scoped conclusions:

- `NO_INCREMENTAL_VALUE`;
- `INCREMENTAL_CALIBRATION_ONLY`;
- `DISCOVERY_INCREMENT_SUPPORT`;
- `CONFIRMATION_INCREMENT_SUPPORT`;
- `FORWARD_INCREMENT_SUPPORT`;
- `RISK_ONLY_VALUE`;
- `EXECUTION_ONLY_VALUE`;
- `REDUNDANT_WITH_EXISTING_FEATURE`;
- `INVALID_CAUSALITY_OR_DATA`.

Avoid global statements such as `RSI works`.

## 12. One-shot cleanliness

Any feature promoted after Discovery must have been pre-registered before that Discovery.

If a new feature is proposed because Discovery looked weak/strong in a certain subset:
- do not modify the existing experiment;
- create a new feature/experiment version;
- assign fresh evidence.

## 13. Registry update

After every test append a record to:
`docs/research/sc001-feature-evidence-registry-v0.1.md`

Do not delete negative or redundant records.
