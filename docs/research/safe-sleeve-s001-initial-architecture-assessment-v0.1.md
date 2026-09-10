# Safe-Sleeve S001 — Initial Architecture Assessment v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** initial universal architecture result; no user-specific product allocation
**Protocol:** `docs/research/safe-sleeve-s001-architecture-failure-matrix-protocol-v0.1.md`

## 1. Executive result

Preliminary S001 conclusion:

> **ARCHITECTURE_PREFERRED_FOR_S002: multi-domain layered reserve**

A single instrument does not dominate simultaneously on survival, immediate crypto deployability, venue independence and yield.

The strongest architecture class is therefore a layered reserve with separate failure domains rather than one all-purpose cash substitute.

No allocation percentages are selected at S001.

## 2. Core architectural distinction

The safe layer should ultimately distinguish:

- **off-venue survival reserve** — primary objective is capital preservation outside the crypto venue/collateral failure domain;
- **execution buffer** — deliberately small capital already at the trading venue for ordinary operations;
- **crisis-deployment bridge** — capital that can reach a functioning venue rapidly during stress;
- **derivatives collateral** — capital explicitly exposed to derivatives-venue and collateral mechanics.

R003 futures collateral belongs to the fourth bucket, not the first.

## 3. Initial architecture matrix

Ratings are ordinal and intentionally avoid unsupported failure probabilities.

| Architecture | Crypto-venue independence | Stablecoin independence | H1 mobility | H24/H72 mobility | Principal weakness | S001 status |
|---|---|---|---|---|---|---|
| Single-venue USDT/cash | Low | Low/Medium | High if venue works | Low if venue frozen | catastrophic common-mode concentration | ARCHITECTURE_UNSAFE as sole safe sleeve |
| Off-venue stablecoin | High vs venue | Low | Medium/High if chain works | Medium/High | issuer/depeg/chain wrong-way risk | useful bridge, not sole survival reserve |
| Insured-bank USD | High | High | Low/Medium | Medium/High subject to transfer rails | transfer/access timing; insurance limits | strong survival component |
| Broker-held short T-bills | High | High | Low outside market/access hours | Medium/High | broker/access/settlement latency | strong survival component |
| TreasuryDirect-held T-bills | High | High | Low | Low/Medium for crisis deployment | 45-day transfer/sale hold on newly purchased marketables | poor immediate bridge; strong hold-to-maturity reserve |
| Government MMF | High | High | Low/Medium | Medium/High on business days | fund/broker access; not FDIC insured | plausible liquid off-venue component |
| Multi-domain layered reserve | High if designed correctly | High if stablecoin share bounded | High through execution buffer | High through off-venue reserve + bridge | complexity / operational discipline | PREFERRED FOR S002 |

## 4. Why all-on-exchange fails the safe-sleeve test

It maximizes immediate deployability only in the scenario where the venue remains functional.

The exact scenario that creates the intended opportunity can coincide with:

- withdrawal suspension;
- venue insolvency or long access interruption;
- stablecoin/collateral impairment;
- infrastructure congestion.

Therefore capital already committed to the same crypto failure domain cannot be counted as fully independent dry powder.

## 5. Why stablecoin self-custody is useful but insufficient

Moving a stablecoin off the trading venue removes one counterparty layer but does not remove:

- issuer/redemption risk;
- depeg risk;
- blockchain congestion;
- possible wrong-way correlation with a crypto-system crisis.

It is better classified as a potential **mobility bridge** than as the entire survival reserve.

## 6. Why short Treasuries are not automatically perfect crisis cash

Short U.S. Treasury bills are high-quality government obligations and exist in maturities from 4 to 52 weeks.

But custody route matters.

TreasuryDirect states that newly purchased marketable securities must generally remain in TreasuryDirect for 45 days before they can be sold or transferred to a bank/broker/dealer. Therefore TreasuryDirect-held bills and broker-held bills have materially different crisis mobility.

For this project, safety and mobility must be modeled separately.

## 7. Why bank deposits are not identical to securities cash

For an FDIC-insured U.S. bank, the standard insurance amount is $250,000 per depositor, per insured bank, per ownership category.

This is strong nominal protection within the insured structure but does not guarantee instant transfer to a crypto venue during every operational stress scenario.

Future sizing must therefore consider both insurance structure and transfer rails.

## 8. Why government MMFs are not bank deposits

Government money-market funds invest overwhelmingly in cash/government securities/fully collateralized government repos and are designed as liquid cash-management products, but they are mutual funds rather than FDIC-insured bank deposits.

They can have fund/broker access risks and money-market funds can employ liquidity-management tools in stress.

Therefore they are a distinct architecture class, not simply "insured cash with yield."

## 9. Preferred architecture logic

The current preferred S002 design class is not a specific product but a **failure-domain barbell**:

- substantial survival capital outside the primary crypto venue and stablecoin issuer failure domain;
- only operationally necessary capital at the derivatives/trading venue;
- a separate bridge for rapid crisis deployment;
- no assumption that R003 collateral is safe reserve;
- no assumption that one custodian or one stablecoin should hold all liquidity.

This creates redundancy at the infrastructure level, not just diversification of trading signals.

## 10. Key unresolved questions for S002

Before product-level recommendations require:

- user's actual legal/tax jurisdiction and base-currency liabilities;
- accessible banks/brokers/custodians;
- transfer limits and settlement windows;
- whether stablecoin self-custody is operationally acceptable;
- target crisis-deployment speed;
- expected portfolio size, because insurance/counterparty concentration changes with scale;
- after-tax yield and fees.

No answer is assumed at S001.

## 11. Current implications for R003 and R009

- R003 can remain a forward carry candidate, but its exchange collateral is not counted as the safe sleeve.
- R009 can remain a forward directional candidate, but future implementation must not require the entire dry-powder reserve to sit on Binance.
- Low P&L correlation between R003 and R009 does not remove shared venue/collateral failure risk.
- Future combined portfolio analysis must include availability-adjusted capital in joint stress scenarios.

## 12. Next action

Proceed to S002 only after forward infrastructure is technically initialized.

S002 should be user-access aware and should compare concrete implementation pathways rather than generic product APYs.

## Sources used for factual architecture distinctions

- FDIC, Deposit Insurance at a Glance: standard coverage $250,000 per depositor, per insured bank, per ownership category.
- U.S. Treasury / TreasuryDirect, Treasury Bills and Selling a Treasury Marketable Security: T-bill terms and TreasuryDirect 45-day transfer/sale hold.
- SEC Investor.gov, Money Market Funds Investor Bulletin: structure, government-MMF asset rules, lack of FDIC insurance and stress/liquidity considerations.
