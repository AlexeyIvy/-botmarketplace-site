# SC001 Current Roadmap and Stop Rules v5.12

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A V0.6 ENDPOINT LIVE / FUTURES ARCHIVE METADATA SHAPE DIAGNOSTIC NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.11.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A v0.6 state

Exact state:

`B14A_D0_V06_SOURCE_ARCHIVE_METADATA_REVIEW`

Product/hedge semantics remain PASS.

Historical endpoint requests now complete without HTTP errors.

Exact expected archive names remain unresolved.

## 3. Current diagnosis

Remaining layer:

`FUTURES archive metadata naming / response shape`

Do not change transport parameters or filename assumptions again before inspecting the actual returned metadata nodes.

## 4. Immediate next action

Run metadata-only FUTURES response inventory for:

- BTC-USD;
- ETH-USD;
- 2026-09-16;
- 2026-09-15.

No URL is followed.

No archive body or price field is opened.

## 5. Firewalls

Remain closed:

- trade body download/open;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution;
- PnL;
- candidate ID.
