# SC001 Current Roadmap and Stop Rules v5.207

Date: 2026-09-29
Status: NEXT PRIMARY FORCED-FLOW PREFREEZE / S0 NOT AUTHORIZED

Supersedes:
docs/research/sc001-current-roadmap-and-stop-rules-v5.206.md

Governance change:
NONE.

## Primary research priority

Next primary family:

VENUE_LOCAL_FORCED_FLOW_RELATIVE_DISLOCATION

Current terminal handoff:

PREFREEZE_READY_FOR_STRATEGY/USER_GATE

Binding prefreeze:
- feasibility: docs/research/sc001-next-primary-forced-flow-relative-dislocation-feasibility-card-v0.2.md;
- mechanism fingerprint: docs/research/sc001-next-primary-forced-flow-relative-dislocation-mechanism-fingerprint-v0.2.json;
- fee qualification: docs/research/sc001-next-primary-forced-flow-relative-dislocation-fee-qualification-v0.1.md;
- source-semantic gate: docs/research/sc001-next-primary-forced-flow-relative-dislocation-source-semantic-gate-v0.2.md;
- S0 protocol: docs/research/sc001-next-primary-forced-flow-relative-dislocation-s0-protocol-v0.2.md;
- operational continuity: docs/research/sc001-next-primary-forced-flow-relative-dislocation-operational-source-continuity-qualification-v0.1.md;
- contamination registry: docs/research/sc001-contamination-registry-v0.39.json.

Frozen common S0 cost references:
- regular-user product/zone conservative taker fee = 11 bps/fill;
- two-fill fee floor = 22 bps;
- structural burden = 42 bps;
- H = 52 bps.

Fresh window remains fixed:
2026-09-30T00:00:00Z <= event_time < 2026-10-07T00:00:00Z.

Do not move or reconstruct this window.

## S0 authorization state

S0 execution is NOT authorized.

Before any S0 outcome access require all:
1. source-semantic/economic-identity qualification PASS;
2. binding pre-outcome implementation handshake PASS;
3. read-only B13-C acquisition continuity established across the frozen fresh-window boundary;
4. explicit Strategy/User execution authorization.

Current operational continuity state:

B13C_FRESH_WINDOW_CONTINUITY_NOT_ESTABLISHED_READONLY

Therefore return to Strategy/User gate rather than moving the window or reconstructing events.

No C-series experiment ID is assigned before these gates.

## B15-P2 branch

B15-P2 is secondary/source branch, not the default primary capital-growth line.

Frozen B15-P2 P0 remains unchanged:

DEFER_SOURCE_COVERAGE

Do not rerun or modify its frozen P0 as rescue.

Source/semantic-only continuation may proceed only under its existing firewalls and may not influence the new primary's fee, threshold, horizon, symbol or outcome choices.

## Other branch boundaries

- B15-P1 remains unchanged under its operational freeze.
- B13-C simple same-venue S0 remains terminal; RB021 is reused only as frozen event/state semantics.
- B14-B remains terminal.
- B14-A and B13-B remain deferred/rare-event branches under existing governance.
- Candidate 2 and Candidate 3 from the Strategy Manager portfolio review remain reserve/design only; no parallel outcome access.

## Stop rules for the next primary

Do not:
- inspect the B13-C protected interval for threshold/horizon/symbol design;
- search liquidation magnitude, event count, cluster gap, entry delay or horizon;
- lower H=52 bps after outcome;
- reduce the 7-day or 12-symbol breadth denominators;
- mutate the existing liquidation collector;
- substitute alternate reconstructed liquidation events for missing prospective acquisition;
- run price/outcome S0 without the required preconditions;
- open Candidate 2/3 outcome work in parallel.

The next roadmap transition requires a Strategy/User gate decision after the pending pre-outcome qualifications. No governance amendment is required.
