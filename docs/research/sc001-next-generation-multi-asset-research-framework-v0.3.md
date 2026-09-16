# SC001 — Next-Generation Multi-Asset Research Framework v0.3

Date: 2026-09-16  
Status: **STRENGTHENED WORKING RESEARCH ARCHITECTURE AFTER FOUR-ROLE RED-TEAM REVIEW**  
Scope: **SCALPING RESEARCH / SC001 only**  
Supersedes: `sc001-next-generation-multi-asset-research-framework-v0.2.md`

This version incorporates a fresh critical review from four perspectives:

1. financial/economic researcher;
2. market-microstructure trader;
3. statistician/mathematician;
4. software/simulation verifier.

It also makes the companion technical standard binding for future promotional SC001 simulation work:

`docs/research/sc001-simulation-verification-and-accounting-standard-v0.1.md`

E001-E008 remain terminal/closed and are not reopened by this framework.

Independent project branches remain firewalled from SC001.

---

## 1. Research objective

The objective is not to maximize backtest PnL or the number of PASS labels.

The objective is to identify a **repeatable economic mechanism** whose positive executable expectancy survives:

- multiple historically selected instruments;
- independent time periods;
- historically correct exchange specifications;
- realistic and explicitly uncertain execution;
- regular-user fees/funding/spread/depth costs;
- latency and operational constraints;
- data/source semantic controls;
- cross-market and serial dependence;
- multiple-testing controls;
- untouched Confirmation;
- forward/demo reconciliation.

The central question is:

> Under which prospectively observable market conditions does the mechanism have positive executable expectancy, how large is the edge relative to unavoidable cost and uncertainty, and does it replicate across independent markets and time?

---

## 2. Binding lessons from E001-E008

Retain all terminal decisions.

### E002

Predictive microstructure feature, rejected standalone taker strategy. Reuse only as a separately frozen auxiliary/ranking/veto/execution-timing feature.

### E003

Rare flow-impulse continuation remains low priority because primary gross continuation mechanism failed.

### E004/E005

Compression-breakout gross headroom was weak; E005 remains closed with its failed prerequisite.

### E006

Basis-convergence event scarcity may be instrument-dependent; useful later as a multi-asset paired-market replication under a dedicated multi-leg kernel.

### E007

Highest-priority strict legacy replication candidate because a meaningful gross reversal effect existed before economics/robustness gates failed.

### E008

Terminal `E008_DISCOVERY_FAIL` remains binding.

Carry forward two simultaneous conclusions:

1. frozen BTC E008 economics were genuinely poor: negative gross edge, costs made net worse, quoted spread almost never covered regular maker-maker fee floor;
2. the frozen passive-fill implementation was also too adversarial to serve as a central FIFO estimator, especially around own-order omission, queue changes and periodic snapshots.

This distinction is now a general research rule: **strategy failure and simulator-model bias may coexist and must be diagnosed separately.**

---

## 3. Four-role red-team findings

## 3.1 Financial/economic review

### A. Edge must be evaluated relative to cost and capital usage

Do not stop at mean bps/cycle.

Every candidate should report, where relevant:

- gross edge;
- spread/depth cost;
- fees/funding/borrow;
- net edge;
- break-even all-in transaction cost;
- edge-to-cost ratio;
- turnover;
- exposure/inventory time;
- net PnL per instrument-day;
- net PnL per deployed-notional-day;
- capital utilization;
- capacity relative to depth/turnover;
- daily/worst-block tail losses.

A 2 bps edge with 1 bps cost uncertainty is economically different from a 2 bps edge with 0.05 bps cost uncertainty.

### B. Add an implementation reserve

Passing exactly above zero is not enough for a strategy whose historical execution is approximate.

Each strategy protocol should freeze an economic hurdle that includes a margin above modeled cost, rather than merely requiring `net > 0`.

The size of that reserve is strategy-specific and must be set before outcomes.

### C. Small-agent assumption must be explicit

Historical replay assumes our orders do not materially alter the future market path. This is only defensible for sufficiently small orders.

Future protocols must cap order size prospectively relative to liquidity/depth/turnover and perform a later capacity audit for larger capital.

### D. Risk is not captured by average cycle edge

Report loss clustering, worst instrument-days, inventory duration, intraday drawdown/exposure and tail metrics. A positive average with concentrated crash losses is not an acceptable scalp mechanism.

### E. Accounting must reflect the actual contract

Perpetual/futures PnL, fee and funding formulas must use historical contract values and settlement conventions, not generic return approximations.

---

## 3.2 Trader / microstructure review

### A. Separate execution kernels

Do not wait for a complex passive-maker engine to test a taker strategy.

SC001 should use:

- **taker kernel** for E007-like directional strategies;
- **passive-maker kernel** for future maker families;
- **multi-leg kernel** for E006-like basis/pair strategies.

Common data, contract, accounting and validation infrastructure should be shared.

This reduces coupling and prevents a passive-queue modeling error from contaminating a taker study.

### B. Own-order overlay is mandatory for maker work

The historical book is exogenous. Our own resting order must be represented separately so that external level disappearance does not erase our order and BBO logic includes the modeled own quote when relevant.

### C. Queue is an uncertainty problem, not a hidden exact FIFO

With aggregated L2, exact order position is unobservable.

Passive promotion should rely on predeclared physically coherent scenario sensitivity, not one fabricated point estimate.

A conclusion that changes sign across plausible queue scenarios is `EXECUTION_MODEL_SENSITIVE_REVIEW`, not a PASS selected from the preferred scenario.

### D. Taker execution must sweep the correct side of L2

Use causal opposite-side depth and VWAP. Arbitrary next-trade proxies are not canonical taker execution.

### E. Same-timestamp/cross-feed causality needs a formal scheduler

Freeze deterministic event precedence or ambiguity treatment. Do not let implementation iteration order decide fills.

### F. Snapshots, stale trust and own-order cancellation are separate concepts

A snapshot can replace/resynchronize external book state without being a venue cancellation of our own order.

### G. Order/cancel races are economically real

Pending cancels can fill; replacements can overlap depending on action timing. State transitions must be explicit and tested.

### H. Rate limits and order traffic are part of execution feasibility

A profitable historical strategy that requires impossible request throughput is an operational FAIL.

---

## 3.3 Mathematical/statistical review

### A. The effective sample size is much smaller than cycle count

Primary inferential units should be instrument-day/calendar-day blocks rather than individual scalp cycles.

Report both:

- cycle-weighted economics;
- equal-weight market economics;
- instrument-day distributions;
- calendar-day block uncertainty;
- market breadth;
- concentration.

### B. Cross-asset same-date results are not independent

Crypto assets share calendar shocks. Multi-asset replication on one week is not equivalent to time Confirmation.

Use a **two-dimensional holdout design**:

- cross-asset replication/asset holdout;
- later untouched chronological Confirmation.

### C. Prefer contiguous/time-diverse blocks over a handful of isolated convenient days

Future chronology should capture multiple market regimes and serial dependence. Exact sample design will be frozen later, but eight isolated days should not be the default evidence standard for a new generalizable family.

A practical design may use several deterministic non-overlapping multi-day blocks across a longer period, subject to storage constraints.

### D. Multiple testing must include human/LLM research choices

The research ledger must count meaningful variants considered by scripts, humans and model-assisted research, not only code branches that reached a final report.

Any strategy changed after viewing Discovery creates a new experiment ID.

### E. Add matched/null controls where meaningful

A signal should be compared against unconditional/matched opportunity behavior, not only against zero.

Examples:

- matched market-state events;
- base versus `base + TFI` on identical opportunities;
- block-shifted/no-signal control preserving dependence.

### F. Execution-model uncertainty is separate from sampling uncertainty

Confidence intervals over historical days do not solve queue-model uncertainty.

Reports should separately identify:

1. sampling uncertainty;
2. execution-model/scenario uncertainty;
3. cost/spec uncertainty;
4. parameter/research-selection uncertainty.

Do not combine these into one misleading standard error.

### G. Avoid winner-only denominators

If the frozen universe has 10 markets and only 4 pass an economic-feasibility gate, report both:

- strategy results on the prospectively eligible subset;
- **coverage = 4/10** across the original universe.

Do not silently discard markets and then claim broad 4/4 success.

### H. Missing/corrupt data need predeclared treatment

Do not drop failed instrument-days after outcomes. Define before body access whether they count as unavailable, fail, substitute under an objective rule, or reduce the evaluable denominator.

### I. Use robust descriptive estimators prospectively

Means, medians, trimmed means and concentration metrics can all be useful, but trimming/winsorization rules must be fixed before outcomes.

---

## 3.4 Software/simulation-verification review

The binding technical rules are in:

`sc001-simulation-verification-and-accounting-standard-v0.1.md`

The most important architectural changes are:

- no opaque monolithic backtest;
- immutable market/intent/order/fill/accounting layers;
- canonical fill ledger;
- independent PnL recomputation;
- integer ticks/lots for execution state;
- causal data-access guard;
- explicit order state machine;
- reference/golden implementation before optimization;
- property/fuzz/fault-injection tests;
- differential testing;
- deterministic run manifests;
- one-shot promotional guard;
- output cause codes instead of generic FAIL only.

A fast script is not acceptable unless it is semantically identical to the validated reference on controlled samples.

---

## 4. Systemic research controls retained from v0.2

The following remain mandatory:

- contamination registry;
- historical universe selection without survivorship/look-ahead;
- historical contract/fee/funding freeze;
- integer exchange discreteness;
- rate-limit feasibility;
- own-order overlay for maker work;
- queue uncertainty scenarios;
- exact-price vs price-through distinction;
- snapshot semantics;
- side-specific L2 taker execution;
- post-only semantics;
- separated latency components;
- hidden-liquidity limitation;
- time-weighted market-state diagnostics;
- markout/adverse-selection decomposition;
- listing/delisting/spec structural-break handling;
- regime analysis labeled descriptive unless frozen prospectively.

---

## 5. Revised research funnel: cheap evidence before expensive L2

To conserve storage/compute and reduce research degrees of freedom, use a staged data funnel.

### Stage 0 — Governance freeze

Before new outcomes:

- create experiment ID;
- state hypothesis/falsification rule;
- record contamination status;
- define universe-selection rule;
- define date roles;
- define primary metrics/gates;
- register parameter/tuning budget.

### Stage 1 — Historical universe/spec metadata audit

Metadata only where possible:

- historical listings;
- product family;
- contract specs;
- pre-period liquidity/history eligibility;
- data availability;
- fee/funding evidence.

Freeze roughly `8-12` instruments prospectively.

### Stage 2 — Cheap economic-feasibility audit

Use the cheapest sufficient data first.

Examples:

- taker candidate: signal gross-move scale, event frequency, coarse spread/depth/cost floor;
- maker candidate: time-weighted spread, top-of-book churn/depth and fee floor;
- basis candidate: basis event frequency/headroom and paired-market availability.

Apply the same frozen feasibility rule to the entire universe and report coverage.

Do not download/replay full 400-level L2 for every market if a strategy is already economically impossible from cheaper evidence.

### Stage 3 — Minimal required data acquisition

Acquire only the market-data depth needed by the candidate's execution kernel.

Examples:

- small taker strategy may need only sufficient top-N depth rather than all 400 levels in downstream derived artifacts;
- passive queue research may require full qualified L2;
- basis research needs synchronized data for both legs.

Raw source identity must remain preserved even when compact derived artifacts are used.

### Stage 4 — Data semantic qualification

Source identity, CRC/SHA, schema, chronology, coverage, archive transformation and gap checks before alpha.

### Stage 5 — Appropriate execution-kernel validation

Use the technical standard. Validate on synthetic + contaminated engineering data only.

### Stage 6 — One frozen Discovery

No outcome-driven changes.

### Stage 7 — Cross-asset replication / asset holdout

No per-asset retuning except a normalization formula frozen before outcomes.

### Stage 8 — Untouched chronological Confirmation

One-shot time holdout.

### Stage 9 — Forward/demo reconciliation

Measure model-versus-reality differences in latency, fill, costs and operations.

---

## 6. Multi-asset universe methodology

Initial target remains roughly 10 instruments (`8-12` acceptable for objective historical reasons).

Universe principles:

- choose venue/product family first;
- use a pre-period lookback only;
- include historically eligible listings even if later delisted, subject to predeclared rules;
- stratify by contemporaneous liquidity rather than only current majors;
- preserve a wide enough liquidity/spread range to test whether mechanism behavior depends on microstructure;
- do not alter the universe after strategy PnL is observed.

### Applicability versus performance

A strategy may prospectively declare that it only applies where an economic-feasibility condition holds.

That is allowed only if the rule is frozen before PnL.

Every report must then show:

- full frozen universe size;
- number meeting the applicability/feasibility rule;
- number actually evaluable after objective data-quality rules;
- positive/negative performance among eligible markets.

This prevents a hidden transition from "multi-asset strategy" to "we kept only the winners."

---

## 7. Chronology and contamination architecture

Future evidence should separate both **assets** and **time**.

Recommended roles:

1. engineering/calibration data — freely inspectable;
2. Discovery instruments/dates;
3. cross-asset replication/asset holdout;
4. later chronological Confirmation across the frozen applicable universe;
5. forward/demo.

Any date/instrument whose result influenced code, queue semantics, threshold logic or execution design becomes contaminated for the redesigned implementation.

The contamination registry should record not only script use but also whether a human/LLM inspected outcome-bearing artifacts.

---

## 8. Strategy-specific economic-feasibility gates

Do not use one generic spread threshold for every strategy.

### Taker directional/reversal candidate

Before full execution simulation quantify:

- event count/breadth;
- gross signed move distribution at frozen horizon;
- round-trip taker fee floor;
- spread/depth execution envelope;
- break-even total cost;
- whether gross headroom is orders of magnitude larger/smaller than cost.

### Passive-maker candidate

Before queue modeling quantify:

- time-weighted spread distribution;
- maker-maker and maker-taker fee floors;
- queue/churn/depth;
- expected adverse-selection markout envelope;
- opportunity duration/frequency.

### Multi-leg basis/carry candidate

Before detailed paired execution quantify:

- event scarcity/breadth;
- gross convergence/carry headroom;
- both-leg fee/depth costs;
- funding/borrow;
- leg-risk duration;
- discrete hedge mismatch.

---

## 9. Statistical promotion architecture — draft, not yet numeric

Exact numerical gates will be frozen per strategy before outcomes.

A robust multi-asset candidate should generally demonstrate:

- adequate applicable-market coverage;
- adequate instrument-day/calendar breadth;
- positive equal-weight market economics, not only pooled-cycle economics;
- positive median/majority breadth under predeclared criteria;
- acceptable worst-quartile/tail behavior;
- limited top-market/top-day contribution concentration;
- stable sign under required cost/latency/execution scenarios;
- cluster/block-aware uncertainty consistent with positive economic effect;
- no accounting/data/implementation invalidity.

For passive work, a result materially dependent on one uncalibrated queue scenario remains REVIEW rather than promotional PASS.

---

## 10. Legacy Replication Program — optimized order

Terminal verdicts remain immutable; replications use new IDs.

### Priority 1 — E007 strict multi-asset replication

Why first:

- retained gross reversal effect;
- taker execution is simpler and more verifiable than passive FIFO;
- it can use the common infrastructure + validated taker kernel without waiting for passive-maker engine v2.

First replicate old frozen signal logic without per-asset retuning. Any later normalized variant is a separate experiment ID.

### Priority 2 — E006 multi-asset basis replication

Proceed after a validated multi-leg kernel and synchronized paired data pipeline exist.

### Priority 3 — E002 TFI incremental feature

Only after an independently viable base mechanism exists. Use paired `base` vs `base + TFI` comparison on identical opportunities.

### Priority 4 — E004 strict replication

Lower priority because gross headroom was weak.

### Low priority — E003/E001

Only if a concrete forensic/modeling reason emerges.

### E005

No independent priority.

### Passive maker after E008

Not an E008 rerun. Open only as a new family after passive execution v2, queue-scenario validation and fresh data.

---

## 11. Data/derived-artifact optimization

Repeatedly decompressing raw L2 for every strategy is wasteful and increases code paths.

After source qualification, it is acceptable to create versioned compact derived artifacts such as:

- normalized trades;
- causal BBO/top-N depth stream;
- contract/spec metadata;
- semantic quality report.

Requirements:

- raw source SHA provenance retained;
- transformation code/blob hash retained;
- derived artifact SHA retained;
- deterministic transformation;
- representative rows/events cross-checked against raw source;
- strategy still accesses only information causally available at that time.

A derived artifact is a cache, not a new source of truth.

---

## 12. Interpretation rules

### A. Realized PnL versus diagnostics

Actual fill-ledger prices determine execution PnL.

Midquote, microprice, last trade and markout are diagnostics and must not be substituted into realized PnL.

### B. PASS/FAIL cause taxonomy

Reports should separate:

- DATA_FAIL;
- IMPLEMENTATION_FAIL;
- SAMPLE_SCARCITY;
- ALPHA/GROSS_EDGE_FAIL;
- COST_FAIL;
- EXECUTION_MODEL_SENSITIVE_REVIEW;
- CAPACITY_FAIL;
- OPERATIONAL_FAIL;
- ROBUST_ECONOMIC_PASS.

### C. A prior PASS of mechanics does not imply profitable economics

Data integrity, state-machine correctness and profitability are separate gates.

### D. A bad simulator does not prove a good strategy

Finding execution-model bias may invalidate confidence in a fill-rate estimate, but it does not retroactively convert negative observed gross economics into positive alpha.

---

## 13. Mandatory pre-promotion four-role review

Before every new promotional experiment, explicitly perform and document a short red-team review from four perspectives.

### Financial reviewer

- Is gross headroom economically capable of clearing costs?
- Is capital/risk/capacity represented correctly?
- Are tail losses and capital utilization visible?

### Trader/microstructure reviewer

- Is execution physically plausible for the order type?
- Are queue, latency, cancel races, post-only and depth semantics correct?
- Are operational limits realistic?

### Mathematical reviewer

- Are the effective units of observation independent enough for the claimed inference?
- Are breadth, concentration, multiple testing and holdouts controlled?
- Are uncertainty sources separated?

### Software verifier

- Are causality, ledgers, invariants, reference tests, hashes and reproducibility complete?
- Can accounting be independently recomputed?
- Can an optimization accidentally change semantics?

Unresolved critical objections keep the promotional run closed.

---

## 14. Immediate next program

No new promotional strategy yet.

Next sequence:

1. create/freeze historical universe selection protocol;
2. create machine-readable contamination registry;
3. perform metadata-only historical universe/spec audit;
4. freeze first multi-asset universe;
5. define fresh chronology roles with broader/time-block coverage;
6. build common normalized data/accounting infrastructure under the simulation standard;
7. build and validate **taker execution kernel first**;
8. perform cheap E007 economic-feasibility audit across the frozen universe;
9. only if feasibility survives, freeze/run new strict E007-replication experiment;
10. build multi-leg kernel before E006 replication;
11. build passive-maker execution v2 separately before any new maker family;
12. preserve untouched chronological Confirmation and forward stages.

This sequence intentionally avoids letting the most complex passive FIFO problem block the simpler and higher-priority E007 replication.

---

## 15. Core doctrine v0.3

1. **Economics before engineering.**
2. **Cheap evidence before expensive L2.**
3. **Mechanism before parameter search.**
4. **Execution kernel appropriate to strategy type.**
5. **Separate execution from accounting.**
6. **Multi-asset breadth before confidence.**
7. **Cross-asset replication is not time Confirmation.**
8. **Fresh data after redesign.**
9. **Queue/FIFO uncertainty must remain explicit.**
10. **Actual fills determine PnL; markouts are diagnostics.**
11. **Integer exchange discreteness is canonical.**
12. **Operational feasibility is part of economics.**
13. **All meaningful research variants count toward data-snooping risk.**
14. **A model-sensitive conclusion is REVIEW, not a chosen-scenario PASS.**
15. **Confirmation remains sacred and one-shot.**
16. **Forward behavior must reconcile with simulation.**

The goal is a small set of strategies whose economic mechanism, execution assumptions, accounting and statistical evidence remain credible after skeptical financial, trading, mathematical and software review.
