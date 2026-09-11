# SC001-DATA-Q003 — Optimized OKX L2 Qualification Protocol v0.2

**Project:** BotMarketplace / BotMarketplace.store  
**Branch:** SCALPING RESEARCH / SC001  
**Date:** 2026-09-11  
**Status:** FROZEN BEFORE Q003 NETWORK RUN  
**Parent:** `docs/research/sc001-data-q002-results-v0.1.md`

## 1. Purpose

Qualify the exact OKX historical L2 acquisition path and raw schema without opening a broad historical data-mining surface or risking phone storage exhaustion.

Q003 is data engineering only. No strategy rules, P&L, edge ranking, parameter tuning, or venue selection by performance are permitted.

## 2. Why the earlier one-day-only idea is insufficient

A single L2 day is not enough to establish that:

- archive availability is continuous across years;
- the file schema is stable;
- daily compressed size is representative;
- snapshot/update semantics are replayable;
- sequence/checksum fields needed for reconstruction are present;
- instrument quantity units are interpreted correctly.

Therefore Q003 first performs metadata discovery on multiple predeclared dates and only then conditionally downloads one fixed sample.

## 3. Predeclared discovery dates

These dates are chosen before any archive sizes or strategy outcomes are inspected:

- `2023-04-15` — early period shortly after the public OKX L2 archive start;
- `2024-01-15` — intermediate historical point;
- `2025-01-15` — canonical cross-venue qualification day already used for Binance and Bybit;
- `2026-07-15` — recent pre-Q003 historical point.

They are engineering/schema checkpoints, not performance samples.

The sole primary raw-download date is fixed as:

> `2025-01-15 UTC`

Q003 must not switch to a smaller or more convenient day after observing file sizes.

## 4. Venue/instrument identity

Venue: OKX.  
Instrument type: `SWAP`.  
Instrument family: `BTC-USDT`.  
Target instrument: `BTC-USDT-SWAP`.

Q003 also records current public instrument metadata to identify fields such as contract value, tick size, lot size and minimum size. Current metadata must not be treated as proof of historical exchange filters.

## 5. Discovery path and trust boundary

OKX officially advertises high-resolution L2 historical order-book data from March 2023 onward on its Historical Market Data page.

The file-link discovery call used by Q003 is the public website backend path observed in the historical-data workflow:

`POST /priapi/v5/broker/public/trade-data/download-link`

with L2 module code `4`.

This endpoint is not treated as a stable documented public trading API. It is used only for credential-free archive discovery. Every returned download URL must pass host/scheme validation before any network follow-up.

Q003 must not authenticate or use private account endpoints.

## 6. Hard storage/network safety

Absolute limits:

- session network download cap: **2,000,000,000 bytes**;
- Q003 workspace cap: **2,000,000,000 bytes**;
- single raw archive cap: **512,000,000 bytes**;
- minimum free-storage reserve after any permitted write: **4,000,000,000 bytes**;
- metadata/JSON response cap: **4 MB**;
- HTML response cap: **2 MB**;
- decompressed schema-inspection cap: **32 MB**;
- no archive extraction to disk.

The raw L2 sample may be downloaded only when:

1. the canonical 2025-01-15 discovery returns exactly one unambiguous L2 file candidate for the scoped family;
2. the URL is HTTPS and belongs to an allowed `static.okx.*` host;
3. reported/HEAD size, when known, is <= 512 MB;
4. the remaining phone free space after the file would still exceed 4 GB;
5. the cumulative Q003 network count would remain below 2 GB.

If any condition fails, Q003 records `SAFE_SKIP` rather than guessing or downloading a different day.

If a streaming transfer exceeds the declared cap, the `.part` file must be deleted and the run must stop that download safely.

## 7. Schema/replay inspection

If the canonical L2 archive is downloaded, inspect it in-place without expanding it to disk.

Record:

- archive type and member names;
- SHA-256;
- compressed bytes;
- first bounded NDJSON/JSON records;
- JSON parse failures;
- timestamp field candidates and observed bounds;
- presence of `snapshot` / `update` actions;
- asks/bids structure;
- presence of `seqId`, `prevSeqId`, checksum or analogous sequencing fields;
- whether updates appear sufficient to reconstruct a deterministic local book.

Q003 does **not** assume that L2 automatically gives exact maker queue position. Price-level L2 can support spread/depth/imbalance and conservative taker execution research; exact maker fill probability may still require unavailable order-level queue data.

## 8. Cross-venue normalization warning

Do not directly compare raw `size` fields across Binance, Bybit and OKX without venue-specific contract/unit normalization.

For OKX derivatives, order-book size is expressed in contracts. Later research must normalize to comparable base/quote notional using instrument metadata and must not assume today's contract filters were historically unchanged.

## 9. What Q003 may decide

Allowed outcomes:

- `QUALIFIED_SAMPLE`: canonical L2 file discovered, safely downloaded, archive/schema inspection passes sufficiently for a later replay prototype;
- `QUALIFIED_METADATA_ONLY`: links/sizes are valid but canonical file is too large or ambiguous for the current phone safety envelope;
- `REDESIGN`: discovery endpoint/path no longer works, returned URLs fail trust checks, or raw schema is not replayable enough for the intended research.

No profitability status is available in Q003.

## 10. Next-stage gate

Only after Q003 may SC001 freeze a bulk calendar.

The first bulk stage should remain staged under 2 GB and should combine:

1. long Binance BTCUSDT 1m backbone;
2. predeclared Binance/Bybit trade-level windows;
3. only the minimum OKX L2 windows needed to test spread/depth/imbalance and execution sensitivity.

Do not download multi-year OKX L2 history by default.
