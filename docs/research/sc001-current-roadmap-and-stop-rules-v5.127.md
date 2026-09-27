# SC001 Current Roadmap and Stop Rules v5.127

Date: 2026-09-27  
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 cluster-census self-test PASS / real event-only census ready**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.126.md`

## B15-P1

Unchanged:
`W1_7_COMPLETE_UTC_DAY_OBSERVATION_ACCUMULATING`

## B14-A

Unchanged:
`B14A_P0_DEFER_DATA`

Transport root cause is already identified. No retrospective price reconstruction.

## B13-C S0 synthetic validation

Runner job:

`job_20260927T064523Z_8278bc96`

Result:

`B13C_S0_SOURCE_ONLY_CLUSTER_CENSUS_V01_SELF_TEST_PASS`

Observed:
- exit code = 0;
- package integrity = PASS;
- stderr empty.

## Real event-only cluster census

Prepared bootstrap:

`research/sc001/sc001_b13c_s0_real_event_only_cluster_census_bootstrap_v0_1.py`

SHA256:

`2e574e273c236d0760e5f2077102d4d412fd108023c0102a08b4521d58793542`

Inputs:
- collector_state.json;
- connection/connection_events.jsonl;
- events/2026-09-19.jsonl through events/2026-09-26.jsonl.

Frozen event interval:

`2026-09-19T06:47:38.969Z .. 2026-09-26T21:05:32.973Z`

The census may report:
- unique event count after exact-fingerprint collapse;
- aggregate raw cluster count;
- under-minimum / mixed-side / gap-censored aggregate counts;
- eligible cluster count;
- whether >=100 cluster sample gate is ready;
- exact symbol-date Bybit archive identities required by frozen entry/exit buckets.

## Firewalls

The real cluster census must not:
- read price bodies;
- calculate returns;
- rank symbols by performance;
- inspect liquidation-size distributions for selection;
- tune thresholds;
- calculate PnL.

## Next state

`BUILD_AND_SEAL_B13C_S0_REAL_EVENT_ONLY_CLUSTER_CENSUS_BUNDLE`
