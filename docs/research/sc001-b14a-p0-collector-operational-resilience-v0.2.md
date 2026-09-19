# SC001 — B14-A P0 Collector Operational Resilience Amendment v0.2

Date: 2026-09-19
Status: **FROZEN PRE-EVENT OPERATIONAL HARDENING / P0 RULES UNCHANGED**
Scope: `SCALPING RESEARCH / SC001`
Supersedes collector implementation semantics only from v0.1.

Parent research protocol:

`docs/research/sc001-b14a-p0-prospective-2026-09-25-headroom-protocol-v0.1.md`

## 1. Research rules unchanged

Unchanged:

- expiry = 2026-09-25T08:00:00Z;
- connect time = 07:28:30Z;
- capture = 07:29:00Z .. 08:02:00Z;
- T0 = 07:30:00Z;
- four frozen instruments;
- 50 bps hurdle;
- STRICT_COACTIVE_1S_NO_CARRY_FORWARD;
- no basis during collection.

## 2. Added persistent state

v0.2 preserves across process restarts:

- raw_trade_messages;
- normalized_trade_rows;
- invalid_trade_rows;
- reconnect_count;
- network connection_gaps;
- process_restart_count;
- process_restart_gaps;
- last_heartbeat_ms;
- subscription status.

Raw JSONL remains append-only.

## 3. Heartbeat

While WAITING:

- persist heartbeat at least every 30 seconds.

While connected/capturing:

- persist heartbeat on ping / incoming control or trade traffic.

## 4. Reboot/crash gap

On restart, record:

`PROCESS_RESTART_GAP`

from the last persisted heartbeat to the new process start.

For later P0 data validity, a family/event is DATA_INVALID if either:

- network connection gap;
- process restart gap;

intersects:

`[T0-1s, T0+6s]`

This strengthens the original fail-closed rule and does not alter the price/headroom definition.

## 5. Completed-event guard

If persisted state is already:

`B14A_P0_COLLECTION_COMPLETE`

a later systemd start exits successfully without recollecting the event.

## 6. Service manager

After self-test PASS, run under systemd with:

- boot start;
- restart on failure;
- network-online ordering;
- graceful SIGTERM;
- restart backoff.

A restart before the event is acceptable and explicitly logged.

A restart overlapping the critical readout window causes later DATA_INVALID/DEFER, never silent repair.
