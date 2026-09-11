# Safe-Sleeve S002 — User Access Profile v0.2

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** **S002-A ACCESS_PROFILE_FROZEN**  
**Protocol:** `docs/research/safe-sleeve-s002-user-access-due-diligence-protocol-v0.1.md`

## 1. Frozen user access facts

Confirmed by user:

- citizenship / passport: Russian Federation;
- tax residency: Russian Federation;
- residence / KYC country to be declared: Russian Federation;
- existing banking relationships: T-Bank and Alfa-Bank;
- existing Bybit account: account was created, current identity-verification status is not remembered and must be checked operationally;
- OKX and comparable venues are acceptable candidates if they lawfully service Russian-resident users and permit withdrawals;
- T-Investments and/or Alfa-Investments can be opened/installed if useful;
- target implementation-study capital: approximately **USD 1,000 equivalent total**;
- reserve preference: **mixed purchasing-power target**, not RUB-only;
- no real-money deployment is authorized by S002.

## 2. Operational defaults frozen for S002-A

These are implementation requirements, not allocation percentages.

### H1

No requirement to make the entire off-venue reserve deployable within one hour.

H1 is satisfied only by the deliberately small execution buffer already positioned at the selected execution venue.

### H24

The architecture should be capable, under ordinary functioning of at least one independent ingress path, of funding the next daily rebalance requirement of the selected validated directional strategy.

This is aligned with the daily rebalance cadence of R009/R010 and avoids forcing the survival reserve into the same failure domain merely for sub-hour mobility.

### H72

A secondary independent path should be capable of restoring or increasing deployable capital within 72 hours if the primary bridge is impaired.

### Self-custody

Self-custodied stablecoin is **not required** for the base S002 implementation candidate. It remains an optional later redundancy path and cannot be assumed without an explicit operational-security decision.

## 3. Current official-source eligibility findings

### Bybit

Current Bybit restricted-jurisdiction documentation, updated 2026-09-01, does not list the Russian Federation as a generally excluded jurisdiction, while specified Russian-controlled regions of Ukraine and sanctioned/prohibited persons are excluded.

Bybit fiat-service documentation states that Russian-KYC users may use RUB under the general fiat service, while USD SWIFT is restricted for the Russian Federation.

Bybit P2P requires identity verification (KYC).

**S002 implication:** Bybit is an eligible candidate for account-level verification, but it is not yet marked `ACCOUNT_VERIFIED` because the user's current KYC/product status must be checked inside the account.

### OKX

Current OKX compliance documentation does not identify Russia as a fully unsupported jurisdiction, but specifically restricts fiat-payment services for Russia.

OKX P2P rules require identity verification and payment methods whose owner name matches the verified OKX user. OKX also documents account/risk-control restrictions that can temporarily prevent trading, depositing or withdrawing.

**S002 implication:** OKX remains an eligible candidate as an independent bridge/execution route, but P2P cannot be treated as guaranteed H1 liquidity.

## 4. Russian banking / brokerage eligibility

### Bank layer

T-Bank and Alfa-Bank are already user-accessible banking relationships.

Bank of Russia documentation states that ordinary insured deposits/accounts are protected up to 1.4 million RUB per depositor per bank under the deposit-insurance system (with separate special-case limits not needed for this capital tier).

At an implementation-study size near USD 1,000 equivalent, deposit-insurance concentration is not a binding sizing constraint. Using two existing banks is still operationally useful as rail redundancy.

### T-Investments

T-Investments publicly states that a brokerage account can be opened online with passport/phone, with no account-opening fee. Its money-market fund ecosystem is therefore an accessible candidate class for a Russian resident.

T-Bank also documents broad extended/weekend trading for supported securities and 24/7 money withdrawal from the brokerage service; exact instrument-specific liquidity still requires drill-level verification.

### Alfa-Investments

Alfa-Bank publicly offers online brokerage-account opening to individuals and maintains a current catalogue including `Альфа-Капитал Денежный рынок` / related money-market funds.

Brokerage assets are not bank deposits and are explicitly outside deposit-insurance protection. They therefore remain a separate reserve class rather than insured cash.

## 5. Tax baseline for S002

For a Russian tax resident, current FNS guidance states that income from purchase/sale and other disposal of digital currency is subject to NDFL at **13% up to the applicable 2.4 million RUB tax-base threshold and 15% on the excess**.

FNS also states that an individual receiving taxable income from sale of digital currency generally calculates/pays the tax and files 3-NDFL independently.

This S002 tax baseline applies to spot purchase/sale/disposal of digital currency. It does **not** automatically settle the tax characterization of perpetual/futures funding and R003 derivatives economics; that remains a separate tax-classification item before any live implementation.

At the current approximately USD 1,000 implementation-study size, tax rate optimization is not an architecture-selection driver, but complete cost-basis and transaction records are mandatory design requirements.

## 6. Mixed-currency interpretation at USD 1,000 scale

`Mixed` does not mean that S002 must hold a bank USD deposit or large stablecoin balance.

For this capital tier the base architecture should distinguish:

- **RUB survival purchasing power / domestic access** through insured Russian banking rails;
- **USD-equivalent crypto execution purchasing power** only where operationally required for the strategy/bridge;
- stablecoin exposure is bridge/execution exposure, not automatically survival reserve.

The architecture should avoid fragmenting approximately USD 1,000 across too many instruments merely to create cosmetic diversification.

## 7. S002-A decision

> **S002-A: PASS — ACCESS_PROFILE_FROZEN**

Frozen profile for the next stage:

- Russian citizen;
- Russian tax resident;
- Russia as KYC/residence jurisdiction;
- T-Bank + Alfa-Bank available;
- T/Alfa brokerage access realistically openable;
- Bybit existing account pending account-level verification;
- OKX eligible for account-opening/access verification;
- approximately USD 1,000 total implementation-study capital;
- mixed RUB / USD-equivalent objective;
- H1 = execution buffer only;
- H24 = next daily rebalance funding path;
- H72 = secondary/recovery path;
- no mandatory self-custody in the base design.

## 8. Next stage

Proceed to **S002-B — ELIGIBILITY_VERIFIED / concrete pathway matrix**.

Primary candidate pathways to test:

1. T-Bank -> Bybit P2P / supported RUB path;
2. Alfa-Bank -> Bybit P2P / supported RUB path;
3. T-Bank -> OKX P2P where account-level access permits;
4. Alfa-Bank -> OKX P2P where account-level access permits;
5. insured bank cash -> T-Investments money-market candidate -> bank cash -> crypto ingress;
6. insured bank cash -> Alfa-Investments money-market candidate -> bank cash -> crypto ingress.

Account-level product visibility and transfer behavior must be checked before any of these is promoted to a production-like pathway.

No active strategy, parameter, forward clock, venue record or G001/G002 conclusion is changed by this document.
