# SC001 — B14-A D0 Dated-Futures Source / Archive Metadata Protocol v0.3

Date: 2026-09-19
Status: **FROZEN OFFICIAL-HISTORICAL-ENDPOINT AMENDMENT / METADATA-ONLY**
Scope: `SCALPING RESEARCH / SC001`
Supersedes archive-transport semantics from:
`docs/research/sc001-b14a-d0-dated-futures-source-archive-metadata-protocol-v0.2.md`

Parents:

- `docs/research/sc001-b14a-d0-v0.3-archive-metadata-transport-review-v0.1.md`;
- `docs/research/sc001-b14a-d0-v0.1-source-review-result.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`.

## 1. Product scope unchanged

Venue:

`OKX`

Families:

- BTC-USD;
- ETH-USD.

Standard crypto-margined inverse expiry futures only.

Same-venue hedges:

- BTC-USD-SWAP;
- ETH-USD-SWAP.

## 2. Official archive metadata transport

Use only:

`GET /api/v5/public/market-data-history`

For each exact expiry contract probe:

- module = `1`;
- instType = `FUTURES`;
- dateAggrType = `1D`;
- begin = exact probe-day UTC start ms;
- end = exact next-day UTC start ms;
- instIdList = exact expiry `instId`.

Do not use the prior C11-specific `/priapi/.../download-link` resolver for B14-A FUTURES.

## 3. Metadata extraction

Recursively walk the returned response.

Admit an archive node only when:

- filename/fileName exists;
- URL field exists as url/fileUrl/downloadUrl;
- filename equals:
  `INSTID-trades-YYYY-MM-DD.zip`;
- HTTPS;
- final archive host = `static.okx.com`;
- URL basename exactly equals filename.

Multiple distinct exact URLs => REVIEW.

No inferred filename.

## 4. HEAD gate

For exact archive candidate require:

- HTTP 200;
- trusted final host;
- exact basename;
- positive numeric Content-Length.

No body GET/open.

## 5. Product semantic gates unchanged

Require:

- FUTURES;
- ruleType normal;
- instCategory 1;
- inverse;
- BTC settleCcy BTC / ETH settleCcy ETH;
- ctValCcy USD;
- future expTime;
- state live/preopen;
- expTime > listTime.

## 6. D0 PASS

Exact PASS:

`B14A_D0_V04_SOURCE_ARCHIVE_METADATA_PASS`

requires:

- >=2 future BTC-USD standard crypto-margined expiry contracts;
- >=2 future ETH-USD standard crypto-margined expiry contracts;
- BTC-USD-SWAP hedge PASS;
- ETH-USD-SWAP hedge PASS;
- >=1 exact FUTURES archive metadata/HEAD PASS per family.

Otherwise:

`B14A_D0_V04_SOURCE_ARCHIVE_METADATA_REVIEW`

## 7. Firewalls

Must remain false:

- futures trade body downloaded/opened;
- swap trade body opened;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution/PnL;
- candidate ID.

## 8. Consequence

PASS authorizes only exact future expiry identity freeze and structural-card design.

No price outcome.
