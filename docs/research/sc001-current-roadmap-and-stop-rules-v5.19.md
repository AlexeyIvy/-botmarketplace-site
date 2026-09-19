# SC001 Current Roadmap and Stop Rules v5.19

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A CHAIN-SCHEMA SELF-TEST PASS / ENGINEERING BODY QUALIFICATION NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.18.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A current state

D0 source/archive metadata:

`B14A_D0_V08_SOURCE_ARCHIVE_METADATA_PASS`

Exact 12-expiry identity freeze:

complete.

Body/schema self-test:

`B14A_CHAIN_SCHEMA_SELF_TEST_PASS`

## 3. Authorized body/schema run

Runner:

`research/sc001/sc001_b14a_futureschain_body_schema_v0_1.py --mode run`

Allowed archives only:

- BTC-USD-futureschain-trades-2026-09-16.zip;
- ETH-USD-futureschain-trades-2026-09-16.zip.

## 4. Allowed inspection

Allowed:

- ZIP CRC;
- CSV member names;
- exact header class;
- first column `instrument_name`;
- total non-empty row count;
- distinct dated-contract IDs;
- presence of BTC-USD-260925 and ETH-USD-260925.

## 5. Hard firewalls

Still forbidden:

- parsing/storing price values;
- basis;
- returns;
- settlePx/delivery price;
- convergence;
- strategy signal;
- execution;
- PnL;
- candidate-ID assignment.

## 6. Expected terminal states

- `B14A_FUTURESCHAIN_BODY_SCHEMA_PASS`;
- `B14A_FUTURESCHAIN_BODY_SCHEMA_REVIEW`.

## 7. Consequence of PASS

Only after PASS may we:

- finalize B14-A Edge-to-Fill structural card;
- freeze a later price-bearing headroom protocol.

PASS does not authorize price/basis/convergence output by itself.

## 8. Immediate next action

Run the exact two-archive engineering body/schema qualifier once.

Do not interpret partial per-family output.
