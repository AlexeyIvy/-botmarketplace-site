# R001 — Antifragile Convex Barbell: Experiment Plan v1.0

**Project:** BotMarketplace / botmarketplace.store  
**Research Candidate:** R001  
**Status:** Active research specification  
**Version:** 1.0  
**Primary goal:** falsify or validate a redesigned convex barbell portfolio using historical and out-of-sample evidence before any production implementation.

---

## 1. Scope and legacy starting point

The original 80/15/5 materials are treated as a historical prototype, not as validated evidence.

Legacy rules to preserve only as comparison points:

- 80% BTCUSDT long futures/perpetual described as a “safe/yield” sleeve;
- 15% BTC spot or BTC perpetual directional exposure;
- 5% long options;
- approximately 3-month options;
- put around 20% OTM;
- call around 10% OTM;
- monthly rebalance/roll;
- volatility-adjusted allocation that increases option weight when volatility is high.

Known issues requiring explicit correction:

- the 80% BTC long futures sleeve is directional BTC exposure, not capital preservation;
- a simple long perpetual is not a reliable positive-yield instrument;
- 5% option NAV allocation and 0.5–1% monthly premium burn are different quantities;
- fixed % OTM rules ignore IV regime;
- volatility logic confuses realized and implied volatility;
- the historical JSX model is not a real option model and cannot establish convex payoff;
- reported historical performance figures are inconsistent and therefore unverified.

No legacy performance claim is carried forward as an acceptance target.

---

## 2. Primary research question

> Can a portfolio combining low-directional-beta capital preservation/carry, controlled BTC directional exposure, and explicitly budgeted long convexity improve long-term geometric and downside-adjusted outcomes relative to simpler portfolios after realistic trading costs and out-of-sample testing?

The objective is not to prove 80/15/5.

The objective is to determine whether any robust version of the underlying barbell/convexity hypothesis deserves continued development.

---

## 3. Economic hypotheses

### H-A — Capital preservation / carry

A low-beta sleeve can preserve capital and, under some market conditions, earn positive net carry from cash, basis, or funding structures without materially inheriting BTC directional beta.

**Falsification:** after realistic costs and operational haircuts, carry is not reliably positive or requires unacceptable counterparty, funding, basis, liquidity, or margin risk.

### H-B — Directional BTC sleeve

A limited BTC exposure may contribute positive long-term growth without allowing BTC drawdowns to dominate total portfolio survival.

**Falsification:** controlled BTC exposure does not improve geometric growth sufficiently relative to cash/carry, or risk-adjusted variants such as trend/vol targeting dominate it robustly.

### H-C — Long convexity sleeve

Long OTM options may be worth their persistent negative carry when purchased under sufficiently attractive volatility conditions if their crisis payouts materially reduce severe drawdowns, improve recovery, and/or improve geometric wealth.

**Falsification:** option premium drag exceeds the value of crisis protection/upside convexity across realistic historical and OOS tests.

### H-D — Volatility-aware purchasing

Convexity may be more attractive when implied volatility is cheap relative to realized/tail risk than when panic IV is already elevated.

**Falsification:** IV/RV, IV percentile, skew, or term-structure filters do not improve net convexity economics robustly out of sample.

### H-E — Option ladder

Staggered option vintages may reduce timing and expiry-cliff risk compared with replacing the full option book at one monthly timestamp.

**Falsification:** laddering does not improve tail continuity or net risk-adjusted results after additional turnover/spread costs.

---

## 4. Sleeve definitions

### Sleeve A — Capital Preservation / Carry

Objective:

- low directional beta;
- high survival probability;
- positive carry where economically justified;
- explicit counterparty/stablecoin/venue risk.

Variants:

- **A0:** cash/stable reserve, no assumed yield;
- **A1:** conservative stable yield with explicit haircut;
- **A2:** dated-futures cash-and-carry: long spot + short futures, matched notional;
- **A3:** funding carry: long spot + short perpetual when expected net funding is sufficiently positive;
- **A4:** opportunistic cash/carry hybrid, defaulting to cash when spreads are unattractive.

A0 is the initial control. A2/A3/A4 are enhancements tested separately.

### Sleeve B — Directional Growth

Variants:

- **B0:** BTC spot buy-and-hold sleeve;
- **B1:** volatility-targeted BTC exposure;
- **B2:** trend-filtered BTC exposure using a slow, pre-specified trend rule.

B0 is the initial control.

### Sleeve C — Convexity / Tail Risk

Only long options in v1.0.

Variants:

- **C0:** no options;
- **C1:** long OTM puts only;
- **C2:** asymmetric put-heavy put+call;
- **C3:** 50/50 premium strangle;
- **C4:** laddered put+call book.

Short-volatility overlays are excluded from R001 v1.0 to preserve clean attribution of convexity.

---

## 5. Initial allocation candidates

Do not optimize a large allocation grid initially.

Use a small coarse set:

| Portfolio | Carry | Directional | Convexity capital reserve |
|---|---:|---:|---:|
| P0 | 90% | 10% | 0% |
| P1 | 90% | 8% | 2% |
| P2 | 85% | 12% | 3% |
| P3 | 80% | 17% | 3% |
| P4 | 80% | 15% | 5% |

P4 preserves the old 80/15/5 allocation only as a comparator.

The option sleeve percentage is not itself the option premium spend rule. Premium budget is defined separately.

---

## 6. Option rules — primary research parameter set

### 6.1 Premium budget

Primary control variable: **annual option premium budget as % of portfolio NAV**.

Coarse candidates:

- 1% NAV/year;
- 2% NAV/year;
- 3% NAV/year;
- 5% NAV/year.

Primary baseline for early experiments: **2% NAV/year**.

Premium budget must be measured using actual option purchase cost including spread/slippage/fees.

### 6.2 Put selection

Candidate absolute deltas:

- 10Δ;
- 15Δ;
- 20Δ.

Primary baseline: **15Δ put**.

### 6.3 Call selection

Candidate deltas:

- 10Δ;
- 15Δ;
- 20Δ.

Primary baseline: **15Δ call**.

### 6.4 DTE

Candidate target maturity buckets:

- ~45 DTE;
- ~60 DTE;
- ~90 DTE.

Primary baseline: choose the nearest sufficiently liquid expiry in approximately **75–105 DTE**.

### 6.5 Roll

Candidate roll rules:

- roll at 30 DTE;
- roll at 21 DTE;
- hold to expiry.

Primary baseline: **roll at or below 30 DTE** on the next scheduled decision timestamp.

### 6.6 Put/call premium split

Candidates:

- 100/0 put/call;
- 75/25 put/call;
- 50/50 put/call.

Primary baseline: **75% put premium / 25% call premium**.

Rationale: the BTC directional sleeve already owns positive delta, so calls must prove incremental right-tail value rather than being assumed useful.

---

## 7. Option contract selection algorithm

At each option purchase timestamp:

1. use only contracts that existed and were tradable at that timestamp;
2. filter to BTC options on the chosen venue;
3. select eligible expiry nearest the target DTE bucket;
4. reject contracts failing minimum liquidity requirements;
5. within that expiry, choose the strike whose historical delta is closest to target delta;
6. if Greeks are unavailable but enough raw data exists, Greeks may be recomputed using contemporaneous inputs, with the method/version recorded;
7. entry purchase price uses executable historical ask, not future mark or settlement price;
8. exits use executable historical bid;
9. apply venue fees and slippage assumptions;
10. record selected instrument, strike, expiry, delta, IV, bid, ask, spread, OI, volume, and timestamp.

If no eligible contract is available, the strategy must follow a pre-defined fallback rule rather than selecting a future-known or illiquid instrument.

Initial fallback: skip that purchase and record a missed-hedge event.

---

## 8. Ladder definitions

### Non-ladder control

Maintain one primary maturity bucket and replace the eligible option book according to the roll rule.

### Three-vintage ladder

Maintain approximately three equal premium vintages targeting different remaining maturities, for example:

- long vintage: ~90 DTE;
- middle vintage: ~60 DTE;
- short vintage: ~30–45 DTE.

At each monthly cycle, replace only the oldest/shortest vintage according to the frozen ladder rule.

Compare:

- annual premium burn;
- option P&L;
- crisis payout;
- average gamma/vega exposure;
- spread cost;
- turnover;
- worst entry-IV timing;
- continuity of protection.

Laddering is a hypothesis, not an assumed improvement.

---

## 9. Volatility regime model

Do not use the old rule “high realized volatility → buy much more options” as the primary model.

Initial state vector:

- RV20;
- RV60;
- ATM IV for comparable DTE;
- IV percentile based only on historical data available at time t;
- IV/RV;
- IV − RV;
- 25Δ put-call skew;
- near/far volatility term structure.

Potential later indicators:

- volatility of volatility;
- funding regime;
- spot/perp basis;
- realized downside semivariance.

### Initial regime hypothesis

**Cheap convexity:**

- IV percentile low/moderate;
- IV/RV not rich;
- skew not extreme.

Action: full scheduled premium budget.

**Neutral:**

Action: normal baseline budget.

**Expensive / panic:**

- extreme IV percentile and/or IV/RV;
- extreme skew.

Action: reduce *new* option purchases according to a pre-defined rule; do not automatically liquidate existing convexity.

Exact numeric thresholds must be selected only through train/validation and then frozen for OOS.

---

## 10. Rebalancing policies

Compare three policies.

### R-CAL — Calendar

Monthly portfolio rebalance at a fixed deterministic timestamp.

### R-BAND — Drift bands

Rebalance capital sleeves only when deviation from target exceeds a pre-defined band.

Initial coarse candidate bands:

- absolute drift >3 percentage points;
- relative drift >20% of target weight.

### R-HYB — Hybrid

Monthly review plus band-triggered capital rebalance.

Primary baseline: **R-HYB**.

Option rolls are governed primarily by DTE/premium rules, not by restoring option mark value to a fixed NAV percentage.

---

## 11. Carry sleeve experiments

Carry must be isolated from the convexity thesis.

### A0 Cash control

Assume no yield. Apply explicit stablecoin/custody stress separately.

### A2 Dated futures basis

Entry only if expected net annualized basis exceeds:

`fees + spread + slippage + financing + risk buffer`.

Matched spot/futures notional; net BTC delta kept near zero.

### A3 Funding carry

Spot long + perp short when the expected funding economics are positive after costs.

Must model:

- historical funding timestamps;
- funding sign changes;
- entry/exit costs;
- basis mismatch;
- margin/collateral rules;
- venue concentration.

No carry return may be assumed without historical support.

---

## 12. Data requirements

### BTC spot/perpetual

- OHLCV;
- index/mark where relevant;
- bid/ask if available;
- funding history;
- venue fees;
- timestamps.

### Dated futures

- historical contract universe;
- expiry;
- futures price;
- bid/ask;
- basis;
- volume/OI;
- settlement.

### BTC options

Minimum desired fields:

- timestamp;
- venue;
- instrument name;
- option type;
- strike;
- expiry;
- underlying/index price;
- mark;
- bid;
- ask;
- bid size;
- ask size;
- IV;
- delta;
- gamma;
- theta;
- vega;
- volume;
- open interest;
- settlement rule.

Raw historical chain snapshots are strongly preferred.

Historical instrument availability is mandatory: the backtest may only select contracts available at the decision timestamp.

---

## 13. Backtest accounting rules

Use a portfolio-level event-driven simulator for R001.

At every decision event:

1. strategy sees only information available at or before the event timestamp;
2. desired holdings are generated from frozen rules;
3. fills occur no earlier than the allowed execution timestamp;
4. each leg is executed at realistic executable prices;
5. option premium is debited explicitly;
6. option positions are marked consistently through time;
7. funding is applied at real funding events;
8. futures/options settle according to contract conventions;
9. fees/spreads/slippage are debited explicitly;
10. total NAV equals the sum of all cash and marked positions;
11. all failed/skipped orders remain in the audit log.

No synthetic linear “hedgeReturn” approximation is acceptable for validation experiments.

---

## 14. Bias controls

### Look-ahead

Store or derive both:

- event timestamp;
- data-available timestamp.

Signals and contract selection cannot use observations published after the decision point.

### Survivorship

Do not discard failed/ruined paths before computing performance statistics.

### Selection bias

Do not hand-select successful crises or strikes to define the strategy.

### Parameter overfit

Use coarse economically justified parameters, robustness neighbourhoods, and walk-forward/OOS evaluation.

### Unrealistic fills

Primary evaluation must use executable bid/ask assumptions rather than mid-only fills.

---

## 15. Benchmark set

Mandatory benchmarks:

1. cash/stable only;
2. BTC HODL;
3. 10/90 BTC/cash;
4. 20/80 BTC/cash;
5. periodic BTC/cash rebalancing;
6. volatility-targeted BTC;
7. trend-filtered BTC;
8. carry + directional without options;
9. same portfolio + put only;
10. same portfolio + put+call;
11. ladder vs non-ladder.

The most important causal benchmark is the **same portfolio without options**.

---

## 16. Core metrics

Minimum common metrics:

- total return;
- CAGR;
- geometric mean return;
- annualized volatility;
- max drawdown;
- drawdown duration;
- recovery time;
- Sharpe;
- Sortino;
- Calmar;
- VaR;
- CVaR / Expected Shortfall;
- worst day/week/month;
- skewness;
- kurtosis;
- Omega ratio;
- upside capture;
- downside capture;
- turnover;
- fee drag;
- funding drag/carry;
- option premium burn/year;
- tail option payout/premium;
- crisis alpha;
- probability of 20%, 30%, and 50% drawdowns where statistically meaningful.

All metrics must be computed for gross and net variants where useful, with net performance used for decisions.

---

## 17. Convexity / antifragility diagnostics

Do not collapse everything into one score initially.

### 17.1 Shock Benefit Curve

Define:

`Benefit_t = Return_with_convexity_t − Return_same_portfolio_without_convexity_t`

For standardized BTC shocks Z:

- B(2) = E[Benefit | |Z| ≥ 2]
- B(3) = E[Benefit | |Z| ≥ 3]
- B(4) = E[Benefit | |Z| ≥ 4]

A desirable convex pattern is increasing benefit with shock magnitude, subject to confidence intervals and sample-size limits.

Evaluate downside and upside tails separately.

### 17.2 Tail Convexity Slope

On tail observations, estimate a diagnostic relationship such as:

`Benefit = α + β1·|Shock| + β2·Shock² + ε`

Positive and stable β2 is supportive evidence of convex payoff.

This is diagnostic, not sufficient proof.

### 17.3 Premium Efficiency

Track:

`tail-event option P&L / cumulative option premium paid`

Report both gross and net of option execution costs.

### 17.4 Geometric Contribution

Compare geometric return of the same portfolio with and without options.

A convexity sleeve that reduces drawdowns but destroys too much geometric growth is a redesign candidate, not an automatic PASS.

---

## 18. Event and crisis studies

Use two layers.

### Mechanical event selection

Identify events using pre-defined rules such as:

- worst 1% daily BTC returns;
- worst 1% weekly BTC returns;
- best 1% daily/weekly returns;
- realized volatility >95th percentile;
- IV >95th percentile;
- funding >95th percentile;
- rapid drawdown acceleration.

### Named historical audit

After mechanical analysis, inspect well-known regimes including:

- COVID crash;
- 2021 leverage flushes;
- Terra/Luna collapse;
- Celsius / Three Arrows period;
- FTX collapse;
- strong upside squeezes;
- ETF-driven bull periods;
- prolonged low-volatility compression;
- high-funding speculative regimes.

Named periods are diagnostic and explanatory; they must not drive parameter selection after the fact.

---

## 19. Walk-forward protocol

Preferred initial structure, subject to options data history:

- Train: 24 months;
- Validation: 6 months;
- Test: 6 months;
- roll forward by 6 months;
- repeat.

If data coverage is too short, use the longest structure that preserves multiple unseen test windows and document the compromise.

Rules:

- only train/validation may influence parameter choice;
- the test window remains unseen until rules are frozen;
- thresholds such as IV percentiles must be computed using only prior data;
- final primary performance is the concatenated OOS test equity curve.

---

## 20. Parameter robustness protocol

For surviving designs, test neighbourhoods rather than a single optimum.

Examples:

- put delta: 10 / 15 / 20;
- call delta: 10 / 15 / 20;
- DTE: 45 / 60 / 90;
- premium budget: 1 / 2 / 3 / 5% NAV/year;
- roll: 21 / 30 DTE / expiry;
- allocation: P1–P4.

Do not run the full Cartesian product immediately.

Use staged one-factor / small-block experiments first, then limited interactions only for surviving concepts.

---

## 21. Stress-test matrix

| Dimension | Normal | Stress | Severe |
|---|---|---|---|
| option spread | historical | ×2 | ×4 |
| spot/perp slippage | baseline | ×2 | ×5 |
| option slippage | baseline | ×2 | ×5 |
| execution delay | normal | +5 min / next event | +1 h |
| funding | historical | adverse shift | sign reversal |
| stablecoin | par | -5% | -20% / failure scenario |
| venue outage | none | 6 h | 72 h |
| data gaps | none | random gaps | clustered gaps |
| hedge leg | normal | delayed | unavailable |
| liquidity | observed | volume haircut | no-fill periods |
| BTC gap | historical | ×1.5 shock | ×2 shock |
| IV/skew | observed | IV shock | IV + skew shock |

Also run combined crises, for example:

`BTC crash + IV spike + spread widening + exchange outage`.

---

## 22. Acceptance / redesign / rejection

These criteria must be defined before final OOS evaluation.

### PASS

R001 may pass only if the surviving variant demonstrates, on concatenated OOS results and realistic costs:

- economically meaningful geometric and/or downside-adjusted improvement versus simpler comparable portfolios;
- material reduction in severe drawdown and/or Expected Shortfall;
- convexity benefit that strengthens with shock magnitude at least in the downside tail, within statistical uncertainty;
- robustness to nearby parameter values;
- persistence across multiple walk-forward windows;
- survival under stressed execution assumptions;
- controlled annual premium burn within the pre-defined budget;
- no dependence on one single venue/stablecoin assumption for profitability.

### REDESIGN

Use REDESIGN when the core idea has value but one component does not, for example:

- puts materially improve survival but calls destroy value;
- convexity works but premium budget is too high;
- laddering is better but static roll is poor;
- carry works while long convexity does not;
- static options work but volatility-aware sizing is harmful.

A redesign creates a new strategy/specification version.

### REJECT

Reject R001 v1.x if, after realistic costs and OOS testing:

- it is dominated by a much simpler BTC/cash or carry/directional portfolio on both geometric return and tail risk;
- convexity benefit does not increase with shock size;
- premium drag overwhelms crisis value;
- results depend on one historical crisis or one narrow parameter point;
- execution stress eliminates the edge;
- required data quality is insufficient to support reliable conclusions.

Rejection is a valid research outcome.

---

## 23. First experiment sequence

The order is intentionally incremental to preserve causal attribution.

### R001-E001 — Legacy reconstruction / invalidation

**Purpose:** reproduce the conceptual old 80/15/5 exposure and demonstrate precisely why the original “safe 80% BTC futures” interpretation is invalid.

**No real-option validation claim.**

Outputs:

- effective BTC delta;
- portfolio response to ±10/20/50% BTC moves;
- funding sensitivity;
- reconciliation against legacy claims.

Decision: documentation/sanity experiment only.

### R001-E002 — Clean baseline: cash + BTC

Test P0/P1-like simple capital-preservation + directional portfolios with no options and no carry alpha.

Purpose: establish the benchmark portfolio economics before adding complexity.

### R001-E003 — Put-only static convexity

Add long puts to the clean baseline.

Primary baseline:

- 15Δ put;
- ~90 DTE;
- roll at 30 DTE;
- 2% annual premium budget.

Question:

> Does downside convexity justify its premium burn?

### R001-E004 — Put premium-budget sensitivity

Compare 1%, 2%, 3%, 5% annual premium budgets using the same option-selection rule.

Goal: determine whether a broad useful budget region exists.

### R001-E005 — Put delta / DTE robustness

Coarse robustness around surviving put budget(s):

- 10/15/20Δ;
- 45/60/90 DTE;
- limited combinations only.

Goal: reject magical single-point behaviour.

### R001-E006 — Incremental calls

Compare the surviving put-only design with:

- 75/25 put/call premium split;
- 50/50 split.

Question:

> Do calls add enough right-tail value to justify additional premium drag beyond the BTC directional sleeve?

### R001-E007 — Ladder vs non-ladder

Compare the best frozen non-ladder variant with a three-vintage ladder using the same annual premium budget.

Question:

> Does laddering materially improve protection continuity / timing robustness net of extra costs?

### R001-E008 — Volatility-aware purchasing

Introduce only after static convexity variants are understood.

Test whether IV percentile, IV/RV, skew, and term structure improve new-option purchase timing.

No large threshold optimization. Use coarse train/validation thresholds.

### R001-E009 — Carry sleeve integration

Replace A0 cash with validated carry variants one at a time:

- basis carry;
- funding carry;
- opportunistic cash/carry.

Question:

> Does positive carry offset premium burn without introducing unacceptable new tail/counterparty risk?

### R001-E010 — Full walk-forward + stress gauntlet

Take only the minimal surviving architecture from E002–E009.

Run:

- walk-forward;
- stitched OOS;
- parameter neighbourhood;
- historical crises;
- combined stress tests;
- realistic execution sensitivity.

Outcome:

- PASS;
- REDESIGN;
- REJECT.

No production implementation before E010 decision.

---

## 24. Research sequencing rule

Do not move automatically through all ten experiments.

At each experiment:

- if the added component fails, remove or redesign it;
- if the core economics fail, stop R001 early;
- if data quality is insufficient, mark the research blocked rather than fabricating assumptions.

The experiment list is a gauntlet, not a checklist that guarantees completion.

---

## 25. R002 control track relationship

R001 remains the first primary strategy candidate.

R002 BTC Trend Following may be implemented earlier in the lightweight research harness as a control to validate:

- historical data loading;
- next-bar execution;
- fees/slippage;
- equity accounting;
- train/validation/test workflow;
- walk-forward stitching;
- metrics;
- experiment registry.

R002 does not replace R001. It reduces the risk of confusing simulator bugs with R001 strategy failure.

---

## 26. Immediate next decision gates

Before writing a R001 backtest implementation, complete:

1. historical BTC options data-source audit;
2. exact minimum data schema;
3. venue/coverage comparison;
4. data quality and licensing/cost assessment;
5. determination of the earliest trustworthy historical test period;
6. design of a minimal independent research harness;
7. R002 control-harness specification if needed.

The next highest-value task is therefore **Data Source & Research Harness Design**, not production strategy code.

---

## 27. Research principle

> The burden of proof is on the strategy.

We will try to disprove the hypothesis under realistic conditions. Only components that survive ablation, costs, OOS, robustness, and stress remain in the strategy.
