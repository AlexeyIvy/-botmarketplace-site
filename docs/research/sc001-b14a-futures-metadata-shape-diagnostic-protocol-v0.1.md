# SC001 — B14-A FUTURES Historical Metadata Shape Diagnostic v0.1

Date: 2026-09-19
Status: **FROZEN ENGINEERING METADATA DIAGNOSTIC / NO MARKET BODY ACCESS**
Scope: `SCALPING RESEARCH / SC001`

Parent:

`docs/research/sc001-b14a-d0-v0.6-exact-archive-unresolved-review-v0.1.md`

## 1. Purpose

Inventory the actual OKX public historical metadata response for standard crypto-margined FUTURES.

No research/economic verdict is calculated.

## 2. Exact queries

Endpoint:

`GET /api/v5/public/market-data-history`

For each family:

- BTC-USD;
- ETH-USD.

For each metadata date:

- 2026-09-16;
- 2026-09-15.

Parameters:

- module=1;
- instType=FUTURES;
- instFamilyList=family;
- dateAggrType=daily;
- begin/end exact UTC day.

## 3. Allowed response fields

Record only metadata/identity fields:

- response code/msg;
- node path;
- filename/fileName;
- URL field name;
- URL host;
- URL basename;
- instId/instFamily/instType if present;
- selected scalar keys useful to understand grouping.

No URL may be followed.

No HEAD.

No body GET/open.

## 4. Forbidden

Do not access:

- trade archive body;
- trade rows;
- prices;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution/PnL.

## 5. Output

Write:

`~/sc001_data/SC001_B14A_D0_SOURCE_ARCHIVE/sc001_b14a_futures_metadata_shape_diag_v0_1.json`

and print a compact inventory suitable for screenshot review.
