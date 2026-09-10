# R009 / R003 / Safe-Sleeve / Deployment Near-Term Research Roadmap v1.7

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** forward evidence priority; deployment strategic route frozen; no broad platform build yet  
**Research posture:** falsification-first, anti-cherry-picking, opportunity-cost aware, capital-scalability aware, common-mode-risk aware

## 1. Active evidence clocks remain unchanged

### R009-E002

- true forward directional/state-dependent beta candidate;
- original inception and frozen rules unchanged;
- no reset from platform architecture work.

### R003-E003

- true forward carry candidate;
- fixed decision boundary 2026-09-10 12:00 UTC;
- 50/50 fully funded equal-BTC construction unchanged;
- Treasury fixed + causal dynamic hurdle tracking unchanged.

### Original BTC SMA120 forward

Continue independently and unchanged.

## 2. Deployment strategic route now frozen

Canonical architecture document:

`docs/platform/botmarketplace-deployment-architecture-strategic-route-v1.0.md`

Decision:

> **Direct non-custodial target-state API execution is the long-term core; native copy trading is optional distribution; pooled/custodial AUM is deferred.**

This route is accepted only with explicit controls for credentials, fan-out failures, exchange mechanics, capacity and compliance.

## 3. Key correction: target-state replication, not order copying

Future BotMarketplace multi-account execution must replicate desired portfolio state rather than literal master orders.

Per account the runtime must calculate feasible quantities from:

- NAV and free balance;
- current positions/orders;
- venue/product availability;
- minQty/minNotional/qtyStep/tickSize;
- margin headroom;
- account-specific risk caps;
- slippage/capacity constraints.

This allows the same strategy logic to serve small and large accounts without making master-account size an accidental strategy parameter.

## 4. Key correction: direct API creates a new common-mode software risk

A central BotMarketplace runtime can cause correlated losses across many accounts if a bug fans out bad orders.

Before any external-account automation require:

- idempotent intents/orders;
- restart/reconnect reconciliation;
- per-account kill switches;
- global fan-out circuit breaker;
- canary accounts;
- shadow release before live release;
- per-strategy and venue exposure/rate budgets;
- immutable runtime/strategy version tagging;
- full target-to-fill audit trail.

## 5. Authorization/security hierarchy

Preferred future order:

1. exchange-approved OAuth/broker authorization;
2. IP-whitelisted read+trade API credentials;
3. manual API-key paste only as bootstrap.

Withdrawal permission should be absent wherever technically possible.

## 6. Capital attraction and monetization are separate

Do not assume BotMarketplace must pool outside capital into the founder's trading account to become economically useful.

Future monetization channels to evaluate separately include:

- software subscription/SaaS;
- approved broker rebates/revenue share;
- native copy-trading economics where strategy-compatible;
- performance-linked pricing only after platform/legal approval;
- later professional managed/fund structures.

Connected AUM must never be allowed to exceed strategy capacity merely because more users want access.

## 7. Safe-Sleeve S002 remains the next parallel implementation-risk study

S001 architecture result remains:

> **MULTI-DOMAIN LAYERED RESERVE**

S002 must determine concrete accessible implementation options and transfer/settlement behavior without optimizing yield before survival/accessibility.

## 8. R003 cross-venue replication remains precommitted to Bybit

Sequence remains:

1. X001 structural funding-premium replication;
2. X002 self-financing implementation replication only if X001 survives.

Venue selection may not be changed after seeing results.

## 9. R009 ETH falsification remains after Bybit replication starts/stabilizes

- unchanged R009 rules;
- ETH only;
- no broad coin search;
- structural falsification, not temporal OOS.

## 10. Capital Granularity & Capacity Audit remains mandatory

Before any candidate goes to direct-API tiny live:

- establish minimum mechanically executable capital;
- minimum economically sensible capital;
- discrete rounding/hedge error;
- expected fees/slippage by account size;
- margin headroom;
- maximum prudent capacity.

## 11. Platform coding gate

The strategy-research pivot remains in force.

Do **not** restart full marketplace/platform development merely because the architecture route is now clearer.

Allowed now:

- freeze interfaces and safety contracts needed to avoid architectural dead ends;
- maintain research/forward tooling;
- implement minimal execution-contract prototypes only when they directly support a validated candidate.

Deferred until a candidate clears forward + implementation gates:

- multi-user production execution;
- smart routing;
- large secret-management rollout;
- billing/performance fees;
- pooled custody;
- broad strategy marketplace fan-out.

## 12. Immediate execution order

1. Initialize/check combined R009-E002 + R003-E003 forward run at the already scheduled time; use first outputs only for technical causality/plumbing validation.
2. In parallel complete Safe-Sleeve S002 due diligence.
3. Then run precommitted Bybit R003-X001 structural replication.
4. If X001 survives, freeze/run Bybit R003-X002 implementation replication.
5. Run unchanged-rule R009 ETH falsification.
6. Apply Capital Granularity & Capacity Audit to surviving candidates.
7. Only then build one-venue **own-account** direct-API shadow execution MVP; tiny live capital follows only after shadow reconciliation is reliable.
8. After own-account runtime is proven, open external user-owned-account replication through OAuth/API broker integrations.
9. Native copy trading stays optional. Pooled/custodial AUM stays deferred pending separate compliance/business case.

## 13. Explicit prohibitions

Do not currently:

- tune R003/R009 historical parameters;
- alter forward inception clocks;
- treat direct API as permission to bypass exchange product/regional rules;
- fan out live trades to external accounts before canary/shadow controls;
- treat API non-custody as automatic regulatory exemption;
- optimize strategy capacity around maximum possible AUM;
- choose venues after seeing which backtest is best;
- redesign a validated strategy solely to fit native copy trading.

## 14. Current strategic state

The project now has two parallel tracks that must remain separated:

**Research track:** prove/falsify strategy economics and resilience.  
**Platform track:** freeze a deployment architecture capable of safely expressing whatever strategies survive.

Platform engineering follows validated strategy needs; strategy research must not be distorted to fit premature platform constraints.