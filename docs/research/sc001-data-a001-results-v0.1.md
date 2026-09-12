# SC001-DATA-A001 — Binance BTCUSDT USD-M 1m DEV Backbone Results v0.1

Status: **PASS**

## Scope
- Venue: Binance USD-M Futures
- Symbol: BTCUSDT
- Interval: 1m
- Split: DEV only
- Period: 2023-04 through 2024-06
- Strategy/P&L calculated: NO
- Validation/FINAL minute-level data opened by this stage: NO

## Acquisition result
- Months: 15 / 15 PASS
- Network bytes read: 27,457,825
- Workspace bytes after outputs: 27,490,233
- Cross-month discontinuities: 0
- All retained monthly archives matched the expected official SHA256 checksums recorded by the acquisition engine.

## Integrity result
Every month from 2023-04 through 2024-06 has:
- 100% minute coverage
- exact expected row count
- 0 duplicate timestamps
- 0 nonmonotonic timestamps
- 0 invalid rows
- 0 out-of-month rows
- 0 minute-alignment errors
- first minute present
- last minute present
- max internal gap = 0 minutes

The DEV backbone is therefore contiguous at 1-minute resolution across month boundaries for the full frozen DEV interval.

## Qualification-only dates
The following dates remain frozen as qualification-only and must be excluded from future performance evaluation even if they are physically present in retained raw monthly archives:
- 2023-04-15
- 2024-01-15
- 2025-01-15
- 2026-07-15

Only the first two fall inside A001 DEV raw archives.

## Interpretation
A001 qualifies the Binance BTCUSDT USD-M 1m DEV backbone as technically complete and reproducible. This is a data-quality result, not a strategy result. No claim about alpha, profitability, execution quality, or true scalping edge is implied.

## Next-stage guardrails
1. Keep VALIDATION and FINAL minute/tick/L2 data closed.
2. Next acquisition should remain DEV-only and move to trade-level data on the pre-registered DEV sample days.
3. Do not infer maker fills or sub-minute execution from 1m bars.
4. Do not use A001 to optimize thresholds against future validation/final periods.
5. Maintain the hard per-run storage/network caps already adopted for the Android workflow.
