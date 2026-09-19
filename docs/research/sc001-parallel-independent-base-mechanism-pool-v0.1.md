# SC001 — Parallel Independent Base Mechanism Pool v0.1

Date: 2026-09-19
Status: **NON-ALPHA DESIGN / NO NEW CANDIDATE ID / NO OUTCOME AUTHORIZED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.98.md`;
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`;
- `docs/research/sc001-strategy-landscape-v0.9.md`.

## 1. Objective

While B13-C protected liquidation data accumulates, identify at most three new independent base mechanisms with:

- a real economic payer/source;
- prospective source feasibility;
- bounded fill count;
- a plausible path to edge scale above cost;
- no dependence on C1-C12 terminal features;
- no use of protected B13-C liquidation outcomes.

No market outcome is opened by this pool.

---

## 2. B14-A — Dated-futures final-settlement basis convergence

### Mechanism

Trade a crypto dated futures contract versus a mature hedge/reference shortly before the contract's deterministic final settlement.

The economic anchor is contractual:

`dated futures final settlement -> exchange-defined settlement/index value`

This differs from ordinary C1 spot/perp basis mean reversion because the dated contract has a fixed terminal convergence event.

### Candidate architecture

Illustrative delta-neutral structure:

1. enter dated futures leg;
2. enter hedge leg in mature perpetual or spot;
3. hold dated futures through final settlement;
4. close hedge after settlement.

Potential structural fills:

- dated futures entry = 1;
- hedge entry = 1;
- hedge exit = 1;
- futures exit may be replaced by contractual settlement.

Preliminary fill count:

`3 structural executions + settlement mechanics`

Exact settlement fee/cost must be sourced before any economic threshold is frozen.

### Economic payer

Mispricing between the expiring dated contract and its terminal settlement value.

Unlike ordinary convergence, the futures leg cannot remain away from terminal settlement indefinitely.

### Expected scale

Unknown.

The mechanism can plausibly produce tens of bps only if basis remains material sufficiently near settlement.

That must be screened prospectively before execution modeling.

### Key risks

- settlement index methodology;
- settlement/expiry fee;
- hedge basis risk;
- exchange trading cutoff before settlement;
- mark/index averaging window;
- price limits;
- low near-expiry liquidity;
- futures contract denomination;
- hedge close after settlement.

### Source feasibility

Potentially strong on OKX because public instrument metadata exposes FUTURES contract identity/expiry fields and official settlement rules are documented.

Historical/current futures trade and mark/index source feasibility must be audited separately.

### Independence from prior candidates

Not C1 rescue:

- C1 relied on ordinary spot/perp basis convergence without a fixed contract termination anchor;
- B14-A relies on deterministic final settlement.

Not B13-B:

- B13-B is new-contract launch price discovery;
- B14-A is expiring-contract terminal convergence.

### Non-alpha disposition

`SELECT_FOR_SOURCE_AND_SETTLEMENT_SPEC_PREFLIGHT`

No candidate ID yet.

---

## 3. B14-B — Persistent multi-settlement cross-venue funding carry

### Mechanism

Maintain a delta-neutral cross-venue perpetual pair across multiple funding settlements so entry/exit fills are amortized over a longer funding horizon.

Primary economic source:

`cumulative realized funding differential`

not short-term price convergence.

### Independence and relationship to B13-A

This is materially different from rejected B13-A only if it freezes:

- multi-settlement holding horizon;
- cumulative signed funding accounting;
- basis/margin risk;
- fill-cost amortization;
- no one-settlement exit.

It may not reuse B13-A as if merely changing a threshold.

### Structural architecture

Still requires paired entry/exit:

`4 fills per carry cycle`

but those fills are amortized over N funding settlements.

Additional costs/risks:

- collateral fragmentation;
- basis drift;
- liquidation buffer;
- venue/counterparty exposure;
- funding-sign changes;
- capital lock.

### Expected scale

B13-A showed one-settlement differentials are ordinarily very small.

Therefore persistent carry is only plausible if cumulative signed differential is stable over a sufficiently long hold.

This is not assumed.

### Source feasibility

Strong:

- OKX/Bybit funding sources already qualified.

Fresh evidence problem:

- H1-2025 funding values are already contaminated by B13-A structural design;
- any B14-B structural value screen needs a separately assigned fresh nonpromotional window.

### Non-alpha disposition

`HOLD_NEW_ARCHITECTURE / LOWER_PRIORITY`

Do not run yet.

Reason:

- genuine new architecture possible;
- but adjacent to B13-A and adds materially more risk/holding complexity.

---

## 4. B14-C — Scheduled venue trading-resumption dislocation

### Mechanism

A venue or contract is temporarily unavailable/suspended while a mature external reference continues price discovery.

At a prospectively announced or objectively timestamped resumption, test whether local price reopening creates a large relative dislocation.

Economic source:

`stale local inventory / accumulated external price discovery during venue inactivity`

### Independence

Distinct from C8B ordinary continuous-market basis because one venue is deliberately/non-randomly inactive before the event.

Distinct from B13-B launch because the local contract already has trading history before suspension.

### Structural architecture

Likely paired relative-value:

- local resumed leg;
- external hedge;
- eventual unwind;

normally 4 fills.

### Expected scale

Potentially larger than ordinary C8B dislocations because external price discovery can accumulate while one market is inactive.

But the edge may disappear essentially at reopen before a non-colocated trader can execute.

### Source feasibility risk

High.

Need authoritative:

- exact suspension start;
- exact resumption time;
- affected instrument scope;
- historical trade source around reopen;
- mature external reference.

A complete historical event census may be difficult.

### Execution feasibility risk

Very high.

A public-cloud/VPS strategy may be structurally too slow if reopening immediately reprices to the external venue.

### Non-alpha disposition

`DEFER_SOURCE_AND_EXECUTION_FEASIBILITY`

Do not assign candidate ID.

---

## 5. Four-role comparison

### Programmer / systems engineer

B14-A is cleanest:

- deterministic event clock;
- official contract metadata;
- bounded state machine;
- no cross-venue semantic identity requirement if hedge is same venue.

B14-B uses already-qualified funding sources but requires longer stateful accounting.

B14-C has the largest event-source and latency fragility.

### Trader

B14-A has the strongest structural reason for convergence.

B14-B may exist economically but likely ties capital for small carry.

B14-C can show large gaps but may be inaccessible after reopening.

### Financial

B14-A can potentially reduce the four-fill burden because the dated leg settles contractually instead of requiring an exit fill.

That makes its edge-to-fill architecture materially more attractive than ordinary paired convergence.

B14-B adds basis/margin/counterparty risk over time.

B14-C retains full four-fill/legging burden under event-time latency.

### Mathematics / statistics

B14-A inference unit should be expiry event × contract.

Do not treat ticks as independent observations.

Need multiple expiries/contracts, not one spectacular expiry.

B14-B inference should be carry-cycle blocks, not individual funding settlements.

B14-C inference should be resumption events.

## 6. Selection

Advance only:

`B14-A DATED FUTURES FINAL-SETTLEMENT BASIS CONVERGENCE`

to a source/specification preflight.

Hold B14-B.

Defer B14-C.

## 7. B14-A next preflight

Before any price outcome verify only:

- exact OKX dated-futures product semantics;
- expiry/settlement timestamp fields;
- final settlement index/method;
- whether futures trading ends before settlement;
- settlement fee;
- exact contract denomination;
- availability of historical/current FUTURES trade source;
- availability of causal hedge/reference source;
- prospective future expiry identities.

No basis value or price outcome.

## 8. Candidate-ID gate

B14-A is not yet C13/C14.

Only after source/specification and Edge-to-Fill feasibility pass may a candidate ID be considered.
