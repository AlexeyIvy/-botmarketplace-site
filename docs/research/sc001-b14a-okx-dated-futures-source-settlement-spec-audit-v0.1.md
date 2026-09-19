# SC001 — B14-A OKX Dated-Futures Source / Settlement Specification Audit v0.1

Date: 2026-09-19
Status: **SOURCE-SPEC FEASIBILITY PASS / ARCHIVE METADATA PROBE REQUIRED BEFORE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-parallel-independent-base-mechanism-pool-v0.1.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`;
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`.

## 1. Mechanism

B14-A studies standard crypto dated futures near deterministic final delivery.

Core structural anchor:

`FUTURES contract -> natural delivery at expTime -> exchange settlement/delivery price`

No ordinary mean-reversion assumption is required for the existence of the terminal anchor.

## 2. Instrument identity source

Official OKX instruments API exposes, for FUTURES:

- `instId`;
- `instFamily`;
- `listTime`;
- `expTime`;
- `settleCcy`;
- `ctVal`;
- `ctMult`;
- `ctValCcy`;
- `ctType`;
- `state`;
- `ruleType`;
- `futureSettlement`;
- `instCategory`.

For FUTURES, `expTime` is the natural delivery time.

Do not infer expiry from alias.

## 3. Product admission

For the first B14-A source program admit only:

- instType = FUTURES;
- ruleType = normal;
- instCategory = 1 (crypto);
- ctType = linear;
- settleCcy = USDT;
- instFamily in {BTC-USDT, ETH-USDT};
- positive listTime/expTime;
- expTime > listTime.

Exclude:

- pre_market;
- xperp;
- equity/stock;
- commodity;
- forex;
- bond futures.

## 4. Settlement anchor source

Official OKX public estimated-price endpoint/channel exposes `settlePx` for FUTURES.

REST estimated price is available only in the final 30 minutes before delivery.

The public estimated-price channel documents approximately 200 ms updates based on the delivery/settlement estimation process.

For B14-A, this official `settlePx` is the preferred causal settlement-anchor source.

Do not reconstruct a private settlement formula from trade prices.

## 5. Documentation discrepancy

Some current OKX help pages describe final settlement using a 30-minute index average, while other official expiry-futures pages describe a final-hour average.

Because B14-A can consume official `settlePx` directly during the final 30 minutes, the strategy need not infer the averaging formula.

The exact documentation discrepancy must remain recorded.

No custom averaging window may be selected from outcomes.

## 6. Final delivery source

OKX public API exposes:

`GET /api/v5/public/delivery-exercise-history`

for FUTURES delivery records, including:

- delivery timestamp;
- contract ID;
- delivery price.

This may be used only in a later authorized outcome/reconciliation stage.

D0 does not call or inspect delivery prices.

## 7. Fee/source economics

Current OKX fee documentation states:

- expiry settlement fee = 0.01% for all tiers.

For a later structural card, minimum explicit fees must include:

- futures entry trading fee;
- hedge entry trading fee;
- hedge exit trading fee;
- expiry settlement fee.

No claim that settlement is free is allowed.

## 8. Daily settlement distinction

OKX also has a daily settlement mechanism for some expiry futures under cross margin.

Daily settlement is distinct from final delivery and does not occur on the delivery date under the documented daily-settlement mechanism.

B14-A's target horizon is the final pre-delivery window only.

## 9. Historical/source availability

OKX advertises tick-level historical trade data from September 2021 onward.

Before any historical B14-A price access, D0 must explicitly verify that the official historical market-data service returns exact FUTURES trade archives for admitted standard contracts.

No assumption that SWAP archive behavior automatically applies to FUTURES.

## 10. Hedge/reference

Preferred first hedge/reference family:

same-underlying OKX USDT perpetual SWAP.

Reason:

- same venue;
- same USDT settlement family;
- avoids cross-venue ticker/underlying ambiguity;
- existing SC001 SWAP trade-source infrastructure is qualified.

Exact contract-unit normalization must still be frozen.

## 11. Source-spec disposition

`B14A_SOURCE_SPEC_FEASIBILITY_PASS_PENDING_D0_ARCHIVE_METADATA`

This is not a strategy or headroom PASS.

## 12. Immediate next action

Run metadata-only B14-A D0 to:

1. enumerate standard BTC-USDT / ETH-USDT expiry futures;
2. validate contract semantic fields;
3. freeze future expTime identities;
4. verify exact FUTURES trade-archive metadata/HEAD on a completed recent day for eligible listed contracts;
5. verify same-family SWAP identity exists.

No trade body, basis, settlePx value, return or PnL is authorized.
