# SC001 — C11 v2 Selection/Calibration Metadata Preflight Protocol v0.3

Date: 2026-09-19
Status: **ENGINEERING-ONLY AMENDMENT AFTER V0.2 REVIEW / NO CHRONOLOGY CHANGE / NO PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`
Supersedes metadata-parser implementation semantics from:
`docs/research/sc001-c11-v2-selection-metadata-preflight-protocol-v0.2.md`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.75.md`;
- `docs/research/sc001-c11-v2-chronology-freeze-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.19.json`.

## 1. Observed v0.2 REVIEW

The v0.2 run returned:

`C11_V2_SC_METADATA_PREFLIGHT_REVIEW`

at the first frozen event:

`EMPLOYMENT 2025-07-03`

with:

`BLS row metadata mismatch EMPLOYMENT 2025-07-03`

Official BLS confirms the frozen event:

- Thursday, July 3, 2025;
- 08:30 AM;
- Employment Situation for June 2025.

The chronology is therefore not defective.

## 2. Objective engineering diagnosis

v0.2 normalized whitespace on the raw HTML string and then applied a continuous row regex.

Raw HTML contains markup tags between visible table cells.

Therefore a visually continuous BLS row may not be a continuous raw-HTML text sequence.

Classification:

`ENGINEERING_BLS_RAW_HTML_REGEX_DEFECT`

This is not a source failure, calendar failure, data-quality failure or strategy verdict.

## 3. v0.3 BLS parsing rule

Before semantic matching:

1. parse the official BLS HTML with Python standard-library `HTMLParser`;
2. collect visible text nodes only;
3. normalize visible whitespace;
4. apply the exact release-row semantic pattern to the resulting visible text.

For each frozen event require, in sequence:

- weekday;
- exact full English month;
- exact calendar day, allowing only optional leading zero;
- exact year;
- exact `08:30 AM`;
- exact release family:
  - `Employment Situation`, or
  - `Consumer Price Index`.

This allows HTML markup differences but does not relax event identity.

## 4. Frozen chronology unchanged

All 24 Selection/Calibration event identities, dates and UTC timestamps remain exactly those in:

`docs/research/sc001-c11-v2-chronology-freeze-v0.1.md`

No event addition, removal, substitution or time-window change is authorized.

## 5. OKX metadata rules unchanged

For each event require:

- exact `BTC-USDT-SWAP-trades-YYYY-MM-DD.zip`;
- unique trusted URL;
- final host `static.okx.com`;
- HTTPS;
- HEAD 200;
- positive numeric Content-Length.

No archive body GET/open.

## 6. Firewalls unchanged

Must remain false:

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

## 7. Exact terminal states

PASS:

`C11_V2_SC_METADATA_PREFLIGHT_PASS`

REVIEW:

`C11_V2_SC_METADATA_PREFLIGHT_REVIEW`

## 8. Rerun rule

Run all 24 events from the beginning under v0.3.

Do not combine partial v0.1/v0.2 checks with v0.3 final evidence.

No price-bearing access is authorized by this amendment.
