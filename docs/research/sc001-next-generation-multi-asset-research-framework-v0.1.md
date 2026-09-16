# SC001 — Next-Generation Multi-Asset Research Framework v0.1

Date: 2026-09-16  
Status: **DRAFT BEFORE E008 MICROSTRUCTURE FORENSIC COMPLETION**  
Scope: **SCALPING RESEARCH / SC001 only**

This document defines the next research architecture for SC001 after E001-E008. It is intentionally created before the current E008 deep microstructure forensic is complete, so that new forensic facts can later be incorporated explicitly rather than reconstructed from chat memory.

It does **not** reopen E001-E008, does not change their terminal verdicts, and does not authorize any new promotional strategy run by itself.

Independent branches remain firewalled: nothing in this framework may alter frozen rules, decisions or forward clocks for `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` or `Safe-Sleeve S002`.

Existing cross-project capital/discreteness constraints remain complementary:
`docs/research/cross-strategy-instrument-universe-and-capital-scalability-requirements-v0.1.md`.

---

## 1. Why SC001 needs a new research architecture

E001-E008 produced useful scientific information, but the sequence exposed several weaknesses in how a microstructure strategy can be researched if one market, one execution model and one pooled statistic are treated as sufficient evidence.

The new objective is not merely to find a profitable BTC backtest. The objective is to identify a **repeatable economic mechanism** that survives:

- multiple instruments;
- independent time periods;
- historically correct exchange specifications;
- realistic execution uncertainty;
- regular-user fees and spread/depth costs;
- latency/cancellation stress;
- data-quality controls;
- cross-market dependence;
- multiple-testing controls;
- untouched confirmation;
- forward testing.

The central research question changes from:

> "Does this strategy work on BTC?"

into:

> "Under which observable market conditions does this mechanism have positive executable expectancy, and does that relationship replicate across independent markets and time?"

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

Same-Venue Spot/Perp Basis Convergence remains terminal `E006_DISCOVERY_FAIL`, classified as event-scarcity + insufficient-economics-headroom. One observed pair had material gross edge, but breadth/sample/latency gates failed. Because event scarcity can be strongly instrument-dependent, E006 is a meaningful **multi-asset replication candidate**, not a reopened E006.

### E007

Extreme 60s Displacement -> Partial Mean Reversion remains terminal `E007_DISCOVERY_FAIL`, but is the highest-priority legacy replication candidate because a moderate positive gross reversal effect was observed before robustness gates failed. Any future test must preserve the old frozen logic for strict replication and must be labeled a new replication experiment rather than E007 rescue.

### E008

E008 remains terminal `E008_DISCOVERY_FAIL`.

The first read-only postmortem found:

- 2058 completed primary cycles;
- ~99.51% forced-taker share;
- mean realized fee drag ~6.985 bps/cycle;
- mean net edge ~-8.530 bps/cycle;
- mean gross edge already negative at roughly -1.544 bps/cycle;
- maker-only cycles were also negative on average;
- 15,740 level-disappearance cancels;
- 37,733 placement activations;
- 11,520 semantic snapshots;
- no >5s gaps in the eight semantic-qualified Discovery days.

Therefore E008 shows two things can be true at once:

1. the specific frozen passive-maker strategy can be genuinely uneconomic;
2. the frozen queue/execution simulator can also be too pessimistic to estimate real passive fill probability as a central point estimate.

E008 itself must never be rerun for promotion or rescue-tuned.

---

## 3. Newly identified systemic weaknesses that future research must control

This section is intentionally broader than the current E008 forensic.

### 3.1 Data contamination / repeated-use bias

Once a date, instrument or output has been inspected and used to redesign the model, that data is no longer untouched promotional evidence for the redesigned system.

Therefore:

- E008 Discovery dates are now **contaminated for future strategy development on BTC** because their outcomes and microstructure are being studied in detail;
- any date used to design execution semantics becomes engineering/calibration data for that implementation;
- a new execution model must not claim a new promotional PASS by rerunning on the same data used to design it;
- future research must maintain a contamination registry covering `instrument × date × purpose`.

Cross-asset data on the same calendar dates may still carry shared regime information with BTC. It must not automatically be called fully independent simply because the symbol differs.

### 3.2 Survivorship and look-ahead in instrument selection

Choosing "today's top 10 coins" to test a 2024 strategy introduces survivorship/look-ahead bias.

A future universe must be frozen using information available **before the tested period**, for example trailing pre-period liquidity/turnover/history requirements. If a historically eligible instrument later delisted, it must not be silently excluded solely because it is inconvenient today.

### 3.3 Pooling thousands of cycles does not create thousands of independent observations

Scalping cycles on the same day and across highly correlated crypto markets share common shocks.

Therefore pooled trade/cycle statistics must not be the only inferential basis. Future statistical units must include:

- instrument-day;
- day blocks;
- instrument blocks;
- equal-weight market summaries;
- concentration diagnostics.

A strategy with 50,000 cycles but only two profitable markets is not robust merely because a pooled standard error is small.

### 3.4 Multiple testing / research degrees of freedom

After many strategies, thresholds, horizons, markets and execution assumptions, false discoveries become increasingly likely.

Future work must record every candidate/variant in a research ledger and predeclare:

- maximum tuning budget;
- parameter grid/range;
- primary metric;
- promotion gate;
- which data are calibration, Discovery and Confirmation.

If a large family of variants is compared, use a family-level robustness procedure such as block-resampled reality-check / SPA-style comparison or another predeclared multiple-testing control appropriate to dependent returns. Do not pick the prettiest curve without accounting for the search process.

### 3.5 Numerical representation

Future microstructure engines should avoid binary floating-point as the canonical representation of exchange discreteness where possible.

Prefer:

- integer price ticks;
- integer lot/contract units;
- exact `tickSz`, `lotSz`, `minSz`, `ctVal` transformations;
- explicit linear/inverse contract PnL formulas.

Floating-point may be used for derived analytics, but order-state invariants should be based on discrete exchange units.

### 3.6 Historical contract specification drift

Current exchange metadata is not proof of historical metadata.

Before any promotional run freeze, for every instrument and tested period:

- contract type;
- quote/settlement currency;
- `tickSz`;
- `lotSz`;
- `minSz`;
- `ctVal` / multiplier;
- listing status and relevant spec changes;
- historical fee basis/assumption;
- funding schedule when applicable.

Any spec change during a test window must be modeled explicitly or the period must be handled under a predeclared rule.

### 3.7 Exchange message-rate / operational feasibility

A historical simulator can generate cancellation/requote churn that a real API account could not sustain.

Future execution tests must measure:

- new-order request rate;
- cancel request rate;
- amend request rate if used;
- peak requests per second/window;
- duplicate cancel suppression;
- exchange rate-limit headroom;
- local backlog if desired messages exceed allowed throughput.

A strategy that is profitable only with operationally impossible order traffic fails implementation feasibility.

### 3.8 Own-order state versus exogenous historical book

The historical exchange book does not contain our hypothetical order. A future passive engine must maintain an explicit own-order overlay.

Consequences:

- exogenous disappearance of all historical size at our price does not automatically mean our order disappeared;
- our own resting order can keep a price level present;
- exogenous best bid/ask can move while our own resting quote may still be venue-best;
- own size should not be confused with external queue-ahead.

### 3.9 Queue inference without market-by-order data

With aggregated L2, exact FIFO cannot be reconstructed. Future passive research should treat queue position as **uncertainty/bounds**, not a falsely precise number.

Candidate architecture to freeze later:

1. **strict lower-bound model** — full initial displayed queue ahead; no cancellation credit; same-ms ambiguity zero; later identifiable additions do not automatically jump ahead of an already-resting order;
2. **central estimator** — predeclared probabilistic/proportional queue-ahead reduction from observed same-price size decreases, calibrated only on engineering data;
3. **upper-bound diagnostic** — generous cancellation-ahead assumptions used only to show the maximum plausible fill envelope.

Promotion must not depend only on the optimistic bound. Exact rules will be frozen only after current forensics and before new promotional outcomes.

### 3.10 Price-through trades and FIFO evidence

A trade print at a worse price is not automatically level-exact executed volume at our hypothetical resting level. Future queue credit must distinguish:

- exact-price compatible trades;
- price-through evidence;
- same-ms ambiguous events;
- unknown decomposition of one aggressive parent order into multiple prints.

No full trade quantity should be casually assigned to queue depletion at another price without a predeclared causal rule.

### 3.11 Snapshot semantics

A data-feed snapshot is state/resynchronization information, not by itself an exchange cancellation of our order.

Future engines must separate:

- local trust restoration;
- reconstructed exogenous state replacement;
- actual own-order cancellation state.

A stale-data safety policy may legitimately submit a cancel, but the reason must be the policy/latency path, not merely the existence of a later snapshot record.

### 3.12 Cross-feed causality

Trade timestamps and book timestamps are not guaranteed to provide exact total ordering across separate feeds.

Future engines need a frozen policy for:

- equal timestamps;
- timestamp precision;
- possible feed-generation versus trade-event timing;
- sequence/checksum information when available;
- conservative ambiguity handling.

### 3.13 Taker exits must use executable book depth

Forced or intentional taker executions should use the opposite side of the reconstructed book at the causal execution timestamp, including depth sweep and order size.

Do not use an arbitrary next public trade as the primary market-order execution proxy in future engines.

### 3.14 Post-only semantics / marketability

A future maker simulator must explicitly model post-only order acceptance/rejection at activation time. A would-be marketable maker order must not be converted silently into a taker fill unless the venue/order type actually specifies that behavior.

### 3.15 Latency is not one number

Future work must separate at least:

- market-data observation latency assumption;
- local decision/processing latency;
- outbound placement latency;
- cancel/amend latency;
- forced-exit latency.

A deterministic primary value may still be used, but promotion must survive predeclared stress and should not rely on a single favorable constant.

### 3.16 Funding and position-state accounting

If a strategy can hold through a funding timestamp, funding must be included rather than avoided by assumption unless a frozen firewall guarantees no crossing. Multi-asset research must also handle instrument-specific funding schedules.

### 3.17 Hidden liquidity / non-displayed orders

Aggregated public L2 cannot reveal all hidden/iceberg liquidity. This is another reason exact FIFO claims are prohibited. Queue uncertainty must remain explicit.

### 3.18 Capacity and order-size normalization across instruments

"One contract" is not economically equivalent across instruments.

Future multi-asset tests must freeze a sizing rule based on historical contract specs, for example a target USD notional rounded to valid lots and additionally capped as a small fraction of displayed liquidity. The exact rule must be prospective.

Report both:

- capital-normalized economics;
- liquidity/capacity ratio.

### 3.19 Spread measurement must be time-weighted

Event-weighted spread overweights high-message periods. Market-feasibility diagnostics should use time-weighted BBO state durations and also report event-weighted diagnostics separately when useful.

### 3.20 Regime analysis must not become post-hoc cherry-picking

Volatility, spread, trend, depth, trade intensity, funding/basis and time-of-day can be useful explanatory variables.

But after seeing outcomes they may only be descriptive. A regime filter becomes a tradable rule only in a **new frozen experiment** tested on untouched data.

---

## 4. New default research pipeline

Every future SC001 strategy should move through the following order unless a written protocol explains why a stage is irrelevant.

### Stage A — Hypothesis statement

Before heavy data work, state:

- economic mechanism;
- why an edge should exist;
- expected holding horizon;
- expected gross-edge scale;
- expected turnover;
- likely fee/execution burden;
- conditions that would falsify the hypothesis.

No strategy should begin with "search parameters until PnL is positive".

### Stage B — Historical universe freeze

Freeze an objective multi-asset universe, normally about **8-12 instruments** for the first generation of cross-market work.

The initial design target is one venue/product family where execution semantics are comparable, e.g. OKX linear perpetuals, before cross-venue replication.

Universe selection must use only pre-period information and should include minimum requirements for:

- trading history before the test start;
- contemporaneous turnover/trade count;
- data availability/quality;
- contract-spec availability;
- sufficient book liquidity;
- no silent survivorship substitution.

Prefer a stratified universe containing highly liquid majors plus medium-liquidity markets, rather than only the very largest current tokens.

Exact symbols and selection thresholds are **not frozen by v0.1** and must be fixed after the current forensic and a metadata-only universe audit.

### Stage C — Chronology and contamination freeze

For each new family define disjoint roles:

1. engineering/calibration;
2. Discovery;
3. cross-asset replication or asset holdout;
4. chronological Confirmation;
5. forward/demo.

Maintain a machine-readable contamination registry. No body/outcome from Confirmation may be opened early.

Because many SC001 BTC dates have already been inspected, future promotional dates should preferentially be genuinely fresh time blocks.

### Stage D — Data identity and semantic qualification

Before alpha/economics:

- source URL/filename/size/SHA256 freeze;
- archive CRC/member validation;
- header/schema validation;
- UTC coverage;
- timestamp monotonicity;
- trade-ID/sequence integrity when available;
- L2 snapshot/update semantics;
- book non-crossing/non-empty checks;
- minute/time coverage;
- duplicate/missing-level rules;
- explicit gap diagnostics.

Any date substitution rule for objectively unavailable/corrupt data must be predeclared before promotional bodies are opened.

### Stage E — Market economic-feasibility gate before full strategy simulation

This is a major change learned from E002/E004/E008.

Before spending large compute on an execution engine, measure whether the market offers enough raw economic room.

Depending on the candidate, measure prospectively relevant quantities such as:

- time-weighted spread distribution;
- fee floors for expected maker/taker path;
- expected gross signal move versus fees;
- top-of-book/depth capacity;
- event frequency;
- turnover;
- funding/basis scale;
- queue turnover/churn;
- adverse markout after comparable market events.

If the raw opportunity is an order of magnitude below unavoidable costs, terminate early rather than engineer an elaborate simulator.

### Stage F — Execution-engine validation before alpha

Required layers:

1. deterministic unit fixtures;
2. synthetic edge cases;
3. accounting/conservation invariants;
4. own-order overlay tests;
5. queue-bound tests;
6. post-only rejection tests;
7. partial-fill tests;
8. stale-data tests;
9. cancel/replace and rate-limit tests;
10. side-specific taker depth tests;
11. historical contract-discreteness tests;
12. replay determinism / identity tests;
13. contaminated engineering-day mechanical replay.

No promotional PnL until implementation identity is frozen and the no-alpha gate passes.

### Stage G — One frozen Discovery run

Run one predeclared implementation with no outcome-driven parameter changes.

Report at minimum:

- gross and net economics;
- fees separately;
- spread/slippage/depth separately;
- maker/taker share;
- fill probability / queue-model scenario;
- inventory/risk duration;
- latency sensitivity;
- rate-limit feasibility;
- long/short breadth;
- instrument breadth;
- day breadth;
- concentration.

### Stage H — Multi-asset replication

The default standard is no longer BTC-only evidence.

A candidate should be evaluated across the frozen universe **without per-asset retuning** unless the hypothesis explicitly defines a prospective normalization formula.

Primary cross-asset outputs should include:

- equal-weight mean market result;
- median market result;
- positive-market count/share;
- active-market count;
- worst quartile;
- top-market contribution share;
- market-level gross/net distributions;
- effect versus spread/depth/volatility/trade-intensity characteristics;
- instrument-day block uncertainty.

Do not require every market to be profitable. Instead require breadth and absence of one-market dependence under predeclared gates.

### Stage I — Untouched chronological Confirmation

Confirmation is one shot. It is not a new tuning set.

Parameters, universe logic, execution semantics, costs and promotion gates remain frozen from before Confirmation body access.

### Stage J — Forward/demo validation

Only after historical Confirmation should a candidate move to forward observation.

Forward work should distinguish:

- signal correctness;
- execution-model correctness;
- queue/fill calibration;
- operational order-rate behavior;
- realized versus simulated fee/slippage differences.

---

## 5. Multi-asset universe design — draft methodology

Target first-generation size: roughly **10 instruments**, with acceptable range 8-12 if historical eligibility/data constraints require it.

Do not freeze specific token names yet.

Preferred selection process:

1. choose venue/product family first;
2. define a pre-period lookback window;
3. list all instruments existing throughout the required research window or handle listings/delistings by a predeclared rule;
4. compute contemporaneous pre-period liquidity metrics only;
5. apply minimum history/data/spec requirements;
6. rank/stratify liquidity without consulting future strategy outcomes;
7. freeze the resulting symbols before promotional bodies are inspected.

Possible stratification:

- Tier A: very high liquidity / tight spread;
- Tier B: high-medium liquidity;
- Tier C: medium liquidity / wider spread but still institutionally tradable enough for small orders.

This is preferable to ten nearly identical high-liquidity majors because it allows us to learn whether the mechanism depends on microstructure conditions.

The universe itself is part of the hypothesis and cannot be expanded/shrunk after seeing which assets are profitable.

---

## 6. Statistical architecture for multi-asset scalping

### 6.1 Do not let BTC or high-frequency markets dominate pooled metrics

Always report both:

- trade/cycle-weighted pooled metrics;
- equal-weight market metrics.

Promotion should never rely solely on the pooled number.

### 6.2 Cluster-aware uncertainty

Cycles within an instrument-day are dependent. Different crypto assets on the same day are also correlated.

Preferred inference hierarchy:

- primary economic summary at instrument-day level;
- block resampling by day and/or instrument-day;
- sensitivity to instrument-level blocks;
- market breadth gates.

A later implementation may use two-way or hierarchical cluster bootstrap; the exact method must be frozen prospectively.

### 6.3 Concentration controls

Predeclare limits on:

- best market contribution;
- best day contribution;
- top-N market/day contribution;
- one-side dominance.

### 6.4 Gross-versus-cost decomposition

Every result must decompose:

`signal/price effect -> spread/depth -> fees/funding -> latency/execution -> net result`.

This is required so a failure can be classified as alpha failure, cost failure, execution failure or capacity failure rather than just "PnL negative".

### 6.5 Robustness is not parameter rescue

Stress tests are predeclared scenarios, not a license to choose whichever assumption produces a PASS.

---

## 7. Legacy Replication Program

Terminal experiment verdicts E001-E008 remain immutable. Legacy replication creates **new experiment IDs**.

Provisional priority:

### Priority 1 — E007 mechanism replication

Reason: strongest retained gross signal among failed SC001 candidates. Replicate the old frozen displacement/reversal logic across the frozen multi-asset universe with no asset-specific retuning. Determine whether the reversal effect is broad or BTC-specific and whether executable economics survive corrected cost/execution modeling.

### Priority 2 — E006 mechanism replication

Reason: event scarcity may be asset-specific. Test the same frozen basis-convergence mechanism across eligible spot/perp pairs where adequate synchronized data exist. Do not loosen the original trigger merely to increase sample size.

### Priority 3 — E002 TFI as an auxiliary feature

Do not replicate standalone taker trading as if the terminal failure did not happen. Instead test incremental value over an independently viable base strategy:

- veto bad entries;
- rank competing entries;
- improve maker adverse-selection timing;
- improve exit timing.

The comparison must be `base` versus `base + TFI`, with identical underlying opportunities and costs.

### Priority 4 — E004 strict replication

Lower priority because gross breakout headroom was weak. A cross-asset test can still determine whether the mechanism was BTC-specific, but it should not outrank candidates that already showed material gross effects.

### Priority 5 — E003 / E001

Low priority unless a specific new forensic reason identifies a plausible modeling distortion. Negative/weak gross mechanisms should not consume the same compute budget as stronger candidates.

### E005

No independent replication priority while its prerequisite mechanism remains failed.

### E008

No strict promotional rerun. Passive-maker research may return only as a **new family with a new execution model**, fresh promotional data and explicit queue uncertainty bounds.

---

## 8. Research ledger and anti-overfitting controls

Create/maintain a machine-readable ledger for every candidate containing:

- experiment ID;
- parent mechanism;
- hypothesis written before outcomes;
- code/blob identity;
- parameter set/hash;
- asset universe/hash;
- date sets by role;
- contamination status;
- number of variants tried;
- primary and secondary metrics;
- pass/fail gates;
- terminal decision;
- whether any human/model saw the next-stage body before freeze.

A candidate altered after Discovery is a new experiment ID.

The research ledger should eventually support a full count of how many hypotheses/variants were tried, enabling realistic multiple-testing correction and preventing forgotten failed attempts from biasing interpretation.

---

## 9. Storage and compute plan for the current VPS

Current heavy-compute environment: 4 vCPU / 8 GB RAM / 80 GB NVMe.

BTC E008 required about 3.725 GB compressed L2 for eight Discovery days plus relatively small trade archives. A naive ten-instrument copy at similar size would be roughly 37 GB of compressed L2 before reports, temporary files and existing project data. Some instruments will be smaller; some can be comparable.

Conclusion: current VPS is **computationally usable** for the first multi-asset generation, but storage must be managed carefully.

Default operating plan:

- stream `.tar.gz` rather than extract full archives;
- process instruments sequentially or at most one/two heavy L2 jobs concurrently;
- preserve a substantial free-disk reserve (target 15-20 GB until measured otherwise);
- download by instrument/date batch;
- SHA-verify before use;
- generate compact derived semantic/microstructure artifacts;
- do not delete raw promotional data merely to make room unless an identical verified copy exists elsewhere;
- if multi-asset L2 becomes the permanent workflow, increase storage to roughly 200-500 GB rather than forcing fragile cleanup cycles.

RAM design:

- streaming L2 replay;
- compact typed arrays for trades;
- avoid loading many instruments/days concurrently;
- no need for a larger CPU machine yet unless runtime becomes the bottleneck after correct architecture is established.

---

## 10. Generic economic-feasibility sanity gates

Exact strategy gates remain strategy-specific, but every future protocol should answer before promotional PnL:

1. What is the unavoidable round-trip fee floor for the intended maker/taker path?
2. What gross move/spread is required to clear fees plus a positive hurdle?
3. How often does the market offer that amount of raw opportunity?
4. Is event frequency sufficient to estimate the effect?
5. Can the intended order size execute within realistic depth?
6. Is expected turnover operationally/rate-limit feasible?
7. Does the mechanism have a plausible adverse-selection story?
8. Is the strategy still interesting under conservative but physically coherent execution assumptions?

If the mechanism cannot plausibly clear these sanity checks, stop before building a complex promotional engine.

---

## 11. Draft multi-asset promotion concepts — not yet binding

These are design targets to refine after the current E008 microstructure forensic; they are **not frozen gates** yet.

A robust candidate should likely require some combination of:

- sufficient active markets rather than one/two symbols;
- majority positive market-level net effects;
- positive median market-level net effect;
- positive equal-weight market aggregate;
- positive block-bootstrap lower confidence bound or another predeclared cluster-aware uncertainty measure;
- no single market/day dominating total edge;
- positive/acceptable stress economics under latency/cost/execution perturbations;
- no unresolved inventory/accounting failures;
- operational message-rate feasibility;
- cost assumptions based on historically correct instrument/fee rules.

The exact numerical thresholds must be frozen **before** the first new promotional multi-asset outcome is inspected.

---

## 12. What the current E008 microstructure forensic may change in v0.2

When `E008_READONLY_MICROSTRUCTURE_FORENSIC_PASS` completes, update this document with observed facts on:

- time-weighted BTC spread distribution;
- share of time above 4/5/7 bps economic thresholds;
- best-price churn;
- best-size increase/decrease activity;
- prior-best disappearance frequency;
- snapshot cadence;
- terminal cycle durations and side asymmetry.

These facts may change the **design of the new execution-model research**, but may not alter E008's terminal verdict.

Any design decision informed by those facts makes the inspected E008 BTC dates engineering/contaminated evidence for that new design.

---

## 13. Planned next documents after v0.1

After the current forensic, likely follow-up artifacts are:

1. `SC001 historical universe selection protocol`;
2. `SC001 contamination registry`;
3. `SC001 execution-model v2 protocol`;
4. `SC001 multi-asset data acquisition/semantic qualification protocol`;
5. `SC001 legacy replication program protocol`;
6. strategy-specific new-family protocol(s).

Do not create all of them mechanically. Each should be created only when the previous gate supplies the information needed to freeze it correctly.

---

## 14. Core research doctrine going forward

1. **Economics before engineering.** Check whether raw opportunity can plausibly clear costs before expensive simulation.
2. **Mechanism before parameter search.** Start with an economic hypothesis, not a profitable grid cell.
3. **Multi-asset before confidence.** BTC-only success is evidence, not sufficient general validation.
4. **Fresh data after redesign.** Once data helped design the model, it cannot be reused as untouched promotional proof.
5. **Execution as uncertainty, not false precision.** If MBO/FIFO is unavailable, model bounded uncertainty explicitly.
6. **Gross and cost components separately.** Know whether alpha or execution failed.
7. **Equal-weight markets as well as pooled cycles.** Do not let the busiest symbol dominate inference.
8. **Historical exchange reality.** Freeze contemporaneous specs, fees, funding and rate limits.
9. **No silent rescue.** Any meaningful post-outcome change creates a new experiment ID.
10. **Confirmation remains sacred.** One untouched chronological test, then forward validation.

The goal is not to maximize the number of PASS labels. The goal is to produce a small number of strategies whose economic mechanism, execution assumptions and statistical evidence are strong enough to survive skeptical review.
