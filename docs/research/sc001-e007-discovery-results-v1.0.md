# SC001-E007 — Discovery Results v1.0

Date: 2026-09-15  
Status: **TERMINAL `E007_DISCOVERY_FAIL`**

Parent protocol:

`docs/research/sc001-e007-extreme-displacement-mean-reversion-executable-protocol-v1.0.md`

Primary identifier:

`E007_REV_G5_W60_T80_R50_LAT500_H10_CAP4`

## 1. Terminal result

Frozen DEV-DISCOVERY returned:

`E007_DISCOVERY_FAIL`

Confirmation, E007 L2, Q2, formal Validation and Final remain closed. No rescue tuning is authorized.

## 2. Primary observed facts

On the frozen 2024-03-01..20 Discovery interval:

- completed-trade minimum gate passed; inferred completed count from frozen side-share/count output is `26` (17/9 split);
- active-day minimum gate passed; positive-day share `0.63636...` is consistent with `7/11` positive active days;
- pooled mean gross edge: approximately `+18.281 bps` versus frozen `>=30 bps`;
- 10% trimmed mean: approximately `+21.492 bps` versus `>=25 bps`;
- pooled median gate passed `>=20 bps`;
- median active-day mean: approximately `+2.992 bps` versus `>=25 bps`;
- positive active-day share: approximately `63.64%` versus `>=70%`;
- day-block bootstrap 95% lower bound: approximately `+4.322 bps` versus strict `>15 bps`;
- top-1 absolute daily contribution share: approximately `0.3292` versus `<=0.25`;
- top-3 share: approximately `0.5968` versus `<=0.55`;
- both-sign breadth passed: at least `9` completed trades on the less-frequent reversal side versus `>=5` required;
- maximum one-sign share: approximately `0.6538`, passing `<=0.80`;
- 1,000 ms mean: approximately `+15.753 bps` versus `>=25 bps`;
- 1,000 ms trimmed mean: approximately `+19.650 bps` versus `>=20 bps`;
- 2,000 ms mean: approximately `+11.336 bps` versus `>=20 bps`;
- 2,000 ms trimmed mean: approximately `+15.545 bps`, passing `>=15 bps`;
- daily cap and one-position invariants passed.

Total failed frozen gates: `10`.

## 3. Interpretation

E007 is neither an event-scarcity failure like E006 nor a near-zero gross-mechanism failure like E004.

The result is better classified as:

**moderate gross reversal effect, but insufficient and unstable economics with material day concentration and latency fragility.**

Reasons:

1. event count and active-day breadth were sufficient to make the test informative;
2. individual-trade median behavior was strong enough to pass its frozen gate, but pooled mean/trimmed economics remained below the required headroom;
3. median active-day economics were very weak, showing that the apparent per-trade edge did not distribute robustly across days;
4. bootstrap lower bound was only about 4.3 bps, far below the economics-first promotion floor;
5. a few days contributed too much of the total edge;
6. the mean degraded materially from the 500 ms primary to 1,000 ms and 2,000 ms stress, indicating fragile timing sensitivity;
7. approximately 18 bps primary gross mean is positive, but the residual headroom over the roughly 10 bps one-leg regular-user taker round-trip reference is not large enough to justify L2/execution engineering under the frozen policy.

Therefore the primary cannot be promoted.

## 4. Stop rule

Effective immediately:

- do not run E007 Confirmation;
- do not acquire E007 L2 for rescue;
- do not lower the 80 bps displacement threshold;
- do not shorten the 500 ms latency assumption;
- do not change 60-second displacement window, 50% retracement, max hold or turnover cap;
- do not switch from reversal to continuation;
- do not select only the better sign/day/hour;
- do not add E002 TFI, E003 FLOW_IMPULSE, E004 compression or E006 basis filters;
- do not open Q2/Validation/Final;
- do not run an E007 parameter diagnostic grid.

The historical verdict remains:

`E007_DISCOVERY_FAIL`

## 5. Reusable lesson

E007 is the strongest one-leg taker candidate in this branch so far in the sense that it produced a nontrivial positive gross response on a usable number of events. But it still failed the economics-first standard because the effect was not broad or latency-robust enough.

This strengthens a strategic conclusion for SC001:

continuing to search nearby one-leg taker variants on the same tape is increasingly unlikely to be the highest-value path. The branch should now consider a mechanism where the economics do not begin with paying the spread and a full taker round trip.

## 6. Next research implication

Pause new neighboring one-leg taker signal variants.

The next prioritized mechanism family should be a separately identified **passive-maker / spread-capture** research branch using conservative L2 queue and adverse-selection modeling. Existing Q009A/Q009B qualified L2 data may be used first only for data-model feasibility and simulator validation, not as an immediate profitability claim.
