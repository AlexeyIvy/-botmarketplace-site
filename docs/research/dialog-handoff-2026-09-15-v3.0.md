# Dialog Handoff — 2026-09-15 v3.0

Project: BotMarketplace / BotMarketplace.store  
Branch: SCALPING RESEARCH / SC001  
Repository: `AlexeyIvy/-botmarketplace-site`

## 1. Read first in the new dialog

Primary context:

1. `docs/research/dialog-handoff-2026-09-15-v3.0.md`
2. `docs/research/sc001-current-roadmap-and-stop-rules-v1.2.md`
3. `docs/research/sc001-e004-volatility-compression-breakout-research-plan-v0.1.md`

Background/reference:

- `docs/research/sc001-e002-reusable-lessons-v0.1.md`
- `docs/research/sc001-e003-discovery-results-v0.1.md`
- `docs/research/dialog-handoff-2026-09-14-v2.0.md`
- `docs/research/dialog-handoff-2026-09-11-v1.0.md`

## 2. Hard independence boundary

SC001 is independent. It must not retrospectively change, retune, merge with or reinterpret:

- R009-E002;
- R003-E003 Binance;
- R003-X003 Bybit;
- R010-E001;
- Safe-Sleeve S002.

No result in SC001 changes any of their forward clocks or rules.

## 3. Current infrastructure

Primary heavy-compute environment is the qualified Timeweb Cloud VPS:

- Frankfurt;
- Ubuntu 24.04 LTS;
- 4 vCPU;
- 8 GB RAM;
- 80 GB NVMe;
- non-root user `botmarket`;
- SSH public-key authentication configured;
- root/password SSH hardened after key-login verification;
- GitHub/OKX/Binance outbound access verified;
- tmux available;
- Q008 2024-01-05 parity test reproduced exact archive SHA256 and replay metrics.

Android/Termux remains the control client, not the primary heavy-compute runtime.

Never put server IP, passwords, private SSH keys, API keys or credentials in GitHub.

## 4. E001 status

SC001-E001 one-hour extreme-move mean-reversion is terminal `FAIL`.

The specific one-hour reversal proposition did not show a meaningful gross edge and must not be rescue-tuned.

## 5. E002 status

E002 mechanism: frozen 5-second aggressive trade-flow imbalance (TFI) continuation.

Evidence ledger:

- Binance Discovery: 15/15 positive days;
- Binance chronological Confirmation: 10/10 positive days;
- OKX transaction-price replication: 5/5 positive days;
- OKX Q1 causal L2 midquote confirmation: terminal `MIDQUOTE_CONFIRMATION_PASS`;
- 100 ms: 4/4 positive daily Spearman, median about 0.06474;
- 250 ms: 4/4 positive, median about 0.05864.

Executable taker economics then ended terminal:

`TAKER_ECONOMICS_FAIL`

Reason:

- positive gross/pre-fee edge survived;
- depth/completion was not binding;
- funding was negligible;
- regular-user round-trip taker fee was about 10 bps;
- pre-fee executable edge was only a few hundredths of a bp;
- net edge was roughly -9.9 bps/trade.

Interpretation to preserve:

**E002 = confirmed predictive microstructure feature; rejected standalone taker strategy.**

Reusable future roles:

- auxiliary veto/filter;
- ranking/confidence feature;
- execution-timing/adverse-selection feature;
- ensemble/meta-model feature.

Do not reopen E002 Q2 and do not rescue E002 standalone economics.

## 6. E003 status

E003 mechanism: rare FLOW_IMPULSE continuation normalized by recent activity.

Protocol:

- Discovery: 2024-03-01..20;
- protected Confirmation: 2024-03-21..30;
- q99.5 causal threshold;
- 250 ms primary latency;
- 60 s horizon;
- coarse pooled gross hurdle >= 12 bps.

March trade acquisition:

- archives 2024-03-01..31 downloaded and locally verified;
- 31/31 PASS;
- Q2/Validation/Final stayed closed.

Terminal Discovery result:

`E003_DISCOVERY_FAIL`

Primary q99.5 / 250 ms / 60 s:

- completed trades: 1640;
- completion rate: 1.0;
- pooled mean gross edge: about -0.118 bps;
- pooled median gross edge: about -0.117 bps;
- median daily mean gross edge: about -0.047 bps;
- positive daily mean days: 9/20.

500 ms stress also slightly negative.

Read-only diagnostics suggested approximately:

- 30 s: small positive mean around +0.08 bps;
- 60 s: around -0.12 bps;
- 120 s: around -0.46 bps;
- q99.75 / 60 s: around -0.21 bps pooled mean.

Interpretation:

- E003 is not an execution-cost failure;
- the frozen gross continuation mechanism itself failed;
- stronger flow intensity did not create a large residual move;
- diagnostics may inform future hypotheses but cannot rescue E003.

Do not run E003 Confirmation. Do not acquire E003 L2. Keep Q2/Validation/Final closed.

## 7. Consolidated research lesson

The central cost/economics lesson from E001-E003:

- small statistically real effects are insufficient when round-trip taker cost is ~10 bps;
- future standalone candidates should target natural movement measured in many bps;
- turnover must be constrained early;
- expensive L2 work should happen only after a strong gross-economics screen;
- pooled mean alone is insufficient; future gates should include median, trimmed mean, day breadth and concentration control;
- E002 TFI should be saved for a later incremental-value test on top of an independently viable base strategy.

## 8. Next priority: E004

New priority candidate:

**SC001-E004 — causal volatility-compression -> breakout / expansion.**

Why:

- enters near a low-volatility -> expansion transition rather than simply chasing post-flow residual movement;
- can plausibly produce tens-of-bps moves;
- expected turnover can be much lower than E002/E003;
- current trade tape permits causal breakout timing without hourly OHLC ambiguity.

E004 base strategy must exclude E002 TFI and E003 FLOW_IMPULSE filters.

Initial data boundary:

- Discovery: 2024-03-01..20;
- Confirmation: 2024-03-21..30 only after Discovery PASS;
- no new L2 during Discovery;
- Q2/Validation/Final remain closed.

## 9. E004 is not yet fully frozen

Important: `sc001-e004-volatility-compression-breakout-research-plan-v0.1.md` is a planning document, not the executable freeze.

In the new dialog, first perform a final mathematical/programming review and then freeze exact:

- compression statistic;
- lookback/warm-up;
- breakout band/level;
- breakout confirmation semantics;
- decision timestamp;
- entry latency;
- holding/exit rule;
- non-overlap/conflict logic;
- turnover ceiling;
- robust gates;
- diagnostic neighborhood.

Current design preference:

- trade-tape-only first-stage screen;
- primary gross-edge hurdle with meaningful margin over ~10 bps costs, target around 15 bps rather than a near-break-even 12 bps;
- robust metrics to include pooled mean, trimmed mean, pooled median, median daily mean, positive-day breadth and concentration limits.

No E004 alpha should be computed until the exact protocol is committed.

## 10. E005 reserved

Only if E004 becomes independently economically viable, create a separate E005 to test incremental value of E002 TFI on top of E004.

E005 must compare base E004 versus E004+TFI as a filter/ranker/timing input. It must not rescue a failed E004 and must not revive standalone TFI.

## 11. Lower-priority future work

Large-price-jump continuation/reversal is retained as a later candidate family, but lower priority than E004 because it enters after a large move has already happened and may repeat the residual-edge problem.

Maker/queue strategies are deferred because current aggregated L2 does not support honest queue-position fill modelling. Cross-venue arbitrage is deferred until synchronized multi-venue data are qualified.

## 12. Immediate first task in next dialog

Do not run a new strategy immediately.

First:

1. review E004 plan critically as financial researcher, mathematician and programmer;
2. settle exact causal formula and gates;
3. create a frozen E004 protocol in GitHub;
4. create implementation preflight;
5. only after preflight PASS, run E004 DEV-DISCOVERY.
