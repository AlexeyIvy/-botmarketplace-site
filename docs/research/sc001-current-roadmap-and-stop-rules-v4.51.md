# SC001 Current Roadmap and Stop Rules v4.51

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C8-D3 PASS / C8B-S0 STRUCTURAL HEADROOM SENTINEL FROZEN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.50.md`

## 1. Binding terminal strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8 still has no strategy verdict.

## 2. C8-D3 result

Exact:

`C8_D3_PRICE_BODY_INTEGRITY_PASS`

Observed:

- OKX active seconds = 83,899;
- Bybit active seconds = 84,190;
- OKX minute/hour coverage = 1440/24;
- Bybit minute/hour coverage = 1440/24;
- failed gates = none;
- no cross-venue price comparison occurred in D3;
- no return/baseline/spread/dislocation/convergence/signal/PnL;
- exit code 0.

Binding result:

`docs/research/sc001-c8-d3-price-body-integrity-pass-result-v0.1.md`

## 3. Price evidence role

The 2025-01-20 C8 price channel remains:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

under:

`docs/research/sc001-contamination-registry-v0.12.json`

The temporal representation remains:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

## 4. C8B-S0 is already frozen before first price outcome

Protocol:

`docs/research/sc001-c8b-s0-cross-venue-relative-basis-headroom-sentinel-v0.1.md`

Runner:

`research/sc001/sc001_c8b_s0_relative_basis_headroom_v0_1.py`

Freeze:

`docs/research/sc001-c8b-s0-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `0f4086b8b3109f35b5def9e4e6180a8b5e0e6bf9`;
- runner: `0fff930fd9fe90472ed7cf2486d884b35af52861`;
- registry: `54203bc2b85bead5b319a1acc2463b5e9a81be19`;
- D3 result: `b234aff4100e8fff958eff1c14a25bd2f4841d53`.

## 5. Frozen structural price statistic

For strict coactive second `s`:

`raw_spread_bps = 10000 * ln(OKX_price / BYBIT_price)`

Causal basis reference:

- prior 300 wall-clock seconds;
- strict coactive observations only;
- minimum 120 prior observations;
- median;
- current second excluded.

Dislocation:

`raw_spread_bps - causal_median_basis_bps`

## 6. Frozen architecture and headroom hurdle

Candidate branch:

`C8B PAIRED CONVERGENCE`

Prospective architecture:

- long cheap venue / short rich venue;
- four structural fills.

Frozen reference:

- 5 bps/fill;
- 20 bps four-fill fee-reference floor;
- 30 bps gross structural headroom hurdle.

No C8A directional lead/lag substitution is allowed after S0 output.

## 7. Frozen persistence rule

Headroom episode requires:

- abs dislocation >=30 bps now;
- immediately next wall-clock second also strict-coactive and >=30 bps;
- same sign both seconds.

A new episode is counted only after at least one eligible/coactive below-30-bps reset.

## 8. Sample gates

Require:

- strict coactive seconds >=50,000;
- baseline eligible seconds >=40,000;
- baseline eligible UTC hours =24.

Failure gives:

`C8B_S0_DEFER_SAMPLE`

## 9. Structural headroom gates

Require all for survive:

- persistent episodes >=10;
- episode UTC hours >=6;
- p99 abs dislocation >=30 bps;
- max abs dislocation >=40 bps.

PASS-through research state:

`C8B_S0_HEADROOM_SURVIVE`

If sample gates pass but any headroom gate fails:

`C8B_S0_REJECT_HEADROOM`

## 10. What S0 does NOT test

S0 does not calculate:

- convergence after entry;
- cross-venue return;
- executable bid/ask;
- legging/slippage;
- funding/fees beyond the frozen structural reference;
- strategy PnL;
- promotional alpha.

SURVIVE only justifies a later convergence/execution study.

## 11. Dual evidence output

S0 writes:

1. structural strategy evidence;
2. feature/building-block evidence.

This preserves:

- raw cross-venue basis as R6 state/reference;
- causal local venue basis as R6;
- transient relative-basis deviation as R1/R2 candidate evidence.

## 12. Immediate next action

Run frozen C8B-S0 exactly once on the 2025-01-20 nonpromotional calibration data.

Do not change threshold, persistence, baseline, venue, date, asset, sign or mechanism after outcome.
