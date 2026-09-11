# Safe-Sleeve S002 — User Access Profile v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** PARTIAL_ACCESS_PROFILE; several fields still required before S002-A can pass  
**Protocol:** `docs/research/safe-sleeve-s002-user-access-due-diligence-protocol-v0.1.md`

## 1. User-supplied access facts

Confirmed by user:

- citizenship / passport: Russian Federation;
- currently used banks: T-Bank and Alfa-Bank;
- expected crypto-venue universe should prioritize venues that permit Russian users and withdrawals, including Bybit, OKX and comparable alternatives;
- user is not currently familiar with the Russian tax treatment of crypto trading and wants S002 to incorporate it.

## 2. Important legal/access distinction

For S002, the following must be tracked separately:

1. citizenship / passport used for KYC;
2. legal place of residence / address used by the exchange or financial institution;
3. tax residency.

Russian citizenship does not, by itself, settle tax residency or all exchange-service eligibility.

Exchange access can depend on residence, account legal entity, product, payment method and sanctions-screening status. Tax residency in Russia depends primarily on statutory residency criteria rather than citizenship alone.

## 3. Preliminary official-source findings — crypto venues

### Bybit

As of the 2026-09-01 Bybit restricted-jurisdictions notice, the Russian Federation as a whole is not listed among the general excluded jurisdictions, while specified Russian-controlled regions of Ukraine are excluded. Bybit separately screens prohibited/sanctioned persons.

Bybit's fiat-service documentation states that Russian-KYC users are limited to RUB transactions under the general fiat service; USD SWIFT for Russian Federation is restricted.

Bybit P2P remains an operational candidate pathway for RUB and requires KYC. Current Bybit P2P fee documentation explicitly includes RUB pairs.

Interpretation for S002:

- Bybit remains a plausible execution/bridge venue candidate for a Russian user, subject to the exact residence/KYC profile and account-level product availability;
- direct foreign-currency bank rails cannot be assumed;
- RUB P2P may be a bridge candidate, not an off-venue survival reserve.

### OKX

OKX terms state that service provider/legal entity depends on place of residence and that not all services are available in all jurisdictions.

The 2026-07-08 OKX risk/compliance disclosure does not list Russia as a fully unsupported jurisdiction, but explicitly identifies **Russia (fiat payments)** as a jurisdiction where services can be restricted.

OKX continues to maintain RUB P2P market pages and P2P rules for verified users. Current P2P documentation states that payment accounts must belong to the verified user and that risk controls may temporarily restrict withdrawal/selling after some purchases.

Interpretation for S002:

- OKX is a plausible spot/crypto/P2P access candidate, but fiat-payment access cannot be assumed;
- P2P liquidity is not equivalent to guaranteed H1/H24 mobility because platform risk controls can impose delays;
- exact account-level availability must be checked after the residence/KYC profile is frozen.

## 4. Preliminary official-source findings — Russian taxes

Current FNS materials state:

- tax residency is not determined by citizenship alone;
- Russian tax residents are generally persons meeting the statutory physical-presence test;
- digital currency is treated as property for tax purposes;
- income from purchase/sale or other disposal of digital currency for individuals is subject to NDFL;
- current FNS guidance states a 13% rate and 15% on the portion above the applicable 2.4 million RUB threshold for income from purchase/sale or other disposal of digital currency;
- sale proceeds can be reduced by documented acquisition-related expenses when calculating the tax base;
- a taxpayer receiving taxable income from sale of digital currency generally calculates the tax and files 3-NDFL independently.

This is a research summary, not personal tax advice. S002 must use the user's actual tax-residency status before applying an after-tax model.

## 5. Preliminary official-source findings — Russian reserve layer

Russian bank deposits/accounts are a realistic off-venue survival-reserve class for a Russian-access profile.

Bank of Russia materials confirm that the standard deposit-insurance protection is currently up to 1.4 million RUB per depositor per bank for ordinary insured accounts/deposits, with separate higher limits for certain special cases.

Because the user already uses T-Bank and Alfa-Bank, the two-bank structure is a natural candidate for avoiding a single-bank failure domain, subject to actual portfolio size and concentration limits.

Russian broker-accessible money-market funds also exist through the user's existing ecosystem:

- T-Investments / T-Capital offers a money-market fund class (for example TMON);
- Alfa-Investments offers a money-market fund class (for example AKMM).

These instruments are **not** bank deposits and must not be counted as insured cash. They require separate analysis of settlement, trading hours, fund/counterparty structure, liquidity and withdrawal path.

## 6. Provisional S002 architecture for this access profile

Without assigning percentages yet, the currently plausible implementation classes are:

### Layer 1 — Off-venue survival reserve

Candidate classes:

- insured RUB bank balances split across T-Bank / Alfa-Bank within applicable insurance/concentration limits;
- potentially short-duration Russian sovereign / money-market instruments through an accessible Russian broker, if their liquidity and settlement pass S002 testing.

### Layer 2 — Execution buffer

Only the minimum operational balance required on the selected crypto venue(s).

No assumption that Bybit or OKX exchange balances are safe reserve.

### Layer 3 — Crisis-deployment bridge

Current leading candidate classes:

- RUB -> Bybit P2P -> USDT/other supported asset;
- RUB -> OKX P2P -> USDT/other supported asset;
- potentially a bounded self-custodied stablecoin bridge if the user accepts wallet/issuer/chain risk.

P2P is treated as an operational bridge with banking/AML/fraud/risk-control dependencies, not as a guaranteed instant rail.

### Layer 4 — Derivatives collateral

R003 collateral remains venue-risk capital and stays separate from the safe reserve.

No change to the frozen R003 economics or Binance/Bybit forward records.

## 7. Remaining fields required for S002-A — ACCESS_PROFILE_FROZEN

Still required from the user:

1. **Actual tax-residency expectation for 2026:** is the user expected to qualify as a Russian tax resident under the statutory day-count test, or not?
2. **Residence/KYC country:** what country/address is or will be declared as residence on Bybit/OKX and other financial accounts?
3. **Current exchange accounts:** does the user already have verified Bybit and/or OKX accounts, and which products are visibly available now (spot, perpetual/futures, P2P, fiat deposit/withdrawal)?
4. **Base reserve currency:** should the safe sleeve primarily preserve purchasing power/liabilities in RUB, USD-equivalent terms, or a mixed target?
5. **Expected implementation capital range:** approximate total capital range for the first realistic implementation study. This is separate from the `$1,000` R009 demo-engineering candidate.
6. **Crisis deployment objective:** how much of the portfolio should be executable within H1, H24 and H72?
7. **Self-custody tolerance:** is the user willing to maintain a small self-custodied stablecoin bridge, or should S002 avoid that route?
8. **Russian brokerage access:** does the user already have T-Investments and/or Alfa-Investments accounts?

Until these fields are answered, product-level allocation percentages remain prohibited.

## 8. Status

> **S002-A: NOT YET PASSED — PARTIAL_ACCESS_PROFILE**

The Russian-access pathway is now materially narrowed, but tax residency, exchange KYC residence, capital range, deployment-speed requirement and self-custody preference are still required before eligibility and layer sizing can be frozen.

No active strategy parameters, forward clocks, venue records or G001/G002 conclusions are changed by this profile update.
