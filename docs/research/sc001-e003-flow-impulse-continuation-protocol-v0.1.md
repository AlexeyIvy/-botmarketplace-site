# SC001-E003 — Rare Flow-Impulse Continuation Protocol v0.1

Date: 2026-09-15  
Status: **FROZEN BEFORE E003 DATA ACQUISITION / BEFORE ANY E003 OUTPUT**

Branch: `SCALPING RESEARCH / SC001`  
Instrument / venue: OKX `BTC-USDT-SWAP`  
Research role: new independent candidate after terminal E002 standalone-taker failure.

## 1. Independence and no-rescue boundary

E003 is a genuinely new hypothesis. It does not reopen, retune or rescue E002.

E002 remains classified as:

**confirmed predictive microstructure feature; rejected standalone taker strategy.**

E003 may reuse the general scientific lesson that aggressive-flow direction contains information, but it changes the economic mechanism from a bounded 5-second imbalance-ratio trigger to a rare **flow-impulse magnitude** event intended to target moves large enough to plausibly clear taker costs.

SC001 remains independent from R009/R003/R010/S002.

E003 must not use any result to retrospectively alter those branches or E001/E002.

## 2. Why this experiment exists

E002 showed a small but repeatable predictive ordering effect, while executable taker economics failed because the remaining pre-fee edge was only a few hundredths of a basis point versus roughly 10 bps round-trip taker fees.

E003 therefore applies an economics-first principle:

> Do not spend heavy L2 compute on a signal unless a cheap, causal transaction-price screen first shows a gross move large enough to have a plausible path through fee + spread/depth costs.

The new hypothesis is that **rare, unusually large signed aggressive-flow impulses**, normalized by recent market activity, may correspond to information arrival, forced flow or inventory pressure with a substantially larger 30-120 second continuation than the ordinary 5-second TFI effect.

## 3. Research firewall and dates

Only still-Development 2024-Q1 dates that were not part of E002's four-day executable Q1 test are used.

### Discovery

- 2024-03-01 through 2024-03-20 inclusive — 20 UTC days.

### One-time DEV confirmation

- 2024-03-21 through 2024-03-31 inclusive — 11 UTC days.

These periods are frozen before any E003 result is viewed.

Still closed:

- 2024-Q2 OKX for E002;
- all 2024-Q2 E003 data;
- formal Validation 2024-07-01 onward;
- Final 2025-07-01 onward.

No result from March may justify opening later periods unless the frozen E003 promotion gates pass.

## 4. Trade source and UTC construction

Primary discovery/confirmation source is OKX public historical trades for `BTC-USDT-SWAP`.

Use the same qualified UTC-day construction semantics as Q006R:

- exact archive for UTC day D;
- required D+1 neighbor archive where needed by the OKX historical archive grouping;
- admit only rows with timestamps inside `[D 00:00:00.000, D+1 00:00:00.000)` UTC;
- instrument identity must equal `BTC-USDT-SWAP`;
- malformed rows, timestamp reversal or archive-identity failure are fatal.

Archive size and SHA256 must be recorded before the experiment result is interpreted.

## 5. Base 5-second flow variables

Use non-overlapping UTC-aligned 5-second buckets.

For bucket `j`:

- `buy_notional_j` = sum(price × size) for aggressive buys;
- `sell_notional_j` = sum(price × size) for aggressive sells;
- `signed_notional_j = buy_notional_j - sell_notional_j`;
- `total_notional_j = buy_notional_j + sell_notional_j`.

A bucket with zero total notional is invalid and is not a valid decision observation.

No future trade may enter the current bucket statistic.

## 6. New E003 signal: causal flow impulse

The E003 score is intentionally different from E002's bounded TFI ratio.

For every valid current bucket `j`, first compute a causal activity scale from the strictly prior 720 valid buckets:

`activity_scale_j = median(total_notional of prior 720 valid buckets)`

Then:

`FLOW_IMPULSE_j = signed_notional_j / activity_scale_j`

Interpretation:

- sign gives aggressive-flow direction;
- magnitude combines directional imbalance and absolute flow intensity relative to recent market activity;
- unlike bounded TFI, the score is intended to be materially more continuous and to distinguish truly large bursts.

No candidate is allowed until 720 prior valid buckets exist and `activity_scale_j > 0`.

## 7. Causal extreme threshold and tie handling

Primary entry threshold is the nearest-rank `q99.5` of the absolute E003 score using the strictly prior 720 valid E003 scores.

For `N=720`:

`rank_index = ceil(0.995 × 720) - 1`

on the sorted prior `abs(FLOW_IMPULSE)` values.

A candidate requires **strict inequality**:

`abs(FLOW_IMPULSE_j) > threshold_j`

not `>=`.

This strict rule is frozen specifically to prevent the percentile mass-point / threshold-tie behavior observed in E002 from mechanically flooding the tail.

Direction:

- positive impulse -> LONG candidate;
- negative impulse -> SHORT candidate.

Diagnostic thresholds, predeclared but never allowed to rescue primary failure:

- q99.0;
- q99.75.

Primary promotion is always q99.5.

## 8. Turnover / overlap rule

Maximum one open position.

For a given scenario:

- no pyramiding;
- no simultaneous long/short;
- candidates arriving while a position is open are ignored;
- opposite candidates do not reverse early;
- same quantity is closed at exit;
- no overnight carry;
- any candidate whose intended exit would be at or after UTC day end is ineligible.

This is designed to prevent an apparent edge from depending on unrealistically dense overlapping bets.

## 9. Transaction-price economics-first screen

The initial E003 stage deliberately does **not** download L2.

It asks only whether the new mechanism produces a gross move remotely large enough to justify expensive L2 work.

### Primary timing

- signal bucket: 5 seconds;
- decision time: end of the fully closed 5-second bucket;
- primary entry latency: **250 ms**;
- primary holding horizon: **60 seconds**;
- entry proxy: first qualified trade timestamp >= `decision + 250 ms`;
- exit proxy: first qualified trade timestamp >= `decision + 250 ms + 60 s`.

Directional gross edge:

`gross_edge_bps = direction × (exit_price / entry_price - 1) × 10,000`

### Predeclared diagnostics

Latency:

- 500 ms STRESS;
- 1000 ms DIAGNOSTIC.

Holding horizon:

- 30 s DIAGNOSTIC;
- 120 s DIAGNOSTIC.

Diagnostics may not replace a failed primary 60 s / 250 ms result.

## 10. Economics hurdle

Pinned regular-user taker fee remains approximately 5 bps per fill, or roughly 10 bps round trip before spread/depth.

Therefore E003 must show a large gross transaction-price continuation before any L2 acquisition is justified.

Primary coarse hurdle is **12 bps pooled mean gross edge** at q99.5 / 250 ms / 60 s.

The 12 bps hurdle is not a profitability claim. It is only a minimum plausibility screen: roughly 10 bps fee burden plus a small residual margin for spread/depth uncertainty.

A signal with sub-bp gross movement is rejected immediately regardless of statistical significance.

## 11. DEV-DISCOVERY gates — 2024-03-01 to 2024-03-20

Primary q99.5 / 250 ms / 60 s must satisfy all:

1. pooled mean gross edge >= **12 bps**;
2. median of the 20 daily mean gross edges >= **8 bps**;
3. positive daily mean gross edge on at least **14 / 20** days;
4. pooled median gross edge > 0;
5. at least **200 completed non-overlapping trades** across the 20 days;
6. entry/exit trade-proxy completion rate >= 99%;
7. 500 ms stress pooled mean gross edge >= **10 bps**;
8. no source/causality/integrity failure.

If any primary discovery gate fails:

`E003_DISCOVERY_FAIL`

and stop. Do not inspect the frozen March confirmation slice for E003.

## 12. One-time DEV-CONFIRMATION gates — 2024-03-21 to 2024-03-31

Only if Discovery passes, run the exact unchanged primary rule once on the 11 frozen confirmation days.

All must hold:

1. pooled mean gross edge >= **12 bps**;
2. median daily mean gross edge >= **8 bps**;
3. positive daily mean gross edge on at least **8 / 11** days;
4. pooled median gross edge > 0;
5. at least **100 completed non-overlapping trades**;
6. completion rate >= 99%;
7. 500 ms stress pooled mean gross edge >= **10 bps**;
8. no source/causality/integrity failure.

If any fail:

`E003_CONFIRMATION_FAIL`

and stop without L2 acquisition.

## 13. Promotion to L2 execution economics

Only if both Discovery and Confirmation pass:

`E003_GROSS_HURDLE_PASS`

Then and only then may SC001 acquire qualified OKX 400-level L2 for the already-open E003 confirmation dates and freeze a separate taker execution-economics protocol.

That later protocol must include at minimum:

- first qualified L2 state at/after arrival;
- observed spread crossing;
- visible-book VWAP;
- period-appropriate contract/lot/tick metadata;
- 10k USDT primary size;
- depth haircuts;
- 5 bps-per-fill regular-user taker fees;
- funding if crossed;
- net edge after all costs.

No L2 result may change the already-frozen E003 signal definition.

## 14. Role of E002 TFI

E002 TFI is **not** an E003 entry filter in v0.1.

It may be logged as an auxiliary diagnostic only after the primary E003 rule has been frozen, but it may not be used to select, exclude, resize or reverse E003 trades under this version.

If E003 itself becomes economically viable, a later separately frozen experiment may test whether E002 TFI adds incremental value as a filter/ranker.

This separation prevents reusing E002 postmortem information as hidden rescue tuning.

## 15. Multiple-testing ledger

Primary dimensions:

- signal: FLOW_IMPULSE only;
- threshold: q99.5;
- latency: 250 ms;
- horizon: 60 s.

Diagnostics only:

- q99.0 / q99.75;
- 500 / 1000 ms;
- 30 / 120 s.

No new threshold, lookback, activity normalization, side filter, event filter, time-of-day filter, horizon or latency may be added after results are observed under v0.1.

## 16. Stop rules

Do not rescue a failed E003 by:

- substituting q99/q99.75 for q99.5;
- relaxing the 12 bps economics hurdle;
- using lower/VIP fees as justification;
- switching to maker assumptions;
- adding E002 TFI as a post-hoc filter;
- selecting only one side;
- excluding weak days/events;
- altering the 60-second horizon;
- opening Q2, Validation or Final.

A materially different rule requires E004 or a separately justified new version frozen before its own data are inspected.

## 17. Interpretation boundary

Passing the trade-only gross hurdle would **not** establish profitability.

It would establish only that the event magnitude is large enough to justify the next, more expensive falsification layer.

The intended research order is now:

`cheap causal gross hurdle -> unchanged confirmation -> L2/execution economics -> only then later temporal holdout/Validation`

This is the principal methodological lesson imported from E002.
