# SC001 Current Roadmap and Stop Rules v5.10

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A V0.6 SELF-TEST PASS / METADATA-ONLY D0 RUN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.09.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A current state

Product scope:

- BTC-USD standard crypto-margined inverse expiry futures;
- ETH-USD standard crypto-margined inverse expiry futures.

Hedges:

- BTC-USD-SWAP;
- ETH-USD-SWAP.

Self-test:

`B14A_D0_V06_SELF_TEST_PASS`

## 3. Next exact run

Execute:

`research/sc001/sc001_b14a_d0_dated_futures_source_archive_metadata_v0_6.py --mode run`

Possible D0 states:

- `B14A_D0_V06_SOURCE_ARCHIVE_METADATA_PASS`;
- `B14A_D0_V06_SOURCE_ARCHIVE_METADATA_REVIEW`.

## 4. D0 source gates

Require:

- >=2 future eligible BTC-USD expiry contracts;
- >=2 future eligible ETH-USD expiry contracts;
- both inverse SWAP hedges PASS;
- representative BTC FUTURES archive metadata/HEAD PASS;
- representative ETH FUTURES archive metadata/HEAD PASS.

Representative rule:

earliest-expiring currently live eligible contract per family, listed before the D-3 probe date.

## 5. Firewalls

No:

- FUTURES trade-body GET/open;
- SWAP trade-body access;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution;
- PnL;
- candidate-ID assignment.

## 6. Consequence of PASS

Only after D0 PASS may we:

- freeze exact future expiry identities;
- build the B14-A Edge-to-Fill structural card;
- design a later headroom sentinel.

No price-bearing B14-A outcome is authorized by D0 PASS alone.

## 7. Immediate next action

Run metadata-only B14-A D0 v0.6 once.

Do not interpret partial output.
