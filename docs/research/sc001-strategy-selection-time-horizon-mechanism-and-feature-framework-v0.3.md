# SC001 — Strategy Selection, Time-Horizon, Mechanism & Feature Research Framework v0.3

Date: 2026-09-17  
Status: **BINDING TOP-LEVEL GOVERNANCE BEFORE NEXT PROMOTIONAL ALPHA**  
Scope: `SCALPING RESEARCH / SC001`

Supersedes as top-level strategy-selection entry point:
`docs/research/sc001-strategy-selection-time-horizon-and-mechanism-framework-v0.2.md`

All controls in v0.2 remain binding unless explicitly strengthened here. Detailed companion documents are normative where referenced.

---

## 1. Starting state

All prior SC001 terminal decisions remain immutable.

- E001-E008 remain terminal/closed;
- E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`;
- E009 remains terminal `E009_GROSS_FEASIBILITY_FAIL`;
- E009 postmortem remains complete.

This framework is not a rescue path.

---

## 2. Two linked research objectives

Future SC001 work produces two different outputs:

### A. Strategy evidence

Find economically viable, causally executable mechanisms across diversified horizons, mechanisms, markets and execution archetypes.

### B. Feature / indicator evidence

Build an append-only empirical knowledge base about reusable market measurements/features, their roles, limitations, redundancy and incremental value.

The two outputs are related but must not be conflated.

A profitable strategy does not prove every feature inside it is useful. A failed strategy does not prove every feature inside it is useless.

---

## 3. Strategy-selection axes retained from v0.2

Every candidate must still be classified across:

- Signal Horizon;
- Position Horizon;
- mechanism family M1-M7;
- execution archetype T1-T4;
- risk signature;
- exact six-part time architecture;
- cost/fill structure;
- data/causality requirements;
- selection/calibration contamination;
- MDE/sample plan;
- cheapest sentinel falsification.

Under-covered H3/H4 regions are information gaps, not evidence of alpha.

---

## 4. New mandatory feature/indicator layer

Binding companion governance:

- `docs/research/sc001-feature-indicator-research-governance-v0.1.md`;
- `docs/research/sc001-feature-indicator-taxonomy-v0.1.md`;
- `docs/research/sc001-incremental-feature-testing-protocol-v0.1.md`;
- `docs/research/sc001-feature-evidence-registry-v0.1.md`.

Every future candidate uses the new:
`docs/research/sc001-candidate-feasibility-card-template-v0.2.md`.

Each candidate must include a Feature / Indicator Inventory before promotional alpha.

---

## 5. Three-role conclusions for feature research

### Financial / economic

An indicator is not an economic mechanism.

Feature research must ask:

- what market primitive is measured;
- why that primitive is relevant to the mechanism;
- whether it adds information/economic value after costs;
- whether it changes opportunity frequency, turnover, risk or capacity;
- whether a simpler feature captures the same information.

Do not conclude `RSI works`, `ATR works`, `VWAP works`, etc. Evidence must be scoped.

### Trader / programmer

Every feature is causal code and must have:

- formula/version;
- exact inputs;
- time-window semantics;
- bar-close availability rules;
- warm-up;
- missing-data policy;
- update cadence;
- lineage/reference implementation;
- golden tests before promotion where material.

Signal clock and execution clock remain separate.

### Mathematical / statistical

Feature exploration creates severe multiplicity.

Therefore:

- all variants/interactions count in the ledger;
- selection/calibration feature diagnostics contaminate that evidence period for the resulting implementation;
- related indicators are not independent discoveries;
- incremental tests use paired/block-aware inference where possible;
- filters must report opportunity retention and economics per base opportunity;
- custom composites require a predeclared complexity/interaction budget.

---

## 6. Feature roles

Every feature must declare one or more roles:

- R1 core signal;
- R2 state/regime;
- R3 filter/veto;
- R4 sizing/risk;
- R5 execution;
- R6 reference/normalization.

A feature can be useful in one role and useless in another.

---

## 7. Feature evidence is contextual, append-only and reusable only prospectively

Central registry:
`docs/research/sc001-feature-evidence-registry-v0.1.md`.

Evidence records are scoped by:

`feature/version × role × market × horizon × mechanism × chronology × execution/cost stage`.

No evidence record is deleted because later evidence disagrees.

Strong reusable feature claims require progressively cleaner evidence dimensions; one calibration/backtest result is not sufficient.

---

## 8. Classical and proprietary indicators

Classical tools such as RSI, MACD, ATR, ADX, Bollinger Bands, Stochastic and VWAP are allowed only through exact causal definitions and explicit roles.

Popularity is not evidence.

Custom/proprietary indicators are allowed when they solve a stated measurement problem and have:

- parent economic primitives;
- simpler comparator;
- exact formula;
- complexity budget;
- causal inputs;
- falsification rule;
- fresh evidence after design.

Do not optimize custom formulas directly against promotional PnL.

---

## 9. Feature discovery versus feature promotion

Selection/Calibration Sandbox may be used to:

- estimate rough feature distributions;
- evaluate redundancy;
- choose within a predeclared parameter budget;
- estimate event frequency/variance;
- form a custom feature hypothesis.

Anything used to choose the implementation is non-promotional for that implementation.

After selection, the feature/version is frozen before clean Discovery.

---

## 10. Incremental feature tests

When scientifically meaningful, use pre-registered:

`BASE` versus `BASE + FEATURE`.

Prefer identical underlying opportunities.

For filters and vetoes always report:

- base opportunities;
- retained/rejected opportunities;
- retention rate;
- economics per executed trade;
- economics per original base opportunity;
- turnover/cost impact;
- tail/risk impact.

If the feature materially changes the economic mechanism or opportunity definition, assign a new strategy experiment ID instead of calling it an incremental test.

---

## 11. Redundancy control

Feature taxonomy groups measurements by underlying economic primitive.

Do not treat many correlated oscillator/trend/volatility transforms as independent confirmations.

Calibration-only redundancy diagnostics may include:

- correlation/rank correlation;
- residual association;
- overlap of selected opportunities;
- nested incremental effect;
- simpler-vs-complex comparison.

Prefer simpler features when incremental information is economically immaterial.

---

## 12. Ordinary SC001 feature-complexity posture

Ordinary candidate experiments should use:

- one clearly defined economic mechanism;
- the minimum feature set required to represent that mechanism;
- a small predeclared auxiliary-feature budget;
- one-at-a-time incremental tests where possible.

High-dimensional feature selection / automated indicator combination belongs to a separate ML-feature program with nested blocked validation and larger untouched evidence reserves.

It must not be smuggled into ordinary SC001 as manual indicator shopping.

---

## 13. Legacy policy remains binding

Use:
`docs/research/sc001-legacy-retest-and-replication-policy-v0.1.md`.

Do not blanket-retest E001-E009 under the new feature framework.

Special retained cases remain:

- E002/Taker-flow evidence may be reused prospectively only as auxiliary information under a new experiment;
- E006R1 strict multi-asset basis replication remains scientifically justified subject to sentinel feasibility;
- E008 BTC same-rule maker is not reopened, though a new prospectively spread/fee-eligible maker universe may be a different future family;
- E007/E007R1/E009 direct reversal retests remain prohibited.

---

## 14. Updated end-to-end candidate process

### Stage 0 — Landscape and registry

Maintain:
- strategy landscape;
- feature taxonomy;
- feature evidence registry;
- contamination ledger.

### Stage 1 — Non-alpha candidate card

Use template v0.2.

Freeze:
- mechanism;
- horizons;
- execution;
- risk signature;
- Feature / Indicator Inventory;
- cost architecture;
- data needs;
- calibration budget.

### Stage 2 — Selection/Calibration Sandbox

Inspect only allowed non-promotional diagnostics.

Record all strategy/feature variants considered.

### Stage 3 — Cheapest sentinel falsification

Use minimum sufficient data and minimum feature set.

Kill structurally weak ideas early.

### Stage 4 — Research batch freeze

From sentinel survivors, prospectively freeze a small diversified batch across mechanisms/horizons/risk signatures.

Do not let the first result invent the next candidate.

### Stage 5 — Experiment and feature freeze

For each selected candidate freeze:
- exact feature code/formulas;
- feature roles;
- strategy parameters;
- universe;
- chronology;
- MDE/sample plan;
- cost/execution gates;
- optional pre-registered incremental feature tests.

### Stage 6 — Data semantics / kernel verification

Use minimal appropriate execution kernel and binding simulation/accounting standards.

### Stage 7 — One-shot Discovery

No outcome-driven feature redesign.

### Stage 8 — Asset holdout

No per-asset feature tuning.

### Stage 9 — Chronological Confirmation

Untouched time evidence only.

### Stage 10 — Forward/demo reconciliation

Verify live feature availability/timing, execution and cost behavior.

### Stage 11 — Append registry evidence

Add scoped strategy and feature evidence, including negative/redundant results.

---

## 15. Current candidate slate

Retain non-alpha slate:

- C1 E006R1 multi-asset spot/perp basis convergence;
- C2 multi-minute deviation/VWAP-style mean reversion;
- C3 5m/10m continuation/volatility expansion;
- C4 BTC/ETH -> alt lead/lag;
- C5 large-trade/sweep/forced-flow exhaustion;
- C6 cross-sectional short-horizon dispersion/reversion;
- C7 wider-spread maker as reserve/lower priority.

Before sentinel design, C1-C6 cards must now receive Feature / Indicator Inventory under template v0.2.

---

## 16. Current hard gate

**NO NEW PROMOTIONAL ALPHA YET.**

Allowed work:

1. bootstrap and review Feature Evidence Registry;
2. update C1-C6 with exact feature primitives/roles and minimal feature sets;
3. define Selection/Calibration Sandbox roles;
4. design one cheapest sentinel per candidate;
5. estimate prospective MDE/sample requirements without opening promotional outcomes;
6. freeze a diversified research batch only after structural feasibility review.

---

## 17. Principle

The goal is not to discover the best indicator.

The goal is to learn which **causally observable market measurements** add robust economic information, in what role, on what horizon and under what execution/cost constraints — and then use that knowledge prospectively to build simpler, stronger strategy mechanisms.
