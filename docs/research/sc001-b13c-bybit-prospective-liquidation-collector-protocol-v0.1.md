# SC001 — B13-C Bybit Prospective Liquidation Raw Collector Protocol v0.1

Date: 2026-09-19
Status: **FROZEN PROTECTED DATA ACQUISITION / NO ALPHA OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b13c-liquidation-source-data-feasibility-audit-v0.1.md`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v4.95.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`.

## 1. Purpose

Begin a free prospective raw dataset of explicit forced-liquidation events before any B13-C strategy feature, threshold, horizon or direction rule is selected.

This is data acquisition only.

## 2. Venue and stream

Venue:

`Bybit`

Product family:

`linear perpetual`

WebSocket:

`wss://stream.bybit.com/v5/public/linear`

Topic per symbol:

`allLiquidation.SYMBOLUSDT`

Official semantics:

- pushes all liquidations on the subscribed symbol;
- push frequency up to 500 ms;
- event fields include:
  - `T` event/update timestamp;
  - `s` symbol;
  - `S` position side;
  - `v` executed size;
  - `p` bankruptcy price;
- `S=Buy` means a long position was liquidated;
- `S=Sell` means a short position was liquidated.

## 3. Frozen symbol universe

Reuse the pre-existing SC001 12-symbol universe:

- BTCUSDT;
- ETHUSDT;
- SOLUSDT;
- DOGEUSDT;
- ORDIUSDT;
- FILUSDT;
- UNIUSDT;
- XRPUSDT;
- LTCUSDT;
- OPUSDT;
- BCHUSDT;
- SUIUSDT.

No substitution based on observed liquidation frequency.

Before WebSocket start, every symbol must pass metadata qualification:

- category = linear;
- exact symbol;
- contractType = LinearPerpetual;
- quoteCoin = USDT;
- status = Trading.

If any frozen symbol fails source qualification:

`B13C_COLLECTION_SOURCE_REVIEW`

Do not silently collect a reduced winner universe.

## 4. Evidence role

All raw records collected under this protocol are:

`PROTECTED_PROSPECTIVE_RAW_LIQUIDATION_STREAM`

Collection start time is permanently recorded.

Raw events may not be retroactively treated as historical calibration selected after inspection.

## 5. Raw message preservation

For every liquidation WebSocket message write an append-only raw JSONL record containing:

- local receive timestamp ms;
- exact topic;
- exact server `ts`;
- exact `data` payload;
- collector version;
- connection epoch ID.

Do not deduplicate raw messages.

## 6. Normalized event preservation

For each event item also write a normalized JSONL row containing:

- receive timestamp ms;
- server timestamp ms;
- liquidation event timestamp `T`;
- symbol;
- raw side `S`;
- derived liquidated position side:
  - Buy -> LONG_LIQUIDATED;
  - Sell -> SHORT_LIQUIDATED;
- raw executed size string;
- raw bankruptcy price string;
- deterministic SHA256 fingerprint of the raw event tuple;
- connection epoch ID.

The fingerprint is diagnostic only.

No event is dropped merely because the fingerprint repeats.

## 7. Connection integrity

Heartbeat:

- send Bybit JSON ping at least every 20 seconds.

On every connection/reconnection record:

- connection epoch;
- connect attempt timestamp;
- subscription ACK;
- disconnect/error timestamp;
- reconnect timestamp;
- resulting gap duration where measurable.

Any disconnect creates an explicit potential data gap.

No future study may assume events were absent during a collection gap.

## 8. Daily rotation

Rotate raw/event files on UTC date.

Directory:

`~/sc001_data/SC001_B13C_PROSPECTIVE_LIQUIDATIONS/`

Suggested structure:

- `raw/YYYY-MM-DD.jsonl`;
- `events/YYYY-MM-DD.jsonl`;
- `connection/connection_events.jsonl`;
- `collector_state.json`.

Append-only event files.

Atomic state updates.

## 9. Allowed collection diagnostics

Allowed before strategy design:

- total raw message count;
- total normalized event count;
- current connection status;
- subscription ACK state;
- reconnect count;
- cumulative gap duration;
- schema-invalid count;
- source-qualified symbol count.

Raw count is data-sufficiency information only.

## 10. Forbidden during protected collection

Do not calculate or inspect for strategy selection:

- post-liquidation returns;
- pre-event returns;
- continuation/reversal;
- liquidation size threshold;
- bankruptcy-price distance to market;
- best symbol;
- long-vs-short predictive performance;
- cluster threshold;
- event window;
- execution;
- PnL.

No outcome-bearing B13-C experiment may use the protected stream until a separate design is frozen prospectively.

## 11. Data completeness

Connection uptime alone is not proof of complete liquidation capture.

Future B13-C research must consult the connection-gap ledger.

An event window overlapping a recorded disconnect/gap cannot be silently treated as complete.

Completeness rules for formal analysis must be frozen later before outcome.

## 12. Self-test gate

Before persistent collection:

`--mode self-test`

must PASS:

- Python/freeze handshake;
- exact frozen universe;
- parser fixtures for valid Bybit liquidation payload;
- invalid-side fixture rejected;
- invalid numeric fixture rejected;
- local output-path/write test;
- `websocket-client` dependency import.

Exact token:

`B13C_COLLECTOR_SELF_TEST_PASS`

Failure:

`B13C_COLLECTOR_SELF_TEST_REVIEW`

## 13. Collector terminal/status states

Persistent collector is not a strategy test.

Operational states:

- `B13C_COLLECTION_RUNNING`;
- `B13C_COLLECTION_SOURCE_REVIEW`;
- `B13C_COLLECTION_IMPLEMENTATION_FAIL`;
- graceful stop `B13C_COLLECTION_STOPPED`.

## 14. Parallel research

Starting this collector does not make B13-C an active strategy candidate.

While data accumulates, SC001 may continue new independent-base design work.

Protected B13-C liquidation data must remain unopened for alpha design.
