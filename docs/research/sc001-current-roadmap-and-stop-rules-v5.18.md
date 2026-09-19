# SC001 Current Roadmap and Stop Rules v5.18

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A EXACT 12-EXPIRY FREEZE COMPLETE / CHAIN-SCHEMA SELF-TEST NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.17.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A D0 source state

Exact state:

`B14A_D0_V08_SOURCE_ARCHIVE_METADATA_PASS`

Canonical report SHA256:

`a7a36245ee668450960873e22f0ce515c95e6c990564fa8df4fedf97d6fbd5e8`

## 3. Exact future-expiry freeze

Binding:

`docs/research/sc001-b14a-exact-12-future-expiry-identity-freeze-v0.1.json`

Frozen:

- 6 BTC-USD future expiry contracts;
- 6 ETH-USD future expiry contracts;
- exact list/expiry times;
- contract value/settlement semantics;
- futureSettlement flags;
- groupId.

No contract may be dropped or replaced after later price outcome.

## 4. Historical body/schema stage

Protocol:

`docs/research/sc001-b14a-futureschain-body-schema-qualification-protocol-v0.1.md`

Runner:

`research/sc001/sc001_b14a_futureschain_body_schema_v0_1.py`

Freeze:

`docs/research/sc001-b14a-futureschain-body-schema-implementation-freeze-v0.1.json`

Registry:

`docs/research/sc001-contamination-registry-v0.27.json`

## 5. Authorized bodies

Exactly:

- BTC-USD-futureschain-trades-2026-09-16.zip;
- ETH-USD-futureschain-trades-2026-09-16.zip.

This is engineering source qualification only.

## 6. Allowed parsing

Allowed:

- ZIP/CSV integrity;
- header class;
- first-column instrument_name;
- total row count;
- distinct dated-contract IDs;
- target 260925 contract presence.

Forbidden:

- parsing/storing price values;
- basis;
- returns;
- settlePx/delivery price;
- convergence;
- execution/PnL;
- candidate ID.

## 7. Next action

Run:

`--mode self-test`

Expected:

`B14A_CHAIN_SCHEMA_SELF_TEST_PASS`

Only after PASS may the two chain archives be opened under `--mode run`.

## 8. Consequence of body/schema PASS

A body/schema PASS will authorize:

- B14-A Edge-to-Fill structural card;
- later price-bearing headroom protocol design.

It will not itself authorize price/basis/convergence output.
