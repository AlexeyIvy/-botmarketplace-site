# SC001-DATA-Q008 — OKX L2 Full-Day Replay Pilot Results v0.1

Status: **FULL_DAY_PASS**

Pilot date: `2024-01-05`
Instrument: `BTC-USDT-SWAP`
Protocol commit: `ada4a6d2ef95fca1bb40f37553d6d630afa00579`

## Result

The full 2024-01-05 OKX 400-level L2 archive passed complete streaming replay from the beginning of the UTC day to end-of-day.

Archive:
- compressed bytes: `500060536`;
- SHA256: `7279d6b87021ea64982449f5a7c86e298a5c46c1c107ac41a368debeaaf5929a`;
- regular tar members: 1;
- member: `BTC-USDT-SWAP-L2orderbook-400lv-2024-01-05.data`;
- uncompressed member bytes: `3819945260`.

Replay:
- records parsed: `7568405`;
- snapshots: `1441`;
- updates: `7566964`;
- first action: `snapshot`;
- resync snapshots after first: `1440`;
- first timestamp: `2024-01-05T00:00:00.005Z`;
- last timestamp: `2024-01-05T23:59:59.990Z`;
- UTC minute buckets observed: `1440/1440`;
- out-of-target-day records: 0;
- nonmonotonic timestamps: 0;
- invalid JSON lines: 0;
- missing required keys: 0;
- wrong instrument: 0;
- malformed levels: 0;
- crossed-book states: 0;
- empty-book states: 0;
- delete-missing-level events: 0;
- max ask/bid depth observed: 400/400;
- max inter-record timestamp gap: `87720 ms`.

The `87720 ms` maximum inter-record gap is retained as a diagnostic, not silently removed. It did not prevent full 1440-minute coverage or create empty/crossed states, and therefore did not fail the frozen full-day integrity gates. Later midquote work should report book-state age at each sampled target instead of assuming every target is near an L2 update.

## Independent artifact verification

The uploaded 500060536-byte archive was independently SHA256-hashed after the run and matched the report SHA exactly:

`7279d6b87021ea64982449f5a7c86e298a5c46c1c107ac41a368debeaaf5929a`

The tar header also independently reports the expected single data member and declared uncompressed size `3819945260` bytes.

## Safety / firewall

On the successful rerun the completed local archive was reused, so network bytes read were `0`.

No E002 strategy feature, midquote-response alpha, execution profitability, or P&L was calculated. OKX Q2, formal Validation, and Final remained unopened.

## Interpretation

Q008 removes the main engineering uncertainty that had remained after bounded-prefix Q004R: at least one full selected OKX L2 day can be replayed deterministically and cleanly through the entire archive.

This is a data-quality result, not evidence of strategy profitability.

## Optimized next action

Before downloading the remaining ~2.10 GB of Q1 L2 archives, use the already-qualified 2024-01-05 full day for a **frozen one-day midquote falsification pilot**:

- exact existing 5s OKX TFI feature;
- no threshold tuning;
- response measured from replayed best-bid/best-ask midpoint rather than trade prints;
- midquote sampled causally as the last valid replayed book state at or before each target time;
- primary latency 100 ms, stress 250 ms, diagnostic 500 ms;
- report book-state age at target timestamps;
- no spread/fee/depth/P&L claim.

If the primary TFI→midquote association is not positive on this predetermined first Q1 day, stop before downloading the remaining four L2 days and reassess whether the trade-price effect is partly microstructure bounce/persistence. If positive, keep the specification frozen and acquire/replay the remaining four Q1 L2 days as the next confirmation layer.
