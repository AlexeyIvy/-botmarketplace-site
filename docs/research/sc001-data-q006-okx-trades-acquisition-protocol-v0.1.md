# SC001-DATA-Q006 — OKX Q1 Tick-Trade Acquisition / Schema Qualification Protocol v0.1

Status: **FROZEN BEFORE ARCHIVE-BODY DOWNLOAD**  
Parent: `SC001-DATA-Q005R` PASS  
Purpose: acquire and qualify exactly five previously frozen OKX `BTC-USDT-SWAP` historical trade archives, without calculating E002 features, returns, P&L, or opening later holdouts.

## 1. Frozen source days

Exactly:
- 2024-01-05 — NFP
- 2024-01-14 — ordinary weekend
- 2024-01-31 — FOMC
- 2024-02-12 — ordinary weekday
- 2024-02-13 — CPI

No substitutions.

## 2. Frozen remote identities

Use only Q005R-qualified exact-date URLs and sizes:
- 2024-01-05 — 7,528,396 bytes
- 2024-01-14 — 2,619,932 bytes
- 2024-01-31 — 4,921,193 bytes
- 2024-02-12 — 6,500,745 bytes
- 2024-02-13 — 8,510,138 bytes

Expected total compressed bytes: **30,080,404**.

Before each GET, re-check HEAD identity and exact size. Abort on mismatch; do not substitute another file.

## 3. Safety

- session network cap: 100,000,000 bytes
- workspace cap: 100,000,000 bytes
- per-file cap: 25,000,000 bytes
- minimum free-space reserve: 4,000,000,000 bytes
- no extraction to disk
- raw ZIPs retained

## 4. Data-only boundary

Forbidden in Q006:
- E002 TFI calculation;
- future-return labels;
- Spearman/deciles;
- strategy thresholds;
- spread/L2/fee/P&L calculations;
- 2024-Q2 OKX trade acquisition;
- formal Validation or Final.

## 5. Archive/schema qualification

For each file:
- exact compressed byte count;
- local SHA-256 recorded;
- ZIP CRC passes;
- data member inventory recorded;
- member must be regular UTF-8 text/CSV-like content;
- header and first bounded rows recorded for schema discovery;
- no strategy feature may be derived from those rows.

The engine may identify candidate column names for timestamp, price, size, side and trade ID from the header, but schema interpretation is engineering metadata only.

## 6. Full-stream integrity when schema is unambiguous

If timestamp, price, size and side columns can be resolved from the archive header without value-based optimization, stream the full member and record:
- rows > 0;
- invalid row count;
- timestamps monotonic nondecreasing;
- timestamps inside target UTC day;
- first/last timestamp;
- positive finite price and size;
- side values and counts;
- minute buckets observed;
- trade-ID diagnostics if a trade-ID column exists.

Trade-ID continuity is diagnostic unless the historical file semantics independently establish strict continuity.

If required columns cannot be resolved, mark that day `SCHEMA_REVIEW`; retain the raw ZIP and stop before signal calculation.

## 7. PASS gate

`PASS` requires all five remote/archive identities to pass and all five files to expose an unambiguous streamable trade schema with zero malformed rows, zero timestamp reversals, and zero out-of-day rows.

If archive integrity passes but one or more schemas need engineering interpretation, use `SCHEMA_REVIEW`, not FAIL.

## 8. Next step

Only after Q006 PASS may a separate same-venue replication experiment be frozen and run. It must preserve the E002 5s lookback/grid/horizon/direction and must not use 2024-Q2 OKX data for tuning.
