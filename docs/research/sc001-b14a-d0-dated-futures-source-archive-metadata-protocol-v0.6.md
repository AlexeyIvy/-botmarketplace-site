# SC001 — B14-A D0 Dated-Futures Source / Archive Metadata Protocol v0.6

Date: 2026-09-19
Status: **FROZEN FUTURES-CHAIN ARCHIVE SEMANTICS / METADATA-ONLY**
Scope: `SCALPING RESEARCH / SC001`
Supersedes archive-identity semantics from v0.5 only.

Parents:

- `docs/research/sc001-b14a-futures-chain-archive-semantics-review-v0.1.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`.

## 1. Product census

Enumerate current standard crypto-margined inverse expiry futures:

- BTC-USD;
- ETH-USD.

Require >=2 future eligible contracts per family.

Record exact dated-contract metadata only.

## 2. Hedge census

Require:

- BTC-USD-SWAP;
- ETH-USD-SWAP;

with the already frozen inverse crypto semantics.

## 3. Historical source unit

Historical FUTURES trade source is family-level.

Expected exact archive basename for probe date D:

- `BTC-USD-futureschain-trades-D.zip`;
- `ETH-USD-futureschain-trades-D.zip`.

Do not expect per-expiry-instId archives.

## 4. Metadata query

Use:

`GET /api/v5/public/market-data-history`

with:

- module = 1;
- instType = FUTURES;
- instFamilyList = exact family;
- dateAggrType = daily;
- query label-day D first;
- previous-day metadata window only if exact D archive is unresolved.

Probe date:

`UTC today - 3 days`.

## 5. Archive trust gate

For each family require exactly one trusted exact URL whose:

- scheme = HTTPS;
- host = static.okx.com;
- basename = exact expected futureschain archive.

Then HEAD require:

- HTTP 200;
- same trusted host;
- same exact basename;
- positive numeric Content-Length.

No body GET/open.

## 6. D0 PASS

Exact PASS:

`B14A_D0_V07_SOURCE_ARCHIVE_METADATA_PASS`

requires:

- >=2 eligible future BTC-USD contracts;
- >=2 eligible future ETH-USD contracts;
- both inverse SWAP hedges PASS;
- BTC-USD futureschain archive metadata/HEAD PASS;
- ETH-USD futureschain archive metadata/HEAD PASS.

Otherwise:

`B14A_D0_V07_SOURCE_ARCHIVE_METADATA_REVIEW`

## 7. Consequence of PASS

PASS authorizes only:

- exact future-expiry identity freeze;
- FUTURES chain-body/schema qualification design;
- Edge-to-Fill structural card.

It does not authorize price/basis/convergence outcome.

## 8. Firewalls

Remain false:

- futures chain body download/open;
- swap body open;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution/PnL;
- candidate ID.
