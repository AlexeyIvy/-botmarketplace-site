# SC001-E002 OKX Q1 Funding Source Amendment v0.1

Date: 2026-09-15  
Status: **SOURCE-TRANSPORT AMENDMENT BEFORE ANY EXECUTION-ECONOMICS OUTPUT**

Parent protocol: `docs/research/sc001-e002-okx-q1-taker-economics-protocol-v0.2.md`

## 1. Trigger

The first execution-metadata preflight used the current public REST endpoint:

`GET /api/v5/public/funding-rate-history`

for the frozen 2024-Q1 dates. In September 2026 that endpoint returned zero records for 2024-01-14 and the preflight failed closed before any execution-economics calculation.

No alpha, execution P&L, net edge, promotion metric, Q2, formal Validation or Final result was calculated or observed before this amendment.

## 2. Cause and permitted source repair

The frozen economics protocol v0.2 already permits either the official OKX public funding-rate history endpoint **or the OKX historical funding-rate dataset**.

OKX now exposes old funding data through its historical market-data bulk archive endpoint:

`GET /api/v5/public/market-data-history`

Funding is module `3` (`FundingRate`) and historical funding files are monthly. The legacy `/public/funding-rate-history` endpoint is not suitable for retrieving these 2024 records in 2026.

This amendment changes only the retrieval transport/source within the already-permitted official OKX historical funding dataset. It does **not** alter the funding cost rule or any financial/statistical parameter.

## 3. Frozen archive query

For this Q1 preflight only:

- endpoint: `/api/v5/public/market-data-history`;
- module: `3` (funding rate);
- `instType=SWAP`;
- `instFamilyList=BTC-USDT`;
- `dateAggrType=monthly`;
- query window covers only the January/February 2024 monthly funding archives required to recover the four already-open frozen dates;
- archive URLs must be HTTPS on `static.okx.com` and URL basename must equal the returned filename;
- downloaded ZIP files are retained with SHA256 and size metadata.

The implementation filters archive rows to `BTC-USDT-SWAP` only and then to the four frozen UTC dates:

- 2024-01-14;
- 2024-01-31;
- 2024-02-12;
- 2024-02-13.

No Q2 archive is requested or inspected.

## 4. Bulk funding row semantics

The OKX bulk funding CSV uses the form:

`instrument_name,funding_rate,funding_time`

The preflight must:

- require the target instrument exactly;
- parse the published funding rate as a finite decimal;
- parse the funding timestamp as Unix milliseconds;
- deduplicate identical funding timestamps;
- require exactly three records on each frozen UTC day;
- require UTC hours `[0, 8, 16]` for each of the four frozen days;
- fail closed on any mismatch.

The bulk archive's published historical `funding_rate` is the historical assessment rate used by the economics ledger. The conservative primary rule from protocol v0.2 remains unchanged: if a five-second position spans a historical funding timestamp, charge `abs(funding_rate)` as a cost regardless of direction.

## 5. Unchanged economics rules

This amendment does not change:

- TFI signal definition;
- q95 causal threshold and 720-observation lookback;
- four Q1 dates;
- 5-second holding horizon;
- 100/250/500 ms latency grid;
- 0/25/50% depth-haircut grid;
- 1k/10k/50k notional grid;
- one-position/non-overlap logic;
- taker-only execution;
- visible-book VWAP;
- Lv1 0.05% taker fee per fill;
- conservative funding treatment;
- Base / Stress A / Stress B gates;
- no-rescue rule;
- Q2 / Validation / Final firewall.

## 6. Implementation

Use:

`research/sc001/sc001_e002_okx_q1_execution_metadata_preflight_v0_2.py`

The failed v0.1 preflight remains part of the audit trail. The v0.2 preflight must complete before the execution-economics implementation is frozen or run.
