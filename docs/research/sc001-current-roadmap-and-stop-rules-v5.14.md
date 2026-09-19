# SC001 Current Roadmap and Stop Rules v5.14

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A FUTURESCHAIN SEMANTICS RESOLVED / V0.7 SELF-TEST NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.13.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A source semantics resolved

Metadata-shape diagnostic established that OKX historical FUTURES trade archives are family-level chain files.

Observed form:

`INSTFAMILY-futureschain-trades-YYYY-MM-DD.zip`

Example:

`ETH-USD-futureschain-trades-2026-09-16.zip`

This replaces the incorrect per-contract archive assumption.

## 3. B14-A v0.7

Protocol:

`docs/research/sc001-b14a-d0-dated-futures-source-archive-metadata-protocol-v0.6.md`

Runner:

`research/sc001/sc001_b14a_d0_dated_futures_source_archive_metadata_v0_7.py`

Freeze:

`docs/research/sc001-b14a-d0-implementation-freeze-v0.7.json`

## 4. D0 source gate

Require:

- >=2 eligible future BTC-USD contracts;
- >=2 eligible future ETH-USD contracts;
- BTC-USD-SWAP hedge PASS;
- ETH-USD-SWAP hedge PASS;
- exact BTC-USD futureschain archive metadata/HEAD PASS for D-3;
- exact ETH-USD futureschain archive metadata/HEAD PASS for D-3.

## 5. Separation of identities

Current instrument API remains authoritative for exact expiry-contract identities.

Historical archive source is family-level.

Any later body/schema stage must prove exact per-row contract attribution before price outcome.

## 6. Firewalls

No:

- futureschain body GET/open;
- trade rows;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution;
- PnL;
- candidate ID.

## 7. Immediate next action

Run B14-A D0 v0.7 self-test.

If PASS, run metadata-only v0.7 once.
