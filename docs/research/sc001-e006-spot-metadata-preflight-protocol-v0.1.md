# SC001-E006 — SPOT Metadata-Only Preflight Protocol v0.1

Date: 2026-09-15  
Status: **FROZEN DATA-ONLY PREFLIGHT — NO MARKET-DATA BODY / NO ALPHA**  
Parent plan: `sc001-e006-same-venue-spot-perp-basis-dislocation-research-plan-v0.2.md`

## Scope

Instrument: OKX `BTC-USDT` SPOT.  
Historical module: trade history (`module=1`).

Required archive labels:

`2024-03-01` through `2024-03-21` inclusive.

The March-21 label is boundary-neighbor only, required to reconstruct Discovery UTC day March 20, and is permanently excluded from E006 performance inference.

## Allowed actions

For each required label:

- query only the public historical metadata endpoint;
- resolve the exact expected filename `BTC-USDT-trades-YYYY-MM-DD.zip`;
- require exactly one trusted `https://static.okx.com/.../<expected filename>` URL;
- perform HEAD only;
- require HTTP 200 and exact basename preservation;
- record `Content-Length`;
- compute total expected bytes;
- check local free disk.

No ZIP/CSV body may be downloaded or opened under this preflight.

## PASS criteria

All 21 labels must resolve uniquely.  
Every trusted URL must use `static.okx.com`.  
Every HEAD must return a positive content length.  
Aggregate expected bytes must fit within current free disk while preserving at least 20 GiB free reserve.

Terminal status:

- `E006_SPOT_METADATA_PREFLIGHT_PASS`, or
- `E006_SPOT_METADATA_PREFLIGHT_REVIEW`.

## Firewalls

The report must explicitly record:

- `market_data_body_downloaded = false`;
- `basis_calculated = false`;
- `returns_calculated = false`;
- `pnl_calculated = false`;
- `l2_accessed = false`;
- `q2_accessed = false`;
- `validation_or_final_accessed = false`.

A PASS authorizes only design/freeze of a subsequent SPOT body-download/integrity stage. It does not authorize E006 alpha.
