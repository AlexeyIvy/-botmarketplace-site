# R001-E003 — Put-Only Protocol v0.1

**Candidate:** R001 Antifragile Convex Barbell  
**Experiment:** E003 — incremental value of long downside convexity  
**Status:** Protocol frozen for first implementation pass  

## 1. Question

Does adding a systematically budgeted long BTC put sleeve improve downside-adjusted and/or geometric portfolio outcomes relative to the exact same cash/BTC portfolio without options after executable option pricing and costs?

This experiment tests puts only. Calls, ladders, carry enhancement and volatility-regime sizing are excluded.

## 2. Baseline portfolio

Primary baseline for the first pass:

- 90% cash / stable reserve, assumed 0% yield;
- 10% BTC directional exposure;
- monthly portfolio decision cycle;
- no leverage;
- no assumed funding or yield.

Comparator B0 is the exact same portfolio without puts.

## 3. Put rule

Primary frozen rule for the first pass:

- venue: Deribit BTC inverse options;
- side: long put only;
- target absolute delta: 0.15;
- eligible DTE: initially 60–120 days because real listed expiries are discrete;
- expiry selection: choose the eligible expiry nearest target 90 DTE, then choose strike nearest 15Δ within that expiry;
- if no eligible executable contract exists: skip purchase and log a missed-hedge event;
- entry: historical ask;
- pre-expiry close/roll: historical bid;
- no mid-price fills in the decision result.

The first real-data sample demonstrated that exact 90-DTE expiries cannot be assumed. On 2020-03-01 the relevant available longer expiry was approximately 117 DTE.

## 4. Premium budget

Primary annual option premium budget:

- 2% of portfolio NAV per year;
- divided equally across 12 scheduled monthly purchase cycles for the first pass;
- monthly budget = NAV × 0.02 / 12;
- actual quantity is rounded down to the venue lot increment;
- unspent budget is not force-spent on a worse option.

This definition replaces the legacy ambiguity between “5% NAV in options” and “0.5–1% NAV premium burn per month.”

## 5. Deribit inverse option accounting

For BTC inverse options quoted in BTC:

- one BTC option contract represents 1 BTC of underlying exposure;
- premium quote is BTC per contract;
- USD premium at trade time = option_price_BTC × BTC_index_USD × contracts;
- a long option purchase debits the premium immediately;
- pre-expiry executable liquidation value uses historical bid × contemporaneous BTC index × contracts;
- expiry intrinsic USD for a put = max(strike − settlement_price, 0) × contracts;
- corresponding BTC settlement is intrinsic_USD / settlement_price.

Current Deribit documentation confirms inverse BTC options are European, cash-settled, quoted/margined in BTC. Historical contract-detail consistency for the tested dates must still be recorded in the dataset audit rather than silently assumed.

## 6. Initial implementation

Research-only modules:

- `research/r001/option_selector.py`
- `research/r001/tardis_options_adapter.py`
- `research/r001/put_only_simulator.py`
- associated tests.

The simulator is intentionally independent of BotMarketplace production code.

## 7. Required datasets for a real E003 backtest

A single-day options sample is sufficient for selection/accounting validation but not for a performance backtest.

Minimum serious dataset must contain repeated historical option-chain observations spanning multiple market regimes, with at least:

- timestamp;
- actual listed instruments;
- strike;
- expiry;
- bid/ask and sizes;
- underlying/index price;
- delta;
- preferably IV, OI and volume.

BTC spot/index history is required at the same decision/valuation timestamps.

For accurate drawdown, CVaR and crisis-path analysis, daily or finer option valuations are preferred. Monthly-only snapshots may be used only as an explicitly labelled coarse feasibility test, not as final evidence.

## 8. First-pass outputs

For baseline and put-overlay variants report:

- ending NAV;
- total return;
- geometric return / CAGR where period supports it;
- max drawdown;
- drawdown duration;
- Expected Shortfall / CVaR where sampling supports it;
- worst day/week/month where sampling supports it;
- total option premium paid;
- total option sale/expiry proceeds;
- net option P&L;
- premium burn / NAV;
- tail-period benefit versus same portfolio without puts;
- missed-hedge events;
- spread/execution drag.

Do not report probability-of-ruin claims from insufficient samples.

## 9. Decision rule for E003

### Continue / PASS to robustness stage

Puts show material downside benefit and the value is not obviously destroyed by premium/spread drag. The result must justify testing neighbouring deltas, DTEs and premium budgets.

### REDESIGN

Protection is economically visible but premium drag is too high, liquidity rules are too restrictive, or value appears concentrated in an overly narrow contract rule.

### STOP put hypothesis

After realistic executable pricing across a sufficiently broad dataset, the put overlay worsens geometric outcomes without material improvement in severe downside risk, or its apparent benefit is dependent on isolated hand-picked crises/parameters.

## 10. Next data gate

Before E003 performance claims, acquire a multi-date historical options dataset. The next research milestone is therefore:

> **multi-date data coverage → repeated selector validation → E003 historical simulation → ablation versus no-option baseline**

No production BotMarketplace capability is required before this gate is passed.
