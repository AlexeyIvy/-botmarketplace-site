# SC001 Current Roadmap and Stop Rules v4.50

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C8-D1E PASS / C8-D2 METADATA PASS / C8-D3 BODY INTEGRITY FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.49.md`

## 1. Binding terminal strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8 still has no strategy verdict.

## 2. C8-D1E result

Exact:

`C8_D1E_STRICT_COACTIVE_1S_PASS`

Qualified temporal representation:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

Observed engineering quality on 2025-01-15:

- joint coactive seconds = 72,539;
- joint share about 83.96%;
- minimum joint-active seconds/hour = 2,378;
- median last-event skew = 150.5 ms;
- p99 skew = 846.7 ms;
- failed gates = none.

## 3. C8-D2 result

Exact:

`C8_D2_PRICE_CALIBRATION_METADATA_PASS`

Exact prospective price-calibration day:

`2025-01-20 UTC`

Selection rule:

`first Monday after 2025-01-15 engineering day`

Resolved source sizes:

- OKX D = 31,328,006 bytes;
- OKX D+1 = 30,915,552 bytes;
- Bybit D = 311,242,935 bytes;
- total = 373,486,493 bytes.

No historical body or cross-venue price outcome was opened in D2.

Binding result:

`docs/research/sc001-c8-d2-price-calibration-metadata-pass-result-v0.1.md`

## 4. Contamination declared before price body access

Current registry:

`docs/research/sc001-contamination-registry-v0.12.json`

The exact 2025-01-20 C8 price channel is now:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

Authorized bodies:

- OKX 2025-01-20;
- OKX 2025-01-21 D+1 source support;
- Bybit 2025-01-20.

## 5. C8B-S0 price statistic frozen before body access

Future structural headroom protocol:

`docs/research/sc001-c8b-s0-cross-venue-relative-basis-headroom-sentinel-v0.1.md`

Frozen identity:

`0f4086b8b3109f35b5def9e4e6180a8b5e0e6bf9`

Key rules frozen before any C8 price comparison:

- candidate branch = C8B paired convergence;
- strict same-second coactivity;
- per-venue chronologically last trade in second;
- raw log spread in bps;
- causal 5-minute median cross-venue basis;
- minimum 120 prior coactive observations;
- dislocation = raw spread minus causal baseline;
- four-fill structural architecture;
- gross headroom hurdle = 30 bps;
- persistence = same-sign >=30 bps for two consecutive wall-clock seconds;
- no C8A leader/lag switch after outcome.

## 6. C8-D3 stage

D3 is body/schema normalization only.

Protocol:

`docs/research/sc001-c8-d3-price-calibration-body-integrity-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c8_d3_price_calibration_body_integrity_v0_1.py`

Freeze:

`docs/research/sc001-c8-d3-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `d3446e3dd977492a00e546e53575c0e9323fb389`;
- runner: `47a2b04f46b023b5c38dd84402f0555ee08022df`;
- registry: `54203bc2b85bead5b319a1acc2463b5e9a81be19`;
- D2 result: `074c5e467e5e758fb4b19be138ae8cf58ee70fe4`.

## 7. D3 normalized outputs

Per venue only:

- one last trade per active second;
- no carry-forward;
- no future interpolation.

Files:

- `okx_last_trade_1s.csv`;
- `bybit_last_trade_1s.csv`.

D3 may not intersect or compare the two price series.

## 8. Exact D3 states

PASS:

`C8_D3_PRICE_BODY_INTEGRITY_PASS`

REVIEW:

`C8_D3_PRICE_BODY_INTEGRITY_REVIEW`

REVIEW remains data/implementation state only.

## 9. D3 firewalls

Must remain false:

- cross-venue price comparison;
- cross-venue return;
- rolling cross-venue baseline;
- raw spread;
- dislocation;
- convergence outcome;
- signal;
- PnL;
- promotional alpha.

## 10. Immediate next action

Run frozen C8-D3 price-body integrity/normalization on VPS.

Only after exact D3 PASS may the already-frozen C8B-S0 protocol be implemented and run.
