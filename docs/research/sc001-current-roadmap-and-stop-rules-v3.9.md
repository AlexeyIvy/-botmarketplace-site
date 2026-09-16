# SC001 Current Roadmap and Stop Rules v3.9

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — FOUR-ROLE RED-TEAM COMPLETE / ARCHITECTURE HARDENED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v3.8.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed.

E008 remains exact terminal:

`E008_DISCOVERY_FAIL`

No E008 rescue-tuning, no promotional rerun, no E008 Confirmation, no Q2/formal Validation/Final.

SC001 remains fully independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. E008 forensic complete

Completed without strategy rerun:

- `E008_READONLY_POSTMORTEM_PASS`;
- `E008_READONLY_MICROSTRUCTURE_FORENSIC_PASS`;
- forensic exit code `0`.

Binding interpretation:

- E008 BTC economics were genuinely negative before and after fees;
- quoted spread almost never covered regular maker-maker fee floor;
- frozen passive queue/reset model also contained material pessimistic biases and must not be reused as a central FIFO estimator.

## 3. Research architecture strengthened

Current working research framework:

`docs/research/sc001-next-generation-multi-asset-research-framework-v0.3.md`

New binding technical standard for future promotional simulations:

`docs/research/sc001-simulation-verification-and-accounting-standard-v0.1.md`

The architecture was red-teamed from four perspectives:

- finance/economics;
- market microstructure/trading;
- mathematics/statistics;
- software/simulation verification.

## 4. Major changes from v3.8

### Simulation architecture

Do not build future research as opaque monolithic backtests.

Separate:

1. market events;
2. causal features/strategy intents;
3. order lifecycle;
4. immutable fill ledger;
5. independent position/cash/PnL ledger;
6. metrics/statistics.

Accounting must reconcile independently from the fill ledger.

### Execution kernels

Use strategy-specific kernels:

- taker kernel;
- passive-maker kernel;
- multi-leg kernel.

Do not force E007 replication to wait for passive-maker FIFO research.

### Numerical correctness

Execution state should use integer ticks/lots and historical contract specifications. Float is not the authority for exchange-state equality or rounding.

### Causality

Future engines must distinguish source-event, observed, decision, send and activation/ack times and mechanically prevent future-data access.

### Queue uncertainty

Aggregated L2 cannot prove exact FIFO. Passive results must use predeclared physically coherent scenarios and may be classified `EXECUTION_MODEL_SENSITIVE_REVIEW` when the conclusion depends on queue assumptions.

### Financial outputs

Mean bps/cycle alone is insufficient. Add break-even cost, capital utilization, turnover, instrument-day PnL, tail/concentration and capacity metrics.

### Statistics

Cross-asset same-date results are correlated. Use both asset and time holdouts, instrument-day/calendar blocks, market breadth and concentration controls.

### Research degrees of freedom

Human/LLM-guided meaningful variants count toward the research ledger and contamination history.

## 5. Revised research funnel

Future SC001 research proceeds from cheap/robust evidence to expensive simulation:

1. governance/hypothesis/contamination freeze;
2. historical universe + instrument-spec metadata audit;
3. cheap strategy-specific economic-feasibility audit;
4. minimal required data acquisition;
5. semantic qualification;
6. appropriate execution-kernel validation;
7. one frozen Discovery;
8. cross-asset replication / asset holdout;
9. untouched chronological Confirmation;
10. forward/demo reconciliation.

Do not acquire/replay full 400-level L2 across all markets when a candidate already fails a cheaper prospectively defined economic gate.

## 6. Multi-asset design remains provisional until universe protocol

Target first generation remains roughly `8-12` instruments, around 10 if historically eligible.

Requirements:

- one comparable venue/product family initially;
- pre-period universe selection only;
- survivorship/look-ahead controls;
- stratified liquidity rather than current-popularity selection;
- explicit applicability coverage;
- no per-asset retuning during strict replication unless a prospective normalization formula was frozen.

Exact symbols are not yet frozen.

## 7. Legacy replication priority — optimized

All old verdicts remain immutable. Replications use new experiment IDs.

1. **E007 mechanism** — first priority; use validated taker kernel and multi-asset replication.
2. **E006 mechanism** — after validated multi-leg kernel and synchronized paired data.
3. **E002 TFI** — auxiliary feature only, paired base-vs-base+TFI test after a viable base exists.
4. **E004** — lower priority.
5. **E003/E001** — low priority absent a specific forensic reason.
6. **E005** — no independent priority.
7. **Passive maker** — only as a new family after passive execution v2 and fresh data; never an E008 rerun.

## 8. Current hard gate

Do **not** launch a new promotional strategy yet.

Next implementation/design work:

1. create historical-universe selection protocol;
2. create machine-readable contamination registry;
3. perform metadata-only historical universe/spec audit;
4. freeze first multi-asset universe;
5. freeze broader/fresh chronology roles;
6. build common normalized data + independent accounting infrastructure;
7. build/validate taker execution kernel under `sc001-simulation-verification-and-accounting-standard-v0.1.md`;
8. run cheap E007 economic-feasibility audit across the frozen universe;
9. only if that survives, freeze one strict E007 replication experiment.

Passive-maker execution v2 is a parallel/later engineering track and must not block E007.

## 9. Required validation before any promotional runner

At minimum require:

- source/archive semantics understood;
- syntax/import check;
- golden hand-calculated fixtures;
- parser/contract unit tests;
- legal order-state transitions;
- accounting conservation;
- causal future-access tests;
- property/fuzz/fault injection where applicable;
- deterministic replay;
- independent accounting recomputation;
- reference/differential validation on controlled samples;
- exact data/config/code/run manifest identity;
- one-shot duplicate-run protection.

A `py_compile` PASS alone is never sufficient implementation validation.

## 10. Stop rules

Do not:

- reopen E001-E008;
- treat cross-asset replication as chronological Confirmation;
- reuse contaminated dates as fresh proof after redesign;
- choose instruments using future popularity/performance;
- silently drop economically/data-inconvenient markets from breadth denominators;
- select the best queue scenario after outcomes;
- use midquote/markout as realized fill PnL;
- use arbitrary next public trade as canonical taker execution;
- let performance optimization change validated event/order/fill semantics;
- change a strategy after Discovery without assigning a new experiment ID.

## 11. Immediate next action

No further E008 strategy command.

Proceed to the historical-universe selection protocol and contamination registry, then metadata-only universe/spec audit. Do not download a large new multi-asset promotional body set until that architecture is frozen.
