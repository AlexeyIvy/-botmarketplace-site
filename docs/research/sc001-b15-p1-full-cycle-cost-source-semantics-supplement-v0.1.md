# SC001 — B15-P1 Full-Cycle Cost Source-Semantics Supplement v0.1

Date: 2026-09-24  
Status: **PRE-PRICE SUPPLEMENT / BINDING FOR STAGE C PREFLIGHT**

Parent:

`docs/research/sc001-b15-p1-full-cycle-edge-to-fill-card-v0.1.md`

## 1. Purpose

Remove venue-specific fee ambiguities before the Stage C structural preflight.

No B15 price, spread, headroom or PnL outcome is used.

## 2. Bybit withdrawal amount convention

For inventory restoration, freeze:

`feeType = 0`

Interpret the modeled transfer quantity as the target amount that must arrive at the destination.

If Bybit reports percentage fee `p > 0` and fixed fee `F`:

`handling_fee = Q_receive / (1 - p) × p + F`

If `p = 0`:

`handling_fee = F`

Reject `p >= 1`.

The buffered prospective burden remains:

`1.25 × handling_fee`

This is deliberately conservative.

## 3. OKX withdrawal burden

Use all applicable source fields:

- fixed `fee`;
- `feeCcy`;
- `burningFeeRate`;
- withdrawal/minimum/maximum constraints.

The fee currency must be explicit.

If `feeCcy` is neither the transferred asset nor USDT:

`FEE_CCY_CONVERSION_REQUIRED`

The event cannot obtain a primary headroom PASS until a later frozen causal price protocol defines conversion of that fee currency.

No ad-hoc conversion is allowed.

## 4. Route selection is amount-aware but outcome-blind

A future event's restoration route may depend on the required transfer quantity because percentage fees and minimums are amount-dependent.

This does not permit route choice based on observed arbitrage profitability.

Selection inputs are restricted to:

- frozen canonical route identity;
- current source availability;
- required restoration quantity;
- source-reported fee/minimum/limit metadata;
- deterministic network_uid tie-break.

Relative price dislocation, later PnL and historical strategy outcome are forbidden route-selection inputs.

## 5. Account/pair trading fee

For both venues, query the authenticated exact spot pair/account fee endpoint when Stage D/E later needs a causal fee snapshot.

Applied opening fee rate per fill:

`max(10 bps, causally known exact account/pair taker commission rate)`

If unavailable:

`FEE_RATE_UNKNOWN`

The 10 bps floor cannot be lowered by VIP status, rebates, zero-fee promotions or post-hoc account changes.

## 6. Stage C consequence

Stage C does not need prices.

It only needs to prove:

- the frozen arithmetic is internally coherent;
- every future cost component has a defined source field or explicit fail-closed state;
- the route-selection algorithm cannot depend on price outcomes;
- no cost can be silently omitted;
- later price conversion rules are clearly deferred and version-gated.
