# SC001 — B14-A Hedge Funding & Settlement Cost Preflight PASS v0.1

Date: 2026-09-19
Status: **B14A_COST_PREFLIGHT_PASS**
Scope: `SCALPING RESEARCH / SC001`

## 1. Exact observed state

`B14A_COST_PREFLIGHT_PASS`

BTC-USD-SWAP:

- rows = 275;
- p99 absolute funding = 1.0 bp;
- UTC dates with 08:00 funding = 92.

ETH-USD-SWAP:

- rows = 275;
- p99 absolute funding = 1.0 bp;
- UTC dates with 08:00 funding = 92.

All frozen source/sample gates passed.

## 2. Frozen structural economics

Funding reserve:

`1 bp`

Known components:

- 3 taker fills = 15 bps;
- expiry settlement fee = 1 bp;
- spread/depth reserve = 10 bps;
- execution/model reserve = 10 bps;
- hedge funding reserve = 1 bp.

Final structural burden:

`37 bps`

Minimum additional economic reserve:

`10 bps`

Raw arithmetic threshold:

`47 bps`

Frozen operational headroom hurdle, rounded upward under the predeclared rule:

`50 bps`

## 3. Interpretation

B14-A now has a complete pre-price structural burden.

The 50 bps headroom hurdle was determined before any dated-futures basis value was opened.

## 4. Firewalls preserved

Observed false:

- FUTURES price accessed;
- SWAP price accessed;
- basis calculated;
- return calculated;
- settlePx accessed;
- delivery price accessed;
- convergence calculated;
- execution/PnL;
- candidate ID assigned.

## 5. Next step

Use the nearest already-frozen prospective expiry event:

`2026-09-25T08:00:00Z`

for a protected P0 raw-data capture followed by a separately frozen headroom readout.
