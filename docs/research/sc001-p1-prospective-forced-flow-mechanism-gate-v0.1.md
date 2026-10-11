# SC001 P1 Prospective Forced-Flow Mechanism Gate v0.1

TASK_ID: SC001-P1-FLOW-CAUSAL-002
WORKER_ID: P1_PROSPECTIVE_EVENT
TERMINAL_STATUS: PROSPECTIVE_MECHANISM_DEFER_SOURCE_OR_LATENCY
Authorization: T0_DESIGN_ONLY
Outcome accessed: false
Market/source body accessed: false
Network/executor/VPS/collector used: false
Frozen rules changed: false

## DECISION

The frozen `E+1..E+2` S0 cannot be repaired into an online signal. Moving its
observation or entry until after five-second inactivity confirmation changes
timing, not the economic payer or monetization architecture. It is
`SAME_MECHANISM_VARIANT`; using the prior interval would be
`DISGUISED_RESCUE_REJECT`.

One economically different architecture is conceptually identifiable:
`EXTERNAL_FORCED_FLOW_TO_BYBIT_CAUSAL_PROPAGATION`. It uses an explicit
forced-flow event on a fixed source venue as the causal source and trades only a
temporarily lagging Bybit leg. Its payer is finite cross-venue price-discovery
delay, not post-cluster re-anchoring of the forced Bybit venue.

This is retained only as one DRAFT. Current canonical sources do not establish
that an external forced-flow message and its source-price state are publicly
available early enough to submit a Bybit order before the response. Therefore
the correct terminal decision is
`SOURCE_OR_LATENCY_DEFER`, represented by
`PROSPECTIVE_MECHANISM_DEFER_SOURCE_OR_LATENCY`. No experiment, engineering,
data acquisition, or outcome stage is authorized.

## EXACT BINDINGS

Current main and dispatch base:
`e1de40ede4f9126078cbd84cd87c85f234b2f458`.

Necessary source SHA256 values:

- Research Strategy Charter v0.1:
  `4423c0ca1aec69754f12a476f8587abe041e9670cf8e5600f677fd99a6a2a64b`
- Midcourse governance v0.2:
  `27198051695483799afee8e014f8125e59b819917bea894be22651381afc7180`
- Edge-to-Fill preflight v0.1:
  `21d43bb41f78e4f829cb47465236358fb30485b9e7bf25af4faf1c12ab861a7f`
- Portfolio review v0.1:
  `1fd1f00930da86911faa94b10e0d2765fd924f5a6d7f1687c7bdcfd7b2f25289`
- Forced-flow relative-dislocation fingerprint v0.2:
  `8d225dbbfb76fe489b3da380d14101c62e1713a14ab3d665f31bd7392d695ea3`
- Forced-flow S0 protocol v0.2:
  `331bc684246ed03470c2cb0008e167e7dd01c2efad41a37aa09d2b1122cf7f96`
- B13-C reversal protocol v0.1:
  `8f8035b0f1e9c7add09732d0e55e399b8a20a4357799193b06e80208b2c54829`
- B13-C binding outcome review v0.1:
  `5b1f45ec43875a3f1c6f5989b931a160315d3f1b4ec0458ff9e998de88fd4c5f`
- PR #468 causal audit at exact head
  `ca5c9dfd29b8f77f93d3c30696a647a09b81b6f2`:
  `7f2bf03ae8ccba63dae3a88ef643377aacbe988cc716df636d54df51a9be664f`

Strategy Control receipt `6102625423` requires a causal trigger after
availability, explicit lateness/watermark rules, a post-availability decision
bucket, separable Bybit return/cost estimand, and fresh evidence. It authorizes
no successor.

## STATIC CAUSAL ORDER

For any online design, distinguish the following times:

1. `X_src`: source exchange event time of the individual forced-flow event.
2. `R_src`: local receipt time of that event message.
3. `W_src`: watermark proving required source messages through the trigger
   boundary are complete.
4. `X_px_src` and `R_px_src`: source trade event and receipt times.
5. `B_src_close`: end of the source observation bucket.
6. `A_src`: time at which the finalized source event/price state is actually
   available to the decision process.
7. `X_byb` and `R_byb`: Bybit market event and receipt times used to verify
   that the lagging state still exists.
8. `D`: completed decision time.
9. `O`: Bybit order-submit time.
10. `F`: fill/acknowledgement time.

A causal order must prove:

`X_src <= R_src <= W_src <= B_src_close <= A_src <= D <= O <= F`

and, separately, that the economically relevant Bybit response is not already
complete before `O`.

The rejected cluster-end architecture cannot meet this order for its frozen
bucket. The cluster admits a continuation at exactly `E+5000 ms`, so safe
finality requires a watermark strictly after `E+5000 ms`. Its selected price
second starts before `E+2000 ms` and closes before `E+3000 ms`. The trigger
therefore depends on future membership information.

The single draft below removes that dependency by using an individual,
deduplicated source event and a finalized source bucket. It does not claim that
the event belongs to a future-defined cluster and does not require later
absence to label the trigger. This repairs causality only at the design level;
it does not prove a remaining opportunity.

Missing observable fields or facts in current sources are:

- an eligible external forced-flow source and exact public message semantics;
- source exchange-event and local receive timestamps in the same record;
- duplicate and late-arrival bounds;
- source bucket trade event, receive, close, and availability times;
- synchronized Bybit event/receive/availability times;
- clock-quality and cross-host clock-offset bounds;
- decision completion, order-submit, acknowledgement, and fill times;
- proof that Bybit remains unadjusted after all prior steps;
- an opportunity-frequency estimate from clean, independent evidence.

These are `UNKNOWN`; no latency number is invented.

## SAME-MECHANISM AND RESCUE SCREEN

The following are rejected without outcome work:

- wait until the old Bybit cluster is known closed, then measure or enter later;
- move E+1..E+2 to E+6, E+10, or another delay;
- retain the same cross-venue basis state and change only the hold horizon;
- alter cluster gap, minimum event count, size threshold, symbol subset, sign,
  H=52, or the seven-day interval;
- add an intensity/volatility/filter threshold learned from B13-C or S0;
- turn the same basis into a four-fill hedge solely to make convergence
  monetizable.

All preserve the parent forced-venue re-anchor thesis or tune it after failure.
They are not new mechanisms.

## ONE DISTINCT MECHANISM FINGERPRINT DRAFT

Status: `DRAFT_ONLY_SOURCE_AND_LATENCY_UNPROVEN`.

- parent/family lineage:
  portfolio Candidate 2, same-asset cross-venue causal flow propagation;
  no inheritance of S0 outcome eligibility.
- family:
  `EXTERNAL_FORCED_FLOW_TO_BYBIT_CAUSAL_PROPAGATION`.
- disposition:
  `RELATED_BUT_MATERIALLY_DIFFERENT_ARCHITECTURE` conceptually, but
  `SOURCE_OR_LATENCY_DEFER` operationally.
- economic payer:
  a forced, price-insensitive event moves a fixed source venue first; finite
  fragmentation/arbitrage/market-maker reaction time leaves Bybit temporarily
  stale. The payer must be a still-open Bybit price response after public
  receipt and order latency.
- causal trigger/state:
  one prospectively defined, individually observable external forced-flow event
  plus a completed source-price bucket, finalized by receive-time/watermark
  rules. No cluster-end or future absence claim.
- economic objects:
  source forced-flow event; source same-underlying perpetual trade state;
  directly executable Bybit perpetual price; Bybit order/fill state.
- monetization path:
  one-sided Bybit entry and exit only. The external venue is a signal source,
  never a hedge leg.
- entry architecture:
  decide only after event receipt, source bucket close, watermark, and proof
  that the contemporaneous Bybit state is available. Exact order type and
  executable price definition remain unfrozen pending feasibility.
- exit/termination anchor:
  one primary two-second response timescale inherited from the already
  published portfolio reserve rationale: finite venue propagation is expected
  to decay within seconds. No horizon grid or alternate horizon is proposed.
- structural fill count:
  two fills on Bybit. A paired version would require four fills and is excluded
  because it changes the object, doubles fee/fill surfaces, and is unsuitable
  as a rescue for weak headroom.
- latency dependency:
  very high. Survival requires a measured public-feed-to-order path shorter
  than the remaining Bybit response, not merely correct historical ordering.
- capital/risk constraint:
  USD 1,000 capacity is not the main obstacle; taker cost, adverse selection,
  stale-source risk, partial/non-fill, and abrupt common-market moves dominate.
  Exposure is one-leg and unhedged.
- relationship to rejected S0:
  S0 asked whether Bybit was displaced relative to OKX after a retrospectively
  closed Bybit liquidation cluster. This draft asks whether a fixed external
  forced-flow event reaches Bybit with an actionable lag. Payer, trigger,
  traded-leg role, and estimand differ.

No impulse-size threshold is selected here. Choosing a threshold from any
observed response, swapping leader/lagger, or searching event types would be
adaptive parameter search and is forbidden.

## EDGE-TO-FILL AND SMALL-CAPITAL TEST

The Edge-to-Fill control counts one-sided entry plus exit as two fills and a
paired trade as four. This draft uses two fills.

The prior S0 value `H=52 bps` is recorded only as a nonpromotional warning
about two-fill taker economics. It is not imported as this draft's hurdle and
is not lowered. A future, separately authorized pre-outcome cost card would
have to freeze current Bybit fee, spread/depth, model reserve, and any funding
term before opening alpha evidence.

Current classification:
`UNKNOWN_NEEDS_NON_ALPHA_DATA`.

The portfolio review states that ordinary SC001 information is commonly
low-single-digit bps and that the propagation family is attractive only if an
event-conditioned source impulse produces a much larger actionable response.
No such scale is established here. The architecture is economically relevant
for small capital only if:

- actionability survives real receive, compute, submit, and fill latency;
- gross Bybit response exceeds the new conservative two-fill burden;
- opportunities occur often enough that short occupancy matters;
- losses from synchronous/common shocks and stale triggers remain bounded.

None is proven by static sources.

## COMPETING NULL AND EVIDENCE PLAN

Primary null:
both venues reprice nearly simultaneously to a common-market shock; apparent
source leadership is feed latency, timestamp error, or selection. Under this
null, basis compression or source-first timestamps do not imply a profitable
Bybit leg.

Required estimand for any future sentinel:
signed executable Bybit price change from an orderable post-trigger anchor to
the single frozen two-second termination anchor, net treatment deferred until
cost semantics are frozen. Cross-venue basis change is diagnostic only and
cannot substitute for Bybit-leg return.

A possible future sequence, only if Strategy Manager separately dispatches it:

1. non-alpha source-semantic and timestamp-feasibility review;
2. bounded public-feed receive/clock/order-path latency qualification with no
   outcome search;
3. prefreeze one source, one trigger definition, Bybit as lagging/traded venue,
   one two-second timescale, two-fill cost card, and exact stop rules;
4. allocate a new post-freeze evidence window independent of the B13-C and S0
   intervals;
5. run at most one smallest sentinel, with no threshold, leader, symbol, or
   horizon grid;
6. treat any positive result as adaptive Discovery requiring fresh
   chronological/prospective Confirmation.

The present task authorizes none of these actions.

## THREE-LENS VERDICT

Market/financial:
a finite venue-propagation payer is distinct in principle, but professional
arbitrage competes directly for it. Small capacity is adequate; latency and
two-fill burden are potentially fatal. Economic viability is UNKNOWN.

Programmer/trader:
the draft avoids future cluster membership, but required source, receive,
watermark, clock-quality, bucket-availability, decision, order, and fill
identities are absent. Static eligibility cannot pass.

Mathematician/statistician:
leader choice, impulse definition, threshold, horizon, and symbol selection are
major multiplicity surfaces. Only a single pre-frozen source/leader/timescale
on fresh evidence could be interpretable. Common-shock simultaneity is the
mandatory null.

Combined verdict:
`PROSPECTIVE_MECHANISM_DEFER_SOURCE_OR_LATENCY`.

## NEXT ALLOWED ACTION

No automatic successor. Strategy Manager may decide whether one bounded,
non-alpha source/latency feasibility task for this exact draft is worth its
research cost. If not, close this forced-flow branch and return effort to the
portfolio reserve/B15-P1 work already governed elsewhere.

No new experiment ID, source acquisition, implementation, collector change,
outcome run, or host task follows from this report.

## DO NOT DO

- Do not run or reinterpret the frozen S0.
- Do not move the old entry, observation, threshold, horizon, symbol set, H=52,
  dates, sign, denominator, or evidence role.
- Do not use B13-C or S0 evidence to choose a new source, trigger threshold,
  leader, horizon, or winner symbols.
- Do not claim that historical event-time order proves live orderability.
- Do not treat basis convergence as executable Bybit profitability.
- Do not invent latency, source completeness, opportunity frequency, or fill
  quality.
- Do not create a four-fill hedge version as a rescue.
- Do not build code, acquire data, access VPS/collectors, or dispatch a follow-up
  task from this worker.
- Do not merge, close, retarget, or otherwise mutate PR lifecycle.

## NO SHARED-STATE CHANGE

No roadmap, governance, Strategy State, contamination registry, reusable
registry, or frozen artifact was modified. The one draft and defer disposition
are task-local proposals for independent Strategy Review.
