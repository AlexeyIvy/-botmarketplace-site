# SC001 Current Roadmap and Stop Rules v5.164

Date: 2026-09-27
Status: **B15-P2 SOURCE CENSUS PASS / EXACT 94-EVENT SET FREEZE WRAPPER PREPARED**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.163.md`

## Current B15-P2 state

The Bybit source-only census passed:

- in-scope closed USDT linear perpetuals: **94**
- admitted events: **94**
- announcement coverage: **100%**
- delivery months: **9**
- source timestamp-integrity issues: **0**

Canonical summary:

`docs/research/sc001-b15p2-bybit-delisting-source-census-networked-result-v0.1.json`

No price, basis, return or PnL data was opened.

## Mandatory event-set freeze before semantic audit

The next step is to promote and freeze the exact host source-only result containing all 94 admitted event identities.

Prepared wrapper:

`scripts/research/freeze-b15p2-bybit-source-census-event-set-v0.1.sh`

SHA256:

`b63134c62eb79f62da3246c2870d98cdceb45b60b0e21876fc0dcc32c2fdae11`

The wrapper is network-free.

It validates before promotion:

- exact source-census PASS state;
- exact frozen census window;
- 479 announcements retrieved;
- 271 derivative-relevant announcements;
- 32 globally missing `publishTime` rows;
- zero invalid `publishTime` rows;
- 94 closed in-scope instruments;
- 94 admitted events;
- 100% announcement coverage;
- nine delivery months;
- zero source-integrity issues;
- every frozen source gate true;
- all 94 unique event identities;
- causal first/last announcement timestamps;
- positive recomputed lead time;
- official Bybit announcement URL domains;
- source-only firewalls.

Promotion preserves the original result bytes and computes an independent deterministic SHA256 digest of the frozen event-set core.

## Target GitHub artifact

`docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json`

Freeze manifest:

`docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json`

No semantic audit is authorized before this exact-set freeze is complete.

## Strategy Manager

No Strategy Review is triggered yet.

Reason:
the source-census PASS is already governed by the frozen `pass_alone_triggers_review=false` rule, and the event-set freeze is evidence-preservation work only.

The next mandatory strategic gate remains before any B15-P2 price outcome.

## Next state

`RUN_NO_NETWORK_EVENT_SET_FREEZE_PREFLIGHT_AND_PROMOTE`
