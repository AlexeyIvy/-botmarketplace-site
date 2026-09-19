# SC001 Current Roadmap and Stop Rules v5.01

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A D0 SELF-TEST PASS / METADATA-ONLY RUN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.00.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Do not inspect protected liquidation outcomes for strategy design.

## 2. B14-A current state

B14-A remains pre-candidate:

`B14-A_NOT_YET_C13`

Self-test:

`B14A_D0_SELF_TEST_PASS`

Binding result:

`docs/research/sc001-b14a-d0-self-test-pass-result-v0.1.md`

## 3. Immediate D0 task

Run metadata-only:

`research/sc001/sc001_b14a_d0_dated_futures_source_archive_metadata_v0_1.py --mode run`

Expected research/source states:

- `B14A_D0_SOURCE_ARCHIVE_METADATA_PASS`;
- `B14A_D0_SOURCE_ARCHIVE_METADATA_REVIEW`.

## 4. D0 allowed fields

Allowed:

- FUTURES instrument identity;
- BTC/ETH family;
- listTime;
- expTime;
- state/ruleType/category;
- ctVal/ctMult/ctValCcy;
- settleCcy/ctType;
- SWAP hedge identity;
- FUTURES trade archive filename/HEAD Content-Length.

Forbidden:

- trade body GET/open;
- price;
- basis;
- settlePx value;
- delivery price;
- convergence;
- strategy signal;
- execution;
- PnL.

## 5. Consequence of PASS

PASS authorizes only:

- future expiry identity freeze;
- Edge-to-Fill structural card;
- later headroom protocol design.

No price-bearing B14-A run yet.

## 6. Immediate next action

Execute B14-A D0 metadata-only run.

Do not interpret partial contract output.
