# SC001 Current Roadmap and Stop Rules v5.145

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 SIMPLE REVERSAL REJECT terminal**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.144.md`

## B13-C S0 exact real outcome

Runner job:

`job_20260927T085710Z_8508adc3`

Package integrity:

PASS

Bootstrap:

`B13C_S0_REAL_OUTCOME_BOOTSTRAP_PASS`

Terminal frozen classification:

`B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`

## Real frozen statistics

Valid price clusters:

`1,793`

Pooled:
- p25 = -5.1393 bps;
- median = +1.3682 bps;
- p75 = +9.1050 bps;
- positive count = 1,002;
- positive share = 55.884%.

Complete-day positive medians:

`5 / 6`

Frozen gates:
- sample >=100 = PASS;
- median >=30 bps = **FAIL**;
- positive share >=55% = PASS;
- positive complete days >=4/6 = PASS.

## Binding interpretation

This is an economic magnitude failure of the simple frozen 30-second reversal architecture.

The source, sample size and breadth are adequate. A weak directional reversal tendency exists descriptively, but median gross effect is only about 4.56% of the pre-frozen 30 bps headroom hurdle.

Do not calculate PnL or execution simulation for S0 because the gross headroom gate already failed.

## Anti-rescue

Do not tune the same interval by:
- liquidation size;
- cluster event count;
- symbol;
- cluster gap;
- side purity;
- entry delay;
- alternate horizons.

S0 is terminal/closed.

## Parallel program status

B15-P1 continues independently under operational freeze and W1 accumulation.

B14-A Sep25 P0 remains DEFER_DATA due transport/source failure; future prospective event may retry only after transport repair/preflight.

For B13-C, any successor S1 architecture must be frozen prospectively and evaluated only on fresh post-definition liquidation events.

## Current next state

`SELECT_NEXT_INDEPENDENT_OR_PROSPECTIVE_MECHANISM_WITHOUT_RESCUING_B13C_S0`
