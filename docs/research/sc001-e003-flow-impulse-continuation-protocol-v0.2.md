# SC001-E003 — Rare Flow-Impulse Continuation Protocol v0.2

Date: 2026-09-15  
Status: **FROZEN BEFORE E003 DATA ACQUISITION / BEFORE ANY E003 OUTPUT**

Supersedes: `sc001-e003-flow-impulse-continuation-protocol-v0.1.md`.

Reason for v0.2: pre-acquisition implementation review identified that constructing a complete UTC day for 2024-03-31 with the previously qualified OKX UTC-stitch method may require the D+1 archive dated 2024-04-01. That would open raw Q2 data even though the E003 protocol explicitly keeps Q2 closed. No E003 market-data body had been downloaded and no E003 output had been observed before this correction.

Therefore the confirmation slice is shortened by one day so all required exact/neighbor source archives remain within 2024-Q1.

All economic, signal, threshold, latency, horizon and stop rules from v0.1 remain unchanged unless explicitly stated below.

## 1. Independence and no-rescue boundary

E003 is a genuinely new hypothesis. It does not reopen, retune or rescue E002.

E002 remains:

**confirmed predictive microstructure feature; rejected standalone taker strategy.**

SC001 remains independent from R009/R003/R010/S002.

## 2. Economic hypothesis

Rare, unusually large **signed aggressive-flow impulses**, normalized by recent market activity, may represent information arrival, forced flow or inventory pressure that continues for tens of seconds with a gross move large enough to plausibly clear taker costs.

This is materially different from E002's bounded 5-second TFI-ratio standalone trigger.

## 3. Frozen research dates

### DEV-DISCOVERY

- 2024-03-01 through 2024-03-20 inclusive — 20 UTC days.

### One-time DEV-CONFIRMATION

- 2024-03-21 through 2024-03-30 inclusive — 10 UTC days.

The required source archive set therefore ends at 2024-03-31, still inside Q1.

Closed:

- all 2024-Q2 raw market-data bodies;
- E002 Q2 holdout;
- formal Validation;
- Final.

## 4. UTC trade construction

Use OKX public historical `BTC-USDT-SWAP` trades with the same qualified Q006R UTC stitching semantics:

- exact archive for day D;
- D+1 neighbor archive where required by OKX historical grouping;
- admit only target UTC-day rows;
- instrument identity, timestamps and row structure must pass integrity checks;
- archive byte size and SHA256 must be recorded.

No E003 alpha/P&L is calculated during acquisition.

## 5. Five-second flow variables

For each non-overlapping UTC-aligned 5-second bucket j:

- `buy_notional_j` = aggressive-buy price × size sum;
- `sell_notional_j` = aggressive-sell price × size sum;
- `signed_notional_j = buy_notional_j - sell_notional_j`;
- `total_notional_j = buy_notional_j + sell_notional_j`.

Zero-total buckets are invalid decisions.

## 6. Primary E003 score

From the strictly prior 720 valid buckets:

`activity_scale_j = median(total_notional_prior_720)`

Then:

`FLOW_IMPULSE_j = signed_notional_j / activity_scale_j`

No candidate is possible before 720 prior valid buckets and a positive activity scale exist.

This score combines aggressive-flow direction with absolute intensity relative to recent activity and is intentionally more continuous than E002 TFI.

## 7. Causal tail threshold

Primary threshold: nearest-rank q99.5 of strictly prior 720 valid `abs(FLOW_IMPULSE)` values.

`rank_index = ceil(0.995 × 720) - 1`

Candidate rule uses strict inequality:

`abs(FLOW_IMPULSE_j) > threshold_j`

Direction = sign of FLOW_IMPULSE.

Diagnostics only, never rescue:

- q99.0;
- q99.75.

## 8. Position / turnover rule

For each scenario:

- maximum one open position;
- no pyramiding;
- no simultaneous long/short;
- ignore new candidates while open;
- no early reversal;
- no overnight carry;
- candidate ineligible if intended exit reaches or exceeds UTC day end.

## 9. Economics-first trade-price screen

Initial E003 stage uses trade data only and does not download L2.

Primary timing:

- decision = end of closed 5-second signal bucket;
- latency = 250 ms;
- horizon = 60 s;
- entry proxy = first qualified trade at/after decision + 250 ms;
- exit proxy = first qualified trade at/after decision + 250 ms + 60 s.

Directional gross edge:

`direction × (exit_price / entry_price - 1) × 10,000 bps`

Diagnostics only:

- latency 500 ms stress;
- latency 1000 ms diagnostic;
- horizon 30 s diagnostic;
- horizon 120 s diagnostic.

Diagnostics cannot replace failed primary results.

## 10. Coarse economics hurdle

Pinned regular-user taker burden is about 10 bps round trip before spread/depth.

Primary q99.5 / 250 ms / 60 s must therefore show gross movement large enough to justify L2 work.

Minimum coarse hurdle:

**pooled mean gross edge >= 12 bps.**

This is only a plausibility screen, not profitability proof.

## 11. DEV-DISCOVERY gates — 20 days

All must hold for q99.5 / 250 ms / 60 s:

1. pooled mean gross edge >= 12 bps;
2. median of 20 daily mean gross edges >= 8 bps;
3. positive daily mean gross edge on at least 14/20 days;
4. pooled median gross edge > 0;
5. at least 200 completed non-overlapping trades;
6. proxy completion rate >= 99%;
7. 500 ms stress pooled mean gross edge >= 10 bps;
8. no source/causality/integrity failure.

If any fail: `E003_DISCOVERY_FAIL` and confirmation remains unopened.

## 12. One-time DEV-CONFIRMATION gates — 10 days

Only if Discovery passes, run exact unchanged rules on 2024-03-21 through 2024-03-30.

All must hold:

1. pooled mean gross edge >= 12 bps;
2. median daily mean gross edge >= 8 bps;
3. positive daily mean gross edge on at least 7/10 days;
4. pooled median gross edge > 0;
5. at least 90 completed non-overlapping trades;
6. proxy completion rate >= 99%;
7. 500 ms stress pooled mean gross edge >= 10 bps;
8. no source/causality/integrity failure.

If any fail: `E003_CONFIRMATION_FAIL` and stop without L2 acquisition.

## 13. L2 promotion

Only Discovery + Confirmation PASS yields:

`E003_GROSS_HURDLE_PASS`

Only then may SC001 acquire 400-level OKX L2 for the already-open E003 confirmation dates and freeze a separate executable taker-economics protocol including spread, visible-book VWAP, depth haircuts, fee ledger, 10k primary size, funding and net edge after all costs.

## 14. E002 TFI boundary

E002 TFI is not an E003 v0.2 entry filter.

It may not select, veto, resize or reverse E003 trades under this protocol. A later incremental-value experiment is allowed only after a base strategy is independently economically viable and must be separately frozen.

## 15. Multiple-testing ledger

Primary:

- score: FLOW_IMPULSE;
- threshold: q99.5;
- latency: 250 ms;
- horizon: 60 s.

Diagnostics only:

- q99.0 / q99.75;
- 500 / 1000 ms;
- 30 / 120 s.

No new side/event/time-of-day filter, threshold, normalization, lookback, horizon or latency may be introduced after output is observed.

## 16. Stop rule

No rescue via:

- alternate diagnostic threshold;
- relaxed 12 bps hurdle;
- lower/VIP fees;
- maker assumptions;
- E002 post-hoc filtering;
- one-sided selection;
- event/day exclusions;
- horizon changes;
- Q2 / Validation / Final exploration.

A materially different hypothesis requires a new experiment/version frozen before its own data are inspected.

## 17. Research order

`Q1 trade acquisition -> Discovery gross hurdle -> unchanged Confirmation -> only if PASS, L2 execution economics -> later protected temporal validation`

This is the economics-first workflow learned from E002.
