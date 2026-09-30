# SC001 — Strategy Manager Forward Portfolio Checkpoint Request v0.1

Date: 2026-09-30
Status: REVIEW REQUEST / NO NEW OUTCOME AUTHORIZED
Scope: SCALPING RESEARCH / SC001 / FORWARD PORTFOLIO THINKING WHILE PRIMARY WINDOW ACCUMULATES

## Why this review is requested

Execution work for the current primary has reached a natural waiting boundary.

Primary family:
VENUE_LOCAL_FORCED_FLOW_RELATIVE_DISLOCATION

Fresh evidence window:
2026-09-30T00:00:00Z <= event_time < 2026-10-07T00:00:00Z

No real S0 outcome has been opened.

Relevant current Worker Result Manifests:
- docs/research/worker-results/sc001-next-primary-forced-flow-relative-dislocation-prefreeze-manifest-v0.3.json
- docs/research/worker-results/sc001-next-primary-forced-flow-archive-metadata-review-manifest-v0.1.json
- docs/research/worker-results/sc001-next-primary-okx-archive-publication-lag-manifest-v0.1.json
- docs/research/worker-results/sc001-reserve-candidate2-b-lite-static-feasibility-manifest-v0.1.json

Current source/materialization state:
- Bybit exact archive transport qualified on the metadata preflight;
- OKX resolver contract is functional;
- recent OKX daily archives exhibit publication lag;
- post-window S0 materialization must wait for all exact required archive identities;
- provenance planner and full-window gap/completeness checker passed offline self-test;
- S0 remains locked until the fresh window closes and a separate exact execution authorization exists.

## Review objective

Do not create work merely to fill the waiting period.

Use this checkpoint to look one level ahead and advise on the next research portfolio decisions that would be useful after the current primary produces a terminal S0 state.

Please consider:

1. If Candidate 1 returns REJECT_FORCED_FLOW_RELATIVE_HEADROOM:
   - should Candidate 2 become the next primary;
   - should another already-known family take priority instead;
   - what is the cheapest next mechanism-level falsification path.

2. If Candidate 1 returns DEFER_SOURCE_OR_SAMPLE:
   - what conditions justify waiting/collecting more;
   - when should the program stop allocating attention to this family.

3. If Candidate 1 returns SURVIVE_HEADROOM:
   - confirm the minimum next evidence sequence before any PnL/trading interpretation;
   - identify what must remain fresh/chronological;
   - identify the smallest necessary execution/latency validation.

4. Reassess reserve Candidate 2:
   SAME_ASSET_CROSS_VENUE_CAUSAL_FLOW_PROPAGATION
   using the current B-Lite static package only.
   Do not open old C8 outcome bodies.
   Confirm whether its reserve status, mechanism-overlap verdict and future live-latency gate still look appropriate.

5. Portfolio horizon:
   identify at most two additional mechanism families worth keeping on the medium-term SC001 slate after Candidate 1 / Candidate 2, based on:
   - frequent opportunity potential;
   - realistic small-capital suitability;
   - two-fill or otherwise economical execution architecture;
   - causal public observability;
   - low avoidable data/engineering burden;
   - mechanism distinction from already terminal SC001 families.

This is strategic planning only, not an authorization to launch those mechanisms.

## Requested output

Return only:
- STATE CHANGE
- PRIMARY AFTER EACH CANDIDATE-1 TERMINAL BRANCH: REJECT / DEFER / SURVIVE
- CANDIDATE-2 RESERVE VERDICT
- MEDIUM-TERM PORTFOLIO: at most two mechanism families
- CONTAMINATION / MULTIPLICITY CONSTRAINTS
- NEXT ALLOWED ACTION
- DO NOT DO

If no change is justified, explicitly return:

NO ROADMAP CHANGE REQUIRED

## Hard boundaries

Do not:
- authorize Candidate 1 S0 through this request;
- inspect Candidate 1 fresh-window outcomes;
- reopen B15-P2;
- mine protected B13-C outcomes;
- reuse old C8 price/lag outcomes for Candidate 2;
- start Candidate 2 outcome work while Candidate 1 remains the active outcome-bearing family;
- start Candidate 3 outcome work;
- lower H=52 bps;
- change the fixed 7-day / 12-symbol breadth rules;
- move the fresh window;
- create a long historical recap when the manifests already contain the facts.

GitHub remains the source of truth.
