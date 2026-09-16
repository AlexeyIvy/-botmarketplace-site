# SC001 — Next-Generation Multi-Asset Research Framework v0.2

Date: 2026-09-16  
Status: **WORKING RESEARCH ARCHITECTURE AFTER E008 MICROSTRUCTURE FORENSIC**  
Scope: **SCALPING RESEARCH / SC001 only**  
Supersedes: `sc001-next-generation-multi-asset-research-framework-v0.1.md`

This document defines the next research architecture for SC001 after E001-E008 and incorporates the completed E008 read-only postmortem plus deep microstructure forensic.

It does **not** reopen E001-E008, does not change their terminal verdicts, and does not authorize a new promotional strategy run by itself.

Independent branches remain firewalled: nothing in this framework may alter frozen rules, decisions or forward clocks for `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` or `Safe-Sleeve S002`.

Existing cross-project capital/discreteness constraints remain complementary:
`docs/research/cross-strategy-instrument-universe-and-capital-scalability-requirements-v0.1.md`.

---

## 1. Research objective

The objective is no longer to find a profitable BTC backtest. The objective is to identify a **repeatable economic mechanism** that survives:

- multiple instruments;
- independent time periods;
- historically correct exchange specifications;
- realistic execution uncertainty;
- regular-user fees and spread/depth costs;
- latency/cancellation stress;
- data-quality controls;
- cross-market dependence;
- multiple-testing controls;
- untouched Confirmation;
- forward/demo testing.

The central research question is:

> Under which observable market conditions does this mechanism have positive executable expectancy, and does that relationship replicate across independent markets and time?

---

## 2. Binding lessons from E001-E008

### E002

Classification remains:

**predictive microstructure feature; rejected standalone taker strategy.**

TFI may be reused only in a new experiment as an auxiliary filter, veto, ranker, execution-timing feature or meta-model input. It must not be silently revived as the same standalone taker strategy.

### E003

Rare Flow-Impulse Continuation remains terminal `E003_DISCOVERY_FAIL`. Primary gross continuation mechanism was negative. This family is low priority for strict replication unless new multi-asset evidence is sought under a separately frozen replication protocol.

### E004 / E005

Volatility Compression -> Breakout remains terminal `E004_DISCOVERY_FAIL`; observed gross economics were around zero to low-single-digit bps. E005 remains closed because the E004 prerequisite failed. E005 is not a standalone replication priority.

### E006

Same-Venue Spot/Perp Basis Convergence remains terminal `E006_DISCOVERY_FAIL`, classified as event-scarcity + insufficient-economics-headroom. Because event scarcity can be instrument-dependent, E006 is a meaningful **multi-asset replication candidate**, not a reopened E006.

### E007

Extreme 60s Displacement -> Partial Mean Reversion remains terminal `E007_DISCOVERY_FAIL`, but is the highest-priority legacy replication candidate because a moderate positive gross reversal effect was observed before robustness gates failed. Any future test must preserve the old frozen logic for strict replication and use a new experiment ID.

### E008

E008 remains terminal `E008_DISCOVERY_FAIL`.

First read-only postmortem:

- primary cycles = `2058`;
- forced-taker share ~= `99.514%`;
- mean realized fee drag ~= `6.9853 bps/cycle`;
- mean net edge ~= `-8.5296 bps/cycle`;
- mean gross edge already negative at roughly `-1.544 bps/cycle`;
- forced-cycle mean gross edge ~= `-1.547 bps`;
- maker-only cycles = `10` and their mean gross edge was also negative (~`-1.05 bps`);
- level-disappearance cancels = `15,740`;
- placement activations = `37,733`;
- semantic snapshots = `11,520`;
- semantic >5s gaps = `0`;
- same-ms zero-credit share of trade rows ~= `3.016%`.

Deep microstructure forensic then added:

- `prior-best disappearance events = 605,477` across the eight inspected BTC days;
- `snapshots = 11,520`, exactly consistent with `1,440/day` and therefore a strongly periodic one-per-minute pattern in these archives;
- primary cycle duration p50/p90/p99 ~= `60,632 / 61,732.3 / 64,098.45 ms`;
- primary gross-positive share ~= `39.456%`, so a majority of frozen cycles were gross-negative even before fees;
- long-first mean gross/net ~= `-1.655 / -8.640 bps`;
- short-first mean gross/net ~= `-1.426 / -8.412 bps`;
- forensic classification includes `MEAN_SPREAD_BELOW_MAKER_MAKER_FEE_FLOOR` and `SPREAD_RARELY_COVERS_4BPS_FEE_FLOOR`;
- forensic classification also includes material-model-risk flags for zero cancellation credit, all additions ahead, own-order omission from the exogenous book and periodic-snapshot cancellation semantics;
- `NEGATIVE_GROSS_EDGE_ROBUST_IN_FROZEN_RESULT` remains true;
- the forensic was read-only: strategy rerun = false and E008 terminal decision unchanged.

### E008 conclusion to carry forward

Two statements are simultaneously true and must not be conflated:

1. **The specific frozen E008 strategy is genuinely uneconomic on the inspected BTC data.** The quoted spread is structurally far below the regular-user maker-maker fee floor for almost all observed time, and the realized gross edge is negative for both sides and for the majority of cycles.
2. **The E008 passive-fill simulator is not a credible central FIFO estimator.** Its deliberately adversarial queue/reset semantics can substantially understate passive completion probability and overstate forced-exit frequency.

Therefore E008 is not reopened, but its execution model must not be reused unchanged as the central estimator for a new passive strategy family.

---

## 3. Systemic weaknesses future research must control

### 3.1 Data contamination / repeated-use bias

Once a date, instrument or output has been inspected and used to redesign a model, it is no longer untouched promotional evidence for that redesigned system.

Requirements:

- E008 BTC Discovery dates are permanently engineering/contaminated for future execution-model design;
- any date used to design execution semantics becomes engineering/calibration data;
- a redesigned model may not claim promotional validation on data used to design it;
- maintain a machine-readable `instrument × date × purpose` contamination registry;
- cross-asset data on the same calendar dates are not automatically independent because crypto markets share regime shocks.

### 3.2 Survivorship/look-ahead in instrument selection

Do not choose today's top coins for a historical test.

Universe selection must use only pre-period information such as trailing liquidity, history, contemporaneous listing state and data availability. Historically eligible delisted instruments must not be silently removed simply because they are inconvenient now.

### 3.3 Statistical dependence / pseudo-replication

Thousands of scalping cycles do not imply thousands of independent observations.

Required analysis units:

- instrument-day;
- day block;
- instrument block;
- equal-weight market summaries;
- concentration diagnostics;
- cluster-aware uncertainty.

A pooled cycle mean is descriptive, not sufficient evidence of robustness.

### 3.4 Multiple testing / research degrees of freedom

Every candidate/variant must enter a research ledger with:

- hypothesis;
- code hash;
- parameter hash;
- universe hash;
- date roles;
- number of variants tried;
- primary metric/gates;
- terminal decision.

For large families of variants, use a predeclared family-level robustness method appropriate to dependent returns rather than selecting the prettiest curve.

### 3.5 Numerical discreteness

Canonical execution state should use:

- integer price ticks;
- integer lot/contract units;
- exact historical `tickSz`, `lotSz`, `minSz`, `ctVal`;
- explicit linear/inverse PnL formulas.

Binary float may remain for analytics but not as the source of truth for order-state invariants.

### 3.6 Historical contract/fee/funding drift

Current exchange metadata is not proof of historical metadata.

Freeze per instrument and period:

- contract type;
- quote/settlement currency;
- tick/lot/min size;
- multiplier/contract value;
- historical fee basis;
- funding schedule;
- listing/spec changes.

### 3.7 Message-rate / operational feasibility

Historical execution may demand more order traffic than a real API account can sustain.

Measure:

- order/cancel/amend rate;
- peak request windows;
- duplicate cancel suppression;
- rate-limit headroom;
- local backlog;
- whether expected edge survives throttling.

### 3.8 Own-order overlay

Future passive engines must explicitly represent our resting order separately from the exogenous historical book.

Consequences:

- exogenous level disappearance does not delete our order;
- our order may keep a price level present;
- exogenous best can move while our order remains venue-best;
- own size and external queue-ahead must remain separate quantities.

### 3.9 Queue inference as uncertainty bounds

Aggregated L2 cannot recover exact FIFO. Use a predeclared model family rather than one falsely precise queue estimate:

1. **strict lower bound** — full initial queue ahead, no ambiguous credit, conservative cancellation treatment;
2. **central estimator** — calibrated only on engineering data with explicitly justified proportional/probabilistic queue reduction;
3. **upper-bound diagnostic** — generous queue depletion, used only as a plausibility envelope.

Promotion must not depend only on the optimistic bound.

Crucially, size **added after our order is already resting should not automatically be placed ahead of us** under normal price-time priority unless data provide evidence that it belongs ahead.

### 3.10 Exact-price versus price-through trade evidence

Distinguish:

- exact-price compatible trades;
- price-through prints;
- same-ms ambiguous events;
- unknown parent-order decomposition.

Do not assign an entire worse-price print as level-exact FIFO depletion at our price without a frozen causal rule.

### 3.11 Snapshot semantics

The E008 archives show exactly `1,440 snapshots/day`, strongly indicating periodic archival/full-state refresh behavior.

Therefore future engines must separate:

- feed snapshot/resynchronization;
- trust restoration;
- exogenous-book state replacement;
- own-order venue state.

A periodic data snapshot is not an automatic own-order cancellation.

### 3.12 Cross-feed causality

Trade and order-book feeds do not necessarily provide an exact total ordering.

Freeze rules for:

- equal timestamps;
- timestamp precision;
- sequence/checksum information when available;
- ambiguity windows;
- fail-closed handling.

### 3.13 Taker exits from executable opposite-side L2

Forced or intentional taker exits must sweep the correct opposite-side book at the causal execution timestamp, including depth and order quantity.

Do not use the next arbitrary public trade as the primary market-order proxy.

### 3.14 Post-only behavior

At activation time explicitly model post-only acceptance/rejection. Do not silently convert a marketable maker order into taker execution unless venue semantics explicitly require that behavior.

### 3.15 Latency components

Separate at least:

- market-data observation latency;
- local processing/decision latency;
- outbound placement latency;
- cancel/amend latency;
- forced-exit latency.

Promotion must survive predeclared latency stress rather than one favorable scalar constant.

### 3.16 Funding / position accounting

If a position can cross funding, funding must be included unless a frozen firewall truly guarantees no crossing. Multi-asset research must use instrument-specific funding schedules.

### 3.17 Hidden liquidity

Public L2 does not reveal all hidden/iceberg liquidity. Exact FIFO claims remain prohibited.

### 3.18 Cross-instrument sizing and capacity

One contract is not comparable across assets.

Freeze a prospective sizing rule in economic units, e.g. target USD notional rounded to valid lots and capped as a small fraction of contemporaneous displayed/estimated capacity.

Report capital-normalized economics and liquidity/capacity ratio.

### 3.19 Time-weighted market state

Economic-feasibility diagnostics must use time-weighted BBO state duration as a primary measure. Event-weighted metrics may be secondary diagnostics only.

### 3.20 Regime analysis and post-hoc filters

Volatility, trend, spread, depth, trade intensity, funding/basis and time-of-day may explain outcomes after the fact. They do not become tradable filters until frozen as a new experiment on untouched data.

### 3.21 Markout / adverse-selection decomposition

For maker research, fill probability alone is insufficient. Measure adverse-selection markout at predeclared horizons after maker fills/events, separated by side and market regime.

A high fill rate with consistently negative markout can still be economically toxic.

### 3.22 Order-to-trade and cancel-to-fill ratios

Measure how many placements/cancels are required per completed economically useful cycle. Extremely high churn is both an operational risk and a clue that the mechanism depends on unrealistic queue persistence.

### 3.23 Clock / time-origin consistency

Every feed and derived event must have an explicitly documented time origin: exchange event time, gateway receive time, archive generation time or reconstructed UTC. Never mix these as if they were identical.

### 3.24 Delisting/listing and structural breaks

A multi-asset universe must predeclare treatment of:

- new listings;
- delistings;
- contract migrations;
- symbol changes;
- fee/spec changes;
- exceptional maintenance/outage intervals.

Do not backfill today's stable universe into the past.

---

## 4. Default research pipeline

### Stage A — Economic hypothesis

Before heavy data work state:

- economic mechanism;
- why edge should exist;
- expected horizon;
- expected gross-edge scale;
- turnover;
- fee/execution burden;
- falsification conditions.

No strategy begins with parameter search for positive PnL.

### Stage B — Historical universe freeze

Default first-generation target: roughly **8-12 instruments**, initially within one comparable venue/product family.

Freeze universe from pre-period information only.

### Stage C — Chronology + contamination freeze

Separate:

1. engineering/calibration;
2. Discovery;
3. cross-asset replication or asset holdout;
4. chronological Confirmation;
5. forward/demo.

No Confirmation body access before freeze.

### Stage D — Data identity + semantic qualification

Require source identity, SHA/CRC, schema, timestamp/sequence integrity, full-day coverage, L2 book validity and explicit gap diagnostics before alpha.

### Stage E — Economic-feasibility gate

Before a full simulator, quantify whether the raw market opportunity can plausibly clear unavoidable costs.

For maker families measure at least:

- time-weighted spread distribution;
- share of time above maker-maker and maker-taker fee floors;
- depth/capacity;
- queue/churn diagnostics;
- adverse-selection markout envelope;
- event frequency.

For taker families measure gross signal scale versus round-trip fee + spread/depth.

If the raw opportunity is materially below unavoidable costs, terminate early.

### Stage F — Execution-engine validation

Required layers:

1. deterministic unit fixtures;
2. synthetic edge cases;
3. accounting/conservation invariants;
4. own-order overlay;
5. queue-bound scenarios;
6. post-only acceptance/rejection;
7. partial fills;
8. stale handling;
9. cancel/replace + rate-limit tests;
10. side-specific taker depth;
11. historical contract discreteness;
12. clock/causality tests;
13. replay determinism;
14. contaminated engineering-day mechanical replay.

No promotional PnL before implementation freeze + no-alpha identity gate.

### Stage G — One frozen Discovery

One predeclared implementation only. Report gross/net/cost decomposition, execution pathway, side breadth, day breadth, market breadth, concentration, capacity and stress results.

### Stage H — Multi-asset replication

No per-asset retuning unless a normalization formula was specified before outcomes.

Report:

- equal-weight market result;
- median market result;
- positive/active market share;
- worst quartile;
- top-market contribution;
- market-level gross/net distribution;
- instrument-day uncertainty;
- relation of effect to predeclared market characteristics.

### Stage I — Untouched chronological Confirmation

One shot. No tuning after body access.

### Stage J — Forward/demo

Compare live/forward signal, fill, latency, queue and cost behavior versus historical simulation.

---

## 5. Historical multi-asset universe design

Target first generation: roughly **10 instruments**, acceptable range `8-12` if historical eligibility or data constraints require it.

Do not select symbols from 2026 popularity for a 2024 test.

Preferred procedure:

1. choose venue/product family;
2. define pre-period lookback;
3. inventory all historically existing eligible instruments;
4. compute only pre-period liquidity/history/data-quality metadata;
5. enforce minimum history/spec availability;
6. stratify rather than select only tight-spread majors;
7. freeze symbols before promotional bodies/outcomes.

Suggested strata:

- Tier A: very high liquidity / tight spread;
- Tier B: high-medium liquidity;
- Tier C: medium liquidity / wider spread but still executable for small orders.

Exact symbols and thresholds are **not frozen by v0.2**. They require a metadata-only historical universe protocol first.

---

## 6. Statistical architecture

Always report both pooled and equal-weight market results.

Primary evidence hierarchy:

- instrument-day;
- day-block bootstrap/resampling;
- instrument-level sensitivity;
- market breadth;
- concentration limits;
- optional two-way/hierarchical clustering if frozen before analysis.

Do not let BTC or the busiest symbol dominate inference.

Every result must decompose:

`raw mechanism -> spread/depth -> fees/funding -> latency/execution -> net economics`.

---

## 7. Legacy Replication Program

Terminal verdicts E001-E008 remain immutable. Replications use new IDs.

### Priority 1 — E007 mechanism

Replicate the frozen displacement/reversal logic across the historical universe without per-asset retuning. Determine whether the retained gross reversal is broad or BTC-specific and whether it survives executable costs.

### Priority 2 — E006 mechanism

Replicate the same frozen spot/perp basis-convergence mechanism across eligible pairs. Do not loosen the trigger to manufacture sample size.

### Priority 3 — E002 TFI as auxiliary feature

Test only incremental value over a viable base strategy: veto, ranking, adverse-selection timing or exit timing. Compare `base` versus `base + TFI` on identical opportunities/costs.

### Priority 4 — E004 strict replication

Lower priority because gross headroom was weak, but useful if cross-asset evidence suggests the mechanism was BTC-specific.

### Priority 5 — E003 / E001

Low priority absent a concrete forensic reason to suspect material modeling distortion.

### E005

No independent priority while prerequisite remains failed.

### E008

No promotional rerun. Passive-maker research may return only as a **new family** with own-order overlay, corrected snapshot semantics, side-specific taker depth, fresh promotional data and explicit queue uncertainty bounds.

---

## 8. Research ledger / anti-overfitting

Maintain a machine-readable ledger containing for every candidate:

- experiment ID;
- parent mechanism;
- pre-outcome hypothesis;
- code/blob identity;
- parameter hash;
- universe hash;
- date sets by role;
- contamination status;
- variants tried;
- primary/secondary metrics;
- gates;
- terminal decision;
- whether future-stage data were viewed before freeze.

Any meaningful post-Discovery change creates a new experiment ID.

---

## 9. VPS/storage plan

Current VPS: `4 vCPU / 8 GB RAM / 80 GB NVMe`.

BTC E008 used about `3.725 GB` compressed L2 for eight days. Ten similarly sized markets would be roughly `37 GB` compressed L2 before existing project data, reports and temporary files.

Current VPS is adequate for initial sequential research if we:

- stream archives;
- run one/two heavy L2 jobs at most;
- preserve ~15-20 GB free reserve;
- download/process by batch;
- create compact derived artifacts;
- keep exact SHA identity;
- avoid deleting unique promotional raw data;
- expand storage toward `200-500 GB` if multi-asset L2 becomes permanent.

CPU is not yet the main bottleneck; data volume and research correctness are.

---

## 10. Generic feasibility questions before any new promotional engine

1. What is the unavoidable round-trip fee floor for the intended maker/taker path?
2. What raw spread/move is needed to clear fees plus a positive hurdle?
3. How often is that raw opportunity available in **time-weighted** terms?
4. Is event frequency sufficient for inference?
5. Can intended size execute within realistic depth?
6. Is turnover/rate-limit load feasible?
7. Is adverse selection measured rather than assumed?
8. Does the mechanism remain interesting under physically coherent conservative execution?
9. Is the effect broad across instruments/days rather than concentrated?
10. Are the tested data still genuinely untouched for this implementation?

---

## 11. Next concrete program after E008 forensic

Do **not** open a new strategy immediately.

Next sequence:

1. create historical universe selection protocol;
2. create machine-readable contamination registry;
3. perform metadata-only historical universe audit;
4. freeze first multi-asset universe;
5. define execution-model v2 engineering protocol;
6. validate execution v2 only on contaminated/engineering data;
7. freeze fresh Discovery/Confirmation chronology;
8. begin legacy strict replication with E007 first unless the universe/economic-feasibility audit provides a stronger reason to reorder priorities;
9. only after legacy replication decide which entirely new strategy family deserves promotional resources.

---

## 12. Core doctrine

1. **Economics before engineering.**
2. **Mechanism before parameter search.**
3. **Multi-asset before confidence.**
4. **Fresh data after redesign.**
5. **Execution as bounded uncertainty, not false precision.**
6. **Gross and costs separately.**
7. **Equal-weight markets plus pooled cycles.**
8. **Historical exchange reality.**
9. **Operational feasibility is part of execution.**
10. **No silent rescue.**
11. **Confirmation stays untouched.**
12. **Forward behavior must reconcile with simulated behavior.**

The goal is not to maximize PASS labels. The goal is to produce a small number of strategies whose economic mechanism, execution assumptions and statistical evidence are strong enough to survive skeptical review.