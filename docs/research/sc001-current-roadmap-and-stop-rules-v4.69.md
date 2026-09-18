# SC001 Current Roadmap and Stop Rules v4.69

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C12-D3 PASS / C12-S0 FROZEN NEXT / C11-S1 DEFER UNRESOLVED**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.68.md`

## 1. Binding prior states

All prior terminal strategy states remain immutable.

C11-S0 remains:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

C11-S1 remains:

`C11_S1_DEFER_SAMPLE`

because the frozen 2025-05-02 first one-second impulse equals exactly zero.

No C11 directional verdict has been inferred.

## 2. C12-D3 result

Exact:

`C12_D3_H1_BODY_INTEGRITY_PASS`

Observed:

- archives passed = 182/182;
- complete H1 source-support body set integrity-qualified;
- no peg deviation/episode/reversion/signal/fill/PnL;
- exit code 0.

Binding result:

`docs/research/sc001-c12-d3-h1-body-integrity-pass-result-v0.1.md`

## 3. C12-S0 was frozen before peg outcome

Protocol:

`docs/research/sc001-c12-s0-parity-reversion-sentinel-v0.1.md`

Runner:

`research/sc001/sc001_c12_s0_parity_reversion_v0_1.py`

Freeze:

`docs/research/sc001-c12-s0-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `ac336734faace800b9a1fd646a3e0253510eb5ef`;
- runner: `b3c783faf786f026cd4abca6c86e95af16507f33`;
- registry: `9c527ee5492ec29b8d4d9a06cff09720555f11a1`;
- D3 result: `f09be54f667c5d4ec031ca987cfe07edf42058a4`.

## 4. Frozen C12-S0 mechanism

Direct USDC-USDT spot cross-parity:

`peg_deviation_bps = 10000 * ln(price / 1.0)`

Episode state:

- re-arm only after abs deviation <=10 bps;
- enter at first abs deviation >=30 bps;
- no repeated entry while active;
- max hold =30 minutes;
- success = first return to abs deviation <=10 bps;
- if no success by deadline, use last trade at/before deadline with <=60s staleness.

No local moving average is used.

## 5. Structural reference

Prospective pre-funded stablecoin inventory architecture:

- two spot fills;
- 10 bps fee reference;
- 5 bps spread/slippage/model reserve;
- structural burden =15 bps.

## 6. C12-S0 data gates

Require:

- target UTC days with valid trades >=175/181;
- all six H1 months represented.

Failure:

`C12_S0_DEFER_DATA_QUALITY`

## 7. C12-S0 reversion gates

SURVIVE requires all:

- evaluable episodes >=12;
- episode dates >=6;
- episode months =6;
- return to <=10 bps band within 30m share >=60%;
- median gross favorable reversion >=15 bps;
- p75 gross favorable reversion >=20 bps.

Exact states:

- `C12_S0_PARITY_REVERSION_SURVIVE`;
- `C12_S0_REJECT_PARITY_REVERSION`;
- `C12_S0_DEFER_DATA_QUALITY`.

## 8. C12-S0 firewalls

Must remain false:

- maker simulation;
- fill model;
- queue model;
- PnL;
- promotional alpha.

S0 is still structural/reversion evidence only.

## 9. Immediate next action

Run frozen C12-S0 exactly once.

Do not launch another C11 direction-rule experiment while C11-S1 remains unresolved.
