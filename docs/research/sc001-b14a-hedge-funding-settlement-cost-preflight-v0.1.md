# SC001 — B14-A Hedge Funding & Settlement Cost Preflight v0.1

Date: 2026-09-19
Status: **FROZEN NON-ALPHA COST PREFLIGHT / NO BASIS OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b14a-edge-to-fill-card-v0.1.md`;
- `docs/research/sc001-b14a-futureschain-body-schema-pass-result-v0.1.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`.

## 1. Purpose

Freeze the remaining non-price structural cost component for B14-A before any dated-futures basis is inspected.

The unresolved component is funding on the inverse SWAP hedge.

## 2. Frozen architecture

Primary conservative cycle:

1. FUTURES entry — taker;
2. inverse SWAP hedge entry — taker;
3. FUTURES held to contractual expiry settlement;
4. inverse SWAP hedge exit — taker.

Known explicit fee floor:

- 3 taker fills × 5 bps = 15 bps;
- expiry settlement fee = 1 bp.

Known explicit fee floor:

`16 bps`

Structural reserves already frozen:

- spread/depth reserve = 10 bps;
- execution/model reserve = 10 bps.

Subtotal before hedge funding:

`36 bps`

## 3. Funding instruments

Exactly:

- `BTC-USD-SWAP`;
- `ETH-USD-SWAP`.

No symbol substitution.

## 4. Funding calibration window

Use only completed recent chronology:

`2026-06-01 00:00:00 UTC <= funding_time < 2026-09-01 00:00:00 UTC`

Role:

`NONPROMOTIONAL_STRUCTURAL_COST_CALIBRATION`

No price return, basis or strategy outcome may be accessed.

## 5. Official funding source

Reuse the already-qualified OKX historical funding source:

`GET /api/v5/public/market-data-history`

with:

- module = 3;
- instType = SWAP;
- instFamilyList = exact family;
- dateAggrType = monthly.

Trusted archive requirements:

- HTTPS;
- host = `static.okx.com`;
- exact metadata filename identity;
- ZIP CRC PASS.

Funding row schema:

`instrument_name,funding_rate,funding_time`

Only exact target SWAP rows inside the frozen window are admitted.

## 6. Source/sample gate

For each target SWAP require:

- >= 200 funding rows in the frozen 3-month window;
- all rates finite;
- all timestamps unique after exact duplicate collapse;
- >= 3 represented calendar months;
- >= 80 distinct UTC dates containing a funding settlement at hour 08:00 UTC.

The 08:00 diagnostic is needed because the frozen B14-A future expiries occur at 08:00 UTC.

Failure:

`B14A_COST_PREFLIGHT_REVIEW`

No structural burden is finalized.

## 7. Funding reserve rule

For each instrument compute:

`p99_abs_funding_bps = nearest-rank p99 of 10000 * abs(funding_rate)`

Then:

`raw_funding_reference_bps = max(BTC p99, ETH p99)`

Freeze the conservative one-settlement reserve as:

`funding_reserve_bps = max(1, ceil(raw_funding_reference_bps))`

No favorable funding credit is counted.

No mean/median reduction is allowed.

## 8. Final structural burden

If source/sample gate passes:

`final_structural_burden_bps = 36 + funding_reserve_bps`

## 9. Minimum headroom hurdle

Retain the pre-frozen minimum economic reserve:

`10 bps`

Raw headroom threshold:

`final_structural_burden_bps + 10`

Operational headroom hurdle:

round this value **up** to the next multiple of 5 bps.

Formally:

`headroom_hurdle_bps = 5 * ceil((final_structural_burden_bps + 10) / 5)`

This hurdle is frozen before any B14-A basis value is opened.

## 10. Timing interpretation

Historical 08:00 funding presence is structural corroboration only.

Before any future/live expiry trade, the actual upcoming SWAP fundingTime must be rechecked prospectively.

If funding schedule changes, later event admission must use the actual announced/current funding timestamp and may not reuse an obsolete assumption.

## 11. Firewalls

Allowed:

- funding rates;
- funding timestamps;
- static cost arithmetic.

Forbidden:

- FUTURES trade prices;
- SWAP trade prices;
- basis;
- returns;
- settlePx;
- delivery price;
- convergence;
- strategy signal;
- execution PnL;
- candidate ID.

## 12. PASS

Exact PASS:

`B14A_COST_PREFLIGHT_PASS`

Report:

- rows/months/date coverage;
- 08:00 UTC date coverage;
- median/p95/p99/max abs funding bps as diagnostics;
- frozen funding reserve;
- final structural burden;
- final headroom hurdle.

PASS authorizes only a later price-bearing B14-A headroom protocol freeze.

No price outcome is authorized by this preflight itself.
