# SC001 B15-P2 P0 — Three-Role Review v0.1

Date: 2026-09-29
Status: **DEFER_SOURCE_COVERAGE**

Canonical result:
`docs/research/sc001-b15p2-p0-basis-convergence-result-v0.1.json`

SHA256:
`e2554fcf95992e64d58ffcdac85faf68edff45f5320a596a5249256176bd13a3`

Execution job:
`job_20260929T142359Z_85d4a91d`

Frozen implementation SHA256:
`dc52b2fb4914ea29bc6bc85a9cfc8aa27f327d8dd160e6c4aa9feeab5e328945`

## Registered result

The exact frozen full P0 run completed once with exit code 0.

The pre-registered source gate failed:
- eligible events: 23 / 94; required >= 90;
- eligible delivery clusters: 18 / 37; required >= 35;
- eligible months: 8 / 9; required all nine;
- 2026-09 has no eligible event or cluster.

The source ledger records 126 registered-snapshot errors:
- 125 CONTRACT_ZERO_ACTIVITY under the frozen rule requiring volume > 0 and turnover > 0;
- 1 Bybit contract-kline retCode 10016 for LISTAUSDT at one snapshot.

No alternate source, interpolation, nearest candle, symbol filtering, horizon change, or threshold change was used.

## Role 1 — market / financial review

The evidence does not support advancing this branch to execution-feasibility research. The decisive reason is insufficient admissible source coverage, not an economic rejection.

Descriptive surviving-set values:
- cluster median D = 0.43078129 bps;
- D-positive cluster share = 55.56%;
- cluster median C_event = 0.652667335 bps;
- positive monthly median D = 4 months.

These values are not strong, but the source gate failed first, so they are not admissible as a terminal timing or economic verdict.

Conclusion: preserve the frozen P0 result as DEFER_SOURCE_COVERAGE and do not promote surviving-subset statistics into a stronger claim.

## Role 2 — programmer-trader / research engineering review

Execution integrity passed:
- exact frozen implementation SHA matched;
- exact frozen specification and event clock were used;
- the full registered run completed once;
- canonical result bytes match the Test Executor artifact exactly;
- prohibited data classes remained closed.

The dominant issue is source eligibility, not a code crash: 125 of 126 snapshot errors are deterministic CONTRACT_ZERO_ACTIVITY under the pre-registered rule.

Because outcome access has occurred, do not modify the implementation, offsets, activity rule, source, metrics, or gates and rerun this same 94-event evidence as a rescue.

Conclusion: freeze this P0. Any successor must be separately specified before new outcome access.

## Role 3 — mathematician / statistician review

The primary inferential design required >=90 events, >=35 delivery clusters, and coverage of all nine months. Actual coverage is 23 events, 18 clusters, and eight months.

The observed descriptive 90% bootstrap interval for median D is:
`[-24.623053925, 26.20930124] bps`.

Because the source gate failed and eligibility is conditioned on contemporaneous activity, the surviving subset cannot replace the pre-registered population for inference.

Conclusion: DEFER, not PASS and not terminal REJECT.

## Joint decision

Final verdict:
`DEFER_SOURCE_COVERAGE`

Allowed next work:
1. Review official Bybit source-coverage semantics only.
2. Determine why registered snapshots frequently have zero volume/turnover.
3. If a defensible successor design exists, pre-register it fresh before new successor outcome access.
4. Require a new gate before another outcome-bearing run.

Forbidden:
- changing the current P0 result;
- relaxing zero-activity eligibility and rerunning the same evidence;
- substituting mark, premium, spot, another venue, third-party archives, interpolation, or nearest candles;
- outcome-based symbol/horizon/threshold selection;
- advancing this result as if the source gate had passed.
