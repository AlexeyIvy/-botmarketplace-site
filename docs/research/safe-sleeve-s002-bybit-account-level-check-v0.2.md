# Safe-Sleeve S002-B — Bybit Account-Level Check v0.2

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** STRONG_PARTIAL_PASS — KYC/P2P/RUB/Russia-residence selection/account structure confirmed; external withdrawal and standard Spot/Perpetual visibility still need a minimal check  
**Parent:** `docs/research/safe-sleeve-s002-eligibility-pathway-screen-v0.1.md`  
**Supersedes:** `docs/research/safe-sleeve-s002-bybit-account-level-check-v0.1.md`

## 1. Evidence set

The user supplied an additional six Bybit mobile-app screenshots on 2026-09-11 after the initial three-screen check.

Observed directly from the screenshots:

- country/region residence selection screen shows **Russia**;
- Bybit services interface is visible with full-service categories rather than a minimal P2P-only shell;
- P2P RUB payment-method filter is visible;
- payment-method list contains generic `Bank Transfer` plus other generic methods, but does not enumerate T-Bank or Alfa-Bank by name in that filter screen;
- account-transfer screen shows **Unified Trading Account -> Funding Account** internal transfer functionality;
- this internal-transfer screen is not an external crypto withdrawal screen;
- no deposit, trade, external transfer or withdrawal was performed.

Together with the previous screenshots, the account-level evidence now supports:

- Bybit account exists and is accessible;
- Identity Verification Level 1 passed;
- P2P visible;
- Buy USDT with RUB visible;
- Russia is the user-visible residence-country selection in the verification flow;
- unified trading/funding account structure is available.

## 2. Current account-level flags

- `BYBIT_ACCOUNT_EXISTS = YES`
- `BYBIT_KYC_LEVEL1 = PASSED`
- `BYBIT_P2P_VISIBLE = YES`
- `BYBIT_RUB_P2P_VISIBLE = YES`
- `BYBIT_USDT_RUB_BRIDGE_CANDIDATE = ACCOUNT_LEVEL_VISIBLE`
- `BYBIT_RESIDENCE_SELECTION_RUSSIA = VISIBLE`
- `BYBIT_UNIFIED_TRADING_ACCOUNT = VISIBLE`
- `BYBIT_FUNDING_ACCOUNT = VISIBLE`
- `BYBIT_GENERIC_BANK_TRANSFER_P2P_METHOD = VISIBLE`
- `BYBIT_TBANK_P2P_METHOD = NOT_YET_CONFIRMED`
- `BYBIT_ALFABANK_P2P_METHOD = NOT_YET_CONFIRMED`
- `BYBIT_EXTERNAL_CRYPTO_WITHDRAWAL = NOT_YET_CONFIRMED`
- `BYBIT_STANDARD_SPOT_ACCESS = NOT_YET_EXPLICITLY_CONFIRMED`
- `BYBIT_STANDARD_PERPETUAL_ACCESS = NOT_YET_EXPLICITLY_CONFIRMED`

## 3. Interpretation of the Russia screen

The screenshot is sufficient to show that `Russia` is accepted and visible as the residence-country selection in the user's current Bybit verification path.

It is not treated as stronger evidence than the app itself provides; S002 does not infer a specific legal entity from this screen alone.

For the access study this materially reduces the earlier jurisdiction uncertainty because the user's intended Russia residence profile is compatible with the visible account flow.

## 4. Interpretation of the services / mode screens

The user could not find a separate `Pro` switch.

The currently visible services catalogue is already a full-featured interface with trading/banking/service categories. The earlier profile screen also displayed a `Bybit Lite` switch/control, which is consistent with the user already being outside Lite mode rather than needing to switch into Pro.

S002 therefore does **not** require the user to keep searching for a `Pro` toggle.

However, the screenshots do not yet explicitly show a standard Spot order-entry product or a standard USDT perpetual product, so those remain visibility checks rather than assumed permissions.

## 5. Interpretation of P2P payment methods

The RUB P2P filter screen shows a generic `Bank Transfer` option but does not list T-Bank or Alfa-Bank by name.

This means:

- generic bank-transfer P2P is account-visible;
- specific compatibility with T-Bank / Alfa-Bank should be verified from live marketplace advertisements/payment-method labels, not inferred from the generic filter;
- no transaction is needed for this verification.

## 6. Interpretation of the transfer screen

The screenshot titled `В аккаунте` shows an internal transfer from `Единый торговый аккаунт` to `Аккаунт финансирования`.

This confirms internal account mobility, but **does not** confirm external blockchain withdrawal.

External withdrawal remains a separate security/access check.

## 7. Current S002-B classification for Bybit

> **BYBIT ACCOUNT PATH: STRONG_PARTIAL_PASS / RUB-P2P + KYC + RUSSIA PROFILE VISIBLE / NO LIVE DRILL**

For the approximately USD 1,000 research capital tier, Bybit remains the strongest first crypto-ingress/execution candidate because the account already exists and the RUB->USDT P2P path is visible at account level.

This still does not make the route deterministic H1/H24 infrastructure.

## 8. Minimal remaining evidence

Only two evidence groups remain useful before closing the Bybit visibility phase:

1. **External crypto withdrawal entry:** first screen of `Withdraw crypto` / `Вывести криптовалюту`, with no address or amount entered.
2. **Standard trading products:** one screen showing either a Spot market/order-entry interface and one showing a USDT perpetual / derivatives interface, or one combined screen/menu where both are clearly present.

Optional, not mandatory for the Bybit account-level eligibility decision:

- one P2P marketplace result screen where payment methods on actual RUB/USDT ads reveal whether T-Bank and/or Alfa-Bank are accepted by counterparties.

No deposit, purchase, transfer, order or withdrawal should be made for these checks.

## 9. Research invariants

- no real-money deployment is authorized;
- no active strategy parameters are changed;
- R009-E002 remains fixed at 2026-09-10 00:00 UTC;
- R003-E003 Binance remains fixed at 2026-09-10 12:00 UTC and must use the causality-safe hotfix on retry;
- R003-X003 Bybit remains separate at 2026-09-10 16:00 UTC;
- R010-E001 remains fixed at 2026-09-11 00:00 UTC;
- S002 remains an implementation/access study only.
