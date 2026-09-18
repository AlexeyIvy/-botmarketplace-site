# SC001 — C11 v2 Selection Stage A/B v1.0 Implementation-Fail Review v0.1

Date: 2026-09-19
Status: **ENGINEERING REVIEW — NO STAGE A/B VERDICT COMPUTED**
Scope: `SCALPING RESEARCH / SC001`

Parent:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.77.md`;
- `docs/research/sc001-c11-direction-rule-v2-stage-ab-selection-protocol-v1.0.md`;
- `docs/research/sc001-c11-v2-stage-ab-selection-implementation-freeze-v1.0.json`.

## 1. Observed run state

The frozen one-shot Selection runner started normally and progressed through events 1-12.

It stopped at event 13:

`EMPLOYMENT 2026-04-03`

with exact implementation token:

`C11_V2_SELECTION_IMPLEMENTATION_FAIL`

and error:

`RuntimeError: header mismatch`

## 2. Interpretation

This is an implementation/data-schema review state.

It is **not**:

- `C11_V2_SC_DEFER_DATA_QUALITY`;
- `C11_V2_SC_REJECT_RESIDUAL_HEADROOM`;
- `C11_V2_SC_REJECT_DIRECTION_RETENTION`;
- `C11_V2_SC_SURVIVE_TO_PROSPECTIVE_CONFIRMATION`.

No Stage A or Stage B verdict was written.

No Confirmation outcome was authorized or opened.

No execution/PnL conclusion is authorized.

## 3. Known boundary

The first 12 event bodies were accessed under the already frozen Selection/Calibration authorization.

They remain nonpromotional Selection/Calibration evidence.

The failure occurred while validating the exact CSV header of the 2026-04-03 archive before that event was admitted into the calculation.

No chronology, gate, direction rule, horizon or burden may be changed because of this failure.

## 4. Required next action

Perform a read-only engineering diagnostic on exactly:

`BTC-USDT-SWAP-trades-2026-04-03.zip`

Allowed diagnostic fields:

- ZIP member name/count;
- raw first-line bytes;
- UTF-8-decoded first line/header only;
- whether a UTF-8 BOM is present.

Do not print or inspect any data row, price, trade, return, impulse or event outcome.

After the exact header is known:

- if semantically identical with an encoding/format artifact, version an engineering-only parser correction;
- if the archive schema genuinely changed, freeze a schema-version-aware parser only after mapping exact fields without changing financial rules;
- do not accept arbitrary extra/reordered columns without explicit semantic review.

No rerun is authorized until the diagnostic is recorded.
