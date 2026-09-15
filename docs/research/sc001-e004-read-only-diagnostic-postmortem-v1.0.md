# SC001-E004 Read-Only Diagnostic Postmortem v1.0

Date: 2026-09-15  
Status: **POSTMORTEM KNOWLEDGE CAPTURE — TERMINAL VERDICT UNCHANGED**

Parent terminal result:

`E004_DISCOVERY_FAIL`

Primary protocol:

`docs/research/sc001-e004-volatility-compression-breakout-executable-protocol-v1.0.md`

## 1. Purpose

Record the already-frozen eight one-factor diagnostic variants after the terminal E004 Discovery failure.

These diagnostics are read-only scientific context. They do not alter the failed primary, cannot open Confirmation, and cannot select a replacement E004 parameterization.

## 2. Primary terminal result retained

Frozen primary 250 ms result remained far below the economics-first gates:

- pooled mean gross edge: about `+0.17935 bps` versus `>=20 bps` required;
- 10% trimmed mean: about `+1.05414 bps` versus `>=15 bps`;
- pooled median: about `+1.66221 bps` versus `>=10 bps`;
- median active-day mean: about `-1.75324 bps` versus `>=12 bps`;
- positive active-day share: about `47.37%` versus `>=70%`;
- day-block-bootstrap lower bound: about `-3.93417 bps` versus `>10 bps`;
- 500 ms and 1,000 ms stresses were also near zero and failed.

The primary verdict remains exactly:

`E004_DISCOVERY_FAIL`

## 3. Frozen diagnostic neighborhood results

The eight one-factor variants produced the following already-observed read-only outcomes.

| Variant | Single change | Completed | Mean bps | Median bps | 10% trimmed mean bps |
|---|---|---:|---:|---:|---:|
| W10 | compression window 10 min | 75 | +1.04908 | +0.86148 | +1.85573 |
| W30 | compression window 30 min | 74 | +1.07956 | -1.95363 | -0.47014 |
| Q10 | compression percentile 10% | 71 | +0.24245 | -3.37974 | -2.27229 |
| Q30 | compression percentile 30% | 76 | -4.07812 | -0.60471 | -3.67661 |
| B0 | breakout buffer 0 bps | 76 | +1.06603 | +1.99083 | +1.57398 |
| B5 | breakout buffer 5 bps | 76 | -1.49924 | +0.33901 | -0.32134 |
| H10 | holding horizon 10 min | 76 | +1.39123 | -0.08931 | +0.69204 |
| H30 | holding horizon 30 min | 76 | -2.47433 | -2.76736 | -3.80196 |

## 4. Interpretation

The local neighborhood strengthens rather than weakens the terminal conclusion.

No diagnostic mean exceeded approximately `+1.4 bps`. None approached the tens-of-bps scale required for a standalone regular-user taker strategy.

Several variants with slightly positive means had weak or negative medians/trimmed means, so there is no evidence that a robust broad distribution is hidden immediately next to the primary configuration.

In particular:

- reducing the breakout buffer to zero improved the median only to roughly `+2 bps`, still far below the economic scale;
- shortening the hold to 10 minutes gave the largest diagnostic mean, about `+1.39 bps`, while the median remained slightly negative;
- longer 30-minute holding became materially negative;
- looser compression selection (Q30) was clearly negative;
- neither a shorter nor longer compression window produced a meaningful gross edge.

Therefore E004 failed because the chosen compression-to-breakout family did not generate a sufficiently large residual directional move, not because one neighboring parameter was accidentally missed.

## 5. No-rescue rule

Do not:

- promote W10/W30/Q10/Q30/B0/B5/H10/H30;
- combine diagnostic changes;
- tune a new window/percentile/buffer/holding horizon on these same Discovery outcomes;
- add E002 TFI or E003 FLOW_IMPULSE to rescue E004;
- open E004 Confirmation, L2, Q2, formal Validation or Final.

A new mechanism must receive a new experiment identifier and be frozen before its own alpha is observed.

## 6. Research lesson added to SC001

E001-E004 now provide increasingly strong evidence that single-venue, one-leg directional BTC scalp hypotheses which enter after a visible price/flow state transition tend to leave only a very small post-entry residual edge relative to approximately 10 bps round-trip taker costs.

The next priority should therefore change mechanism class rather than keep searching tiny neighboring directional formulations.
