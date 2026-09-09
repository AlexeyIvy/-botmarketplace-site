# R002 Near-Term Research Roadmap v1.0

**Project:** BotMarketplace strategy research  
**Primary candidate:** R002 BTC / Cross-Asset Trend Following  
**Current frozen baseline:** SMA120, long/cash, daily bars, next-day execution assumption  
**Research status:** historical robustness PASS; cross-asset PARTIAL PASS; survivorship-bias stress PASS WITH CAVEATS; forward validation in progress  
**Purpose of this document:** fix the next research steps, test order, decision rules, and anti-overfitting constraints so the plan does not drift with each new result.

---

## 1. Current evidence summary

### 1.1 R001 options / convexity track

R001 demonstrated that long puts can provide crisis convexity, but static protection was too expensive. IV-only and IV/RV timing improved economics but did not validate robustly on the later period. R001 is therefore not abandoned, but is **paused in REDESIGN**. No additional calls, ladders, or complex option timing rules should be added until denser crisis-window data or a new economically distinct hypothesis is available.

### 1.2 R002 SMA120 track

The simple rule `close > SMA120 -> long, else cash` has survived several distinct checks:

- strong BTC historical result versus buy-and-hold;
- broad SMA plateau around roughly 110-130 days;
- transaction-cost stress;
- next-day execution sensitivity;
- cross-asset testing on BTC, ETH, SOL, XRP, LTC, ADA, BNB;
- historical / delisted-asset survivorship-bias stress;
- most historical non-survivors showed materially better downside behavior under SMA120 than buy-and-hold.

The frozen SMA120 version must **not** be modified. Any additional filter or sizing rule is a new research branch.

### 1.3 R002.1 SMA120 + ADX20

ADX20 is promising as a portfolio-level risk filter. It reduced drawdown substantially in several tests, but did not dominate SMA120 on every asset and sometimes reduced CAGR materially. It remains a candidate branch, not a replacement for the baseline.

---

## 2. Research principles for the next phase

1. **Preserve a frozen control.** SMA120 v1.0 remains unchanged throughout all further experiments.
2. **One new idea at a time.** Do not stack RSI, MACD, ADX, volatility filters, momentum, and other rules in one model.
3. **Prefer orthogonal information.** A new component should answer a different economic question from the existing trend signal.
4. **Use pre-specified coarse grids only.** No fine parameter search after viewing results.
5. **Judge robustness, not peak CAGR.** A broad stable region is preferred over one best point.
6. **Separate signal from sizing.** Trend decides whether risk is allowed; volatility decides how much risk to take.
7. **Keep late-period and non-survivor diagnostics visible.** No result may be called robust if it only works on the full sample.
8. **Execution realism comes after signal robustness, not before.** Minute data and order-book modeling are unnecessary until the daily rule survives portfolio-level testing.
9. **Forward clock must not be reset by research branches.** Frozen SMA120 forward validation continues independently.
10. **Every new branch gets its own name/version and explicit reject/pass decision.**

---

## 3. Ordered next-step plan

### STEP A — Build a true point-in-time historical portfolio

**Priority:** highest.  
**Goal:** answer whether a portfolio built only from assets actually available at each historical date would have behaved well without knowledge of future survivors or delistings.

#### A1. Universe rules

For each asset:

- it becomes eligible only after actual historical data begin;
- it cannot generate an SMA120 signal before 120 closed daily observations exist;
- it remains eligible only while real trading data are present;
- no future delisting information may be used in advance;
- after the final real trading day, the asset leaves the tradable universe;
- zero-volume frozen post-delisting archive tails must be removed.

#### A2. Baseline portfolio variants

Test only the following pre-specified variants:

1. **PTI Buy & Hold Equal Weight** — equal weight among all eligible assets.
2. **PTI SMA120 Equal Weight** — equal target weight among eligible assets whose signal is long; unused weight stays in cash.
3. **PTI SMA120 Equal Risk Bucket** — optional diagnostic only if equal-weight results are interpretable; no leverage.

Primary comparison is #2 versus #1.

#### A3. Rebalancing convention

Primary: daily signal update, portfolio weights recalculated daily using information available at the prior close.  
Secondary diagnostic: weekly rebalance to estimate implementation-cost sensitivity.

#### A4. Costs

Coarse stress grid only:

- 10 bps per exposure change — base research assumption;
- 25 bps;
- 50 bps.

No cost calibration to improve results.

#### A5. Required metrics

- CAGR;
- Max Drawdown;
- annualized volatility;
- worst calendar year;
- worst rolling 12-month return;
- turnover;
- number of active assets through time;
- fraction of portfolio in cash through time;
- late-period metrics;
- survivor vs non-survivor contribution;
- drawdown recovery time.

#### A6. Decision rule

**PASS signal:** SMA120 point-in-time portfolio improves downside materially and does not require implausibly high turnover or a narrow subperiod to justify itself.  
**FAIL signal:** advantage disappears once the universe is made point-in-time or after moderate cost stress.

---

### STEP B — R002.2 Volatility Targeting / Risk Scaling

**Priority:** second, run after or in parallel with Step A.  
**Economic question:** not "will price rise?" but "how much risk should we take when the trend is on?"

#### B1. Frozen entry logic

Signal remains exactly:

`long_allowed = close > SMA120`

No change to SMA length.

#### B2. Realized volatility estimator

Primary estimator: 20-day realized volatility from daily close-to-close returns.  
Secondary diagnostic: 60-day realized volatility.

No optimization of estimator windows beyond these two pre-specified values.

#### B3. Target-vol grid

Test only:

- 15% annualized target vol;
- 20%;
- 25%;
- 30%.

Position fraction:

`position = min(1.0, target_vol / estimated_vol)` when SMA120 is long, else `0`.

Hard rule: **no leverage above 1.0x**.

#### B4. Why this branch is preferred over RSI/MACD

SMA, MACD, momentum, and RSI all derive mostly from price direction / speed. Volatility targeting adds a different dimension: position size based on current risk. This is more orthogonal and therefore less likely to add complexity without new information.

#### B5. Evaluation

Compare each target-vol variant against frozen SMA120 on:

- CAGR;
- Max DD;
- annualized vol;
- worst year;
- worst rolling 12 months;
- turnover;
- cost stress;
- survivor and non-survivor subsets;
- late period;
- point-in-time portfolio.

#### B6. Decision rule

Do **not** select the target with highest CAGR.  
Advance only if a broad range, ideally at least 2-3 neighboring targets, improves risk-adjusted behavior consistently.

---

### STEP C — Re-evaluate R002.1 ADX20 under the point-in-time portfolio

**Priority:** third.  
**Purpose:** determine whether ADX20 still helps after survivorship bias is reduced.

Rules:

- frozen SMA120;
- ADX14;
- primary threshold fixed at 20;
- thresholds 15 and 25 retained only as coarse robustness neighbors;
- no asset-specific ADX thresholds.

Decision:

- if ADX20 improves point-in-time portfolio drawdown without excessive CAGR loss and neighboring thresholds behave coherently -> keep R002.1 alive;
- otherwise reject ADX branch and retain plain SMA120 / volatility-scaling branches.

---

### STEP D — Independent trend formulation test

**Priority:** fourth, only after A-C.  
**Purpose:** test the economic principle of trend following rather than the specific SMA120 formula.

Use one simple pre-specified breakout family, for example:

- long when price breaks above a 100-day high;
- exit when price falls below a 50-day low.

This is a separate candidate, not a filter on SMA120.

Why useful: if a structurally different trend rule works on similar universes, confidence shifts from "SMA120 worked" toward "crypto trend persistence may be exploitable."

No multi-parameter Donchian optimization should be done at this stage.

---

### STEP E — Freeze comparison set

After A-D, compare only the surviving simple candidates:

1. **R002 v1.0:** SMA120;
2. **R002.1:** SMA120 + ADX20, if still alive;
3. **R002.2:** SMA120 + volatility targeting, if validated;
4. **R003 candidate:** simple breakout trend, if validated.

Score them using a fixed decision table:

| Dimension | What matters |
|---|---|
| Return | CAGR and rolling returns |
| Downside | Max DD, worst year, recovery time |
| Robustness | survivors, non-survivors, late period, cost stress |
| Simplicity | number of parameters and rules |
| Turnover | implementation burden |
| Portability | BTC-only vs cross-asset |
| Forward readiness | easy to reproduce from closed daily data |

The simplest strategy that survives the largest number of independent tests should be preferred over the highest-CAGR strategy.

---

## 4. Tests we deliberately postpone

Do **not** add these yet:

- RSI filter;
- MACD filter;
- third/fourth technical indicator stacks;
- machine learning;
- neural networks;
- parameter optimizers;
- intraday signals;
- order-book features;
- social sentiment;
- on-chain features;
- leverage;
- shorting;
- options overlay on top of R002;
- dynamic asset-specific parameter tuning.

Reason: these increase model degrees of freedom before we have finished validating the simpler economic mechanisms already showing promise.

---

## 5. Additional data: when it becomes justified

Current daily OHLCV data are sufficient for Steps A-D.

Only after a candidate survives those steps should we add execution-specific datasets.

### 5.1 Perpetual-futures production research

Needed later:

- funding history;
- actual maker/taker fees;
- contract specifications;
- minimum order sizes;
- slippage estimates;
- exchange outages / data gaps.

### 5.2 Spot production research

Needed later:

- independent spot history cross-check;
- real spot fees;
- stablecoin / cash assumptions;
- delisting mechanics.

### 5.3 Intraday data

Only justified if daily execution ambiguity materially affects results. It is **not** needed to decide whether the daily trend hypothesis is valid.

---

## 6. Forward validation that continues in parallel

The frozen BTC SMA120 forward clock continues independently of all research branches.

Forward record should track:

- prior closed daily close;
- SMA120;
- next-day signal;
- theoretical exposure;
- paper execution;
- fees/slippage;
- strategy equity;
- BTC buy-and-hold benchmark;
- deviations / anomalies.

Research changes to R002.1 or R002.2 must not alter or restart R002 v1.0 forward history.

---

## 7. Stop / advance criteria

### Advance a branch when

- the effect appears across multiple assets / regimes;
- neighboring coarse parameters behave similarly;
- late-period results remain economically sensible;
- non-survivors do not destroy the result;
- moderate cost stress does not erase the advantage;
- point-in-time construction does not reverse the conclusion;
- complexity added is justified by measurable improvement.

### Reject or pause a branch when

- only one parameter value works;
- improvement is driven by one or two assets;
- late-period performance collapses;
- cost stress removes the benefit;
- point-in-time portfolio invalidates the edge;
- complexity rises but downside/return profile does not improve materially.

---

## 8. Immediate execution order

1. **Implement point-in-time historical portfolio engine** on the cleaned survivor + non-survivor dataset.
2. **Run frozen SMA120 point-in-time baseline** with 10/25/50 bps cost stress.
3. **Add R002.2 volatility targeting** with RV20/RV60 and 15/20/25/30% targets, no leverage.
4. **Re-run R002.1 ADX20** on the same point-in-time engine.
5. **Compare SMA120 vs ADX20 vs volatility-targeting** using the fixed metrics and decision rules above.
6. **Only then** test one independent breakout trend formulation.
7. Freeze whichever candidate(s) survive and move them toward longer forward / paper execution.
8. After signal validation, perform BotMarketplace execution-gap analysis and production integration work.

---

## 9. Current default decision hierarchy

Unless new evidence changes the order:

**Primary control:** R002 SMA120  
**Most promising next enhancement:** R002.2 volatility targeting  
**Secondary enhancement under review:** R002.1 ADX20  
**Independent future control:** breakout / Donchian trend  
**Paused research:** R001 options convexity  
**Avoid for now:** indicator stacking and parameter optimization

---

## 10. Interpretation in plain language

We have enough evidence to believe that simple trend following in crypto deserves serious continued validation. The next goal is no longer to make the historical chart prettier. The next goal is to see whether the same simple logic survives a realistic historical universe, position-sizing rules, costs, and future unseen data.

The research plan therefore prioritizes **portfolio realism and risk sizing** over adding more prediction indicators.