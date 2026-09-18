# SC001 — C11 v2 Selection/Calibration Metadata Preflight Protocol v0.1

Date: 2026-09-19
Status: **FROZEN METADATA-ONLY DESIGN / NO C11 V2 PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.73.md`;
- `docs/research/sc001-c11-v2-chronology-freeze-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.19.json`;
- `docs/research/sc001-c11-d0-source-calendar-pass-result-v0.1.md`.

## 1. Purpose

Verify source/calendar/archive availability for the exact frozen 24-event C11 v2 Selection/Calibration chronology before any historical BTC trade body is opened.

This stage is metadata-only.

## 2. Exact target set

Use exactly the 24 Selection/Calibration releases frozen in:

`docs/research/sc001-c11-v2-chronology-freeze-v0.1.md`

Counts:

- CPI = 12;
- Employment Situation = 12;
- total = 24.

No event may be added, removed, replaced or shifted because of BTC movement, archive size or expected strategy quality.

## 3. Official calendar source

Primary source:

`https://www.bls.gov/schedule/YYYY/MM_sched_list.htm`

For every event require the official BLS schedule page to contain:

- exact frozen release calendar date;
- correct release family;
- 08:30 AM publication time.

For the February 2026 revised dates, current official BLS calendar/revised-release records are authoritative.

Do not access:

- release value;
- consensus;
- surprise;
- revision magnitude;
- article/news interpretation.

## 4. Historical BTC archive metadata

Instrument:

`BTC-USDT-SWAP`

For each frozen event date resolve exactly:

`BTC-USDT-SWAP-trades-YYYY-MM-DD.zip`

through the already-qualified OKX historical module-1 SWAP resolver.

Require:

- exact filename;
- trusted final static host `static.okx.com`;
- HTTPS;
- unique exact match;
- HEAD status 200;
- positive numeric Content-Length.

No archive body GET/open is authorized.

## 5. PASS

Exact PASS token:

`C11_V2_SC_METADATA_PREFLIGHT_PASS`

requires:

- 24/24 official BLS calendar checks PASS;
- 24/24 exact OKX archive identities resolve uniquely;
- 24/24 HEAD checks return positive Content-Length;
- family counts remain 12 CPI / 12 Employment;
- all price/signal/PnL firewalls remain false.

## 6. REVIEW

Exact REVIEW token:

`C11_V2_SC_METADATA_PREFLIGHT_REVIEW`

Any of the following must REVIEW/fail closed:

- missing or ambiguous BLS schedule identity;
- unexpected BLS host;
- exact archive missing;
- multiple exact archive URLs;
- untrusted final archive host/path;
- failed/non-positive HEAD;
- event count mismatch;
- implementation/freeze identity mismatch.

No substitute date may be chosen automatically.

## 7. Mandatory firewalls

The final report must explicitly keep false:

- historical_trade_body_downloaded;
- historical_trade_body_opened;
- macro_release_value_accessed;
- macro_surprise_calculated;
- first_impulse_calculated;
- residual_post_decision_move_calculated;
- direction_signal_calculated;
- continuation_outcome_calculated;
- execution_model_calculated;
- pnl_calculated;
- confirmation_outcome_accessed;
- promotional_alpha_accessed.

## 8. Output

Write one JSON report:

`~/sc001_data/SC001_C11_V2_SC_METADATA/sc001_c11_v2_sc_metadata_preflight_report_v0_1.json`

Report at minimum:

- stage/version/status;
- exact event rows;
- BLS check result per event;
- exact archive filename per event;
- archive Content-Length per event;
- total verified events;
- CPI/Employment counts;
- all firewalls.

No aggregate return, price move, first impulse or direction statistic is allowed.

## 9. Consequence of PASS

PASS authorizes only the next design freeze:

- Direction Rule v2;
- Stage A residual-headroom metric/gates;
- Stage B opportunity-retention/family-breadth/signed-continuation gates;
- report semantics.

PASS does **not** itself authorize historical trade-body access.

Price-body access requires a later explicit implementation/outcome freeze after Stage A/B rules are fixed.
