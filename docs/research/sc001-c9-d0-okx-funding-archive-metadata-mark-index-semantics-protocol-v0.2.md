# SC001 — C9-D0 OKX Funding Archive Metadata / Mark-Index Semantics Protocol v0.2

Date: 2026-09-18
Status: **FROZEN DATA-ONLY SOURCE-TRANSPORT REPAIR AFTER V0.1 REVIEW / NO ALPHA AUTHORIZED**
Scope: `SCALPING RESEARCH / SC001`
Supersedes: `sc001-c9-d0-okx-funding-mark-index-data-semantics-protocol-v0.1.md`

## 1. Trigger for v0.2

C9-D0 v0.1 completed fail-closed with:

`C9_D0_DATA_SEMANTICS_REVIEW`

Observed pattern:

- mark 4H coverage: complete;
- index 4H coverage: complete;
- mark/index alignment: complete;
- funding rows from `/api/v5/public/funding-rate-history`: zero for all 2024 probe windows.

This is a source-transport limitation, not C9 research evidence.

OKX's current public funding-rate-history REST endpoint returns at most recent history (official API documentation states up to approximately the last three months), while deeper funding history is published through the official historical market-data download service.

SC001 already encountered the same transport issue in E002 and repaired it prospectively by using:

`GET /api/v5/public/market-data-history`

with funding module `3` and monthly archives.

No C9 return, signal, threshold, event window, strategy PnL or promotional alpha was calculated before this repair.

## 2. Protected-data implication

Historical funding bulk files are monthly.

A July 2024 monthly funding archive necessarily contains timestamps beyond the already contaminated July 1-14 C9-D0 probe window, including the SC001 July 16-30 protected gap.

Therefore C9-D0 v0.2 MUST NOT download or open the historical funding archive body.

It may inspect only:

- historical archive metadata returned by OKX;
- trusted archive URL identity;
- HTTP HEAD / Content-Length;
- filename / source metadata.

Historical funding values and interval reconstruction are deferred.

## 3. Public sources

### Instrument metadata

`GET /api/v5/public/instruments`

Use exact SWAP identity and `uly`.

### Historical funding archive metadata

`GET /api/v5/public/market-data-history`

Frozen parameters:

- `module=3` (FundingRate);
- `instType=SWAP`;
- `instFamilyList=<uly>`;
- `dateAggrType=monthly`.

Query only monthly archive metadata corresponding to:

- July 2024;
- September 2024.

No archive body GET is authorized.

Trusted historical archive URL:

- HTTPS only;
- final/declared host exactly `static.okx.com`;
- URL basename equals returned filename;
- Content-Length must be finite and >0.

### Historical mark/index candles

Continue using:

- `/api/v5/market/history-mark-price-candles`;
- `/api/v5/market/history-index-candles`.

Use 4H bars for schema/timestamp coverage only.

## 4. Probe universe

Exactly:

- BTC-USDT-SWAP;
- ETH-USDT-SWAP;
- DOGE-USDT-SWAP;
- ORDI-USDT-SWAP;
- UNI-USDT-SWAP;
- XRP-USDT-SWAP;
- OP-USDT-SWAP;
- BCH-USDT-SWAP.

This is a source/data-semantic probe universe, not a final C9 alpha universe.

## 5. Historical metadata probe months

Archive metadata windows follow OKX monthly UTC+8 archive boundaries.

July archive query:

- begin = 2024-07-01 00:00 UTC+8;
- end = 2024-08-01 00:00 UTC+8.

September archive query:

- begin = 2024-09-01 00:00 UTC+8;
- end = 2024-10-01 00:00 UTC+8.

These queries may reveal file metadata for a full month, but no funding body may be downloaded/opened.

## 6. Mark/index probe dates

Retain only already contaminated performance windows:

- 2024-07-01..2024-07-14;
- 2024-09-01..2024-09-14.

For each asset/window:

- expected 4H grid count = 84;
- minimum admitted mark rows = 80;
- minimum admitted index rows = 80;
- minimum exact mark/index timestamp overlap = 80;
- confirmed bars only;
- UTC 4H alignment required;
- OHLC numeric positivity checked but values are not stored in the report.

## 7. Funding metadata PASS semantics

For each asset and each month require:

- official OKX response code 0;
- at least one unique trusted funding archive file node;
- no conflicting URLs for the same filename;
- each archive URL on `static.okx.com`;
- HEAD status 200;
- trusted final URL identity;
- positive Content-Length.

D0 v0.2 does NOT claim:

- historical funding row count;
- historical funding interval;
- historical funding method/formulaType;
- historical funding-rate distribution.

Those require body access and belong to a separately governed later stage.

## 8. Exact terminal states

PASS:

`C9_D0_V02_DATA_SEMANTICS_PASS`

REVIEW:

`C9_D0_V02_DATA_SEMANTICS_REVIEW`

REVIEW remains data/source state only, not a strategy verdict.

## 9. Hard firewalls

Report must state false:

- historical_funding_body_downloaded;
- historical_funding_body_opened;
- funding_values_used_for_strategy;
- mark_index_prices_used_for_strategy;
- returns_calculated;
- basis_transition_calculated;
- strategy_signal_calculated;
- sentinel_outcome_calculated;
- pnl_calculated;
- direction_selected;
- threshold_selected;
- event_window_selected;
- protected_market_body_accessed;
- promotional_alpha_accessed.

## 10. Consequence of PASS

C9-D0 v0.2 PASS means:

- old funding archives exist through the official OKX source;
- mark/index historical timestamp coverage is usable;
- source transport is feasible.

It does NOT authorize opening July/September funding bodies.

Before a C9 funding-value/state-transition stage:

1. prospectively select one or more **entire calendar months** that are not protected;
2. update the contamination registry before body access;
3. label the entire selected month(s) `NONPROMOTIONAL_SELECTION_CALIBRATION`;
4. freeze archive acquisition/integrity protocol;
5. only then inspect historical funding values/intervals and design any C9 outcome-bearing sentinel.

No direction, threshold, event window or execution architecture is selected by D0.
