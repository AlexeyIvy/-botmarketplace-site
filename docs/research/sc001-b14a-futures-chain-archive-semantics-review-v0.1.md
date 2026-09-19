# SC001 — B14-A FUTURES Chain-Archive Semantics Review v0.1

Date: 2026-09-19
Status: **SOURCE SEMANTICS RESOLVED / NO MARKET BODY OPENED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b14a-futures-metadata-shape-diagnostic-protocol-v0.1.md`;
- `docs/research/sc001-b14a-d0-v0.6-exact-archive-unresolved-review-v0.1.md`.

## 1. Diagnostic result

The metadata-shape diagnostic completed successfully with:

- HTTP 200;
- API code 0;
- archive_body_accessed = false;
- price_accessed = false.

Observed FUTURES metadata nodes for ETH-USD include:

`ETH-USD-futureschain-trades-2026-09-16.zip`

and:

`ETH-USD-futureschain-trades-2026-09-15.zip`

hosted on:

`static.okx.com`

The metadata response identifies:

- instFamily = ETH-USD;
- instType = FUTURES;
- family-level groupDetails archive files.

## 2. Correct archive identity model

For OKX historical FUTURES trade module, the archive unit is not an individual expiry instrument.

The archive is a **family futures-chain daily archive**:

`INSTFAMILY-futureschain-trades-YYYY-MM-DD.zip`

Example:

`ETH-USD-futureschain-trades-2026-09-16.zip`

Therefore the prior expectation:

`INSTID-trades-YYYY-MM-DD.zip`

was incorrect for FUTURES.

## 3. Research implication

B14-A source feasibility should be separated into two layers:

### Instrument layer

Current instruments API freezes exact dated contracts:

- instId;
- listTime;
- expTime;
- contract semantics.

### Historical body layer

Historical trade source is family-level:

- BTC-USD futures chain;
- ETH-USD futures chain.

A later body/schema protocol must prove that individual trade rows can be attributed unambiguously to exact expiry `instId`.

No such body access is authorized by this review.

## 4. D0 correction

D0 archive source gate should require one exact family archive per family for the frozen probe date:

- `BTC-USD-futureschain-trades-D.zip`;
- `ETH-USD-futureschain-trades-D.zip`.

Require:

- exact metadata filename;
- trusted static.okx.com URL;
- HEAD 200;
- positive Content-Length.

Do not inspect archive members or trade rows.

## 5. No-change list

Unchanged:

- product families BTC-USD / ETH-USD;
- inverse crypto-margined expiry contracts;
- same-venue inverse SWAP hedges;
- D-3 source lag;
- daily aggregation;
- no price/basis/settlePx/deliveryPx/convergence/PnL.
