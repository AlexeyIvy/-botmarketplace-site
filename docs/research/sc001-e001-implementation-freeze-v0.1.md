# SC001-E001 — Implementation Freeze v0.1

**Project:** BotMarketplace / BotMarketplace.store  
**Branch:** SCALPING RESEARCH / SC001  
**Experiment:** SC001-E001  
**Date:** 2026-09-11  
**Status:** IMPLEMENTATION FROZEN BEFORE FIRST SC001-E001 RESULT

## 1. Independence

SC001-E001 remains fully independent of R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001, and Safe-Sleeve S002. No result from this experiment may alter their frozen rules, clocks, parameters, or decisions. No real-money authorization is created.

## 2. Research-rule freeze

Canonical pre-test protocol:

`docs/research/sc001-e001-pretest-freeze-v0.1.md`

Protocol commit:

`f832499479014edf868428e71f9c195546bb4fcf`

The economic rules, validation split, cost tracks, robustness variants, bootstrap, and PASS/FAIL gates are unchanged.

## 3. Frozen engine

Engine path:

`research/sc001/sc001_e001_extreme_move_mean_reversion.py`

Frozen engine commit:

`a0a18910ee7518164ad14cc3d88bdcac36e8d3c0`

The engine reads the already-existing R003-E002 raw cache rather than downloading a new market dataset.

Expected local source locations:

- `/storage/emulated/0/Download/R003_E002_WORKSPACE/_cache/`; or
- `/storage/emulated/0/Download/R003_E002_WORKSPACE/_cache_bundle.zip`.

Required cached streams:

- `futures-contract` raw Binance 1h kline pages;
- `funding` raw Binance funding pages.

Why raw cache is used: the normalized `r003_e002_hourly_clean.csv` intentionally retained close-based fields but does not contain the perpetual `open` required by the already-frozen E001 rule `entry at open(t+1)`. Replacing the missing open with close would violate the frozen execution rule, so the original cached Binance kline rows are used instead.

The engine does not change, write into, or reset the R003 workspace. SC001 outputs go to a separate folder:

`/storage/emulated/0/Download/SC001_E001_RESULTS/`

## 4. Frozen launcher

Launcher path:

`research/sc001/sc001_e001_mobile_launcher.py`

Launcher commit:

`52b0a206e1d40edb2fa15da962ff53dc0cf8feb6`

The launcher is implementation-only. It:

1. verifies that `R003_E002_WORKSPACE` exists;
2. requires `_cache` or `_cache_bundle.zip`;
3. downloads the engine pinned to commit `a0a18910ee7518164ad14cc3d88bdcac36e8d3c0`;
4. compiles the downloaded Python before execution;
5. prints its SHA256;
6. executes the frozen engine locally.

It does **not** download new market data and does **not** update the frozen engine to repository HEAD.

## 5. Data boundary

SC001-E001 uses only the fixed historical window already defined before results:

- start: `2020-01-01 00:00 UTC`;
- final allowed bar open: `2026-09-09 19:00 UTC`.

Even if newer rows are available in a cache or API later, E001-v0.1 must not append them to the historical proof.

## 6. Pre-P&L technical gates

Before strategy results are accepted, the engine verifies at minimum:

- exact frozen start/end boundary;
- monotonic UTC ordering after deduplication;
- positive OHLC values;
- close timestamp after open timestamp;
- no same-bar entry;
- explicit gap handling;
- source hashes / snapshot identity where available.

A structural data-integrity failure stops the experiment before a strategy verdict is promoted.

## 7. Mandatory outputs

Expected result bundle:

- `sc001_e001_source_identity.json`
- `sc001_e001_data_audit.json`
- `sc001_e001_primary_trades_base.csv`
- `sc001_e001_metrics.csv`
- `sc001_e001_regimes.csv`
- `sc001_e001_bootstrap.json`
- `sc001_e001_summary.md`
- `sc001_e001_run_state.json`

For review, the minimum upload set is:

1. `sc001_e001_run_state.json`;
2. `sc001_e001_summary.md`;
3. `sc001_e001_metrics.csv`.

## 8. Decision after run

The run may return FAIL, WEAK, or PROMISING_SCREEN under the already-frozen gates. A poor result must not be rescued by modifying E001. Any genuinely different hypothesis must receive a new experiment identifier.

If existing raw cache is missing/corrupt, that is a data-availability failure, not permission to silently substitute a new sample. A separate SC001 data-acquisition step must then be documented before downloading replacement or higher-frequency history.
