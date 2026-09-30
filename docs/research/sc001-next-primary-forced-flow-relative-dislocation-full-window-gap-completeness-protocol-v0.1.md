# SC001 — Forced-Flow Full-Window Gap / Completeness Readout Protocol v0.1

Date: 2026-09-30
Status: FROZEN DESIGN / SYNTHETIC-ONLY UNTIL WINDOW CLOSE
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01

## Purpose

Define the final read-only acquisition-integrity check for the full frozen window before any real S0 price/outcome access.

Window:

2026-09-30T00:00:00Z <= event_time < 2026-10-07T00:00:00Z.

The readout asks whether the B13-C source-gap ledger is complete enough to deterministically censor affected clusters. It does not require the window to be gap-free.

## Allowed real inputs after window close

Only:
- collector_state.json;
- connection/connection_events.jsonl.

No liquidation event rows, prices, trade archives, clusters, returns or PnL are required to determine ledger qualification.

## State requirements

Require:
- collector stage = SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3;
- frozen symbols exact 12/12;
- strategy_outcomes_calculated = false;
- collector_start_ms <= window_start_ms;
- last persisted heartbeat/stopped marker >= window_end_ms;
- source_qualified_symbols = 12.

A heartbeat before the window end cannot establish full-window coverage.

## Gap reconstruction

Read the complete connection ledger in timestamp order, including rows before window start when needed to establish the state at the opening boundary.

Availability state:
- SUBSCRIBED closes an unavailable interval;
- DISCONNECTED opens an unavailable interval;
- STOPPED opens an unavailable interval;
- PROCESS_RESTART_GAP contributes its explicit [start_ms,end_ms] interval.

Also include every explicit collector_state.process_restart_gaps interval.

Initial state at window start is derived causally from ledger events preceding the boundary:
- if latest valid availability state before start is SUBSCRIBED, coverage starts available;
- otherwise coverage begins unavailable until the next SUBSCRIBED event.

At window end:
- if unavailable remains open, close it at window_end_ms for reporting;
- this does not become a silent complete interval.

Merge overlapping/touching gap intervals after clipping to the frozen window.

## Qualification

PASS token:

FORCED_FLOW_FULL_WINDOW_GAP_LEDGER_PASS

PASS means:
- ledger/state schemas are internally valid;
- the opening availability state is determinable;
- the collector record proves observation through the closing boundary;
- every disconnect/process restart interval is deterministically representable;
- no unbounded/ambiguous source outage remains.

PASS does NOT mean zero gaps.

Recorded gaps are permitted and remain mandatory censor intervals for event clusters.

REVIEW token:

FORCED_FLOW_FULL_WINDOW_GAP_LEDGER_REVIEW

REVIEW if:
- closing boundary is not covered by persisted collector state;
- state/ledger schema is inconsistent;
- process-gap interval has unresolved bounds;
- connection availability around a boundary cannot be determined;
- source-qualified universe is not 12;
- any integrity condition needed for deterministic censoring is unresolved.

No arbitrary maximum gap-duration threshold is introduced here. Source/sample sufficiency remains decided later by the already frozen S0 sample gate after gap censoring.

## Required outputs

Report only source-integrity aggregates:
- window start/end;
- collector start;
- closing heartbeat/stopped timestamp;
- connection event counts;
- merged gap count;
- merged gap total milliseconds;
- gap fraction of the seven-day wall-clock window;
- process restart count;
- source-qualified symbol count;
- exact merged gap intervals;
- qualification PASS/REVIEW;
- all outcome firewalls false.

No per-symbol liquidation frequency or event-size distribution.

## Event-level use

A later authorized cluster materializer must censor a cluster if:

[cluster_start - 5000 ms, cluster_end + 5000 ms]

overlaps any qualified merged source-gap interval.

No gap is interpreted as zero liquidations.

## Outcome firewall

The readout must not:
- open liquidation event rows;
- construct clusters;
- open trade archives;
- read prices;
- calculate basis/dislocation;
- calculate returns/PnL;
- execute S0;
- mutate/restart the collector.
