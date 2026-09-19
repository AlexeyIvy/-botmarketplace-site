# SC001 — B14-A D0 Dated-Futures Source / Archive Metadata Protocol v0.4

Date: 2026-09-19
Status: **FROZEN QUALIFIED-LIVE-TRANSPORT AMENDMENT / METADATA-ONLY**
Scope: `SCALPING RESEARCH / SC001`
Supersedes archive-request transport from v0.3 only.

Parents:

- `docs/research/sc001-b14a-d0-v0.4-http400-transport-review-v0.1.md`;
- `docs/research/sc001-b14a-d0-v0.1-source-review-result.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`.

## 1. Product scope unchanged

Standard crypto-margined inverse expiry futures:

- BTC-USD;
- ETH-USD.

Same-venue hedges:

- BTC-USD-SWAP;
- ETH-USD-SWAP.

## 2. Exact historical metadata request

Use:

`GET /api/v5/public/market-data-history`

with:

- module = `1`;
- instType = `FUTURES`;
- dateAggrType = `daily`;
- exact `instIdList = expiry contract instId`;
- UTC day begin;
- UTC next-day end.

Do not use `1D`.

## 3. Deterministic metadata-window resolution

For archive label date D:

1. query D UTC day window;
2. if exact trusted archive not found, query D-1 UTC day window;
3. accept only one unique exact URL whose basename is:
   `INSTID-trades-D.zip`.

This fallback changes metadata lookup only.

The archive filename/date identity stays D.

## 4. Trust requirements

Archive candidate must satisfy:

- HTTPS;
- host `static.okx.com`;
- exact expected basename;
- unique exact URL.

Then HEAD must return:

- HTTP 200;
- same trusted host;
- same basename;
- positive numeric Content-Length.

No body GET/open.

## 5. D0 PASS

`B14A_D0_V05_SOURCE_ARCHIVE_METADATA_PASS`

requires:

- >=2 future BTC-USD expiry contracts;
- >=2 future ETH-USD expiry contracts;
- both inverse SWAP hedges PASS;
- >=1 exact FUTURES archive metadata/HEAD PASS per family.

Otherwise:

`B14A_D0_V05_SOURCE_ARCHIVE_METADATA_REVIEW`

## 6. Firewalls

Remain false:

- futures trade body downloaded/opened;
- swap trade body opened;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- signal;
- execution/PnL;
- candidate ID.
