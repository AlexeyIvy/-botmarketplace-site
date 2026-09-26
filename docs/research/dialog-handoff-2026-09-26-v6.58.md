# SC001 / B15-P1 — dialog handoff v6.58 — 2026-09-26

Current state:

`B15P1_STAGE_E_W0_REAL_DATA_SMOKE_SEALED_AWAITING_APPROVAL`

Stage E v0.1.1 offline synthetic self-test is PASS:
- job: `job_20260926T171533Z_f889d71b`
- stdout: `B15P1_STAGE_E_PIPELINE_SMOKE_V011_SELF_TEST_PASS`
- stderr: empty
- exit: 0
- package integrity: PASS

Exact next bundle:
- ID: `bundle_20260926T171912Z_bea3fa42`
- SHA256: `2fbdec62031aa51c3ed64b769dbf26548fc8adfc03802183ee26adf26659fc64`
- approval code: `BM-2FBDEC62031A`
- files: 6
- bytes: 31239
- runtime: `offline-research-v1`

It has five read-only runtime inputs from allowlisted root `sc001_data`: state, manifest, current-day poll ledger, and current-day Bybit/OKX fee files.

W0 objective: validate real data plumbing only. No opportunity-rate conclusion from partial-day data.

Expected PASS tokens:
- `B15P1_STAGE_E_REAL_DATA_PIPELINE_SMOKE_PASS`
- `B15P1_STAGE_E_W0_REAL_DATA_SMOKE_BOOTSTRAP_PASS`

After PASS: preserve collector freeze, record W0 input hashes, continue accumulation toward W1 = 7 complete UTC days, and prepare the W1 source-only checkpoint analyzer independently.
