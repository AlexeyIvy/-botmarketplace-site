# BotMarketplace Strategy-First Research Roadmap v2.2

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009 BTC forward leading; R009 ETH unchanged-rule MIXED; R003 Bybit X001 MIXED; platform development frozen

## 1. Current evidence state

### R009 BTC

- Historical mechanism screen remains `PROMISING_SCREEN`.
- BTC forward R009-E002 remains frozen and active from its original inception.
- No parameter changes are permitted.

### R009 ETH

- Cross-asset X001 result is `UNCHANGED_RULE_MIXED`.
- The exact rules remain economically coherent overall but fail the eligible PRE_2020 comparison versus TREND10.
- Do not retune ETH or sweep additional coins.

### R003

- Binance historical implementation remains promising but recent capital efficiency is marginal.
- Bybit X001 is formally `STRUCTURAL_SIGNAL_MIXED` because of completed-year concentration.
- Do not open Bybit X002 under the frozen gate.
- Binance R003-E003 forward continues unchanged.

## 2. Immediate mandatory step

At the already scheduled time, initialize/check the combined R009-E002 + R003-E003 forward tracker.

The first forward package is a **technical causality/plumbing audit only**. Check:

- fixed inception boundaries;
- fully closed bars only;
- causal state/funding mapping;
- persistent output behavior;
- no forward-clock reset;
- data integrity.

Do not interpret initial profit/loss as evidence of strategy quality.

## 3. Capital granularity work opened prospectively

Because R009 remains the leading candidate and the project requires small-account feasibility, open the Capital Granularity & Capacity branch without changing strategy rules.

### G001 — current mechanical granularity snapshot

Protocol:

`docs/research/r009-g001-capital-granularity-snapshot-protocol-v0.1.md`

Frozen engine commit:

`cede11a1eac65f4bdff2ad485dab62c9f2a5e367`

Android launcher commit:

`ecfecea8fbe310de178b57e4d3828804b2902f7c`

G001 uses current Binance BTCUSDT filters plus the current latest fully closed daily price to determine the mechanical lower bound for R009's 2.5pp target increments and allowed target states.

G001 is not a performance test and does not authorize demo/live.

### G002 — pathwise discrete replay

Only after the first forward initialization is checked technically, freeze and run a pathwise discrete-order replay that measures:

- daily drift-rebalance orders;
- skipped orders below minimums;
- target-weight error through time;
- realized performance distortion by account-size tier;
- fee sensitivity under the exact frozen R009 logic.

No rebalance-frequency change is allowed as a rescue inside G002.

### G003 — capacity/liquidity

Later, for larger AUM, evaluate depth, slippage, market impact and venue concentration. Do not treat small-account feasibility as proof of unlimited capacity.

## 4. Why G001 is prepared now but G002 waits

Preparing G001 now prevents current continuous-fraction assumptions from becoming an implementation blind spot.

G002 waits for the first forward technical check because it is a deeper implementation-replay step and should be built only after the forward data plumbing is confirmed.

## 5. Safe sleeve

Safe-Sleeve S001 remains valid. Detailed S002 remains deferred until a candidate approaches demo/real-capital implementation.

## 6. Demo gate

Demo remains a future execution-validation channel, not a replacement for forward evidence.

A minimal demo may start only after:

- historical implementation evidence remains strong enough;
- independent falsification does not create a hard contradiction;
- forward initialization is technically clean;
- capital granularity is understood well enough to choose a mechanically valid demo account size.

## 7. Immediate execution order

1. At the scheduled time run combined R009 + R003 forward and send the first outputs for technical review.
2. After that technical review, run R009-G001 capital granularity snapshot.
3. If G001 is interpretable, freeze/run G002 pathwise discrete replay.
4. Continue R009/R003 forward records without retuning.
5. Decide demo eligibility only after G002 and safe-sleeve requirements are sufficiently clear.
6. Broad BotMarketplace development remains frozen.

## 8. Explicit prohibitions

Do not:

- retune R009 from the ETH MIXED result;
- reopen Bybit R003 X002 under the failed frozen gate;
- reset forward clocks;
- change R009 daily-target mechanics to make small accounts easier before measuring the distortion;
- use G001/G002 to optimize historical profitability;
- infer unlimited capacity from small-account feasibility;
- begin broad platform implementation before a leading strategy justifies it.
