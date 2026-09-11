# SC001-DATA-Q003 — Results v0.1

Date: 2026-09-11

## Status

`QUALIFIED_METADATA_ONLY`

No strategy/P&L was calculated. No bulk or multi-year L2 archive was downloaded.

## What was established

For `BTC-USDT-SWAP`, OKX instrument metadata was retrieved successfully:

- `ctVal = 0.01`
- `ctMult = 1`
- `ctValCcy = BTC`
- `settleCcy = USDT`
- `tickSz = 0.1`
- `lotSz = 0.01`
- `minSz = 0.01`

These fields must be preserved in any future cross-venue normalization. Derivatives size must not be treated as BTC quantity without contract conversion.

## L2 archive discovery

The public historical-data backend returned one trusted OKX static archive for each frozen date:

- 2023-04-15: 130.1 MB reported
- 2024-01-15: 471.97 MB reported
- 2025-01-15: 530.22 MB reported
- 2026-07-15: 328.41 MB reported

The canonical 2025-01-15 file was not downloaded because it exceeded the frozen 512 MB single-file cap. HEAD reported `Content-Length = 555,972,136` bytes.

This `SAFE_SKIP` is a successful safety outcome, not a data failure.

## Important format-risk observation

The archive path changed by 2026 from a path containing `/orderbook/L2/400lv/` to `/orderbook/pro/L2/400lv/`. This is evidence that format/path evolution is plausible and must be qualified before multi-period replay.

## Safety outcome

- session cap: 2,000,000,000 bytes
- workspace cap: 2,000,000,000 bytes
- per-file cap: 512,000,000 bytes
- minimum free reserve: 4,000,000,000 bytes
- downloaded in Q003: 3,566 bytes
- workspace after outputs: 20,895 bytes
- free storage after outputs: 69,144,920,064 bytes

## Research interpretation

Q003 proves that the historical L2 source can be discovered reproducibly and that file sizes are material. It does not yet prove that the archive schema is stable or that exact maker queue position can be reconstructed.

L2 should initially be used for spread, depth, imbalance, liquidity-state and conservative execution diagnostics. Exact maker-fill modelling is prohibited unless the data are later shown to contain sufficient queue/order-level information.

## Next step

Open `SC001-DATA-Q004` as schema qualification, not bulk collection.

Q004 should:

1. use the already-frozen archive URLs/dates;
2. request only bounded byte prefixes using HTTP Range where supported;
3. hard-abort if the server ignores Range and attempts to return a full archive above the local cap;
4. inspect archive/container structure and the first data rows for 2023, 2024, 2025 and 2026;
5. compare field names, timestamp units, action semantics, side semantics, level/depth representation and any sequence/checksum fields;
6. write only small schema reports, not decompressed datasets;
7. keep the 2 GB session/workspace caps and 4 GB storage reserve.

Only after Q004 confirms schema compatibility should a staged L2 calendar be frozen.

## Independence

This branch does not alter R009, R003, R010, S002, or any existing forward protocol.
