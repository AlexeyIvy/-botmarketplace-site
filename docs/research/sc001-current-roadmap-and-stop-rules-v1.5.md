# SC001 Current Roadmap and Stop Rules v1.5

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**

Supersedes for current SC001 execution order:

`docs/research/sc001-current-roadmap-and-stop-rules-v1.4.md`

## 1. Preserved independence and terminal decisions

SC001 remains fully independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Nothing in SC001 may retrospectively alter their rules, decisions or forward clocks.

Terminal SC001 history now stands as follows:

- E001: terminal `FAIL`; no rescue tuning;
- E002: terminal standalone `TAKER_ECONOMICS_FAIL`; TFI retained only as a possible future auxiliary/filter/ranking/execution-timing/meta-model feature;
- E003: terminal `E003_DISCOVERY_FAIL`; no Confirmation/L2/rescue;
- E004: terminal `E004_DISCOVERY_FAIL`; no Confirmation/L2/rescue.

Q2, formal Validation and Final remain closed.

## 2. E004 terminal result

Canonical E004 financial protocol remains frozen for the historical record:

`docs/research/sc001-e004-volatility-compression-breakout-executable-protocol-v1.0.md`

Terminal results are recorded in:

`docs/research/sc001-e004-discovery-results-v1.0.md`

The frozen primary 250 ms result failed the central gross-economics gates by a very large margin:

- pooled mean gross edge approximately +0.179 bps versus >=20 bps required;
- 10% trimmed mean approximately +1.054 bps versus >=15 bps;
- pooled median approximately +1.662 bps versus >=10 bps;
- median active-day mean approximately -1.753 bps versus >=12 bps;
- positive active-day share approximately 47.4% versus >=70%;
- day-block bootstrap lower bound approximately -3.934 bps versus >10 bps.

500 ms and 1,000 ms latency stresses were also near zero and failed their frozen hurdles.

This is classified as a gross-mechanism failure, not an execution-cost failure.

## 3. E004 stop rule

Effective immediately:

- do not run E004 DEV-CONFIRMATION;
- do not acquire E004 L2;
- do not open Q2/Validation/Final for E004;
- do not replace the failed primary with any diagnostic variant;
- do not add TFI/FLOW_IMPULSE, side filters, event filters, hour-of-day filters, alternate hold, buffer, compression percentile/window or lower economics hurdles to rescue E004.

The exact terminal verdict remains:

`E004_DISCOVERY_FAIL`

## 4. E004 read-only postmortem

The eight diagnostic variants frozen in E004 v1.0 may now be run once strictly as read-only postmortem research knowledge.

Their purpose is only to learn whether the primary failure is locally stable or whether a materially different future hypothesis might deserve a new experiment identifier.

They cannot:

- alter E004's terminal verdict;
- open Confirmation;
- promote an alternate E004 parameter;
- authorize L2/Q2/Validation/Final;
- select the best-looking diagnostic as a replacement strategy.

## 5. E005 remains closed

E005 had been reserved for an incremental-value test of E002 TFI on top of an independently viable E004 base strategy.

Because E004 failed, the prerequisite for E005 is not satisfied. Therefore E005 is not opened.

TFI remains preserved only for a future independently viable base strategy under a separately frozen experiment.

## 6. Consolidated lesson after E001-E004

Four candidates now reinforce a stronger research prior:

1. Small predictive effects are not sufficient for standalone taker scalping under an approximately 10 bps round-trip regular-user fee reference.
2. Post-event residual continuation has repeatedly been tiny relative to that cost scale.
3. A future standalone candidate must plausibly capture movement at a natural tens-of-bps scale before L2 work.
4. Turnover should stay low and event selection must be frozen before output.
5. Mean alone is insufficient; day breadth, trimmed/median behavior, bootstrap robustness and concentration controls remain mandatory.
6. L2 engineering is downstream of gross-economics evidence, not a substitute for it.
7. Failed candidates remain failed; diagnostics are knowledge capture, not rescue tuning.

## 7. Next research stage

Immediate sequence:

1. run the already-frozen E004 read-only diagnostic neighborhood once;
2. document the diagnostic postmortem without changing the E004 verdict;
3. choose a genuinely new SC001 candidate family under a new experiment identifier;
4. freeze its exact causal/economic protocol before any new alpha output;
5. require an economics-first gross screen before L2.

A previously retained lower-priority family is large-price-jump continuation/reversal, but it should not be promoted automatically merely because E004 failed. The next candidate should be selected after reviewing the full E001-E004 evidence and asking which mechanism has a credible path to tens-of-bps movement rather than another tiny residual effect.

## 8. Infrastructure

Primary heavy compute remains the qualified Timeweb Cloud VPS:

- Ubuntu 24.04;
- 4 vCPU;
- 8 GB RAM;
- 80 GB NVMe;
- non-root `botmarket`;
- SSH public-key authentication;
- tmux.

Android/Termux remains the control client.

Do not store IPs, passwords, private SSH keys, API keys or credentials in GitHub.

## 9. Immediate next action

Run only the frozen E004 diagnostic mode on the already-completed Discovery record. Do not run Confirmation.

After diagnostic postmortem, select/freeze the next independent candidate before any further alpha computation.
