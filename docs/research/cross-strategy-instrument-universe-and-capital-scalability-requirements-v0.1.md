# Cross-Strategy Instrument Universe & Capital Scalability Requirements v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** cross-strategy implementation constraint; frozen before production sizing  
**Scope:** R003, R009, future convexity/carry candidates and portfolio assembly

## 1. Why this track exists

A strategy can look attractive in percentage-return space and still be unusable in practice if:

- required instruments are unavailable to the user's account/jurisdiction;
- minimum order size / lot step prevents accurate sleeve sizing;
- option contract granularity makes a tail hedge too coarse for a small account;
- margin/collateral requirements consume too much capital;
- fees dominate small trades;
- large notional creates material market impact or venue concentration.

Therefore every candidate must eventually have an explicit **capital implementation envelope**, not only a backtest CAGR/MaxDD.

## 2. Separate market primitives from packaged products

For strategy research, prefer transparent market primitives whose payoff and risk can be modeled directly.

Primary instrument classes to inventory on each venue:

1. spot assets;
2. spot margin / borrow where relevant;
3. linear USDT/USDC perpetuals;
4. inverse perpetuals;
5. dated/expiry futures;
6. listed options;
7. exchange-native spread combinations / RFQ execution where they can reduce two-leg execution risk;
8. venue cash/stablecoin balances only as operational collateral, not automatically as safe reserve.

Packaged yield/structured products, copy trading and black-box bots are not treated as primitive strategy instruments. They may be reviewed later, but their embedded counterparty/payoff risks must first be decomposed.

## 3. Potential role of each primitive

### Spot

- unlevered directional exposure;
- hedge leg for cash-and-carry;
- crisis deployment sleeve.

### Perpetuals

- funding carry;
- delta hedge / short exposure;
- capital-efficient directional exposure;
- introduces funding, liquidation, collateral and venue risks.

### Dated futures

- expiry-basis / cash-and-carry research without perpetual funding;
- deterministic expiry but introduces roll and delivery/basis convergence mechanics.

### Options

- bounded long-convexity / tail protection;
- potentially asymmetric payoff;
- introduces premium drag, IV surface, expiry/strike granularity and liquidity constraints.

### Margin borrowing

- can improve capital efficiency but creates borrowing-rate, recall/availability, liquidation and wrong-way risks;
- not a default enhancement merely to raise CAGR.

### Exchange-native spread/RFQ execution

- potentially useful for funding/basis/carry combinations and multi-leg execution;
- must not be assumed atomic or riskless without venue-specific execution documentation and testing;
- belongs to execution engineering, not alpha creation.

## 4. Current venue capability observations (2026-09-10)

Technical market-data/API documentation currently shows:

- Binance supports spot/margin, USD-M and COIN-M derivatives and listed crypto options; its instrument metadata exposes quantity/price filters including minimum quantity and step size.
- Bybit V5 exposes spot, linear, inverse and option instrument categories and explicitly documents USDT/USDC perpetual/futures products; its spread API also exposes combinations such as `FundingRateArb`, `CarryTrade`, `FutureSpread` and `PerpBasis`.
- OKX product documentation includes spot/margin, perpetual/expiry futures and options.

These are **technical product-universe observations**, not a guarantee that every product is legally/account-accessible to a particular user. Actual availability must be checked at implementation time for the user's account, jurisdiction and exchange entity.

## 5. Capital scalability is a first-class acceptance criterion

Do not assume continuous fractional sizing.

Every production candidate must be tested at multiple account sizes using actual venue constraints:

- minimum quantity;
- quantity step / contract multiplier;
- minimum notional;
- price tick;
- option contract unit;
- initial/maintenance margin;
- fee schedule and minimum effective fee drag;
- position/risk limits;
- maximum order quantity;
- borrow limits where applicable;
- liquidity / market impact.

Instrument limits may change over time, so production code must read current exchange metadata rather than hard-code historical examples.

## 6. Minimum viable capital

For a sleeve with target portfolio weight `w_i` and effective minimum executable notional `Nmin_i`, a first-order feasibility bound is:

`C_min_i ~= Nmin_i / w_i`

The portfolio-level minimum is at least the maximum of the required sleeves' bounds, adjusted upward for:

- two-leg hedge rounding mismatch;
- option premium/contract granularity;
- required futures collateral headroom;
- fees and execution buffer;
- reserve that must remain uncommitted.

This is only a first-order bound. A strategy should not be called small-account compatible until a discrete-order simulation verifies it.

## 7. Quantization / hedge-error test

Historical engines often use continuous quantities. Production feasibility must round every trade exactly to venue rules.

Report after rounding:

- target sleeve weight vs executable sleeve weight;
- residual net delta / hedge mismatch;
- uninvested residual cash;
- fee drag as % of NAV;
- margin buffer;
- skipped trades because the target is below minimum size.

For R003 this is especially important because equal-BTC spot/perpetual quantities may not remain exactly equal after independent venue lot-step rounding.

For R009 this is especially important because small 2.5-percentage-point crisis tranches can become non-executable on a very small account.

## 8. Do not force one implementation across every account size

The economic strategy may remain the same, but the implementation can have distinct prospectively defined capital tiers.

Example conceptual tiers:

- **micro/small:** only components that can be executed accurately after minimum-size and fee constraints;
- **standard:** full intended set of liquid primitives;
- **large/institutional:** same economic logic but with explicit market-impact, order-splitting, venue-capacity and custody diversification controls.

If a small tier cannot implement a required component, it must be labeled a separate implementation profile/candidate rather than silently claiming equivalence to the full strategy.

## 9. Large-capital capacity ceiling

Scalability is two-sided. Large capital can fail even when small capital works.

Future capacity analysis must include:

- order-book depth and expected slippage at target notional;
- percentage of hourly/daily traded volume;
- open interest and venue position/risk limits;
- funding/basis edge decay caused by own execution;
- ability to exit both legs in stress;
- concentration by venue/collateral/custodian.

A candidate therefore needs both:

- **minimum viable capital**;
- **maximum prudent capacity**.

## 10. Required capital-envelope outputs before production

For each candidate implementation, report at least:

- minimum mechanically executable capital;
- minimum economically sensible capital after fees;
- account-size grid (for example logarithmic sizes, chosen prospectively);
- discrete realized weights after venue rounding;
- residual hedge error;
- expected fees/slippage by capital size;
- margin/collateral headroom;
- skipped-trade frequency;
- estimated capacity ceiling and its limiting factor.

Do not select the account-size grid after seeing which sizes look best.

## 11. Research-order implications

This track does not justify changing frozen R003 or R009 forward rules.

Immediate use:

- maintain an inventory of primitives and execution tools that may support future architectures;
- ensure Safe-Sleeve S002 and future portfolio assembly are capital-size aware;
- pre-specify a later **Capital Granularity & Capacity Audit** before production promotion.

Do not add leverage, options, dated futures or spread products to an existing candidate merely because they are available. A new instrument must solve a defined economic/risk problem and be introduced under a separate frozen protocol.

## 12. Core design principle

Target architecture:

> same economic logic across capital sizes where mechanically possible; explicit tier boundaries where it is not.

The system should be designed to avoid requiring a six-figure account merely to reproduce its core risk logic, but it must also be honest when exchange lot sizes, options granularity or margin requirements make a particular implementation infeasible for a small account.
