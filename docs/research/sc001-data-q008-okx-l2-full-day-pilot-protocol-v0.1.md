# SC001-DATA-Q008 — OKX L2 Full-Day Replay Pilot Protocol v0.1

Status: **FROZEN BEFORE FULL L2 DOWNLOAD**
Parent: `SC001-DATA-Q007-OKX-L2-Q1-PREFLIGHT`

## 1. Purpose

Q008 is a data-engineering/full-replay pilot. It validates one complete OKX historical 400-level L2 archive end-to-end before any multi-day L2 acquisition or midquote-performance test.

It calculates no E002 signal, no future midquote response, no execution P&L, and no strategy ranking.

## 2. Fixed pilot date

The sole pilot date is the chronologically first frozen Q1 date:

`2024-01-05`

This date is fixed before any full-day L2 strategy result is observed and must not be substituted based on archive behavior, market volatility, or later strategy performance.

Frozen Q007 identity:

- filename: `BTC-USDT-SWAP-L2orderbook-400lv-2024-01-05.tar.gz`
- compressed bytes: `500060536`
- venue/instrument: OKX `BTC-USDT-SWAP`

## 3. Safety limits

Hard decimal-byte limits:

- session network cap: **700,000,000 bytes**;
- Q008 workspace cap: **700,000,000 bytes**;
- single-file cap: **650,000,000 bytes**;
- minimum free-space reserve: **4,000,000,000 bytes**;
- no extracted L2 member written to disk;
- decompression/replay is streaming only.

These limits remain far below the project hard ceiling of 2 GB downloaded per run.

A partial `.part` archive may be retained after an interrupted transfer for resumable HTTP Range continuation. It must never be treated as qualified data.

## 4. Parent verification

Before download, Q008 must require the local Q007 report and verify:

- parent stage and PASS status;
- archive bodies were not already used for strategy/midquote analysis;
- exact pilot date/filename/URL;
- Q007 HEAD compressed size = `500060536`;
- Q2/Validation/Final remained unopened.

A fresh HEAD must still return the same trusted static OKX URL identity and exact compressed size.

## 5. Download integrity

Download the one fixed archive only.

Requirements:

- HTTPS host `static.okx.com`;
- exact filename path identity;
- compressed byte count exactly `500060536`;
- SHA-256 recorded;
- gzip/tar stream must be fully readable to EOF;
- no extraction of the uncompressed member to disk.

## 6. Full-stream semantic replay

The complete regular tar member must be parsed as newline-delimited JSON.

Required record keys:

- `instId`
- `action`
- `ts`
- `asks`
- `bids`

Required instrument: `BTC-USDT-SWAP`.

Allowed actions: `snapshot`, `update`.

Price levels must have shape `[price, size, orders]`, with valid positive price, nonnegative size, and nonnegative integer-like order count.

Replay rules are the same economic semantics already qualified in Q004R:

- snapshot replaces the book;
- update changes/deletes only supplied price levels;
- zero size deletes a price level;
- a later snapshot is an allowed resynchronization.

Q008 uses an in-memory price-level book only. It does not infer order-level queue priority.

## 7. Full-day integrity diagnostics

Record at minimum:

- regular tar member count/name/declared size;
- records parsed;
- snapshots/updates/resync snapshots;
- first/last timestamp and UTC rendering;
- UTC minute buckets observed;
- records outside target UTC day;
- invalid JSON;
- missing required keys;
- wrong instrument;
- invalid action;
- nonmonotonic timestamps;
- malformed levels;
- crossed-book states;
- empty-book states;
- zero-size deletions;
- zero-size with nonzero order count;
- delete-missing-level events;
- max reconstructed ask/bid levels;
- maximum inter-record timestamp gap.

## 8. UTC boundary gate

The pilot must test rather than assume the archive time boundary.

For a clean exact-UTC-day PASS:

- all parsed records must fall inside `[2024-01-05T00:00:00Z, 2024-01-06T00:00:00Z)`;
- all 1,440 UTC minute buckets must be represented;
- first and last timestamps must lie inside the target UTC day.

If the archive uses a different day boundary, the verdict is `BOUNDARY_REVIEW`, not a silent filter or strategy run. A separately frozen stitch redesign would then be required before performance analysis.

## 9. Replay PASS gates

`FULL_DAY_PASS` requires all of:

1. exact archive identity/size and complete stream read;
2. exactly one regular data member;
3. first valid action is `snapshot`;
4. at least one snapshot and one update;
5. invalid JSON = 0;
6. missing required keys = 0;
7. wrong instrument = 0;
8. invalid action = 0;
9. nonmonotonic timestamps = 0;
10. malformed levels = 0;
11. crossed-book states = 0;
12. empty-book states = 0;
13. zero-size/nonzero-orders anomalies = 0;
14. delete-missing-level events = 0;
15. exact UTC-day boundary gate passes.

If replay/schema passes but UTC boundary fails: `BOUNDARY_REVIEW`.
Any other integrity failure: `REVIEW`.

## 10. Hard research boundary

Q008 must output:

- `strategy_features_calculated = false`
- `midquote_response_calculated = false`
- `strategy_pnl_calculated = false`
- `execution_profitability_calculated = false`
- `q2_okx_accessed = false`
- `validation_or_final_accessed = false`

No spread distribution, E002 correlation, threshold, midquote alpha, or executable fill statistic is allowed in this pilot.

## 11. Next-stage rule

Only if Q008 returns `FULL_DAY_PASS` may the remaining four Q1 L2 archives be acquired/replayed in frozen sub-2GB batches. The five-day midquote falsification test must remain separately frozen before its response metrics are calculated.
