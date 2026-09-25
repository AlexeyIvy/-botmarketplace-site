# SC001 Current Roadmap and Stop Rules v5.84

Date: 2026-09-25
Status: **B15-P1 FIRST FINAL-LAUNCH ATTEMPT TECHNICAL WRAPPER FAIL / RECOVERY PREFLIGHT SEALED**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.83.md`

## First real launch attempt

The collector passed:
- staged collector self-test;
- staged launch authorization validator;
- final launch prerequisites;
- runtime freeze/capability/authorization prestart validator.

The systemd unit was enabled and the collector was started.

The first post-start verification then raised:

`AssertionError`

Exact failing assertion:

`poll_count >= 2`

This occurred on the first verification attempt, before two 15-second polls had time to complete.

## Root cause

Failure class:

`EXPECTED_NOT_READY_STATE_TRIGGERED_GLOBAL_ERR_TRAP`

The Bash wrapper used a global ERR trap. The Python verifier's temporary rc=1 for `poll_count < 2` triggered the trap immediately, so the intended retry loop never got to wait and re-check.

This is a launch-wrapper control-flow defect, not evidence of:
- collector parser failure;
- Bybit/OKX API failure;
- credential failure;
- launch-authorization failure;
- runtime freeze mismatch;
- price/PnL firewall failure.

## Recovery plan

Before technical retry:
1. verify/force service stopped and disabled;
2. archive any failed-attempt state/manifest/systemd log/polls/raw/events/fees;
3. preserve live snapshot and host-readiness evidence;
4. remove only exact expected runtime authorization/unit if still present;
5. return active data root to a clean baseline;
6. then prepare corrected launch wrapper v0.1.1.

Recovery wrapper:

`scripts/research/run-b15p1-final-launch-v0.1-failure-recovery-v0.1.sh`

SHA256:

`9ef7d1631d5e1b54d01b33c27b30050837e1914051784d2e114f7ed7efe903bb`

## Recovery offline-preflight bundle

- bundle ID: `bundle_20260925T163125Z_2331de78`
- SHA256: `a31a6d0a9bb4f2ac62e5c6f9e94b8ca6f320e2575d6f5da5c3a989cf0e8e73aa`
- approval code: `BM-A31A6D0A9BB4`
- files: 5
- bytes: 22204
- runtime: offline-research-v1
- inputs: none

The bundle is sealed and has NOT been run.

## Stop rule

Do not rerun the failed final launch wrapper v0.1.

Do not start/enable collector manually.

Run the sealed recovery offline-preflight first.

## Next state

`RUN_B15P1_FINAL_LAUNCH_V01_FAILURE_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_AFTER_USER_APPROVAL`
