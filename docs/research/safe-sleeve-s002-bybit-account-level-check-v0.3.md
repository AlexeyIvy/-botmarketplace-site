# Safe-Sleeve S002-B — Bybit Account-Level Check v0.3

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** ACCOUNT_VISIBILITY_PASS_FOR_RESEARCH — core account/KYC/RUB-P2P/trading-category visibility established; live operational checks deferred  
**Parent:** `docs/research/safe-sleeve-s002-eligibility-pathway-screen-v0.1.md`  
**Supersedes:** `docs/research/safe-sleeve-s002-bybit-account-level-check-v0.2.md`

## 1. Additional user-supplied evidence

The user supplied seven additional Bybit mobile-app screenshots on 2026-09-11.

Observed directly:

- top trading navigation visibly includes `Спот`, `Фьючерсы`, `Опцион`, and `Alpha`;
- a futures trading interface is visible with leverage controls, order type, long/short buttons and a funding-rate field;
- an options interface is visible for BTC;
- TradFi/global-assets/CFD interfaces are also visible;
- the services catalogue exposes full trading/service categories rather than a restricted P2P-only shell;
- the account remains unfunded; user reports no prior deposit and no live trading activity.

## 2. Important product-scope distinction

The futures screenshot shown is a TradFi/global-asset futures interface (for example TSLAUSDT) rather than direct proof that the specific crypto contract required by R003 (`BTCUSDT` perpetual) is enabled for live trading.

Therefore S002 records two different facts:

- **trading product categories are visibly available at account level** — confirmed;
- **specific BTCUSDT perpetual live-order eligibility** — not yet operationally checked and not inferred from the TradFi screenshot.

Likewise, the visible `Спот` tab establishes Spot product-category visibility, but no funded BTCUSDT spot order-entry drill has been performed.

This distinction prevents overclaiming account capabilities from UI labels alone.

## 3. External withdrawal interpretation

The user could not locate a usable external-crypto-withdrawal entry while the account balance is zero and reports never having deposited funds.

S002 does not treat this as evidence that withdrawals are unavailable.

At this stage:

`BYBIT_EXTERNAL_CRYPTO_WITHDRAWAL = UNTESTED / ZERO-BALANCE ACCOUNT`

This is no longer a blocker for the research eligibility screen. It becomes an operational-drill item before any production-like demo or real-capital promotion.

No deposit should be made solely to satisfy S002-B.

## 4. Consolidated account-level flags

- `BYBIT_ACCOUNT_EXISTS = YES`
- `BYBIT_KYC_LEVEL1 = PASSED`
- `BYBIT_RESIDENCE_SELECTION_RUSSIA = VISIBLE`
- `BYBIT_P2P_VISIBLE = YES`
- `BYBIT_RUB_P2P_VISIBLE = YES`
- `BYBIT_USDT_RUB_BRIDGE_CANDIDATE = ACCOUNT_LEVEL_VISIBLE`
- `BYBIT_GENERIC_BANK_TRANSFER_P2P_METHOD = VISIBLE`
- `BYBIT_UNIFIED_TRADING_ACCOUNT = VISIBLE`
- `BYBIT_FUNDING_ACCOUNT = VISIBLE`
- `BYBIT_SPOT_PRODUCT_CATEGORY = VISIBLE`
- `BYBIT_FUTURES_PRODUCT_CATEGORY = VISIBLE`
- `BYBIT_OPTIONS_PRODUCT_CATEGORY = VISIBLE`
- `BYBIT_FUTURES_ORDER_INTERFACE = VISIBLE`
- `BYBIT_SPECIFIC_BTCUSDT_PERPETUAL_LIVE_ELIGIBILITY = DEFERRED_TO_OPERATIONAL_CHECK`
- `BYBIT_EXTERNAL_CRYPTO_WITHDRAWAL = DEFERRED_TO_OPERATIONAL_CHECK`
- `BYBIT_TBANK_P2P_COUNTERPARTY_SUPPORT = NOT_YET_CONFIRMED`
- `BYBIT_ALFABANK_P2P_COUNTERPARTY_SUPPORT = NOT_YET_CONFIRMED`

## 5. S002-B conclusion for Bybit

> **BYBIT ACCOUNT PATH: ACCOUNT_VISIBILITY_PASS_FOR_RESEARCH**

The account-level evidence is now sufficient to retain Bybit as the primary crypto-ingress/execution candidate in S002 without asking the user to deposit or trade.

The remaining unknowns are operational rather than eligibility blockers:

1. actual RUB P2P counterparties accepting T-Bank and/or Alfa-Bank;
2. specific BTCUSDT spot and BTCUSDT perpetual live-product availability at the moment of a future demo;
3. external withdrawal path/security prerequisites;
4. actual H1/H24/H72 transfer latency and failure behavior.

These should be tested only in the later controlled operational-drill stage and must not require real-money deployment now.

## 6. Effect on broader S002

Bybit can now be used as the primary account-verified crypto path for constructing the S002 pathway matrix.

OKX remains the independent backup-venue candidate. Its account-level verification can be performed later and is not required to keep progressing with the architecture study.

The next valid S002 task is therefore to build the concrete pathway/failure matrix for approximately USD 1,000 equivalent capital across:

- T-Bank survival cash;
- Alfa-Bank redundancy;
- Bybit primary RUB->USDT ingress/execution;
- OKX backup ingress candidate;
- optional Russian money-market reserve layer;
- derivatives collateral kept explicitly outside the safe reserve.

## 7. Research invariants

- no real-money deployment is authorized;
- no active strategy parameters are changed;
- R009-E002 remains fixed at 2026-09-10 00:00 UTC;
- R003-E003 Binance remains fixed at 2026-09-10 12:00 UTC and must use the causality-safe hotfix on retry;
- R003-X003 Bybit remains separate at 2026-09-10 16:00 UTC;
- R010-E001 remains fixed at 2026-09-11 00:00 UTC;
- S002 remains an implementation/access study only.
