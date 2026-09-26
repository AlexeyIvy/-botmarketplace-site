# SC001 Current Roadmap and Stop Rules v5.109

Date: 2026-09-26  
Status: **B15-P1 Stage E W0 offline self-test PASS / W0 real-data read-only smoke prepared for immutable bundling**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.108.md`

## Collector boundary

Collector remains:

`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

No collector code, cadence, service, authorization, storage semantics or firewall is changed.

## Stage E offline self-test PASS

Corrected v0.1.1 Runner job:

`job_20260926T171533Z_f889d71b`

Result:

`B15P1_STAGE_E_PIPELINE_SMOKE_V011_SELF_TEST_PASS`

Evidence:
- exit code = 0;
- package integrity = PASS;
- stderr empty;
- no input dataset;
- no network/exchange call;
- no credentials;
- no collector mutation/restart;
- no price/PnL;
- no opportunity-rate inference.

Result document:

`docs/research/sc001-b15-p1-stage-e-w0-pipeline-smoke-v0.1.1-offline-selftest-result-v0.1.json`

## W0 real-data smoke

A separate immutable read-only W0 smoke is prepared.

Purpose:

verify the actual path

`collector -> sc001_data snapshot -> Runner materialization -> Stage E analyzer`

without drawing any source-opportunity-rate conclusion.

Bootstrap:

`research/sc001/sc001_b15p1_stage_e_w0_real_data_smoke_bootstrap_v0_1.py`

SHA256:

`53e80cafad3d3b6fbd4e93befd5cc5c0450eeff5e511ed8582bf7c3d3fd4ce95`

Analyzer remains:

`research/sc001/sc001_b15p1_stage_e_pipeline_smoke_v0_1_1.py`

SHA256:

`c077503ec29a691fd808cfbf0f7d93b5a7f39137e21b39892efad12f2a2e9df4`

## W0 declared read-only inputs

Runner allowlisted root:

`sc001_data`

Files to be snapshotted at Runner execution time:
- `SC001_B15P1_TRANSFERABILITY/collector_state.json`;
- `SC001_B15P1_TRANSFERABILITY/collector_manifest.json`;
- `SC001_B15P1_TRANSFERABILITY/polls/2026-09-26.jsonl`;
- `SC001_B15P1_TRANSFERABILITY/fees/bybit/2026-09-26.jsonl`;
- `SC001_B15P1_TRANSFERABILITY/fees/okx/2026-09-26.jsonl`.

W0 verifies:
- snapshot materialization;
- collector state/manifest semantics;
- price/PnL firewalls;
- poll JSONL parsing;
- poll-chain hash recomputation and continuity;
- at least two scheduled polls;
- at least one fully valid Bybit+OKX poll;
- at least one successful fee instrument from each venue;
- no price/PnL/opportunity-rate inference.

## Research boundary

W0 is pipeline validation only.

Even if W0 sees route/source events, it must not classify B15 opportunity frequency.

Formal source-only opportunity-rate inference remains frozen to:
- W1 = 7 complete UTC days for operational source checkpoint;
- W2 = 30 complete UTC days for first formal opportunity-rate checkpoint;
- W3 = 90 complete UTC days if W2 has fewer than 10 independent outage clusters.

## Stop rules

- Do not modify a healthy collector to simplify W0.
- Do not infer opportunity rate from the partial first day.
- Do not open price/PnL.
- Do not select assets/networks from W0 event frequency.
- W0 must use Runner read-only materialized inputs only.

## Next state

`BUILD_AND_SEAL_W0_REAL_DATA_READ_ONLY_SMOKE_BUNDLE`
