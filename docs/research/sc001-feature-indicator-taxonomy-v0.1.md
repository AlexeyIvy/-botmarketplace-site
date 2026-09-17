# SC001 — Feature / Indicator Taxonomy v0.1

Date: 2026-09-17  
Status: **BINDING TAXONOMY FOR FUTURE FEATURE RECORDS**

This taxonomy groups features by underlying economic information rather than by popular indicator names.

## 1. P1 — Price / return location

Measures price level, return, relative location or deviation.

Examples:
- raw/log return;
- distance from moving average;
- rolling z-score;
- RSI/Stochastic-style recent-price-position transforms;
- Bollinger-style deviation components.

Typical roles: core signal, state, normalization.

## 2. P2 — Trend / persistence

Measures directional persistence or trend strength.

Examples:
- SMA/EMA slopes;
- moving-average spread;
- MACD-style transforms;
- ADX/trend-strength measures;
- breakout/range expansion state.

Typical roles: signal, regime, filter.

## 3. P3 — Volatility / range

Measures realized movement scale or compression/expansion.

Examples:
- realized volatility;
- ATR/true range;
- rolling MAD scale;
- high-low range;
- volatility compression/expansion ratios.

Typical roles: state, normalization, sizing, stop/hold scaling.

## 4. P4 — Volume / turnover / activity

Measures trading activity or participation intensity.

Examples:
- traded volume/quote turnover;
- relative volume;
- trade count;
- volume acceleration;
- volume-at-price summaries.

Typical roles: state, filter, event definition.

## 5. P5 — Aggressive order flow

Measures signed liquidity-taking pressure.

Examples:
- taker flow imbalance / TFI;
- signed notional imbalance;
- buy/sell trade count imbalance;
- sweep intensity;
- large-aggressive-trade features.

Typical roles: signal, event, filter, execution timing.

## 6. P6 — Order-book / liquidity state

Measures visible liquidity and short-horizon book pressure.

Examples:
- spread;
- depth;
- order-book imbalance;
- microprice;
- book slope;
- replenishment/churn;
- stale-book age.

Typical roles: signal, state, execution, risk.

## 7. P7 — Reference price / fair-value transforms

Defines a causal reference rather than a standalone direction.

Examples:
- VWAP;
- rolling median;
- midquote;
- microprice-derived reference;
- robust local center.

Typical roles: reference, normalization, deviation signal input.

## 8. P8 — Relative value / derivative state

Measures relationships across linked instruments.

Examples:
- spot/perpetual basis;
- futures basis;
- funding;
- implied/realized spread measures;
- cross-venue spread;
- hedge residual.

Typical roles: core signal, state, risk.

## 9. P9 — Cross-asset information transfer

Measures leader/follower or residual relationships across assets.

Examples:
- BTC/ETH impulse vs alt response;
- beta-residual return;
- market-index residual;
- cross-sectional relative move;
- lagged cross-asset flow.

Typical roles: core signal, normalization, relative-value state.

## 10. P10 — Forced-flow / event state

Measures economically forced or episodic activity.

Examples:
- liquidation bursts where source semantics are valid;
- abnormal sweep events;
- funding/settlement events;
- abrupt depth depletion;
- large-trade clusters.

Typical roles: event trigger, state, exhaustion/continuation signal input.

## 11. P11 — Calendar / session / structural context

Measures deterministic timing or market-structure context.

Examples:
- UTC session/time-of-day;
- weekday/weekend;
- funding timestamp proximity;
- listing age;
- scheduled venue mechanics.

Typical roles: state/context only unless separately justified.

Do not create post-hoc profitable-hour filters from promotional outcomes.

## 12. Composite / proprietary features

Composite features receive a separate ID but must list all parent primitives.

Required fields:
- parent primitive IDs;
- formula;
- role;
- why composition is economically motivated;
- simpler baseline comparator;
- parameter/interaction budget.

A composite is not treated as independent evidence from its parents.

## 13. Classical-indicator mapping rule

Popular indicator names are aliases for formulas, not evidence categories.

Examples:
- RSI -> primarily P1 recent-price-position/momentum;
- MACD -> P2 trend/persistence;
- ATR -> P3 volatility/range;
- ADX -> P2 trend strength;
- Bollinger Bands -> P7 reference + P3 scale + P1 deviation;
- VWAP -> P7 reference, sometimes P4 weighting;
- OBV-like constructs -> P4/P5 depending exact formula.

The exact implementation must still be versioned. Similar names do not imply identical formulas.

## 14. Redundancy rule

Features derived from the same primitive are presumed potentially redundant until shown otherwise on calibration data.

The Feature Evidence Registry should record:
- same-family relationship;
- observed dependence where measured;
- residual/incremental information where tested;
- whether a simpler feature dominates a more complex one.

## 15. Evidence-scope rule

No taxonomy category has a global verdict.

Evidence is always scoped by:
`feature/version × role × market × horizon × mechanism × evidence stage`.
