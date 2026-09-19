# SC001 Current Roadmap and Stop Rules v5.21

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A COST SELF-TEST PASS / FUNDING-ONLY COST RUN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.20.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A current state

Source/archive metadata:

`B14A_D0_V08_SOURCE_ARCHIVE_METADATA_PASS`

FUTURES-chain body/schema:

`B14A_FUTURESCHAIN_BODY_SCHEMA_PASS`

Exact 12-expiry freeze:

complete.

Cost preflight self-test:

`B14A_COST_PREFLIGHT_SELF_TEST_PASS`

## 3. Frozen structural subtotal before funding

- 3 taker fills = 15 bps;
- expiry settlement fee = 1 bp;
- spread/depth reserve = 10 bps;
- execution/model reserve = 10 bps.

Subtotal:

`36 bps`

## 4. Funding-only run

Instruments:

- BTC-USD-SWAP;
- ETH-USD-SWAP.

Window:

`2026-06-01 <= funding_time < 2026-09-01 UTC`

Funding reserve rule:

`max(1, ceil(max(BTC p99 abs funding bps, ETH p99 abs funding bps)))`

Final structural burden:

`36 + funding_reserve_bps`

Headroom hurdle:

`5 * ceil((final_structural_burden_bps + 10) / 5)`

## 5. Allowed fields

Funding-only run may access:

- funding rate;
- funding timestamp;
- source/archive metadata;
- static cost arithmetic.

## 6. Hard firewalls

No:

- FUTURES/SWAP price;
- basis;
- returns;
- settlePx;
- delivery price;
- convergence;
- signal;
- execution/PnL;
- candidate ID.

## 7. Expected terminal states

- `B14A_COST_PREFLIGHT_PASS`;
- `B14A_COST_PREFLIGHT_REVIEW`.

## 8. Consequence of PASS

PASS freezes:

- funding reserve;
- final structural burden;
- final B14-A raw headroom hurdle.

Only after that may a price-bearing headroom protocol be designed.

No basis outcome is authorized by the cost preflight alone.

## 9. Immediate next action

Run the funding-only B14-A cost preflight once.
