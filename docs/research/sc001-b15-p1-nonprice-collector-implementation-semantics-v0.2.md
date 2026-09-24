# SC001 — B15-P1 Non-Price Collector Implementation Semantics v0.2

Date: 2026-09-24  
Status: **IMPLEMENTATION-BINDING / PRE-LAUNCH**  
Supersedes: `sc001-b15-p1-nonprice-collector-implementation-semantics-v0.1.md`

## 1. Unchanged foundation

Frozen identity/route, Stage C cost model, 15-second cadence, storage policy, launch authorization and price firewall remain unchanged.

## 2. OKX Get currencies adapter

Endpoint:

`GET /api/v5/asset/currencies`

Core row fields that must exist for identity/state parsing:

- ccy;
- chain;
- ctAddr;
- canDep;
- canWd.

Economic fields are evaluated per row rather than requiring the entire endpoint response to be economically complete.

Required for an economically complete row:

- fee;
- burningFeeRate;
- minDep;
- minWd;
- wdTickSz;
- minDepArrivalConfirm;
- minWdUnlockConfirm.

`maxWd` is retained when available but is not a mandatory completeness field.

### feeCcy

`feeCcy` is optional for this endpoint adapter.

If present and non-empty, preserve it explicitly.

If absent/empty, classify fixed withdrawal fee currency as the withdrawn `ccy`:

`IMPLICIT_WITHDRAWAL_ASSET_GET_CURRENCIES`

This is explicit adapter semantics, not a silent zero/default.

### burningFeeRate

- key absent => percentage fee unknown, economic metadata incomplete;
- key present as empty string => zero burning fee;
- key present nonzero => `OKX_BURNING_FEE_FORMULA_REVIEW`.

Missing `burningFeeRate` must never become zero.

## 3. OKX trade-fee adapter

Endpoint:

`GET /api/v5/account/trade-fee`

Primary current schema:

`feeGroup[]`

Use public Spot instrument metadata `groupId` to select the exact feeGroup row.

Required selected feeGroup fields:

- groupId;
- taker;
- maker.

If `feeGroup[]` is absent but deprecated top-level `taker` and `maker` are still returned, accept them only as:

`DEPRECATED_TOP_LEVEL`

If multiple fee groups are present and groupId cannot disambiguate them:

`FEE_RATE_UNKNOWN`

No arbitrary first-row selection.

## 4. Capability snapshot extension

Capability snapshot retains existing pair lists and adds:

`qualified_pair_metadata.OKX[instId].groupId`

The collector remains backward-safe:
- pair lists remain explicit;
- groupId metadata is used when present;
- ambiguity remains fail-closed.

## 5. Bybit Spot instrument metadata

Spot instrument discovery is not paginated.

Use:

`GET /v5/market/instruments-info?category=spot`

without cursor/limit logic.

Qualification remains:

- quoteCoin = USDT;
- status = Trading.

## 6. No research rule change

This v0.2 implementation-semantics update changes API compatibility only.

Unchanged:
- admitted asset universe;
- canonical representations;
- route graph;
- route admission rules;
- 61/71 bps structural cost floors;
- price/PnL firewall;
- collector launch boundary.
