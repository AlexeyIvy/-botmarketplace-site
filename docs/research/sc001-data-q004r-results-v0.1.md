# SC001-DATA-Q004R — Semantic OKX L2 Replay Qualification Results v0.1

Date recorded: 2026-09-11
Stage: SC001-DATA-Q004R
Status: PASS
Strategy/P&L calculated: NO
Full L2 archive downloaded: NO

## Purpose
Q004R was a corrective semantic qualification stage after Q004 showed that OKX historical L2 archives are JSONL rather than CSV-like tabular data. Q004R parses the actual JSON records, reconstructs the price-level order book from snapshots and updates, and checks replay integrity across four frozen dates.

## Frozen dates
- 2023-04-15
- 2024-01-15
- 2025-01-15
- 2026-07-15

All four dates passed.

## Safety / storage result
- Range bytes per sample: 8 MiB
- Four samples total network bytes: 33,554,432
- Emergency session cap: 2,000,000,000 bytes
- Workspace cap: 2,000,000,000 bytes
- Minimum free-storage reserve: 4,000,000,000 bytes
- Workspace after outputs: 14,193 bytes
- Free storage after outputs: 69,142,269,952 bytes
- No full L2 archive was downloaded.

## Semantic schema
All four frozen epochs had the same semantic signature:
- instrument: BTC-USDT-SWAP
- first action: snapshot
- required keys: action, asks, bids, instId, ts
- no extra keys observed in the sampled prefixes
- level shape: [price, size, orders]
- max ask levels observed: 400
- max bid levels observed: 400

`coherent_semantic_schema = true`.

## Replay integrity
### 2023-04-15
- records parsed: 207,931
- snapshots: 46
- updates: 207,885
- invalid JSON lines: 0
- missing required keys: 0
- wrong instrument: 0
- invalid action: 0
- nonmonotonic timestamps: 0
- malformed levels: 0
- crossed-book states: 0
- empty-book states: 0
- zero-size deletions: 403,729
- delete-missing-level events: 0

### 2024-01-15
- records parsed: 89,782
- snapshots: 16
- updates: 89,766
- invalid JSON lines: 0
- missing required keys: 0
- wrong instrument: 0
- invalid action: 0
- nonmonotonic timestamps: 0
- malformed levels: 0
- crossed-book states: 0
- empty-book states: 0
- zero-size deletions: 512,262
- delete-missing-level events: 0

### 2025-01-15
- records parsed: 122,856
- snapshots: 24
- updates: 122,832
- invalid JSON lines: 0
- missing required keys: 0
- wrong instrument: 0
- invalid action: 0
- nonmonotonic timestamps: 0
- malformed levels: 0
- crossed-book states: 0
- empty-book states: 0
- zero-size deletions: 533,439
- delete-missing-level events: 0

### 2026-07-15
- records parsed: 146,748
- snapshots: 3
- updates: 146,745
- invalid JSON lines: 0
- missing required keys: 0
- wrong instrument: 0
- invalid action: 0
- nonmonotonic timestamps: 0
- malformed levels: 0
- crossed-book states: 0
- empty-book states: 0
- zero-size deletions: 324,524
- delete-missing-level events: 0

## Interpretation
The Q004 CSV-style comparison issue is resolved. The historical OKX 400-level L2 data supports deterministic price-level replay on the frozen sampled prefixes across 2023, 2024, 2025 and 2026, including the newer `/pro/L2/` archive path in 2026.

This qualifies the data structure for future research on spread, depth, book imbalance, book-state transitions and conservative taker-execution modelling.

## Hard boundary
PASS does **not** prove:
- exact maker queue position,
- MBO/order-level priority,
- fill probability for passive orders,
- profitability of any scalping strategy,
- integrity of every byte of every future full-day archive.

Any later bulk collector must run replay-integrity checks per downloaded file/window rather than assuming Q004R generalizes automatically.

## Next step
Before any strategy P&L or broad tick/L2 bulk acquisition:
1. freeze development / validation / final time partitions;
2. freeze a deterministic calendar of microstructure windows;
3. freeze macro-event windows under the event-calendar policy;
4. only then collect the minimum Binance aggTrades / Bybit trades / OKX L2 data required for those windows, in resumable batches below the phone storage cap;
5. preserve a final untouched slice and do not choose windows after viewing strategy P&L.

This stage is data qualification only and does not alter any other frozen project branch.
