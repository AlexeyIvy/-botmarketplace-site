# SC001-X1-002E — Independent PIT source GO/NO-GO

Date: 2026-10-11
Worker: `X1_CROSS_ASSET_STRUCTURE`
Authorization: `T0_SOURCE_DOCUMENTATION_AND_STRATEGY_ONLY`
Frozen cutoff: strictly before `2026-10-01`
Predecessor: PR #466 / `X1_PIT_METADATA_CAPTURE_SOURCE_INCOMPLETE`

## Decision

`X1_PIT_HISTORICAL_SOURCE_STOP_PROSPECTIVE_OPTION_ONLY`

No reviewed independent source is publicly documented as a complete, auditable point-in-time identity master for the full Binance USD-M perpetual lifecycle required by the frozen X1 atlas. The earliest-stop condition is met. Do not acquire vendor data, restart X1-003, substitute current survivors, infer membership from price/archive availability, or relax the frozen cutoff/universe.

This is a source-feasibility STOP, not an alpha rejection and not evidence that cross-asset information transfer is absent.

## Required source standard

A qualifying source must establish, as of the frozen cutoff and without outcome-based selection:

1. historical onboarding/listing identity and time;
2. effective delisting/termination status and time;
3. redenomination and contract-multiplier lineage;
4. symbol reuse, aliasing, relisting and identity continuity;
5. an explicit historical-completeness attestation;
6. immutable or reproducibly versioned records suitable for external audit.

All six are conjunctive. A current catalog, trade-first/last timestamps, archive-key presence, or a vendor's general market-data history is insufficient.

## Option 1 — Tardis.dev Instruments Metadata API

Official public documentation reviewed:

- <https://docs.tardis.dev/api/instruments-metadata-api>
- <https://docs.tardis.dev/historical-data-details>

Documented strengths:

- independent normalized instrument metadata with exchange-native IDs;
- `availableSince`, optional `availableTo`, optional exchange `listing`, current `active`, contract type and multiplier;
- a chronological `changes` structure;
- explicit recognition that exchanges may reuse symbol IDs or retain aliases/legacy symbols.

Binding gaps:

- `availableSince` is Tardis metadata availability and may differ from exchange listing time;
- `availableTo` may lag the actual exchange delisting;
- `listing` is optional;
- only `contractMultiplier` changes are guaranteed accurate and complete; other historical field changes are best effort and may omit changes;
- the public documentation does not attest complete onboarding, delisting, relisting, redenomination and identity continuity for all Binance USD-M perpetuals before 2026-10-01;
- most metadata access requires a paid Pro/Business subscription and API key.

Disposition: `DOCUMENTED_PARTIAL_LINEAGE_NOT_QUALIFIED`.

The explicit completeness limitations decide this option without any API call or purchase. Acquisition would also be an exact `USER_COST_T3_GATE`, not permission granted by this task.

## Option 2 — Kaiko Reference Data

Official public documentation reviewed:

- <https://www.kaiko.com/products/reference-data>
- <https://docs.kaiko.com/explore-our-data/data-dictionary>
- <https://docs.kaiko.com/rest-api/general/getting-started/data-versioning>
- <https://docs.kaiko.com/coverage/instrument-explorer>

Documented strengths:

- independent standardized identifiers, exchange-asset mappings and derivatives contract specifications;
- product coverage claims include supported trading pairs and derivatives details;
- datasets are versioned, and semantic corrections create a new dataset version rather than being changed silently;
- historical derivatives metrics are offered, subject to subscription and coverage.

Binding gaps:

- public documentation does not define an append-only historical contract-master event stream for Binance USD-M;
- no public attestation establishes complete pre-cutoff onboarding, exact delisting effectiveness, redenomination/multiplier lineage, relisting or reused-symbol identity continuity;
- a “complete mapping” of supported/current pairs is not a point-in-time completeness guarantee for every historical contract;
- data versioning improves auditability of returned datasets but does not itself prove lifecycle completeness; additions may occur without a new dataset version;
- access to the relevant commercial product would require licensing/credentials and cost review.

Disposition: `AUDITABLE_VERSIONING_WITHOUT_DOCUMENTED_PIT_COMPLETENESS_NOT_QUALIFIED`.

No trial, API request, sales contact, data sample or purchase is authorized. Any future commercial evaluation is an exact `USER_COST_T3_GATE` and would first need a written vendor attestation covering the six conjunctive requirements.

## Three-lens review

### Trader / market economics

A multiyear 1m atlas built from survivors or inferred archive presence can manufacture apparent breadth and stability. Correlation remains descriptive, not trading proof. With no trustworthy historical membership clock, downstream leader/follower results cannot support an Edge-to-Fill decision. Opportunity frequency, actionable latency and economic headroom remain unknown because no outcome data were opened.

### Engineering / trading systems

Tardis exposes useful lifecycle-like fields but documents timing lag and incomplete change history. Kaiko documents reproducible versioning but not the required lifecycle-completeness contract. Neither public documentation closes the identity boundary. A hashable vendor response cannot compensate for incomplete semantics.

### Statistics / evidence

Missing delisted, renamed or reused-symbol histories creates survivorship and identity-mixture bias before pair/lag multiplicity is even considered. That bias cannot be repaired by later holdout, robustness metrics or factor residualization. The frozen historical atlas therefore stops before outcome access.

## One prospective-only option — not authorized

`PROSPECTIVE_FIXED_ANCHOR_TARGET_REGISTRY_V0`

If Strategy Manager later finds the economic question worth pursuing, define a new forward-only program:

- freeze one very small anchor set before observation (for example BTC and ETH) and an outcome-blind target eligibility rule;
- establish a new start timestamp; do not claim any pre-start history;
- capture append-only raw instrument metadata snapshots plus contract-info/listing/delisting notices from that timestamp forward;
- bind every identity transition to request/receive times, raw bytes, SHA256, source URL/stream identity and immutable sequence;
- treat symbol reuse/relisting as a new lineage unless continuity is explicitly proven;
- predeclare a small lag-profile rule, survivor budget and untouched chronological holdout before any return/lag outcome access.

This is only a prospective architecture concept. It is not X1-003, does not authorize a collector, source acquisition, Test Executor/Runner execution, market-data access or outcome computation. It requires a separate mechanism/economic review and separate authorization; collector creation or mutation remains a T3 user gate.

## Safety and accounting

- documentation source families reviewed: 2;
- prospective redesign drafts: 1;
- market/API requests: 0;
- source/data downloads: 0;
- Test Executor jobs: 0;
- Runner bundles: 0;
- VPS reads: 0;
- market rows or bodies opened: 0;
- protected evidence or outcomes opened: 0;
- returns, lag, correlation or PnL computed: 0;
- shared roadmap/governance/Strategy State/contamination/reusable registries changed: false;
- PR lifecycle changed: false.

## Next allowed action

Strategy Manager review only. The historical X1 atlas remains stopped. A future vendor path requires explicit written completeness proof plus `USER_COST_T3_GATE`; the prospective option requires a separate strategy/mechanism decision and task. No automatic continuation is authorized.
