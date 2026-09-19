# SC001 Current Roadmap and Stop Rules v5.20

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A CHAIN-SCHEMA PASS / COST PREFLIGHT SELF-TEST NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.19.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A source/schema state

D0 source/archive metadata:

`B14A_D0_V08_SOURCE_ARCHIVE_METADATA_PASS`

FUTURES-chain body/schema:

`B14A_FUTURESCHAIN_BODY_SCHEMA_PASS`

Exact 12-expiry identity freeze:

complete.

## 3. Edge-to-Fill card

Binding:

`docs/research/sc001-b14a-edge-to-fill-card-v0.1.md`

Known preliminary structural burden before hedge funding:

- 3 taker fills = 15 bps;
- expiry settlement fee = 1 bp;
- spread/depth reserve = 10 bps;
- execution/model reserve = 10 bps.

Subtotal:

`36 bps + funding_reference`

## 4. Funding cost preflight

Protocol:

`docs/research/sc001-b14a-hedge-funding-settlement-cost-preflight-v0.1.md`

Runner:

`research/sc001/sc001_b14a_cost_preflight_v0_1.py`

Freeze:

`docs/research/sc001-b14a-cost-preflight-implementation-freeze-v0.1.json`

Registry:

`docs/research/sc001-contamination-registry-v0.28.json`

## 5. Frozen calibration

Instruments:

- BTC-USD-SWAP;
- ETH-USD-SWAP.

Window:

`2026-06-01 <= funding_time < 2026-09-01 UTC`

Funding reserve:

max of BTC/ETH p99 absolute funding, rounded up to whole bp, minimum 1 bp.

Final structural burden:

`36 + funding_reserve_bps`

Headroom hurdle:

`5 * ceil((final_structural_burden_bps + 10) / 5)`

This rule is frozen before any B14-A basis value is opened.

## 6. Firewalls

Cost preflight may access only:

- funding rates;
- funding timestamps;
- static cost arithmetic.

Still no:

- FUTURES/SWAP prices;
- basis;
- returns;
- settlePx;
- delivery price;
- convergence;
- signal;
- execution/PnL;
- candidate ID.

## 7. Immediate next action

Run B14-A cost-preflight self-test only.

If PASS, run the funding-only cost preflight.

No basis outcome is authorized yet.
