# SC001 Current Roadmap and Stop Rules v5.112

Date: 2026-09-26  
Status: **B15-P1 Stage E W1 seven-day source-only offline self-test SEALED / awaiting exact Runner approval**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.111.md`

## Current collector state

Collector remains frozen and running:

`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

The W1 preparation does not modify or restart the collector.

## W0 real-data state

W0 pipeline has already passed on real read-only collector data:

`B15P1_STAGE_E_W0_REAL_DATA_SMOKE_PASS`

This established the real path:

`collector -> sc001_data -> Runner snapshot -> Stage E analyzer`

without price/PnL or opportunity-rate inference.

## W1 implementation freeze candidate

Frozen W1 window:

`2026-09-27 .. 2026-10-03`

inclusive, seven complete UTC days.

Earliest real W1 census:

`after 2026-10-04T00:00:00Z`

once the Oct 3 daily manifest exists.

Components:
- input census SHA256: `5386182a73eb6e0561eb3670223168d3e1ebe7d11640ee9d67ce753569de4aaf`;
- source-only analyzer SHA256: `da4a218e7b624775e44e8403a1acf6ee1bff581ec1a7ddaa59eb42fd0f2330ce`;
- offline harness SHA256: `061ebfa96db2728e44c71473cc70ede06c0c764c59533fadba0fce8ac59358bc`.

## Exact sealed offline self-test bundle

- ID: `bundle_20260926T174651Z_681d463a`
- SHA256: `9a06452b4ef5b924cdb21fa48a66a0602632167ce4bbae97f51342d4e690d6eb`
- approval code: `BM-9A06452B4EF5`
- runtime: `offline-research-v1`
- inputs: none
- files: 7
- bytes: 77216

The bundle is SEALED and has not been run.

Expected PASS tokens:
- `B15P1_STAGE_E_W1_INPUT_CENSUS_V01_SELF_TEST_PASS`;
- `B15P1_STAGE_E_W1_SOURCE_ONLY_ANALYZER_V01_SELF_TEST_PASS`;
- `B15P1_STAGE_E_W1_OFFLINE_SELFTEST_PASS`.

## What this self-test validates

Synthetic fixtures validate:
- exact W1 window/pre-window design;
- Runner launcher contract;
- daily-manifest hash/row binding;
- poll hash recomputation;
- within-day and cross-day poll-chain continuity;
- 99% quality-gate mechanics;
- effective multi-route ACTIVE/BLOCKED/UNKNOWN semantics;
- clean ACTIVE -> BLOCKED episode starts only when all frozen common routes are blocked;
- clean BLOCKED -> ACTIVE completion;
- censoring rules;
- conservative shared-blocker outage clustering;
- opposite-direction USDT source state;
- causal account/pair fee freshness;
- price/PnL firewall.

## Boundaries

This offline self-test uses **no real SC001 data**.

It performs:
- no exchange/network calls;
- no credentials use;
- no collector mutation/restart;
- no price/PnL;
- no formal W2 opportunity-rate inference.

W1 itself remains an operational/source checkpoint. The first formal source-only opportunity-rate classification remains W2 after 30 complete UTC days.

## Next state

`RUN_STAGE_E_W1_OFFLINE_SELFTEST_AFTER_EXPLICIT_APPROVAL`
