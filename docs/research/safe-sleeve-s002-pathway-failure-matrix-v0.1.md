# Safe-Sleeve S002-C — Pathway & Failure Matrix v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** PATHWAY_MATRIX_INITIALIZED — primary account-verified path established; operational latencies remain untested  
**Access profile:** Russian tax resident / Russia KYC / T-Bank + Alfa-Bank / approximately USD 1,000 equivalent / mixed RUB-USD preservation objective  
**Primary verified crypto candidate:** Bybit  
**Backup crypto candidate:** OKX (official-eligibility candidate; user account not yet checked)

## 1. Purpose

Translate the S001 `MULTI-DOMAIN LAYERED RESERVE` architecture into a concrete pathway/failure model for the user's actual access profile without assigning live-money allocations and without changing any active strategy.

The objective is not maximum yield. The objective hierarchy remains:

1. survival;
2. availability;
3. failure-domain independence;
4. transfer reliability;
5. only then yield/fees/taxes.

## 2. Current four-layer implementation candidate

### Layer 1 — Off-venue survival reserve

Primary class:

- insured RUB cash/deposit at one Russian bank;
- second existing bank maintained as an independent payment/transfer rail.

Current candidates:

- T-Bank;
- Alfa-Bank.

At the approximately USD 1,000 capital tier, deposit-insurance capacity is not the limiting factor. The second bank is valuable mainly for operational redundancy.

### Layer 2 — Execution buffer

Future small balance at the active crypto venue only when a demo requires it.

Current primary venue candidate:

- Bybit.

The execution buffer is not safe reserve.

### Layer 3 — Crisis-deployment bridge

Primary candidate path:

> T-Bank or Alfa-Bank -> Bybit P2P RUB -> USDT -> Unified Trading Account

Independent backup candidate:

> T-Bank or Alfa-Bank -> OKX P2P RUB -> crypto asset -> execution venue

OKX remains unverified at account level and therefore is a backup research path, not an assumed available rail.

### Layer 4 — Derivatives collateral

R003 collateral remains separate risk capital.

No part of R003 margin/collateral is counted as survival reserve.

## 3. Accessibility horizons

### H1

Only capital already positioned at the execution venue may be treated as plausibly executable inside one hour.

S002 does **not** assume that bank -> P2P -> venue settlement is deterministic inside H1.

### H24

Primary objective:

- normal bank/P2P route should be capable of reaching the venue in time for the next daily operational cycle under non-failure conditions.

This remains unproven until a later controlled transfer drill.

### H72

Primary objective:

- if one bank, P2P path or crypto venue is unavailable, a second path should exist to restore deployable capital within roughly three days under ordinary contingency conditions.

This is an architecture target, not a guaranteed SLA.

## 4. Failure matrix

| Scenario | T-Bank cash | Alfa-Bank cash | Bybit execution buffer | Bybit P2P bridge | OKX backup candidate | Expected architecture response |
|---|---|---|---|---|---|---|
| Bybit outage | survives | survives | temporarily inaccessible | unavailable | potentially available | do not count Bybit balance as safe reserve; use backup venue only if independently verified |
| Bybit withdrawal freeze | survives | survives | trapped | ingress may be pointless | potentially available | stop new funding to Bybit; preserve off-venue reserve |
| T-Bank transfer restriction | delayed/inaccessible | available | unaffected if already funded | T-Bank branch impaired | potentially available via Alfa | use Alfa rail; do not depend on single bank |
| Alfa transfer restriction | available | delayed/inaccessible | unaffected if already funded | Alfa branch impaired | potentially available via T-Bank | use T-Bank rail |
| RUB P2P liquidity degradation | survives | survives | unaffected if already funded | slower/wider spread | may provide alternate liquidity | reduce reliance on immediate deployment; avoid forced conversion |
| USDT depeg/issuer event | survives | survives | exposed if held as USDT | bridge impaired | may share same issuer risk | minimize permanent USDT holdings; consider alternate bridge asset only after separate due diligence |
| Crypto market crash + venue stress | survives | survives | exposed to venue/access risk | possibly impaired | possibly impaired | preserve majority of dry powder off-venue; execution buffer stays deliberately small |
| Single bank technical outage | one rail unavailable | other rail available | unaffected | one ingress branch unavailable | unchanged | use second bank |
| One P2P counterparty failure | survives | survives | unaffected | transaction-level disruption | alternate ads/venue may exist | no dependence on one counterparty; follow platform dispute process |
| Account security lock | survives | survives | account inaccessible | inaccessible | backup venue possibly available | off-venue reserve prevents catastrophic access concentration |
| Weekend/holiday | available subject to bank controls | available subject to bank controls | available if venue up | potentially available but unguaranteed | potentially available | H1 relies on pre-positioned buffer; do not promise bank-to-venue weekend SLA |
| Broker/MMF settlement delay (if later added) | bank cash unaffected | bank cash unaffected | unaffected | delayed if reserve is trapped in fund settlement | unchanged | money-market layer remains optional until it proves H24/H72 value |

## 5. Current classification by component

### T-Bank

`SURVIVAL_CANDIDATE + PRIMARY_OR_SECONDARY_BANK_RAIL`

Not selected as sole bank dependency.

### Alfa-Bank

`SURVIVAL_CANDIDATE + INDEPENDENT_BANK_RAIL`

Main value at current capital tier is redundancy.

### Bybit

`ACCOUNT_VISIBILITY_PASS_FOR_RESEARCH / PRIMARY_CRYPTO_INGRESS_CANDIDATE`

Confirmed at account level:

- KYC Level 1;
- Russia visible in residence flow;
- RUB P2P;
- USDT/RUB purchase path;
- unified trading/funding account structure;
- Spot/Futures/Options product categories visible.

Deferred to later operational check:

- specific BTCUSDT spot live order path;
- specific BTCUSDT perpetual live order path;
- external crypto withdrawal;
- actual transfer latency and fees;
- T-Bank / Alfa-Bank counterparty availability in real P2P ads.

### OKX

`BACKUP_CANDIDATE / ACCOUNT_LEVEL_UNVERIFIED`

Do not assume availability until a separate account/KYC check is performed.

### Money-market fund layer

`OPTIONAL / DEFERRED_AT_USD_1K`

At current capital size, added settlement complexity may outweigh modest absolute yield improvement. Revisit only if the pathway matrix later shows a clear operational benefit.

## 6. Preliminary sizing logic — no live allocation yet

No fixed percentages are approved.

Sizing must follow function:

1. **Execution buffer:** only enough for expected ordinary rebalancing and minimum-order/fee headroom.
2. **Crisis bridge:** only enough to meet the H24/H72 deployment target after the transfer path is measured.
3. **Derivatives collateral:** exactly what the frozen R003 implementation requires; this remains risk capital.
4. **Survival reserve:** residual capital kept off-venue, subject to bank/rail concentration rules.

At approximately USD 1,000, the default bias should be toward a **small number of components** rather than maximum fragmentation.

## 7. What S002-C still needs before PASS

The matrix is structurally complete but operationally uncalibrated.

Remaining unknowns:

- actual Bybit P2P spread and counterparty availability for T-Bank / Alfa-Bank;
- actual transfer limits on the user's bank accounts;
- real settlement latency in normal conditions;
- Bybit withdrawal security prerequisites;
- specific BTCUSDT spot/perpetual live-product availability at future demo time;
- backup venue account validation;
- tax-record export/reconciliation procedure;
- crisis drill design without production deployment.

These are operational checks, not reasons to alter R009/R003/R010.

## 8. S002-C status

> **S002-C: PATHWAY_MATRIX_INITIALIZED / STRUCTURAL_PASS / LATENCY_UNCALIBRATED**

The failure-domain architecture is now concrete enough to proceed to S002-D sizing research using frozen strategy mechanics and the approximately USD 1,000 capital tier.

No real-money transfer, deposit, trade or withdrawal is authorized by this status.

## 9. Research invariants

- R009-E002 inception remains `2026-09-10 00:00 UTC`;
- R003-E003 Binance boundary remains `2026-09-10 12:00 UTC`; retry only with the causality-safe hotfix and no reset;
- R003-X003 Bybit boundary remains `2026-09-10 16:00 UTC` and separate from Binance;
- R010-E001 inception remains `2026-09-11 00:00 UTC`; no threshold/weight/reset changes; inherited tranches are not prospective validation;
- no real-money deployment;
- broad platform development remains frozen.
