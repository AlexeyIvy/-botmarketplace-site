# SC001 Current Roadmap and Stop Rules v5.107

Date: 2026-09-26  
Status: **B15-P1 Stage E W0 offline self-test v0.1 failed on Runner launcher argument contract / v0.1.1 correction prepared**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.106.md`

## Collector boundary

Collector remains:

`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

No collector mutation, restart, exchange call, credentials use, price data or PnL occurred during the failed Stage E self-test.

## Failed Stage E v0.1 Runner job

Exact job:

`job_20260926T165638Z_8bd1dc56`

Exact bundle:

`bundle_20260926T134907Z_ab6df192`

Bundle SHA256:

`3ada7e59d80e54931e0f21366805c7f796d6a5becd3f5713b02877af165b2a80`

Observed:
- package integrity = PASS;
- process exit code = 2;
- no artifacts created;
- failure occurred before analyzer self-test logic ran.

Root cause:

Runner v1.0.5 supplies two positional Python entrypoint arguments:
1. package root;
2. exact entrypoint path.

The v0.1 analyzer used strict argparse without declaring those Runner launcher arguments, so argparse rejected them as unknown.

This is a launcher-interface defect, not a Stage E research-logic or data defect.

Failure diagnostic:

`docs/research/sc001-b15-p1-stage-e-w0-pipeline-smoke-v0.1-runner-failure-diagnostic-v0.1.json`

## v0.1.1 technical correction

New analyzer:

`research/sc001/sc001_b15p1_stage_e_pipeline_smoke_v0_1_1.py`

SHA256:

`c077503ec29a691fd808cfbf0f7d93b5a7f39137e21b39892efad12f2a2e9df4`

Correction:
- explicitly declares exactly two optional Runner launcher positional arguments;
- when present, exact entrypoint must equal the current script;
- package root must be an ancestor of the current script;
- malformed partial launcher binding fails closed;
- `parse_known_args` is not used;
- standalone local execution with no launcher args remains valid.

Stage E research semantics are unchanged.

Updated contract:
`docs/research/sc001-b15-p1-stage-e-pipeline-smoke-contract-v0.1.1.json`

Updated offline self-test spec:
`docs/research/sc001-b15-p1-stage-e-pipeline-smoke-offline-selftest-spec-v0.1.1.json`

Expected self-test PASS token:

`B15P1_STAGE_E_PIPELINE_SMOKE_V011_SELF_TEST_PASS`

## Stop rules

- Do not reuse the failed v0.1 bundle as evidence of analyzer correctness.
- Do not weaken argparse with generic unknown-argument acceptance.
- Do not alter Stage E source-only statistical semantics to solve a launcher problem.
- Keep collector frozen and running.
- Price/PnL remain closed.
- Only a new immutable v0.1.1 bundle may establish the corrected offline self-test PASS.

## Next state

`SEAL_STAGE_E_W0_PIPELINE_SMOKE_V011_OFFLINE_SELFTEST_BUNDLE`
