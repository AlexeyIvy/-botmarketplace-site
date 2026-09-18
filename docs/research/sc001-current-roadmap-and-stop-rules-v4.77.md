# SC001 Current Roadmap and Stop Rules v4.77

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — C11 V2 METADATA PASS / DIRECTION + STAGE A/B FROZEN / SELECTION OUTCOME READY**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.76.md`

## 1. Binding state

All prior terminal C1-C10 and C12 decisions remain unchanged.

C11 remains the only active structural survivor.

Historical states remain:

- `C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`;
- `C11_S1_DEFER_SAMPLE`.

## 2. Metadata preflight passed

Exact state:

`C11_V2_SC_METADATA_PREFLIGHT_PASS`

Observed:

- 24/24 events verified;
- 12 CPI / 12 Employment;
- chronology unchanged;
- no historical trade body opened;
- no first impulse/residual/direction/continuation/execution/PnL;
- no Confirmation outcome.

Binding result:

`docs/research/sc001-c11-v2-selection-metadata-preflight-pass-result-v0.3.md`

## 3. Direction Rule v2 and Stage A/B are now frozen

Binding protocol:

`docs/research/sc001-c11-direction-rule-v2-stage-ab-selection-protocol-v1.0.md`

Implementation:

`research/sc001/sc001_c11_v2_selection_stage_ab_v1_0.py`

Implementation freeze:

`docs/research/sc001-c11-v2-stage-ab-selection-implementation-freeze-v1.0.json`

## 4. Direction Rule v2

For DATA_VALID event:

- first causal 1-second impulse >0 -> LONG;
- <0 -> SHORT;
- =0 -> NO_TRADE.

No alternate impulse window.

No epsilon threshold.

No macro surprise.

## 5. Data-quality gate

Require:

- data-valid >=22/24;
- CPI valid >=11/12;
- Employment valid >=11/12.

Failure:

`C11_V2_SC_DEFER_DATA_QUALITY`

No Stage A/B verdict is computed in that case.

## 6. Stage A — residual headroom

Metric:

`abs(ln(price_60s / price_1s)) * 10000`

Require all:

- >=12/24 scheduled events at >=20 bps;
- median DATA_VALID residual >=20 bps;
- CPI >=5/12 at >=20 bps;
- Employment >=5/12 at >=20 bps.

Failure:

`C11_V2_SC_REJECT_RESIDUAL_HEADROOM`

Stage B remains NOT_COMPUTED.

p75/max are diagnostic only.

## 7. Stage B — direction + retention

Computed only if Stage A survives.

Opportunity retention requires:

- actionable >=18/24;
- CPI actionable >=8/12;
- Employment actionable >=8/12.

Signed continuation:

`direction * ln(price_60s / price_1s) * 10000`

Require all:

- median actionable signed continuation >=20 bps;
- >=10/24 scheduled events signed >=20 bps;
- CPI signed >=20 bps >=4/12;
- Employment signed >=20 bps >=4/12.

Failure:

`C11_V2_SC_REJECT_DIRECTION_RETENTION`

Full survive:

`C11_V2_SC_SURVIVE_TO_PROSPECTIVE_CONFIRMATION`

## 8. One-shot Selection authorization

Contamination registry:

`docs/research/sc001-contamination-registry-v0.20.json`

authorizes historical trade-body access only for the exact frozen 24 Selection/Calibration events under the frozen Stage A/B protocol.

This evidence remains nonpromotional.

## 9. Confirmation firewall

The 12 prospective Confirmation identities remain untouched.

No Confirmation outcome access unless Selection exact state is:

`C11_V2_SC_SURVIVE_TO_PROSPECTIVE_CONFIRMATION`

No retuning between Selection and Confirmation.

## 10. Execution firewall

Execution/slippage/fill/PnL remains closed even if Selection survives.

Only after prospective Confirmation survives may execution modeling be frozen.

## 11. C13+ gate

Do not open C13+ while C11 remains unresolved.

## 12. Immediate next action

Run the frozen one-shot 24-event C11 v2 Selection Stage A/B runner.

This is the first authorized price-bearing v2 Selection run.
