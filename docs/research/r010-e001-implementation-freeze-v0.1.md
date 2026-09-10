# R010-E001 — Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** frozen before any R010 forward P&L  
**Protocol:** `docs/research/r010-e001-prospective-shadow-forward-protocol-v0.1.md`

## Frozen protocol

Protocol commit:

`5f13f36712bd48ffdf21292591ddb7b592ba1d03`

## Frozen engine

Path:

`research/r010/r010_e001_prospective_shadow_forward.py`

Engine commit:

`5088678bdf480a222f9b2cc276ab3573ec4a3639`

## Frozen Android launcher

Path:

`research/r010/r010_e001_prospective_shadow_forward_mobile.py`

Launcher commit:

`e456e32d19437b5fa5cd0e7abc5540a7fc91d5a8`

## Fixed prospective clock

- protocol frozen before the 2026-09-10 UTC BTCUSDT daily bar closes;
- signal bar = 2026-09-10 UTC;
- immutable forward inception = **2026-09-11 00:00:00 UTC**;
- first realized forward interval is the 2026-09-10 close to 2026-09-11 close interval, using the target determined from the fully closed 2026-09-10 bar;
- later launcher execution may reconstruct from this boundary but may never move it.

## Frozen state machine

- Binance Spot BTCUSDT daily, fully closed UTC bars only;
- SMA120 trend state;
- trend sleeve = 10% BTC when `close > SMA120`, else 0%;
- four drawdown arming levels = -20/-35/-50/-65%;
- four equal 2.5pp armed recovery tranches;
- armed recovery capital remains cash while trend is OFF;
- when trend is ON, all currently armed recovery tranches are permitted to deploy;
- if trend turns OFF, recovery exposure returns to cash but arming memory remains;
- all armed memory resets only on a new closing ATH;
- total R010 target range 0-20%;
- no leverage, hysteresis, cooldown, expiry, second indicator or parameter grid.

## Frozen accounting

- self-financing daily target accounting;
- cost tracks 5/10/25/50 bps on traded notional;
- 10 bps baseline;
- cash return 0%;
- historical pre-inception bars initialize state only and contribute no R010 forward P&L.

## Frozen comparators

- R010_COMBINED_DAILY;
- RECOVERY10_DAILY;
- R009_COMBINED_DAILY on the same state path;
- TREND10_DAILY;
- STATIC10_DAILY;
- STATIC15_DAILY;
- STATIC20_DAILY.

## Evidence restriction

No terminal positive or negative strategy conclusion before 365 realized forward daily intervals, except implementation/source failure may invalidate the record.

A strong mature interpretation additionally requires at least one prospective post-freeze arming event and at least one prospective recovery activation event.

R010-E001 is a new shadow-forward candidate. It does not modify, replace or reset R009-E002, R003-E003, or R003-X003.
