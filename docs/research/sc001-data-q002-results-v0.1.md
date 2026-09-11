# SC001-DATA-Q002 — Validation + OKX Probe Results v0.1

**Project:** BotMarketplace  
**Branch:** SCALPING RESEARCH / SC001  
**Stage:** SC001-DATA-Q002  
**Date:** 2026-09-11  
**Status:** COMPLETE / QUALIFICATION PASS WITH TWO FOLLOW-UP FIXES  
**Strategy/P&L calculated:** NO  
**Bulk OKX L2 downloaded:** NO

## 1. Independence boundary

SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. No result in this data-acquisition stage changes any frozen rule, inception, forward clock, or interpretation in those branches.

## 2. Q002 outcome

Q002 successfully revalidated the existing Q001 trade-level samples and established that OKX public market-data endpoints and its official historical-data page are reachable from the user's Android workflow.

### Binance USD-M BTCUSDT aggTrades — PASS

Fixed day: 2025-01-15 UTC.

- compressed file: 21,271,119 bytes;
- data rows: 1,681,098;
- correct timestamp field: `transact_time` (column 6 / index 5);
- first timestamp: 1736899205109 ms;
- last timestamp: 1736985599991 ms;
- invalid rows: 0;
- out-of-day rows: 0;
- non-monotonic timestamps: 0;
- agg trade IDs strictly increasing;
- agg trade ID gaps: 0;
- same-millisecond adjacent events are common and valid.

This corrects the Q001 validator mistake that treated `agg_trade_id` as if it were a timestamp. The underlying archive itself was valid; only the first-stage validator semantics were wrong.

### Bybit BTCUSDT tick trades — PASS

Fixed day: 2025-01-15 UTC.

- compressed file: 74,892,440 bytes;
- data rows: 2,049,441;
- invalid rows: 0;
- invalid side rows: 0;
- out-of-day rows: 0;
- non-monotonic timestamps: 0;
- time range spans effectively the complete UTC day;
- repeated identical sub-second timestamps are common and valid.

The file is suitable as a trade-level microstructure source for frozen research windows.

## 3. OKX qualification

Both `https://www.okx.com` and `https://us.okx.com` responded successfully to documented market endpoints.

Confirmed:

- historical 1m candles around the fixed date: HTTP 200 / code 0;
- recent historical trades schema: HTTP 200 / code 0;
- current 5-level order book schema: HTTP 200 / code 0;
- official historical-data pages are reachable and explicitly expose trade-history and order-book download sections;
- discovered static OKX host families were recorded but no bulk link was automatically followed.

The guessed `market-data-history` module names used in Q002 returned code 51000 and are therefore not accepted as production retrieval parameters. This failure does not invalidate OKX historical data availability because the official historical-data page and separate documented market endpoints are working.

## 4. Safety audit

Frozen Q002 limits:

- session network cap: 2,000,000,000 bytes;
- workspace cap: 2,000,000,000 bytes;
- per-response cap: 512,000,000 bytes;
- minimum free-storage reserve: 4,000,000,000 bytes.

Observed Q002 network usage was only 249,831 bytes. No bulk OKX L2 archive was followed or downloaded.

### Minor accounting defect

The reported `workspace_bytes_end = 0` was measured before the final tiny JSON/Markdown outputs were written. This is not a storage-risk event and did not weaken the network safety guard, but the future bulk collector must compute final workspace size after all output writes and enforce the cap continuously after every successful file move.

## 5. Research interpretation

We now have three distinct usable data roles:

1. **Binance 1m:** long low-storage backbone for multi-year signal/context work.
2. **Binance aggTrades + Bybit tick trades:** trade-level microstructure for predeclared windows.
3. **OKX historical L2:** potentially the strongest source for real spread/depth/imbalance and execution modeling, but its actual file size/schema must be qualified with one fixed-day sample before any wider pull.

Do not download years of tick/L2 data merely because they are available. That would create unnecessary storage pressure and a large retrospective search surface.

## 6. Next stage decision

Open **SC001-DATA-Q003** before any bulk calendar.

Q003 must:

- discover the exact official OKX historical trade/L2 download mechanism without scraping arbitrary mirrors;
- predeclare one fixed sample day before seeing file size/content diagnostics;
- use HEAD/metadata first where available;
- follow at most one OKX L2 sample file;
- retain the 2.0 GB session cap and 4.0 GB free-space reserve;
- use a stricter per-file cap for the first L2 sample (recommended <= 512 MB);
- never auto-follow a second large archive in the same run;
- record compressed and inspected schema sizes;
- write checkpoints atomically and support safe reruns;
- perform no strategy/P&L calculation.

Only after Q003 establishes real L2 size and schema may a staged bulk calendar be frozen.

## 7. Proposed staged bulk architecture after Q003

Subject to Q003 PASS:

- download the multi-year Binance 1m backbone first because it is inexpensive and auditable;
- freeze microstructure windows by calendar before looking at strategy outcomes;
- collect Binance aggTrades / Bybit trades only for those frozen windows;
- collect OKX L2 only for the same frozen windows, preferably in smaller independent batches comfortably below 2 GB;
- keep venue datasets separate and never choose the venue retrospectively by prettier P&L.

No live trading is authorized.
