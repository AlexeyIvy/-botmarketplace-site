# BotMarketplace Strategy-First Research Roadmap v2.4

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009 cross-asset breadth completed MIXED; BTC forward remains primary; R003 forward unchanged; platform development frozen

## 1. Current evidence state

### R009 BTC

- E001 remains `PROMISING_SCREEN`.
- R009-E002 true forward remains frozen and primary.
- No parameter change or inception reset.

### R009 ETH

- X001 remains `UNCHANGED_RULE_MIXED`.
- The principal weakness is prolonged sticky crisis exposure during the 2018-2020 recovery.

### R009 five-asset breadth panel

Canonical result:

`docs/research/r009-x002-cross-asset-breadth-results-v0.1.md`

Formal panel conclusion:

> **CROSS_ASSET_BREADTH_MIXED**

Fixed panel result: **3 SUPPORT / 2 MIXED / 0 FAIL**.

- SUPPORT: BNB, ADA, SOL.
- MIXED: LTC, XRP.
- no hard-fail asset.

The breadth panel materially weakens the hypothesis that R009 is purely BTC-specific, but it does not meet the frozen >=4 SUPPORT threshold and therefore cannot be called broad cross-asset validation.

Do not expand the panel or select a winner asset.

### R003

- Binance historical implementation remains promising but modern capital efficiency is marginal.
- Bybit X001 remains `STRUCTURAL_SIGNAL_MIXED`.
- Do not open Bybit X002.
- Binance R003-E003 true forward continues unchanged.

## 2. New cross-asset synthesis

Canonical synthesis:

`docs/research/r009-cross-asset-synthesis-v0.1.md`

Current defensible interpretation:

> **The trend-gated + crisis-state interaction has partial cross-asset breadth, while sticky-to-new-ATH crisis deployment has a repeated structural persistence weakness outside BTC.**

The crisis sleeve is highly persistent across the fixed altcoin panel and should continue to be described as state-dependent beta handoff, not proven crisis alpha or true convexity.

This observation is not permission to optimize reset rules on inspected history.

## 3. No more cross-coin breadth expansion now

Further historical coin additions have diminishing information value and rising selection/cherry-picking risk.

Therefore:

- no DOGE/AVAX/LINK expansion;
- no SOL winner promotion;
- no ETH-specific or altcoin-specific retuning;
- no search for an asset on which the current rule looks best.

If a future cross-asset test is opened, it must answer a genuinely new pre-specified hypothesis rather than extend the current sweep.

## 4. Immediate mandatory step — forward initialization

At the scheduled time run the combined R009-E002 + R003-E003 forward launcher v0.2.

First package is technical only. Verify:

- R009 original daily inception and first target are preserved;
- R003 fixed 2026-09-10 12:00 UTC decision boundary is preserved;
- only fully closed bars enter realized forward paths;
- funding events at/before R003 establishment are excluded;
- Treasury dynamic benchmark remains causal (quote usable next day only);
- persistent folders/history are not reset;
- source and merge integrity are clean.

Do not interpret first-day P&L.

## 5. R009 capital granularity after clean forward initialization

### G001

Run the already frozen mechanical granularity snapshot after the first forward technical package is accepted.

Purpose: quantify current Binance BTCUSDT minimum-order/step constraints against R009's 2.5 percentage-point target increments.

### G002

Then freeze and run a pathwise discrete replay.

Purpose: measure whether realistic rounding/minimum-order skipping materially changes R009 behavior by account-size tier.

Do not change daily-target mechanics to make small accounts look easier.

### G003

Capacity/liquidity testing remains later for larger AUM.

## 6. Safe sleeve and demo

Safe-Sleeve S002 remains deferred until the leading candidate approaches demo/real-capital implementation.

Minimal exchange demo becomes eligible only after:

- forward plumbing is technically stable;
- G001/G002 show a mechanically sensible account-size tier;
- no new hard contradiction appears;
- execution tooling can preserve frozen strategy semantics.

Demo validates execution, not long-run profitability.

## 7. Execution order

1. Run combined R009 + R003 forward at the scheduled time and submit both result folders plus bundle status.
2. Perform technical causality/plumbing review only.
3. If clean, run R009-G001.
4. Freeze/run R009-G002 pathwise discrete replay.
5. Continue R009/R003 forward unchanged.
6. Open Safe-Sleeve S002 before real-capital promotion.
7. Consider minimal one-strategy demo only after the above gates.
8. Broad BotMarketplace development remains frozen.

## 8. Explicit prohibitions

Do not:

- expand the cross-asset panel after seeing 3/2/0;
- promote SOL because its CAGR is highest;
- retune R009 thresholds, weights, SMA or reset;
- reopen Bybit R003 X002;
- reset forward clocks;
- optimize small-account mechanics before measuring the distortion;
- infer antifragility from historical breadth;
- begin broad platform development before strategy evidence warrants it.
