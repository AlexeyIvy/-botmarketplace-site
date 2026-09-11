# Safe-Sleeve S002-B — Eligibility & Pathway Screen v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** **PARTIAL — ACCOUNT_LEVEL_CHECK_REQUIRED**  
**Frozen access profile:** `docs/research/safe-sleeve-s002-user-access-profile-v0.2.md`

## 1. Executive result

For a Russian tax resident / Russian KYC profile with T-Bank, Alfa-Bank and approximately USD 1,000 equivalent total implementation-study capital, the strongest current base architecture is still:

> **INSURED RUB SURVIVAL CASH + MINIMAL VENUE BUFFER + AT LEAST TWO INDEPENDENT CRYPTO INGRESS CANDIDATES**

Money-market funds are viable secondary reserve candidates, but at the current capital tier they should not be added merely for yield before transfer-path drills demonstrate that the added layer improves the total system after fees, settlement latency and operational complexity.

A permanent large stablecoin balance is not required for the base architecture.

No real-money deployment is authorized.

## 2. Pathway A — T-Bank -> Bybit

### Eligibility screen

- user already has T-Bank;
- user already created a Bybit account;
- current Bybit restricted-jurisdiction documentation does not generally exclude the Russian Federation;
- Bybit fiat documentation allows Russian-KYC users RUB under the general fiat service while restricting USD SWIFT;
- Bybit P2P requires identity verification (KYC).

### Main risks

- user's current Bybit KYC/product status is not yet confirmed;
- P2P is a third-party transfer path rather than a guaranteed bank-to-exchange settlement rail;
- Russian banks must monitor transfers under anti-fraud / AML rules;
- T-Bank states that transfers can be restricted under 115-FZ/161-FZ and that a 115-FZ verification may take up to approximately two days;
- Bank of Russia rules can require a two-day suspension for certain suspicious-recipient cases.

### Current classification

`ELIGIBLE_CANDIDATE / NOT H1-GUARANTEED / ACCOUNT_CHECK_REQUIRED`

This pathway can plausibly serve H24/H72 under normal operation, but S002 must not promise H1 or even deterministic H24 access before an operational drill.

## 3. Pathway B — Alfa-Bank -> Bybit

### Eligibility screen

- user already has Alfa-Bank;
- same Bybit jurisdiction / KYC conditions as Pathway A;
- Alfa-Bank is an independent bank failure/rail domain relative to T-Bank.

### Main risks

- Bybit account-level status still unresolved;
- P2P counterparty / AML / fraud-control risk remains;
- bank transfer restrictions can occur under 115-FZ/161-FZ and related risk controls.

### Current classification

`ELIGIBLE_CANDIDATE / SECOND_BANK_REDUNDANCY / ACCOUNT_CHECK_REQUIRED`

For approximately USD 1,000, the value of Alfa-Bank is primarily rail redundancy rather than deposit-insurance capacity.

## 4. Pathway C — T-Bank -> OKX

### Eligibility screen

- OKX compliance materials do not identify Russia as completely unsupported, but fiat-payment services for Russia are specifically restricted;
- OKX P2P rules require identity verification and payment accounts in the verified user's own name;
- OKX documents risk-control/account restrictions that can temporarily prevent trading or withdrawals.

### Main risks

- no user OKX account is yet confirmed;
- fiat services cannot be assumed;
- P2P may trigger platform risk controls including T+N-style restrictions;
- bank-side anti-fraud/AML controls remain.

### Current classification

`ELIGIBLE_BACKUP_CANDIDATE / NOT PRIMARY H1 RAIL`

OKX is useful primarily as an independent venue/bridge failure domain, not as a reason to split trading capital across venues before strategy evidence requires it.

## 5. Pathway D — Alfa-Bank -> OKX

Same core eligibility and OKX limitations as Pathway C, with Alfa-Bank providing an independent domestic bank rail.

### Current classification

`ELIGIBLE_BACKUP_CANDIDATE / DUAL-DOMAIN REDUNDANCY`

This route becomes operationally valuable only if the account-level OKX service set is confirmed and a controlled transfer drill succeeds.

## 6. Pathway E — T-Bank -> T-Investments money market -> T-Bank -> crypto ingress

### Eligibility screen

T-Investments publicly offers online brokerage-account opening with passport/phone and maintains money-market fund products. T-Bank also states that:

- brokerage opening is free;
- cash withdrawal from the brokerage service can be available 24/7;
- many supported securities have extended/weekend trading;
- money-market fund TMON is offered as a RUB money-market instrument.

### Safe-sleeve interpretation

A money-market fund is **not insured bank cash**. It adds fund, market, broker and settlement mechanics.

### Current classification

`VIABLE SECONDARY RESERVE / NOT BASE REQUIREMENT AT USD 1,000`

At approximately USD 1,000 total capital, the incremental absolute yield benefit must be weighed against an extra operational layer. S002 should not add TMON merely because its quoted yield exceeds a bank balance.

Promotion condition: demonstrate reliable liquidation -> bank cash -> crypto ingress within the required H24/H72 window under a controlled drill.

## 7. Pathway F — Alfa-Bank -> Alfa-Investments money market -> Alfa-Bank -> crypto ingress

### Eligibility screen

Alfa-Bank publicly offers online brokerage opening for individuals and lists `Альфа-Капитал Денежный рынок` / related money-market products in its investment catalogue.

Alfa's own materials note that brokerage/investment assets are not bank deposits and are not covered by deposit insurance.

### Current classification

`VIABLE SECONDARY RESERVE / ACCOUNT_AND_SETTLEMENT_DRILL_REQUIRED`

It is an alternative failure domain to T-Investments, but there is no reason at approximately USD 1,000 to fund both money-market ecosystems simultaneously before a measured operational need exists.

## 8. New Russian regulated-crypto intermediary branch

A new Russian legal regime for cryptocurrency circulation entered into force on 2026-09-01.

Bank of Russia materials state that non-qualified investors may purchase the most liquid cryptocurrencies through regulated intermediaries after testing and subject to a 300,000 RUB annual limit per intermediary. The infrastructure is in transition and includes existing financial institutions and new crypto exchanges / digital repositories.

### S002 classification

`WATCH / POTENTIAL FUTURE BRIDGE / NOT YET BASE PATH`

At the current approximately USD 1,000 capital tier, the statutory amount is not the issue. The issue is whether an actually registered, user-accessible intermediary currently provides the required asset, custody, withdrawal and API/deployment behavior.

Until concrete providers and transfer rules are verified, this branch must not replace Bybit/OKX research.

## 9. Banking failure-domain result

Bank of Russia currently states ordinary insured accounts/deposits are covered up to 1.4 million RUB per depositor per bank.

At approximately USD 1,000 total capital, insurance capacity is therefore far above the project scale.

The reason to keep both T-Bank and Alfa-Bank available is **operational redundancy**, not insurance optimization:

- one bank can be under transfer review or technical outage;
- one payment counterparty may support one bank but not the other;
- a second bank reduces single-rail dependence.

S002 does not require a 50/50 bank split.

## 10. Tax result relevant to the pathway design

Current FNS guidance specifically states that income of individuals from purchase/sale or other disposal of digital currency is taxed at 13%, with 15% on the portion above 2.4 million RUB, and the individual generally calculates/pays the tax and files 3-NDFL.

For S002 this creates an operational requirement:

- preserve exchange trade history;
- preserve P2P/bank payment evidence;
- preserve acquisition cost and disposal proceeds;
- record fees and timestamps;
- do not rely on a venue remaining permanently available as the only tax record store.

R003 perpetual/funding tax treatment remains a separate due-diligence item and is not inferred from spot crypto rules.

## 11. USD 1,000 architecture implication

At this capital tier, S002 should optimize for **simplicity and recoverability**, not maximum number of products.

Current preferred implementation class for later operational testing:

1. one primary insured-bank cash location;
2. second existing bank maintained as an independent transfer rail;
3. minimal execution balance only after a venue is account-verified;
4. Bybit as the first account-level execution/bridge check because an account already exists;
5. OKX as the independent venue/bridge candidate, not as a prettier-return substitute;
6. money-market fund layer optional and deferred until its H24/H72 value is demonstrated;
7. self-custody stablecoin remains optional, not part of the base design.

This is a pathway hierarchy, not a live allocation.

## 12. Remaining S002-B blockers

Only account-level facts remain before stronger eligibility status is possible:

### Bybit account check

Confirm inside the existing account:

- identity verification status;
- country/residence shown as Russia;
- Spot visible/enabled;
- Derivatives / Perpetual visible/enabled;
- P2P visible/enabled;
- RUB appears as a P2P/fiat option;
- crypto withdrawal is enabled after required security setup.

### OKX account check

If/when opened:

- identity verification can be completed with Russia as country/residence;
- Spot / Derivatives / P2P product visibility;
- RUB P2P visibility;
- withdrawal availability and any cooling/risk-control restrictions shown to the account.

No deposit or trade is needed for these checks.

## 13. S002-B status

> **S002-B: PARTIAL — OFFICIAL ELIGIBILITY SCREEN PASSED FOR RESEARCH; ACCOUNT-LEVEL VERIFICATION STILL REQUIRED**

The current evidence is sufficient to keep Bybit, OKX, T-Bank, Alfa-Bank, T-Investments and Alfa-Investments in the candidate matrix. It is not sufficient to declare any crypto ingress rail deterministic or production-ready.

No active strategy, parameter, forward clock, venue-forward record, capital-tier conclusion or real-money status is changed.
