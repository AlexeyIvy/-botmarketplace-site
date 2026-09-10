# BotMarketplace Strategy-First Research Roadmap v2.9

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009/R003 forwards active; R009 G001/G002 complete; R010-E001 prospective shadow-forward frozen before first signal bar close; broad platform development remains frozen

## 1. Active forward records

### R009-E002 — BTC forward

- initialization technically accepted;
- fixed inception remains 2026-09-10 00:00 UTC;
- exact frozen R009 v0.1 rules unchanged;
- only fully closed future daily bars accumulate evidence.

### R003-E003 — Binance canonical forward

- fixed decision boundary remains 2026-09-10 12:00 UTC;
- first establishment snapshot technically accepted;
- funding-timestamp causality hotfix was frozen before any funding event entered the record;
- temporary Binance HTTP 418/source-access failure does not authorize reset or venue substitution;
- continue from original inception when access permits.

### R003-X003 — Bybit parallel venue forward

- fixed boundary 2026-09-10 16:00 UTC;
- initial establishment and first forward hour technically accepted;
- source coverage, equal-BTC hedge, margin proxy and causal funding eligibility passed initialization audit;
- remains separate from Binance E003 and earlier Bybit X001.

## 2. R009 implementation granularity branch

### G001

Status: **MECHANICAL_ENVELOPE_ESTABLISHED**.

- current BTCUSDT step = 0.00001 BTC;
- minQty = 0.00001 BTC;
- minNotional = 5 USDT;
- step-aware 2.5pp executable threshold about 219.26 USD;
- first frozen tested tier with all target states/transitions statically feasible = 250 USD.

### G002

Status: **DISCRETE_IMPLEMENTATION_ENVELOPE_ESTABLISHED**.

- replay 2018-01-01 through 2026-09-09;
- no negative-cash accounting errors;
- no trapped zero-target dust exits in the frozen baseline replay;
- all observed signal-state changes executed even at the smallest tested tiers;
- high skipped-order share at small capital is dominated by tiny daily drift corrections;
- 250 USD remains a coarse mechanical floor, not a practical minimum;
- 1,000 USD remains the current descriptive small-account demo-engineering candidate on tracking-fidelity grounds, not an optimized universal minimum;
- 5,000 USD+ is near-continuous under the frozen current-rule quantity/min-notional model.

G003 liquidity/capacity remains deferred until material real-capital scaling or multi-user fanout makes depth/slippage analysis decision-relevant.

## 3. R010-E001 prospective shadow-forward

The previously documented R010 hypothesis has now been converted into one exact frozen prospective state machine without historical parameter search.

Protocol:

`docs/research/r010-e001-prospective-shadow-forward-protocol-v0.1.md`

Protocol commit:

`5f13f36712bd48ffdf21292591ddb7b592ba1d03`

Frozen engine:

`research/r010/r010_e001_prospective_shadow_forward.py`

Engine commit:

`5088678bdf480a222f9b2cc276ab3573ec4a3639`

Android launcher:

`research/r010/r010_e001_prospective_shadow_forward_mobile.py`

Launcher commit:

`e456e32d19437b5fa5cd0e7abc5540a7fc91d5a8`

Implementation freeze:

`docs/research/r010-e001-implementation-freeze-v0.1.md`

Implementation-freeze commit:

`3c93e58f929fc4065daa8b8fc2230c1a652ed84c`

### Frozen R010 v0.1 semantics

- BTCUSDT Binance Spot daily source;
- SMA120 trend state;
- 10% trend sleeve;
- drawdown arms four 2.5pp tranches at -20/-35/-50/-65%;
- armed capital remains cash while trend is OFF;
- while trend is ON, armed weight may deploy as recovery exposure;
- trend OFF returns recovery exposure to cash but preserves arming memory;
- new closing ATH is the only arming-memory reset;
- total risky target 0-20%;
- no leverage, expiry, hysteresis, cooldown, extra indicator or parameter grid.

The new-ATH reset is not claimed optimal. It is reused because it is an existing state primitive and introduces no new numerical degree of freedom.

### Fixed prospective clock

- protocol frozen before the 2026-09-10 UTC daily bar closes;
- 2026-09-10 UTC is the post-freeze signal bar;
- immutable R010 forward inception = **2026-09-11 00:00 UTC**;
- first realized forward daily interval is 2026-09-10 close to 2026-09-11 close using the 2026-09-10 closed-bar target;
- delayed first run may reconstruct from this clock but may not move it.

### Evidence discipline

- old BTC/ETH/BNB/LTC/XRP/ADA/SOL history remains contaminated for confirmatory R010 efficacy;
- pre-inception BTC bars are state warmup only;
- no historical R010 P&L is produced by E001;
- no terminal positive or negative strategy conclusion before 365 realized forward daily intervals, except operational/source invalidation;
- strong mature interpretation additionally requires at least one prospective arming event and one prospective recovery activation event;
- R009-E002 continues independently and is never reset or replaced by R010.

## 4. Immediate execution order

1. Initialize R010-E001 after the frozen 2026-09-10 UTC signal bar is fully closed; if run earlier, WAITING status is expected and must not move inception.
2. Continue R009-E002 unchanged.
3. Continue Bybit R003-X003 unchanged.
4. Retry Binance R003-E003 only after source access permits, preserving original inception and causality-safe implementation.
5. Keep G003 deferred until liquidity/capacity becomes decision-relevant.
6. Open Safe-Sleeve S002 before any real-capital promotion.
7. Consider minimal demo only after forward plumbing remains stable and safe-sleeve/access constraints are understood.
8. Broad BotMarketplace platform feature development remains frozen until strategy/implementation gates justify it.

## 5. Explicit prohibitions

Do not:

- retune R009 after G001/G002;
- call 250 USD a practical minimum deposit;
- choose a capital tier by whichever historical replay ended highest;
- backfit R010 reset semantics on inspected history;
- change R010 thresholds/weights after forward launch;
- treat inherited pre-inception armed tranches as prospective validation of the arming mechanism;
- replace R009 with R010;
- merge Binance and Bybit R003 forward histories;
- move any fixed forward inception;
- treat favorable R010 shadow behavior as proof of antifragility;
- restart broad platform development yet.
