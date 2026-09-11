# SC001-DATA-Q004 — OKX L2 Range/Schema Qualification v0.1

Status: PRE-TEST / DATA-ONLY FREEZE

## Purpose
Qualify the actual OKX BTC-USDT-SWAP historical L2 archive format across multiple epochs without downloading full daily archives. This stage does not calculate strategy P&L and does not authorize live trading.

## Inputs
Use only the previously frozen Q003 output at `/storage/emulated/0/Download/SC001_DATA_Q003/sc001_data_q003_report.json`.

Frozen dates:
- 2023-04-15
- 2024-01-15
- 2025-01-15
- 2026-07-15

The Q003 report must provide one trusted `static.okx.com` L2 archive URL per date.

## Network method
For each frozen archive request only the first 8 MiB using HTTP `Range: bytes=0-8388607`.

A sample is accepted only if:
1. HTTP status is 206;
2. `Content-Range` starts at byte 0;
3. final host is exactly `static.okx.com`;
4. bytes actually read do not exceed the frozen per-sample cap.

If the server ignores Range and returns HTTP 200, close the response immediately and mark the sample `RANGE_UNSUPPORTED`; do not read or save the full body.

## Inspection
- Do not save partial archive bodies to disk.
- Decompress only in memory.
- Maximum decompressed prefix per sample: 64 MiB.
- Parse tar headers from the decompressed prefix and inspect only available member prefixes.
- Record member names/types/declared sizes.
- For text/CSV-like member prefixes, record detected delimiter/header and a small row preview.
- Compare detected schema/header across epochs.

This is schema/replay qualification only. It does not prove full-day completeness, exact maker queue position, or profitability.

## Safety gates
- Emergency hard session network cap: 2,000,000,000 bytes.
- Q004 normal planned network budget: <= 40 MiB plus small metadata overhead.
- Per Range response body: <= 8 MiB.
- In-memory decompressed prefix: <= 64 MiB per sample.
- Q004 workspace hard cap: 2,000,000,000 bytes.
- Minimum free-storage reserve: 4,000,000,000 bytes.
- No full OKX L2 archive download.
- No archive extraction to disk.

## Outputs
Folder: `/storage/emulated/0/Download/SC001_DATA_Q004/`

- `sc001_data_q004_report.json`
- `sc001_data_q004_summary.md`
- `sc001_data_q004_schema_compare.json`
- `sc001_data_q004_final_safety.json`

## Decision rule
`SCHEMA_COMPATIBLE_SCREEN` only if at least three frozen epochs, including 2025-01-15 and 2026-07-15, support Range sampling and expose a coherent parseable L2 text schema with no unexplained incompatible header break.

Otherwise use `NEEDS_REVIEW`; do not escalate to bulk L2 download until the incompatibility is understood.

## Research boundary
Economic/news-event calendars remain a separate frozen diagnostic layer. Q004 must not use events or price outcomes to choose dates or schema samples.
