# SC001 Current Roadmap and Stop Rules v5.26

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — COLLECTOR SYSTEMD MIGRATION PASS / B15 DESIGN REVIEW NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.25.md`

## 1. Operational state

Collector migration:

`SC001_COLLECTOR_SYSTEMD_MIGRATION_PASS`

B13-C and B14-A P0 are now supervised by systemd.

Old tmux launch mode is retired for these two collectors.

## 2. B13-C

State:

protected prospective liquidation collection continues.

Do not inspect alpha outcomes.

## 3. B14-A

State:

prospective P0 remains armed for 2026-09-25.

Frozen:

- connect = 07:28:30Z;
- T0 = 07:30:00Z;
- capture = 07:29:00Z .. 08:02:00Z;
- expiry = 08:00:00Z;
- structural burden = 37 bps;
- headroom hurdle = 50 bps.

Do not alter before event.

## 4. Infrastructure protection

systemd now covers:

- VPS reboot;
- process crash;
- temporary network loss;
- SSH/Termux disconnect;
- process restart auditing.

Persistent gap ledgers remain mandatory for later data-validity checks.

## 5. B15 authorization

B15 may now enter:

`INDEPENDENT_BASE_MECHANISM_REVIEW`

No candidate ID yet.

No B15 price/outcome run yet.

The next task is conceptual/mechanism selection only.

## 6. B15 review requirements

Before choosing a mechanism:

- review prior terminal/rejected mechanism classes;
- avoid disguised rescue of C1-C12/B13-A;
- prefer a different economic payer/source;
- estimate structural fills and cost burden first;
- require free-source feasibility;
- require clean future evidence path;
- shortlist at most three mechanisms;
- select one only after critical multi-role review.

## 7. Immediate next action

Perform a fresh, critical B15 independent-base mechanism review before any implementation.
