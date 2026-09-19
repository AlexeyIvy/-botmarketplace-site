# SC001 Current Roadmap and Stop Rules v5.15

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A V0.7 HANDSHAKE REVIEW / V0.8 SELF-TEST NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.14.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A v0.7 self-test state

Observed:

`B14A_D0_V07_SELF_TEST_REVIEW`

Reason:

`ENGINEERING_PARENT_CHAIN_HANDSHAKE_MISMATCH`

The self-test stopped before any OKX API call.

No source or market outcome was opened.

## 3. v0.8 implementation

Runner:

`research/sc001/sc001_b14a_d0_dated_futures_source_archive_metadata_v0_8.py`

Freeze:

`docs/research/sc001-b14a-d0-implementation-freeze-v0.8.json`

Protocol remains:

`docs/research/sc001-b14a-d0-dated-futures-source-archive-metadata-protocol-v0.6.md`

## 4. Parent chain now explicit

Both runner and freeze verify the same parent set:

- product-family source review;
- FUTURES selector/T+2 availability review;
- futureschain archive semantics review;
- v0.7 handshake review;
- current protocol;
- runner identity.

## 5. Source logic unchanged

Still frozen:

- BTC-USD / ETH-USD inverse expiry futures;
- BTC-USD-SWAP / ETH-USD-SWAP hedges;
- FUTURES family archive identity:
  `INSTFAMILY-futureschain-trades-YYYY-MM-DD.zip`;
- D-3 probe lag;
- metadata-only archive check.

## 6. Firewalls unchanged

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

Run B14-A D0 v0.8 self-test only.

If PASS, run metadata-only v0.8.
