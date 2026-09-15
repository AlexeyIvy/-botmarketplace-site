# SC001 Current Roadmap and Stop Rules v1.6

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**

Supersedes for current SC001 execution order:

`docs/research/sc001-current-roadmap-and-stop-rules-v1.5.md`

## 1. Preserved independence and terminal decisions

SC001 remains fully independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Nothing in SC001 may retrospectively alter their frozen rules, decisions or forward clocks.

Terminal SC001 history:

- E001: terminal `FAIL`; no rescue tuning;
- E002: terminal standalone `TAKER_ECONOMICS_FAIL`; TFI retained only as a future auxiliary/filter/ranking/execution-timing/meta-model feature;
- E003: terminal `E003_DISCOVERY_FAIL`; no Confirmation/L2/rescue;
- E004: terminal `E004_DISCOVERY_FAIL`; no Confirmation/L2/rescue.

Q2, formal Validation and Final remain closed.

## 2. E004 diagnostic postmortem complete

Recorded in:

`docs/research/sc001-e004-read-only-diagnostic-postmortem-v1.0.md`

All eight frozen one-factor diagnostics were inspected once as read-only postmortem.

Best observed diagnostic mean was only about `+1.39 bps` (H10). Other locally positive means were also around one bp, and several medians/trimmed means were zero or negative.

No diagnostic approached the many-tens-of-bps economics scale required for a robust standalone taker strategy.

Therefore E004 remains terminal `E004_DISCOVERY_FAIL`. The local neighborhood cannot be promoted or combined into a rescue candidate on the same Discovery outcomes.

## 3. E005 remains closed

E005 was reserved only for an incremental E002-TFI test on top of an independently viable E004 base strategy.

E004 failed, so E005 is not opened.

Do not repurpose E005 for another mechanism.

## 4. Updated mechanism-level lesson after E001-E004

The branch now has increasingly strong evidence that one-leg directional BTC scalp hypotheses which enter after an already-visible price/flow/state transition often leave only a tiny residual move relative to approximately 10 bps single-instrument round-trip regular-user taker cost.

This applies differently across the failed history:

- E001: gross reversal proposition failed;
- E002: predictive information existed but monetizable standalone edge was tiny relative to fees;
- E003: rare flow continuation gross mechanism failed;
- E004: volatility-compression breakout residual edge was near zero; local diagnostic neighborhood remained around one bp.

Research priority should therefore change mechanism class rather than continue neighboring one-leg directional tweaks.

## 5. Next priority: SC001-E006

New planning document:

`docs/research/sc001-e006-same-venue-spot-perp-basis-dislocation-research-plan-v0.1.md`

Candidate family:

**same-venue BTC spot/perpetual transient basis dislocation -> convergence.**

Initial pair:

- OKX `BTC-USDT` spot;
- OKX `BTC-USDT-SWAP` perpetual.

Why prioritized:

- tests relative value rather than the next directional BTC residual;
- temporary derivatives-specific dislocation can plausibly have a larger natural bps scale;
- common BTC directional movement is substantially offset in a paired response;
- same venue reduces cross-venue clock/transfer complexity;
- turnover can be kept event-driven and low;
- existing qualified swap March data can be reused without altering prior experiments.

This is a research hypothesis only, not a profitability claim.

## 6. Large-price-jump family remains deferred

Large-price-jump continuation/reversal remains a legitimate later fallback family.

It is not selected next because it again enters after a large directional move has already happened and therefore has a high risk of repeating the residual-edge problem seen in E002/E003/E004.

It may receive a future experiment identifier only if later evidence or data availability justifies it. It must not be mined now for a best-looking horizon/direction on already inspected outcomes.

## 7. E006 current hard gate

**NO E006 ALPHA IS AUTHORIZED.**

Immediate work is data engineering only.

First qualify whether matching March-2024 public historical OKX `BTC-USDT` SPOT trades can be obtained reproducibly and causally aligned with the already-qualified `BTC-USDT-SWAP` trade data.

Initial E006 data-only scope:

- metadata/identity feasibility first;
- only source labels needed to reconstruct DEV-DISCOVERY UTC days 2024-03-01..20;
- no E006 Confirmation spot body access yet;
- no basis calculation;
- no paired return/P&L;
- no L2 acquisition;
- no Q2/Validation/Final.

Any data-stage ambiguity leaves E006 alpha closed.

## 8. E006 economics warning

A paired strategy has two instruments and therefore more execution cost than a one-leg scalp.

The executable protocol must normalize paired gross edge and fee burden explicitly before alpha. Four taker fills are required for a two-leg open/close cycle, so a several-bps effect is automatically uninteresting.

The eventual gross-economics hurdle must demand meaningful several-tens-of-bps headroom before paired L2 work.

The exact numerical hurdle, synchronization statistic, basis baseline/threshold and exit rule are **not yet frozen** and may not be selected from E006 returns.

## 9. Required E006 order

1. Data-only historical SPOT feasibility preflight.
2. If data PASS: final financial/mathematical/programming audit.
3. Freeze exact executable E006 protocol before first basis/return output.
4. Freeze implementation and run no-alpha preflight.
5. Run DEV-DISCOVERY only after preflight PASS.
6. If Discovery PASSes every frozen gate: unchanged one-time DEV-CONFIRMATION.
7. Only after both gross stages PASS: paired L2/execution economics.
8. Later protected temporal validation only after a separately frozen promotion decision.

No stage may be skipped.

## 10. Base-feature firewall

Base E006 must not use:

- E002 TFI;
- E003 FLOW_IMPULSE;
- E004 compression state;
- post-hoc event/day/hour exclusions;
- a basis sign selected because its observed P&L is better.

Any auxiliary feature requires an independently viable base and a new frozen experiment.

## 11. Infrastructure

Primary heavy compute remains the qualified Timeweb Cloud VPS:

- Ubuntu 24.04;
- 4 vCPU;
- 8 GB RAM;
- 80 GB NVMe;
- non-root `botmarket`;
- SSH public-key authentication;
- tmux.

Android/Termux remains the control client.

Never store IPs, passwords, private SSH keys, API keys or credentials in GitHub.

## 12. Immediate next action

Create a fail-closed **E006 data-only SPOT feasibility preflight**. It may query/record public historical-data metadata and, only after identities are unambiguous, acquire the March source labels required for Discovery reconstruction.

The stage must emit only data-integrity facts: source identity, size/hash, schema, timestamp/order coverage and UTC reconstruction feasibility.

It must not calculate spot/perpetual basis, convergence, returns or P&L.
