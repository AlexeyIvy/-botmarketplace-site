# BotMarketplace Strategy-First Research Roadmap v2.3

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009 BTC forward leading; ETH X001 MIXED; bounded cross-asset breadth panel opened; R003 forward unchanged; platform development frozen

## 1. Active forward records remain unchanged

### R009-E002 BTC

- original fixed inception unchanged;
- no parameter reset or retuning;
- first forward snapshot is technical/plumbing evidence only.

### R003-E003 Binance carry

- fixed 2026-09-10 12:00 UTC boundary unchanged;
- exact 50/50 fully funded equal-BTC implementation unchanged;
- Treasury hurdles unchanged;
- no historical rescue.

### Original BTC SMA120 control

Continue independently.

## 2. R009 ETH X001 completed MIXED

The exact R009 rules were economically coherent overall on ETH but failed the eligible PRE_2020 comparison versus TREND10 because the sticky crisis sleeve remained deployed through a prolonged recovery.

No ETH-specific tuning is allowed.

## 3. Bounded breadth diagnostic now opened

User raised the valid question of whether one ETH test is enough to understand asset portability.

A broad winner-search would be methodologically weak, but a **fixed panel diagnostic** can add useful information if the panel is chosen before results and no winner is selected afterward.

Therefore open R009-X002 on exactly five assets already present in the earlier R002 major-asset subset:

- BNB
- LTC
- XRP
- ADA
- SOL

Protocol:

`docs/research/r009-x002-cross-asset-breadth-panel-protocol-v0.1.md`

Frozen engine commit:

`9e5c28428ba62bdae8eda80db364fa6c65b3d34c`

Frozen launcher commit:

`150aa00687bbc74d1a5c303d7d2cfb7cfb4e0255`

Implementation freeze:

`docs/research/r009-x002-cross-asset-breadth-implementation-freeze-v0.1.md`

## 4. Why this is allowed despite the anti-sweep rule

This is not a search for the best altcoin.

The panel is useful only to estimate breadth and detect recurring failure modes such as:

- persistent sticky crisis exposure;
- inability to recover to prior ATH;
- crisis sleeve destroying trend-only risk control;
- excessive average risky weight;
- failure of cost robustness.

Because the panel is opened after seeing ETH, its evidence is explicitly weaker than a clean precommitted independent test. It cannot be called independent confirmation.

No sixth coin may be added if the result is disappointing, and no best performer may be promoted merely because it looks attractive.

## 5. Panel decision

Per asset use the same unchanged-rule gate as ETH X001.

Panel verdict:

- breadth support: >=4 SUPPORT, 0 FAIL;
- breadth rejected: >=3 FAIL;
- otherwise breadth mixed.

This verdict informs whether R009 should be treated as a BTC-specific candidate or a broader state-allocation architecture.

## 6. Tonight's mandatory forward step unchanged

At the scheduled time run the combined R009-E002 + R003-E003 forward launcher.

The breadth panel does not alter either forward clock or rule set.

First forward package remains a causality/data-plumbing audit only.

## 7. Capital granularity branch remains queued

After the first forward technical initialization is verified:

1. run G001 mechanical granularity snapshot;
2. if interpretable, freeze/run G002 pathwise discrete replay;
3. later G003 capacity/liquidity.

The cross-asset panel does not replace capital-granularity work.

## 8. Current execution order

1. Run R009-X002 fixed five-asset breadth panel now if time permits before the scheduled forward run.
2. At the scheduled time run combined R009 + R003 forward regardless of X002 status.
3. Inspect X002 as a breadth/failure-mode diagnostic only; no winner selection or tuning.
4. Inspect first forward package technically only.
5. Run R009-G001 after forward plumbing is confirmed.
6. Continue R009/R003 forward without retuning.
7. Apply G002, Safe-Sleeve S002 and demo-readiness gates before any real-capital step.
8. Broad BotMarketplace development remains frozen.

## 9. Explicit prohibitions

Do not:

- add coins beyond the fixed X002 five-asset panel;
- choose the best X002 coin as a replacement strategy;
- retune SMA120, sleeve weights, thresholds or reset rules from X002 results;
- reset R009/R003 forward clocks;
- relax R003 Bybit X001 gates;
- start broad platform development;
- infer antifragility or production safety from historical breadth alone.
