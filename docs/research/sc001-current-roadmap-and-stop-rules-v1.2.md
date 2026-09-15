# SC001 Current Roadmap and Stop Rules v1.2

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**

Supersedes for current branch execution order: `docs/research/sc001-current-roadmap-and-stop-rules-v1.1.md`.

## 1. Independence retained

SC001 remains fully independent from R009-E002, R003-E003, R003-X003, R010-E001 and Safe-Sleeve S002. Nothing in SC001 may retrospectively alter their rules, clocks, parameters or interpretation.

## 2. Research firewall retained

Formal Validation and Final remain unopened. For the March-2024 microstructure work already opened in DEV, use the same protected split discipline:

- DEV-DISCOVERY: 2024-03-01 through 2024-03-20;
- one-time DEV-CONFIRMATION: 2024-03-21 through 2024-03-30;
- all 2024-Q2 raw bodies remain closed unless a separately frozen candidate earns promotion;
- formal Validation and Final remain closed.

## 3. E001 terminal result

SC001-E001, one-hour extreme-move mean reversion, remains terminal `FAIL`.

Key lesson: the frozen one-hour reversal proposition did not possess a meaningful gross edge before transaction costs. It must not be rescued with post-hoc filters or retuning.

## 4. E002 terminal result and reusable knowledge

E002 standalone taker economics remains terminal `TAKER_ECONOMICS_FAIL`.

However, E002 should be retained as:

**confirmed predictive microstructure feature; rejected standalone taker strategy.**

Evidence preserved:

- Binance discovery: 15/15 positive days;
- Binance chronological confirmation: 10/10 positive days;
- OKX transaction-price replication: 5/5 positive days;
- OKX Q1 causal L2 midquote confirmation: 4/4 positive days at 100 ms and 4/4 positive at 250 ms;
- executable taker economics failed because pre-fee edge was only a few hundredths of a bp while the frozen regular-user round-trip taker fee burden was about 10 bps.

Reusable role for E002 TFI:

- auxiliary filter / veto;
- confidence / ranking feature;
- execution-timing / adverse-selection feature;
- ensemble / meta-model feature.

It must not be reused as a standalone frequent BUY/SELL engine by default.

## 5. E003 terminal result and reusable knowledge

SC001-E003 rare flow-impulse continuation ended with terminal `E003_DISCOVERY_FAIL`.

Frozen primary `q99.5 / 250 ms / 60 s`:

- completed trades: 1640;
- completion rate: 1.0;
- pooled mean gross edge: about -0.118 bps;
- pooled median gross edge: about -0.117 bps;
- median daily mean gross edge: about -0.047 bps;
- positive daily mean days: 9/20.

The 500 ms stress was also slightly negative. E003 failed before fees and before L2. Therefore this is not an execution-cost failure like E002; the frozen continuation mechanism itself did not produce a sufficiently positive gross edge.

Read-only diagnostics suggested a short-lived response profile: approximately +0.08 bps at 30 s, around -0.12 bps at 60 s and more negative by 120 s. This is research knowledge only and may not rescue E003.

E003 confirmation remains unopened. No E003 L2 is acquired. Q2/Validation/Final remain closed.

## 6. Consolidated lessons from E001-E003

The next candidate should satisfy all of the following before expensive L2 work:

1. **Economics first.** Candidate mechanisms must plausibly generate moves measured in many bps, not hundredths of a bp.
2. **Turnover constrained.** Thousands of tiny round trips are unattractive under regular-user taker costs.
3. **Do not merely chase an already-completed micro move.** E002/E003 show that post-flow residual movement is too small for standalone taker trading.
4. **Use robust distribution diagnostics.** Mean alone is insufficient; inspect median, trimmed mean, day breadth and concentration.
5. **Auxiliary features come later.** E002 TFI may be tested only after an independently viable base strategy exists.
6. **No maker/queue claims yet.** Aggregated 400-level L2 is insufficient for honest queue-position / maker-fill modelling.
7. **No rescue tuning.** Failed frozen candidates stay failed.

## 7. Next priority candidate: E004

Priority is now:

**SC001-E004 — causal volatility-compression -> breakout / expansion.**

Rationale:

- unlike E002/E003, the design aims to enter near the transition from low volatility to expansion rather than after a flow event has largely occurred;
- rare breakouts can plausibly generate tens of bps, compatible with the cost hurdle;
- trade-tape data remove the intrabar-ordering ambiguity that previously made this family awkward on 1h OHLC alone;
- expected turnover can be materially lower than E002/E003.

E004 must begin with a trade-tape-only gross-economics Discovery screen. No L2 is allowed until the gross hurdle is passed in Discovery and then unchanged Confirmation.

## 8. E004 protocol-design requirements before first result

Before any E004 output is observed, freeze:

- exact compression statistic;
- exact causal lookback;
- exact breakout level;
- breakout confirmation semantics;
- latency;
- holding / exit rule;
- non-overlap / conflict handling;
- one-position maximum;
- no overnight carry;
- turnover ceiling;
- primary economics hurdle;
- stress/diagnostic neighborhood;
- robust statistics and concentration gates.

Current design target, subject to final pre-test audit before freeze:

- use March trade tape only;
- Discovery 2024-03-01..20;
- Confirmation 2024-03-21..30 only if Discovery PASSes;
- regular-user taker economics remains the reference hurdle;
- primary gross-edge hurdle should have a safety margin over ~10 bps round-trip cost, with approximately 15 bps as the design target rather than a 12 bps near-break-even threshold;
- robust gates should include pooled mean, trimmed mean, pooled median, median daily mean, positive-day breadth and concentration control;
- E002/E003 features are excluded from E004 base entry logic.

## 9. E005 reserved role

Only if E004 becomes independently economically viable may a separately frozen E005 test whether E002 TFI adds **incremental** value to the E004 base strategy.

E005 may compare:

- base E004 alone;
- E004 + TFI confirmation / veto / ranking.

The objective is incremental expectancy and/or reduced bad-trade frequency without creating a new standalone TFI round trip.

E005 must not be used to rescue a failed E004.

## 10. Lower-priority candidates

Simple large-price-jump continuation/reversal remains a legitimate future family, but is lower priority than E004 because it enters after a large move has already occurred and risks repeating the residual-edge problem seen in E002/E003.

Cross-venue arbitrage and maker/queue strategies remain deferred until data support honest synchronized multi-venue or queue-position modelling.

## 11. VPS status

The Timeweb Frankfurt VPS is now the qualified primary heavy-compute environment for SC001.

Known successful qualification already completed:

- Ubuntu/Python/git/tmux environment audit;
- non-root `botmarket` user;
- SSH key authentication and SSH hardening;
- GitHub/OKX/Binance outbound access;
- Q008 parity test reproduced exact archive SHA256 and replay metrics;
- E002 Q1 confirmation and taker-economics completed successfully on VPS;
- E003 March trade acquisition/verification completed successfully on VPS.

Do not store IPs, passwords, private keys or credentials in GitHub.

## 12. Immediate next action

In the next clean dialog:

1. read `docs/research/dialog-handoff-2026-09-15-v3.0.md`;
2. read this roadmap v1.2;
3. read `docs/research/sc001-e004-volatility-compression-breakout-research-plan-v0.1.md`;
4. perform final E004 mathematical/programming audit;
5. freeze exact E004 protocol before first E004 alpha output;
6. implement preflight and only then run DEV-DISCOVERY.
