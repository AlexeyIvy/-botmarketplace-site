# R010 — Drawdown-Armed Recovery Barbell Hypothesis v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** hypothesis-generation note only; not yet a test protocol; no validation claim

## 1. Motivation

R009 cross-asset diagnostics show a repeated structural weakness: the sticky crisis sleeve can remain active for years when an asset fails to regain its old ATH. This converts intended crisis dry powder into persistent distressed beta.

A second-pass diagnostic also shows that, for most non-BTC assets inspected, the crisis sleeve's cumulative gross contribution was concentrated during periods when the existing SMA120 trend state was already ON.

Because these facts were learned from inspected history, they cannot be used to retroactively improve R009 and then claim validation. R009 v0.1 stays frozen.

## 2. New hypothesis

A distinct future candidate may test the idea:

> **Drawdown should arm recovery capital; recovery confirmation should permit deployment.**

This changes the economic job of the crisis sleeve from 'buy and remain exposed until old ATH' to 'reserve capital during deterioration, then accelerate participation when a distressed asset enters a confirmed recovery state.'

## 3. Lowest-degree-of-freedom conceptual version

Reuse only existing frozen primitives:

- SMA lookback = 120 daily closes;
- trend state ON iff close > SMA120;
- drawdown arming levels = -20/-35/-50/-65%;
- four equal 2.5pp armed tranches;
- maximum recovery sleeve = 10%;
- trend sleeve remains 0/10%;
- total risky target remains 0-20%;
- no leverage.

Conceptual state machine:

1. A drawdown breach **arms** the corresponding 2.5pp tranche.
2. Armed capital remains cash while TREND10 is OFF.
3. When TREND10 is ON, armed tranches are permitted to become recovery exposure.
4. If TREND10 turns OFF again, recovery exposure returns to cash while the arming state may remain recorded until a separately frozen reset rule is defined.

The exact reset semantics must be frozen before any test. Do not choose a reset from a grid after examining old performance.

## 4. Why this is not simply R009 tuning

R009's crisis sleeve is a persistent drawdown-beta sleeve. R010 would assign a different economic role: **drawdown memory + recovery confirmation**.

Therefore it must be treated as a new candidate family/version, not as a patch to R009.

## 5. Validation discipline

Before any R010 engine is run:

- freeze one exact state machine;
- freeze any reset rule without parameter search;
- define hard falsification gates;
- explicitly mark BTC/ETH/BNB/LTC/XRP/ADA/SOL histories as contaminated for confirmatory purposes;
- if old data are used, use them only for sanity/failure-mode diagnostics;
- begin a new forward shadow record from a post-freeze inception for actual prospective evidence;
- do not interrupt or replace the existing R009 forward record.

## 6. Why not add a fixed holding-period parameter now

A 30/90/180/365-day crisis expiry would directly attack long state duration, but choosing the horizon from inspected history introduces another numerical degree of freedom and a strong overfitting channel.

The first redesign should therefore prefer existing frozen state variables before introducing a new duration parameter.

## 7. Relationship to antifragility objective

Even a successful R010 would remain long-beta and would not by itself prove true convexity or antifragility.

The broader antifragility architecture may still require an orthogonal bounded-convexity sleeve, potentially funded by realized carry, plus a true off-venue safe reserve.

R010's narrower objective is to make crisis/recovery beta less path-trapped and more state-responsive without increasing leverage or historical parameter complexity.

## 8. Current decision

Do not implement or backtest R010 before the already scheduled R009/R003 forward initialization is technically checked.

After that, R009 G001/G002 remains the precommitted implementation-priority branch. R010 can then be converted into a separately frozen prospective protocol if the project chooses to investigate the identified state-duration weakness in parallel.
