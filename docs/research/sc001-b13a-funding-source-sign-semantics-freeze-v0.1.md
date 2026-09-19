# SC001 — B13-A Funding Source & Sign Semantics Freeze v0.1

Date: 2026-09-19
Status: **FROZEN BEFORE B13-A FUNDING-VALUE RUN**
Scope: `SCALPING RESEARCH / SC001`

Parent:

`docs/research/sc001-b13a-funding-differential-structural-preflight-v0.1.md`

## 1. Sign convention

Both venues use the same economic sign convention for perpetual funding:

- positive funding rate -> longs pay shorts;
- negative funding rate -> shorts pay longs.

Therefore for a delta-neutral cross-venue pair with equal notional, the best-orientation upper-bound gross funding transfer at a matched settlement is:

`abs(okx_rate - bybit_rate)`

This is an upper-bound structural statistic only.

No claim is made that the favorable orientation could always be established causally at low cost.

## 2. OKX historical source

Do not use the recent REST funding-history endpoint for H1-2025.

Use the already-qualified official historical bulk service:

`GET /api/v5/public/market-data-history`

with:

- module = `3` FundingRate;
- instType = `SWAP`;
- instFamilyList = exact `SYMBOL-USDT`;
- dateAggrType = `monthly`;
- H1-2025 monthly archive range only.

Trusted archive requirements:

- HTTPS;
- host `static.okx.com`;
- basename equals returned filename;
- ZIP CRC pass.

Historical funding row semantics inherited from the qualified E002 source amendment:

`instrument_name,funding_rate,funding_time`

Rows outside the exact target instrument/window are ignored.

## 3. Bybit historical source

Use:

`GET https://api.bybit.com/v5/market/funding/history`

with:

- category = `linear`;
- exact `SYMBOLUSDT`;
- backward pagination using `endTime`;
- limit = `200`.

Required response fields:

- symbol;
- fundingRate;
- fundingRateTimestamp.

No fixed 8-hour cadence is assumed.

Each symbol may have a different or dynamically changed funding interval.

## 4. Matching

Match only observed settled funding records.

Frozen tolerance:

`abs(okx_funding_time - bybit_funding_time) <= 5 minutes`

Each source record may be used once.

Deterministic matching:

- candidate pairs ordered by smallest absolute timestamp skew;
- tie break by earlier OKX timestamp, then earlier Bybit timestamp;
- greedy one-to-one assignment.

No carry-forward.

## 5. Funding-value firewall

Allowed:

- funding rates;
- funding settlement timestamps;
- source/archive metadata;
- static cost arithmetic.

Forbidden:

- price;
- mark/index return;
- basis;
- trade/L2 bodies;
- strategy price PnL;
- execution fills;
- symbol selection by subsequent return.

## 6. Current official semantic corroboration

Official OKX and Bybit documentation both describe positive funding as payment from longs to shorts and negative funding as payment from shorts to longs.

This source-semantic freeze is not a strategy result.
