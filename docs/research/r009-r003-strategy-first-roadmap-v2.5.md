# BotMarketplace Strategy-First Research Roadmap v2.5

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009 cross-asset second-pass diagnostics completed; R010 hypothesis queued; forward clocks unchanged; platform development frozen

## 1. Current evidence state

R009 BTC remains the primary forward candidate. R009 ETH remains `UNCHANGED_RULE_MIXED`. The fixed BNB/LTC/XRP/ADA/SOL breadth panel remains `CROSS_ASSET_BREADTH_MIXED` with 3 SUPPORT / 2 MIXED / 0 FAIL. R003 Binance forward remains active; Bybit X001 remains formally MIXED and does not open X002.

No existing frozen strategy or forward inception changes.

## 2. New second-pass R009 diagnostic

Canonical note:

`docs/research/r009-cross-asset-second-pass-diagnostics-v0.1.md`

Main conclusions:

- crisis persistence is strongly negatively associated with observed cross-sectional Calmar in the small seven-asset sample;
- CRISIS10 is not robust standalone alpha relative to STATIC10;
- the crisis sleeve often improves CAGR but not consistently Calmar versus TREND10;
- overlapping altcoin crisis states are highly synchronized, so adding many R009 coins is not assumed to create orthogonal antifragility;
- a large share of gross crisis contribution on most inspected non-BTC assets occurs after the SMA120 trend state is already ON;
- the old-ATH reset embeds potentially multi-year time-under-water exposure.

These are retrospective clues only, not independent evidence.

## 3. R010 hypothesis queued, not activated

Hypothesis note:

`docs/research/r010-drawdown-armed-recovery-hypothesis-v0.1.md`

Concept:

> drawdown arms recovery capital; recovery confirmation permits exposure.

R010 is a separate future candidate, not a patch to R009. It should initially reuse existing frozen primitives where possible to minimize new degrees of freedom.

Do not run or promote R010 on already inspected BTC/ETH/BNB/LTC/XRP/ADA/SOL history as if that were independent validation.

## 4. Immediate execution order unchanged

1. At the scheduled time run combined R009-E002 + R003-E003 forward launcher v0.2.
2. Review the first forward package technically only: inception, closed-bar causality, funding mapping, Treasury causality, persistence, no reset.
3. If clean, run frozen R009-G001 capital granularity snapshot.
4. Freeze/run R009-G002 pathwise discrete replay.
5. Continue R009/R003 forward records unchanged.
6. Only after G001/G002, decide whether to convert R010 hypothesis into a prospectively frozen shadow-forward protocol in parallel.
7. Safe-Sleeve S002 remains required before any real-capital promotion.
8. Broad BotMarketplace development remains frozen.

## 5. Anti-overfitting rule

Do not use the new diagnostic to:

- retune R009;
- choose a best-performing coin;
- optimize an R010 holding period/reset on inspected histories;
- replace the existing BTC forward with a redesigned candidate;
- claim cross-sectional correlations as statistical proof.

The diagnostic may guide what failure mode a new hypothesis attacks, but promotion requires prospective evidence.
