# SC001 — B15-P1 Full-Cycle Cost Source-Semantics Supplement v0.2

Date: 2026-09-24  
Status: **PRE-PRICE BINDING SUPPLEMENT**  
Supersedes: `sc001-b15-p1-full-cycle-cost-source-semantics-supplement-v0.1.md`

## 1. Purpose

Clarify venue-specific fee arithmetic before Stage C structural preflight.

No B15 price, spread, headroom or PnL outcome has been opened.

## 2. Bybit

Use authenticated account/pair fee data later when required.

Opening taker fee:

`max(10 bps, takerFeeRate × 10,000)`

For restoration withdrawal modeling freeze `feeType=0`.

If target received amount is `Q`, fixed fee is `F`, and percentage fee is `p`:

- `p = 0`: `handling = F`;
- `0 < p < 1`: `handling = Q/(1-p) × p + F`;
- `p >= 1`: fail closed.

Prospective withdrawal burden:

`1.25 × handling`

## 3. OKX account/pair taker fee

OKX API sign convention:

- negative taker rate = commission;
- positive taker rate = rebate.

Freeze:

`commission_bps = max(0, -taker_rate × 10,000)`

`applied_taker_bps = max(10, commission_bps)`

A rebate never reduces the frozen 10 bps floor.

## 4. OKX withdrawal fee currency

If fixed fee currency equals transferred asset:

`DIRECT_ASSET_UNIT_COST`

If fixed fee currency is USDT:

`DIRECT_USDT_COST`

Otherwise:

`FEE_CCY_CONVERSION_REQUIRED`

and primary headroom is blocked until a later causal price protocol defines conversion.

## 5. OKX burningFeeRate

Official OKX semantics state that some currencies can have a percentage burning fee based on withdrawal quantity.

Stage C v0.1 deliberately does **not** infer a target-receive gross-up formula from that description.

Therefore:

- empty / zero `burningFeeRate` => structurally supported;
- nonzero `burningFeeRate` => `OKX_BURNING_FEE_FORMULA_REVIEW`;
- such a route is not eligible for primary route selection in Stage C v0.1.

This is fail-closed, not an assumption that the fee is zero.

## 6. Amount-aware but outcome-blind route selection

Route selection may depend on required transfer amount because fees/minimums can be amount dependent.

It may not depend on:

- observed cross-venue spread;
- realized PnL;
- future price outcome;
- historical strategy success.

Allowed inputs:

- frozen canonical route identity;
- route state observed causally;
- required restoration amount;
- source fee/minimum/limit metadata;
- deterministic canonical network_uid tie-break.

## 7. Consequence

Stage C can PASS only if every future economic component is either:

1. explicitly computable from frozen reserve/source semantics; or
2. mapped to an explicit fail-closed status.

No silent zero-cost default is allowed.
