# BotMarketplace — Deployment Architecture Strategic Route v1.0

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** strategic route frozen; implementation gated by strategy evidence  
**Scope:** long-term deployment, replication, distribution and monetization architecture for systematic trading strategies

## 1. Executive decision

The long-term strategic core of BotMarketplace is **not native exchange copy trading** and is **not pooled custody of client capital**.

The preferred core is:

> **non-custodial server-side strategy execution + target-state portfolio replication into user-owned exchange accounts through exchange APIs / approved broker-OAuth integrations.**

Native copy trading remains an optional distribution/track-record channel. Pooled/fund structures remain a later business/legal branch.

This architecture does not remove exchange rules, market microstructure, jurisdictional restrictions or API limits. It only removes unnecessary dependence on the feature set of an exchange's built-in bot/copy-trading product.

## 2. Why this route survives critical review

### 2.1 Advantages retained

- multi-leg strategies can be expressed even when native copy trading cannot represent them as one product;
- strategy logic remains under BotMarketplace control;
- users can keep capital in their own exchange accounts;
- position sizing can be account-specific;
- exchange adapters can normalize minQty, qtyStep, tickSize, margin and order semantics;
- multiple venues can be supported without rewriting the economic strategy core;
- a broker/OAuth integration can later improve onboarding and key security;
- business monetization does not require pooling client money.

### 2.2 Critical limitations explicitly accepted

Direct API execution does **not** bypass:

- product availability by country/account type;
- KYC/eligibility rules;
- exchange maintenance/liquidation rules;
- API rate limits;
- position and order limits;
- minimum order/contract granularity;
- exchange outage/insolvency/withdrawal risk;
- legal/regulatory requirements for managing or directing third-party accounts.

The platform must treat these as first-class constraints, not implementation details.

## 3. Important architectural correction: replicate TARGETS, not MASTER ORDERS

Do not architect external-account replication as literal order copying.

A master order such as "buy 0.01 BTC" is not portable across accounts with different NAV, balances, minQty, current positions or risk limits.

The canonical object emitted by a strategy/portfolio engine should instead be a **target state**, for example:

```text
strategyVersion = R003-v0.1
accountExposureTarget:
  BTC_SPOT = +0.50 NAV
  BTC_PERP_DELTA = -same BTC quantity
  rebalancePolicy = month-end UTC
```

For every account, the replication layer must independently convert that target into feasible quantities after:

- account NAV and available balance;
- venue/product availability;
- minQty/minNotional/qtyStep/tickSize;
- margin headroom;
- per-account risk caps;
- existing positions/open orders;
- slippage and capacity constraints.

This prevents master-account size from becoming an accidental strategy parameter.

## 4. Canonical execution architecture

```text
Strategy Definition / Version
        ↓
Strategy Intent Engine
        ↓
Portfolio Target Engine
        ↓
Account Feasibility + Capital Scaling
        ↓
Pre-Trade Risk Gate
        ↓
Venue/Product Adapter
        ↓
Order Execution Manager
        ↓
Exchange
        ↓
Fills / Positions / Balances
        ↓
Reconciliation + Audit + Monitoring
```

The layers must have explicit contracts and be independently testable.

## 5. Exchange abstraction rule

Use a **canonical economic intent** plus venue-specific market semantics.

Do not pretend all venues are interchangeable. Funding schedules, margin engines, mark prices, contract units and product availability can differ enough to change strategy economics.

Therefore:

- exchange adapters normalize mechanics;
- venue models expose venue-specific economics;
- a strategy version must declare which venue/product assumptions are allowed;
- changing the venue of an economically venue-dependent strategy such as funding carry is a separately validated strategy instance, not silent smart routing.

General smart-order routing is deferred until venue equivalence has been demonstrated for the relevant strategy.

## 6. Failure containment is mandatory before multi-user fan-out

A centralized platform creates a new catastrophic common-mode risk: one software bug can send the wrong order to every connected account.

Before any multi-user live execution, require:

- deterministic idempotency keys for every intent/order;
- reconciliation after restart, timeout and reconnect;
- per-account risk caps and kill switch;
- per-strategy global exposure cap;
- venue-level order-rate budget;
- global fan-out circuit breaker;
- maximum number/value of accounts allowed in one execution wave;
- canary account(s) before broad rollout of a new strategy/runtime version;
- shadow/dry-run mode on every production release;
- immutable strategy/runtime version identifiers in each intent;
- complete audit trail from strategy target to final fills;
- rollback/pause procedure independent of the strategy engine.

No single strategy process should possess unrestricted ability to broadcast arbitrary orders to all accounts.

## 7. Credential and authorization security

Preferred authorization hierarchy:

1. exchange-approved OAuth/broker authorization where available;
2. IP-whitelisted trade-only API credentials;
3. manually pasted API credentials only as an early bootstrap path.

Default principle:

> **read + required trade permissions; no withdrawal permission wherever the venue architecture allows it.**

Also require:

- encrypted-at-rest secrets;
- secrets isolated from application/database logs;
- key rotation/revocation workflow;
- per-venue permission validation at connection time;
- IP allowlisting where supported;
- explicit rejection of over-privileged keys where feasible.

## 8. Distribution and capital are separate questions

Do not conflate:

- growing capital controlled by one legal vehicle/account;
- growing user AUM connected to the platform;
- growing BotMarketplace revenue.

BotMarketplace can potentially monetize user-owned accounts through software subscriptions, approved broker/affiliate economics and, where legally/platform-permitted, strategy/performance-linked fees without pooling client money.

Increasing connected AUM is not automatically beneficial. Every strategy has finite capacity. New capital must be refused/throttled if expected market impact, slippage, venue concentration or operational risk would materially degrade the edge.

## 9. Deployment channels — ranked by strategic role

### Channel A — own-account direct API

**Role:** first real-money engineering pilot after research gates.  
**Priority:** highest for implementation validation.

Advantages: smallest legal/product surface, exact control, real execution data.

### Channel B — user-owned accounts through BotMarketplace API/OAuth/broker integration

**Role:** long-term core distribution architecture.  
**Priority:** highest for scalable product architecture.

Users keep exchange accounts; BotMarketplace computes target positions and executes authorized trades.

### Channel C — native exchange copy trading

**Role:** optional discovery, public track record and distribution channel.  
**Priority:** opportunistic/secondary.

Do not alter a validated strategy merely to fit native copy-trading limitations.

### Channel D — signal-only product

**Role:** fallback/low-execution-responsibility offering where direct execution is unavailable or undesirable.

Its performance must not be assumed equivalent to direct execution because user delay/slippage can be material.

### Channel E — pooled fund / managed vehicle / custodial AUM

**Role:** later optional business model.  
**Priority:** deferred.

Requires explicit legal, custody, administration, valuation, investor-rights and operational analysis before use.

## 10. Broker-program evidence relevant to architecture

Current official venue documentation supports the plausibility of the long-term route:

- Bybit API Broker Program explicitly lists trading platforms, trading strategies, trading bots, asset management and social trading as supported broker business types; its documented supported products include spot, perpetuals, expiry products and options.
- Bybit documents broker OAuth onboarding and broker-specific API order tagging.
- OKX Fully Disclosed Broker documentation explicitly supports API and OAuth broker models for trading aggregators, trading-bot platforms, technical providers, asset-management platforms and social-trading platforms; it supports trade/read permissions and third-party IP whitelisting.
- Binance Exchange Link exposes broker subaccounts and subaccount API permissions including spot, margin and futures trading.

These programs demonstrate technical/business pathways, but they do not by themselves establish that BotMarketplace is legally eligible in every target jurisdiction or for every fee model.

## 11. Compliance gate

Before BotMarketplace executes trades for external users or charges performance/management-style compensation, require a separate jurisdiction-specific legal/compliance review.

The architecture must not assume that "non-custodial" automatically means "unregulated".

The product should be designed so compliance restrictions can disable:

- specific jurisdictions;
- specific products/derivatives;
- performance-fee models;
- external-account automation;
- pooled/custodial features;

without rewriting the strategy engine.

## 12. Capital-size rule

The previously frozen Capital Implementation Envelope remains mandatory.

A strategy approaching live use must publish:

- minimum mechanically executable capital;
- minimum economically sensible capital;
- residual target error after rounding;
- expected fees/slippage by account tier;
- margin headroom;
- maximum prudent capacity;
- behavior when a required sleeve falls below venue minimum size.

One strategy may have multiple prospectively defined implementation tiers, but tiers may not be invented after seeing disappointing live results.

## 13. Monetization principle

Do not optimize the platform around attracting third-party capital into the founder's own account.

Preferred early monetization options to evaluate later:

- SaaS/subscription for automation and analytics;
- approved exchange broker rebates/revenue share;
- optional native-copy revenue where compatible;
- performance-linked pricing only after legal/platform approval;
- enterprise/private strategy deployment later.

This reduces the pressure to take custody or artificially increase strategy risk merely to make an investable pooled product attractive.

## 14. What NOT to build now

The 2026-09 research pivot remains in force: strategy validation precedes broad platform feature development.

Therefore do not yet build:

- multi-exchange smart routing;
- pooled custody/fund infrastructure;
- mass multi-user live fan-out;
- performance-fee billing;
- broad strategy marketplace automation;
- production secret vaulting at full scale.

Only freeze interfaces/requirements needed to avoid architectural dead ends while R009/R003 forward evidence and adjacent falsification studies continue.

## 15. Immediate execution sequence

1. Keep R009-E002 and R003-E003 forward clocks unchanged.
2. Complete Safe-Sleeve S002 before production allocation design.
3. Run precommitted Bybit R003 replication.
4. Run unchanged-rule ETH falsification for R009.
5. For any surviving candidate, run Capital Granularity & Capacity Audit.
6. Then build **own-account direct-API execution MVP** on one validated venue with shadow mode first and tiny live capital second.
7. Only after the own-account runtime is reliable, implement user-owned-account replication through approved API/OAuth/broker integration.
8. Native copy trading remains optional; pooled/custodial AUM remains deferred.

## 16. Decision

**Strategic route: ACCEPTED WITH CONTROLS.**

The strongest long-term architecture is direct, non-custodial, target-state API execution with exchange adapters and broker/OAuth integration, but only if failure containment, capital feasibility, security and compliance gates are treated as core product requirements.