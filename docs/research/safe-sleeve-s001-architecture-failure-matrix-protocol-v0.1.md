# Safe-Sleeve S001 — Architecture & Failure-Matrix Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** pre-result frozen architecture study  
**Research posture:** survival-first; availability-adjusted capital before yield optimization

## 1. Objective

Define what a genuinely defensive / dry-powder layer must do for R009, R003 and future convexity work before selecting specific products, custodians or allocation percentages.

Primary question:

> Which safe-sleeve architecture classes preserve the greatest usable capital across market, venue, collateral and access failures, while retaining enough mobility to deploy during stress?

This is not a product recommendation and does not authorize live allocation.

## 2. Core correction

Nominal NAV is insufficient.

A dollar that still exists but cannot be accessed during the crisis is not equivalent to executable dry powder.

S001 therefore evaluates both:

- **capital survival** — how much value remains;
- **capital availability** — how much value can plausibly become executable within specified time horizons.

## 3. Availability horizons

Freeze three deployment horizons:

- **H1 = 1 hour** — immediate execution buffer;
- **H24 = 24 hours** — next-day crisis deployability;
- **H72 = 72 hours** — delayed but still tactically useful reserve.

No attempt is made to optimize these horizons after results.

## 4. Architecture classes to compare

Compare at least these classes without assigning portfolio percentages:

### A. Single-venue crypto cash

- USDT / cash-like balance held primarily at the trading venue.

### B. Off-venue stablecoin reserve

- stablecoin held away from the primary trading venue, potentially self-custodied or at a separate custodian.

### C. Insured-bank USD reserve

- USD deposits at an insured bank, subject to applicable insurance limits and transfer/access mechanics.

### D. Short Treasury reserve

- short-duration U.S. Treasury bills held through a broker/dealer or equivalent commercial book-entry channel.
- TreasuryDirect-held bills must be treated separately where mobility differs.

### E. Government money-market reserve

- government money-market fund / equivalent short-government-cash vehicle held off the crypto venue.

### F. Multi-domain layered reserve

A conceptual architecture containing distinct failure domains:

- off-venue reserve;
- execution buffer;
- crisis-deployment bridge;
- derivatives collateral.

No percentages are selected in S001.

## 5. Failure scenarios

Evaluate each architecture under the following frozen scenario families:

1. **BTC_CRASH_ONLY** — BTC falls sharply but venue/collateral systems continue functioning.
2. **PRIMARY_VENUE_WITHDRAWAL_FREEZE** — trading venue remains quoted/trading but withdrawals/transfers unavailable.
3. **PRIMARY_VENUE_INSOLVENCY_OR_LONG_FREEZE** — severe impairment of venue-held assets.
4. **STABLECOIN_MODERATE_DEPEG** — stablecoin loses 5% versus USD.
5. **STABLECOIN_SEVERE_IMPAIRMENT** — stablecoin loses 20% versus USD or redemption becomes materially impaired.
6. **BANK_OR_BROKER_ACCESS_DELAY** — off-venue fiat/securities inaccessible for 24-72h.
7. **CHAIN_CONGESTION_OR_TRANSFER_HALT** — on-chain transfer unavailable or materially delayed.
8. **CRYPTO_CRASH_PLUS_VENUE_FREEZE** — market stress and primary venue access failure jointly occur.
9. **CRYPTO_CRASH_PLUS_STABLECOIN_IMPAIRMENT** — market stress and collateral impairment jointly occur.
10. **CRYPTO_CRASH_PLUS_VENUE_FREEZE_PLUS_STABLECOIN_IMPAIRMENT** — combined wrong-way stress.

These are research stress cases, not probability forecasts.

## 6. Required output matrix

For every architecture x scenario report qualitatively or quantitatively where defensible:

- value survival haircut;
- H1 availability;
- H24 availability;
- H72 availability;
- principal failure domain;
- whether failure is correlated with crypto stress;
- whether capital can still reach a functioning execution venue;
- whether the architecture creates a new single point of failure.

## 7. Availability-adjusted capital concept

S001 introduces a portfolio-engineering metric for later quantitative stages:

`availability_adjusted_capital(H) = sum_i market_value_i * survival_haircut_i * accessibility_i(H)`

where accessibility is a scenario-specific fraction in [0,1].

S001 may use ordinal scores where exact fractions would create false precision. Numerical probabilities of failure are explicitly prohibited unless sourced and defensible.

## 8. Required common-mode map

Create a dependency graph covering at least:

- trading venue;
- stablecoin issuer/redemption mechanism;
- blockchain/bridge;
- bank;
- broker/custodian;
- Treasury/government issuer;
- internet/API/account access;
- legal/jurisdictional access.

R003 collateral and R009 execution capital must not be counted as independent merely because their P&L sources differ.

## 9. Yield treatment

Yield is deliberately secondary in S001.

For each architecture record only:

- broad yield source;
- whether yield is floating or locked;
- whether earning yield changes liquidity or failure domain.

Do not rank architectures primarily by APY.

The existing dynamic 13-week Treasury benchmark remains an opportunity-cost reference, not a production allocation decision.

## 10. Important instrument-specific distinctions

Do not collapse the following into one category:

- bank deposit vs money-market mutual fund;
- government MMF vs prime MMF;
- broker-held Treasury bill vs TreasuryDirect-held Treasury bill;
- self-custodied stablecoin vs exchange-held stablecoin;
- USDT/USDC or other stablecoins as interchangeable cash.

Each has different access, insurance, redemption and common-mode properties.

## 11. Jurisdiction/tax rule

S001 remains universal and pre-personalized.

Do not assume the user's final tax jurisdiction, banking access, broker eligibility or base-currency liabilities.

A later S002 implementation stage must incorporate actual jurisdiction/account access before producing specific product allocations or after-tax comparisons.

Research accounting base unit remains USD because R003/R009 and the Treasury hurdle are USD-denominated.

## 12. S001 decision outputs

S001 does not return PASS/FAIL for a product.

It returns:

- **ARCHITECTURE_PREFERRED_FOR_S002** — one or more architecture classes dominate on survival/common-mode separation while remaining sufficiently mobile;
- **ARCHITECTURE_TRADEOFF_UNRESOLVED** — no architecture clearly dominates and user-specific access is required;
- **ARCHITECTURE_UNSAFE** — an architecture should not be considered the safe sleeve because it shares the primary crypto failure domain.

## 13. Expected next stages

### S002 — Instrument / custodian due diligence

Only after S001:

- identify accessible banks/brokers/custodians/funds;
- verify insurance/custody structure;
- measure practical transfer/settlement latency;
- compare current net yields and fees;
- incorporate tax/jurisdiction constraints.

### S003 — Capital sizing

Only after forward evidence and S002 operational facts exist:

- choose off-venue reserve size;
- choose execution buffer size;
- choose derivatives collateral budget;
- choose crisis-deployment bridge.

No percentage optimization in S001.

## 14. Anti-overfitting / anti-false-precision rule

Do not invent failure probabilities, recovery values, allocation percentages or transfer times simply to make the matrix numerical.

Prefer explicit unknowns and ordinal resilience rankings to unsupported precision.
