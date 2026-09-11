# SC001-DATA-A001 — Binance BTCUSDT USD-M 1m DEV Backbone Protocol v0.1

Date: 2026-09-11
Status: FROZEN BEFORE DOWNLOAD/P&L

## Purpose

Acquire the cheap, reproducible 1-minute BTCUSDT USD-M futures backbone for the DEV split only. This is an acquisition/integrity stage, not a strategy test.

## Frozen scope

- Venue: Binance USD-M Futures.
- Symbol: BTCUSDT.
- Interval: 1m.
- Source: official `data.binance.vision` monthly archives.
- DEV months only: 2023-04 through 2024-06 inclusive.
- VALIDATION minute-level data is not acquired in A001.
- FINAL minute-level data is not acquired in A001.
- No strategy signal, no P&L, no parameter search.

The four qualification-only dates remain excluded from future performance evaluation even if they are physically present inside an official monthly archive:
- 2023-04-15
- 2024-01-15
- 2025-01-15
- 2026-07-15

## Integrity checks per month

1. Fetch the official `.CHECKSUM` sidecar.
2. Resolve a unique expected SHA-256 for the monthly ZIP.
3. Download or safely reuse the exact monthly ZIP.
4. Verify ZIP SHA-256 against the official checksum.
5. Require exactly one non-directory data member.
6. Parse 1m kline rows without transforming the official archive.
7. Validate millisecond timestamp scale for USD-M futures.
8. Validate timestamps belong to the target UTC month and are minute-aligned.
9. Record duplicates, non-monotonic timestamps, gaps and coverage.
10. Frozen monthly quality gate: coverage >= 99.5%, zero duplicate timestamps, zero non-monotonic timestamps, zero malformed rows, zero out-of-month rows, exact first minute and exact last minute.
11. Check continuity across adjacent monthly archives.

A month that fails a gate is `REVIEW`; no rescue or silent patching is allowed.

## Safety

- Session network cap: 2,000,000,000 bytes.
- Workspace cap: 2,000,000,000 bytes.
- Per archive cap: 100,000,000 bytes.
- Checksum response cap: 1,000,000 bytes.
- Minimum free-storage reserve: 4,000,000,000 bytes.
- Partial downloads use `.part` and are deleted on failure.
- Completed valid archives are idempotently reused on rerun.
- Official ZIP archives are retained; no extraction to disk.

## Outputs

Folder: `/storage/emulated/0/Download/SC001_DATA_A001_BINANCE_DEV_1M`

- `sc001_data_a001_report.json`
- `sc001_data_a001_manifest.json`
- `sc001_data_a001_summary.md`
- `sc001_data_a001_final_safety.json`
- `archives/*.zip`

## Interpretation

A001 `PASS` means the DEV 1m backbone is reproducibly acquired and structurally qualified. It does not imply scalping edge, execution realism, or profitability.
