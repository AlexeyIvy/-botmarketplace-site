# SC001 Current Roadmap and Stop Rules v5.210

Date: 2026-09-30
Status: **B15-P2 P0S SOURCE-STRUCTURE STOP / FROZEN SECONDARY**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.209.md`

## B15-P2 frozen baseline

The original 2026 frozen P0 remains:
`DEFER_SOURCE_COVERAGE`

No same-evidence rescue is authorized.

The fresh 2025 source-only successor remains nonpromotional. Its original census found:
- 154 in-scope closed USDT LinearPerpetual instruments;
- 120 admitted causal exact-symbol events;
- coverage 77.9220779221%;
- 34 unmatched symbols;
- one legacy source timestamp integrity issue.

Price/index/basis/returns/PnL remained closed throughout the successor source work.

## Cross-type audit execution

Frozen protocol:
`docs/research/sc001-b15p2-p0s-2025-unmatched-announcement-index-cross-type-audit-protocol-v0.1.md`

Implementation:
`research/sc001/sc001_b15p2_p0s_2025_cross_type_index_audit_v0_1.py`

Implementation SHA256:
`2ab1203788747e857d1fb89a3e849e0d8eb47b6cdd000e13875cf683811fb2a2`

Offline validation:
- job `job_20260930T001448Z_a4175115`;
- network `offline`;
- PASS;
- exactly one offline self-test.

Live source-only run:
- job `job_20260930T033315Z_83502e67`;
- repo head `f749565e513d322a2ba815a050528b06689595df`;
- network `public_research`;
- exactly one live run;
- exit code 2;
- terminal state `B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_REVIEW`;
- fail-closed cause `UNKNOWN_ANNOUNCEMENT_TYPE:Earn`.

Canonical exact result:
`docs/research/sc001-b15p2-p0s-2025-cross-type-index-audit-result-v0.1.json`

SHA256:
`79dc9be3dcc8b9334518cc9653025bbd8a55e086cad85aa19f988a7fab7aec7a`

Canonical exact log bytes:
`docs/research/runtime-inbox/sc001-b15p2-p0s-2025-cross-type-index-audit-v0.1.log.txt`

SHA256:
`95eaa50989f3dbe53725472a3d88eae71e1f0aa848d5d0fb852131cfcc1b1bb6`

Three-role review:
`docs/research/sc001-b15p2-p0s-2025-cross-type-index-audit-review-v0.1.md`

SHA256:
`f9c498942ca0b615f2094a16909d517141f463d160b0bf502bf54840e9c6277b`

Contamination registry:
`docs/research/sc001-contamination-registry-v0.40.json`

SHA256:
`6bc1af6e94e8de941b839782134029e6ba5f34c058ea2e4c9b8367367a838334`

## Interpretation

The run did not compute a recovery count because the live official source violated the frozen announcement-type schema before the coverage analysis could complete.

Therefore:
- the audit did not materially pass;
- the unchanged 80% source gate was not demonstrated;
- the audit also does not justify a numerical claim that the 80% gate would fail after a corrected parser;
- the material finding is that the preregistered source structure was not stable enough to complete the test.

Under the current stop objective, this is the natural end of B15-P2 rather than a trigger for another parser-rescue sequence.

## B15-P2 terminal branch rule

Current disposition:
`B15P2_P0S_SOURCE_STRUCTURE_STOP_FREEZE_SECONDARY`

Do not:
- add `Earn` to the enum and rerun;
- widen announcement-type parsing based on this observed run;
- launch an article-body rescue audit;
- rerun the cross-type audit;
- open new B15-P2 price/index/basis outcomes;
- lower the 80% source gate;
- use an alternate execution plane;
- bypass Test Executor rate limits.

Reopening B15-P2 requires a new explicit Strategy/User decision and genuinely new source-level justification. It is not an automatic continuation of this audit.

## Firewalls

Still CLOSED:
- affected-contract price;
- observed index values;
- basis;
- returns;
- PnL;
- L1/L2;
- individual trades;
- funding;
- mark/premium/spot;
- external venues;
- trading.

## Portfolio-level next state

B15-P2 returns to the portfolio as a frozen secondary candidate, not an active engineering branch.

The separately preregistered next-primary forced-flow relative-dislocation candidate remains under its existing Strategy/User gate and receives **no automatic outcome authorization** from this B15-P2 decision.

Next allowed action:
`RETURN_TO_STRATEGY_USER_GATE_WITH_B15P2_FROZEN_SECONDARY`
