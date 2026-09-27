# SC001 Current Roadmap and Stop Rules v5.144

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C real S0 outcome bundle SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.143.md`

## Preconditions complete

B13-C source-only event census:
PASS

Exact 1,905-cluster freeze:
PASS

76-archive metadata preflight:
PASS

Price-anchor extraction:
PASS

Price-anchor dataset freeze:
PASS

Outcome analyzer synthetic self-test:
PASS

No real signed reversal has yet been calculated.

## Exact real outcome bundle

Bundle ID:

`bundle_20260927T085215Z_c2fc14bb`

SHA256:

`8263a1192caf1e7927b83fde66bc676b3411a5579b53d602e5c2403dce6f90e1`

Approval code:

`BM-8263A1192CAF`

Runtime:

`offline-research-v1`

Package files:
7

Package bytes:
29,589

Runtime read-only inputs:
- frozen extraction manifest;
- frozen price_anchors.jsonl.

Frozen valid sample:
1,793 clusters.

## Frozen real computation

For each valid cluster only:

`signed_reversal_bps = reversal_sign * 10000 * ln(P_exit/P_entry)`

Report only:
- pooled n / p25 / median / p75;
- strictly-positive count/share;
- six complete-day valid counts and medians;
- four frozen gate booleans;
- one terminal classification.

Frozen gates:
- n >=100;
- median >=30 bps;
- positive share >=55%;
- >=4/6 complete UTC days have positive median.

Allowed terminal states:
- `B13C_S0_SIMPLE_REVERSAL_HEADROOM_SURVIVE`;
- `B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`;
- `B13C_S0_DEFER_SAMPLE`.

No rescue search, alternate horizon, per-symbol ranking or PnL is allowed.

## Next state

`RUN_B13C_S0_REAL_OUTCOME_AFTER_EXPLICIT_APPROVAL`
