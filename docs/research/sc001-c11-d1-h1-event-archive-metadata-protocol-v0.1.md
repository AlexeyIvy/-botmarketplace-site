# SC001 — C11-D1 H1-2025 Event Calendar / Archive Metadata Batch v0.1

Date: 2026-09-18
Status: **FROZEN METADATA-ONLY H1 2025 BATCH / NO PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c11-d0-source-calendar-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.15.json`.

## 1. Purpose

Prospectively freeze and verify the exact C11 Selection/Calibration event chronology before any post-release BTC price outcome.

D1 is metadata-only.

## 2. Frozen chronology

Window:

`2025-01-01 through 2025-06-30`

Exactly 12 events:

- 2025-01-10 Employment Situation — 08:30 ET / 13:30 UTC;
- 2025-01-15 Consumer Price Index — 08:30 ET / 13:30 UTC;
- 2025-02-07 Employment Situation — 08:30 ET / 13:30 UTC;
- 2025-02-12 Consumer Price Index — 08:30 ET / 13:30 UTC;
- 2025-03-07 Employment Situation — 08:30 ET / 13:30 UTC;
- 2025-03-12 Consumer Price Index — 08:30 ET / 12:30 UTC;
- 2025-04-04 Employment Situation — 08:30 ET / 12:30 UTC;
- 2025-04-10 Consumer Price Index — 08:30 ET / 12:30 UTC;
- 2025-05-02 Employment Situation — 08:30 ET / 12:30 UTC;
- 2025-05-13 Consumer Price Index — 08:30 ET / 12:30 UTC;
- 2025-06-06 Employment Situation — 08:30 ET / 12:30 UTC;
- 2025-06-11 Consumer Price Index — 08:30 ET / 12:30 UTC.

The UTC shift reflects U.S. daylight-saving time and is frozen prospectively.

## 3. Official source checks

For each event require the official BLS monthly schedule page to contain:

- exact release family;
- exact calendar date;
- 08:30 AM publication time.

Do not access release values, surprises or revisions.

## 4. Historical BTC trade archive metadata

For each event date require exact metadata/HEAD for:

`BTC-USDT-SWAP-trades-YYYY-MM-DD.zip`

using the already-qualified OKX module-1 SWAP resolver.

No body GET/open.

## 5. PASS

Exact:

`C11_D1_H1_EVENT_ARCHIVE_METADATA_PASS`

requires:

- all 12 official event schedule checks PASS;
- all 12 exact BTC archive metadata/HEAD checks PASS.

REVIEW:

`C11_D1_H1_EVENT_ARCHIVE_METADATA_REVIEW`

is engineering/source-only.

## 6. Firewalls

Must remain false:

- historical_trade_body_downloaded;
- historical_trade_body_opened;
- macro_release_value_accessed;
- macro_surprise_calculated;
- first_impulse_calculated;
- post_release_move_calculated;
- strategy_signal_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 7. Consequence of PASS

Only after D1 PASS may C11 freeze the first outcome-bearing headroom sentinel for this already contaminated H1-2025 Selection/Calibration batch.
