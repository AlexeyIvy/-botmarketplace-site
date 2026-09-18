# SC001 — C12-D0 USDC-USDT Instrument / Historical Source Preflight v0.1

Date: 2026-09-18
Status: **FROZEN METADATA-ONLY / NO PEG OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parent:

`docs/research/sc001-c12-candidate-assignment-freeze-v0.1.md`

## 1. Purpose

Verify:

1. current USDC-USDT spot instrument identity;
2. historical daily trade archive availability;
3. external USDC parity-source availability.

No historical price body is opened.

## 2. Current instrument

Exact instrument:

`USDC-USDT`

Require:

- instType=SPOT;
- baseCcy=USDC;
- quoteCcy=USDT;
- state=live.

## 3. External parity anchor source

Reference:

`https://www.circle.com/usdc`

D0 may perform HEAD only.

The economic anchor recorded in C12 is USDC's external 1:1 USD redemption design for eligible redemption channels.

D0 does not inspect market price outcomes from this source.

## 4. Representative historical date

Fixed source-qualification date:

`2025-01-15 UTC`

This date is selected for source semantics only, not because of a known stablecoin dislocation.

Expected exact trade archive filename:

`USDC-USDT-trades-2025-01-15.zip`

## 5. Historical metadata resolver

Attempt metadata-only exact resolution in this order:

### Resolver A — OKX historical-data priapi
POST:

`/priapi/v5/broker/public/trade-data/download-link`

with:

- module=1;
- instType=SPOT;
- instQueryParam.instIdList=[USDC-USDT];
- daily exact date bounds.

### Resolver B — public historical metadata
GET:

`/api/v5/public/market-data-history`

with:

- module=1;
- instType=SPOT;
- dateAggrType=daily;
- exact begin/end;
- instIdList=USDC-USDT.

Accept only:

- exact filename;
- trusted static.okx.com URL;
- HEAD 200;
- positive Content-Length.

No body GET.

## 6. Exact states

PASS:

`C12_D0_SOURCE_PARITY_PREFLIGHT_PASS`

REVIEW:

`C12_D0_SOURCE_PARITY_PREFLIGHT_REVIEW`

## 7. Firewalls

Must remain false:

- historical_trade_body_downloaded;
- historical_trade_body_opened;
- peg_deviation_calculated;
- reversion_outcome_calculated;
- threshold_selected;
- pnl_calculated;
- promotional_alpha_accessed.

## 8. Consequence of PASS

Only after exact PASS may C12 freeze:

- Selection/Calibration chronology;
- fixed parity-deviation threshold derived from structural burden;
- max hold <=30 minutes;
- cheapest headroom/reversion sentinel.

No price outcome is authorized by D0.
