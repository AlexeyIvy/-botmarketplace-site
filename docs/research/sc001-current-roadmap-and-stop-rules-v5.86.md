# SC001 Current Roadmap and Stop Rules v5.86

Date: 2026-09-25  
Status: **B15-P1 RECOVERY PASS / FINAL LAUNCH v0.1.1 OFFLINE PREFLIGHT SEALED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.85.md`

## Recovery result

The failed v0.1 launch attempt was recovered successfully.

Observed host result:

`B15P1_FINAL_LAUNCH_V01_FAILURE_RECOVERY_PASS`

Recovery report SHA256:

`59d77abb773e482c3fc804878ac17214b516bc72807635f52efa881507741a25`

Archived failed-attempt files: 7.

Recovered host baseline:
- service active = inactive;
- service enabled = not-found;
- runtime unit = absent;
- runtime authorization = absent;
- active collector state = absent;
- active collector manifest = absent;
- collector start authorization = false;
- price/PnL authorization = false.

## v0.1 root cause

The first launch did not fail because of collector/API/research logic.

The first post-start verifier observed `poll_count < 2`, which was an expected transient NOT_READY state.

The old v0.1 wrapper used `set +e` under a global ERR trap. Bash still invoked the ERR trap, causing immediate rollback before the retry loop could wait.

## Corrected final launch wrapper v0.1.1

Path:

`scripts/research/run-b15p1-final-collector-deployment-launch-v0.1.1.sh`

SHA256:

`fe7c93187f0e8a84f550fd37240c3a80e7aa6a21c4d296a5042677b15ae0b6b0`

Research contract is unchanged:
- collector v0.1.3 unchanged;
- service v0.1.3 unchanged;
- live capability snapshot unchanged;
- runtime launch authorization payload unchanged;
- 15-second cadence unchanged;
- price/PnL remain closed.

Operational hardening in v0.1.1:
- tri-state verifier: PASS=0 / NOT_READY=10 / HARD_FAIL=20;
- expected nonzero rc captured only inside Bash `if` conditions;
- `set +e` exists only inside rollback;
- single-instance `flock`;
- HUP/INT/TERM/EXIT rollback traps;
- exact recovery-report SHA gate;
- recursive re-hash of all 7 archived failure-evidence files;
- runtime parent-symlink guard;
- storage-pressure gate before mutation;
- transactional runtime-file rollback ledger;
- atomic temp + SHA + rename for runtime files;
- atomic service-unit install;
- atomic launch-authorization install;
- poll JSONL/state reconciliation;
- poll-chain reconciliation;
- raw-object SHA revalidation;
- process_epoch must equal 1;
- process_restart_count must equal 0;
- systemd NRestarts must equal 0;
- MainPID must be positive;
- SubState must be running.

## Structural audit before seal

Exact counts:
- source files = 24;
- source SHA pins = 24;
- runtime deploy files = 19;
- runtime deploy SHA pins = 19;
- embedded Python blocks = 6;
- staged self-test invocations = 1;
- direct collector `--mode run` invocations = 0;
- systemctl enable = 1;
- systemctl start = 1;
- `set +e` count = 1, rollback only;
- legacy 90-second verifier = absent;
- old v0.1 PASS token = absent;
- v0.1.1 PASS token = exactly one.

## New offline-preflight

The preflight executes real synthetic control-flow fixtures:
- Bash ERR-trap + rc=10 conditional capture must PASS;
- poll_count=0 -> NOT_READY rc=10;
- 2 polls but no valid poll -> NOT_READY rc=10;
- valid 2-poll fixture + raw-object integrity -> PASS rc=0;
- price firewall violation -> HARD_FAIL rc=20;
- process restart -> HARD_FAIL rc=20;
- raw-object corruption -> HARD_FAIL rc=20.

## Sealed bundle

- bundle ID: `bundle_20260925T172458Z_c1e406a4`
- SHA256: `46eb3ed89605eb40b526f0ff03b2a3ffd7f6869958b082509ee0bd2196697f65`
- approval code: `BM-46EB3ED89605`
- files: 29
- bytes: 370061
- runtime: `offline-research-v1`
- inputs: none

The bundle has NOT been run.

## Stop rule

Do not execute real final launch v0.1.1 until this offline preflight returns full PASS and the user separately approves the host retry.

Do not use final launch v0.1 again.

## Next state

`RUN_B15P1_FINAL_LAUNCH_V011_WRAPPER_OFFLINE_PREFLIGHT_AFTER_USER_APPROVAL`
