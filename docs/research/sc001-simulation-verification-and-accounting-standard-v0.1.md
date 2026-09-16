# SC001 — Simulation Verification & Accounting Standard v0.1

Date: 2026-09-16  
Status: **WORKING TECHNICAL STANDARD — REQUIRED BEFORE NEW PROMOTIONAL SC001 SIMULATIONS**  
Scope: **SCALPING RESEARCH / SC001**

This document defines how future SC001 simulation code must represent time, orders, fills, accounting, costs, uncertainty, testing and reporting.

It is motivated by lessons from E001-E008, especially E008, but it does not reopen or alter any terminal experiment verdict.

The purpose is to prevent a future strategy result from depending on an unnoticed parser, causality, queue, accounting or interpretation error.

---

## 1. Core architecture: separate mechanism from accounting

Future promotional simulators must not be one opaque script that simultaneously parses data, generates signals, simulates fills and reports PnL.

Preferred deterministic pipeline:

1. **market-event layer** — normalized source events with provenance;
2. **feature/signal layer** — causal state and strategy intents only;
3. **order-lifecycle layer** — submission, activation, resting, cancel, rejection, partial fill, fill;
4. **fill ledger** — immutable executed quantities/prices/liquidity type;
5. **position/cash ledger** — independently reconstructed inventory, cash, fees, funding and realized/unrealized PnL;
6. **metrics layer** — economics/statistics derived from the ledger, never from hidden simulator state.

The fill ledger is the canonical bridge between execution and accounting.

The accounting layer must be able to recompute PnL from the fill ledger without calling strategy logic.

---

## 2. Time and causality model

Every market/order event should distinguish, where applicable:

- `source_event_ts` — exchange/source event timestamp;
- `observed_ts` — when the strategy is allowed to know the event under the latency model;
- `decision_ts` — strategy decision time;
- `send_ts` — outbound order/cancel submission time;
- `ack_or_activation_ts` — when the action becomes effective in the execution model.

Rules:

- no strategy read may access market state whose `observed_ts` is in the future relative to the decision;
- rolling features must be strictly backward-looking;
- centered windows are prohibited for live-decision features;
- day-file boundaries must not silently reset rolling state unless the strategy specification requires a reset;
- required previous/next-neighbor data for UTC reconstruction must be explicit;
- equal-timestamp ordering must be frozen before outcomes;
- if exact cross-feed ordering is unavailable, ambiguity must be modeled explicitly rather than invented.

Recommended implementation control: a causal data accessor that raises an error on any future-state access in test/debug mode.

---

## 3. Source provenance and transformation audit

Before using a new historical source, record:

- venue/source;
- raw filename/URL;
- SHA256 and byte size;
- archive format/member identity;
- source timestamp field semantics;
- snapshot/update semantics;
- trade aggregation semantics;
- whether the archive provider resampled, inserted periodic snapshots, normalized or transformed exchange messages;
- known sequence/checksum fields and limitations.

A transformed archive is not assumed to be a literal packet-by-packet exchange feed.

E008's exactly 1,440 snapshots/day is a concrete example of why archive transformation semantics must be audited before snapshots are interpreted as venue order events.

---

## 4. Numerical representation

Canonical execution state should use exchange-discrete units wherever possible:

- integer price ticks;
- integer lot/contract units;
- integer order quantities after rounding;
- explicit historical `tickSz`, `lotSz`, `minSz`, `ctVal`/multiplier;
- explicit linear/inverse contract formulas.

Do not use binary float equality as the authority for order-state transitions.

Derived analytics may use float. Monetary/fee calculations should use either exact integer minor units or a controlled decimal representation where necessary.

Every rounding rule must be explicit: price rounding direction, quantity floor/rounding, minimum size/notional rejection.

---

## 5. Historical instrument and fee specification

For every instrument-period promotional run freeze:

- listing/delisting state;
- contract type;
- quote and settlement currency;
- contract value/multiplier;
- tick and lot sizes;
- min/max quantity if relevant;
- fee formula and assumed account tier;
- funding schedule/formula for perpetuals;
- margin/liquidation rules if leverage/liquidation can matter;
- known specification changes during the period.

Current venue metadata is not historical proof.

If historical fee/spec evidence is unavailable, the uncertainty must be disclosed and handled by a predeclared conservative assumption or the instrument-period cannot be promoted.

---

## 6. Order lifecycle state machine

A future engine should use explicit legal states such as:

`INTENT -> SENT -> ACK/ACTIVE -> PARTIAL -> FILLED`

and cancellation/rejection paths such as:

`ACTIVE/PARTIAL -> CANCEL_SENT -> CANCELLED`

`SENT -> REJECTED`

`ACTIVE/PARTIAL -> EXPIRED`

Requirements:

- impossible transitions raise errors;
- order quantity conservation is exact;
- fills can occur while cancel is pending if the model permits that causal race;
- replacement cannot silently erase an old live order before cancel effectiveness;
- amend semantics must state whether queue priority is preserved or lost for the venue/order type;
- duplicate cancels must be suppressed or explicitly counted as requests, not confused with distinct cancel acknowledgements;
- self-trade prevention / crossed-own-order behavior must be defined if two-sided quoting can create interaction.

---

## 7. Own-order overlay and the small-agent assumption

Historical books are exogenous and do not contain our hypothetical order.

Passive engines must therefore maintain an explicit own-order overlay separate from external displayed liquidity.

At minimum:

- own resting size is not external queue-ahead;
- exogenous disappearance of all historical size at our price does not automatically delete our own order;
- our order can keep a price level present;
- exogenous BBO and venue BBO including our order may differ;
- subsequent strategy decisions must use the modeled venue state including our order where relevant.

However, the future historical world is still counterfactual: our real order could have changed other participants' behavior and later book states. Therefore promotional simulations require a **small-agent/capacity assumption** with prospectively frozen size caps relative to displayed depth/turnover. Large-capital capacity requires separate analysis.

---

## 8. Separate execution kernels by strategy type

Do not force all SC001 strategies through one execution engine.

### 8.1 Taker kernel

Use for aggressive-entry/exit strategies such as a future E007 replication.

Required behavior:

- execute from the correct opposite-side L2 at causal execution time;
- sweep depth level by level;
- respect quantity/tick/lot rules;
- record partial/unfilled quantity if available depth is insufficient;
- apply side-specific fees;
- no arbitrary next-trade-price proxy as primary execution;
- predeclare treatment when no trusted book exists at execution time.

### 8.2 Passive-maker kernel

Required behavior:

- own-order overlay;
- post-only acceptance/rejection;
- explicit placement/cancel/ack timing;
- partial fills;
- queue uncertainty scenarios;
- snapshot semantics separated from own-order state;
- exact-price versus price-through trade evidence separated;
- stale-data policy;
- message-rate feasibility.

### 8.3 Multi-leg kernel

Use for spot/perp basis or other paired strategies.

Required behavior:

- explicit leg order/timing sequence;
- non-atomic leg risk unless a venue mechanism is proven atomic;
- quantity rounding on both legs;
- residual delta/hedge error;
- side-specific depth and fees per leg;
- funding/borrow where relevant;
- failure behavior when one leg fills and the other does not.

Common data, accounting and validation layers should be shared across kernels.

---

## 9. Queue inference without market-by-order data

Aggregated L2 cannot identify exact FIFO position.

Do not report a single queue estimate as truth.

A future passive study should freeze a physically coherent scenario family before promotional results:

1. **conservative scenario** — full displayed initial queue ahead, no ambiguous cancellation credit, conservative same-ms treatment;
2. **central scenario** — only if justified/calibrated on engineering or forward data under a predeclared rule;
3. **optimistic diagnostic** — plausibility envelope only, never sufficient for promotion.

Important:

- size added after our order is resting normally should not automatically jump ahead under price-time priority unless source/venue semantics justify it;
- size decreases cannot be cleanly classified as cancellations ahead/behind with aggregated L2;
- exact-price aggressive volume is stronger queue evidence than a worse-price print;
- price-through prints require a separate causal rule;
- hidden/iceberg liquidity remains unobserved.

Do not assume PnL is monotonic from conservative to optimistic queue assumptions: additional fills can increase adverse selection. Treat scenarios as execution-model sensitivity, not mathematical PnL bounds.

Recommended verdict language for passive studies:

- **ROBUST** — economics acceptable across required physically coherent scenarios;
- **ROBUST_FAIL** — economics fail across scenarios;
- **EXECUTION_MODEL_SENSITIVE / REVIEW** — conclusion changes materially across plausible scenarios; requires forward calibration rather than tuning historical rules.

---

## 10. Market-data staleness and snapshots

Staleness is a trust property of the observed external book, not proof that an own order vanished.

Separate:

- external book trusted/untrusted state;
- strategy cancel policy triggered by stale data;
- actual cancellation effective time;
- later snapshot resynchronization;
- own-order state.

A snapshot may restore trust in external market state. It does not automatically prove an exchange-side cancellation of our hypothetical order.

---

## 11. Taker execution and depth

For aggressive execution, the canonical fill price is derived from executable opposite-side book levels, not from midquote or an arbitrary public trade.

For requested quantity `Q`:

- consume available levels causally in price order;
- compute VWAP of actually filled quantity;
- record unfilled remainder if insufficient trusted depth;
- apply order-size discreteness before sweeping;
- record spread/depth cost separately from fees.

If historical feed frequency means the true within-interval path is unknown, that uncertainty must appear in stress/scenario analysis.

---

## 12. Fees, funding and other costs

Costs must be recorded as independent ledger components:

- maker fee/rebate;
- taker fee;
- funding;
- borrow/interest if applicable;
- spread/depth slippage;
- optional market-impact stress for capacity;
- liquidation/margin losses if relevant to the strategy.

Do not hide all costs inside one net-return number.

Fee tier assumptions are frozen before outcomes. A lower VIP tier/rebate may be a prospective sensitivity scenario, but cannot rescue a failed base result after the fact.

---

## 13. PnL and accounting identities

PnL must be independently reconstructed from the immutable fill ledger.

For every run verify identities such as:

- ending inventory = starting inventory + signed filled quantity;
- filled quantity per order <= submitted quantity;
- sum of fill fees = reported fee ledger;
- cash/settlement changes reconcile to fills and fees;
- realized + unrealized PnL reconciliation is exact under the selected contract formula;
- if protocol requires flat end state, ending inventory is exactly zero or run is unresolved/fail-closed;
- no fee is charged twice or omitted after partial fills.

Midquote/microprice/last trade may be used for diagnostics/markout, but must not replace actual fill prices in realized execution PnL.

---

## 14. Economic outputs beyond mean bps/cycle

Mean edge per completed cycle is insufficient.

Future reports should include where relevant:

- gross edge distribution;
- spread/depth cost;
- fee/funding cost;
- net edge distribution;
- break-even all-in transaction cost in bps;
- edge-to-cost ratio when meaningful;
- completed/attempted opportunity counts;
- fill and completion rates;
- partial-fill rate;
- cancel/placement counts;
- exposure/inventory duration;
- capital utilization;
- turnover;
- net PnL per instrument-day and per deployed-notional-day;
- daily tail metrics / worst instrument-days;
- concentration by day, instrument and side;
- maker-fill markouts at frozen horizons;
- capacity ratio relative to depth/turnover.

For maker strategies report all quote opportunities and lifecycle denominators, not only completed cycles, to avoid selection bias from conditioning on successful fills.

---

## 15. Markout and adverse selection

For maker fills, predeclare diagnostic markout horizons before promotional results, for example short and medium horizons appropriate to the strategy.

Signed markout should use a stated reference price such as causal midquote after the fill and be reported separately from realized PnL.

Markout analysis must distinguish:

- maker entry fills;
- passive exit fills;
- side;
- market/instrument;
- regime variables only if predeclared or clearly labeled post-hoc descriptive.

High fill probability with negative markout is not a healthy maker edge.

---

## 16. Baselines and counterfactual controls

Where meaningful, every new strategy should have a predeclared comparison that asks whether the strategy adds value beyond the unconditional market behavior.

Examples:

- matched no-signal events with similar time/market state;
- base strategy versus `base + auxiliary feature` for E002/TFI reuse;
- same-frequency block-shift/permutation control that preserves serial dependence;
- simple execution baseline using identical costs/opportunity set.

Controls must not introduce future information and their construction must be frozen before outcomes.

---

## 17. Feature-distribution audit before thresholds

Before using percentile/quantile thresholds or ranks, inspect on engineering/calibration data:

- mass points/ties;
- missing values;
- bounded/discrete score support;
- numerical quantization;
- threshold equality frequency;
- sensitivity to nearest-rank/interpolation convention.

E002 showed why an upper percentile of a discrete score can fail to create a selective tail.

Threshold/tie handling must be frozen before promotional data.

---

## 18. Verification ladder for every execution kernel

`py_compile` is only the first check, not evidence of correctness.

Required validation ladder should include as applicable:

1. syntax/import check;
2. deterministic hand-calculated golden fixtures;
3. unit tests for parsers and contract conversions;
4. state-transition tests;
5. property-based/fuzz tests for malformed and random valid event sequences;
6. accounting conservation tests;
7. causal/future-access tests;
8. partial-fill and cancel-race fixtures;
9. stale/snapshot fixtures;
10. tick/lot rounding edge cases;
11. rate-limit/backlog fixtures;
12. fault injection: CRC failure, timestamp reversal, duplicate event, missing snapshot, gap;
13. replay determinism: same inputs/config/code -> byte-equivalent canonical ledgers or hashes;
14. differential test against a small independent/reference implementation on toy/sampled data;
15. independent accounting recomputation from the fill ledger;
16. contaminated real-data mechanical replay with no promotional economics;
17. performance-optimized implementation compared against the reference semantics on identical samples.

Any optimization/vectorization/parallelization is unacceptable if it changes canonical order/fill ledger output relative to the validated reference for the same deterministic scenario.

---

## 19. Metamorphic tests

Use transformations whose expected relationship is known to catch implementation errors.

Examples on controlled synthetic fixtures:

- splitting one same-price/same-side execution volume into causal chunks should preserve total queue depletion when ambiguity rules are unchanged;
- side-mirrored synthetic books/signals should produce mirrored inventory/PnL under symmetric costs;
- zero-fee rerun of a fixed fill ledger should differ from the fee-bearing accounting only by exactly the fee ledger;
- recomputing metrics from a shuffled report order must not change economic totals;
- duplicate source events must be rejected/detected rather than silently double-counted.

Do not invent monotonic relationships that are not guaranteed (for example, more maker fills do not necessarily mean better PnL).

---

## 20. Run manifest and reproducibility

Every promotional run must write a machine-readable manifest including at minimum:

- experiment ID and stage;
- git commit and relevant file/blob identities;
- Python/runtime/package lock identity;
- configuration file/hash;
- universe hash;
- date-role hash;
- contamination-registry hash;
- data file SHA256 identities;
- historical instrument-spec identities;
- fee/funding assumptions;
- latency/execution scenario identities;
- random seeds if any;
- start/end time and exit status;
- firewall flags for unopened future stages.

Long runs must be resumable only when all relevant identities match exactly.

A checkpoint is a computational optimization, not permission to alter semantics.

---

## 21. One-shot promotional guard

Promotional runners should be designed to refuse an accidental duplicate run when a complete terminal report already exists for the same experiment/config/data identity.

A deliberate new implementation or configuration requires a new experiment ID and fresh eligibility/contamination review.

---

## 22. Reporting and terminal classification

Do not collapse every failure into generic `FAIL`.

Reports should distinguish, when possible:

- `DATA_FAIL`;
- `IMPLEMENTATION_FAIL`;
- `SAMPLE_SCARCITY`;
- `ALPHA/GROSS_EDGE_FAIL`;
- `COST_FAIL`;
- `EXECUTION_MODEL_SENSITIVE_REVIEW`;
- `CAPACITY_FAIL`;
- `OPERATIONAL_FAIL`;
- `ROBUST_ECONOMIC_PASS`.

The terminal experiment decision remains controlled by the predeclared promotion gates; these labels explain mechanism, not provide post-hoc rescue.

---

## 23. Forward calibration is part of execution validation

Historical aggregated L2 cannot fully validate queue position or real latency.

Before production confidence in a passive strategy, forward/demo or appropriately small live shadow observations should compare:

- simulated versus observed order acceptance;
- time-to-fill / fill probability;
- partial fill behavior;
- cancel latency;
- message-rate behavior;
- realized versus simulated slippage/fees;
- predicted queue-scenario envelope versus observed outcomes.

Historical profitability alone cannot certify an unobservable FIFO model.

---

## 24. Required pre-promotion technical sign-off

Before a new promotional SC001 run, produce a short technical sign-off answering:

1. Are data semantics and archive transformations understood?
2. Is causality enforced mechanically?
3. Are contract units and cost formulas historically correct?
4. Is the appropriate execution kernel validated?
5. Does accounting independently reconcile from the fill ledger?
6. Are execution uncertainties explicit rather than hidden?
7. Are operational rate limits/capacity respected?
8. Is the run configuration immutable and reproducible?
9. Are promotional dates/assets uncontaminated for this implementation?
10. Can another implementation recompute the key ledger totals?

If any required answer is unresolved, the promotional run remains closed.
