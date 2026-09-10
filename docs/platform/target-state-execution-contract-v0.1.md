# BotMarketplace — Target-State Execution Contract v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** architecture interface freeze; no production implementation claim

## 1. Purpose

Define the minimum contract between a validated strategy and future exchange execution so BotMarketplace can scale from one founder account to multiple user-owned accounts without literal order copying.

This document is intentionally implementation-light while strategy research remains the project priority.

## 2. Core principle

The strategy engine emits **economic intent / desired portfolio target**.

It does not emit venue-specific final order quantity as the canonical strategy output.

Venue/account-specific sizing and execution are downstream responsibilities.

## 3. Minimum canonical objects

### StrategyVersionRef

- `strategyId`
- `strategyVersionId`
- `researchProtocolId` / evidence tag where applicable
- immutable code/config hash

### PortfolioTarget

- `targetId`
- `generatedAt`
- `effectiveAfter`
- `strategyVersionRef`
- one or more `TargetLeg`
- rebalance/expiry semantics
- target-level risk metadata

### TargetLeg

Minimum fields:

- economic instrument class: `spot | perp | future | option | cash_like`
- underlying / quote currency
- direction / signed exposure
- sizing semantic: percent NAV, fixed notional, equal-quantity hedge, delta target, premium budget, etc.
- venue constraint: explicit venue if economics are venue-dependent; otherwise allowed-venue set only after equivalence validation
- product-specific metadata where required

### AccountExecutionPlan

Derived separately for each account:

- `accountId`
- `targetId`
- resolved venue/product IDs
- current account state snapshot hash
- rounded target quantities
- expected residual target error
- required margin/collateral
- estimated fees/slippage
- risk-check results
- ordered execution steps / atomicity policy
- idempotency keys

### ExecutionResult

- submitted orders
- exchange order IDs/client IDs
- fills/average prices
- fees
- rejected/partial state
- final reconciled positions/balances
- residual deviation from target
- alerts/failsafe actions

## 4. Required invariants

Before an `AccountExecutionPlan` can become live orders:

1. strategy version is immutable and known;
2. target is not stale;
3. account/venue permissions match required products;
4. no withdrawal permission is required for ordinary trading execution;
5. account is reconciled immediately before material execution;
6. venue minQty/minNotional/step/tick rules are satisfied;
7. post-rounding residual exposure is within strategy-specific tolerance;
8. margin/collateral headroom passes risk policy;
9. estimated execution cost does not invalidate the target's allowed cost envelope;
10. per-account, per-strategy and venue/global fan-out limits pass;
11. duplicate execution of the same target is impossible through idempotency/reconciliation;
12. every order can be traced back to target + strategy/runtime versions.

## 5. Multi-leg execution rule

For multi-leg targets such as R003 spot-long + perp-short:

- do not assume exchange-native atomicity;
- strategy definition must state maximum tolerated temporary unhedged exposure;
- execution planner must define leg order, timeout, partial-fill behavior and unwind/failsafe behavior;
- if venue-native spread/atomic execution is later used, it is an execution implementation that must be separately validated before replacing sequential-leg assumptions.

## 6. Small-account rule

If rounding/minimums make a target materially inaccurate:

- do not silently place a distorted strategy;
- return `NOT_FEASIBLE_AT_ACCOUNT_SIZE` or an equivalent explicit state;
- record minimum required capital estimate;
- use a separately pre-defined implementation tier only if one exists.

## 7. Capacity rule

For many accounts receiving the same target:

- execution must be capacity-aware;
- accounts may be scheduled in bounded waves;
- if projected aggregate order flow exceeds the strategy/venue capacity envelope, new execution must be throttled or rejected rather than increasing slippage without bound.

## 8. Failure-containment rule

Global fan-out must be subordinate to independent safety services.

At minimum future implementation requires:

- global pause;
- venue pause;
- strategy-version pause;
- account pause;
- canary-first deployment;
- stale-target rejection;
- maximum aggregate notional per execution wave;
- maximum order count per time window;
- post-wave reconciliation before continuation when required by policy.

## 9. Relationship to current Strategy DSL

The existing declarative DSL remains useful as an authoring/validation layer, but the current MVP shape is too narrow for portfolio targets such as R003 because it is centered on one exchange/category/symbol and one position.

Do not break existing DSL versions. A later DSL/portfolio-intent extension should be versioned and backward compatible.

## 10. Relationship to current Bot Runtime

Current runtime principles of deterministic state transitions, idempotent client order IDs and restart/reconnect reconciliation remain valid and should be preserved.

The future change is mainly scope:

- from one strategy/user/symbol lifecycle
- to portfolio-target planning plus per-account execution state machines.

## 11. Implementation gate

No broad production implementation follows from this contract today.

The first implementation is allowed only for a strategy that clears the applicable research/forward/capital-granularity gates, and should proceed:

1. shadow target generation;
2. one founder-owned demo account;
3. one founder-owned tiny-live account;
4. only then external user-owned accounts.

## 12. Current decision

This contract is the architecture bridge between strategy research and future direct-API deployment. It is frozen early to prevent current single-order/single-symbol assumptions from becoming a long-term platform constraint.