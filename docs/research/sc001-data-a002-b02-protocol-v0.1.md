# SC001-DATA-A002-B02 Protocol v0.1

Status: **FROZEN BEFORE DOWNLOAD**  
Batch: **2023-Q3**  
Purpose: acquire and integrity-qualify exactly five frozen Binance BTCUSDT USD-M `aggTrades` DEV-DISCOVERY days. Data only; no strategy features/P&L.

## Frozen inputs

Calendar SHA256:
`e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b`

Required prior stage:
`SC001-DATA-A002-PREFLIGHT` with overall PASS, 25/25 DEV days PASS, archive bodies not downloaded, and the same calendar SHA256.

Frozen B02 dates and identities:

| Date | Type | Event | Bytes | SHA256 |
|---|---|---|---:|---|
| 2023-07-12 | EVENT | CPI | 15,117,699 | `e19d5baa4d38b25d176ffb8e45e3e18812a1c19659d834827a0cd3ffdf60ab6e` |
| 2023-07-26 | EVENT | FOMC | 10,484,375 | `c7d43ced9bda96ed2d22eb9b783f9150df85917187a0b65e6b399e00a51426f4` |
| 2023-07-30 | ORDINARY_WEEKEND | — | 6,147,333 | `8de5561586e4e554f6dd53e5d3c4882468ac070d32e885152743253d1723ec67` |
| 2023-08-04 | EVENT | NFP | 7,865,401 | `edd1fb4a9fab76814bc3523cc8d022feea23d84340b3dd5fedbbf93e2a72bff8` |
| 2023-08-23 | ORDINARY_WEEKDAY | — | 13,977,351 | `d75b0426082a4be111138bb36db5e21b73916368245de379dd375834594dabe8` |

Expected total compressed bytes: **53,592,159**.

## Safety freeze

- network/session cap: 200,000,000 bytes;
- workspace cap: 200,000,000 bytes;
- per-file cap: 256,000,000 bytes;
- minimum free-space reserve: 4,000,000,000 bytes;
- maximum uncompressed ZIP member accepted: 2,000,000,000 bytes;
- no VALIDATION or FINAL access;
- no strategy features;
- no P&L.

## Identity checks before each download

For every frozen day the collector must:

1. read the live official `.CHECKSUM`;
2. require the live checksum to equal the frozen preflight SHA256;
3. issue HEAD to the exact official archive URL;
4. require exact URL identity and HTTP 200;
5. require live `Content-Length` to equal the frozen preflight size;
6. stop on any mismatch before admitting the file.

## Download and ZIP integrity

- download to `.part`;
- stream SHA256 while downloading;
- require exact frozen size and SHA256 before atomic rename;
- require one non-directory CSV member with exact expected filename;
- run ZIP CRC test;
- never extract the full CSV to disk.

## Row/schema validation

Expected columns:

`agg_trade_id, price, quantity, first_trade_id, last_trade_id, transact_time, is_buyer_maker`

Header may be present or absent but, if present, must match exactly after lowercase normalization.

Each data row must have exactly seven fields and satisfy:

- integer aggregate trade ID;
- finite positive price via Decimal;
- finite positive quantity via Decimal;
- integer first/last underlying trade IDs with first <= last;
- integer millisecond timestamp;
- maker flag exactly true/false.

## Mandatory per-day PASS gates

- rows > 0;
- invalid rows = 0;
- all rows inside the exact target UTC date;
- timestamps nondecreasing;
- aggregate trade IDs strictly contiguous (`+1`) with no duplicate/backward IDs;
- underlying trade ranges never overlap/go backwards;
- all 1,440 UTC minute buckets observed;
- both maker-flag states observed.

## Diagnostics, not FAIL gates

- same-millisecond adjacent aggTrades;
- gaps between adjacent underlying trade-ID ranges.

B01 demonstrated that underlying trade-ID gaps can exist while aggTrade IDs remain perfectly contiguous and all other integrity gates pass. Therefore these gaps remain recorded diagnostics only and must not be reinterpreted as missing aggTrades without separate raw-trades evidence.

## Cross-selected-day order diagnostic

Because the five selected days are not adjacent calendar dates, cross-day continuity is not required. However aggregate and underlying trade IDs must progress forward chronologically across the selected dates. Any reversal is REVIEW.

## Decision

`PASS` requires 5/5 days PASS and zero cross-selected-day order violations.

PASS qualifies B02 data for later DEV-DISCOVERY use only. It does **not** authorize strategy analysis. Under `sc001-a002-development-firewall-v0.1.md`, strategy work remains blocked until B03 completes and `SC001-E002-SCREEN-v0.1` is frozen.
