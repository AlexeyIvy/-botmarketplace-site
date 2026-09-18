# SC001 — Independent Base Concept B3: Stablecoin Parity Dislocation Reversion v0.1

Date: 2026-09-18
Status: **NON-ALPHA FEASIBILITY CARD / BASE MECHANISM**
Scope: `SCALPING RESEARCH / SC001`

## 1. Identity

- provisional base concept: `B3_STABLECOIN_PARITY_REVERSION`
- candidate ID: **NOT YET ASSIGNED**
- mechanism family: M3/M5 structural parity reversion
- execution archetype: T1 directional spot
- Signal Horizon: S1-S3
- Position Horizon: P2-P4
- independence: external redemption/parity anchor, not local statistical mean reversion

## 2. Economic mechanism

Initial pair:

`USDC-USDT`

Economic anchor:

USDC is designed/redeemable at USD parity through eligible institutional redemption channels, while exchange-market prices may temporarily deviate from parity.

The base hypothesis is not `price reverts to its moving average`.

It is:

`exchange stablecoin cross-rate dislocation may normalize toward external fiat parity/arbitrage pressure`.

The trader need not itself have direct Circle Mint access for the market-wide arbitrage anchor to exist, but lack of direct redemption access remains a risk.

## 3. Time architecture

Preliminary design envelope:

- spot trade/book data;
- causal cross-rate versus 1.0000 reference;
- decision cadence 1-5 seconds;
- expected hold 1-15 minutes;
- hard max hold <=30 minutes.

No threshold is selected in this card.

## 4. Feature inventory

Base-defining measurement:

`peg_deviation_bps = 10000 * ln(USDCUSDT_price / 1.0)`

No local-reference feature and no RB001-RB018.

## 5. Risk signature

- directional crypto beta: low;
- stablecoin credit/depeg risk: primary;
- liquidity risk: material during stress;
- inventory duration: minutes;
- funding: none;
- legging: none for direct cross pair;
- tail risk: severe if parity anchor itself is impaired.

## 6. Edge-to-Fill preflight

Structural fills:

- spot entry;
- spot exit;
- total = 2.

Conservative references:

- fee floor: 10 bps total at 5 bps/fill reference;
- spread/slippage/model reserve: 5 bps;
- preliminary structural burden: `15 bps`.

Expected information scale:

Ordinary deviations may be much smaller than 15 bps, but a genuine peg-dislocation mechanism has a credible reason to occasionally reach tens of bps during stress.

Edge-to-Fill classification:

`UNKNOWN_NEEDS_NON_ALPHA_HEADROOM_SENTINEL`

## 7. Data feasibility

Current OKX spot market support for `USDC-USDT` exists.

Historical spot trade/candle data are public; historical order-book availability requires metadata qualification.

No paid dataset is required for the cheapest sentinel.

## 8. Selection/calibration governance

Do not choose famous depeg dates after outcome.

Calibration chronology must be selected prospectively by calendar rule.

Do not exclude adverse credit events merely because convergence failed.

## 9. Cheapest sentinel

Before execution modeling measure on a frozen chronology:

- seconds/minutes with absolute peg deviation above the future structural burden;
- episode duration;
- reversion within fixed <=30m max horizon;
- data coverage.

The structural threshold must be derived from cost reserve before outcome, not from historical quantiles.

## 10. Independence check

Not C2 rescue because:

- reference is external fixed parity, not a rolling local VWAP/median;
- economic anchor is redemption/arbitrage parity;
- state is a stablecoin cross-rate, not a generic price deviation.

Not C8B because no cross-venue paired convergence and only two fills.

## 11. Main falsification

If deviations large enough to clear the structural burden are too rare, or fail to normalize within the frozen max horizon, reject.

## 12. Disposition

`ELIGIBLE_FOR_BATCH`

Reason:

Independent parity anchor, two-fill architecture, public data, bounded mechanism, plausible rare large deviations.

No outcome run authorized yet.
