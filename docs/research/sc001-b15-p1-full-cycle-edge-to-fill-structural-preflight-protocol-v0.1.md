# SC001 — B15-P1 Full-Cycle Edge-to-Fill Structural Preflight Protocol v0.1

Date: 2026-09-24  
Status: **PRE-PRICE STRUCTURAL PREFLIGHT SPECIFICATION**

## Inputs

Binding inputs:

1. final v0.2.2 identity/freeze artifact supplement;
2. artifact-complete checkpoint PASS;
3. Full-Cycle Edge-to-Fill Card v0.1;
4. Full-Cycle Cost Model v0.1;
5. Spot Fee Source Evidence v0.1;
6. Stage C Source-Semantics Evidence v0.1;
7. Cost Source-Semantics Supplement v0.1;
8. Post-Identity Next-Stage Authorization v0.1.

## Mandatory checks

### Foundation

- final semantic freeze PASS;
- artifact set complete;
- artifact-complete checkpoint PASS;
- 192 admitted / 0 review / 9 excluded;
- 207 canonical representations;
- 414 directed asset edges;
- 12 common USDT representations;
- zero unresolved identity rows.

### Opening execution

- exactly two spot taker fills;
- reference notional = 10,000 USDT per opening leg;
- per-fill fee floor = 10 bps;
- two-fill fee floor = 20 bps;
- actual account/pair taker fee can only raise the burden;
- unknown fee => fail closed.

### Reserves

- legging/latency/model = 10 bps;
- venue/counterparty/inventory = 10 bps;
- capital lock = 3 bps per started 24h;
- minimum lock horizon = 7 days;
- minimum lock reserve = 21 bps;
- minimum non-transfer structural floor = 61 bps;
- extra economic headroom = 10 bps;
- minimum hurdle before transfer costs = 71 bps.

### Transfer restoration

- base direction = cheap -> rich;
- quote direction = rich -> cheap;
- only frozen common routes route-eligible;
- one-sided quote identities never route-eligible;
- route selection is price-outcome-blind;
- source fee/minimum metadata required;
- transfer fee uncertainty multiplier = 1.25;
- actual higher cost is upward mandatory;
- missing base cost => BASE_REBALANCE_COST_UNKNOWN;
- missing quote cost => QUOTE_REBALANCE_COST_UNKNOWN;
- unsupported fee-currency conversion => FEE_CCY_CONVERSION_REQUIRED;
- notional/minimum/limit failure => NOTIONAL_NOT_RESTORABLE.

### Bybit fee adapter

Synthetic unit cases must pass:

1. fixed fee 1.0, p=0, target receive=100 => handling=1.0;
2. fixed fee 1.0, p=0.01, target receive=100 => handling=100/0.99*0.01+1;
3. p>=1 => invalid/fail closed.

### Structural arithmetic

Must verify:

`20 + 10 + 10 + 21 = 61 bps`

and

`61 + 10 = 71 bps`

No transfer-fee amount or price conversion may be fabricated at Stage C.

### Price firewall

Must verify all Stage C artifacts explicitly retain:

- price_data_used=false;
- pnl_data_used=false;
- collector launch unauthorized;
- live execution unauthorized.

## PASS state

`B15_P1_FULL_CYCLE_EDGE_TO_FILL_STRUCTURAL_PREFLIGHT_PASS`

A PASS authorizes only:

`PREPARE_15_SECOND_NONPRICE_COLLECTOR_DESIGN`

It does not authorize collector launch or any price/PnL stage.

## FAIL state

Any missing field semantics, arithmetic mismatch, route-selection ambiguity, silent cost omission, identity hash mismatch or price-firewall violation:

`B15_P1_FULL_CYCLE_EDGE_TO_FILL_STRUCTURAL_PREFLIGHT_FAIL`

Then STOP.
