# SC001 — B15-P1 Full-Cycle Edge-to-Fill Structural Preflight Protocol v0.2

Date: 2026-09-24  
Status: **PRE-PRICE STRUCTURAL PREFLIGHT SPECIFICATION**  
Supersedes: `sc001-b15-p1-full-cycle-edge-to-fill-structural-preflight-protocol-v0.1.md`

## Binding foundation

Require:

- final v0.2.2 identity freeze PASS;
- final artifact set complete;
- artifact-complete checkpoint restore PASS;
- 192 admitted, 0 review, 9 excluded;
- 207 canonical representations;
- 414 directed asset edges;
- 12 common USDT representations;
- 14 known-one-sided quote representations;
- zero unresolved identity rows.

## Binding cost model

Reference notional:

`10,000 USDT per opening leg`

Opening architecture:

- exactly 2 spot taker fills;
- rich venue sells base;
- cheap venue buys base;
- no maker rebate required;
- no borrow;
- no derivative hedge.

Trading fee floor:

- 10 bps per fill;
- 20 bps total minimum;
- actual causally known account/pair commission can only increase burden;
- unknown actual fee => `FEE_RATE_UNKNOWN`.

## Reserves

- legging/latency/model = 10 bps;
- venue/counterparty/inventory = 10 bps;
- capital lock = 3 bps per started 24h;
- minimum lock horizon = 7 days;
- minimum lock reserve = 21 bps;
- minimum economic headroom = 10 bps.

Arithmetic invariants:

`20 + 10 + 10 + 21 = 61 bps`

`61 + 10 = 71 bps before transfer costs`

## Transfer restoration

Base:

`cheap -> rich`

Quote:

`rich -> cheap`

Only frozen common routes are cross-venue route eligible.

Known one-sided quote identities are never route eligible.

Route choice must be amount-aware but price-outcome-blind.

Prospective transfer fee multiplier:

`1.25`

Higher realized source cost is an upward-only adjustment.

## Venue adapters

### Bybit

Synthetic tests:

- Q=100, F=1, p=0 => handling=1;
- Q=100, F=1, p=0.01 => handling=100/0.99*0.01+1;
- p>=1 => invalid.

### OKX trading fee

Synthetic tests:

- taker=-0.001 => applied 10 bps;
- taker=-0.0015 => applied 15 bps;
- taker=+0.002 rebate => applied 10 bps floor.

### OKX withdrawal

- zero/empty burningFeeRate is supported;
- nonzero burningFeeRate => `OKX_BURNING_FEE_FORMULA_REVIEW`;
- unsupported fee currency => `FEE_CCY_CONVERSION_REQUIRED`.

## Fail-closed coverage

Required explicit statuses include:

- FEE_RATE_UNKNOWN;
- BASE_REBALANCE_COST_UNKNOWN;
- QUOTE_REBALANCE_COST_UNKNOWN;
- FEE_CCY_CONVERSION_REQUIRED;
- OKX_BURNING_FEE_FORMULA_REVIEW;
- NOTIONAL_NOT_RESTORABLE;
- SOURCE_INVALID.

No missing cost may default to zero.

## Price firewall

Stage C bundle must contain no market-price dataset.

Must remain false:

- price_data_used;
- pnl_data_used;
- collector_authorized;
- collector_launch_authorized;
- live_execution_authorized.

## PASS

`B15_P1_FULL_CYCLE_EDGE_TO_FILL_STRUCTURAL_PREFLIGHT_PASS`

PASS authorizes only:

`PREPARE_15_SECOND_NONPRICE_COLLECTOR_DESIGN`

It does not authorize collector launch or price/PnL.
