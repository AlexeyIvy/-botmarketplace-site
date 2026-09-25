# SC001 Current Roadmap and Stop Rules v5.87

Date: 2026-09-25  
Status: **B15-P1 FINAL LAUNCH v0.1.1 CORRECTED PREFLIGHT SEALED / AWAITING APPROVAL**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.86.md`

## Previous offline-preflight attempt

Bundle:

`bundle_20260925T172458Z_c1e406a4`

Job:

`job_20260925T173412Z_3406a130`

Result:

technical preflight harness failure before harness execution.

Observed:
- package integrity = true;
- exit code = 1;
- artifacts = none;
- Python SyntaxError at harness line 543.

Failure class:

`PYTHON_STRING_QUOTING_COLLISION_IN_PREFLIGHT_HARNESS`

Root cause:

The preflight harness used a Python single-quoted marker string containing the Bash ANSI-C quoted token `$'\t'`. The nested single quote terminated the Python string.

This did NOT execute or affect:
- final launch wrapper;
- VPS;
- systemd;
- runtime authorization;
- collector;
- exchanges;
- price/PnL.

Diagnostic SHA256:

`ed52f7980e250a3aa3dfb03191f5302be5fefe21d4268add0a1ff364ba124bcd`

## Corrected preflight harness

New versioned harness:

`research/sc001/sc001_b15p1_final_launch_v011_wrapper_offline_preflight_v0_1_1.py`

SHA256:

`133f8ccc8e515727feee11fddf8718964a18bda754fe22a74aaceb6509869108`

Correction:
- Bash marker containing `$'\t'` is represented with a double-quoted Python string;
- both PASS and REVIEW manifests use schema v0.1.1.

The real final launch wrapper is unchanged:

`scripts/research/run-b15p1-final-collector-deployment-launch-v0.1.1.sh`

SHA256 remains:

`fe7c93187f0e8a84f550fd37240c3a80e7aa6a21c4d296a5042677b15ae0b6b0`

## New bootstrap compile gate

Bootstrap:

`research/sc001/sc001_b15p1_final_launch_v011_wrapper_offline_preflight_bootstrap_v0_1.py`

SHA256:

`832636ad7555e5a61da47f61a01a720f09f0ec531d621b963b5f2104f124c4d4`

Before the harness may execute, bootstrap:
1. checks exact corrected-harness SHA;
2. reads the full harness source;
3. calls Python `compile(..., "exec")`;
4. only after compile PASS runs the harness in a child Python process;
5. captures return code/stdout/stderr;
6. requires the harness manifest and PASS token;
7. writes its own bootstrap manifest even when the harness fails at runtime.

Thus a future harness syntax/runtime failure becomes a controlled REVIEW artifact instead of an unclassified job exit.

## Corrected preflight spec/freeze

Spec v0.1.1 SHA256:

`825ad90f5108ea1951cda37999864a775e228637531f3e463ba3e1b80a859e97`

Freeze v0.1.1 SHA256:

`3fbda84fe40ca20912d285a89ad00f65a88eee8cf9623d995049b86beca939fe`

The substantive v0.1.1 dynamic fixtures remain unchanged:
- Bash ERR-trap conditional fixture;
- poll_count=0 -> NOT_READY rc=10;
- no valid poll -> NOT_READY rc=10;
- valid 2-poll/raw-object fixture -> PASS rc=0;
- price firewall violation -> HARD_FAIL rc=20;
- process restart -> HARD_FAIL rc=20;
- raw-object corruption -> HARD_FAIL rc=20.

## New sealed bundle

- bundle ID: `bundle_20260925T174309Z_c07a9fa9`
- SHA256: `29415541c9f162d9bcfba8515c94f34f6693f0c5b970dc8138fc81c751fbe30f`
- approval code: `BM-29415541C9F1`
- files: 31
- bytes: 378239
- runtime: `offline-research-v1`
- inputs: none
- entrypoint: bootstrap compile gate

The bundle has NOT been run.

## Stop rule

Do not execute real final launch v0.1.1 until this corrected offline preflight returns full PASS.

Do not use old preflight bundle `bundle_20260925T172458Z_c1e406a4` again.

## Next state

`RUN_CORRECTED_V011_WRAPPER_OFFLINE_PREFLIGHT_AFTER_USER_APPROVAL`
