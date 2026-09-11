# SC001-DATA-Q004 — reviewed results v0.2

## Status after expert review

Q004 network/archive qualification itself passed for all four frozen epochs, but the engine's final `NEEDS_REVIEW` is a validator false-negative caused by treating newline-delimited JSON order-book records as comma-separated tabular rows and then comparing the resulting value-dependent pseudo-headers literally.

This document does **not** promote the dataset to final replay-ready status. It records what Q004 actually established and the required corrective step.

## Safety / acquisition

- Frozen epochs: 2023-04-15, 2024-01-15, 2025-01-15, 2026-07-15.
- HTTP Range respected for all four samples (`206 Partial Content`).
- 8 MiB read per epoch; total network bytes: 33,554,432.
- No full L2 archive downloaded.
- Workspace after outputs: ~1.66 MB.
- Minimum free-storage protection remained satisfied.

## What the payload actually is

The L2 archive member is text containing one JSON object per line (NDJSON / JSONL style), not CSV.

Across all four epochs the observed semantic object shape is consistent:

- `instId`
- `action`
- `ts`
- `asks`
- `bids`

The first record begins with `action="snapshot"`; following records observed in the prefix use `action="update"`.

Each book level is a 3-element array of the form:

`[price, size, order_count]`

Observed update rows contain zero size / zero order-count entries, which must be treated as level deletion semantics during replay rather than as ordinary positive depth.

## Why Q004 reported NEEDS_REVIEW

The Q004 parser fed each JSON line through CSV parsing and therefore split the JSON object at commas. The resulting so-called `header` included actual price, size, order-count and timestamp values. Exact-header equality across dates was therefore impossible by construction.

So `coherent_exact_header=false` does **not** demonstrate an OKX schema break. It demonstrates that the comparison method was inappropriate for NDJSON.

## Positive evidence from Q004

- Range acquisition succeeded for 4/4 frozen epochs.
- gzip prefix decompression succeeded for 4/4.
- tar member discovery succeeded for 4/4.
- Text records were present for 4/4.
- The semantic fields visible in every epoch are the same: `instId`, `action`, `ts`, `asks`, `bids`.
- Initial snapshot followed by updates is visible in every epoch prefix.
- Sampled update timestamps are monotonic in the inspected rows.
- Both 2025 and the 2026 `/pro/L2/` path use the same apparent semantic record shape in the inspected prefix.

## Remaining uncertainty

Q004 does not yet prove:

- that every complete record in the sampled prefix parses as valid JSON;
- that exact semantic keys/types are stable across all sampled records;
- that replaying snapshot + updates produces a valid uncrossed book throughout the prefix;
- full-day completeness;
- sequence-gap detection beyond timestamp ordering;
- exact maker queue position;
- strategy profitability.

## Required corrective step

Run `SC001-DATA-Q004R` (semantic replay qualification) before any bulk L2 calendar is frozen.

Q004R must re-use the same four frozen dates and small Range prefixes, but parse complete lines with `json.loads` and validate:

1. exact required keys/types;
2. `instId == BTC-USDT-SWAP`;
3. first event is `snapshot`;
4. subsequent actions are recognized (`snapshot`/`update` only unless explicitly documented);
5. monotonic millisecond timestamps;
6. each ask/bid level is `[price,size,orders]` with valid numeric domains;
7. zero-size updates delete levels;
8. deterministic in-memory replay from snapshot;
9. after each replayed event, best bid < best ask (or any exception is counted and surfaced);
10. epoch-to-epoch semantic schema compatibility.

No P&L and no full archive download are allowed in Q004R.

## Research boundary

Do not interpret L2 availability as permission to assume perfect maker fills. Price-level L2 can support spread/depth/imbalance and conservative taker execution modelling, but exact maker queue position still requires additional assumptions or order-level evidence.
