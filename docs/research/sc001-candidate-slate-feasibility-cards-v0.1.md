# SC001 — Candidate Slate Feasibility Cards v0.1

Date: 2026-09-17  
Status: **STEP-2 NON-ALPHA FIRST PASS / NO PROMOTIONAL OUTCOME INSPECTED**

Parent governance:

- `sc001-strategy-selection-time-horizon-and-mechanism-framework-v0.2.md`;
- `sc001-candidate-feasibility-card-template-v0.1.md`;
- `sc001-legacy-retest-and-replication-policy-v0.1.md`.

This document is a first structural pass only. It does not select a winner and does not authorize alpha.

---

# C1 — E006R1 multi-asset spot/perpetual basis convergence

## Identity

- legacy relationship: strict multi-asset replication candidate of E006; new ID required;
- mechanism: M5 relative value / basis convergence;
- execution: T3 multi-leg;
- signal horizon: S2-S4 depending on baseline/state construction;
- position horizon: P2-P4, potentially up to ~30 min;
- prior limitation addressed: single-BTC event scarcity / limited breadth.

## Economic mechanism

Temporary richness of perpetual vs spot may converge because arbitrageurs / hedgers rebalance relative pricing. Edge payer is temporary imbalance between derivative and underlying demand/supply.

Persistence challenge: same-venue basis is highly arbitrageable, so gross dislocation must exceed four-fill fees, spread/depth, legging risk and funding/borrow effects by a meaningful reserve.

## Risk signature

- low intended directional beta when paired correctly;
- material legging risk;
- four-fill cost burden;
- funding/borrow and discrete hedge mismatch;
- simultaneous spot/perp liquidity dependence.

## Cost architecture

- typically four taker fills for full entry+exit if using taker/taker legs;
- structurally higher cost hurdle than T1 directional candidates;
- exact historical fee/spec intervals must be reconstructed before promoted execution/PnL;
- old E006 regular-user reference illustrated ~20 bps fee burden per reference-leg notional before spread/depth/legging, but this historical example is not automatically binding for E006R1.

## Data / causality

Need causally synchronized same-venue spot + perp feeds, exact UTC alignment, pair availability, historical contract specs, and later multi-leg execution accounting.

## Selection Sandbox needs

- pair eligibility by historical date;
- pre-period liquidity;
- rough basis event frequency;
- rough dislocation scale;
- variance for MDE/sample planning.

All such inspected periods become calibration-only.

## Cheapest sentinel

Before multi-leg engineering, estimate prospectively across eligible pairs whether dislocation events occur often enough and at a scale materially above conservative four-fill cost floor.

Kill if event frequency/headroom is structurally insufficient across most of the frozen eligible universe.

## First-pass disposition

`HOLD_INFORMATION_VALUE / SENTINEL_REQUIRED`

Reason: scientifically orthogonal and justified legacy replication, but expensive enough that cheap cost/event screening is mandatory first.

---

# C2 — multi-minute deviation / VWAP-style mean reversion

## Identity

- new family; not E001/E007/E009 rescue;
- mechanism: M3 overshoot / mean reversion;
- execution: T1 directional taker;
- signal horizon: S3 (~1-5 min);
- position horizon: P3 (~5-15 min).

## Economic mechanism

Temporary inventory pressure / short-lived order-flow imbalance may push price away from a local volume-weighted or robust central reference, followed by partial normalization after pressure decays.

Required distinction from E007/E009: signal must be genuinely multi-minute state/deviation based, not a re-labeled 60-second displacement threshold.

## Risk signature

- directional beta during each trade;
- moderate volatility/regime dependence;
- lower relative latency sensitivity than sub-minute taker strategies;
- potentially clustered losses in persistent trends.

## Cost architecture

- usually two taker fills per cycle;
- must demonstrate prospective gross move materially above two-fill fee + spread/depth + reserve;
- slower horizon may improve move/cost ratio, but this is a hypothesis, not evidence.

## Data / causality

Can likely begin with qualified trades or causal 1m-derived bars. Bar close semantics are mandatory; no same-bar entry using final bar values. L2 is deferred until gross/cost sentinel survives.

## Selection Sandbox needs

- rough distribution of multi-minute deviations;
- event frequency;
- conditional move variance for MDE/sample planning;
- trend-regime frequency only as descriptive calibration, not post-hoc filter selection.

## Cheapest sentinel

Pre-freeze one simple causal deviation definition and one horizon family, then test whether unconditional/triggered gross reversion scale and event breadth plausibly exceed conservative two-fill cost floor across the historical calibration universe.

Kill if median/typical move scale is too small relative to cost or events are too rare.

## First-pass disposition

`HOLD_INFORMATION_VALUE / SENTINEL_REQUIRED`

Reason: fills an under-covered S3/P3 cell with relatively simple T1 execution and low engineering cost, but must prove it is not merely E007/E009 at a slower clock.

---

# C3 — 5m/10m continuation or volatility expansion

## Identity

- new family; not E004 rescue;
- mechanism: M4 continuation / breakout / short trend;
- execution: T1;
- signal horizon: S3-S4;
- position horizon: P3-P4.

## Economic mechanism

Persistent informed/forced flow or delayed participation may create short-lived continuation after a multi-minute range/volatility expansion.

Required distinction from E004: the future candidate must define a new multi-minute mechanism and bar-causal rule prospectively rather than extending the failed short compression-breakout threshold neighborhood.

## Risk signature

- directional beta;
- vulnerable to false breakouts / mean reversion;
- potentially better in trending or stress regimes, so regime concentration risk is material;
- moderate latency sensitivity relative to H0/H1.

## Cost architecture

- two fills per cycle for a simple directional taker implementation;
- must show gross continuation scale comfortably above transaction costs;
- longer holds increase path risk even if fee ratio improves.

## Data / causality

Causal 1m/5m bars may suffice for first sentinel if final-bar timing is enforced. Intrabar stop/target ordering cannot be inferred from OHLC; event-order-dependent rules require finer source data.

## Selection Sandbox needs

- candidate event frequency;
- bar-return distribution;
- persistence horizon variance;
- common-market regime frequency for MDE planning.

## Cheapest sentinel

Use one simple prospectively defined expansion/continuation condition and test whether future signed move over the chosen multi-minute horizon has enough magnitude/breadth to clear a conservative two-fill cost reserve.

Kill if continuation is too weak/unstable or only present in isolated regimes/instruments.

## First-pass disposition

`HOLD_INFORMATION_VALUE / SENTINEL_REQUIRED`

Reason: materially under-covered S3/S4 region and cheap first-pass data requirements, but prior E004 failure warrants skepticism and strict no-rescue separation.

---

# C4 — BTC/ETH -> alt lead/lag

## Identity

- new family;
- mechanism: M6 cross-asset information transfer;
- execution: T1 directional on follower asset;
- signal horizon: S1-S2;
- position horizon: P1-P2.

## Economic mechanism

Information or forced flow may reach the most liquid leader markets first and diffuse to selected followers with a short delay.

The economic question is not same-asset reversal/continuation but delayed cross-market price discovery.

## Risk signature

- directional beta on follower trades;
- strong common-market exposure can create spurious predictability;
- synchronization/clock error risk;
- likely decay sensitive to market efficiency and latency.

## Cost architecture

- usually two follower-market taker fills;
- signal leg may be observation-only;
- must beat follower fees/spread/depth;
- latency may still matter substantially because lead/lag can decay quickly.

## Data / causality

Requires synchronized leader/follower timestamps and strict availability semantics. Must control for common market move; naive correlation is insufficient.

## Selection Sandbox needs

- synchronization quality;
- lagged relation scale;
- follower event frequency;
- common-factor residual variance;
- universe of historically liquid followers chosen independently of profitability.

## Cheapest sentinel

Pre-register leader shock definition and follower response horizon, then test causal lagged predictive relation after common-market/beta control on calibration data.

Kill if predictive relation disappears after synchronization/common-factor control or is too small versus follower cost floor.

## First-pass disposition

`HOLD_INFORMATION_VALUE / SENTINEL_REQUIRED`

Reason: genuinely orthogonal mechanism with moderate engineering cost, but high risk of spurious correlation if synchronization/common-factor controls are weak.

---

# C5 — large-trade / liquidity-sweep / forced-flow exhaustion

## Identity

- new family;
- mechanism: M7 forced-flow + M3 exhaustion/reversion;
- execution: T1;
- signal horizon: S0-S2;
- position horizon: P1-P2.

## Economic mechanism

A large aggressive trade or liquidity sweep may be partially price-insensitive/forced, temporarily consuming local depth and creating an overshoot that reverts after the forced flow ends.

## Risk signature

- event-driven directional exposure;
- adverse-selection risk if event is informed rather than forced;
- strong dependence on stress/liquidation regimes;
- likely right-tail event concentration.

## Cost architecture

- typically two taker fills;
- potentially large raw moves, but adverse selection can dominate;
- event rarity and regime concentration are key economic risks.

## Data / causality

Trade data may support large-trade candidates; true sweep/depth-consumption definitions may require L2. Do not acquire heavy L2 until a trade-level frequency/headroom sentinel justifies it.

## Selection Sandbox needs

- objective event-frequency estimate;
- size/liquidity normalization design;
- post-event move variance;
- stress-day concentration;
- MDE/sample planning.

## Cheapest sentinel

Start with an objectively normalized aggressive-trade/cluster definition that is observable from trades alone. Test event frequency and post-event signed move scale versus two-fill cost floor before any L2 sweep semantics.

Kill if too rare, too regime-concentrated or post-event move lacks stable economic headroom.

## First-pass disposition

`HOLD_INFORMATION_VALUE / SENTINEL_REQUIRED`

Reason: economically meaningful forced-flow story and new M7 coverage, but event scarcity/adverse-selection risk may make sample requirements large.

---

# C6 — cross-sectional short-horizon dispersion/reversion

## Identity

- new family;
- mechanism: M5/M6 cross-sectional relative value;
- execution: T3 or portfolio multi-leg;
- signal horizon: S3-S4;
- position horizon: P3-P4.

## Economic mechanism

Temporary dispersion among contemporaneously related liquid assets may partially mean-revert after common-market effects are removed, allowing a lower-beta relative-value portfolio rather than outright direction prediction.

## Risk signature

- lower intended market beta;
- multi-leg/portfolio turnover;
- factor-model / common-shock misspecification risk;
- cross-asset liquidity mismatch;
- legging and discrete sizing risk.

## Cost architecture

- potentially several fills per rebalance, so turnover cost can dominate;
- requires conservative portfolio turnover and fee/depth budget before profitability testing;
- must avoid creating apparent alpha from tiny residual moves overwhelmed by multi-leg costs.

## Data / causality

Needs historically selected multi-asset universe, synchronized prices, causal factor/common-market estimate, and later discrete portfolio execution/accounting.

## Selection Sandbox needs

- cross-sectional correlation/factor structure;
- residual dispersion scale;
- rebalance frequency;
- expected turnover;
- MDE/sample planning.

## Cheapest sentinel

Estimate prospective residual-dispersion move scale and expected turnover under a simple predeclared causal common-factor construction. Compare gross residual convergence scale with conservative multi-leg cost floor.

Kill if turnover/cost consumes plausible residual convergence or cross-sectional structure is too unstable.

## First-pass disposition

`HOLD_INFORMATION_VALUE / SENTINEL_REQUIRED`

Reason: valuable low-beta/under-covered cell, but more complex than C2/C3/C4 and must first prove residual move scale can support portfolio execution costs.

---

# Cross-candidate first-pass conclusion

No candidate is yet `ELIGIBLE_FOR_BATCH` because the required sentinel/calibration quantities have not been prospectively frozen and measured under the new framework.

Structural observations only:

- C2 and C3 appear cheapest to falsify using causal trade/bar-derived data;
- C4 is also relatively cheap but synchronization/common-factor controls are essential;
- C1 and C6 are economically orthogonal but structurally cost-heavy due to multi-leg execution;
- C5 has a strong economic story but may be event-scarce and eventually L2-heavy.

These are research-cost observations, not profitability rankings.

Next step: define one prospectively frozen **Selection/Calibration Sandbox** and sentinel specification for each C1-C6 without using new promotional outcomes.
