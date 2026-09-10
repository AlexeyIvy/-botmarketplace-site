# BotMarketplace Strategy-First Research Roadmap v1.9

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** strategy research active; R003 Bybit X001 completed as MIXED; forward clocks unchanged  
**Research posture:** falsification-first, forward-aware, anti-overfitting, implementation-realism before real capital

## 1. Active forward records

### R009-E002

- true forward directional/state-dependent beta candidate;
- original fixed inception unchanged;
- no parameter reset or retuning.

### R003-E003

- true forward carry candidate;
- fixed decision boundary 2026-09-10 12:00 UTC;
- exact 50/50 fully funded equal-BTC implementation unchanged;
- safe-capital hurdle tracking unchanged;
- no funding threshold/leverage/rebalance-frequency rescue.

### Original BTC SMA120 control

Continue independently and unchanged.

## 2. R003 Bybit X001 completed

Canonical result:

`docs/research/r003-bybit-x001-results-v0.1.md`

Formal conclusion:

> **STRUCTURAL_SIGNAL_MIXED**

Data gate passed and all major sign/persistence checks passed, including positive FULL, PRE_2023 and POST_2023 funding, 100% positive rolling-365d windows, majority/all completed full years positive, and positive deep-drawdown average funding.

The only frozen structural check that failed was completed-year concentration: 2021 contributed approximately 56.94% of the sum of positive completed full-year funding returns, above the prospectively fixed <50% ceiling.

## 3. Interpretation discipline

The Bybit result is not a failed economic replication in the ordinary-language sense: aggregate and recent funding statistics are very similar to Binance and therefore materially support the hypothesis that positive BTC perpetual funding carry is not purely Binance-specific.

However the prospectively frozen decision rule must control promotion. Because X001 is formally MIXED, **do not advance directly to Bybit X002**.

Do not relax the concentration rule, drop 2021, change venue or add filters after seeing this result.

## 4. R003 status after X001

R003 remains a live research branch because:

- Binance E001 structural signal was present;
- Binance E002 implementation study was promising, albeit with marginal recent capital efficiency;
- Bybit X001 qualitatively supports cross-venue portability but formally fails one robustness gate;
- Binance R003-E003 forward is already frozen and must continue regardless of X001.

No new historical R003 optimization is opened now.

## 5. Immediate next falsification priority

The next historical structural test is **R009 v0.1 on ETH with unchanged rules**.

Purpose:

> determine whether the R009 mechanism is specifically a BTC-history artifact or retains useful structure on a second major crypto asset without any parameter change.

Constraints:

- ETH only;
- same SMA120 trend logic;
- same crisis sleeve rules and thresholds;
- same 10/10 architecture and 20% maximum exposure;
- same self-financing accounting and cost grid;
- no parameter search;
- no broad coin sweep;
- interpret as cross-asset structural falsification, not temporal OOS.

Freeze the exact protocol and implementation before inspecting ETH results.

## 6. Forward execution today

At the already scheduled time initialize/update the combined R009-E002 + R003-E003 forward tracker.

The first output is a plumbing/causality check only. Do not infer strategy quality from hours or days of forward P&L.

## 7. Safe sleeve and capital granularity

Safe-Sleeve S001 and capital-scalability requirements remain valid but are not the immediate edge bottleneck.

Detailed S002 implementation and Capital Granularity & Capacity Audit become mandatory before demo/tiny-live promotion of any surviving leading candidate.

## 8. Demo gate

A candidate that remains strong after historical implementation, independent falsification and technically stable forward initialization may later enter minimal exchange demo execution in parallel with continued forward paper testing.

Demo tests execution mechanics; it does not replace forward evidence and short demo profitability is not proof of robustness.

## 9. Current execution order

1. Keep R009-E002, R003-E003 and original BTC SMA120 forward clocks unchanged.
2. Today initialize/check combined R009 + R003 forward tracker at the scheduled time.
3. Freeze and run unchanged-rule R009-on-ETH structural falsification.
4. Compare the resulting R009 BTC/ETH structure without retuning.
5. Continue accumulating R003 forward evidence; do not open Bybit X002 under the current X001 outcome.
6. Apply capital-granularity/capacity and Safe-Sleeve S002 before demo eligibility.
7. Only then consider minimal exchange demo of the strongest surviving candidate(s).
8. Broad BotMarketplace implementation remains deferred until a leading strategy justifies it.

## 10. Explicit prohibitions

Do not currently:

- relax the Bybit X001 concentration gate;
- drop 2021 from Bybit because it dominates gains;
- shop for another venue to rescue R003;
- add leverage or funding thresholds to R003;
- retune R009 after seeing ETH;
- reset any forward clock;
- restart broad marketplace development;
- call any candidate antifragile or production-safe based only on historical results.
