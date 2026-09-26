# SC001 Current Roadmap and Stop Rules v5.111

Date: 2026-09-26  
Status: **B15-P1 Stage E W0 real-data PASS / W1 7-day source-only checkpoint implementation prepared / offline self-test next**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.110.md`

## W0 real-data milestone

Exact W0 Runner job:

`job_20260926T172841Z_50087abd`

Result:

`B15P1_STAGE_E_W0_REAL_DATA_SMOKE_PASS`

Both required tokens were observed:
- `B15P1_STAGE_E_REAL_DATA_PIPELINE_SMOKE_PASS`;
- `B15P1_STAGE_E_W0_REAL_DATA_SMOKE_BOOTSTRAP_PASS`.

W0 snapshot:
- scheduled poll rows = 1045;
- both-venue-valid rows = 1045;
- invalid polls = 0;
- missed slots = 0;
- source gaps = 0;
- process restarts = 0;
- fee rows = 384 / all successful;
- Bybit fee instruments = 192;
- OKX fee instruments = 192;
- route/source event rows in this partial-day snapshot = 0.

The zero-event W0 observation is **not** an opportunity-rate conclusion.

Result document:

`docs/research/sc001-b15-p1-stage-e-w0-real-data-smoke-result-v0.1.json`

## Collector boundary

Collector remains:

`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

Do not modify or restart the healthy collector for W1.

## W1 frozen window

First seven complete UTC days after launch:

- 2026-09-27
- 2026-09-28
- 2026-09-29
- 2026-09-30
- 2026-10-01
- 2026-10-02
- 2026-10-03

Earliest real W1 census:

`after 2026-10-04T00:00:00Z`

and only once the 2026-10-03 daily manifest has been finalized.

Pre-window day `2026-09-26` is used only for:
- the last frozen route-state baseline before W1;
- fee snapshots that can still be causally fresh under the frozen 8-hour rule.

## W1 implementation

Input census:
`research/sc001/sc001_b15p1_stage_e_w1_input_census_v0_1.py`

SHA256:
`5386182a73eb6e0561eb3670223168d3e1ebe7d11640ee9d67ce753569de4aaf`

Source-only analyzer:
`research/sc001/sc001_b15p1_stage_e_w1_source_only_analyzer_v0_1.py`

SHA256:
`da4a218e7b624775e44e8403a1acf6ee1bff581ec1a7ddaa59eb42fd0f2330ce`

Offline self-test harness:
`research/sc001/sc001_b15p1_stage_e_w1_offline_selftest_harness_v0_1.py`

SHA256:
`061ebfa96db2728e44c71473cc70ede06c0c764c59533fadba0fce8ac59358bc`

Binding contract:
`docs/research/sc001-b15-p1-stage-e-w1-source-only-checkpoint-contract-v0.1.json`

## W1 semantics

W1 remains source-only and is an **operational/source checkpoint**, not the formal W2 opportunity-rate decision.

It reconstructs effective asset-direction transferability from:
1. the final pre-W1 route snapshot;
2. chronological route-transition events.

Clean episode:
- start only on effective ACTIVE -> BLOCKED;
- complete only on BLOCKED -> ACTIVE;
- BLOCKED -> UNKNOWN is censored;
- UNKNOWN -> BLOCKED is not a clean new incident;
- already-blocked at W1 start is left-censored.

Independent outage clusters conservatively merge episodes with a shared blocker component when their starts are within 600 seconds or their intervals overlap; clustering is transitive.

Cause remains `CAUSE_UNCLASSIFIED` unless a separate official-source annotation stage is frozen.

## W1 data-quality gate

Required:
- poll coverage >= 99%;
- both-venue-valid fraction >= 99%;
- daily manifest file hashes/row counts agree;
- poll hashes recompute;
- poll chain is continuous within and across selected days;
- price/PnL firewalls remain closed.

If data quality fails, stop and review. Do not rescue-tune.

## W1 allowed outputs

W1 may report:
- source integrity and gaps;
- clean episode counts;
- completed/censored episode counts;
- duration diagnostics;
- cluster count and breadth;
- blocker concentration;
- opposite-direction USDT state at episode start;
- fee-snapshot freshness at episode start.

W1 must not:
- calculate formal 30-day opportunity rate;
- open price/PnL;
- promote assets/networks from event frequency;
- automatically authorize Stage F.

## Next state

`BUILD_AND_SEAL_STAGE_E_W1_OFFLINE_SELFTEST_BUNDLE`
