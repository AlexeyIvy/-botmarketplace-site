# SC001 — C1-C6 Feature / Indicator Inventory v0.1

Date: 2026-09-17  
Status: **NON-ALPHA IMPLEMENTATION OF ROADMAP v4.21 / NO NEW PROMOTIONAL OUTCOME**

Parent:
- `sc001-current-roadmap-and-stop-rules-v4.21.md`;
- `sc001-candidate-feasibility-card-template-v0.2.md`;
- `sc001-feature-indicator-research-governance-v0.1.md`.

This document narrows feature scope before sentinel design. It does not freeze final formulas/thresholds or authorize alpha.

General default: use the **minimum mechanism-defining feature stack**. Optional auxiliary features are not automatically included. Adding an auxiliary feature requires a separately stated incremental-value question and search-budget entry.

---

# C1 — E006R1 multi-asset spot/perpetual basis convergence

## Minimum core feature stack

### C1-F1 — spot/perp relative basis
- primitive: P8 relative value / derivative state;
- role: R1 core signal;
- raw inputs: synchronized same-venue spot and perpetual prices/trades;
- purpose: measure relative richness/cheapness between linked instruments.

### C1-F2 — causal ordinary-basis reference
- primitive: P8/P7;
- role: R6 reference/normalization;
- purpose: distinguish ordinary persistent basis from temporary dislocation.

## Required feasibility/execution state, not alpha augmentation

### C1-F3 — pair liquidity / spread / depth eligibility
- primitive: P6;
- role: R2/R5;
- purpose: cost/eligibility screening for both legs.

### C1-F4 — funding/borrow/contract state
- primitive: P8;
- role: R2/R4/R5;
- purpose: accounting/feasibility, not rescue signal.

## Optional auxiliary candidates

- volatility normalization P3: **not included by default**;
- flow confirmation P5: **not included by default**.

Any addition requires new incremental hypothesis and clean evidence.

## Prior evidence

Registry F003 basis-dislocation record applies. Old BTC profitability is not promotional evidence for E006R1.

## Initial feature budget

Minimum core only for sentinel. No auxiliary alpha filter in first sentinel.

---

# C2 — multi-minute deviation / VWAP-style mean reversion

## Minimum core feature stack

### C2-F1 — causal local reference price
- primitive: P7;
- role: R6;
- candidate representations for calibration only: VWAP or robust local center;
- final representation must be chosen/frozen inside budget before clean Discovery.

### C2-F2 — multi-minute price deviation from reference
- primitive: P1;
- role: R1 core signal;
- purpose: measure displacement from local center on S3 horizon.

## Optional auxiliary candidates

### C2-A1 — volatility scale
- primitive: P3;
- role: R6/R2;
- rationale: compare raw deviation versus volatility-adjusted deviation;
- status: optional controlled feature question, not default.

### C2-A2 — trend persistence veto
- primitive: P2;
- role: R3;
- rationale: persistent trends may invalidate short mean reversion;
- status: not allowed as post-hoc rescue; only pre-registered incremental test with opportunity-retention reporting.

## Deliberately excluded initially

- RSI/Stochastic/MACD bundles;
- multiple overlapping oscillators;
- E007/E009 60-second displacement rules.

## Prior evidence

Registry F004/F005/F007 are relevant limitations/reference evidence but do not prove or disprove this new H3 family.

## Initial feature budget

One reference representation + one deviation transform. At most one auxiliary family may be pre-registered for an incremental test after base definition; no combinatorial indicator search.

---

# C3 — 5m/10m continuation / volatility expansion

## Minimum core feature stack

### C3-F1 — multi-minute directional persistence / breakout state
- primitive: P2;
- role: R1 core signal;
- purpose: measure whether a completed multi-minute move/range break persists.

### C3-F2 — movement-scale / expansion state
- primitive: P3;
- role: R2 or R1 depending final mechanism;
- purpose: distinguish ordinary drift from unusual expansion.

Before clean Discovery, the experiment must decide whether P3 is core mechanism or only state; it cannot change role after outcomes.

## Optional auxiliary candidates

### C3-A1 — relative volume/activity
- primitive: P4;
- role: R2/R3;
- rationale: participation may distinguish meaningful breakout from noise;
- status: optional incremental test only.

### C3-A2 — flow confirmation
- primitive: P5;
- role: R3;
- status: not default; prior E002 information does not authorize automatic reuse.

## Deliberately excluded initially

- MACD/ADX/volume/flow stacks all at once;
- post-hoc time-of-day filters;
- direct reuse of E004 compression thresholds.

## Prior evidence

Registry F002 records that E004 strategy failed without isolating all volatility-state features.

## Initial feature budget

P2 + one explicitly defined P3 state/core transform. Maximum one auxiliary incremental family in the initial research batch.

---

# C4 — BTC/ETH -> alt lead/lag

## Minimum core feature stack

### C4-F1 — causal leader impulse
- primitive: P9 cross-asset information transfer;
- role: R1;
- raw inputs: synchronized BTC/ETH return/flow state available strictly before target-alt decision time.

### C4-F2 — target residual / common-market adjustment
- primitive: P9;
- role: R6;
- purpose: prevent ordinary simultaneous market beta from masquerading as lead/lag.

This residual/common-factor adjustment is part of mechanism identification, not an optional performance filter.

## Required causality state

### C4-F3 — cross-feed timestamp/alignment quality
- primitive: data/causality state;
- role: R5/R2;
- purpose: reject ambiguous timing rather than fabricate lead.

## Optional auxiliary candidates

- target volatility scale P3;
- target liquidity state P6.

Neither enters initial core alpha unless prospectively justified.

## Deliberately excluded initially

- selecting only alts that previously followed BTC profitably;
- trying many lags and reporting the historical best as clean evidence;
- using contemporaneous target return inside leader feature.

## Initial feature budget

One leader impulse definition, one predeclared lag family/budget in calibration, one common-factor adjustment. No multi-leader/lag ensemble in first experiment.

---

# C5 — large-trade / sweep / forced-flow exhaustion

## Minimum core feature stack

### C5-F1 — objective aggressive-flow event
- primitive: P5/P10;
- role: R1 event trigger;
- possible raw basis: large signed notional, clustered aggressive trades or objectively defined sweep-like trade activity;
- exact event definition must be frozen before promotional data.

### C5-F2 — post-event displacement / response state
- primitive: P1;
- role: R1/R6;
- purpose: distinguish continuation versus exhaustion question after event.

## Later execution/confirmation state if sentinel survives

### C5-F3 — book depth/depletion/replenishment
- primitive: P6/P10;
- role: R2/R5;
- status: defer L2 until cheap trade-only event-frequency/headroom sentinel survives.

## Optional auxiliary candidates

- short-horizon volatility state P3;
- broader market direction P2/P9.

Not included in first sentinel.

## Deliberately excluded initially

- manually hand-picked liquidation/news days;
- multiple large-trade thresholds selected by PnL;
- unverified third-party liquidation feeds.

## Initial feature budget

One objective event family + one response definition for sentinel. L2 features only after structural survival.

---

# C6 — cross-sectional short-horizon dispersion/reversion

## Minimum core feature stack

### C6-F1 — common-market factor / benchmark move
- primitive: P9;
- role: R6;
- purpose: separate market-wide crypto movement from relative asset movement.

### C6-F2 — cross-sectional residual/dislocation
- primitive: P9/P1;
- role: R1;
- purpose: rank relative over/under-movement within frozen liquid universe.

### C6-F3 — portfolio neutrality / hedge weights
- primitive: risk/accounting transform;
- role: R4/R6;
- purpose: control unintended directional beta.

## Required eligibility/execution state

### C6-F4 — contemporaneous liquidity/cost eligibility
- primitive: P6;
- role: R2/R5;
- purpose: prevent illiquid assets from driving apparent cross-sectional edge.

Eligibility rule must be frozen before performance and must not select historical winners.

## Optional auxiliary candidates

- volatility scaling P3 for comparability across assets;
- flow/liquidity interaction P5/P6.

Not included by default.

## Deliberately excluded initially

- winner/loser asset selection using E007R1/E009 outcomes;
- large portfolio of tuned factors;
- dynamic feature weighting optimized on promotional PnL.

## Initial feature budget

One common-factor model, one residual definition, one neutrality rule. Any volatility scaling is a pre-registered alternative/incremental question, not automatic.

---

# Cross-candidate conclusions

## 1. Classical indicators are not yet required

None of C1-C6 structurally requires RSI, MACD, ADX, Stochastic or Bollinger Bands by name.

If later considered, they must solve an explicit measurement problem and compete with simpler primitive-level features.

## 2. Feature complexity ordering

Simplest initial feature stacks appear structurally in C1/C2/C5; C3/C4/C6 require more interacting primitives to identify their mechanisms correctly. This is engineering complexity only, not expected-profit ranking.

## 3. Next step

For each C1-C6:

1. assign Selection/Calibration Sandbox data roles;
2. freeze allowed feature-parameter budget;
3. define one cheapest sentinel quantity and kill condition;
4. estimate MDE/block requirements;
5. only then decide which candidates are `ELIGIBLE_FOR_BATCH`.

No promotional PnL has been opened by this inventory stage.
