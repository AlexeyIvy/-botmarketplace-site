# SC001 — Post-C11 Independent Base Opportunity Pool v0.1

Date: 2026-09-19
Status: **NON-ALPHA STRUCTURAL DESIGN / NO C13+ ID ASSIGNED / NO OUTCOME AUTHORIZED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.81.md`;
- `docs/research/sc001-independent-base-opportunity-design-brief-v0.1.md`;
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`;
- `docs/research/sc001-c11-final-three-role-disposition-review-v0.1.md`.

## 1. Design objective

Identify at most three independent base opportunities that:

- do not require C1-C12 weak features to exist;
- have a direct economic payer/source;
- can plausibly exceed structural fill burden;
- have free/public source feasibility;
- are not parameter-neighbor rescues.

No market outcome is opened by this review.

## 2. B13-A — Cross-venue funding-differential carry

### Mechanism

Same underlying, two perpetual venues.

Prospectively:

- long the lower-funding / receive-more-favorable leg;
- short the higher-funding / pay-less-favorable leg;
- hold through a frozen funding settlement;
- close both legs after the settlement under frozen timing.

Primary edge source is the actual funding cash transfer, not short-horizon price prediction.

### Independence

Distinct from C9:

- C9 tested scheduled funding/mark-index price normalization;
- B13-A targets the funding transfer itself.

Distinct from C8B:

- C8B tested ordinary transient price-basis convergence;
- B13-A does not require price convergence to create the primary gross transfer.

### Edge-to-Fill

Structural fills:

- two legs in;
- two legs out;
- total = 4 fills.

Therefore cost burden is material.

Proceed only if a prospective metadata-only funding screen shows that gross cross-venue funding differential itself can exceed:

`fee floor + spread/legging reserve + execution reserve`

with enough event frequency.

Do not assume ordinary funding is sufficient.

### Data feasibility

Potential public/free sources exist:

- Bybit historical funding-rate endpoint;
- OKX funding-history / historical-data infrastructure already used elsewhere in the project;
- instrument funding intervals are queryable.

### Non-alpha disposition

`ELIGIBLE_FOR_CHEAP_STRUCTURAL_PREFLIGHT`

Required next preflight:

- source semantics;
- same-symbol/contract comparability;
- funding timestamps/intervals;
- fee/fill-count burden;
- metadata-only or funding-value-only magnitude/frequency screen;
- no price PnL.

No C13 ID yet.

---

## 3. B13-B — Scheduled new-perpetual launch cross-venue price-discovery dislocation

### Mechanism

Use prospectively announced launch time of a new OKX perpetual where a sufficiently mature same-underlying reference already trades on another qualified venue.

At launch, test whether the new contract exhibits a large temporary relative-price dislocation versus the pre-existing reference.

The base mechanism is:

`scheduled new-market price discovery / inventory transfer`

not ordinary continuous-market cross-venue basis.

### Independence

Distinct from C8B because:

- event is an exogenous contract launch;
- the new venue/instrument has no mature local price history at t=0;
- initial inventory establishment and price discovery create a different structural state.

Distinct from C3/C11 because:

- direction is relative to an external mature reference, not inferred from first impulse sign.

### Edge-to-Fill

A truly delta-neutral paired implementation likely requires four fills.

Therefore require a cheap sentinel showing launch dislocations materially larger than ordinary C8B ~single-digit-bps scale and large enough to clear a 4-fill burden.

No maker-queue assumption in the primary feasibility stage.

### Data feasibility

OKX publishes new-listing/perpetual-launch announcements with exact scheduled enable times.

Historical/public trade data and external-venue references may make event reconstruction feasible.

Potential issue:

- historical reference-instrument availability and exact launch-time archive coverage must be audited before any outcome.

### Non-alpha disposition

`ELIGIBLE_FOR_SOURCE_AND_HEADROOM_PREFLIGHT`

Required next preflight:

- prospectively definable event universe;
- exact launch timestamps;
- mature reference-venue availability before launch;
- structural 4-fill burden;
- data/source feasibility;
- no outcome until event universe and sentinel are frozen.

No C14 ID yet.

---

## 4. B13-C — Explicit liquidation-flow event transfer

### Mechanism

Use an actual liquidation/forced-close event identifier rather than generic aggressive-flow imbalance.

Economic source:

`mandatory deleveraging / forced inventory transfer`

Potential future question:

Does directly observed liquidation flow create a repeatable short-horizon impact state large enough to support a causal trade or execution policy?

### Independence

This is not C5 if and only if:

- event identity comes from explicit liquidation semantics;
- it does not reconstruct "liquidation-like" events from the same C5 flow thresholds;
- direction/horizon are frozen independently before outcome.

### Edge-to-Fill

Potentially 2 fills for one-sided impact trading.

But expected information scale cannot yet be stated credibly without qualified historical liquidation data.

### Data feasibility

Current project has no qualified long historical public liquidation-event dataset with the same evidence quality as OKX trade archives.

Public/current APIs contain liquidation semantics, but historical free coverage adequate for a robust study has not been qualified.

### Non-alpha disposition

`DEFER_DATA_FEASIBILITY`

Do not assign candidate ID.

---

## 5. Comparative structural review

### B13-A funding differential carry

- independent payer: yes, funding transfer;
- directional prediction required: no;
- fills: 4;
- cost burden: high;
- possible edge scale: can be structurally large in extreme funding states, unknown breadth;
- free data feasibility: plausible;
- hidden-rescue risk: moderate/low if price convergence is not required;
- disposition:
  `ELIGIBLE_FOR_CHEAP_STRUCTURAL_PREFLIGHT`.

### B13-B launch dislocation

- independent payer/mechanism: initial price discovery / inventory transfer;
- directional prediction required: relative-value direction from external reference;
- fills: likely 4;
- cost burden: high;
- possible edge scale: plausibly much larger than ordinary continuous-market basis, not yet measured;
- free data feasibility: plausible but event-source audit required;
- hidden-rescue risk: moderate because ordinary C8B failed; event identity must remain the defining difference;
- disposition:
  `ELIGIBLE_FOR_SOURCE_AND_HEADROOM_PREFLIGHT`.

### B13-C explicit liquidation flow

- independent payer/mechanism: forced deleveraging;
- fills: 2;
- potential scale: plausible;
- historical data feasibility: currently unqualified;
- hidden-rescue risk: high if reconstructed from generic C5 flow;
- disposition:
  `DEFER_DATA_FEASIBILITY`.

## 6. Three-role synthesis

### Programmer/trader

B13-A has the cleanest accounting identity: funding transfer can be separated from price PnL.

B13-B has the strongest event-specific price-discovery rationale but requires careful event/reference synchronization.

B13-C should not proceed until a true liquidation source is qualified.

### Financial

B13-A is attractive only if the funding transfer itself clears four-fill costs; do not rely on favorable price movement.

B13-B is attractive only if launch dislocations are structurally much larger than ordinary C8B effects.

B13-C has a credible forced-flow payer but currently lacks evidence infrastructure.

### Mathematics/statistics

For B13-A the inference unit should be funding settlement event × symbol pair, with cross-event/time blocking.

For B13-B the inference unit should be launch event, not ticks.

Both need event breadth; a few spectacular episodes cannot establish a systematic strategy.

## 7. Selection decision

No candidate ID is assigned yet.

Advance only:

1. B13-A to a **funding-differential structural preflight**;
2. B13-B to a **launch-event source/headroom preflight**.

Keep B13-C deferred.

Run the cheaper non-alpha preflight first:

`B13-A FUNDING DIFFERENTIAL STRUCTURAL PREFLIGHT`

Reason:

- exact cash-transfer mechanism;
- easier source semantics;
- no market-price outcome required for the first feasibility step;
- a simple funding-magnitude/frequency vs 4-fill-burden check can kill the idea cheaply.

## 8. Immediate next action

Design and freeze B13-A metadata/value-only structural preflight.

It may inspect official funding rates/timestamps and static cost arithmetic only.

It may not calculate strategy price PnL, optimize symbol subset by return, or assign C13 until structural feasibility is established.
