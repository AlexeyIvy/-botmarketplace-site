# SC001 / B15-P1 — dialog handoff v6.53 — 2026-09-26

Current state:

`B15P1_STAGE_E_SOURCE_ONLY_PROTOCOL_AND_W0_SMOKE_PREPARED`

Collector remains frozen and healthy:

`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

No collector changes are authorized or required.

Stage E binding protocol:

`docs/research/sc001-b15-p1-source-only-opportunity-rate-analysis-protocol-v0.1.md`

Key research boundary:
- source-only;
- primary unit = venue-level effective-transferability outage cluster;
- W0 partial-day smoke only;
- W1 = 7 complete UTC days;
- W2 = 30 complete UTC days;
- W3 sparse extension = 90 complete UTC days;
- price/PnL remain closed.

W0 read-only smoke implementation:

`research/sc001/sc001_b15p1_stage_e_pipeline_smoke_v0_1.py`

SHA256:

`9cdbe1e33f6c3d9ad90f11c494690adadd0ec9d0fab05ec32b59c73db7bdb69e`

Local py_compile and synthetic self-test passed with:

`B15P1_STAGE_E_PIPELINE_SMOKE_V01_SELF_TEST_PASS`

Contracts:
- `docs/research/sc001-b15-p1-stage-e-pipeline-smoke-contract-v0.1.json`
- `docs/research/sc001-b15-p1-stage-e-pipeline-smoke-offline-selftest-spec-v0.1.json`

Next exact action:
1. package the exact Stage E W0 smoke implementation into an immutable Runner offline-selftest bundle;
2. seal and verify exact bundle SHA/approval code;
3. run only after the exact Runner approval boundary;
4. after PASS, prepare a separate read-only W0 real-data bundle bound to `sc001_data` inputs;
5. W0 must not report opportunity rate.
