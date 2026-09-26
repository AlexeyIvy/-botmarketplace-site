# SC001 Current Roadmap and Stop Rules v5.116

Date: 2026-09-26  
Status: **B15-P1 W1 accumulation continues / B14-A P0 readout offline self-test SEALED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.115.md`

B15-P1 remains unchanged in W1 accumulation.

B14-A P0 readout implementation has been frozen and packaged for synthetic offline validation.

Exact sealed bundle:
- ID: `bundle_20260926T200825Z_9958f82d`
- SHA256: `d56c76d45e793dd28b14818241379c3ee6fd86fe79e083d7aca5d39ccfed33a5`
- approval code: `BM-D56C76D45E79`
- runtime: `offline-research-v1`
- inputs: none
- files: 5
- bytes: 21967

Expected PASS:

`B14A_P0_READOUT_V01_SELF_TEST_PASS`

No real B14-A data are opened by this self-test.

After PASS, build a separate immutable read-only real-data bundle using only:
- `SC001_B14A_P0_20260925/collector_state.json`
- `SC001_B14A_P0_20260925/raw_trades.jsonl`
- `SC001_B14A_P0_20260925/connection_events.jsonl`

The real readout must preserve the frozen P0 rule and 50 bps hurdle.

Next state:

`RUN_B14A_P0_READOUT_OFFLINE_SELFTEST_AFTER_EXPLICIT_APPROVAL`
