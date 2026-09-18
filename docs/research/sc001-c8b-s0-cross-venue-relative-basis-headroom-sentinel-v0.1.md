# SC001 — C8B-S0 Cross-Venue Relative-Basis Structural Headroom Sentinel v0.1

Date: 2026-09-18
Status: **FROZEN BEFORE FIRST C8 CROSS-VENUE PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c8-d1e-strict-coactive-1s-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.12.json`;
- `docs/research/sc001-c8-d3-price-calibration-body-integrity-protocol-v0.1.md`.

## 1. Candidate identity

Candidate:

`C8B`

Mechanism:

`PAIRED CROSS-VENUE TRANSIENT RELATIVE-BASIS CONVERGENCE`

Execution family if later pursued:

`T3 paired`

C8A directional lead/lag is **not** tested by this sentinel and must not be substituted after outcome.

## 2. Purpose

Cheapest price-bearing kill test:

> Do strict same-second OKX/Bybit BTC perpetual prices exhibit transient deviations from their causal local cross-venue basis large and persistent enough to justify later paired-convergence research?

This is structural headroom only, not a convergence/PnL test.

## 3. Frozen temporal representation

Exactly:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

For each UTC second, use the D3 normalized chronologically last trade price **only if both venues were active inside that exact same second**.

No prior-second carry-forward.

No future interpolation.

## 4. Frozen raw spread

For a strict coactive second `s`:

`raw_spread_bps[s] = 10000 * ln(OKX_last_price[s] / BYBIT_last_price[s])`

This signed value is not itself considered a tradable dislocation because persistent venue basis may exist.

## 5. Frozen causal local-basis reference

For each current coactive second `s`, form a causal lookback:

`[s-300 seconds, s)`

using only strict coactive seconds inside that wall-clock interval.

Require at least `120` prior coactive observations.

Reference:

`baseline_bps[s] = median(raw_spread_bps in prior 300 wall-clock seconds)`

No current-second spread enters the baseline.

## 6. Frozen dislocation statistic

`dislocation_bps[s] = raw_spread_bps[s] - baseline_bps[s]`

`abs_dislocation_bps[s] = abs(dislocation_bps[s])`

No direction/leader is chosen.

## 7. Structural execution hurdle

Prospective paired architecture:

- long cheap venue / short rich venue;
- open two legs + close two legs;
- four structural fills.

Frozen selection reference:

- 5 bps per fill;
- 20 bps four-fill fee-reference floor;
- `30 bps` gross structural headroom hurdle.

This is not an exact executable cost estimate.

## 8. Frozen persistence/event definition

A structural headroom episode exists when:

1. current eligible second has `abs_dislocation_bps >= 30`;
2. the immediately following wall-clock second is also strict-coactive and has `abs_dislocation_bps >= 30`;
3. the sign of `dislocation_bps` is the same in both seconds.

Count an episode only on entry into such a qualifying run.

A later episode can start only after at least one eligible/coactive second with `abs_dislocation_bps < 30`.

This prevents counting every second of one persistent episode as a new opportunity.

## 9. Sample gates

Require:

- strict coactive seconds >=50,000;
- baseline-eligible seconds >=40,000;
- baseline-eligible UTC hours =24.

Failure gives:

`C8B_S0_DEFER_SAMPLE`

No thresholds may be relaxed.

## 10. Headroom gates

SURVIVE structural headroom only if all:

- qualifying persistent episodes >=10;
- qualifying episodes span >=6 UTC hours;
- 99th percentile `abs_dislocation_bps >=30 bps`;
- maximum absolute dislocation >=40 bps.

Exact survive token:

`C8B_S0_HEADROOM_SURVIVE`

If sample gates pass but any headroom gate fails:

`C8B_S0_REJECT_HEADROOM`

## 11. Interpretation

SURVIVE means only that trade-price relative-basis dislocations have enough raw structural scale/frequency to justify a later convergence-outcome and quote/execution study.

It does not prove:

- convergence;
- executable fills;
- arbitrage;
- net profitability.

REJECT means this exact 1-second paired relative-basis mechanism lacks enough raw headroom on the frozen calibration day.

## 12. No-rescue rules

After output do not:

- lower 30 bps;
- shorten persistence to one second;
- change 5-minute causal baseline;
- lower minimum 120 baseline observations;
- choose only one spread sign;
- switch to C8A directional lag;
- change venue/asset/date;
- add volatility/flow filters.

Any materially different mechanism requires a new ID.

## 13. Dual evidence outputs

Create:

1. Strategy/Structural Evidence Report;
2. Feature/Building-Block Evidence Report.

Retain separately:

- cross-venue raw basis as R6 state/reference;
- causal local cross-venue basis median as R6;
- transient relative-basis deviation as R1/R2 candidate evidence.

No global `works=true` field.
