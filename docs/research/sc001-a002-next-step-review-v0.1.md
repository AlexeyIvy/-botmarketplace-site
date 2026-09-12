# SC001 — A002 next-step expert review v0.1

## Decision

A002 remains the correct next data stage, but the original plan is strengthened before any bulk download.

The current state is sufficient to justify moving beyond minute bars: A001 qualified a continuous DEV-only BTCUSDT USD-M 1m backbone from 2023-04 through 2024-06 with 15/15 months PASS, 100% minute coverage, zero gaps/duplicates, and no cross-month discontinuities. However, 1m bars are too coarse to validate true scalping microstructure and can hide or manufacture sub-minute effects through aggregation.

## Why not stop and optimize on 1m now

A minute-only strategy screen would be cheap, but it would not answer the actual SC001 objective. It cannot resolve event ordering inside the minute, aggressor bursts, short-lived reversals/continuations, or realistic latency at sub-minute horizons. Optimizing a strategy on 1m before acquiring trade-level data risks selecting a bar-construction artifact. Therefore A001 is treated as context/backbone, not as the final microstructure layer.

## Why Binance aggTrades is the first trade-level layer

Binance USD-M aggTrades preserves aggregate trade id, price, quantity, first and last underlying trade ids, millisecond timestamp, and buyer-maker side. That is sufficient for signed aggressive flow, burst intensity, price response, and a proxy for underlying print count while being substantially smaller than full raw trades. Raw trades are deferred unless a later hypothesis genuinely depends on individual print sequence.

AggTrades still cannot provide historical bid/ask spread, depth, queue position, or exact maker fills. It therefore cannot by itself authorize a final execution model. OKX L2 remains the execution-quality layer after a candidate hypothesis exists.

## Main optimization to the original A002 plan

Do not bulk-download all 25 DEV days immediately.

First run `SC001-DATA-A002-PREFLIGHT` against the already frozen 25 DEV acquisition dates. It downloads only official checksum files plus archive metadata. The purpose is to prove availability and exact compressed size before committing phone storage/network budget.

If preflight passes, acquire data in five quarter batches: 2023-Q2, 2023-Q3, 2023-Q4, 2024-Q1, 2024-Q2. Each batch contains exactly the frozen five strata for that quarter: CPI, NFP, FOMC, ordinary weekday, ordinary weekend. This keeps acquisition resumable and preserves the frozen design.

## Frozen safety rules before sizes are observed

- Preflight network cap: 50 MB.
- No aggTrades archive body download during preflight.
- Later single archive hard cap: 256 MB.
- Later quarter-batch hard cap: 1.0 GB.
- Later session hard cap: 2.0 GB.
- Minimum free-storage reserve: 4.0 GB.
- Do not raise a cap after seeing a file size; redesign instead.
- No automatic deletion of downloaded raw archives without explicit approval.

## Validation rules for the later A002 acquisition

For each downloaded day, require official checksum match, one expected data member, correct timestamp column, monotonic aggregate-trade ids, monotonic timestamps, valid first/last trade-id ranges, valid buyer-maker values, and timestamps confined to the requested UTC day. Equal timestamps are allowed. Do not require exact reconstruction of 1m OHLCV from aggTrades because archive/API boundary semantics can differ at sub-minute edges.

## What is explicitly postponed

- No VALIDATION or FINAL trade-level data.
- No P&L or strategy optimization during A002 acquisition.
- No Bybit bulk layer yet; use it later only as independent robustness evidence if a candidate merits it.
- No OKX full-L2 bulk yet; first resolve/record historical contract-size assumptions and run one bounded full-day engineering pilot.
- No maker-queue claims from aggregate L2.

## Research logic after A002

A002 is justified only because it unlocks information A001 cannot supply: sub-minute aggressive-flow sequencing. Once DEV aggTrades is qualified, the next experiment must be pre-registered before looking at strategy P&L. Candidate families should remain economically distinct and few in number. A hypothesis that fails DEV/validation gates is not rescued by post-hoc threshold, side, latency, or event-window changes.

This sequence minimizes researcher degrees of freedom and avoids downloading expensive microstructure data before we know exactly why it is needed.
