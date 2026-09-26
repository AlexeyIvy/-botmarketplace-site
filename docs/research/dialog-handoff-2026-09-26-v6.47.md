# SC001 / B15-P1 — dialog handoff v6.47 — 2026-09-26

Current state:

`B15P1_V011_SOURCE_INVALID_RECOVERY_V012_PASS_PREPARE_V014_LAUNCH`

Recovery v0.1.2 PASS:
- archived files: 134;
- recovery report SHA: `553a89d82dba67ee80166ccff32841b51ecbc25a9d8b47f5d84f6f6dd769e89b`;
- archive: `/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/launch_attempts/20260926T120327Z_final_launch_v0.1.1_source_invalid_failed`.

Current capability snapshot v0.2.2 remained unchanged through recovery:
`01cfa63b6001ec972c4ed87daba5bbd9fba932233b9e8323a49a6a5355e89647`.

Host baseline is clean:
- service inactive;
- enabled not-found;
- runtime unit absent;
- runtime authorization absent;
- active state/manifest absent.

Next: build and offline-validate a new controlled launch gate bound to collector v0.1.4. Do not reuse v0.1.3 launch authorization or old launch wrapper unchanged.
