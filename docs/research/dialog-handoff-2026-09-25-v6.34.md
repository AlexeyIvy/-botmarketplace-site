# SC001 / B15-P1 — dialog handoff v6.34 — 2026-09-25

Current state:

`B15P1_RECOVERY_PASS_FINAL_LAUNCH_V011_OFFLINE_PREFLIGHT_SEALED`

## Recovery PASS

Recovery report SHA256:

`59d77abb773e482c3fc804878ac17214b516bc72807635f52efa881507741a25`

Seven failed-attempt evidence files were archived.

Active baseline is clean:
- service inactive;
- enabled not-found;
- runtime unit absent;
- runtime authorization absent;
- state absent;
- manifest absent.

## v0.1.1 correction

Corrected wrapper:

`scripts/research/run-b15p1-final-collector-deployment-launch-v0.1.1.sh`

SHA256:

`fe7c93187f0e8a84f550fd37240c3a80e7aa6a21c4d296a5042677b15ae0b6b0`

Key correction:
- transient startup state is explicit NOT_READY rc=10;
- HARD_FAIL is rc=20;
- expected nonzero verifier rc is captured inside Bash if/else so global ERR trap cannot prematurely rollback.

Additional hardening:
- flock;
- signal/EXIT rollback;
- transactional runtime rollback ledger;
- atomic deployment;
- recovery archive rehash;
- poll/raw persistence checks;
- zero-restart first-start contract.

## Sealed v0.1.1 offline preflight

- bundle ID: `bundle_20260925T172458Z_c1e406a4`
- bundle SHA256: `46eb3ed89605eb40b526f0ff03b2a3ffd7f6869958b082509ee0bd2196697f65`
- approval code: `BM-46EB3ED89605`
- files: 29
- bytes: 370061
- runtime: offline-research-v1
- inputs: none

The bundle is sealed and has NOT been run.

Next: after explicit approval run this offline preflight. Only a full PASS permits a real v0.1.1 host retry.
