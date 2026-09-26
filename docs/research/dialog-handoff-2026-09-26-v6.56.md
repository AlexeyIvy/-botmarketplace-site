# SC001 / B15-P1 — dialog handoff v6.56 — 2026-09-26

Current state:

`B15P1_STAGE_E_W0_V011_OFFLINE_SELFTEST_SEALED_AWAITING_APPROVAL`

Original v0.1 failed only at Runner launcher/argparse boundary. No collector or data defect was observed.

Corrected analyzer:
`research/sc001/sc001_b15p1_stage_e_pipeline_smoke_v0_1_1.py`

SHA256:
`c077503ec29a691fd808cfbf0f7d93b5a7f39137e21b39892efad12f2a2e9df4`

Exact new sealed bundle:
- ID: `bundle_20260926T170027Z_667fd89e`
- SHA256: `87b96848501d4e362533e5866c8f7f3fa57f03af7844b068a5582c7a37a45679`
- approval code: `BM-87B96848501D`
- inputs: none
- files: 5
- bytes: 24263

Expected PASS:
`B15P1_STAGE_E_PIPELINE_SMOKE_V011_SELF_TEST_PASS`

Next after PASS:
prepare a separate immutable W0 real-data pipeline smoke bundle using read-only `sc001_data` input. That future bundle must not infer opportunity rate from partial-day W0 data.
