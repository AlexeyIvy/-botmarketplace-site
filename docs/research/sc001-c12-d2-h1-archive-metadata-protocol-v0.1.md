# SC001 — C12-D2 H1-2025 USDC-USDT Archive Metadata Batch v0.1

Date: 2026-09-18
Status: **FROZEN METADATA-ONLY H1 BATCH / NO PEG OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c12-d1-spot-trade-semantics-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.16.json`.

## 1. Purpose

Prospectively freeze and verify a broad calendar Selection/Calibration source window for C12 before any peg-deviation outcome.

No historical trade body is downloaded/opened.

## 2. Frozen target window

Target UTC days:

`2025-01-01 through 2025-06-30`

inclusive.

Selection rule:

`calendar H1 2025`

chosen before peg outcomes.

Because qualified SPOT semantics require D+D1 UTC stitching, required unique source archives are:

`2025-01-01 through 2025-07-01`

inclusive, exactly `182` daily archives.

## 3. Historical metadata

For each required source date resolve exact:

`USDC-USDT-trades-YYYY-MM-DD.zip`

using the qualified priapi SPOT `instIdList=[USDC-USDT]` contract.

Require:

- unique exact trusted URL;
- HTTPS;
- host = `static.okx.com`;
- HEAD 200;
- positive Content-Length.

No body GET.

## 4. PASS

Exact:

`C12_D2_H1_ARCHIVE_METADATA_PASS`

requires all 182 source archives to resolve and HEAD-pass.

REVIEW:

`C12_D2_H1_ARCHIVE_METADATA_REVIEW`

is source/data availability only.

## 5. Firewalls

Must remain false:

- historical_trade_body_downloaded;
- historical_trade_body_opened;
- peg_deviation_calculated;
- reversion_outcome_calculated;
- threshold_selected;
- strategy_signal_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 6. Consequence of PASS

Only after D2 PASS may C12 freeze:

- exact structural parity threshold from the already frozen 15 bps burden;
- max hold <=30m;
- episode definition;
- bounded H1 body acquisition;
- first peg-dislocation headroom/reversion sentinel.

No outcome is authorized by D2.
