# SC001 Current Roadmap and Stop Rules v5.09

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A V0.5 SOURCE REVIEW / V0.6 FUTURES-FAMILY TRANSPORT FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.08.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A v0.5 state

Observed:

`B14A_D0_V05_SOURCE_ARCHIVE_METADATA_REVIEW`

No price outcome was opened.

Product semantics remain valid:

- BTC-USD future contracts exist;
- ETH-USD future contracts exist;
- both inverse SWAP hedges pass.

## 3. Historical API semantic correction

The historical market-data endpoint uses product-type-specific selectors.

For FUTURES/SWAP/OPTION:

`instFamilyList`

is required.

The prior v0.5 used SPOT-style `instIdList`.

Historical trade modules are also normally T+2, so yesterday is not a robust source-feasibility probe date.

## 4. v0.6 source probe

Protocol:

`docs/research/sc001-b14a-d0-dated-futures-source-archive-metadata-protocol-v0.5.md`

Runner:

`research/sc001/sc001_b14a_d0_dated_futures_source_archive_metadata_v0_6.py`

Freeze:

`docs/research/sc001-b14a-d0-implementation-freeze-v0.6.json`

## 5. Exact transport

- GET /api/v5/public/market-data-history;
- module=1;
- instType=FUTURES;
- instFamilyList = BTC-USD or ETH-USD;
- dateAggrType=daily;
- probe date = UTC today minus 3 days;
- label-day then previous-day metadata window;
- exact filename filtering;
- HEAD only.

## 6. Representative source check

Probe one deterministic contract per family:

earliest-expiring currently live eligible contract whose listTime is before probe date.

No price/liquidity/return selection.

## 7. Firewalls

No:

- archive body GET/open;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution;
- PnL;
- candidate ID.

## 8. Immediate next action

Run B14-A D0 v0.6 self-test.

If PASS, run metadata-only v0.6 once.
