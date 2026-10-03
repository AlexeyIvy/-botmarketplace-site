# SC001-H1-002 — Binance 1m Source / Prior-use Audit v0.1

Date: 2026-10-03
Worker: H1_HISTORICAL_INDICATORS
Authorization: DESIGN_ONLY / SOURCE_PRIOR_USE_AUDIT
Task PR: https://github.com/AlexeyIvy/-botmarketplace-site/pull/426
Task branch: sc001/h1/SC001-H1-002
Task manifest: docs/research/tasks/sc001-h1-002-binance-source-prior-use-audit.json
Task manifest SHA256: 155ddf25a1c28b9fb887a798b2a92b7a2792afa165b444ec36da29ec9e142c69
Dispatch / pre-claim revalidated main: 300793b0f8065252fd0020ec96783a929b2bb72c
Starting task head: 0d5e8765ab5eb541a4d17206c7f7203ef7af95c3

Terminal status: H1_SOURCE_PRIOR_USE_AUDIT_DEFER_METADATA_ACCESS
Secondary unresolved gate: common coverage and exact eligible universe are not proven.
Strategy review required: true. Merge authorized: false.

## SOURCE IDENTITY

Mechanically proven in this run:
- The supplied pull_request event identified this repository, PR #426 and action ready_for_review. Exact PR retrieval confirmed repository ID 1149728560, open/non-draft state, the case-sensitive [SC001][H1][READY] title prefix, TASK_ID SC001-H1-002, WORKER_ID H1_HISTORICAL_INDICATORS and DISPATCH_STATE READY before claim.
- No existing PR comments, review instructions, claims or terminal receipts were returned before claim. The PR body and exact manifest provide the current Strategy dispatch.
- The task allows this source-only audit with zero research executions, zero source-network runs and zero new variants. It permits exactly two result artifacts, at most three worker repository commits, and no lifecycle mutation.
- Claim was written as prescribed: only DISPATCH_STATE changed to IN_PROGRESS; one CLAIM_BLOCK with a three-hour lease was appended; title unchanged.
- Current canonical documents fix the source class as Binance USD-M perpetual completed 1m klines.
- Reader list_roots returned exactly one logical root: b15_identity_inventory, mode read_only. This is not an approved SC001/H1 historical-data or metadata-inventory root for this task. No list_files call followed.

Canonical historical claims, not newly reverified source facts:
- Acquisition protocol identifies data.binance.vision / binance/binance-public-data, daily/monthly archives and accompanying SHA-256 checksums.
- Q001 reports a BTCUSDT USD-M 1m sample for 2025-01-15 UTC: 1,440 data rows, compressed size 63,072 bytes, checksum match, monotonic timestamps, zero duplicate opens and zero minute-interval breaks.
- Q001 qualifies OHLC, volume, quote volume, trade count and taker-buy fields for that sample. Q002 rechecks Binance aggTrades, not multi-symbol 1m history.
- The protocol's 2020-01-01 through 2026-08-31 range is an acquisition target, not proof of acquired coverage.

Unresolved:
Exact H1 archive basenames/URLs, exact-resource schema/version and timestamp applicability, canonical raw content hashes, present storage locations and the mapping from legacy files to source identities. The cited Q001 narrative says its checksum matched but does not supply the digest. No basename, digest or local path is fabricated. Basic Q001/Q002 qualification was not rerun; no concrete schema discrepancy was observed through the permitted surface.

## COMMON COVERAGE

No common multi-symbol interval of at least 120 complete UTC days is mechanically established. T0, T1 and D remain null/unresolved.

The canonical historical qualification claim covers one instrument on one fixed UTC day. It cannot establish six eligible instruments, continuous coverage across four blocks, or current local possession. This is absence of permitted proof, not evidence that Binance lacks coverage.

No archive availability query, source HEAD/body request, market-row parsing, gap reconstruction or timestamp recomputation was performed. DEFER_METADATA_ACCESS is primary because the allowed inventory surface is missing; coverage remains an explicit secondary DEFER_COVERAGE gate, not a PASS.

## OUTCOME-BLIND UNIVERSE

exact_instruments: null
development_instruments: null
holdout_instruments: null
eligibility_status: UNRESOLVED_NOT_FROZEN

The unchanged eligibility rule requires causal completed OHLCV semantics, continuous common source coverage across the planned blocks, no unresolved timestamp duplication/bar-close ambiguity, and exact-resource applicability of settled quote-volume semantics. At least 6 and at most 12 eligible instruments are required.

Only after eligibility is proven may normalized symbols be sorted lexicographically, capped at the first 12 if necessary, and split with 1-indexed positions 5,10,... as asset holdout and the remainder as development assets. No instrument list is inferred from market popularity, Q001's BTCUSDT sample or performance. No alternative symbol subsets or venues were considered.

## PRIOR USE / CONTAMINATION

Canonical historical claims:
- Q001's 2025-01-15 BTCUSDT sample was opened for engineering/schema/access/storage qualification. It remains ENGINEERING_CALIBRATION_ONLY_NONPROMOTIONAL, not untouched promotional evidence.
- Q002's Binance sample is aggTrades on the same day. It neither certifies fresh H1 kline blocks nor enlarges qualified kline breadth.
- The reviewed benchmark is ADAPTIVE_DISCOVERY_GENERATED. This audit does not change that classification.
- Registry v0.41 and the task-referenced census preserve the C8 engineering-only fence and deny reuse of C8B calibration outcomes, Candidate 1 fresh-window outcomes and B13C protected intervals. Candidate 2 historical lag-response calculation remains unauthorized.
- Any window inspected for feature, threshold, horizon, asset-subset, execution-mode or candidate choice is nonpromotional for that implementation. Terminal outcome windows cannot become fresh H1 promotional evidence.

Unresolved:
No exact candidate resource/window/universe can yet be matched against prior SC001 use. Registry v0.41 inherits older lineage; reading it does not prove a complete prior-use audit of an unidentified Binance resource. No older outcome report, protected P1 evidence or raw outcome was opened to resolve that gap.

Conservative disposition:
Unresolved legacy source/window eligibility is CALIBRATION_ONLY_NONPROMOTIONAL. This is a task-local conservative access interpretation, not a contamination-registry mutation or a finding that all Binance history was used. No block is certified UNTOUCHED and no exact overlap is asserted without identities.

Untouched eligibility requires exact DATASET_KEY/RESOURCE_ID, mechanically known dates/instruments, prior-use audit, proof of no Selection/calibration inspection, and task-specific evidence authorization before opening. None is replaced by physical possession.

## DATASET_KEY / RESOURCE_ID

dataset_key: null
resource_id: null
freeze_status: NOT_FREEZABLE_FROM_ALLOWED_EVIDENCE

| Required field | Supported status |
|---|---|
| source_provider | Binance, canonical source class |
| source_host_or_endpoint_class | data.binance.vision public archive, canonical historical claim |
| market_type | USD-M perpetual, canonical source class |
| instrument_or_frozen_universe_identifier | Unresolved |
| data_kind | Completed klines |
| granularity_or_archive_class | 1m fixed; exact daily/monthly resource set unresolved |
| utc_start | Unresolved |
| utc_end_exclusive | Unresolved |
| exact_source_identity_rule | Exact basename/query/resource mapping unresolved |
| source_semantic_version_when_relevant | Exact-resource applicability unresolved |

A partial key is not a frozen dataset identity. No placeholder key is hashed. RESOURCE_ID must be SHA256 of the canonical JSON serialization of the complete DATASET_KEY, independent of strategy name.

No verified, reservation, derived or task-access registry record was created. No exact deterministic registry lookup can certify the requested resource until its identity is known. This audit makes no claim that such records or files do not exist elsewhere.

## LOCAL REUSE / DERIVED_ID

Observed permitted inventory response:

```json
{"roots":[{"name":"b15_identity_inventory","mode":"read_only"}]}
```

This root is unrelated to the approved H1 historical-data inventory. Under the task's legacy_inventory_rule it was not inspected. No logical path, basename, size, extension or raw hash for an H1 file was therefore observed.

local_raw_reuse_verified: false
local_presence: UNKNOWN
derived_id: null
derived_reuse_verified: false

LEGACY_PRESENT_UNRESOLVED is not asserted as an observed presence state: physical presence itself was not established. The canonical sample report is historical lineage, not current VPS inventory. Exact DERIVED_ID requires ordered verified parent RESOURCE_IDs, transform implementation hash, exact configuration hash and schema version; these inputs are not known here.

No Runner, Test Executor, shell/network or alternate-root workaround was attempted. No reacquisition or recomputation is authorized.

## EVIDENCE BLOCK ALLOCATION

Exact allocation is not frozen because [T0,T1), D and eligible instruments remain unresolved. No calendar dates or memberships are invented.

The binding prospective rule is unchanged:
1. Selection: earliest 40% of complete UTC days, development assets only; opened Selection is permanently calibration-only for that implementation.
2. Discovery: next 20%, development assets only.
3. Asset Holdout: next 20%, pre-frozen holdout assets only.
4. Chronological Confirmation: final 20%, unchanged implementation on the pre-frozen eligible universe.

Use whole UTC days from T0, assigning rounding remainder to final Chronological Confirmation. Block boundaries cannot move after outcome inspection. Discovery, Asset Holdout and Confirmation each need separate explicit authorization. All blocks remain unopened by this task.

The unresolved R1 family-wise multiplicity decision rule still blocks R1 outcomes. State-only incremental testing still requires its separately frozen base-opportunity denominator. Neither is resolved or bypassed by a source audit.

## ACCESS BOUNDARY

```json
{
  "outcome_accessed": false,
  "protected_evidence_accessed": false,
  "market_rows_read": false,
  "network_accessed": false,
  "test_executor_job_launched": false,
  "runner_bundle_created": false,
  "runner_bundle_executed": false,
  "vps_read_text_used": false,
  "collector_changed": false
}
```

network_accessed=false means no market-source metadata/HEAD/body requests, acquisition or external research network run; authorized GitHub operations and the Reader metadata RPC were used.

Observed operations: GitHub canonical reads, task claim, one VPS Reader list_roots call, and authorized task-artifact/terminal writes. No VPS list_files, protected/raw access, resource registry write, research execution, repair, feature calculation or search occurred. All variant budgets remain zero. No shared state or PR lifecycle change is authorized.

## TERMINAL DISPOSITION

H1_SOURCE_PRIOR_USE_AUDIT_DEFER_METADATA_ACCESS

The bounded audit establishes a concrete access limitation: no relevant approved historical-data metadata root is exposed. It preserves existing sample qualification and identifies the exact unproven gates instead of substituting historical targets for acquired data.

Strategy Manager review is required. Within this task, stop after the manifest and terminal receipt. A separate authorized follow-up may provide an approved H1/SC001 metadata inventory with source identity, common coverage, current local hashes/lineage and prior-use mapping. This result does not authorize that follow-up, network acquisition, a new root, or any outcome access. Do not repeat a source qualification smoke without a concrete schema discrepancy.

PROPOSED_SHARED_STATE_CHANGE: none.
MERGE_AUTHORIZED: false.
PR remains open for Strategy Manager review.

### Canonical reference snapshot

All references below were read from main; pre-claim comparison to DISPATCH_BASE_HEAD was identical. The manifest and terminal receipt record post-result main revalidation. SHA values below are Git blob identities, not raw-dataset SHA256 values.

- docs/research/sc001-h1-historical-indicators-project-instructions-v0.1.md — 99574753f038c6f435ff358cad273b682379e9e1
- docs/research/sc001-h1-work-event-trigger-instructions-v0.1.md — f12bb2302db1adf96729e45b65f703b4579db72e
- docs/research/sc001-execution-worker-routing-and-automation-architecture-v0.3.md — 8a6010e2fdc6d914f73c165701f93bba4ac7acb0
- docs/research/sc001-shared-data-and-resource-coordination-v0.1.md — cff6ec686601db030f4d8d1a16cad050745cf0bd
- docs/research/sc001-historical-discovery-data-contamination-census-v0.1.md — 06714cabb73c7c4438ed9bd4c2143eba1fbe666d
- docs/research/sc001-historical-indicator-benchmark-batch-design-v0.1.md — 6b82d39c6e3c3af48e5458106d954a8f953ab8a8
- docs/research/sc001-historical-indicator-benchmark-variant-ledger-v0.1.json — 325b89cad164c9ad3e411abd5e08a07e82a168d7
- docs/research/sc001-contamination-registry-v0.41.json — df03cf18222fafb7cb8bbc4f69c720c03ecc528e
- docs/research/sc001-data-acquisition-protocol-v0.1.md — 8d594424ff7b30e2cb159840f133ff881bd2c3b5
- docs/research/sc001-data-q001-qualification-results-v0.1.md — be0676eed5d4a503d2f23f5225e44fcb4c872624
- docs/research/sc001-data-q002-results-v0.1.md — 0babb95ae8a9c08ce2682824581d7416dd1dd96f
- docs/research/sc001-worker-result-manifest-schema-v0.1.json — e9507a2b88abd86316695baa841b3194b9b52898
