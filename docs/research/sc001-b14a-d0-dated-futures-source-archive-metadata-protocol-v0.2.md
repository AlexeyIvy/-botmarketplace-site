# SC001 — B14-A D0 Dated-Futures Source / Archive Metadata Protocol v0.2

Date: 2026-09-19
Status: **FROZEN PRODUCT-FAMILY AMENDMENT / METADATA-ONLY**
Scope: `SCALPING RESEARCH / SC001`
Supersedes v0.1 target-product semantics only.

Parents:

- `docs/research/sc001-b14a-d0-v0.1-source-review-result.md`;
- `docs/research/sc001-b14a-okx-dated-futures-source-settlement-spec-audit-v0.1.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`.

## 1. Reason for v0.2

BTC-USDT and ETH-USDT expiry futures were discontinued by OKX; their final contracts expired 2026-06-26.

Therefore v0.2 moves only the product family.

No economic threshold or price outcome is changed because none existed yet.

## 2. Exact source target

Venue:

`OKX`

Families:

- `BTC-USD`;
- `ETH-USD`.

Admit only standard crypto-margined expiry futures:

- instType = FUTURES;
- ruleType = normal;
- instCategory = 1;
- ctType = inverse;
- BTC-USD settleCcy = BTC;
- ETH-USD settleCcy = ETH;
- ctValCcy = USD;
- positive listTime;
- positive future expTime;
- state in {live, preopen};
- expTime > listTime.

Exclude:

- USDT-margined;
- USDC/USDG-margined USDⓈ expiry products;
- pre_market;
- xperp;
- equities/stocks;
- commodities;
- forex;
- bonds.

## 3. Hedge identity

Same-venue hedge:

- BTC-USD-SWAP;
- ETH-USD-SWAP.

Require:

- instType = SWAP;
- ctType = inverse;
- BTC settleCcy = BTC;
- ETH settleCcy = ETH;
- instCategory = 1;
- state = live.

## 4. Contract-unit compatibility

Before any future basis calculation, freeze exact normalization using:

- ctVal;
- ctMult;
- ctValCcy;
- inverse contract semantics.

D0 only records these fields.

No basis ratio or position sizing is calculated.

## 5. Expiry / delivery semantics

Use instrument API `expTime` as the natural delivery timestamp.

Official OKX expiry-futures documentation states crypto-margined BTCUSD/ETHUSD expiry futures remain supported and settle against the USD index.

Any later outcome stage must use official settlement/delivery source rather than an inferred terminal price.

## 6. Historical archive metadata probe

For each currently eligible future contract that has at least one completed UTC trading day:

- deterministically probe yesterday UTC;
- resolve exact FUTURES trade archive;
- require trusted static.okx.com URL;
- HEAD 200;
- positive Content-Length;
- no body GET/open.

## 7. PASS

`B14A_D0_V02_SOURCE_ARCHIVE_METADATA_PASS`

requires:

- >=2 future BTC-USD standard crypto-margined expiry contracts;
- >=2 future ETH-USD standard crypto-margined expiry contracts;
- both inverse SWAP hedge identities PASS;
- >=1 exact FUTURES trade archive metadata/HEAD PASS per family;
- all semantic fields valid.

Otherwise:

`B14A_D0_V02_SOURCE_ARCHIVE_METADATA_REVIEW`

## 8. Firewalls

Must remain false:

- futures trade body downloaded/opened;
- swap trade body opened;
- price accessed;
- basis calculated;
- settlePx accessed;
- delivery price accessed;
- convergence calculated;
- execution/PnL;
- candidate ID assigned.
