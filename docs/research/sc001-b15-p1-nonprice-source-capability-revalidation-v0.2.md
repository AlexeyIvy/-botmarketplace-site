# SC001 — B15-P1 Collector Live Read-Only Source Capability Revalidation v0.2

Date: 2026-09-24  
Status: **API-COMPATIBILITY HARDENED / LIVE RETRY NOT YET AUTHORIZED**  
Supersedes: `sc001-b15-p1-nonprice-source-capability-revalidation-v0.1.md`

## 1. Trigger

The first live v0.1 probe reached authenticated OKX `GET /api/v5/asset/currencies` and failed because `feeCcy` was incorrectly required on every returned row.

Observed:

`OKX currencies schema missing required fields in 591 rows`

No collector launch, price or PnL occurred.

## 2. Purpose

Revalidate the dedicated B15 read-only source access against the current API schemas and generate the exact secret-free capability snapshot required by collector v0.1.3.

## 3. Frozen implementation anchors

Collector runner v0.1.3 SHA256:

`f8181c4f25d6fc842d13c1faf8e259756883fcbb0bbcf08c23b3e60c9ed7bce0`

Collector implementation freeze v0.1.3 SHA256:

`cdc6654ce5bbf265ce5cc5af2e448806ba306292d29fb986c7eb78bb1379df96`

Final route graph SHA256:

`06a9edd309a002aa5dc8408d992cff7b774604fc1cfb04f90fd7f56333f27928`

## 4. Permission gate

Bybit:
- readOnly = 1;
- no Withdraw permission token;
- IP binding required.

OKX:
- permission exactly read_only;
- IP binding required.

## 5. Allowed endpoints

Public non-price:
- Bybit server time;
- Bybit Spot instrument metadata;
- OKX server time;
- OKX public Spot instrument metadata.

Authenticated read-only:
- Bybit query-api permissions;
- Bybit coin-info;
- Bybit one exact account fee-rate probe;
- OKX account config;
- OKX currencies;
- OKX one exact trade-fee probe.

No ticker/orderbook/candle/order/transfer/withdrawal endpoint.

## 6. OKX Get currencies schema policy

Core required on every row:

- ccy;
- chain;
- ctAddr;
- canDep;
- canWd.

Profile per-row economic fields:

- fee;
- feeCcy;
- burningFeeRate;
- minDep;
- minWd;
- maxWd;
- wdTickSz;
- minDepArrivalConfirm;
- minWdUnlockConfirm.

`feeCcy` is not mandatory.

The capability probe reports presence counts and one of:

- `NONE`;
- `PARTIAL`;
- `ALL`.

Economic completeness requires at least one row with:

- fee;
- burningFeeRate;
- minDep;
- minWd;
- wdTickSz;
- minDepArrivalConfirm;
- minWdUnlockConfirm.

Missing economic metadata on some rows does not invalidate the entire endpoint; the collector later fails closed per affected row.

## 7. Bybit Spot pair discovery

Use:

`GET /v5/market/instruments-info?category=spot`

No cursor/limit pagination.

Qualification:
- quoteCoin = USDT;
- status = Trading.

## 8. OKX Spot pair discovery

Use public `Get instruments` with `instType=SPOT`.

For every live USDT pair preserve:

- base asset;
- instId;
- groupId when returned.

Frozen asset universe is not modified by pair availability.

## 9. OKX fee probe

Call:

`GET /api/v5/account/trade-fee?instType=SPOT&instId=<exact pair>`

Primary parser:

`feeGroup[]`

If instrument `groupId` is available, select exactly one matching feeGroup.

If groupId is unavailable but exactly one feeGroup exists, use it.

If multiple feeGroup rows are ambiguous, REVIEW.

Deprecated top-level taker/maker are accepted only as explicit compatibility fallback when feeGroup is absent.

## 10. Capability snapshot v0.2

Retain pair lists:

- `qualified_pairs.BYBIT`;
- `qualified_pairs.OKX`.

Add:

`qualified_pair_metadata.OKX[instId].groupId`

so collector v0.1.3 can resolve current feeGroup semantics without price data.

## 11. Clock and transport

IPv4-only process-local DNS.

Absolute server clock skew <= 10,000 ms.

## 12. PASS

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS`

PASS still does not launch collector.

## 13. REVIEW

Any permission, IP-binding, core schema, source auth, clock skew, pair qualification, feeGroup ambiguity, hash-anchor or firewall violation:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_REVIEW`

Then STOP.

## 14. Price firewall

Always false:
- price_data_used;
- pnl_data_used;
- collector_launch_authorized;
- live_execution_authorized.
