# SC001-E008 — Discovery Full Semantic Integrity Protocol v1.0

Date: 2026-09-16  
Status: **FROZEN DATA-QUALITY GATE — NO MAKER ALPHA / NO P&L**

Prerequisites:
- promotional Discovery chronology already frozen;
- `E008_DISCOVERY_METADATA_PREFLIGHT_PASS`;
- staged acquisition completed for trades + L2 A/B/C/D;
- exact `E008_DISCOVERY_ACQUISITION_VERIFY_PASS` with 24 verified local files.

## 1. Purpose

Before any E008 maker Discovery simulation, prove that every frozen promotional Discovery day has full-day, deterministic, semantically valid trade and L2 data.

This stage is data qualification only. It must not place hypothetical maker orders or calculate fills, spread capture, markouts, fees, inventory P&L or profitability.

## 2. Frozen Discovery days

Exactly:
- 2024-01-06
- 2024-01-13
- 2024-01-19
- 2024-01-24
- 2024-02-06
- 2024-02-11
- 2024-02-21
- 2024-02-23

No date substitution is allowed after body access.

Confirmation dates/bodies remain closed.

## 3. Input identity

All inputs must come only from:

`~/sc001_data/SC001_E008_DISCOVERY_DATA/`

and must be the exact files recorded in the successful staged-acquisition verify report:

`reports/sc001_e008_discovery_acquisition_verify.json`.

The runner must recompute local SHA256 before semantic use and record it in the per-day qualification artifact.

## 4. Trade UTC-day reconstruction

For each target day D, reconstruct UTC `[D, D+1)` from the frozen exact archive D plus D+1 neighbor archive, using the same historical OKX boundary rule already established in Q006R.

Expected row schema:

`instrument_name, trade_id, side, price, size, created_time`

Required trade conditions per day:
- ZIP CRC passes;
- one non-directory CSV member per archive;
- exact normalized header;
- every admitted row is `BTC-USDT-SWAP`;
- side is buy/sell;
- price and size are finite and strictly positive;
- target-day timestamps are nondecreasing;
- target-day trade IDs are strictly increasing with no duplicate/backward IDs;
- trade-ID gap count = 0;
- both buy and sell rows are nonzero;
- exactly 1440/1440 target UTC minute buckets represented;
- first and last admitted timestamps lie inside target UTC day.

No trade price response, return or strategy feature may be calculated.

## 5. L2 semantic replay

Replay the exact-date `BTC-USDT-SWAP-L2orderbook-400lv-D.tar.gz` causally in source order.

Required record keys:
- `instId`
- `action`
- `ts`
- `asks`
- `bids`

Each L2 level must be exactly `[price, aggregate_size, aggregate_order_count]` with:
- finite positive price;
- finite nonnegative size;
- nonnegative integer aggregate order count;
- zero-size deletion requires zero aggregate order count.

Replay rules:
- exactly one regular tar member;
- first action must be `snapshot`;
- later `snapshot` is a valid full resync and clears reconstructed book;
- `update` mutates levels causally;
- zero-size level removes the price;
- source timestamps must be nondecreasing;
- all records must be `BTC-USDT-SWAP`;
- all record timestamps must lie within the target UTC day;
- exactly 1440/1440 UTC minute buckets represented;
- no malformed JSON/schema/levels;
- no delete-missing-level anomaly;
- no crossed or empty reconstructed book state after a valid record;
- best bid and best ask must have positive aggregate size and positive aggregate order count.

## 6. Stale-gap treatment

Inter-record L2 gaps greater than 5,000 ms are recorded diagnostically:
- count;
- maximum gap;
- timestamps of first/last such gap may be retained in machine-readable output.

A >5 s gap does not by itself fail semantic archive integrity because E008 already has a separately frozen fail-closed stale-latch rule:
- age >5 s => stale latch;
- no quoting/queue/fill credit while latched;
- only a later full snapshot restores trusted state.

This semantic stage must not reinterpret or weaken that rule.

## 7. Resumability

A per-day checkpoint may be reused only when:
- protocol/stage version matches exactly;
- current L2 SHA256 equals checkpoint L2 SHA256;
- current exact-trade SHA256 equals checkpoint value;
- current neighbor-trade SHA256 equals checkpoint value;
- prior day status is exact `DAY_PASS`.

Checkpoint reuse is computational only and may not change qualification logic.

## 8. Overall PASS gate

Exact terminal token:

`E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS`

requires all 8 days to be exact `DAY_PASS` and the output firewall to confirm:
- hypothetical maker orders created = false;
- fill simulation calculated = false;
- spread capture calculated = false;
- markout calculated = false;
- fees calculated = false;
- inventory P&L calculated = false;
- profitability calculated = false;
- TFI used = false;
- Confirmation/Q2/Validation/Final accessed = false.

Any day failure yields:

`E008_DISCOVERY_SEMANTIC_INTEGRITY_REVIEW`

and blocks E008 maker Discovery.

## 9. Next step after PASS

PASS does not itself authorize maker P&L.

Only after exact PASS may the frozen E008 maker Discovery implementation be built/frozen and pass a separate implementation preflight/identity gate before one promotional Discovery run.