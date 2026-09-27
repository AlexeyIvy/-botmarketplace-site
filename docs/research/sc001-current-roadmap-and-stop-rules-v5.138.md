# SC001 Current Roadmap and Stop Rules v5.138

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 price-anchor extractor self-test PASS / networked price-body access awaiting approval**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.137.md`

## B13-C extractor self-test

Runner job:

`job_20260927T080705Z_561e3c54`

PASS:

`B13C_S0_PRICE_ANCHOR_EXTRACTOR_V011_SELF_TEST_PASS`

Observed:
- canonical clusters = 1,905;
- canonical archives = 76;
- exit code = 0;
- package integrity = PASS;
- stderr empty;
- network calls = none;
- real price bodies = unopened;
- returns/PnL = CLOSED.

## Next boundary: first real price-body access

Binding launch contract:

`docs/research/sc001-b13c-s0-networked-price-anchor-extraction-launch-contract-v0.1.json`

Exact extractor:

`research/sc001/sc001_b13c_s0_streaming_price_anchor_extractor_v0_1_2.py`

SHA256:

`abb876276976198be65d049c6269d732dd24c5364c6c496bfeb5ed9d3f1f5be9`

Canonical cluster master SHA:

`0636ac25d6b7a484a4a9959f256aa57e0a1ead7f4e228423715f688b194fb87b`

Archive source:
- exact files = 76;
- HEAD PASS = 76/76;
- total compressed bytes = 2,633,144,445;
- sequential one-file processing;
- >=2 GiB disk reserve required in addition to current archive;
- archive deleted after successful extraction;
- resume via per-archive integrity ledger.

## This stage MAY

- open exact frozen Bybit historical trade archives;
- read price fields for source extraction;
- extract the exact frozen entry/exit 1-second anchor trades.

## This stage MUST NOT

- calculate return;
- calculate signed reversal;
- evaluate the 30 bps / 55% / 4-of-6 S0 gates;
- rank symbols;
- calculate PnL;
- change any cluster or bucket.

Only after extraction PASS and an immutable price-anchor dataset freeze will a separate offline outcome bundle be allowed to calculate the frozen S0 metric.

## Current next state

`AWAIT_EXPLICIT_APPROVAL_FOR_NETWORKED_B13C_S0_PRICE_ANCHOR_EXTRACTION`
