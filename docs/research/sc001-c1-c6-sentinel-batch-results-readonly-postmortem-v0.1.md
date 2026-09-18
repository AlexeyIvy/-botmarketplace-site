# SC001 — C1-C6 Sentinel Batch Results & Read-Only Postmortem v0.1

Date: 2026-09-18  
Status: **BATCH COMPLETE — 0/6 SURVIVORS / READ-ONLY POSTMORTEM**  
Scope: `SCALPING RESEARCH / SC001`

## 1. Batch execution integrity

Frozen all-six batch terminal state:

`SC001_C1C6_SENTINEL_BATCH_COMPLETE`

Execution facts:

- all six candidates attempted: true;
- all six recognized terminal reports: true;
- total frozen strategy variants: 11;
- between-result adaptation: false;
- protected data accessed: false;
- promotional alpha accessed: false;
- batch exit code: 0.

Terminal candidate states:

- C1: `C1_REJECT_SENTINEL`;
- C2: `C2_REJECT_SENTINEL`;
- C3: `C3_REJECT_SENTINEL`;
- C4: `C4_REJECT_SENTINEL`;
- C5: `C5_REJECT_SENTINEL`;
- C6: `C6_REJECT_SENTINEL`.

There are no sentinel survivors in this batch.

This is not an execution failure. The frozen batch completed correctly and the six candidates failed their predeclared selection gates.

---

## 2. C1 — multi-asset same-venue spot/perp basis convergence

Frozen terminal state:

`C1_REJECT_SENTINEL`

Observed:

- pooled measured triggers: 0;
- active pairs with >=3 triggers: 0;
- equal-weight active-pair mean: unavailable;
- median active-pair mean: unavailable;
- positive active pairs: 0.

Failed gates:

- pairs with >=3 triggers >=4;
- pooled triggers >=40;
- equal-weight active-pair mean contraction >=30 bps;
- median active-pair mean contraction >=30 bps;
- positive breadth >=3/4.

### Read-only interpretation

The strict legacy E006 mechanism did not produce a usable multi-asset event set under the frozen +50 bps dislocation rule on the July/September contaminated sandbox.

Primary failure class:

`EVENT_SCARCITY_UNDER_FROZEN_MECHANISM`

No threshold reduction, hold extension, asset cherry-picking, or volatility/flow rescue is authorized.

This strengthens the earlier E006 lesson that event scarcity is a central limitation of this exact family.

---

## 3. C2 — multi-minute local-reference mean reversion

Frozen terminal state:

`C2_REJECT_SENTINEL`

### C2-A — 5-minute trailing VWAP reference

- pooled non-overlapping opportunities: 2032;
- assets with >=10 opportunities: 8/8;
- equal-weight asset mean: about -3.9601 bps;
- median asset mean: about -6.1943 bps;
- positive assets: 2/8;
- active calendar days: 28/28.

Failed only the economic/breadth gates:

- equal-weight mean >=15 bps;
- median asset mean >=15 bps;
- positive assets >=5.

### C2-B — median of five completed 1-minute VWAPs

- pooled non-overlapping opportunities: 4730;
- assets with >=10 opportunities: 8/8;
- equal-weight asset mean: about -4.2796 bps;
- median asset mean: about -3.6349 bps;
- positive assets: 0/8;
- active calendar days: 28/28.

Failed the same economic/breadth gates.

### Read-only interpretation

This is not a sample-size failure. Both frozen reference representations had abundant opportunities and full calendar coverage.

The average signed outcome was negative, i.e. the tested deviations did not show the required reversion; on average the move was in the opposite direction of the hypothesis.

Primary failure class:

`ABUNDANT_SAMPLE_BUT_MEAN_REVERSION_EFFECT_NEGATIVE`

No trend veto, volatility filter, RSI/Stochastic, threshold change, or horizon search may be added as a rescue under C2.

---

## 4. C3 — 5m/10m continuation / volatility expansion

Frozen terminal state:

`C3_REJECT_SENTINEL`

### C3-A — 5-minute expansion breakout

- pooled non-overlapping events: 4871;
- active assets: 8/8;
- equal-weight asset mean: about -0.5157 bps;
- median asset mean: about -0.4549 bps;
- positive assets: 2/8;
- active days: 28/28.

### C3-B — 10-minute expansion breakout

- pooled non-overlapping events: 2375;
- active assets: 8/8;
- equal-weight asset mean: about -0.4933 bps;
- median asset mean: about +0.1688 bps;
- positive assets: 4/8;
- active days: 28/28.

Both variants failed:

- equal-weight mean >=15 bps;
- median asset mean >=15 bps;
- positive assets >=5.

### Read-only interpretation

Again, event frequency and coverage were not limiting. The frozen continuation/expansion effect was essentially zero to slightly negative cross-market and far below the 15 bps structural screen.

Primary failure class:

`ABUNDANT_SAMPLE_NO_CONTINUATION_HEADROOM`

No ADX/MACD/volume/flow/time-of-day rescue is authorized under C3.

---

## 5. C4 — BTC/ETH -> alt lead/lag

Frozen terminal state:

`C4_REJECT_SENTINEL`

All four variants had 28 active days and all six target assets evaluable.

### BTC 30s -> alt 60s

- leader events: 2261;
- event-target observations: 13421;
- raw equal-weight response: about +0.3076 bps;
- residual equal-weight response: about +0.3796 bps;
- residual median target mean: about +0.4065 bps;
- positive residual targets: 5/6;
- diagnostic: `COMMON_BETA_NOT_LEAD_LAG = true`.

### BTC 60s -> alt 60s

- leader events: 904;
- observations: 5359;
- raw equal-weight response: about -1.2500 bps;
- residual equal-weight response: about +0.4458 bps;
- residual median target mean: about +0.4945 bps;
- positive residual targets: 6/6.

### ETH 30s -> alt 60s

- leader events: 2097;
- observations: 12455;
- raw equal-weight response: about +0.2828 bps;
- residual equal-weight response: about +0.6673 bps;
- residual median target mean: about +0.5844 bps;
- positive residual targets: 6/6;
- diagnostic: `COMMON_BETA_NOT_LEAD_LAG = true`.

### ETH 60s -> alt 60s

- leader events: 957;
- observations: 5665;
- raw equal-weight response: about -1.1968 bps;
- residual equal-weight response: about +0.6285 bps;
- residual median target mean: about +0.7671 bps;
- positive residual targets: 6/6.

All four failed the 15 bps residual economic gates.

### Read-only interpretation

C4 is informative because sample size and target breadth are strong, and residual means are broadly positive, but the magnitude is only sub-1-bps.

The 30-second raw-positive cases do not establish lead/lag after common-market interpretation; the frozen diagnostic classified them as common-beta rather than a viable lag edge.

Primary failure class:

`BROAD_BUT_ECONOMICALLY_TINY_RESIDUAL_EFFECT`

No lag grid, target selection, leader ensemble, volatility filter, or winner-alt selection is authorized as a C4 rescue.

---

## 6. C5 — large aggressive-flow / forced-flow exhaustion

Frozen terminal state:

`C5_REJECT_SENTINEL`

Observed:

- pooled events: 10033;
- per-asset counts ranged from 550 to 2516;
- all eight assets highly active;
- positive active-asset count: 6/8;
- median active-asset mean: about +0.5050 bps;
- per-asset means ranged approximately from -0.362 bps to +1.104 bps.

The printed per-asset means imply an equal-weight mean of roughly +0.468 bps.

Failed gates:

- equal-weight asset mean >=15 bps;
- median active-asset mean >=15 bps.

### Read-only interpretation

The trade-only forced-flow exhaustion mechanism had extremely ample event frequency and reasonable breadth, but its gross effect magnitude was economically tiny relative to the frozen two-fill hurdle.

Primary failure class:

`ABUNDANT_SAMPLE_BROAD_SIGN_BUT_SUB_BPS_EFFECT`

Because the cheap trade-only sentinel failed economic headroom, L2 depth/depletion/replenishment work is not justified as a rescue for C5.

---

## 7. C6 — cross-sectional short-horizon dispersion/reversion

Frozen terminal state:

`C6_REJECT_SENTINEL`

Observed:

- opportunities: 2688;
- opportunity days: 28/28;
- 10% trimmed mean gross spread: about +3.0037 bps;
- median opportunity spread: about +3.8395 bps;
- equal-weight calendar-day mean spread: about +1.9336 bps;
- positive calendar-day share: about 0.7143;
- top long-role absolute contribution share: about 0.3301;
- top short-role absolute contribution share: about 0.3201.

Passed sample/day/breadth-concentration style diagnostics, but failed:

- equal-weight calendar-day mean >=30 bps;
- median opportunity spread >=20 bps;
- trimmed mean >=30 bps.

### Read-only interpretation

C6 shows a positive directional tendency with good day breadth and acceptable concentration, but the gross spread is only a few bps against a four-fill structural screen of 30 bps.

Primary failure class:

`ROBUST_SIGN_PATTERN_BUT_INSUFFICIENT_PAIRED_ECONOMIC_HEADROOM`

No factor addition, volatility scaling, historical winner/loser asset selection, or hold optimization may rescue C6 under this ID.

---

## 8. Cross-candidate conclusion

The C1-C6 batch ruled out several materially different mechanisms under one frozen nonpromotional sandbox:

- strict same-venue basis dislocation: too scarce;
- multi-minute local-reference reversion: wrong-sign average effect;
- multi-minute expansion continuation: near-zero effect;
- BTC/ETH -> alt lead/lag: broad but sub-1-bps residual effect;
- forced-flow exhaustion: broad but sub-1-bps effect;
- cross-sectional dispersion/reversion: positive but only low-single-digit bps, far below four-fill headroom.

This batch did **not** fail because of a universal lack of sample.

Five of the six families had abundant observations. The dominant finding is that raw predictive structure can exist while economic magnitude is far below a realistic structural cost reserve.

C1 is the exception: its frozen mechanism failed primarily through event scarcity.

---

## 9. Selection dispositions

Under the frozen disposition vocabulary:

- C1: `REJECT_SENTINEL`;
- C2: `REJECT_SENTINEL`;
- C3: `REJECT_SENTINEL`;
- C4: `REJECT_SENTINEL`;
- C5: `REJECT_SENTINEL`;
- C6: `REJECT_SENTINEL`.

There are:

- `0 ELIGIBLE_FOR_BATCH`;
- `0 DEFER_SAMPLE_INSUFFICIENT`;
- `0 DEFER_HIGH_SAMPLE_COST`;
- `6 REJECT_SENTINEL`.

Therefore no MDE/block planning is required for C1-C6.

---

## 10. No-rescue rule

Do not:

- lower C1's +50 bps threshold;
- change C2 deviation threshold/reference/horizon after observing output;
- add trend/volatility filters to C2;
- add volume/ADX/MACD/flow/time-of-day filters to C3;
- grid-search C4 lags/leaders/targets;
- add L2 to rescue C5;
- add factors/volatility scaling/asset selection to rescue C6.

Any scientifically different future mechanism must receive a new candidate/experiment ID and prospective nonpromotional design.

---

## 11. Next research phase

Because there are no survivors, SC001 moves to a new **landscape reallocation / next-slate design** stage rather than MDE planning.

Required sequence:

1. append the C1-C6 scoped negative evidence to the Feature Evidence Registry;
2. update the strategy landscape to mark the tested horizon/mechanism cells as covered with negative selection evidence;
3. identify genuinely orthogonal or materially different mechanisms, horizons, or execution structures;
4. explicitly prevent parameter-neighbor repackaging of C1-C6 as "new" candidates;
5. freeze a new non-alpha candidate slate before any new outcome;
6. continue to keep all protected holdout/Confirmation periods closed.

The next slate should be chosen for information value and structural plausibility, not because any neighboring historical asset looked good.
