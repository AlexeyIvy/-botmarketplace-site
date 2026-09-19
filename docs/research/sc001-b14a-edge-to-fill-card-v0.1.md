# SC001 — B14-A Dated-Futures Final-Settlement Convergence Edge-to-Fill Card v0.1

Date: 2026-09-19
Status: **NON-ALPHA STRUCTURAL CARD / FUNDING-COST QUALIFICATION REQUIRED BEFORE HEADROOM FREEZE**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`;
- `docs/research/sc001-b14a-futureschain-body-schema-pass-result-v0.1.md`;
- `docs/research/sc001-b14a-exact-12-future-expiry-identity-freeze-v0.1.json`;
- `docs/research/sc001-b14a-okx-dated-futures-source-settlement-spec-audit-v0.1.md`.

## 1. Independent base mechanism

`DATED FUTURES FINAL-SETTLEMENT BASIS CONVERGENCE`

Economic source:

a dated futures contract has a contractual terminal settlement/delivery anchor at `expTime`.

The edge, if present, is residual pre-expiry mispricing relative to an economically compatible same-underlying hedge/reference.

This is not ordinary open-ended mean reversion.

## 2. Initial architecture

Preferred same-venue structure:

- dated inverse FUTURES leg;
- same-underlying inverse SWAP hedge.

Illustrative cycle:

1. enter dated FUTURES;
2. enter inverse SWAP hedge;
3. carry FUTURES to contractual expiry settlement;
4. exit SWAP hedge after settlement.

The dated FUTURES exit is replaced by contractual settlement, but settlement is not free.

## 3. Structural fills / charges

Conservative primary execution assumption:

- FUTURES entry = taker;
- SWAP hedge entry = taker;
- SWAP hedge exit = taker;
- FUTURES expiry settlement = exchange settlement charge.

Structural market fills:

`3`

Settlement event:

`1`

Current regular-user fee reference:

- taker = `5 bps/fill`;
- 3 taker fills = `15 bps`;
- expiry settlement fee = `1 bp`.

Preliminary explicit fee floor:

`16 bps`

No maker rebate/discount is assumed.

## 4. Spread / depth exposure

Three executable market fills remain exposed to:

- bid/ask spread;
- depth/VWAP;
- latency;
- legging;
- discrete contracts.

Prospective conservative reserve before L2 qualification:

`10 bps`

This is a structural reserve, not a measured execution estimate.

## 5. Execution/model reserve

Prospective reserve:

`10 bps`

Covers:

- expiry-time timing mismatch;
- hedge close timing;
- settlement/reference mechanics;
- residual delta/contract rounding;
- source/clock/model error.

## 6. Funding exposure — unresolved mandatory item

The SWAP hedge may cross an official funding timestamp during the final pre-expiry holding interval.

Therefore funding cannot be assumed zero.

Before freezing any B14-A headroom threshold, qualify:

- exact BTC-USD-SWAP / ETH-USD-SWAP funding schedule around expiry;
- applicable realized funding-rate source;
- conservative cost treatment;
- sign handling for long/short hedge orientation.

Required later rule:

funding benefit may not be counted prospectively as guaranteed edge.

A conservative burden must include either:

- realized adverse funding where causally known, or
- an absolute / otherwise fail-closed funding reserve frozen before outcomes.

## 7. Preliminary burden excluding unresolved funding

Known/reserved components:

- explicit fee floor = 16 bps;
- spread/depth reserve = 10 bps;
- execution/model reserve = 10 bps.

Subtotal:

`36 bps + funding_reference`

This is not yet the final structural burden.

## 8. Minimum economic reserve

Require at least:

`10 bps`

of raw headroom above final structural burden before a convergence study is justified.

Therefore the eventual raw headroom hurdle must satisfy:

`headroom_hurdle >= 46 bps + funding_reference`

For operational simplicity, a later protocol may round upward only after the funding reference is frozen.

No threshold may be lowered after price outcomes.

## 9. Expected information scale

Mechanism-specific prior:

`UNKNOWN_NEEDS_NON_ALPHA_DATA`

Reason:

the contractual terminal anchor makes convergence economically real, but current SC001 evidence has not yet measured the scale of residual basis close to expiry for these inverse contracts.

No assumed 50+ bps edge is claimed before the headroom sentinel.

## 10. Expected horizon

Candidate design zone:

final pre-expiry window only.

Preferred first causal anchor source:

official exchange settlement-estimate / expiry clock.

Exact price-bearing decision window must be frozen later.

No window is selected from observed basis outcomes here.

## 11. Capital-time / opportunity rate

Each dated contract offers one terminal expiry event.

Inference unit:

`expiry event × underlying family`

Ticks are not independent trials.

Current frozen future set provides:

- six BTC expiries;
- six ETH expiries.

Future events may accumulate prospectively.

## 12. Capacity / liquidity concerns

Potential concerns:

- liquidity can decay near expiry;
- dated contract and SWAP contract values differ by underlying family;
- hedge sizing must account for inverse-contract delta;
- settlement in BTC/ETH introduces coin-denominated PnL/accounting;
- funding on the SWAP hedge can alter carry economics.

These require later non-alpha execution specification.

## 13. Edge-to-Fill classification

Current classification:

`UNKNOWN_NEEDS_NON_ALPHA_DATA`

Reason:

- independent mechanism = PASS;
- fill architecture = materially better than four-fill open-ended convergence;
- explicit fee floor known;
- source/schema = PASS;
- funding reference = not yet frozen;
- actual pre-expiry basis headroom = unopened.

## 14. Hard stop / next gate

Do not open B14-A basis prices yet.

Required next non-alpha step:

`B14A_HEDGE_FUNDING_AND_SETTLEMENT_COST_PREFLIGHT`

Only after its PASS may the final structural burden and price-bearing headroom hurdle be frozen.
