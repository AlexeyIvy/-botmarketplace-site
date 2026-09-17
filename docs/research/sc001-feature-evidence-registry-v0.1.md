# SC001 — Feature Evidence Registry v0.1

Date: 2026-09-17  
Status: **APPEND-ONLY BOOTSTRAP REGISTRY**

Governance:
- `sc001-feature-indicator-research-governance-v0.1.md`
- `sc001-feature-indicator-taxonomy-v0.1.md`
- `sc001-incremental-feature-testing-protocol-v0.1.md`

## 1. Registry rule

This is not a leaderboard and contains no global `works/does-not-work` verdict.

Each record is scoped by feature/version, role, market, horizon, strategy, evidence stage and limitations.

Existing records are never deleted because later evidence disagrees.

## 2. Bootstrap records from completed SC001 work

### F001 — Taker Flow Imbalance / signed aggressive-flow imbalance

- primitive family: P5 aggressive order flow;
- historical strategy relationship: E002;
- roles observed: R1 core predictive signal; possible future R2/R3/R5 roles not yet established;
- historical horizon: very short / approximately 5-second signal and label in core E002 research;
- evidence summary: positive short-horizon predictive association was repeatedly observed in prior Binance/OKX research, including quote-based robustness work;
- economic summary: standalone taker implementation failed its economics gate;
- scoped classification: `PREDICTIVE_SUPPORT_BUT_STANDALONE_ECONOMICS_FAILED`;
- reusable conclusion: signed aggressive flow contains historically observed short-horizon information in the tested contexts, but this does not prove profitable standalone taker trading;
- forbidden conclusion: `TFI works as a profitable strategy`;
- future use: auxiliary ranking/veto/timing only under new pre-registered experiment and fresh evidence, consistent with legacy policy.

### F002 — Volatility compression / expansion state

- primitive family: P3 volatility/range;
- historical strategy relationship: E004/E005;
- role observed: R2 state/regime plus strategy trigger context;
- evidence summary: the frozen E004 compression-breakout strategy failed Discovery economics; E005 remained closed by prerequisite;
- scoped classification: `STRATEGY_FAILED_FEATURE_NOT_ISOLATED`;
- reusable conclusion: the tested compression-breakout implementation did not establish viable economics;
- forbidden conclusion: `volatility compression is useless`;
- future use: a genuinely new multi-minute volatility-state hypothesis may use a separately defined feature under new ID/fresh evidence.

### F003 — Spot/perpetual basis dislocation

- primitive family: P8 relative value / derivative state;
- historical strategy relationship: E006;
- role observed: R1 core relative-value signal plus R6 baseline/deviation construction;
- evidence summary: original BTC same-venue study was limited by event scarcity and insufficient economic headroom under its frozen rules;
- scoped classification: `STRATEGY_FAILED_FEATURE_NOT_ISOLATED`;
- reusable conclusion: BTC-only evidence did not establish a viable paired strategy and did not resolve whether scarcity/headroom is instrument-specific across a wider universe;
- future use: strict multi-asset E006R1 candidate is scientifically justified under new ID, cheap event/cost sentinel first.

### F004 — 60-second displacement / price overshoot

- primitive family: P1 price/return location;
- historical strategy relationship: E007 and E007R1;
- role observed: R1 reversal signal;
- evidence summary: an event-level reversal effect existed in part of the evidence, but strict multi-asset E007R1 failed frozen cross-market headroom, breadth and latency robustness gates;
- scoped classification: `STRATEGY_FAILED_WITH_PARTIAL_EVENT_EFFECT`;
- reusable conclusion: a short-displacement reversal effect can exist locally, but the frozen family did not establish portable multi-asset economics;
- forbidden conclusion: selecting E007R1 winners for a new strategy;
- future use: no direct retest; genuinely different multi-minute state/deviation family allowed only under new ID.

### F005 — VWAP / local volume-weighted reference

- primitive family: P7 reference price with P4 volume weighting;
- historical strategy relationship: used as causal price/reference component in several SC001 constructions including E006/E007/E009-style work;
- role observed: R6 reference/normalization;
- evidence summary: prior strategy failures do not isolate VWAP as a feature claim;
- scoped classification: `DEFINED_AND_USED / FEATURE_NOT_ISOLATED`;
- reusable conclusion: VWAP is an implementable causal reference when window/timestamp semantics are explicit;
- forbidden conclusion: strategy failure implies VWAP is ineffective;
- future use: multi-minute deviation candidate may test a new VWAP-reference role under fresh evidence.

### F006 — Visible spread / top-of-book liquidity state

- primitive family: P6 order-book/liquidity;
- historical strategy relationship: E008 and taker-execution research;
- roles observed: R2 state, R5 execution, economic feasibility primitive;
- evidence summary: frozen BTC E008 showed quoted-spread/gross economics were generally inadequate relative to regular-user fee burden; queue-model limitations coexisted but did not rescue BTC spread economics;
- scoped classification: `BTC_MAKER_ECONOMICS_UNFAVORABLE_IN_TESTED_CONTEXT`;
- reusable conclusion: spread/fee feasibility should be screened before queue-heavy maker research;
- forbidden conclusion: all maker strategies or wider-spread assets are invalid;
- future use: new maker family only on prospectively spread/fee-eligible markets with new ID.

### F007 — Robust MAD volatility normalization of displacement

- primitive family: P3 volatility/range + P1 price displacement;
- historical strategy relationship: E009;
- roles observed: R6 normalization and core signal construction;
- evidence summary: prospectively frozen E009 v0.1 failed its fresh September multi-asset gross-feasibility gates despite adequate sample/activity;
- scoped classification: `STRATEGY_FAILED_FEATURE_NOT_ISOLATED`;
- reusable conclusion: the specific MAD-normalized 60-second reversal formulation did not establish portable economics;
- forbidden conclusion: robust MAD scaling or volatility normalization is globally useless;
- future use: any reuse must solve a separately stated measurement problem under new evidence.

### F008 — Queue-ahead / passive-fill state model

- primitive family: P6 order-book/liquidity / execution state;
- historical strategy relationship: E008;
- role observed: R5 execution feature, not alpha;
- evidence summary: conservative frozen model was useful as a pessimistic scenario but too adversarial to serve as a central exact-FIFO estimator with aggregated historical L2;
- scoped classification: `EXECUTION_MODEL_SENSITIVE`;
- reusable conclusion: aggregated L2 queue position is an uncertainty/scenario problem; own-order overlay and multiple physically coherent scenarios are required for future maker work;
- forbidden conclusion: queue model failure implies maker alpha failure by itself.

## 3. Empty registry families to populate prospectively

No positive/negative claim is currently made here for generic classical indicators such as:

- RSI;
- MACD;
- ADX;
- ATR as a standalone trading feature;
- Stochastic;
- Bollinger Bands as a standalone rule;
- OBV and similar transforms.

If used later, each receives an exact feature/version definition and evidence record. Popularity is not evidence.

## 4. Append template

For each new record append:

- feature ID/version:
- primitive family:
- formula/version reference:
- role:
- experiment ID:
- market/universe:
- signal horizon:
- position horizon:
- evidence chronology/role:
- baseline comparator:
- sample/block breadth:
- predictive effect:
- gross effect:
- incremental net effect:
- turnover/opportunity effect:
- risk/tail effect:
- cost/latency robustness:
- contamination status:
- classification:
- limitations:
- allowed reusable conclusion:
- forbidden overclaim:
