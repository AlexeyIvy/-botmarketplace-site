# SC001 — C9-D1 September Funding Archive Acquisition / Integrity Protocol v0.1

Date: 2026-09-18  
Status: **FROZEN DATA-ONLY PROTOCOL — BODY ACCESS AUTHORIZED ONLY AFTER CONTAMINATION REGISTRY v0.6**  
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c9-d0-v0.2-data-semantics-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.6.json`;
- `docs/research/sc001-c9-d0-okx-funding-archive-metadata-mark-index-semantics-protocol-v0.2.md`.

## 1. Purpose

Acquire and qualify the exact OKX historical FundingRate bodies for the prospectively designated C9 Selection/Calibration source month.

This stage is still data engineering only.

It must not calculate:

- mark/index returns;
- basis transitions;
- strategy direction;
- funding threshold;
- event window;
- strategy signal;
- sentinel outcome;
- PnL.

## 2. Authorized source month

Only the OKX FundingRate archive month:

`2024-09 UTC+8`

is authorized.

Source-time interval:

`[2024-08-31T16:00:00Z, 2024-09-30T16:00:00Z)`

This source interval is permanently:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

for C9.

No July or October funding body may be downloaded or opened.

## 3. Authorized universe

Exactly eight OKX perpetual swaps:

- BTC-USDT-SWAP;
- ETH-USDT-SWAP;
- DOGE-USDT-SWAP;
- ORDI-USDT-SWAP;
- UNI-USDT-SWAP;
- XRP-USDT-SWAP;
- OP-USDT-SWAP;
- BCH-USDT-SWAP.

Use the exact current `uly` resolved in C9-D0 v0.2.

## 4. Required D0 parent

Local parent report:

`~/sc001_data/SC001_C9_D0_V02_DATA_SEMANTICS/sc001_c9_d0_v02_data_semantics_report_v0_1.json`

Require exact:

`C9_D0_V02_DATA_SEMANTICS_PASS`

and:

- assets passed = 8/8;
- historical funding bodies downloaded/opened = false;
- returns/basis-transition/signal/sentinel/PnL = false;
- direction/threshold/event-window selected = false;
- protected/promotional market body accessed = false.

D1 must re-query the same September archive metadata to obtain current trusted download URLs and compare filenames/Content-Length with the frozen D0 report before downloading.

## 5. Historical source identity

Metadata endpoint:

`GET /api/v5/public/market-data-history`

Parameters:

- `module=3`;
- `instType=SWAP`;
- `instFamilyList=<uly>`;
- `dateAggrType=monthly`;
- September 2024 UTC+8 source boundaries only.

Archive requirements:

- HTTPS;
- host exactly `static.okx.com`;
- URL basename equals filename;
- HEAD status 200;
- positive Content-Length;
- filename and Content-Length exactly match the C9-D0 v0.2 parent metadata for that asset/month.

No alternate month or venue substitution.

## 6. Acquisition integrity

For each admitted archive:

1. exact byte size;
2. SHA256 after download/reuse;
3. ZIP CRC;
4. regular CSV member(s) only;
5. target funding rows parse as:
   `instrument_name,funding_rate,funding_time`;
6. target instrument identity exact;
7. funding rate finite decimal;
8. funding timestamp positive Unix milliseconds.

Non-target rows may be ignored.

## 7. Funding timestamp integrity

For each target instrument combine all admitted September archive files.

Deduplicate identical funding timestamps only when the associated funding rate is identical.

Hard fail on conflicting duplicate values.

For the exact target instrument require:

- at least 80 unique funding timestamps;
- strictly increasing unique timestamps;
- every admitted target timestamp inside the authorized source interval;
- first target timestamp no more than 8 hours after source start;
- last target timestamp no more than 8 hours before source end;
- all consecutive intervals >0;
- maximum consecutive interval <=8 hours.

Record only:

- row count;
- first/last timestamp;
- distinct observed interval hours;
- archive identities.

Funding-rate values are validated but **not stored in the D1 report** and are not used for a strategy.

## 8. Data-volume safety

Per archive body cap:

`20 MiB`

Total D1 funding-body cap:

`200 MiB`

These are safety caps only, not research parameters.

## 9. Exact terminal states

PASS:

`C9_D1_FUNDING_ARCHIVE_INTEGRITY_PASS`

REVIEW:

`C9_D1_FUNDING_ARCHIVE_INTEGRITY_REVIEW`

REVIEW is a data/implementation state, not a C9 strategy FAIL.

## 10. Report firewalls

Must state false:

- mark_index_values_opened_for_c9_d1;
- funding_values_used_for_strategy;
- returns_calculated;
- basis_transition_calculated;
- strategy_signal_calculated;
- sentinel_outcome_calculated;
- pnl_calculated;
- direction_selected;
- threshold_selected;
- event_window_selected;
- july_funding_body_accessed;
- october_funding_body_accessed;
- protected_market_body_accessed;
- promotional_alpha_accessed.

## 11. Consequence of PASS

D1 PASS establishes only:

- exact September funding archive integrity;
- historical funding timestamp coverage;
- observed historical funding interval semantics.

It does not establish predictive value or economic headroom.

Only after D1 PASS may a separate C9 state-transition sentinel be designed and frozen using the already-declared nonpromotional calibration interval.
