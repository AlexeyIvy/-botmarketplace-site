# R003-X001 Bybit — Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** frozen before X001 result inspection  
**Protocol:** `docs/research/r003-bybit-x001-structural-replication-protocol-v0.1.md`  
**Frozen engine commit:** `c411a1a92f5682f2a5af33871c22064311c4cb86`  
**Frozen mobile launcher commit:** `a18d062a5121a7a6cbc2cb7248425cf02039c01f`

## 1. Purpose

Remove remaining implementation ambiguity before the first independent-venue R003 replication result is inspected.

## 2. Data mechanics frozen

- Venue: Bybit.
- Product: BTCUSDT `linear` perpetual.
- Funding history: Bybit V5 `/v5/market/funding/history`, backward pagination, 200 rows/page.
- Stress reference: Bybit V5 `/v5/market/index-price-kline`, `linear`, `BTCUSDT`, daily bars, backward pagination, up to 1000 rows/page.
- Instrument metadata: Bybit V5 `/v5/market/instruments-info`.
- First-run cutoff is stored locally and reused after interruption.
- Downloaded API pages are checkpointed locally; a restart resumes instead of intentionally moving the historical endpoint.
- No interpolation.

## 3. Funding sign

Normalized short funding carry is `+fundingRate`.

This follows Bybit's documented convention that when funding is positive, longs pay shorts; when negative, shorts pay longs.

## 4. Launch-year treatment

The instrument launch timestamp is fetched from Bybit metadata.

The first full calendar year is determined from the later of instrument launch and earliest retained funding event. A partial launch year is descriptive and is excluded from completed-full-year gates.

## 5. Current funding interval is diagnostic

The engine records `fundingInterval` from current instrument metadata and compares observed event gaps with it.

Because Bybit may dynamically alter settlement frequency in exceptional conditions, cadence mismatch alone is diagnostic and is not used to fabricate missing events or automatically rewrite historical funding.

## 6. Crisis-state implementation

Each funding observation receives the latest causally closed Bybit daily index-price state.

No future daily bar may be used.

The index-price reference is a pre-result implementation choice and may not be replaced by a more favorable price series after inspecting X001.

## 7. Output package

Exactly eight user-facing result files are expected under `R003_X001_BYBIT/results`:

1. `r003_x001_bybit_run_state.json`
2. `r003_x001_bybit_source_audit.json`
3. `r003_x001_bybit_funding_clean.csv`
4. `r003_x001_bybit_index_daily.csv`
5. `r003_x001_bybit_metrics.csv`
6. `r003_x001_bybit_yearly.csv`
7. `r003_x001_bybit_drawdown_buckets.csv`
8. `r003_x001_bybit_summary.md`

Local checkpoint, snapshot, instrument-info and engine files do not need to be uploaded.

## 8. No-result-chasing rule

After output inspection, do not rescue X001 by changing:

- venue;
- symbol;
- funding sign or thresholds;
- first-full-year logic;
- PRE/POST slices;
- rolling-window gate;
- drawdown thresholds;
- index/spot stress reference;
- leverage or implementation sizing.

Any material change is a separately versioned hypothesis.

## 9. Allowed next step

Only if X001 returns interpretable data and `STRUCTURAL_SIGNAL_PRESENT` may the project freeze a Bybit-specific X002 self-financing implementation replication.

X001 itself can never be a production, OOS, demo or live PASS.
