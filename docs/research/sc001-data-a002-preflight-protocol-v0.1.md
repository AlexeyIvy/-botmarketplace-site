# SC001-DATA-A002-PREFLIGHT — frozen protocol v0.1

## Purpose

Qualify availability and exact compressed size of Binance USD-M BTCUSDT daily `aggTrades` archives for the 25 already-frozen DEV acquisition dates before downloading any archive body.

This is a data-engineering preflight only. Strategy/P&L is forbidden.

## Frozen input

The engine must load:

`/storage/emulated/0/Download/SC001_MICRO_CALENDAR_V0_1/sc001_micro_calendar_manifest_v0_1.json`

and require SHA256:

`e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b`

Only rows with `split == DEV` are permitted. Exactly 25 unique dates must be present.

## Data source

Official Binance public-data daily USD-M futures aggTrades archives:

`https://data.binance.vision/data/futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-YYYY-MM-DD.zip`

Each archive must also have its official adjacent `.CHECKSUM` file.

## Preflight behavior

For every frozen DEV date:

1. Download only the small `.CHECKSUM` response and resolve the exact 64-hex SHA256 for the expected archive filename.
2. Probe archive metadata with `HEAD`.
3. If `HEAD` does not yield a usable `Content-Length`, fall back to `Range: bytes=0-0`.
4. If Range is ignored and the server returns a full-body response, close without reading the body.
5. Record final URL, HTTP status, Content-Length/Content-Range, ETag/Last-Modified when available, and expected SHA256.

No ZIP archive body may be downloaded in this stage.

## Safety — frozen before archive sizes are seen

- preflight session network cap: 50,000,000 bytes
- preflight workspace cap: 50,000,000 bytes
- per small response cap: 1,000,000 bytes
- minimum free-storage reserve: 4,000,000,000 bytes
- later single-archive cap: 256,000,000 bytes
- later quarter-batch cap: 1,000,000,000 bytes
- later acquisition session cap: 2,000,000,000 bytes

Caps must not be raised after observing archive sizes. A cap violation means redesign, not override.

## Frozen batching rule

If preflight passes, later acquisition is grouped by calendar quarter. DEV must produce exactly five batches:

- 2023-Q2
- 2023-Q3
- 2023-Q4
- 2024-Q1
- 2024-Q2

Each quarter must contain exactly five frozen dates from the calendar design.

## PASS gate

Overall PASS requires:

- 25 / 25 DEV dates available;
- 25 / 25 official checksum files resolve uniquely;
- exact compressed size known for every archive;
- every archive size > 0 and <= 256 MB;
- five quarter batches, each with exactly five dates;
- every quarter batch <= 1.0 GB;
- no archive body downloaded;
- all preflight safety limits respected.

Anything else is `REVIEW` or `ERROR`.

## Forbidden interpretation

PASS does not mean the aggTrades content is valid yet. It only authorizes staged download and later content validation. PASS does not authorize strategy/P&L, opening VALIDATION/FINAL, replacing aggTrades with raw trades, or inferring spread/depth/queue information.
