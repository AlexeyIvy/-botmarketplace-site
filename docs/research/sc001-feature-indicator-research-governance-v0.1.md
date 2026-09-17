# SC001 — Feature / Indicator Research Governance v0.1

Date: 2026-09-17  
Status: **BINDING COMPANION GOVERNANCE BEFORE NEXT PROMOTIONAL ALPHA**  
Scope: `SCALPING RESEARCH / SC001`

Parent strategy-selection framework:
`docs/research/sc001-strategy-selection-time-horizon-and-mechanism-framework-v0.2.md`

This document integrates feature/indicator learning into the strategy-search process without turning SC001 into indicator mining.

---

## 1. Core objective

SC001 now has two linked research outputs:

1. identify economically viable strategy mechanisms;
2. accumulate reusable evidence about market features/indicators, their roles, limits, causal semantics and incremental value.

The second objective is subordinate to research integrity. Feature research must not contaminate untouched promotional evidence or create unlimited search degrees of freedom.

A feature is not automatically a strategy and a strategy is not automatically explained by one feature.

---

## 2. Three-role red-team conclusions

### 2.1 Financial / economic review

The useful object is not the indicator name but the **economic primitive it measures**.

Examples:

- RSI/Stochastic may represent normalized recent price position/momentum;
- ATR/realized volatility may represent volatility/range state;
- VWAP may be a reference price rather than a directional signal;
- TFI/order-flow imbalance may measure aggressive demand pressure;
- spread/depth/microprice may measure liquidity and short-horizon imbalance;
- basis/funding may measure relative-value pressure.

Therefore do not record global claims such as `RSI works` or `ATR does not work`.

Evidence must be scoped by:

- market/venue/product;
- time period;
- signal and position horizon;
- feature role;
- strategy mechanism;
- execution model/cost assumptions;
- evidence stage.

A feature may fail as a standalone trading rule while remaining useful as state/filter/risk/execution information.

### 2.2 Trader / programmer review

Feature implementations are part of the causal trading engine and must be versioned like execution code.

Every feature definition must state:

- raw inputs;
- exact formula;
- parameterization;
- warm-up;
- half-open time windows;
- timestamp/availability semantics;
- missing-data rule;
- normalization rule;
- update cadence;
- decision-time availability;
- source lineage;
- version/hash where promoted.

Library defaults are not canonical definitions. Two libraries can calculate nominally the same indicator differently.

Bar-derived features obey bar-close causality: final OHLCV for `[a,b)` is unavailable until `b`; no same-bar use of final close/high/low/volume.

No hidden forward fill is allowed unless a feature protocol explicitly defines a causally valid carry-forward state and its expiration.

### 2.3 Mathematical / statistical review

A feature registry must not become a leaderboard used for unrestricted strategy construction.

All variants considered count toward the research ledger, including human/LLM-generated variants.

Feature dependence/redundancy matters. Ten highly related oscillators are not ten independent discoveries.

Primary inference for incremental feature value should use paired instrument-day/calendar-block differences where possible, not millions of events as IID observations.

Selection/calibration evidence used to choose a feature, parameter, interaction or composite is non-promotional for that implementation.

---

## 3. Feature roles

Every feature occurrence must declare one or more explicit roles.

### R1 — Core signal

Directly contributes to entry/exit direction or expected-return ranking.

### R2 — State / regime descriptor

Describes market state such as volatility, trend, liquidity, compression, funding or stress. It may have no standalone directional edge.

### R3 — Filter / veto

Allows or blocks an otherwise defined base opportunity.

### R4 — Sizing / risk feature

Changes position size, risk budget, stop/exit horizon or exposure without being the primary alpha mechanism.

### R5 — Execution feature

Changes order type/timing/aggressiveness/depth handling/cancel logic but not the economic signal itself.

### R6 — Reference / normalization feature

Defines a baseline or scale such as VWAP, rolling volatility, basis baseline, residualization or normalization.

A feature may hold multiple roles, but the protocol must state which role is being tested.

---

## 4. Feature architecture

Use the causal dependency chain:

`raw market data -> economic primitives -> feature transforms/indicators -> strategy mechanism -> intent/orders -> fills -> accounting -> evidence`

Do not jump directly from indicator name to trading rule.

The registry should distinguish:

- raw observable;
- primitive economic quantity;
- derived feature;
- composite/proprietary feature;
- strategy rule using that feature.

This allows us to learn, for example, that several oscillators are alternative representations of the same underlying recent-price-position primitive.

---

## 5. Evidence is append-only and contextual

There is no single mutable global field `works = true/false`.

Each evidence record is scoped and appended.

Required evidence fields:

- feature ID/version;
- feature family / economic primitive;
- role under test;
- strategy/experiment ID;
- market/universe;
- signal horizon;
- position horizon;
- chronology/data role;
- baseline comparator;
- costs/execution stage;
- opportunity count and block breadth;
- effect measured;
- incremental effect if applicable;
- robustness/latency/cost notes;
- contamination status;
- evidence classification;
- limitations.

Suggested evidence classifications:

- `DEFINED_ONLY`;
- `DESCRIPTIVE_CALIBRATION`;
- `PREDICTIVE_CALIBRATION`;
- `INCREMENTAL_CALIBRATION`;
- `DISCOVERY_SUPPORT`;
- `CONFIRMATION_SUPPORT`;
- `FORWARD_SUPPORT`;
- `NO_INCREMENTAL_VALUE`;
- `REDUNDANT_WITH_EXISTING_FEATURE`;
- `INVALID_CAUSALITY_OR_DATA`;
- `STRATEGY_FAILED_FEATURE_NOT_ISOLATED`.

The last status is important: if a strategy containing a feature fails, do not infer that the feature itself failed unless the experiment isolated that question.

---

## 6. Incremental feature testing principle

Indicator usefulness is not equivalent to standalone strategy profitability.

When scientifically meaningful, compare a frozen base mechanism against a pre-registered feature augmentation:

`BASE`

versus

`BASE + FEATURE_X`.

Prefer identical underlying opportunity sets.

For filters/vetoes report both:

- economics per executed trade;
- economics per **base opportunity**;
- opportunity-retention rate;
- turnover change;
- total block-level economic contribution;
- tail/risk change.

A filter that raises mean bps/trade by discarding most opportunities is not automatically useful.

If FEATURE_X materially changes the strategy mechanism, signal event definition or opportunity universe, it is no longer a simple incremental feature test; it becomes a new strategy experiment ID.

---

## 7. Redundancy and feature families

Do not count mathematically related indicators as independent evidence.

Maintain a feature-family/economic-primitive taxonomy and record likely redundancy.

Examples:

- SMA/EMA/MACD are related price-trend transforms;
- RSI/Stochastic/price-location oscillators share recent-price-position/momentum information;
- Bollinger-style z/deviation features combine reference-price deviation and volatility scaling;
- ATR/realized range/realized volatility represent related volatility-state information;
- order-flow imbalance variants share aggressive-flow information.

Redundancy may be assessed on calibration data using correlation, rank correlation, residual tests or other predeclared dependence diagnostics. Such diagnostics are descriptive and do not create promotional evidence.

---

## 8. Parameter and interaction budget

Feature research creates a large combinatorial search space, so each experiment must freeze a budget before outcome-bearing exploration.

Record:

- number of feature families considered;
- number of parameter variants per family;
- number of transformations;
- number of interactions/composites;
- manual/LLM proposals considered;
- selection rule.

Do not search arbitrary combinations such as every RSI/ATR/ADX/MACD subset and promote the best-looking combination.

Default posture for ordinary SC001 experiments:

- one economically motivated core mechanism;
- small predeclared auxiliary-feature budget;
- one-at-a-time incremental tests where possible;
- multi-feature optimized models only under a separate ML/feature-selection protocol with nested/blocked validation and larger untouched evidence reserves.

---

## 9. Custom / proprietary indicators

Creating our own indicators is allowed and encouraged only when it answers a defined economic measurement problem.

A custom feature proposal must state:

1. underlying economic primitive(s);
2. why existing simpler features are insufficient;
3. exact causal inputs;
4. formula and parameters;
5. expected role;
6. complexity relative to simpler baselines;
7. calibration/tuning budget;
8. falsification condition.

A custom feature built after inspecting promotional outcomes gets a new feature version, new experiment ID and fresh promotional evidence.

Do not optimize formulas directly against historical PnL without a separately governed feature-selection program.

Prefer the simplest representation that preserves the hypothesized information.

---

## 10. Feature evidence does not override strategy economics

A statistically predictive feature can still be economically unusable after fees/spread/depth/latency.

A feature that improves gross prediction but worsens turnover or execution costs may be net negative.

Therefore evidence records should distinguish, when available:

- predictive information;
- gross economic effect;
- incremental net effect;
- turnover/cost effect;
- risk/tail effect;
- execution robustness.

No predictive correlation alone promotes a strategy.

---

## 11. Feature reuse across strategies

Previously studied features may be reused only prospectively.

Before reuse:

- identify previous evidence and its exact scope;
- state why the feature is relevant to the new mechanism;
- freeze its role and formula;
- do not select parameter values because they were profitable in another contaminated experiment unless that is explicitly treated as calibration and fresh promotional evidence remains untouched.

Negative evidence also transfers only within scope. Failure of one strategy containing ATR, VWAP or MAD does not make those features globally invalid.

---

## 12. Required outputs from every future candidate

Every future SC001 candidate card must contain a `Feature / Indicator Inventory` with:

- raw inputs;
- economic primitives;
- derived indicators/features;
- feature IDs/versions;
- role of each feature;
- causal availability;
- core vs auxiliary status;
- prior evidence references;
- redundancy notes;
- parameter budget;
- contamination status.

After the experiment, append evidence records to the central registry without rewriting earlier records.

---

## 13. Promotion rules for feature claims

Permitted language must match evidence strength.

Examples:

- calibration association -> `associated on calibration data`;
- clean Discovery -> `supported on frozen Discovery`;
- independent time Confirmation -> `confirmed on the frozen Confirmation period`;
- forward/demo -> `survived forward/demo reconciliation`.

Do not say `feature X works` based on one strategy, one market or one calibration sample.

A feature becomes a strong reusable building block only after evidence survives multiple relevant dimensions such as asset breadth, time Confirmation and realistic execution/costs.

---

## 14. Integration with SC001 strategy-selection process

Feature research is embedded at each stage:

1. **Strategy Landscape** — record which economic primitives/features prior experiments actually used.
2. **Candidate Card** — freeze Feature / Indicator Inventory.
3. **Selection Sandbox** — inspect only allowed calibration feature diagnostics; mark contamination.
4. **Sentinel** — use the smallest feature set needed to falsify the mechanism.
5. **Frozen experiment** — lock feature code/formulas/roles/parameter budget.
6. **Discovery** — evaluate strategy and pre-registered feature diagnostics only.
7. **Asset holdout / Confirmation** — no post-Discovery feature redesign.
8. **Forward/demo** — reconcile feature availability/timing with live reality.
9. **Registry update** — append scoped evidence records.

---

## 15. Hard prohibitions

Do not:

- create a leaderboard of dozens of indicators and trade the historical winner;
- infer global usefulness from one strategy result;
- use final-bar values before bar close;
- hide parameter searches from the multiple-testing ledger;
- silently change indicator library/defaults;
- combine many features after viewing Discovery and reuse the same Discovery as evidence;
- treat highly redundant indicators as independent confirmations;
- let a feature filter improve per-trade metrics while hiding lost opportunities;
- promote a custom indicator without formula/version/data-lineage freeze.

---

## 16. Immediate implementation

Before the next promotional alpha family:

1. create the Feature / Indicator Taxonomy;
2. create and bootstrap an append-only Feature Evidence Registry using E001-E009 only for historically supported scoped records;
3. adopt an Incremental Feature Testing Protocol;
4. update the candidate feasibility-card template with Feature / Indicator Inventory;
5. add feature inventory to C1-C6 before sentinel design;
6. keep `NO NEW PROMOTIONAL ALPHA` until the strategy-selection and feature-selection governance package is complete.
