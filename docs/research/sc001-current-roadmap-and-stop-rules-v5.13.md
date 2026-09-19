# SC001 Current Roadmap and Stop Rules v5.13

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A FUTURES METADATA-SHAPE DIAGNOSTIC READY**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.12.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A current source state

Binding:

`B14A_D0_V06_SOURCE_ARCHIVE_METADATA_REVIEW`

Product semantics pass:

- 6 future BTC-USD expiry contracts;
- 6 future ETH-USD expiry contracts;
- both inverse SWAP hedges pass.

Historical endpoint requests complete without HTTP errors, but exact expected FUTURES archive filenames remain unresolved.

## 3. Diagnostic

Protocol:

`docs/research/sc001-b14a-futures-metadata-shape-diagnostic-protocol-v0.1.md`

Runner:

`research/sc001/sc001_b14a_futures_metadata_shape_diag_v0_1.py`

The diagnostic inspects only public metadata response structure for:

- BTC-USD;
- ETH-USD;
- 2026-09-16;
- 2026-09-15.

It records filenames/URL basenames/identity fields only.

## 4. Hard firewall

No:

- archive URL follow;
- HEAD;
- body GET/open;
- trade rows;
- prices;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution/PnL.

## 5. Immediate next action

Run the metadata-shape diagnostic once.

Do not modify B14-A resolver again until the actual returned metadata inventory is reviewed.
