# SC001 / B15-P1 — dialog handoff v6.45 — 2026-09-26

Current state:

`B15P1_RECOVERY_V012_OFFLINE_PREFLIGHT_SEALED_AWAITING_APPROVAL`

Recovery v0.1.1 host attempt failed before mutation because it searched the probe tee-log for outer-wrapper tokens that are printed only after tee ends.

This is a recovery log-contract bug, not a capability/parser failure.

New recovery v0.1.2:

`scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.2.sh`

SHA256:

`04d6f49a38882e94928ae7fef0b1068670dfb536361cd72c77659aefc17bac20`

It keeps the rolling-snapshot semantic validation and replaces only the log contract with real probe-level tokens.

Sealed offline-preflight bundle:
- ID: `bundle_20260926T115009Z_9a599660`
- SHA256: `6ec32292acaccf905cc25c0dc6f15e126cb1067fc5463e9257ab7f0f82c8c707`
- approval code: `BM-6EC32292ACAC`
- files: 6
- bytes: 40164

Not run yet.

Next: explicit approval -> run v0.1.2 offline preflight. Only PASS permits v0.1.2 recovery on VPS.
