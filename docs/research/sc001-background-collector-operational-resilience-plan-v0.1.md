# SC001 — Background Collector Operational Resilience Plan v0.1

Date: 2026-09-19
Status: **READY FOR TMUX -> SYSTEMD MIGRATION**
Scope: `SCALPING RESEARCH / SC001`

## 1. Protected collectors

### B13-C

Final supervised runner:

`research/sc001/sc001_b13c_bybit_prospective_liquidation_collector_v0_3.py`

Freeze:

`docs/research/sc001-b13c-bybit-prospective-liquidation-collector-implementation-freeze-v0.3.json`

### B14-A P0

Final supervised runner:

`research/sc001/sc001_b14a_p0_prospective_trade_collector_v0_3.py`

Freeze:

`docs/research/sc001-b14a-p0-collector-implementation-freeze-v0.3.json`

## 2. systemd services

B13-C:

`sc001-b13c-liquidation.service`

B14-A:

`sc001-b14a-p0.service`

Both services:

- start automatically at VPS boot;
- order after network-online and time-sync targets;
- restart on process failure / crash;
- use 15-second restart backoff;
- receive graceful SIGTERM;
- run as user `botmarket`;
- use explicit SC001_DATA_ROOT;
- keep file logs in the existing SC001 data roots.

## 3. Collector-level resilience

Both final collectors add persistent heartbeat and restart-gap accounting.

B13-C records:

- network reconnect gaps;
- process/reboot gaps;
- cumulative process gap duration.

B14-A records:

- network gaps;
- process/reboot gaps;
- persistent counters across restarts.

If a B14-A process/network gap intersects the frozen critical window:

`[T0-1s, T0+6s]`

the later readout must fail closed as DATA_INVALID / DEFER.

No restart is allowed to hide a missing prospective interval.

## 4. Completed P0 guard

After a successful B14-A P0 collection:

`B14A_P0_COLLECTION_COMPLETE`

future service starts exit successfully without recollecting the event.

If the event window has ended without COMPLETE, the collector terminates as REVIEW and does not enter a restart loop.

## 5. tmux migration

Migration helper:

`ops/systemd/migrate_sc001_collectors_to_systemd.sh`

Before stopping any current tmux session it must:

1. self-test B13-C v0.3;
2. self-test B14-A P0 v0.3;
3. install both unit files;
4. run systemd unit verification;
5. enable both services for boot.

Only then does it stop:

- `b13ccol`;
- `b14ap0`.

The stop/start interval is written to:

`~/sc001_data/SC001_COLLECTOR_RESILIENCE/operational_events.jsonl`

as:

`PLANNED_SYSTEMD_MIGRATION_GAP`

This prevents the migration interruption from becoming invisible evidence.

## 6. Failure coverage

### Covered

- SSH / Termux disconnect;
- user phone power-off;
- VPS reboot;
- provider-initiated ordinary reboot;
- Python process crash;
- uncaught collector exception;
- OOM/process kill followed by service restart;
- temporary network loss;
- WebSocket stale connection;
- collector process restart;
- B14-A reboot before event;
- B14-A reboot during event, with fail-closed gap accounting.

### Not recoverable on a single VPS

- complete provider outage spanning the critical B14-A window;
- permanent VPS/disk loss;
- filesystem corruption destroying already-written data.

Those require independent off-host redundancy.

## 7. Code-drift protection

Each collector retains Git-blob/freeze handshake.

If a frozen runner or parent is modified by a future repository update, the collector fails closed instead of silently running changed research logic.

Therefore frozen collector files must remain immutable; changes require a new version.

## 8. Operational status helper

Use:

`bash ops/systemd/sc001_collectors_status.sh`

after migration.

The helper reports:

- active/enabled service state;
- B13-C collector state/counters;
- B14-A state/counters;
- recent service logs.

## 9. Migration acceptance

Migration PASS requires:

- B13-C systemd service = active;
- B14-A systemd service = active;
- old tmux sessions gone;
- planned migration gap logged;
- B13-C resumes protected collection;
- B14-A returns to WAITING state;
- no basis/convergence/PnL calculation.

Exact success token:

`SC001_COLLECTOR_SYSTEMD_MIGRATION_PASS`

## 10. After migration

Once migration PASS is observed:

1. do not use old tmux launch commands;
2. use systemctl/status helper for collector operations;
3. leave B13-C and B14-A frozen in background;
4. proceed to B15 independent-base design review.
