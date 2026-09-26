# SC001 Current Roadmap and Stop Rules v5.105

Date: 2026-09-26  
Status: **B15-P1 collector operational freeze preserved / Stage E source-only protocol prepared / W0 pipeline smoke implementation prepared**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.104.md`

## Frozen collector remains unchanged

Formal collector state remains:

`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

No collector code, cadence, service, authorization, normalization, storage or firewall semantics are changed by Stage E.

The collector remains the live input-producing instrument and continues accumulating prospective non-price evidence.

## Stage E research objective

Next research phase is:

`B15-P1 SOURCE-ONLY OPPORTUNITY-RATE ANALYSIS`

Binding protocol:

`docs/research/sc001-b15-p1-source-only-opportunity-rate-analysis-protocol-v0.1.md`

Stage E remains pre-price. It may analyze only transferability-state chronology, integrity, route-state episodes, outage clusters and fee-source completeness.

Still forbidden:
- cross-venue prices;
- spreads;
- returns;
- PnL;
- retrospective price reaction around collected events;
- price-driven asset/network selection.

## Statistical unit and effective-state rule

Primary inference unit is:

`VENUE-LEVEL EFFECTIVE-TRANSFERABILITY OUTAGE CLUSTER`

15-second polls, route rows, assets and networks are not independent samples.

Per asset and direction, effective transferability is:
- ACTIVE if at least one frozen common representation is ACTIVE;
- BLOCKED only if all frozen common representations are observed blocked;
- UNKNOWN otherwise.

This prevents one disabled chain from being treated as venue segmentation when another frozen common route remains open.

Clusters use a frozen conservative 600-second join window plus interval overlap and shared blocker component. Clustering is transitive.

## Frozen observation windows

- W0: current partial-day pipeline smoke only; no opportunity-rate inference.
- W1: 7 complete UTC days; first operational source checkpoint.
- W2: 30 complete UTC days; first formal source-only opportunity-rate checkpoint.
- W3: 90 complete UTC days if W2 remains sparse (<10 independent clusters), unless a separately reviewed scheduled clean event justifies a prospective event-specific protocol.

At W2, descriptive categories are:
- >=10 clusters: EVENT_RICH;
- 1..9 clusters: EVENT_SPARSE;
- 0 clusters: ZERO_EVENT_30D.

These are source-sample categories, not profitability thresholds and do not authorize prices automatically.

## Data-quality gate

Formal Stage E inference requires:
- daily manifest/hash integrity;
- poll-chain integrity;
- poll coverage >=99%;
- both-venue-valid fraction >=99%;
- source gaps excluded from usable exposure;
- price/PnL firewalls closed.

## W0 implementation

Separate read-only implementation:

`research/sc001/sc001_b15p1_stage_e_pipeline_smoke_v0_1.py`

SHA256:

`9cdbe1e33f6c3d9ad90f11c494690adadd0ec9d0fab05ec32b59c73db7bdb69e`

Contract:

`docs/research/sc001-b15-p1-stage-e-pipeline-smoke-contract-v0.1.json`

Offline self-test spec:

`docs/research/sc001-b15-p1-stage-e-pipeline-smoke-offline-selftest-spec-v0.1.json`

The implementation has been locally syntax-checked and synthetic-self-tested before Runner packaging. Official evidence still requires an immutable sealed Runner self-test bundle.

W0 real-data smoke, after official offline self-test PASS, is allowed to read a snapshot from the Runner `sc001_data` allowlisted input only. It must not mutate the collector or call exchanges.

## Stop rules

- Do not change the healthy collector for Stage E convenience.
- Do not run Stage E analysis against price data.
- Do not infer opportunity rate from W0 partial-day smoke.
- Do not use route rows/ticks as IID sample size.
- Do not promote assets/networks from event frequency into a price-test subset.
- Do not open Stage F price/headroom research without a separate review/authorization after Stage E evidence.

## Next state

`SEAL_STAGE_E_W0_PIPELINE_SMOKE_OFFLINE_SELFTEST_BUNDLE`
