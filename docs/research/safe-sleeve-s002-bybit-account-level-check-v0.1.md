# Safe-Sleeve S002-B — Bybit Account-Level Check v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** PARTIAL_PASS — KYC/P2P/RUB confirmed; product/withdrawal/country-detail checks remain  
**Parent:** `docs/research/safe-sleeve-s002-eligibility-pathway-screen-v0.1.md`

## 1. User-supplied account evidence

The user supplied three Bybit mobile-app screenshots on 2026-09-11.

Observed directly from the screenshots:

- Bybit account exists and is accessible;
- user-center screen shows `Верификация личности — Верификация Ур.1 пройдена`;
- profile page shows a verification badge/status;
- P2P Trading is visible in the account;
- P2P search screen allows **Buy USDT** with fiat currency **RUB**;
- no deposit, trade, transfer or withdrawal was performed for this check.

## 2. What this confirms for S002-B

### Confirmed

- `BYBIT_ACCOUNT_EXISTS = YES`
- `BYBIT_KYC_LEVEL1 = PASSED`
- `BYBIT_P2P_VISIBLE = YES`
- `BYBIT_RUB_P2P_VISIBLE = YES`
- `BYBIT_USDT_RUB_BRIDGE_CANDIDATE = ACCOUNT_LEVEL_VISIBLE`

This materially strengthens the candidate pathway:

> T-Bank / Alfa-Bank -> Bybit P2P -> USDT -> execution venue

but does not yet prove deterministic H1/H24 settlement, bank-specific payment-method support, withdrawal availability, or derivatives access.

## 3. Still unconfirmed at account level

The screenshots do not yet establish:

1. country/residence recorded in the Bybit verification profile as Russian Federation;
2. Spot trading visibility/enabled status;
3. Derivatives / Perpetual visibility/enabled status;
4. crypto withdrawal visibility/enabled status and any security prerequisite;
5. whether T-Bank and/or Alfa-Bank appear among usable RUB P2P payment methods in the user's current marketplace view;
6. exact Bybit legal entity/service region shown for the account.

## 4. S002 interpretation

The Bybit path advances from generic official-source eligibility to **account-level partial validation**.

Current classification:

`BYBIT_RUB_P2P_PATH = PARTIAL_PASS / ACCOUNT_VISIBLE / NOT YET OPERATIONALLY DRILLED`

No money needs to be deposited or traded to complete the remaining visibility checks.

## 5. Remaining screenshot evidence requested

Minimal remaining evidence set:

1. verification-details screen showing country/residence, if Bybit exposes it;
2. Pro-mode trading/services screen showing Spot and Derivatives/Perpetual visibility;
3. crypto withdrawal entry screen showing that withdrawal functionality is available to the account, without entering an address or amount;
4. RUB P2P payment-method dropdown/list showing whether T-Bank and/or Alfa-Bank are available.

These checks are visibility/eligibility checks only, not a live transfer drill.

## 6. Safety / research invariants

- no real-money deployment is authorized;
- no active strategy parameters are changed;
- R009-E002 remains fixed at 2026-09-10 00:00 UTC;
- R003-E003 Binance remains fixed at 2026-09-10 12:00 UTC and must use the causality-safe hotfix on retry;
- R003-X003 Bybit remains separate at 2026-09-10 16:00 UTC;
- R010-E001 remains fixed at 2026-09-11 00:00 UTC;
- S002 remains an implementation/access study only.
