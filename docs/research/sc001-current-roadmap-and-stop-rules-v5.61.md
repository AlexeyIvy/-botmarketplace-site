# SC001 Current Roadmap and Stop Rules v5.61

Date: 2026-09-24  
Status: **B15-P1 STAGE C FULL-CYCLE EDGE-TO-FILL PREFLIGHT PASS / 15-SECOND NON-PRICE COLLECTOR DESIGN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.60.md`

## Stage C structural preflight

Bundle:

`bundle_20260924T095623Z_f2990716`

Job:

`job_20260924T100910Z_d1997b2a`

Status:

`B15_P1_FULL_CYCLE_EDGE_TO_FILL_STRUCTURAL_PREFLIGHT_PASS`

All checks passed.

Frozen cost model:
- reference notional = 10,000 USDT per opening leg;
- opening market fills = 2 taker fills;
- minimum opening fee burden = 20 bps;
- legging/latency/model reserve = 10 bps;
- venue/counterparty/inventory reserve = 10 bps;
- minimum 7-day capital-lock reserve = 21 bps;
- minimum non-transfer structural burden = 61 bps;
- minimum economic headroom reserve = 10 bps;
- minimum hurdle before transfer costs = 71 bps;
- transfer-fee uncertainty multiplier = 1.25.

Unit tests:
- Bybit withdrawal formula = 3/3 PASS;
- trading-fee adapters = 5/5 PASS;
- amount-aware/outcome-blind route selection = 4/4 PASS;
- OKX fail-closed withdrawal semantics = 3/3 PASS.

Source-field coverage is PASS for Bybit and OKX fee/minimum/status/confirmation metadata.

Fail-closed statuses include:
- FEE_RATE_UNKNOWN;
- BASE_REBALANCE_COST_UNKNOWN;
- QUOTE_REBALANCE_COST_UNKNOWN;
- FEE_CCY_CONVERSION_REQUIRED;
- OKX_BURNING_FEE_FORMULA_REVIEW;
- NOTIONAL_NOT_RESTORABLE;
- SOURCE_INVALID.

## Firewall

Still false:
- price_data_used;
- pnl_data_used;
- collector_authorized;
- collector_launch_authorized;
- live_execution_authorized.

No price dataset was present in the Stage C bundle.

## What Stage C PASS authorizes

Only:

`PREPARE_15_SECOND_NONPRICE_COLLECTOR_DESIGN`

It does not authorize collector launch.

Required subsequent gates:
1. collector design freeze;
2. collector implementation self-test;
3. read-only source capability revalidation;
4. explicit collector launch authorization;
5. prospective source-only collection;
6. later price/headroom protocol freeze.

## Next state

`PREPARE_15_SECOND_NONPRICE_COLLECTOR_DESIGN`
