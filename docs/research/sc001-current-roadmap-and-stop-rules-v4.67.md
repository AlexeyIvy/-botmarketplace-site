# SC001 Current Roadmap and Stop Rules v4.67

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C12-D2 v0.2 PASS / C11-S1 + C12-D3 FROZEN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.66.md`

## 1. Binding prior states

All prior terminal strategy states remain immutable.

C11-S0 remains:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

C12-D2 v0.2 now remains:

`C12_D2_V02_H1_ARCHIVE_METADATA_PASS`

No rescue tuning is authorized.

## 2. C12-D2 v0.2 result

Observed:

- archives verified = 182/182;
- target window = 2025-01-01 through 2025-06-30;
- source-support window = 2025-01-01 through 2025-07-01;
- combined HEAD Content-Length = 60,978,772 bytes;
- historical trade bodies not downloaded/opened;
- no peg deviation/reversion/threshold/signal/PnL;
- exit code 0.

Binding result:

`docs/research/sc001-c12-d2-v0.2-h1-archive-metadata-pass-result-v0.1.md`

## 3. Contamination registry

Current registry:

`docs/research/sc001-contamination-registry-v0.17.json`

### C11
The frozen H1-2025 12-event batch is authorized for first-impulse direction/continuation Selection/Calibration only.

### C12
The exact H1 source-body set is authorized for Selection/Calibration under the already-frozen parity/reversion rules.

Promotional evidence remains closed.

## 4. C11-S1 frozen

Purpose:

Test whether the first fully causal 1-second BTC impulse after the release predicts enough same-direction continuation from +1s to +60s.

Protocol:

`docs/research/sc001-c11-s1-first-impulse-continuation-sentinel-v0.1.md`

Runner:

`research/sc001/sc001_c11_s1_first_impulse_continuation_v0_1.py`

Freeze:

`docs/research/sc001-c11-s1-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `0f9cadab4db0ab11fa4371534062f2fbfb6753a4`;
- runner: `a1cb118408f8e9bec8afa6e1affc7075909bfdaa`;
- registry: `9c527ee5492ec29b8d4d9a06cff09720555f11a1`;
- S0 result: `ef91436d8ddfb9361daca5d271c3560728ce86e8`;
- freeze: `f0d59b51820feb9f43c0461d95003aae37699c03`.

Exact states:

- `C11_S1_FIRST_IMPULSE_CONTINUATION_SURVIVE`;
- `C11_S1_REJECT_FIRST_IMPULSE_CONTINUATION`;
- `C11_S1_DEFER_SAMPLE`.

## 5. C11-S1 frozen gates

Sample:

- all 12 pre/+1s/+60s anchors valid;
- all 12 first impulses nonzero.

Continuation SURVIVE requires all:

- positive signed continuation events >=8/12;
- signed continuation >=20 bps events >=6/12;
- median signed continuation >=20 bps;
- p75 signed continuation >=30 bps.

No macro surprise, fill model or PnL is calculated.

## 6. C12-S0 rules frozen before H1 body access

Future C12-S0 protocol:

`docs/research/sc001-c12-s0-parity-reversion-sentinel-v0.1.md`

Frozen prospective rules include:

- parity anchor = 1.0000 direct USDC-USDT cross-rate;
- arm only after abs deviation <=10 bps;
- episode entry at abs deviation >=30 bps;
- max hold =30 minutes;
- success = first return to abs deviation <=10 bps;
- structural burden =15 bps;
- no sign selection after outcome.

## 7. C12-D3 frozen engineering stage

Before running C12-S0, integrity-verify all 182 exact H1 source bodies.

Protocol:

`docs/research/sc001-c12-d3-h1-body-integrity-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c12_d3_h1_body_integrity_v0_1.py`

Freeze:

`docs/research/sc001-c12-d3-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `a3022955fd692da651a8b68cf703323564ffa3bb`;
- runner: `f0dd22533ccd11f9e6eece70e617bf266a886ba2`;
- registry: `9c527ee5492ec29b8d4d9a06cff09720555f11a1`;
- D2 result: `5c6160ffa4f48f5f41ba97a8794b1d28ad34e685`;
- future S0 protocol: `ac336734faace800b9a1fd646a3e0253510eb5ef`;
- freeze: `8daf79a7ffbac89c7a5395f066d19e129563c8ef`.

D3 calculates no peg deviation.

## 8. Immediate next action

Run in parallel:

1. C11-S1 exactly once on the frozen 12-event H1 calibration batch;
2. C12-D3 H1 body integrity across all 182 exact source archives.

Only after:

- C11-S1 terminal outcome, and
- C12-D3 exact PASS

may the next candidate-specific stages be designed/run.
