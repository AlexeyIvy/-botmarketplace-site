# SC001 / B15-P1 — dialog handoff v6.57 — 2026-09-26

Current state:

`B15P1_STAGE_E_W0_OFFLINE_SELFTEST_PASS_REAL_DATA_SMOKE_PREPARED`

Collector remains operationally frozen and running.

Corrected offline self-test PASS:
- job: `job_20260926T171533Z_f889d71b`
- status: `B15P1_STAGE_E_PIPELINE_SMOKE_V011_SELF_TEST_PASS`
- exit code: 0
- package integrity: PASS
- stderr: empty

Result:
`docs/research/sc001-b15-p1-stage-e-w0-pipeline-smoke-v0.1.1-offline-selftest-result-v0.1.json`

W0 real-data bootstrap:
`research/sc001/sc001_b15p1_stage_e_w0_real_data_smoke_bootstrap_v0_1.py`

SHA256:
`53e80cafad3d3b6fbd4e93befd5cc5c0450eeff5e511ed8582bf7c3d3fd4ce95`

It will use only five read-only files materialized from Runner allowlisted root `sc001_data`: collector state, collector manifest, current 2026-09-26 poll ledger, and Bybit/OKX fee files.

W0 does not perform opportunity-rate inference and does not use price/PnL.

Next: commit this W0 preparation, build/seal exact real-data bundle, then stop at the exact Runner approval boundary.
