# SC001 — Collector systemd Migration PASS v0.1

Date: 2026-09-19
Status: **SC001_COLLECTOR_SYSTEMD_MIGRATION_PASS**
Scope: `SCALPING RESEARCH / SC001`

## 1. Migration result

Observed exact terminal token:

`SC001_COLLECTOR_SYSTEMD_MIGRATION_PASS`

Both protected collectors were migrated from tmux supervision to systemd supervision.

## 2. Protected services

B13-C:

`sc001-b13c-liquidation.service`

Runner:

`research/sc001/sc001_b13c_bybit_prospective_liquidation_collector_v0_3.py`

B14-A P0:

`sc001-b14a-p0.service`

Runner:

`research/sc001/sc001_b14a_p0_prospective_trade_collector_v0_3.py`

## 3. Operational guarantees now active

Both services are:

- enabled for boot;
- ordered after network-online and time-sync targets;
- restarted on process failure;
- terminated gracefully with SIGTERM;
- protected by persistent heartbeat / restart-gap accounting.

## 4. Research integrity

B13-C remains protected prospective liquidation collection.

B14-A remains frozen prospective P0 for the 2026-09-25 expiry event.

The migration did not alter:

- frozen instruments;
- B14-A T0;
- B14-A capture window;
- B14-A 50 bps hurdle;
- B13-C protected evidence role.

## 5. Remaining infrastructure risk

A single VPS still cannot guarantee survival of:

- complete provider outage spanning the B14-A critical window;
- permanent host/disk loss.

Those require independent off-host redundancy and are not solved by systemd.

## 6. Next research action

Operational hardening is complete.

SC001 may now proceed to a fresh B15 independent-base mechanism review while B13-C and B14-A continue in background.
