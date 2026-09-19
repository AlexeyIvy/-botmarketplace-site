# SC001 Current Roadmap and Stop Rules v5.03

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A V0.2 HANDSHAKE REVIEW / V0.3 SELF-TEST NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.02.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A v0.2 self-test state

Observed:

`B14A_D0_V02_SELF_TEST_REVIEW`

Reason:

`ENGINEERING_PARENT_IDENTITY_KEY_MISMATCH`

The self-test stopped before any OKX API/source call.

No market/source outcome was opened by the failed self-test.

## 3. v0.3 implementation

Runner:

`research/sc001/sc001_b14a_d0_dated_futures_source_archive_metadata_v0_3.py`

Freeze:

`docs/research/sc001-b14a-d0-implementation-freeze-v0.3.json`

Protocol remains:

`docs/research/sc001-b14a-d0-dated-futures-source-archive-metadata-protocol-v0.2.md`

Product family remains:

- BTC-USD;
- ETH-USD;

with inverse same-venue SWAP hedges.

## 4. Exact repair

v0.3 checks the correct parent identity:

`source_review_git_blob_sha`

against:

`docs/research/sc001-b14a-d0-v0.1-source-review-result.md`

No economic/source target changed.

## 5. Firewalls unchanged

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

## 6. Immediate next action

Run B14-A D0 v0.3 self-test only.

If PASS, run metadata-only D0 v0.3.
