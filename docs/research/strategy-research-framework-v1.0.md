# Strategy Research Framework v1.0

**Project:** BotMarketplace / botmarketplace.store  
**Status:** Active research process  
**Version:** 1.0  
**Purpose:** define a research-first process for discovering, falsifying, validating, forward-testing, and only then productionizing systematic trading strategies.

---

## 1. Core principle

BotMarketplace development is no longer driven primarily by adding platform capabilities in advance.

The default sequence is:

> **strategy research → exact specification → historical validation → out-of-sample / walk-forward → robustness & stress testing → forward paper/demo testing → platform gap analysis → productionization → tiny-capital live test**

BotMarketplace is not required to be the research engine during the early stages. A lightweight independent research environment may be used when it enables faster, clearer, and more auditable experiments.

A major platform capability should not be built merely because it might be useful later. It should be justified by either:

1. a strategy that has passed substantial validation; or
2. a concrete research experiment that cannot be performed honestly without that capability.

Negative research results are valid and valuable outcomes.

---

## 2. What counts as a testable strategy

A strategy is not ready for testing if it is described only by discretionary phrases such as “buy in a strong trend” or “increase hedge when volatility is high”.

A Research Candidate must define, at minimum:

- economic hypothesis;
- universe;
- instruments;
- timeframe / decision frequency;
- data inputs;
- signal definitions;
- exact entry rules;
- exact exit rules;
- position sizing;
- portfolio constraints;
- rebalancing rules;
- execution timing;
- fees;
- spreads;
- slippage;
- funding / carry assumptions where applicable;
- risk limits;
- allowed research parameters;
- benchmarks;
- acceptance criteria;
- rejection criteria.

If two independent implementations could interpret the rules differently, the specification is not yet precise enough.

---

## 3. Strategy lifecycle

Each strategy moves through explicit states:

> **Idea → Research Candidate → Historical Validation → OOS Candidate → Forward Candidate → Production Candidate → Live Strategy**

Most ideas are expected to fail before reaching production. A research process in which almost every candidate passes should be treated as suspicious.

---

## 4. Stage 0 — Idea Intake

For every idea record four items before implementation.

### 4.1 Economic edge

Why should the strategy have positive expected geometric and/or risk-adjusted value?

### 4.2 Who pays the edge?

Identify the economic counterparty or structural reason, for example:

- demand for leverage;
- behavioural trend persistence;
- liquidity premium;
- risk-transfer premium;
- crash-insurance premium;
- institutional constraints.

### 4.3 Why may the edge persist?

Record structural, behavioural, operational, or regulatory reasons that could make the opportunity durable.

### 4.4 Falsification hypothesis

State explicitly what observations would make the hypothesis false.

---

## 5. Stage 1 — Research Specification

Create a versioned specification before evaluating final performance.

Suggested naming:

- `R001-antifragile-convex-barbell.md`
- `R002-btc-trend-following.md`
- etc.

Once a specification is tested, material changes create a new version rather than silently changing the old experiment.

This is intended to reduce hidden curve fitting and hindsight-driven rule changes.

---

## 6. Stage 2 — Data Audit

No backtest is considered reliable until its data has been audited.

Required checks:

- provenance;
- date coverage;
- time resolution;
- missing periods / gaps;
- duplicate observations;
- timestamp semantics;
- event time vs data-availability time;
- delisted / inactive instruments;
- historical instrument availability;
- survivorship bias;
- stale or reconstructed data;
- venue-specific settlement and funding conventions.

For derivatives, additional historical metadata may include:

- funding timestamps;
- futures expiry and basis;
- option strikes and expiries;
- bid / ask;
- implied volatility;
- Greeks;
- open interest;
- volume;
- settlement rules.

---

## 7. Independent research environment

Early research may use a lightweight environment separate from BotMarketplace production infrastructure.

A possible structure:

```text
strategy-research/
  data/
  strategies/
  experiments/
  backtests/
  metrics/
  notebooks/
  reports/
```

A practical initial stack may use Python with transparent research-oriented tooling such as:

- pandas or polars;
- numpy;
- scipy;
- statsmodels;
- parquet;
- duckdb;
- matplotlib.

The priority is auditability and correctness, not building a universal framework prematurely.

---

## 8. Backtesting modes

Two broad simulator types may be used depending on the candidate.

### 8.1 Vectorized research

Suitable for relatively simple strategies such as:

- trend following;
- momentum;
- mean reversion;
- simple asset allocation;
- volatility targeting.

### 8.2 Event-driven research

Required when execution and state interactions matter materially, for example:

- options;
- funding;
- multiple instruments;
- expiries;
- multi-leg portfolios;
- margin;
- partial fills;
- order lifecycle.

Do not build a universal event-driven engine before a concrete strategy requires it.

---

## 9. Stage 3 — Naive Historical Backtest

The first backtest is a sanity filter, not proof of profitability.

Its purpose is to answer:

> **Does the strategy have enough economic promise to justify a more expensive validation process?**

If the strategy is already structurally poor under basic but honest assumptions, stop early.

---

## 10. Stage 4 — Realistic Cost Backtest

Performance must be decomposed after including applicable costs:

```text
Gross strategy return
- trading fees
- bid/ask spread
- slippage
- funding
- borrow / financing
- option premium burn
- other execution costs
= net strategy return
```

A strategy that works only before costs is not a viable strategy.

---

## 11. Stage 5 — Benchmarks

No strategy is evaluated in isolation.

Benchmarks must include simpler alternatives that reproduce as much of the candidate's economic exposure as possible.

Examples include:

- cash / stable reserve;
- BTC HODL;
- simple BTC/cash portfolios;
- periodic rebalancing;
- volatility-targeted BTC;
- trend-filtered BTC;
- strategy without a complex overlay;
- put-only vs put+call variants for convexity research.

The key question is not only whether the candidate makes money, but whether each added component improves the result relative to a simpler alternative.

---

## 12. Ablation testing

Complex strategies must be decomposed into incremental versions.

For example:

```text
A: cash / carry
A+B: cash / carry + BTC directional
A+B+C-put
A+B+C-put+C-call
A+B+C + option ladder
A+B+C + volatility regime logic
```

Every added mechanism must justify its complexity through measurable incremental value.

---

## 13. Stage 6 — Train / Validation / Test

Do not optimize parameters on the same full period used to report final performance.

Preferred approaches:

### Fixed split

- Train: coarse parameter exploration;
- Validation: select among reasonable variants;
- Test: untouched until final evaluation.

### Walk-forward

Repeated sequence:

```text
Train → Validation → unseen Test
shift forward
Train → Validation → unseen Test
...
```

Final claims should rely primarily on the concatenated unseen test periods rather than in-sample results.

---

## 14. Parameter robustness

The objective is not to find one magical optimum.

A credible strategy should show a reasonably broad region of acceptable nearby parameters.

Good example:

```text
10Δ options → works
15Δ options → works
20Δ options → works
```

Suspicious example:

```text
14.7Δ → excellent
nearby values → poor
```

The same rule applies to lookbacks, holding periods, DTE, roll timing, allocation weights, volatility thresholds, and other parameters.

---

## 15. Limit parameter searches

Do not run massive combinatorial optimization at the beginning.

Research sequence:

1. choose coarse economically justified values;
2. remove weak concepts;
3. perform limited robustness sweeps around survivors;
4. freeze the rule set;
5. evaluate out of sample.

---

## 16. Stage 7 — Statistical diagnostics

Minimum common metrics:

### Return

- total return;
- CAGR;
- geometric mean return.

### Risk

- annualized volatility;
- maximum drawdown;
- drawdown duration;
- recovery time;
- VaR;
- CVaR / Expected Shortfall.

### Risk-adjusted

- Sharpe;
- Sortino;
- Calmar;
- Omega.

### Distribution

- skewness;
- kurtosis;
- worst day;
- worst week;
- worst month.

### Portfolio behaviour

- upside capture;
- downside capture;
- turnover;
- exposure;
- beta.

### Strategy-specific

Examples:

- funding contribution;
- basis contribution;
- option premium burn;
- option payout / premium;
- crisis alpha;
- convexity / tail metrics.

---

## 17. Stage 8 — Bootstrap / Monte Carlo

Monte Carlo is a robustness and stress tool, not the primary proof of edge.

Avoid relying on iid Gaussian returns as the main evidence for a crypto strategy.

Preferred approaches include:

- historical block bootstrap;
- regime-aware bootstrap;
- volatility-cluster-aware simulation;
- optional jump / stochastic-volatility models where justified.

Monte Carlo assumptions and survival conditioning must be explicit.

---

## 18. Stage 9 — Stress testing

Each candidate must survive deliberately adverse assumptions.

Examples:

- fees ×2;
- spreads ×2 or more;
- slippage ×3;
- execution delay;
- missed signals;
- worse funding;
- funding sign reversal;
- liquidity degradation;
- data gaps;
- exchange outage;
- failed hedge leg;
- stablecoin depeg;
- combined crisis scenarios.

A useful robustness question is:

> **If our assumptions are wrong in an adverse direction, does the economic edge still exist?**

---

## 19. Stage 10 — Event studies

Study performance across market regimes and tail events rather than relying only on full-period averages.

Event windows should preferably be defined mechanically using rules such as:

- worst return percentiles;
- best return percentiles;
- volatility percentiles;
- drawdown acceleration;
- extreme funding;
- extreme IV.

Named historical events may then be used for interpretation, including major crypto crashes, leverage flushes, exchange failures, strong upside squeezes, low-volatility compression, and speculative funding regimes.

Named events must not be hand-selected to optimize reported performance.

---

## 20. Strategy scorecard

Every candidate receives the same decision-oriented scorecard.

Example categories:

| Category | Evaluation |
|---|---|
| Economic rationale | A–F |
| Gross edge | A–F |
| Net edge | A–F |
| OOS stability | A–F |
| Parameter robustness | A–F |
| Tail behaviour | A–F |
| Capacity | A–F |
| Execution complexity | A–F |
| Data reliability | A–F |
| Operational risk | A–F |

Final research decision:

- **PASS**
- **REDESIGN**
- **FAIL**

A high CAGR alone is never sufficient for PASS.

---

## 21. Stage 11 — Forward paper test

Historical PASS is followed by a live-data forward test with frozen strategy rules and no real capital.

Record at minimum:

```text
timestamp
signal
expected action
theoretical / executable fill
actual bid/ask where available
position
NAV
reason for action
```

The goal is to validate both the strategy and the realism of historical execution assumptions.

Forward test duration should be based on the number of relevant decisions, trades, market regimes, funding cycles, or option rolls — not on an arbitrary number of calendar days.

---

## 22. Shadow execution

Before demo trading, a strategy may run in shadow mode:

- consume live market data;
- generate intended orders;
- record them;
- send nothing to the exchange.

This helps detect:

- data latency;
- timezone errors;
- signal discrepancies;
- instrument-selection mistakes;
- pricing discrepancies;
- state-management bugs.

---

## 23. Stage 12 — Demo account

Demo testing is primarily an operational validation stage.

It tests:

- order lifecycle;
- API integration;
- fills;
- reconciliation;
- funding accounting;
- portfolio state;
- restart recovery;
- exchange errors.

Short-term demo P&L is not considered strong statistical evidence of edge.

---

## 24. Platform gap analysis

Only after a strategy passes substantial historical and forward validation do we ask:

> **What does BotMarketplace need in order to reproduce and execute this strategy correctly?**

Existing capabilities are reused where possible. Missing capabilities are added only when justified by the validated strategy or required experiment.

This is the transition from research to product development.

---

## 25. Production equivalence

Before live use, demonstrate that:

> **Research implementation ≈ production implementation**

On the same market data, both should make materially identical decisions under the same strategy specification.

This prevents researching one strategy and accidentally deploying another.

---

## 26. Tiny-capital live test

The first real-money phase exists primarily to validate execution assumptions, not to maximize profit.

Compare expected vs realised:

- spread;
- slippage;
- fees;
- funding;
- fills;
- latency;
- reconciliation;
- operational incidents.

Capital should increase only after sufficient live evidence.

Example staged scaling:

```text
0.1× target capital
→ 0.25×
→ 0.5×
→ 1.0×
```

---

## 27. Kill / redesign criteria

A live or forward strategy returns to research if predefined failure conditions occur, for example:

- drawdown exceeds the validated stress envelope;
- realised costs materially exceed assumptions;
- signal distribution changes structurally;
- funding or basis edge disappears;
- option premium regime changes materially;
- exchange mechanics change;
- repeated operational failures occur.

Strategies are not defended indefinitely after the original edge disappears.

---

## 28. Research registry

Maintain a registry of all candidates, including failures.

Initial registry:

| ID | Strategy | Initial Status | Role |
|---|---|---|---|
| **R001** | **Antifragile Convex Barbell** | Specification / primary research candidate | First primary candidate |
| **R002** | **BTC Trend Following / Time-Series Momentum** | Planned control candidate | Research-pipeline control and benchmark strategy |
| R003 | Funding / Basis Carry | Idea | Independent carry candidate |
| R004 | IV-RV / Volatility Risk Premium | Idea | Options/volatility candidate |
| R005 | Breakout + Volatility Expansion | Idea | Directional candidate |
| R006 | Cross-Timeframe Regime Strategy | Idea | Regime candidate |
| R007 | Regime-Filtered Mean Reversion | Idea | Mean-reversion candidate |

The registry does **not** mean all candidates are researched simultaneously.

Current sequencing is:

1. **R001 Antifragile Convex Barbell is the first primary strategy being investigated.**
2. **R002 BTC Trend Following is introduced early as a simpler control strategy for validating the research pipeline and as a benchmark, not as a replacement for R001.**
3. Other candidates remain queued until there is a reason to promote them.

---

## 29. Experiment registry

Every material test should receive an experiment ID, for example:

```text
R001-E001
R001-E002
R002-E001
```

Store:

- strategy version;
- data version;
- parameter set;
- code commit / notebook version;
- execution assumptions;
- experiment date;
- results;
- decision;
- notes.

This makes research reproducible and reduces accidental selective reporting.

---

## 30. Research integrity rules

1. Do not change strategy rules after seeing the final test period without creating a new version.
2. Do not remove bad historical periods without an objective pre-defined reason.
3. Do not report gross returns as if they were net returns.
4. Do not compare a complex strategy only with BTC HODL.
5. Do not select one isolated best parameter combination as evidence of robustness.
6. Do not treat Monte Carlo output as proof of real-world edge.
7. Do not use future-known information.
8. Do not ignore delisted, inactive, or historically unavailable instruments.
9. Do not treat short-term demo profit as proof of profitability.
10. Treat a negative result as a successful research outcome when it prevents wasted capital or engineering effort.

---

## 31. Initial research order

### Primary Track — R001 Antifragile Convex Barbell

This remains the first main research candidate because:

- substantial source material already exists;
- major conceptual and modelling flaws have already been identified;
- the economic idea of separating capital preservation, directional growth, and convexity is worth falsifying rigorously;
- the candidate provides a demanding test of portfolio, carry, and derivatives research methods.

The objective is **not** to prove the old 80/15/5 construction. The objective is to test whether a redesigned convex barbell has economically meaningful out-of-sample value.

### Early Control Track — R002 BTC Trend Following

R002 is intentionally simpler.

Its purpose is to validate the research pipeline itself using a strategy that requires much less data and simulation complexity.

It helps determine whether failures in R001 arise from:

- strategy economics;
- options data;
- portfolio simulation;
- or errors in the research infrastructure.

R002 may also become an independent production candidate if it performs well, but it does not replace R001 as the first primary research hypothesis.

### Later candidates

Funding/Basis Carry and other candidates remain in the registry and can be promoted after the first research pipeline is operating reliably.

---

## 32. Immediate next steps

1. Freeze this Research Framework v1.0.
2. Create and maintain the Research Candidate Registry.
3. Write **R001 — Antifragile Convex Barbell: Experiment Plan v1.0**.
4. Define exact datasets and especially historical BTC options-chain requirements.
5. Build the smallest independent research harness needed for reproducible experiments.
6. Use **R002 BTC Trend Following** as an early control test of data, execution timing, cost accounting, walk-forward, metrics, and robustness machinery.
7. Run R001 historical and ablation experiments.
8. Promote only surviving variants to forward testing.
9. Perform BotMarketplace gap analysis only for validated candidates.
10. Productionize only after research and forward evidence justify doing so.

---

## 33. Project philosophy

> **BotMarketplace becomes a consequence of validated strategies; strategies do not become a consequence of BotMarketplace capabilities.**

The central development question is therefore:

> **What edge are we trying to prove, what evidence would falsify it, and what is the minimum infrastructure required to test and execute it honestly?**
