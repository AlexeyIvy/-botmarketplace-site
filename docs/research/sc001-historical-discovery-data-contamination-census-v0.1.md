# SC001-H1-001 — Historical Discovery Data / Contamination Census v0.1

Date: 2026-10-02
Task: SC001-H1-001
Worker: H1_HISTORICAL_INDICATORS
Authorization: DESIGN_ONLY
Status: PREFREEZE CENSUS; NO DATA BODY OR OUTCOME ACCESS

## 1. Purpose and boundary

This census identifies the smallest historical bar/trade data surface that could support a bounded indicator benchmark without asserting freshness that has not been audited.

This task did not:
- open VPS/raw market data;
- parse market rows;
- execute network metadata/HEAD/body requests;
- launch Test Executor jobs or Runner bundles;
- open protected/raw outcomes or P1 evidence;
- calculate returns, alpha, PnL or strategy economics;
- search parameters, horizons, symbols, hours or venues;
- modify collectors or shared state.

Canonical control context:
- docs/research/sc001-execution-worker-routing-and-automation-architecture-v0.3.md
- docs/research/sc001-shared-data-and-resource-coordination-v0.1.md
- docs/research/sc001-feature-indicator-research-governance-v0.1.md
- docs/research/sc001-feature-indicator-taxonomy-v0.1.md
- docs/research/sc001-incremental-feature-testing-protocol-v0.1.md
- docs/research/sc001-contamination-registry-v0.41.json
- docs/research/sc001-research-strategy-agent-charter-v0.1.md

The current contamination registry remains read-only. This document is task-local and does not mutate contamination state.

## 2. Candidate physical source census

No row below is asserted to be clean Discovery evidence. Under DESIGN_ONLY, actual file presence, exact coverage and row semantics were intentionally not inspected.

| Census ID | Venue / product | Data kind / granularity | Actual date coverage | Candidate asset breadth | Local availability | Remote/source availability | Evidence role already consumed | Conservative classification now | Intended benchmark support |
|---|---|---|---|---|---|---|---|---|---|
| H1-DATA-BAR-01 | OKX / USDT-margined perpetual swap, exact instruments not yet frozen | OHLCV bar / 1 minute | UNVERIFIED; proposed minimum eligible span is >=120 complete UTC days after source/clock validation | 6-12 mechanically eligible symbols; no outcome ranking | UNVERIFIED_BY_TASK; no VPS/raw read performed | NOT_NETWORK_CHECKED; future metadata-only source check may be proposed | UNKNOWN at resource identity level; no H1 evidence consumed by this task | CALIBRATION_ONLY_PENDING_PRIOR_USE_AUDIT | P1, P2, P3, P4 when volume semantics are valid, P7 |
| H1-DATA-TRADE-01 | OKX / same USDT-margined perpetual swap universe | Public trades / event level | UNVERIFIED; only needed if exact trade-derived activity semantics are later authorized | Same mechanically frozen universe as H1-DATA-BAR-01 | UNVERIFIED_BY_TASK; no VPS/raw read performed | NOT_NETWORK_CHECKED; future metadata-only source check may be proposed | UNKNOWN at resource identity level; no H1 evidence consumed by this task | CALIBRATION_ONLY_PENDING_PRIOR_USE_AUDIT | Optional P4 activity validation or causal bar reconstruction; not required for v0.1 if canonical bars contain valid volume |
| H1-DATA-DERIVED-01 | Same venue/product as verified parent resource | Existing verified derived 1-minute feature-neutral table, only if exact DERIVED_ID already exists | INHERIT_VERIFIED_PARENT; not inspected in this task | Must exactly match the frozen eligible universe | REUSE_ONLY_IF_VERIFIED_RECORD_EXISTS; existence not asserted here | No acquisition path under this task | Inherits parent evidence restrictions; task-specific access receipt still required | INHERIT_PARENT; never upgraded to untouched by physical reuse alone | Preferred reuse path to avoid duplicate normalization work |

### Classification rule

For this package, an unresolved legacy source is not called untouched. Until a future metadata/prior-use audit mechanically proves otherwise it is treated as calibration-only/non-promotional.

A future block may be classified UNTOUCHED only when all of the following are proven before opening it:
1. exact DATASET_KEY / RESOURCE_ID identity is fixed;
2. date interval and instrument set are mechanically known;
3. prior SC001 use is audited;
4. no Selection/calibration inspection touched the block;
5. a task-specific evidence-access authorization assigns the block to Discovery, Asset Holdout or Chronological Confirmation.

Physical presence alone never grants evidence authorization.

## 3. Current canonical contamination fences

The current registry v0.41 is inherited without modification. The following constraints are binding for H1 design:

| Canonical fence | Existing role/state | H1 classification | H1 rule |
|---|---|---|---|
| C8 engineering day referenced by v0.41 | ENGINEERING_CLOCK_ONLY_NONPROMOTIONAL | calibration-only / engineering-only | May inform clock semantics only when separately authorized; never clean H1 promotional evidence |
| C8B calibration outcome | reuse_authorized=false | outcome-contaminated for reuse | Excluded from H1 benchmark selection, Discovery, holdout and Confirmation |
| Candidate 1 fresh-window outcome | reuse_authorized=false | protected/outcome-contaminated for reuse | Excluded |
| B13C protected interval | reuse_authorized=false | protected/outcome-contaminated for reuse | Excluded |
| Candidate 2 B-lite response outcome | outcome_accessed=false; historical lag return calculation unauthorized | not an H1 outcome source | No cross-venue response computation or reuse in this task |
| Any period inspected to choose feature, threshold, horizon, symbol subset or execution mode | selection/calibration by governance | calibration-only for that implementation | Cannot later be relabeled Discovery/Confirmation |

No terminal SC001 outcome window may be recycled as promotional evidence for this benchmark.

## 4. Data eligibility rules for the future benchmark

The benchmark source freeze should use one venue-local product class first to avoid venue-choice multiplicity. v0.1 therefore proposes OKX USDT-margined perpetual swaps as the candidate primary source class, subject to a later source-only audit. This is a source-design proposal, not a claim that the data are presently available or clean.

Eligibility must be outcome-blind:
- normalize instrument names first;
- require continuous source coverage across all four planned evidence blocks;
- require causal OHLCV semantics;
- require no unresolved timestamp duplication or bar-close ambiguity;
- if P4 is enabled, require a causally defined volume field;
- require at least 6 eligible instruments;
- cap at 12 instruments by lexicographic normalized symbol order if more are eligible;
- do not rank or filter instruments by return, alpha, volatility performance, historical profitability or feature effect.

If fewer than 6 instruments or fewer than 120 complete UTC days can be established without touching outcomes, return HISTORICAL_DISCOVERY_DEFER_DATA rather than searching a different symbol/hour/venue winner.

## 5. Evidence allocation rule

Once a clean eligible interval [T0,T1) is proven in a future authorized task:
- Selection uses the earliest 40% of complete UTC days and development assets only; once opened it is permanently calibration-only for this implementation.
- Discovery uses the next 20% and development assets only.
- Asset Holdout uses the next 20% and the pre-frozen holdout assets only.
- Chronological Confirmation uses the final 20% with the unchanged implementation and the pre-frozen eligible universe.
- no block boundary may be moved after outcome inspection.

Asset holdout membership is mechanical: sort eligible normalized symbols lexicographically and assign every fifth symbol (1-indexed positions 5,10,...) to holdout; all other eligible symbols are development assets. No outcome statistic participates in this split.

## 6. Required future source-only audit before any outcome-bearing run

A separate explicit task is required to resolve:
- exact archive/source identity;
- exact date coverage;
- exact instrument breadth;
- local verified-resource presence;
- source clock and bar finalization semantics;
- volume field semantics;
- prior-use/contamination classification;
- DATASET_KEY / RESOURCE_ID and, if applicable, DERIVED_ID.

Allowed future source checks may include bounded metadata/HEAD/source-availability checks only if explicitly authorized. This task executed none.

## 7. Census disposition

Census conclusion: the benchmark can be pre-frozen, but no historical dataset is certified untouched by this DESIGN_ONLY task.

Terminal design disposition:
HISTORICAL_BENCHMARK_PREFREEZE_READY_FOR_STRATEGY

Outcome access: false
Network access: false
Protected evidence access: false
VPS raw-file access: false

PROPOSED_SHARED_STATE_CHANGE: none.
