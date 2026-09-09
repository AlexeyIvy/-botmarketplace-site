# R008 — Antifragile Crisis-Opportunity Barbell Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Research Candidate:** R008  
**Status:** pre-result research specification  
**Date:** 2026-09-09  
**Research posture:** falsification-first, no hidden parameter optimization  
**Purpose:** test whether a cash-heavy portfolio that deploys a small pre-budgeted reserve into BTC only during increasingly severe drawdowns can improve geometric growth and crisis response relative to simpler BTC/cash portfolios.

---

## 1. Why R008 exists

R002 showed that slow trend following can materially reduce downside relative to naive passive exposure, but the corrected complete Binance archive-defined wide-universe implementation did not produce convincing post-2023 economics and is therefore FINAL REDESIGN / NOT PASS for broad-universe deployment.

R001 showed genuine option convexity in crises, but persistent premium drag and weak late-period economics prevented promotion of the tested option implementations.

R008 therefore returns to the broader antifragility question without trying to rescue R001 or R002:

> Can a simple payoff architecture preserve most capital in cash, keep a small permanent growth sleeve, and systematically increase exposure only as market stress becomes more severe, so that large shocks create increasing opportunity rather than only damage?

R008 is a new economic hypothesis. It is not an indicator overlay on R002.

---

## 2. Important terminology

R008 is **not true option convexity** and must not be described as such.

It is a spot/perpetual-price proxy for an antifragile architecture:

- limited ordinary directional exposure;
- large dry-powder reserve;
- pre-committed crisis deployment;
- exposure increases stepwise as drawdown severity increases;
- no leverage and no shorting.

A historical PASS would justify deeper antifragility research, not a claim that the portfolio is mathematically convex.

---

## 3. Economic hypothesis

### H-R008 — Crisis-created opportunity

BTC has historically combined long-horizon growth with recurrent severe drawdowns. Investors who maintain full exposure suffer large path-dependent losses, while investors who remain entirely in cash sacrifice long-run upside.

A cash-heavy barbell may improve geometric outcomes if it:

1. keeps a small permanent BTC growth sleeve;
2. holds most capital unexposed during ordinary conditions;
3. preserves a separately budgeted dry-powder sleeve;
4. deploys that reserve only after objectively large drawdowns;
5. deploys more capital as the drawdown becomes more severe;
6. resets the reserve only after a new closing all-time high.

### Who pays / why could this persist?

The proposed opportunity is behavioural and path-dependent rather than an arbitrage:

- forced deleveraging and panic selling can create deep dislocations;
- many market participants cannot or will not preserve cash through bull markets;
- many investors become less willing to buy as drawdowns deepen;
- a pre-committed rule may exploit this behavioural asymmetry without forecasting the exact bottom.

### Falsification

The hypothesis is weakened or rejected if:

- crisis deployment does not improve geometric return versus a simpler 10% BTC / 90% cash benchmark;
- the strategy only looks good because one historical crash/recovery dominates the result;
- additional drawdown exposure increases losses without sufficiently improving recovery economics;
- the candidate does not improve risk-adjusted results versus both 10% and 20% static BTC/cash benchmarks;
- post-2023 behavior contradicts the full-period result;
- moderate transaction costs erase the incremental benefit;
- deeper stress does not produce increasing or at least non-deteriorating incremental benefit.

---

## 4. Initial data and scope

### Primary dataset

Use the already validated Binance USD-M daily archive dataset:

`r002_binance_full_universe_daily.csv`

For R008-E001, use only the BTCUSDT daily series.

### Why BTC only initially

The initial question is payoff architecture, not universe selection. BTC is used because:

- it has the longest continuous history in the existing validated dataset;
- it was the original directional asset in R001;
- it avoids repeating the broad-universe selection problem discovered in R002;
- the strategy can be falsified with minimal degrees of freedom.

### Initial historical window

The available Binance archive window begins in 2020. This is sufficient only for a **Stage-3 sanity screen**.

R008 cannot receive a final historical PASS from 2020-2026 alone because the number of independent severe drawdown episodes is small.

If R008-E001 is promising, the next required data step is an independent longer BTC spot history, preferably extending substantially before 2020, before any OOS/forward promotion.

---

## 5. Frozen R008-E001 portfolio architecture

### 5.1 Capital sleeves

Total NAV = 100%.

At the beginning of a fresh non-crisis state:

- **Permanent growth sleeve:** 10% BTC exposure.
- **Opportunity reserve:** 10% cash reserved for crisis deployment.
- **Core cash reserve:** 80% cash.

Therefore:

- ordinary BTC target exposure = **10%**;
- maximum BTC target exposure after all crisis tranches = **20%**;
- cash target ranges from **90% down to 80%**;
- no leverage.

Cash return = 0% in the first signal-architecture test.

### 5.2 Drawdown definition

At daily close `t`:

`Peak_t = max(close_0 ... close_t)`

`Drawdown_t = close_t / Peak_t - 1`

Only information available by close `t` may be used.

### 5.3 Crisis deployment thresholds

The 10% opportunity reserve is split into four equal **2.5 percentage-point** BTC tranches.

A tranche becomes deployed when closing drawdown first reaches or exceeds the following severity within the current drawdown episode:

1. **-20%**;
2. **-35%**;
3. **-50%**;
4. **-65%**.

Thus target BTC exposure is:

| Current episode state | BTC target |
|---|---:|
| No threshold triggered | 10.0% |
| -20% tranche triggered | 12.5% |
| -35% tranche triggered | 15.0% |
| -50% tranche triggered | 17.5% |
| -65% tranche triggered | 20.0% |

If one daily close crosses more than one previously untriggered threshold, all newly crossed tranches are deployed together at the next allowed execution step.

### 5.4 One trigger per episode

Once a tranche has been triggered inside a drawdown episode, it remains deployed until the episode resets.

A partial recovery followed by another decline does **not** re-buy an already deployed tranche.

This prevents repeated averaging rules from becoming an unbounded parameterized system.

### 5.5 Episode reset

A drawdown episode resets when BTC closes at a new all-time closing high.

At that close:

- all crisis tranches are marked for liquidation;
- next target returns to the permanent 10% BTC sleeve;
- all four opportunity tranches become available for a future episode.

No intermediate profit-taking threshold is used in v0.1.

---

## 6. Timing and execution convention

For every portfolio variant:

- state is computed from fully closed day `t`;
- target exposure determined at close `t` applies to return `t+1`;
- no same-close execution;
- no future peak, future recovery, or future drawdown information is used.

Transaction cost is charged on absolute BTC target-weight change.

Primary baseline cost = **10 bps** per absolute portfolio weight change.

Cost stress grid:

- 5 bps;
- 10 bps;
- 25 bps;
- 50 bps.

No funding or cash yield is credited in E001. If the architecture survives, spot/perpetual implementation realism becomes a separate later experiment.

---

## 7. Mandatory benchmarks

R008-E001 must be evaluated against simpler alternatives.

### B0 — CASH

- 100% cash;
- return = 0.

### B1 — STATIC10

- constant target 10% BTC / 90% cash;
- target reset daily for accounting consistency;
- same transaction-cost convention on target-weight changes.

### B2 — STATIC20

- constant target 20% BTC / 80% cash;
- same cost convention.

### B3 — BTC100

- 100% BTC price return;
- contextual benchmark only, not a comparable risk budget.

The two causal benchmarks are STATIC10 and STATIC20.

R008 must justify the added state machine relative to these simpler portfolios.

---

## 8. Required metrics

For R008 and all benchmarks report:

- CAGR;
- ending multiple;
- annualized volatility;
- Max Drawdown;
- Calmar;
- worst calendar year;
- worst calendar quarter;
- worst month;
- worst rolling 12-month return;
- longest drawdown / recovery time;
- average BTC exposure;
- maximum BTC exposure;
- turnover;
- fee drag;
- full-period result;
- post-2023 result.

Also report per-calendar-year returns.

---

## 9. Crisis-event diagnostics

Headline CAGR is not sufficient.

Every mechanically detected drawdown episode must be logged with:

- prior peak date;
- first -20% breach date;
- first -35% breach date if reached;
- first -50% breach date if reached;
- first -65% breach date if reached;
- maximum drawdown and date;
- recovery/new-ATH date if observed;
- number of deployed tranches;
- episode duration;
- R008 return from first threshold breach to reset/end;
- STATIC10 return over the same event window;
- STATIC20 return over the same event window;
- incremental R008 benefit vs STATIC10;
- incremental R008 benefit vs STATIC20.

Open/unrecovered episodes at the dataset endpoint must be retained and explicitly labeled censored/open.

No named crisis may be manually selected or excluded.

---

## 10. Antifragility diagnostics

### 10.1 Opportunity Benefit

Primary incremental diagnostic:

`Benefit_episode = R008_episode_return - STATIC10_episode_return`

A useful crisis-opportunity architecture should generally create positive incremental benefit after meaningful stress without requiring exact bottom prediction.

### 10.2 Severity-response ordering

Episodes will be categorized by deepest threshold reached:

- Level 1: reaches -20% but not -35%;
- Level 2: reaches -35% but not -50%;
- Level 3: reaches -50% but not -65%;
- Level 4: reaches -65% or deeper.

Report incremental benefit by level.

The desirable pattern is that deeper episodes do not systematically produce worse incremental benefit and ideally produce larger recovery benefit.

Because the available 2020-2026 sample may contain very few independent Level 3/4 episodes, this is descriptive rather than a high-confidence statistical test.

### 10.3 Dry-powder utilization

Report:

- fraction of time at 10%, 12.5%, 15%, 17.5%, and 20% BTC exposure;
- average unused opportunity reserve;
- number of tranche activations;
- number of full resets.

A strategy that almost never deploys cannot claim meaningful antifragile behavior; a strategy that stays near maximum exposure most of the time has ceased to be a cash-heavy barbell.

---

## 11. Decision rule for E001

E001 is a **sanity-screen experiment**, not final validation.

### PROMISING / ADVANCE TO LONGER-DATA VALIDATION

Advance only if all of the following are broadly true:

- net full-period CAGR exceeds STATIC10;
- Max Drawdown remains materially below STATIC20;
- Calmar is better than both STATIC10 and STATIC20, or there is an otherwise clear Pareto improvement in growth vs drawdown;
- post-2023 behavior does not contradict the full-period result;
- 25-50 bps cost stress does not destroy the incremental benefit;
- crisis-event benefit is not explained by a single event;
- deeper shock levels show economically coherent benefit rather than accelerating damage;
- the strategy spends substantial time with dry powder available.

### REDESIGN

Use REDESIGN if the architecture shows partial crisis value but:

- improvement is weak or concentrated;
- recovery logic creates very long trapped exposure;
- static 10% or 20% allocations are economically comparable or better;
- the short 2020-2026 sample is too event-poor to judge despite a plausible result.

### FAIL

Fail the v0.1 architecture if:

- R008 does not beat STATIC10 on geometric growth;
- R008 drawdown approaches or exceeds STATIC20 without compensating return;
- crisis deployment worsens outcomes in deeper shocks;
- post-2023 is materially inconsistent with the full-period result;
- moderate costs erase the incremental edge;
- results depend almost entirely on one historical crash/recovery.

No parameter rescue is allowed after observing E001.

---

## 12. Anti-overfitting freeze for E001

Do not change after seeing E001 results:

- 10% permanent BTC sleeve;
- 10% opportunity reserve;
- four equal 2.5% tranches;
- thresholds -20/-35/-50/-65%;
- reset only at new closing ATH;
- cash return = 0;
- no leverage;
- no shorts;
- no SMA/Donchian/RSI/MACD/ADX filter;
- no volatility filter;
- no liquidity filter;
- no per-event discretionary override.

If this architecture fails, record the failure. Any materially different crisis deployment schedule is a new R008 version, not a hidden tweak.

---

## 13. Relationship to R001 and R002

### R001

R001 remains the true long-convexity/options branch. R008 does not replace it.

If R008 demonstrates that cash-heavy crisis deployment has useful path economics, a later experiment may compare:

- R008 without options;
- R008 plus separately budgeted long convexity;
- carry-financed convexity.

That requires better option/carry data and a new pre-specified protocol.

### R002

R002 broad-universe rescue work remains closed.

The existing frozen BTC SMA120 forward record continues independently as a research control.

Do not add SMA120 to R008-E001. A later `trend + dry powder` architecture may be tested only as a separately specified experiment after the pure crisis-opportunity mechanism is understood.

---

## 14. Immediate execution order

1. Freeze this protocol in GitHub before running results.
2. Implement one reproducible R008-E001 BTC daily engine.
3. Read BTCUSDT only from the validated archive dataset.
4. Validate timing and threshold state transitions with synthetic tests.
5. Run B0/B1/B2/B3 and R008 under the same daily return convention.
6. Run cost stress 5/10/25/50 bps.
7. Produce full-period, post-2023, yearly and crisis-event diagnostics.
8. Make a PROMISING / REDESIGN / FAIL decision.
9. Do not tune v0.1 after seeing the result.
10. If PROMISING, acquire longer independent BTC spot history before stronger validation claims.

---

## 15. Plain-language summary

R008 deliberately gives up most ordinary BTC upside in exchange for survival and dry powder.

It owns 10% BTC all the time, keeps another 10% in reserve, and deploys that reserve in four small steps only after BTC has fallen 20%, 35%, 50%, and 65% from its closing peak. The extra exposure stays invested until BTC makes a new closing all-time high, at which point the portfolio returns to 10% BTC and rebuilds the dry powder.

The first test asks a narrow question:

> Does pre-committing a small amount of cash to increasingly severe crises improve the geometric path enough to justify the added state machine compared with simply holding 10% or 20% BTC all the time?

If not, we stop. If yes, we earn the right to test the idea on a longer history and later combine it with true convexity/carry research.
