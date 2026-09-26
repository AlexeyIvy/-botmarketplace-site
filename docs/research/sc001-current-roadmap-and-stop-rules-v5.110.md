# SC001 Current Roadmap and Stop Rules v5.110

Date: 2026-09-26  
Status: **B15-P1 Stage E W0 real-data read-only smoke SEALED / awaiting exact Runner approval**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.109.md`

## Collector boundary

Collector remains healthy and frozen:

`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

W0 is an offline read-only consumer of Runner-materialized snapshots and cannot modify or restart the collector.

## Offline analyzer gate

Corrected Stage E analyzer v0.1.1 has passed official Runner synthetic self-test:

`B15P1_STAGE_E_PIPELINE_SMOKE_V011_SELF_TEST_PASS`

Runner job:

`job_20260926T171533Z_f889d71b`

## Exact W0 real-data bundle

Bundle ID:

`bundle_20260926T171912Z_bea3fa42`

Bundle SHA256:

`2fbdec62031aa51c3ed64b769dbf26548fc8adfc03802183ee26adf26659fc64`

Approval code:

`BM-2FBDEC62031A`

Runtime:
`offline-research-v1`

Bundle files:
6

Bundle bytes:
31239

Entrypoint:

`research/sc001/sc001_b15p1_stage_e_w0_real_data_smoke_bootstrap_v0_1.py`

Entrypoint SHA256:

`53e80cafad3d3b6fbd4e93befd5cc5c0450eeff5e511ed8582bf7c3d3fd4ce95`

The bundle is SEALED and has not been run.

## Declared runtime read-only inputs

All inputs are from allowlisted Runner root `sc001_data` and are materialized only at execution time:

1. `SC001_B15P1_TRANSFERABILITY/collector_state.json`
2. `SC001_B15P1_TRANSFERABILITY/collector_manifest.json`
3. `SC001_B15P1_TRANSFERABILITY/polls/2026-09-26.jsonl`
4. `SC001_B15P1_TRANSFERABILITY/fees/bybit/2026-09-26.jsonl`
5. `SC001_B15P1_TRANSFERABILITY/fees/okx/2026-09-26.jsonl`

## W0 purpose

W0 validates the real pipeline:

`collector -> sc001_data -> Runner read-only materialization -> Stage E analyzer`

It checks parsing, state/manifest firewalls, poll-chain recomputation/continuity, and fee-file readability.

It does **not** estimate opportunity frequency from the partial first day.

## Expected PASS

Analyzer:

`B15P1_STAGE_E_REAL_DATA_PIPELINE_SMOKE_PASS`

Bootstrap:

`B15P1_STAGE_E_W0_REAL_DATA_SMOKE_BOOTSTRAP_PASS`

## Hard boundaries

W0 must perform:
- no exchange/network calls;
- no credentials use;
- no collector mutation;
- no collector restart;
- no price/PnL access;
- no asset/network selection;
- no opportunity-rate inference.

## After W0 PASS

If W0 passes:
- record the exact input snapshot hashes;
- keep collector running unchanged;
- do not repeatedly rerun W0 for tuning;
- accumulate toward W1 = 7 complete UTC days;
- prepare the W1 source-only checkpoint analyzer offline while data accumulate.

## Next state

`RUN_W0_REAL_DATA_READ_ONLY_SMOKE_AFTER_EXPLICIT_APPROVAL`
