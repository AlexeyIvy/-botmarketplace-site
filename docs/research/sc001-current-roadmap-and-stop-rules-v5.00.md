# SC001 Current Roadmap and Stop Rules v5.00

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-C COLLECTION LIVE / B14-A D0 IMPLEMENTATION FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.99.md`

## 1. Protected prospective collection

B13-C collector remains live:

`B13C_COLLECTION_RUNNING`

Do not inspect protected liquidation outcomes for strategy design.

## 2. New active non-alpha branch

B14-A:

`DATED_FUTURES_FINAL_SETTLEMENT_CONVERGENCE`

Still pre-candidate:

`B14-A_NOT_YET_C13`

## 3. Source/specification audit

Binding:

`docs/research/sc001-b14a-okx-dated-futures-source-settlement-spec-audit-v0.1.md`

Key source facts:

- FUTURES instrument API provides natural `expTime`;
- contract denomination fields are available;
- standard-vs-pre-market identity is distinguishable;
- official `settlePx` estimate is available near delivery;
- expiry settlement fee must be included later;
- no historical price access yet.

## 4. D0 implementation

Protocol:

`docs/research/sc001-b14a-d0-dated-futures-source-archive-metadata-protocol-v0.1.md`

Runner:

`research/sc001/sc001_b14a_d0_dated_futures_source_archive_metadata_v0_1.py`

Freeze:

`docs/research/sc001-b14a-d0-implementation-freeze-v0.1.json`

## 5. D0 target

Metadata-only verify:

- >=2 future standard BTC-USDT expiry contracts;
- >=2 future standard ETH-USDT expiry contracts;
- BTC/ETH USDT SWAP hedge identities;
- >=1 exact FUTURES trade archive metadata/HEAD PASS per family.

## 6. Firewalls

D0 may not access:

- trade bodies;
- prices;
- basis;
- settlePx values;
- delivery prices;
- convergence;
- execution;
- PnL.

No candidate ID assignment.

## 7. Next action

1. run B14-A D0 self-test;
2. only if PASS, run metadata-only D0.

No price-bearing B14-A run is authorized.
