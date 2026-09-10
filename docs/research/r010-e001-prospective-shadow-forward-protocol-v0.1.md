# R010-E001 — Prospective Shadow-Forward Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R010 — Drawdown-Armed Recovery  
**Experiment:** E001 — BTC prospective shadow-forward  
**Date:** 2026-09-10  
**Status:** frozen before the 2026-09-10 UTC daily bar closes and before any R010 forward P&L  
**Parent hypothesis:** `docs/research/r010-drawdown-armed-recovery-hypothesis-v0.1.md`  
**Research posture:** prospective-only evidence; no historical optimization; R009-E002 remains unchanged

## 1. Objective

R009 cross-asset diagnostics identified a structural weakness in the sticky crisis sleeve: crisis exposure can remain active for very long periods while an asset remains below its prior ATH.

R010 tests a distinct economic role for the same already-inspected primitives:

> **Drawdown arms recovery capital; trend confirmation permits deployment.**

R010 is not a patch to R009 and may not overwrite, pause or reset R009-E002.

The primary forward question is:

> Does keeping drawdown-armed capital in cash while SMA120 trend is OFF, then permitting that armed capital to participate only while the same trend state is ON, improve the prospective growth/drawdown tradeoff relative to frozen R009 and simpler comparators without adding new numeric tuning degrees of freedom?

## 2. Frozen market and source

Use Binance Spot `BTCUSDT` UTC daily klines from the public market-data-only endpoint family:

- base: `https://data-api.binance.vision`;
- endpoint: `GET /api/v3/klines`;
- interval: `1d`;
- only fully closed daily bars whose close timestamp is strictly in the past may enter state or P&L.

Do not silently substitute another venue, symbol or source. A permanent source change requires a versioned protocol revision and cannot overwrite E001.

## 3. Historical state initialization versus forward evidence

R010 is path dependent.

Pre-inception BTC history may be used only to initialize:

- SMA120;
- running closing-price ATH;
- which drawdown tranches are already armed at the forward boundary.

Pre-inception R010 P&L is prohibited.

The already inspected BTC/ETH/BNB/LTC/XRP/ADA/SOL histories remain contaminated for confirmatory R010 efficacy. This E001 tracker does not backtest R010 on them.

## 4. Frozen state machine

### 4.1 TREND10

- SMA lookback = 120 fully closed daily bars;
- trend ON iff `close_t > SMA120_t`;
- trend target = 10% BTC when ON, otherwise 0%;
- state known at daily close `t` applies to the next close-to-close interval.

### 4.2 Drawdown arming

Maintain a running closing-price ATH.

Four recovery tranches are armed at the same already-existing R009 drawdown levels:

- first 2.5pp at -20%;
- second 2.5pp at -35%;
- third 2.5pp at -50%;
- fourth 2.5pp at -65%.

A tranche becomes armed on the first closing-price breach of its level within the current ATH episode.

Armed state by itself creates **no BTC exposure** while TREND10 is OFF.

### 4.3 Recovery deployment

Let:

`armed_weight = 2.5% × number_of_armed_tranches`

Then:

- if TREND10 is OFF: `RECOVERY10 target = 0%`;
- if TREND10 is ON: `RECOVERY10 target = armed_weight`.

Therefore:

`R010 target = TREND10 target + RECOVERY10 target`

Total desired BTC target remains between 0% and 20%.

If trend turns OFF after recovery capital has been deployed, recovery exposure returns to cash at that close while the arming memory remains.

If trend later turns ON again while tranches are still armed, the armed recovery weight is again permitted to deploy.

No hysteresis, cooldown, expiry, holding-period parameter, volatility filter, second moving average or leverage is allowed.

## 5. Frozen reset semantics

All armed tranches reset to unarmed **only on a new closing-price ATH**.

This reset is chosen prospectively because it reuses the existing R009 state primitive and adds no new numerical parameter. It is not selected from a historical grid and is not claimed to be optimal.

On a new closing ATH:

- running ATH updates;
- all four armed flags reset to false;
- recovery target becomes 0%;
- TREND10 remains independently determined by `close > SMA120`.

No time-based expiry is allowed in E001.

## 6. Fixed prospective boundary

This protocol is frozen during 2026-09-10 UTC before the 2026-09-10 daily bar is fully closed.

Therefore:

- the fully closed 2026-09-10 UTC bar may be used after close to determine the first R010 forward target;
- formal forward inception is **2026-09-11 00:00:00 UTC**;
- the first realized forward daily interval, when available, is the BTCUSDT close-to-close return from the 2026-09-10 close to the 2026-09-11 close, held at the target determined from the 2026-09-10 closed bar;
- a later first tracker run must reconstruct causally from this same boundary and may not move inception forward.

The 2026-09-10 signal bar is post-freeze state information even though realized P&L begins with the next complete daily interval.

## 7. Canonical accounting

Use the same self-financing daily target accounting convention as R009-E002.

At each fully closed day:

1. prior BTC allocation experiences the realized close-to-close BTC return;
2. the risky weight drifts naturally;
3. compute the new desired target from the newly closed bar;
4. rebalance conceptually at the close;
5. charge cost on actual traded portfolio notional;
6. hold the new target for the next daily interval.

Cost tracks:

- 5 bps;
- **10 bps baseline**;
- 25 bps;
- 50 bps.

Cash return = 0% for direct comparability with R009-E002.

## 8. Frozen comparators

Track from the same R010 inception:

- `R010_COMBINED_DAILY`;
- `RECOVERY10_DAILY`;
- `R009_COMBINED_DAILY` using the same initialized armed flags but with armed drawdown weight deployed regardless of trend;
- `TREND10_DAILY`;
- `STATIC10_DAILY`;
- `STATIC15_DAILY`;
- `STATIC20_DAILY`.

No comparator may be added or removed after viewing forward results inside E001.

## 9. Prospective mechanism-event diagnostics

Because pre-inception history may initialize existing armed tranches, inherited arming cannot by itself validate the R010 mechanism.

Track separately from the post-freeze 2026-09-10 signal bar onward:

- number of newly armed tranche breaches;
- number of days with trend OFF while one or more tranches are armed;
- recovery activation events, defined as a positive increase in `RECOVERY10 target` caused by either a new arming breach while trend is already ON or a trend OFF→ON transition while armed;
- recovery deactivation events;
- new-ATH reset events.

A strong mature interpretation requires at least one prospective arming event and at least one prospective recovery activation event. If 365 forward days elapse without those mechanism events, continue the forward record rather than declaring R010 validated.

## 10. Evidence threshold and review cadence

The tracker may run at any time, but only fully closed daily bars count.

No terminal positive or negative strategy conclusion before at least **365 realized forward daily intervals**, except an operational/data failure may invalidate the implementation record.

Allowed descriptive checkpoints are quarterly. No rule change is allowed at checkpoints.

After 365 days:

- if the prospective mechanism-event requirement has also been observed, classify the sample as ready for formal mature review;
- otherwise continue under `365D_REACHED_WAITING_FOR_MECHANISM_EVENT`.

## 11. Mature review framework

Possible eventual classifications:

- `FORWARD_SUPPORTIVE`;
- `FORWARD_NEUTRAL_CONTINUE`;
- `FORWARD_NEGATIVE`.

Broad support would require, after sufficient evidence:

- R010 is economically useful relative to TREND10 and frozen R009 on the same forward path;
- recovery gating materially reduces unwanted distressed exposure while trend is OFF rather than simply sacrificing all crisis/recovery participation;
- R010 is not clearly dominated by simple STATIC10/15 comparators on growth/drawdown terms;
- conclusions remain coherent under 25/50 bps shadow costs;
- at least one prospective arming and recovery-activation cycle has actually occurred;
- no source/state/accounting discrepancy invalidates causal tracking.

A favorable short run is not evidence of antifragility.

## 12. Relationship to antifragility objective

R010 remains a controlled long-beta recovery architecture. Even if forward-supportive, it does not by itself create true convexity or prove antifragility.

The broader architecture may still require an orthogonal bounded-convexity sleeve plus a genuinely safe/off-venue reserve and separately validated carry.

## 13. Required outputs

Keep the user-facing package <=10 files:

1. `r010_e001_run_state.json`
2. `r010_e001_source_audit.json`
3. `r010_e001_state_history.csv`
4. `r010_e001_forward_daily.csv`
5. `r010_e001_forward_metrics.csv`
6. `r010_e001_state_events.csv`
7. `r010_e001_summary.md`

## 14. Anti-overfitting freeze

During R010-E001 do not change:

- BTCUSDT / Binance daily source;
- SMA120;
- 10% trend sleeve;
- -20/-35/-50/-65 arming levels;
- four 2.5pp recovery tranches;
- maximum 10% recovery sleeve;
- trend-gated recovery deployment rule;
- new-closing-ATH reset;
- total 0-20% target range;
- no leverage;
- daily self-financing accounting;
- 5/10/25/50 bps cost tracks;
- cash return 0%;
- comparator set;
- fixed 2026-09-11 UTC forward inception;
- mature evidence and mechanism-event requirements.

Any material change creates a new candidate/version and cannot overwrite this forward record.