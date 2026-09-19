# SC001 Current Roadmap and Stop Rules v5.17

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A D0 SOURCE PASS / EXACT EXPIRY IDENTITY FREEZE NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.16.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A D0 PASS

Exact state:

`B14A_D0_V08_SOURCE_ARCHIVE_METADATA_PASS`

Binding result:

`docs/research/sc001-b14a-d0-v0.8-source-archive-metadata-pass-result.md`

Observed:

- 6 BTC-USD future contracts;
- 6 ETH-USD future contracts;
- both inverse SWAP hedge identities PASS;
- both family futureschain metadata/HEAD gates PASS.

## 3. Source identities

Historical family archives:

- `BTC-USD-futureschain-trades-2026-09-16.zip`;
- `ETH-USD-futureschain-trades-2026-09-16.zip`.

No body opened.

## 4. Exact-expiry freeze requirement

Before any futureschain body access, freeze from the canonical local v0.8 report:

- report SHA256;
- all 12 future expiry contract identities;
- instId;
- instFamily;
- listTime;
- expTime;
- state;
- ctVal;
- ctMult;
- ctValCcy;
- settleCcy;
- ctType;
- futureSettlement;
- groupId.

No contract may later be dropped because its basis/headroom looks weak.

## 5. Next body/schema stage

After exact identity freeze, design a metadata/body qualification stage that may inspect archive schema and contract identifiers but still may not calculate:

- basis;
- returns;
- settlePx convergence;
- strategy signal;
- execution;
- PnL.

## 6. Candidate-ID gate

B14-A remains:

`B14-A_NOT_YET_C13`

D0 PASS does not assign a candidate ID.

## 7. Immediate next action

Read the existing local v0.8 JSON only and output:

- SHA256;
- exact 12 future-expiry identities and semantic fields.

No network request or archive-body access is required.
