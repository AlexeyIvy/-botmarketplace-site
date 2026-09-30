# SC001 — Reserve Candidate 2 Static Feasibility Card v0.1

Date: 2026-09-30
Status: STATIC FEASIBILITY ONLY / NO OUTCOME AUTHORIZED
Family: SAME_ASSET_CROSS_VENUE_CAUSAL_FLOW_PROPAGATION
Interim allocation: Strategy Manager Option B-Lite
Authority: docs/research/sc001-strategy-manager-existing-data-interim-work-addendum-v0.1.md

## Terminal B-Lite state

RESERVE_STATIC_FEASIBILITY_SURVIVE

This is not Discovery, Confirmation, Forward evidence or alpha. No experiment ID is assigned.

## 1. Mechanism fingerprint

Economic payer:
A participant or forced/informed flow reacts first on one venue. If information incorporation is not simultaneous across venues, the lagging venue may temporarily absorb the same information later. The economic payer is venue-fragmented price discovery under finite transport/liquidity response time.

Frozen draft economic roles:
- source/observation venue: OKX;
- lagging/execution venue: Bybit;
- same-underlying USDT linear perpetuals only;
- source venue is never a hedge leg;
- monetization, if ever authorized later, is one-sided directional trading on Bybit;
- entry + exit = 2 structural fills.

Why these roles are fixed now:
- both venues already have qualified public same-asset trade semantics and strict-coactive clock machinery;
- Bybit execution reuses the already-qualified conservative regular-user fee semantics from the current primary;
- venue roles are chosen before Candidate 2 response evidence and may not be swapped after outcome.

Causal trigger concept:
A completed one-second OKX public trade-tape aggressive-flow impulse, represented prospectively by a single signed aggressive-notional-imbalance architecture.

The numeric impulse threshold is NOT chosen in this B-Lite review. If Candidate 2 is later selected for an experiment, one threshold must be frozen from source-only/non-outcome activity semantics before any response price is opened. No grid is allowed.

Response object:
Signed Bybit same-underlying response in the source-flow direction.

Mechanism-derived response horizon:
exactly 2 seconds from the first actionable Bybit observation after the completed source bucket.

No horizon grid.

## 2. Mechanism-overlap verdict

Disposition:

RELATED_BUT_MATERIALLY_DIFFERENT_ARCHITECTURE

### Relative to legacy C8A

Legacy C8A was retained only as a broad conceptual fork:
- directional lead/lag;
- one traded venue;
- two fills;
- directional exposure.

It did not freeze a source-flow trigger, fixed leader venue, fixed lagging venue, or executable directional outcome protocol.

Candidate 2 is admissible only under the narrower fingerprint above:
- fixed OKX source;
- fixed Bybit lagging/execution venue;
- source aggressive-flow impulse as the causal object;
- no price-basis threshold trigger;
- no venue-role swap;
- one fixed two-second response horizon.

This is not merely a new numerical lag, threshold or symbol subset.

Important boundary:
If a later implementation drops the source-flow trigger and becomes generic price lead/lag, or changes source/lag roles after observing response, classify it as SAME_MECHANISM_VARIANT / DISGUISED_RESCUE_REJECT rather than this Candidate 2 fingerprint.

### Relative to C8B

C8B is paired four-fill transient relative-basis convergence. Candidate 2 is one-sided two-fill causal information propagation. The payer, trigger object and monetization architecture are different.

No C8B price-calibration outcome is used as Candidate 2 evidence.

## 3. Latency feasibility card

Canonical engineering-only C8 evidence:
docs/research/sc001-c8-d1e-strict-coactive-1s-pass-result-v0.1.md

Qualified representation:
STRICT_COACTIVE_1S_NO_CARRY_FORWARD

Engineering observations:
- 72,539 joint coactive seconds on the frozen clock day;
- joint coactive share about 0.83957;
- minimum joint-active seconds per hour 2,378;
- median absolute last-event timestamp skew 150.5 ms;
- p99 absolute last-event timestamp skew 846.7 ms.

These are clock/engineering facts only, not Candidate 2 return evidence.

Mechanism latency rule:
- source signal is calculated only after a complete one-second OKX bucket closes;
- earliest actionable decision is the next causal instant;
- response horizon is fixed at 2 seconds;
- latest acceptable end-to-end public-cloud decision/order-submission latency is 1.0 second after source-bucket close.

Reason:
A 2-second mechanism that requires more than half its horizon merely to observe/decide/transmit is not suitable for the target independent-trader architecture.

Static interpretation:
- existing 1-second cross-venue clock qualification does not structurally rule the mechanism out;
- historical event-time skew is close enough to the latency budget that live receive/decision latency is a serious gate;
- before any future outcome sentinel, a source-only/non-alpha live latency probe must show p99 end-to-end decision path <=1.0 second;
- failure of that future latency gate gives structural rejection before response outcomes.

Current static latency verdict:
FEASIBLE_BUT_HIGH_LATENCY_RISK

## 4. Edge-to-Fill card

Frozen draft execution venue:
Bybit only.

Structural fills:
2.

Reuse the current conservative Bybit regular-user product/zone fee reference:
- 11 bps/fill;
- two-fill fee floor = 22 bps.

Conservative reserves:
- spread/slippage/depth = 10 bps;
- execution/model reserve = 10 bps;
- maker rebate credit = 0;
- funding reference = 0 for the proposed 2-second response horizon.

two_fill_structural_burden_bps = 22 + 10 + 10 = 42.

Minimum prospective gross-movement scale:

52 bps.

This reuses the current SC001 two-fill safety posture:
structural burden + 10 bps reserve.

No Candidate 2 outcome has been opened to estimate whether this scale exists.

Static cost verdict:
UNKNOWN_PRE_OUTCOME / NOT_STRUCTURALLY_IMPOSSIBLE.

The mechanism has an explicit event-conditioned information-transfer payer, so static cost alone does not justify REJECT_COST. Any later response sentinel must clear the 52 bps gross scale prospectively; no maker/rebate or lower-fee rescue is allowed after outcome.

## 5. Prospective sentinel design draft — UNAUTHORIZED

Purpose:
Cheapest future test of whether a fixed OKX aggressive-flow impulse produces an actionable same-direction Bybit response large enough for a two-fill architecture.

Frozen draft:
- source venue: OKX;
- lagging/execution venue: Bybit;
- source object: public same-underlying USDT perpetual trades;
- source clock: completed 1-second bucket;
- impulse statistic family: signed aggressive-notional imbalance from trade-side semantics;
- one numeric source-only impulse threshold to be prospectively frozen later; no threshold grid;
- action timing: first causal Bybit observation after source bucket close;
- response horizon: exactly 2 seconds;
- no leader swap;
- no reverse-direction retry;
- no symbol winner selection;
- no L2;
- no PnL;
- no execution simulation in the first sentinel.

Candidate universe for future consideration:
reuse the already semantically qualified 12 same-underlying Bybit/OKX perpetual pairs unless a Strategy/User decision freezes a different source-only universe before any response outcome. No outcome-based symbol removal.

A future sentinel is not authorized by this document.

## 6. Fresh-evidence plan

If Strategy/User later selects Candidate 2 after the current primary result:

1. run a non-outcome live receive/decision-latency qualification for the fixed OKX->Bybit path;
2. freeze one numeric aggressive-flow impulse threshold using source-side activity semantics only;
3. freeze exact prospective chronology and fresh evidence start;
4. freeze exact 12-symbol or other source-only universe before response access;
5. create a new contamination record and only then assign an experiment ID;
6. collect/use fresh chronological/prospective evidence not used for this static review;
7. first price-bearing stage remains structural response headroom only, not PnL;
8. any positive Discovery must later receive fresh chronological/prospective Confirmation.

Forbidden fresh-evidence reuse:
- 2025-01-15 C8 engineering day as Candidate 2 outcome evidence;
- 2025-01-20 C8B calibration outcome as Candidate 2 outcome evidence;
- Candidate 1 fresh-window outcomes;
- B13-C protected interval.

## 7. Three-lens review

Market / financial:
The economic payer is coherent and opportunity frequency could be high, but a 52 bps two-fill gross requirement is demanding. The family remains worth a future cheap sentinel only because the trigger is event-conditioned information transfer rather than unconditional venue basis.

Engineering / trading:
Public trade sources and strict coactive second-level representation are already qualified. The dominant unresolved risk is live actionable latency, not basic data availability.

Statistics / evidence:
No response outcome is opened here. The design remains ADAPTIVE_DISCOVERY_GENERATED. Fixed venue roles, one horizon and no threshold grid bound multiplicity.

## 8. Do not do

Do not:
- run Candidate 2 now;
- read historical Candidate 2 lag/return outcomes;
- use old C8 price bodies to select threshold/leader/horizon;
- swap OKX and Bybit after response;
- scan 100ms/250ms/500ms/1s/2s/etc.;
- lower the 52 bps gross requirement after outcome;
- assign an experiment ID now;
- run Candidate 3;
- interfere with Candidate 1 fresh window.

## 9. Decision

RESERVE_STATIC_FEASIBILITY_SURVIVE

Meaning:
The family is coherent enough to remain the reserve candidate and may later be considered for a fresh prospectively frozen experiment. It is not authorized for execution and carries a mandatory future live-latency gate.
