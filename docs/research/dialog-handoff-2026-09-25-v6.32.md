# SC001 / B15-P1 — dialog handoff v6.32 — 2026-09-25

Current state:

`B15P1_FINAL_LAUNCH_V01_TECHNICAL_FAIL_RECOVERY_PREFLIGHT_SEALED`

## Failure diagnosis

First real final launch reached runtime start successfully.

Observed PASS before failure:
- collector self-test;
- staged launch authorization validator;
- final prerequisites;
- runtime prestart freeze/capability/authorization.

Then post-start verifier failed at embedded Python line 31:

`assert poll_count >= 2`

This was an expected early NOT_READY state. The global Bash ERR trap treated it as a hard error before the retry loop could wait.

Failure class:

`EXPECTED_NOT_READY_STATE_TRIGGERED_GLOBAL_ERR_TRAP`

Do not rerun v0.1.

## Recovery

Prepared wrapper:

`scripts/research/run-b15p1-final-launch-v0.1-failure-recovery-v0.1.sh`

SHA256:

`9ef7d1631d5e1b54d01b33c27b30050837e1914051784d2e114f7ed7efe903bb`

It will:
- stop/disable service;
- archive failed-attempt evidence;
- preserve capability/host evidence;
- remove only exact expected authorization/unit remnants;
- return active collector data root to clean baseline.

## Sealed recovery offline preflight

- bundle ID: `bundle_20260925T163125Z_2331de78`
- bundle SHA256: `a31a6d0a9bb4f2ac62e5c6f9e94b8ca6f320e2575d6f5da5c3a989cf0e8e73aa`
- approval code: `BM-A31A6D0A9BB4`

Not run yet.

Next: run recovery offline-preflight after explicit approval.
