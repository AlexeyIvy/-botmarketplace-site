# SC001 / B15-P1 — dialog handoff v6.36 — 2026-09-25

Current state:

`B15P1_FINAL_LAUNCH_V011_OFFLINE_PREFLIGHT_PASS_AWAITING_REAL_HOST_RETRY_APPROVAL`

## Corrected preflight PASS

Bundle:
`bundle_20260925T174309Z_c07a9fa9`

Job:
`job_20260925T175052Z_259ef10b`

Bootstrap:
`B15P1_FINAL_LAUNCH_V011_PREFLIGHT_BOOTSTRAP_PASS`

Harness:
`B15P1_FINAL_LAUNCH_V011_WRAPPER_OFFLINE_PREFLIGHT_PASS`

Dynamic fixtures:
- poll_count=0 -> rc 10 NOT_READY;
- no valid poll -> rc 10 NOT_READY;
- valid fixture -> rc 0 PASS;
- price firewall violation -> rc 20 HARD_FAIL;
- process restart -> rc 20 HARD_FAIL;
- raw corruption -> rc 20 HARD_FAIL.

## Real retry wrapper

`scripts/research/run-b15p1-final-collector-deployment-launch-v0.1.1.sh`

SHA256:

`fe7c93187f0e8a84f550fd37240c3a80e7aa6a21c4d296a5042677b15ae0b6b0`

The failed v0.1 attempt has already been recovered and archived.

## Next

Only after separate explicit user approval, execute the v0.1.1 final launch wrapper on the VPS.

Do not use v0.1 again.
