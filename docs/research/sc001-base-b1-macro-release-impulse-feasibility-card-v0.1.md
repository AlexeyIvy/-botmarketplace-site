# SC001 — Independent Base Concept B1: Scheduled Tier-1 US Macro Release Impulse v0.1

Date: 2026-09-18
Status: **NON-ALPHA FEASIBILITY CARD / BASE MECHANISM**
Scope: `SCALPING RESEARCH / SC001`

## 1. Identity

- provisional base concept: `B1_MACRO_RELEASE_IMPULSE`
- candidate ID: **NOT YET ASSIGNED**
- mechanism family: M7 external scheduled event
- execution archetype: T1 directional taker
- Signal Horizon: S0/S1
- Position Horizon: P1/P2
- prior SC001 relationship: independent of C1-C10; event selection comes from external official release calendars, not an SC001 feature

## 2. Economic mechanism

Base event set:

- U.S. CPI release;
- U.S. Employment Situation release.

Only official scheduled release timestamps are used.

Economic payer/source:

Macro information arrival forces rapid repricing across risk assets, including crypto. The base opportunity is the post-release price-discovery process, not an endogenous breakout state.

Prospective direction rule for later design:

- direction determined only by the first causal post-release BTC impulse;
- no macro-surprise model;
- no forecast-consensus input;
- no C1-C10 auxiliary feature.

Main falsification:

If scheduled releases do not produce enough post-release gross move headroom to exceed a conservative two-fill + event-slippage burden, stop before execution modeling.

## 3. Time architecture

Preliminary design envelope:

- source price: BTC-USDT-SWAP trade tape;
- official event timestamp: release time;
- initial impulse window: fixed at 1 second in later freeze;
- decision only after that first second closes causally;
- expected hold envelope: 30-60 seconds;
- hard max hold <=120 seconds.

No event outcome is opened in this card.

## 4. Feature inventory

Base-defining features only:

1. official event timestamp;
2. causal 1-second post-release BTC return sign.

No RB001-RB018 is part of the base mechanism.

Possible auxiliary N1/N3 blocks may be considered only after base survival.

## 5. Risk signature

- directional beta: high but short-lived;
- volatility exposure: high;
- liquidity/slippage exposure: high;
- inventory duration: short;
- funding exposure: negligible at sub-minute hold;
- legging risk: none;
- event-regime dependence: extreme;
- venue concentration: single-venue initial study.

## 6. Edge-to-Fill preflight

Structural fills:

- entry taker;
- exit taker;
- total = 2.

Conservative references:

- fee floor: 10 bps total using 5 bps/fill SC001 reference;
- event spread/slippage/model reserve: 10 bps;
- preliminary structural burden: `20 bps`.

Expected information scale:

Unknown prospectively, but a scheduled macro repricing mechanism can plausibly generate tens of bps on some releases.

Edge-to-Fill classification:

`UNKNOWN_NEEDS_NON_ALPHA_HEADROOM_SENTINEL`

Unlike ordinary 1-4 bps endogenous features, there is an independent reason for larger move scale.

## 7. Universe

Initial base universe:

- BTC-USDT-SWAP only.

Reason:

BTC is the deepest crypto macro proxy and avoids asset-selection multiplicity.

No alt subset.

## 8. Data feasibility

Required:

- official BLS CPI/Employment release timestamps;
- historical BTC-USDT-SWAP trades at sub-second/second resolution;
- historical source identity and UTC mapping.

Current public-data feasibility is high.

## 9. Calibration governance

Use only prospectively declared historical release dates.

Anything used to define impulse/hold/slippage becomes nonpromotional.

No surprise-size threshold, event subtype winner selection, or outcome-based date exclusion.

## 10. Cheapest sentinel

Before execution simulation:

Measure for a frozen calibration set:

- absolute BTC move from release timestamp to +60s;
- event count;
- event-day coverage.

Prospective kill concept:

If broad event move scale is far below a 20 bps structural burden, reject before detailed entry timing.

Exact sentinel gates must be frozen later before outcome.

## 11. Independence check

Not C3 rescue because:

- C3 selects endogenous range/expansion events;
- B1 selects exogenous official information-release timestamps;
- B1 has no range/ATR/breakout threshold.

Not C5/C10 because no flow/depth stress feature defines the event.

## 12. Disposition

`ELIGIBLE_FOR_BATCH`

Reason:

Independent economic payer, two-fill architecture, public data, plausible event-scale headroom, bounded complexity.

No outcome run authorized yet.
