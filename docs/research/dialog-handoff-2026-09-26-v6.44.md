# SC001 / B15-P1 — dialog handoff v6.44 — 2026-09-26

Current state:

`B15P1_ROLLING_SNAPSHOT_SAFE_RECOVERY_V011_OFFLINE_PASS_VPS_RECOVERY_NEXT`

Offline preflight:
- bundle: `bundle_20260926T101521Z_09b874f8`
- job: `job_20260926T113445Z_a1d1038b`
- main PASS: `B15P1_V011_SOURCE_INVALID_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_V011_PASS`
- bootstrap PASS: `B15P1_V011_SOURCE_INVALID_RECOVERY_BOOTSTRAP_V011_PASS`

Recovery wrapper:

`scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.1.sh`

SHA256:

`2a14da8e599feb0f2e075144bd64b269de44c916715790152e71ae5cc67eb2a7`

This version validates any current valid capability snapshot v0.2.2 semantically, then preserves its exact SHA through recovery.

Next user-visible action is one VPS command using this v0.1.1 wrapper.
