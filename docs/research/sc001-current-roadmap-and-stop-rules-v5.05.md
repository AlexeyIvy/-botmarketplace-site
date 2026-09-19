# SC001 Current Roadmap and Stop Rules v5.05

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A PRODUCT SEMANTICS PASS / OFFICIAL FUTURES ARCHIVE TRANSPORT V0.4 FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.04.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A v0.3 D0 result

Observed:

`B14A_D0_V03_SOURCE_ARCHIVE_METADATA_REVIEW`

But product semantics passed:

- BTC-USD future contracts = 6;
- ETH-USD future contracts = 6;
- BTC-USD-SWAP hedge = PASS;
- ETH-USD-SWAP hedge = PASS.

Only archive metadata probe breadth failed:

- BTC = 0;
- ETH = 0.

No price outcome was opened.

## 3. Source-transport diagnosis

v0.3 used the C11-style private resolver with family-level FUTURES query.

This transport was never independently qualified for dated FUTURES.

SC001 previously qualified the public historical endpoint:

`GET /api/v5/public/market-data-history`

with exact `instIdList`.

## 4. B14-A v0.4

Protocol:

`docs/research/sc001-b14a-d0-dated-futures-source-archive-metadata-protocol-v0.3.md`

Runner:

`research/sc001/sc001_b14a_d0_dated_futures_source_archive_metadata_v0_4.py`

Freeze:

`docs/research/sc001-b14a-d0-implementation-freeze-v0.4.json`

## 5. Exact archive metadata request

For each FUTURES contract:

- module = 1;
- instType = FUTURES;
- dateAggrType = 1D;
- exact probe begin/end;
- exact instIdList = expiry contract ID.

No body GET/open.

## 6. Firewalls

No:

- trade body access;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution;
- PnL;
- candidate ID.

## 7. Immediate next action

Run B14-A D0 v0.4 self-test.

If PASS, run metadata-only v0.4 once.

Do not interpret partial contract output.
