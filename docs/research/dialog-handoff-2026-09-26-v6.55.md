# SC001 / B15-P1 — dialog handoff v6.55 — 2026-09-26

Current state:

`B15P1_STAGE_E_W0_V01_RUNNER_LAUNCHER_FAILURE_V011_CORRECTION_PREPARED`

Collector remains operationally frozen and unaffected.

Failed Runner job:
- job: `job_20260926T165638Z_8bd1dc56`
- bundle: `bundle_20260926T134907Z_ab6df192`
- package integrity: PASS
- exit code: 2
- artifacts: none

Root cause:
Runner v1.0.5 passes package-root and entrypoint as positional args. v0.1 strict argparse did not declare them.

Correction:
`research/sc001/sc001_b15p1_stage_e_pipeline_smoke_v0_1_1.py`

SHA256:
`c077503ec29a691fd808cfbf0f7d93b5a7f39137e21b39892efad12f2a2e9df4`

v0.1.1 explicitly accepts exactly the Runner launcher positional contract and validates it fail-closed. Stage E research logic is unchanged.

Expected PASS token:
`B15P1_STAGE_E_PIPELINE_SMOKE_V011_SELF_TEST_PASS`

Next:
commit the v0.1.1 correction, create/seal a new immutable offline self-test bundle, then stop at the new exact Runner approval boundary.
