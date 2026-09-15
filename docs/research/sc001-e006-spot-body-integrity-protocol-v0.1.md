# SC001-E006 — SPOT Body Download / Integrity / UTC Reconstruction Protocol v0.1

Date: 2026-09-15  
Status: **FROZEN DATA-ONLY PROTOCOL — NO E006 ALPHA AUTHORIZED**  
Parent plan: `docs/research/sc001-e006-same-venue-spot-perp-basis-dislocation-research-plan-v0.2.md`

## 1. Purpose

Qualify the exact OKX `BTC-USDT` SPOT trade bodies required for E006 DEV-DISCOVERY data engineering, without calculating spot/perpetual basis, convergence, returns, P&L, or any strategy metric.

This stage is data engineering only.

## 2. Prerequisite

The authoritative metadata manifest is:

`~/sc001_data/SC001_E006_SPOT_FEASIBILITY/sc001_e006_spot_metadata_preflight.json`

It must have exact status:

`E006_SPOT_METADATA_PREFLIGHT_PASS`

The downloader may use only the 21 archive identities already recorded there.

## 3. Frozen source scope

Instrument: OKX `BTC-USDT` SPOT.  
Historical module: trade history (`module=1`).

Permitted archive labels only:

- 2024-03-01 through 2024-03-21 inclusive.

Performance role:

- 2024-03-01..20: future E006 DEV-DISCOVERY candidate days;
- 2024-03-21: D+1 boundary-neighbor only, permanently excluded from E006 performance.

Forbidden:

- labels 2024-03-22 onward at this stage;
- Q2;
- formal Validation;
- Final;
- L2.

No network metadata rediscovery may silently substitute a different archive identity during body download. A changed/missing identity produces REVIEW/FAIL.

## 4. Download identity rules

For every permitted label, require before GET:

- exact expected filename `BTC-USDT-trades-YYYY-MM-DD.zip`;
- HTTPS;
- host exactly `static.okx.com`;
- exact Content-Length from the frozen metadata preflight;
- total expected body size equal to the frozen manifest total.

Downloads may resume from `.part` files using HTTP Range only when the server response is compatible with the expected byte range. If resume semantics are ambiguous, restart that file safely rather than append blindly.

A completed local file is reusable only when its exact byte size matches the frozen expected size and all integrity checks PASS.

## 5. Archive integrity checks

For each completed ZIP:

1. exact byte size matches metadata preflight;
2. SHA256 is computed and recorded;
3. ZIP CRC passes;
4. exactly one non-directory CSV member exists;
5. exact header is:
   `instrument_name,trade_id,side,price,size,created_time`;
6. all nonempty rows have exactly six fields;
7. instrument is exactly `BTC-USDT` on every admitted source row;
8. side is `buy` or `sell`;
9. price and size are finite and strictly positive;
10. timestamp parses with the qualified epoch-scale resolver;
11. source timestamps are nondecreasing;
12. source trade IDs are strictly increasing;
13. first/last timestamp, row count, buy/sell counts, duplicate-timestamp count and trade-ID gap count are recorded.

Trade-ID gaps are diagnostic unless duplicate/backward ordering occurs.

No row may be removed because of price movement, apparent dislocation, volatility, return, or any strategy-related value.

## 6. Qualified UTC reconstruction

Use the same Q006R-style source semantics already qualified in SC001.

For each target UTC day `D` in 2024-03-01..20:

- read archive label `D`;
- read archive label `D+1`;
- admit only `BTC-USDT` rows with `created_time` in
  `[D 00:00:00.000 UTC, D+1 00:00:00.000 UTC)`.

Target-day PASS requires:

1. admitted row count > 0;
2. timestamps nondecreasing after D then D+1 stitching;
3. trade IDs have zero duplicate/backward count;
4. both buy and sell are present;
5. all 1,440 UTC minute buckets contain at least one admitted trade;
6. all admitted timestamps lie inside the target interval.

Record, but do not tune on:

- number of occupied UTC seconds;
- longest inter-trade timestamp gap;
- first/last admitted timestamp;
- trade-ID gap count.

No price comparison with SWAP is allowed in this stage.

## 7. Storage and failure behavior

Workspace:

`~/sc001_data/SC001_E006_SPOT_FEASIBILITY/`

Archive directory:

`archives/`

Before downloading, require free disk >= frozen expected total bytes + 20 GiB reserve.

Writes must be resumable/atomic where practical. A malformed archive, hash/size mismatch, schema failure, ordering failure or UTC reconstruction failure yields terminal REVIEW/FAIL. Do not substitute another date.

## 8. Required output

Write machine-readable report:

`sc001_e006_spot_body_integrity_report.json`

containing at least:

- stage/version/status;
- exact metadata-preflight identity;
- per-archive filename, bytes, SHA256 and source diagnostics;
- per-target-day UTC reconstruction diagnostics;
- total downloaded/reused bytes;
- disk facts;
- explicit firewalls.

Terminal PASS token:

`E006_SPOT_BODY_INTEGRITY_PASS`

Any failure/review token keeps E006 alpha closed.

## 9. Explicit firewalls

The report must state:

- `basis_calculated = false`;
- `returns_calculated = false`;
- `pnl_calculated = false`;
- `swap_prices_compared = false`;
- `l2_accessed = false`;
- `q2_accessed = false`;
- `validation_or_final_accessed = false`.

## 10. Promotion rule

A body-integrity PASS does **not** authorize E006 alpha.

After PASS, the next allowed stage is a separate no-alpha causal SPOT/SWAP synchronization-feasibility audit. Only after complete data qualification may the E006 financial protocol be frozen and later tested.
