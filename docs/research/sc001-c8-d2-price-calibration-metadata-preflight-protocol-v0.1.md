# SC001 — C8-D2 Price-Calibration Archive Metadata Preflight v0.1

Date: 2026-09-18
Status: **FROZEN METADATA-ONLY PREFLIGHT BEFORE C8 PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parent:

- `docs/research/sc001-c8-d1e-strict-coactive-1s-pass-result-v0.1.md`.

## 1. Purpose

Verify that the exact historical bodies needed for the first C8 nonpromotional price/headroom calibration day exist and are safely retrievable before any price body is opened.

No historical body may be downloaded/opened by D2.

## 2. Prospective calibration date rule

Freeze:

`2025-01-20 UTC`

Selection rule:

`first Monday after the 2025-01-15 engineering clock-qualification day`.

This rule is calendar-based and is fixed before inspection of any C8 cross-venue price outcome.

D2 metadata access alone does not yet contaminate the body.

## 3. Exact source bodies required

### OKX target UTC day reconstruction

Because qualified OKX archive semantics require D+D1:

- `BTC-USDT-SWAP-trades-2025-01-20.zip`;
- `BTC-USDT-SWAP-trades-2025-01-21.zip`.

Use the already-qualified historical resolver:

`POST /priapi/v5/broker/public/trade-data/download-link`

with target-day payload for 2025-01-20.

Require both exact trusted URLs from the same metadata response.

### Bybit

Exact archive:

`BTCUSDT2025-01-20.csv.gz`

URL:

`https://public.bybit.com/trading/BTCUSDT/BTCUSDT2025-01-20.csv.gz`.

## 4. Metadata/HEAD checks

For all three files require:

- HTTPS;
- exact trusted host;
- exact basename;
- HTTP HEAD 200;
- positive Content-Length;
- per-file size <=350 MiB;
- combined size <=700 MiB.

No body GET.

## 5. D1E parent requirement

Require documented D1E result identity and exact PASS:

`C8_D1E_STRICT_COACTIVE_1S_PASS`.

Qualified representation inherited:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`.

D2 does not alter this representation.

## 6. Exact terminal states

PASS:

`C8_D2_PRICE_CALIBRATION_METADATA_PASS`

REVIEW:

`C8_D2_PRICE_CALIBRATION_METADATA_REVIEW`

REVIEW is source/data availability only.

## 7. Firewalls

Must remain false:

- historical_archive_body_downloaded;
- historical_archive_body_opened;
- cross_venue_price_compared;
- cross_venue_return_calculated;
- raw_spread_calculated;
- dislocation_calculated;
- lag_calculated;
- strategy_signal_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 8. Consequence of PASS

Only after D2 PASS:

1. update contamination registry **before body access**;
2. classify 2025-01-20 C8 cross-venue price channel as nonpromotional Selection/Calibration;
3. freeze the exact within-second price statistic;
4. freeze a raw structural headroom sentinel;
5. only then download/open the three bodies.

No price outcome is authorized by D2.
