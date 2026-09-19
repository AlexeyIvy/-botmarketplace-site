# SC001 Current Roadmap and Stop Rules v5.02

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A USDT EXPIRY FAMILY DISCONTINUED / V0.2 CRYPTO-MARGINED D0 FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.01.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A v0.1 source state

Observed:

`B14A_D0_SOURCE_ARCHIVE_METADATA_REVIEW`

Reason:

`SOURCE_PRODUCT_FAMILY_DISCONTINUED`

Official OKX discontinued BTC/USDT- and ETH/USDT-margined expiry futures; final contracts expired 2026-06-26.

No price outcome was opened.

## 3. B14-A v0.2 target

Retarget metadata-only D0 to standard crypto-margined inverse expiry futures:

- BTC-USD;
- ETH-USD.

Same-venue hedges:

- BTC-USD-SWAP;
- ETH-USD-SWAP.

## 4. Product semantics

Require:

- instType FUTURES;
- ruleType normal;
- instCategory 1;
- ctType inverse;
- ctValCcy USD;
- BTC-USD settles in BTC;
- ETH-USD settles in ETH;
- future expTime;
- state live/preopen.

## 5. D0 firewalls

Still no:

- trade body GET/open;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution;
- PnL.

## 6. Next action

Run B14-A v0.2 self-test.

Only after self-test PASS run metadata-only D0 v0.2.
