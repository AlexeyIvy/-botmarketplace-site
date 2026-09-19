# SC001 — B13-C Prospective Liquidation Collector Operational Resilience Amendment v0.2

Date: 2026-09-19
Status: **FROZEN OPERATIONAL HARDENING / RESEARCH SEMANTICS UNCHANGED**
Scope: `SCALPING RESEARCH / SC001`
Supersedes collector implementation semantics only from v0.1.

## 1. Research semantics unchanged

Unchanged:

- Bybit allLiquidation source;
- frozen 12-symbol universe;
- protected prospective evidence role;
- no threshold/symbol/return/PnL inspection;
- append-only raw/event JSONL.

## 2. Added operational resilience

v0.2 adds:

- persistent `last_heartbeat_ms`;
- `process_restart_count`;
- `process_restart_gaps`;
- `cumulative_process_gap_ms`;
- restart-gap records in the connection ledger.

Heartbeat is refreshed at least on:

- WebSocket ping cadence;
- any received WebSocket message;
- clean shutdown.

## 3. Reboot/crash interpretation

After v0.2 is active, a process restart records a potential source gap from the last persisted heartbeat to the new process start.

Future B13-C completeness analysis must consider both:

- network reconnect gaps;
- process/reboot gaps.

No interval covered by either gap may be silently treated as complete.

## 4. v0.1 -> v0.2 migration

v0.1 had no reliable process heartbeat.

Therefore the one-time migration must be logged externally as:

`PLANNED_SYSTEMD_MIGRATION_GAP`

with explicit stop/start timestamps.

Do not infer the migration-gap start from v0.1 `last_message_ms`, because liquidation messages can naturally be sparse.

## 5. Service manager

After self-test PASS, run under systemd with:

- start on boot;
- restart on failure;
- network-online ordering;
- graceful SIGTERM;
- restart backoff.

tmux is no longer the authoritative process supervisor after migration.
