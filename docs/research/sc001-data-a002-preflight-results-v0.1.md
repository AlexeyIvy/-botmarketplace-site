# SC001-DATA-A002-PREFLIGHT — Results v0.1

Status: **PASS**

## Purpose
Preflight qualification of the 25 frozen DEV Binance USD-M BTCUSDT daily `aggTrades` archives before any archive body download, feature engineering, or P&L calculation.

## Frozen provenance
- Split: DEV only.
- Frozen calendar SHA256: `e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b`.
- Expected DEV dates: 25.
- Archive bodies downloaded: **NO**.
- Strategy/P&L calculated: **NO**.

## Qualification result
All 25/25 frozen DEV dates passed metadata/checksum preflight.

For every date:
- official daily `aggTrades` URL resolved;
- official `.CHECKSUM` resolved;
- a unique SHA-256 was parsed;
- HEAD returned HTTP 200;
- content length was present;
- final URL remained on the expected Binance data host;
- each archive was below the frozen 256 MB single-file cap.

Total expected compressed size for all 25 DEV archives: **431,006,933 bytes**.

## Frozen quarter batches
- 2023-Q2 — 5 files — 91,819,076 bytes — PASS.
- 2023-Q3 — 5 files — 53,592,159 bytes — PASS.
- 2023-Q4 — 5 files — 91,449,749 bytes — PASS.
- 2024-Q1 — 5 files — 87,855,109 bytes — PASS.
- 2024-Q2 — 5 files — 106,290,840 bytes — PASS.

Every batch is well below the frozen 1 GB batch cap; the total DEV compressed size is below the 2 GB session cap. This does **not** authorize downloading all batches in one run; the frozen staged design remains one quarter at a time.

## Technical observations
Two 2023 files reported `binary/octet-stream` rather than `application/zip` in HEAD metadata. This is not a failure because filename, HTTP status, content length and official checksum all resolve correctly; the actual ZIP body and checksum will be validated after download.

Some older 2023 archive objects report 2026 `Last-Modified` timestamps. This is treated as object re-publication/rewrite metadata, not proof of changed historical content. The current official SHA-256 is authoritative for the staged download. We will validate the downloaded bytes against that frozen checksum.

## Safety
- Preflight network bytes read: 2,475.
- Preflight workspace: 41,302 bytes.
- Minimum free-storage reserve: 4 GB.
- Future single archive cap: 256 MB.
- Future quarter batch cap: 1 GB.
- Future session cap: 2 GB.

## Decision
**PASS.** The preflight authorizes only staged acquisition of the frozen DEV `aggTrades` dates, beginning with `2023-Q2` (5 dates).

The next acquisition stage must remain data-only and must validate downloaded SHA-256, ZIP integrity, schema, timestamp/day boundaries, aggregate-trade ID monotonicity/duplicates and structural consistency. No strategy features, signal search, P&L, VALIDATION or FINAL access are authorized yet.
