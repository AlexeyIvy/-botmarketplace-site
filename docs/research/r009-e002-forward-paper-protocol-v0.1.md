# R009-E002 — Forward Paper Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R009 — Antifragile Trend-Gated Dry-Powder Barbell  
**Experiment:** E002  
**Date:** 2026-09-09  
**Status:** pre-forward frozen specification  
**Parent result:** `docs/research/r009-e001-results-v0.1.md`  
**Research posture:** forward-only evidence; no historical rescue tuning

## 1. Objective

R009-E001 passed the in-sample mechanism screen but cannot receive independent historical PASS because the BTC history used to design and evaluate the architecture was already inspected.

E002 creates a genuine forward paper record.

Primary question:

> Does the exact frozen R009 v0.1 architecture continue to deliver a useful growth/drawdown tradeoff on future, fully closed executable BTC spot bars without parameter changes?

No E001 parameter may change during E002.

## 2. Frozen R009 architecture

### TREND10

- SMA lookback = 120 fully closed daily bars;
- ON if `close_t > SMA120_t`;
- 10% BTC target when ON, otherwise 0%;
- state at t applies to the next daily return interval.

### CRISIS10

- crisis reserve = 10% NAV;
- four equal 2.5pp tranches;
- running closing-price ATH drawdown triggers: -20%, -35%, -50%, -65%;
- first breach deploys the tranche;
- deployed tranche stays active until a new closing ATH;
- at new ATH all crisis tranches reset to cash;
- target range 0-10% BTC.

### Combined

`R009 target = TREND10 target + CRISIS10 target`

Total desired BTC target range: 0-20%.

No leverage, shorts, volatility targeting, new indicators, interaction overrides, hysteresis, cooldown, or retuned thresholds.

## 3. Forward executable/reference source

Use Binance Spot `BTCUSDT` daily klines from the public market-data endpoint family.

Primary base endpoint:

`https://data-api.binance.vision`

Endpoint:

`GET /api/v3/klines`

Parameters:

- symbol = BTCUSDT;
- interval = 1d;
- UTC daily bars;
- only bars whose close timestamp is strictly in the past may enter state or P&L.

The public market-data-only base endpoint is chosen to avoid account/API-key dependence.

If the endpoint is temporarily unavailable, do not substitute another venue silently. Record source failure and retry later. A permanent source change requires a protocol revision before using the new data for forward decisions.

## 4. State initialization versus forward P&L

R009 is path dependent.

Historical Binance spot bars before forward inception may be used **only** to initialize:

- SMA120;
- running closing ATH;
- currently deployed crisis tranches.

No pre-inception Binance P&L may be included in the forward record.

The forward performance clock is separate from state warmup.

## 5. Forward inception

Protocol and implementation are frozen during 2026-09-09 before the 2026-09-09 UTC daily bar is fully closed.

Therefore:

- the 2026-09-09 UTC bar may be used after it becomes fully closed to determine the first forward target;
- the first forward return interval is the next complete daily interval;
- formal paper inception timestamp: **2026-09-10 00:00:00 UTC**;
- first realized forward daily return, when available, is the BTCUSDT close-to-close return from 2026-09-09 close to 2026-09-10 close, using the target determined from the 2026-09-09 closed bar.

If the first tracker run occurs later, the engine must reconstruct the record causally from this fixed inception. It may not move inception forward.

## 6. Canonical accounting

Use the same E001 `SELF_FINANCING_DAILY_TARGET` convention.

At each fully closed daily bar:

1. prior BTC allocation experiences the realized BTC close-to-close return;
2. the BTC portfolio weight drifts naturally;
3. compute the new desired target from that bar's fully known state;
4. rebalance at the close conceptually to the new target;
5. charge fee on actual traded portfolio notional required to move from pre-trade weight to desired target;
6. hold the new target for the next daily interval.

Paper baseline cost: **10 bps** per traded notional.

Shadow cost tracks:

- 5 bps;
- 25 bps;
- 50 bps.

Cash return: **0%** to preserve comparability with E001.

## 7. Forward comparators

Track in parallel from the exact same inception:

- R009_COMBINED_DAILY;
- TREND10_DAILY;
- CRISIS10_DAILY;
- STATIC10_DAILY;
- STATIC15_DAILY;
- STATIC20_DAILY.

For practical context also track:

- STATIC15_MONTHLY.

No new comparator weight may be selected after seeing forward results.

## 8. Required persistent outputs

The forward tracker must persist or regenerate causally:

1. source audit / latest closed-bar metadata;
2. current R009 state and target;
3. full forward daily paper record from fixed inception;
4. forward metrics by strategy and fee assumption;
5. forward trade/rebalance log;
6. compact summary.

Keep the user-facing run package at **10 files or fewer** whenever possible.

## 9. Forward metrics

Track from inception:

- cumulative return / ending multiple;
- annualized return only once enough observations make it meaningful;
- annualized volatility;
- Max Drawdown;
- Calmar when meaningful;
- average and maximum BTC exposure;
- turnover;
- modeled fee drag;
- worst month / quarter when available;
- daily VaR/CVaR only as descriptive diagnostics.

Also preserve all daily desired targets and realized pre-trade weights for audit.

## 10. Review cadence and evidence threshold

The tracker may be run at any time, but only fully closed daily bars count.

Formal research reviews:

- quarterly descriptive checkpoints are allowed;
- no parameter changes are allowed at checkpoints;
- no positive/negative terminal conclusion should be drawn before at least **365 forward daily intervals**;
- because the crisis sleeve is state dependent, a strong promotion decision additionally requires at least one forward -20% drawdown breach after inception. If 365 days pass without such a breach, continue the forward record rather than declaring the crisis component validated.

No arbitrary stopping after a favorable or unfavorable short run.

## 11. Forward decision framework

E002 does not promise a binary decision at a fixed calendar date. After sufficient forward evidence, classify:

### FORWARD_SUPPORTIVE

Broadly require:

- combined remains economically useful versus STATIC10 and TREND10;
- combined is not clearly dominated by STATIC15 daily/monthly;
- drawdown remains materially below STATIC20 for comparable periods;
- crisis sleeve contributes positively during at least one observed forward stress episode rather than only increasing beta;
- conclusions survive the 25/50 bps shadow cost tracks;
- no operational/state discrepancies invalidate causal tracking.

### FORWARD_NEUTRAL / CONTINUE

Use if sample is still too short/event-poor or comparisons are mixed.

### FORWARD_NEGATIVE

Use if sufficient forward evidence shows that:

- combined is persistently dominated by simple comparators;
- crisis sleeve adds little/negative value to TREND10;
- drawdown advantage disappears while complexity/turnover remains;
- or the architecture fails under realistic costs.

No parameter rescue may follow directly from a negative forward result on the same sample.

## 12. Safe-sleeve interpretation

Paper cash is a zero-yield USD bookkeeping asset only.

This does **not** specify production custody.

Before any implementation promotion, separately model:

- fiat / Treasury-bill safe sleeve;
- stablecoin depeg risk if used;
- exchange/custodian concentration;
- transfer availability during crisis;
- safe-sleeve yield;
- execution spreads/slippage.

The large cash allocation is part of the risk architecture and cannot be treated as operationally riskless in production.

## 13. Anti-overfitting freeze

During E002 do not change:

- SMA120;
- 10% trend sleeve;
- 10% crisis reserve;
- 2.5% x4 crisis tranches;
- -20/-35/-50/-65 thresholds;
- sticky-to-new-ATH crisis reset;
- additive sleeve rule;
- daily self-financing accounting;
- comparator set;
- fixed inception;
- fee assumptions;
- cash return assumption.

Any change creates a new candidate/version and cannot be merged into the existing forward record.