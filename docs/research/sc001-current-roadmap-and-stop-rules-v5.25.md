# SC001 Current Roadmap and Stop Rules v5.25

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — COLLECTOR RESILIENCE READY / SYSTEMD MIGRATION NEXT / B15 AFTER**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.24.md`

## 1. Current research clocks

B13-C:

`B13C_COLLECTION_RUNNING`

B14-A P0:

`B14A_P0_COLLECTION_WAITING`

No B13-C alpha inspection.

No B14-A rule changes before Sep25.

## 2. Operational hardening

Binding plan:

`docs/research/sc001-background-collector-operational-resilience-plan-v0.1.md`

Final supervised collectors:

- B13-C v0.3;
- B14-A P0 v0.3.

## 3. systemd properties

Both collectors will be:

- enabled at boot;
- restarted on failure;
- ordered after network/time synchronization;
- supervised independently of SSH/Termux;
- protected by persistent restart-gap accounting.

## 4. Migration boundary

The current tmux collectors remain authoritative until the migration helper succeeds.

Do not manually kill them before running the helper.

Migration helper:

`ops/systemd/migrate_sc001_collectors_to_systemd.sh`

Expected terminal success:

`SC001_COLLECTOR_SYSTEMD_MIGRATION_PASS`

## 5. Post-migration expected state

B13-C:

systemd `active`, continuing prospective liquidation capture.

B14-A:

systemd `active`, state `B14A_P0_COLLECTION_WAITING`.

Old tmux sessions:

absent.

## 6. Residual infrastructure risk

A single VPS cannot protect against a full-host/provider outage or permanent disk loss.

Optional later resilience:

- second independent B14-A P0 collector;
- off-host B13-C backup.

These do not alter research rules.

## 7. B15 gate

Do not begin B15 candidate design until collector systemd migration is verified.

After migration PASS:

perform a fresh, critical B15 independent-base mechanism review before choosing any candidate.

No B15 price/outcome run is authorized yet.
