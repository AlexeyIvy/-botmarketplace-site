# SC001-H1-001 — Historical Discovery Data / Contamination Census v0.1

Date: 2026-10-02
Task: SC001-H1-001-CORRECTION
Parent task: SC001-H1-001
Worker: H1_HISTORICAL_INDICATORS
Authorization: DESIGN_ONLY_CORRECTION
Strategy review: PR #425 / comment 5961492007 / H1_PREFREEZE_SURVIVES_SOURCE_REUSE_CORRECTION
Status: PREFREEZE CENSUS; NO DATA BODY OR OUTCOME ACCESS

## 1. Purpose and boundary

This census reuses the existing frozen SC001 Binance USD-M 1m backbone for the bounded indicator benchmark without asserting multi-symbol coverage or freshness that has not been audited.

The package is ADAPTIVE_DISCOVERY_GENERATED: it was generated after prior SC001 outcomes and no independently pre-frozen provenance was demonstrated. A future positive Discovery remains adaptive and requires fresh chronological/prospective Confirmation. This correction opened no outcomes.

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

Source-reuse references, read as canonical qualification reports only:
- docs/research/sc001-data-acquisition-protocol-v0.1.md
- docs/research/sc001-data-q001-qualification-results-v0.1.md
- docs/research/sc001-data-q002-results-v0.1.md

The current contamination registry remains read-only. This document is task-local and does not mutate contamination state.

## 2. Candidate physical source census

No row below is asserted to be clean Discovery evidence. Existing source qualification is reused from canonical reports; actual current file presence, multi-symbol coverage and market rows were not inspected.

| Census ID | Venue / product | Data kind / granularity | Actual date coverage | Candidate asset breadth | Local availability | Remote/source availability | Evidence role already consumed | Conservative classification now | Intended benchmark support |
|---|---|---|---|---|---|---|---|---|---|
| H1-DATA-BAR-01 | Binance / USD-M perpetual; exact universe unresolved | Completed klines / 1 minute | Q001 qualified BTCUSDT on 2025-01-15 UTC (1,440 rows); acquisition protocol's 2020-01-01 through 2026-08-31 is a target, not proof of acquired coverage; multi-symbol >=120-day continuous span UNRESOLVED | 6-12 outcome-blind eligible instruments remain unfrozen pending source/prior-use audit; BTCUSDT is the qualified sample, not the selected H1 universe | Canonical Q001 sample qualification exists; current local verified reuse and resource identity UNVERIFIED_BY_THIS_TASK | Canonical Q001 download/checksum PASS; no new network check; current multi-symbol availability unresolved | Fixed day used for schema/access/storage qualification; prior SC001 use of other resources/windows unresolved; no H1 evidence consumed here | Qualified sample is engineering/calibration-only, non-promotional; unresolved legacy blocks CALIBRATION_ONLY_PENDING_PRIOR_USE_AUDIT | Primary source for P1/P2/P3/P4/P7 using completed OHLCV/quote-volume semantics |
| H1-DATA-TRADE-01 | Binance / USD-M BTCUSDT perpetual qualification sample | aggTrades / event level | Q001/Q002 canonical fixed-day sample: 2025-01-15 UTC only | One qualified sample instrument; no multi-symbol trade claim | Canonical sample qualification exists; current local identity not checked | Prior checksum/schema qualification only; no new source check | Engineering/schema qualification; Q002 corrected transact_time field interpretation | ENGINEERING_CALIBRATION_ONLY_NONPROMOTIONAL | Not a v0.1 benchmark input; no trade acquisition/reconstruction or substitute P4 feature proposed |
| H1-DATA-DERIVED-01 | Binance / USD-M perpetual; same verified parent universe | Existing verified derived 1-minute feature-neutral table, only if exact DERIVED_ID already exists | INHERIT_VERIFIED_PARENT; not inspected in this task | Must exactly match the future outcome-blind eligible universe | REUSE_ONLY_IF_VERIFIED_RECORD_EXISTS; existence not asserted here | No acquisition path under this task | Inherits parent evidence restrictions; task-specific access receipt still required | INHERIT_PARENT; never upgraded to untouched by physical reuse alone | Preferred reuse path if exact verified derived resource already exists |

Q001/Q002 do NOT prove multi-symbol 120-day coverage. Q001 establishes basic BTCUSDT 1m bar/quote-volume fields and integrity for one fixed day; Q002's Binance recheck is of aggTrades, not multi-symbol kline history. Reuse settled qualification. Do not rerun single-day basic bar/quote-volume semantics absent a concrete schema discrepancy.

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

The benchmark reuses the existing frozen Binance USD-M perpetual 1m completed-kline backbone. This is the Strategy-directed source-reuse correction, not venue selection by outcomes. Another venue requires a separate future mechanism-specific Strategy decision. The exact 6-12 instrument universe and continuous eligible interval remain unresolved until a separately dispatched source/prior-use audit.

Eligibility must be outcome-blind:
- normalize instrument names first;
- require continuous source coverage across all four planned evidence blocks;
- require causal OHLCV semantics;
- require no unresolved timestamp duplication or bar-close ambiguity;
- for P4, reuse canonical quote-volume qualification and verify applicability to the exact resource; reopen basic semantics only for a concrete schema discrepancy;
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
- exact Binance USD-M 1m archive/source identity;
- multi-symbol continuous coverage meeting the unchanged >=120 complete UTC-day requirement;
- exact outcome-blind 6-12 instrument universe;
- prior SC001 use and task-specific contamination/evidence-role eligibility;
- DATASET_KEY / RESOURCE_ID, verified local reuse and, if applicable, DERIVED_ID;
- exact Selection / Discovery / Asset Holdout / Chronological Confirmation allocation and access boundaries.

Reuse settled single-day basic bar/quote-volume qualification. A concrete schema discrepancy is required before reopening those semantics; do not repeat Q001/Q002 merely to create another smoke. Current local files and clean evidence blocks are not certified by these historical reports.

This source-only audit may be separately dispatched before the R1 family-wise multiplicity decision rule is frozen because it opens no outcomes. Any R1 outcome-bearing run remains blocked until that exact rule is frozen. The audit itself is not authorized by this correction.

Allowed future source checks may include bounded metadata/HEAD/source-availability checks only if explicitly authorized. This task executed none.

## 7. Census disposition

Census conclusion: the corrected prefreeze reuses the existing Binance backbone, but multi-symbol 120-day coverage, local resource identity and clean evidence allocation remain unresolved. No historical dataset is certified untouched by this DESIGN_ONLY_CORRECTION task.

Terminal design disposition:
HISTORICAL_BENCHMARK_PREFREEZE_READY_FOR_STRATEGY

Outcome access: false
Network access: false
Protected evidence access: false
VPS raw-file access: false

PROPOSED_SHARED_STATE_CHANGE: none.
