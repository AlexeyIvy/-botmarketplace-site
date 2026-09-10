# BotMarketplace Strategy-First Research Roadmap v2.7

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009 and Bybit R003 forwards initialized; G001 complete; G002 frozen and ready; Binance R003 canonical forward preserved pending clean retry

## 1. Active forward records

### R009-E002 — BTC forward

- initialization technically accepted;
- fixed inception remains 2026-09-10 00:00 UTC;
- exact frozen R009 v0.1 rules unchanged;
- only fully closed future daily bars accumulate evidence.

### R003-E003 — Binance canonical forward

- original fixed decision boundary remains 2026-09-10 12:00 UTC;
- first establishment snapshot was technically accepted;
- pre-first-funding timestamp-causality hotfix was frozen before any funding event entered the record;
- Binance HTTP 418/source access issue does not authorize reset or venue substitution inside E003;
- continue from original inception when access permits.

### R003-X003 — Bybit parallel venue forward

- fixed boundary 2026-09-10 16:00 UTC;
- initial establishment 16:59:59.999 UTC and first forward hour technically accepted;
- data coverage, equal-BTC hedge, margin proxy and causal funding eligibility passed the initialization audit;
- this remains separate from Binance E003 and from historical Bybit X001.

## 2. R009-G001 result

Formal status: **MECHANICAL_ENVELOPE_ESTABLISHED**.

Frozen current Binance BTCUSDT rules:

- step = 0.00001 BTC;
- minQty = 0.00001 BTC;
- minNotional = 5 USDT;
- reference BTC close = 78,306.43 USDT.

Continuous 2.5pp notional lower bound is 200 USD, but exact step-aware executable threshold is about **219.258 USD** because a 0.00006 BTC rounded order is below 5 USDT and the first executable rounded quantity is 0.00007 BTC.

First frozen tested capital with all nonzero target states and all directed target-state transitions mechanically feasible: **250 USD**.

250 USD is therefore a static mechanical grid floor only, not a practical minimum deposit.

Result/audit:

`docs/research/r009-g001-results-and-technical-audit-v0.1.md`

Result audit commit:

`b3e0960f12f71dae596c8963ba94e0a1b075c6f0`

## 3. R009-G002 frozen pathwise discrete replay

Purpose: determine how finite account size, quantity rounding, 5 USDT minimum orders, skipped daily corrections and residual dust distort the exact R009 path through time.

Frozen protocol:

`docs/research/r009-g002-pathwise-discrete-replay-protocol-v0.1.md`

Protocol commit:

`cde4d52e071b623588ce3583901aea25cff1f13e`

Frozen engine:

`research/r009/r009_g002_pathwise_discrete_replay.py`

Engine commit:

`ea713a8899673733692659a44ce397b96cd3d4c5`

Frozen Android launcher:

`research/r009/r009_g002_pathwise_discrete_replay_mobile.py`

Launcher commit:

`835638b5d844c3f72dca42545604bc954914b680`

Implementation-freeze document:

`docs/research/r009-g002-implementation-freeze-v0.1.md`

Implementation-freeze commit:

`6ebbba46e66c4d2889e2db6a791d5c6db44f8a63`

Frozen account tiers: 200, 250, 500, 1,000, 5,000, 10,000 USD. Frozen fees: 5/10/25/50 bps. Frozen G001 current-rule filters are applied across the historical replay. G002 is implementation fidelity only, not a strategy-validation test.

## 4. Immediate execution order

1. Run R009-G002 once and audit the five-file output.
2. Continue R009-E002 forward unchanged.
3. Continue Bybit R003-X003 forward unchanged.
4. Retry Binance R003-E003 causality-safe path only when source access permits; never reset inception.
5. After G002, decide whether a separate G003 liquidity/capacity study is needed before demo sizing.
6. Open Safe-Sleeve S002 before any real-capital promotion.
7. R010 remains hypothesis-only until current implementation/forward work is sufficiently stable.
8. Broad platform feature development remains frozen.

## 5. Explicit prohibitions

Do not:

- call 250 USD a practical minimum before G002;
- optimize capital tier based on historical ending return;
- change R009 thresholds/weights because of G002;
- add batching/tolerance bands after seeing G002 without opening a new implementation candidate;
- merge Binance and Bybit R003 records;
- move any fixed forward inception;
- treat historical implementation resilience as antifragility proof;
- restart broad platform development before strategy/implementation gates are understood.
