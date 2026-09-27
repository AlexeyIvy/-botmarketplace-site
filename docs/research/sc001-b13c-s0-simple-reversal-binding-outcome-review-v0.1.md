# SC001 — B13-C S0 Simple Reversal Binding Outcome Review v0.1

Date: 2026-09-27  
Status: **B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT / TERMINAL FOR THIS FROZEN ARCHITECTURE**

## Result

The exact prospectively protected B13-C S0 test completed with:

`B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`

Valid price clusters:

`1,793`

Pooled signed 30-second reversal:
- p25 = `-5.139314758 bps`;
- median = `+1.368176223 bps`;
- p75 = `+9.104974174 bps`;
- strictly positive = `1002 / 1793 = 55.8839933%`.

Complete-day breadth:
- 2026-09-20: +1.1902 bps, n=152;
- 2026-09-21: +2.2257 bps, n=487;
- 2026-09-22: +1.3034 bps, n=238;
- 2026-09-23: +1.2994 bps, n=307;
- 2026-09-24: -0.0354 bps, n=239;
- 2026-09-25: +1.1744 bps, n=222.

Positive complete-day medians:

`5 / 6`

## Frozen gates

PASS:
- sample >=100;
- positive-cluster share >=55%;
- positive complete-day medians >=4/6.

FAIL:
- median signed reversal >=30 bps.

Observed median / hurdle:

`1.3682 / 30 = 4.56%`

## Interpretation

The frozen data support a small, fairly broad directional tendency toward reversal after pure-side liquidation clusters.

However, the effect is economically much too small for the pre-frozen gross-headroom requirement.

This distinction matters:

- **mechanism direction**: descriptively present;
- **simple S0 tradable headroom**: absent.

The S0 result is therefore not a data-quality failure, not a sample-size failure, and not a sign-direction failure. It is an **economic magnitude failure**.

The interquartile range is also wide relative to the median:
- p25 ~= -5.14 bps;
- p75 ~= +9.10 bps.

Therefore the typical 30-second reaction is noisy around a very small central edge.

## Binding consequence

Close the exact architecture:

`pure-side >=3-event cluster -> wait 1s -> 30s reversal`

on this protected interval.

Do not rescue it on the same evidence by searching:
- liquidation-size thresholds;
- only large clusters;
- winner symbols;
- other cluster gaps;
- other minimum event counts;
- majority-side rules;
- 5s/10s/60s/5m horizons;
- alternate entry delays.

Those would be post-outcome tuning.

## What remains scientifically useful

The result is not useless.

The positive-share and 5/6 day breadth indicate that explicit liquidation flow contains some short-horizon directional information, but the unconditioned S0 formulation does not concentrate enough magnitude.

Any future B13-C successor must be defined **before** using fresh post-definition events.

Examples of legitimate future research mechanisms, if separately pre-frozen:
- a mechanism-driven intensity/extremeness definition based on information available at event time;
- cross-market confirmation defined before fresh evidence;
- structural execution/imbalance state defined independently of this outcome.

The current protected interval may be used only as completed evidence/postmortem, not as a tuning set for a successor.
