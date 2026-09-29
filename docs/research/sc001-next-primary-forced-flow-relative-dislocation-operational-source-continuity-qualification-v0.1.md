# SC001 — Next Primary Forced-Flow Relative Dislocation Operational Source Continuity Qualification v0.1

Date: 2026-09-29
Status: LIVE FRESH-WINDOW CONTINUITY NOT YET ESTABLISHED / RETURN TO STRATEGY GATE
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01

## Purpose

Read-only verify whether the existing frozen B13-C liquidation acquisition path can support the fixed fresh window:

2026-09-30T00:00:00Z <= event_time < 2026-10-07T00:00:00Z.

No collector mutation, replacement, restart, window movement or reconstruction is authorized by this qualification.

## Canonical operational evidence

Existing frozen collector:
- implementation freeze: docs/research/sc001-b13c-bybit-prospective-liquidation-collector-implementation-freeze-v0.3.json;
- resilience protocol: docs/research/sc001-b13c-prospective-liquidation-collector-operational-resilience-v0.2.md.

Last canonical read-only state census:
docs/research/sc001-b13c-source-quality-state-census-result-v0.1.json.

At cutoff 2026-09-26T21:05:32.973Z it reported:
- status = B13C_COLLECTION_RUNNING;
- connection_status = CONNECTED;
- source_qualified_symbols = 12;
- invalid_event_count = 0;
- reconnect_count = 13;
- cumulative_connection_gap_ms = 271106;
- process_restart_count = 1;
- cumulative_process_gap_ms = 18183.

This establishes historical operational health through that cutoff only.

## Current read-only visibility

At this qualification:
- BotMarketplace VPS Reader exposes only logical root b15_identity_inventory;
- it does not expose the B13-C collector state/log/connection ledger root;
- Research Runner advertises sc001_data only as an execution input root and provides no direct read-only input-file browser;
- no research/outcome job was launched to bypass that read-only limitation.

Therefore a live heartbeat/systemd/collector_state check sufficiently close to the 2026-09-30 window start cannot be established through the currently exposed read-only surface.

## Verdict

B13C_FRESH_WINDOW_CONTINUITY_NOT_ESTABLISHED_READONLY

This is not evidence that the collector is unhealthy. It means continuity for the frozen fresh window has not been proven with currently available read-only access.

Binding consequence:
- do not execute S0;
- do not move the fresh window;
- do not reconstruct missing prospective liquidation events from alternate sources;
- do not mutate/restart/replace the collector as part of this qualification;
- return to Strategy/User gate.

Before any S0 authorization, require read-only operational evidence that covers the fresh-window boundary, including at minimum:
- collector/service running state;
- current connection/subscription state for the frozen 12 symbols;
- current heartbeat;
- collector_state freshness;
- connection/process gap ledger sufficient to censor affected clusters.

A separately approved non-outcome operational diagnostic may be used if direct VPS Reader exposure remains unavailable. It must not inspect liquidation sizes/distributions, cluster outcomes, price, returns or PnL.
