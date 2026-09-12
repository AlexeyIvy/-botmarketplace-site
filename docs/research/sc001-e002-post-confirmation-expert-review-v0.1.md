# SC001-E002 Post-Confirmation Expert Review v0.1

Status: **POST-HOC DIAGNOSTIC REVIEW — DOES NOT ALTER FROZEN E002/CONFIRMATION VERDICTS**

Parent: `SC001-E002 — Aggressive Trade-Flow Continuation Screen`

## 1. Confirmed frozen result

E002 remains `PROMISING_SCREEN` with `CONFIRMATION_PASS` on the 10 reserved DEV-CONFIRMATION days. No strategy P&L, L2 execution profitability, formal Validation, or Final result has been opened.

## 2. Combined DEV diagnostic view

Combining the already-opened 15 DEV-DISCOVERY days and 10 DEV-CONFIRMATION days for post-hoc diagnosis only:

- 25 / 25 daily Spearman values are positive at 100 ms;
- median daily Spearman at 100 ms: `0.0886824858640126`;
- median daily Spearman at 250 ms: `0.0816467109026996`;
- median daily Spearman at 500 ms: `0.0744182814410974`;
- median extreme-decile spread at 100 ms: `0.2582266076421903` bps;
- median extreme-decile spread at 250 ms: `0.2425249127418278` bps;
- median extreme-decile spread at 500 ms: `0.2175500283300316` bps.

A literal 25/25 sign-test under independent 50/50 Bernoulli days would be extremely small, but the days are not guaranteed IID and this value must not be presented as a universal false-positive probability. Quarter/day-block robustness is more appropriate.

All five quarter medians from 2023-Q2 through 2024-Q2 are positive. A very conservative 5/5 quarter-sign diagnostic corresponds to `1/32 = 0.03125` under an independent 50/50 quarter-sign null, again only as a diagnostic.

## 3. New robustness observations

### Latency decay behaves sensibly

- 22 / 25 days show monotonically non-increasing Spearman from 100 -> 250 -> 500 ms.
- 23 / 25 days show monotonically non-increasing extreme-decile spread over the same latency sequence.

This is reassuring because a predictive effect that became stronger randomly as simulated latency increased would be more suspicious. It still does not prove executable alpha.

### Confirmation attenuation is real but not collapse

Discovery median 100 ms Spearman: `0.12936691569403583`.
Confirmation median: `0.07890232206324495`.
Retention: approximately `60.99%`.

The attenuation argues against treating the discovery magnitude as the production expectation. The confirmation still cleared the pre-frozen 50% retention gate.

### Tail separation strengthened while rank correlation weakened

Discovery median 100 ms extreme spread: about `0.2511` bps.
Confirmation median: about `0.2777` bps, roughly 10.6% higher.

At the same time, Spearman declined. This suggests a potentially nonlinear effect: broad monotonic ranking weakened, while the extreme tails remained economically separated. This is a post-hoc observation only and must not be used to promote a decile threshold under E002.

### The signal is not a high-win-rate classifier

Across the 25 already-opened DEV days, the median extreme-decile directional hit rate at 100 ms is below 50%. On confirmation alone it is about 49.8%.

Positive rank correlation plus positive tail mean spread can coexist with a near-50% hit rate because the feature may predict return magnitude/ranking rather than the modal sign and because many 5-second price responses are zero/small. A production rule should not be marketed or optimized as a high-accuracy direction classifier without a separate experiment.

## 4. Balanced-stratum view

The 25 DEV days are exactly balanced across five frozen strata (5 observations each): CPI, NFP, FOMC, ordinary weekday, ordinary weekend.

100 ms median daily Spearman by stratum:

- CPI: `0.0816130861937552`
- NFP: `0.1293669156940358`
- FOMC: `0.0710990051202889`
- ordinary weekday: `0.0886824858640126`
- ordinary weekend: `0.136788624948349`

All are positive. Differences between strata are post-hoc and underpowered; no event or weekend/weekday filter may be created from these numbers under E002.

The balanced sample intentionally overweights macro-event days relative to the natural market calendar. Combined averages are research-design averages, not natural-frequency performance estimates.

## 5. Economic scale — strongest criticism

The confirmation median top-minus-bottom transaction-price response is only about `0.2777` bps. If top and bottom extreme-decile signals were traded symmetrically, the rough gross directional response scale per round-trip observation is on the order of half the spread, about `0.139` bps before executable bid/ask, taker fees, depth consumption, slippage, and impact.

This is the strongest argument against premature optimism. A statistically real signal may still be economically unusable as a taker strategy.

No exact break-even claim is made yet because historical fee assumptions and same-venue L2 execution costs are not yet qualified.

## 6. Potential microstructure artifacts that remain unresolved

1. **Transaction-price bounce** — E002 labels use transaction prices, not mid/microprice or executable opposite-side quotes. Bid/ask bounce can affect 5-second responses.
2. **Target-to-next-trade lag** — entry/exit references use the first transaction at or after target time. Actual target-to-print delay was not recorded in E002 and should be measured in the same-venue stage.
3. **Ex-post daily deciles** — extreme deciles are diagnostics based on each full day's score distribution and are not directly deployable live thresholds.
4. **Same-venue requirement** — Binance predictive evidence cannot establish OKX execution alpha.
5. **Historical derivative units** — OKX trade/L2 sizes for SWAP are in contracts. The TFI ratio can be replicated without needing contract value if the multiplier is constant within the instrument because the common scale cancels; capital sizing and P&L still require period-appropriate contract metadata.

## 7. Exploratory activity relationship

Across the 25 DEV days at 100 ms, daily aggregate-trade row count is negatively associated with daily Spearman and positively associated with extreme-tail spread in a simple post-hoc correlation diagnostic. This may indicate that high-activity regimes weaken broad rank monotonicity while increasing tail response magnitude.

This is exploratory only, based on a small stratified sample, and is explicitly forbidden as a tuning/filter input for E002. Any activity-regime rule would require a new experiment ID.

## 8. Revised next-step decision

Do **not** open formal Validation and do **not** jump directly into multi-day OKX L2 downloads.

Use a cheaper falsification ladder:

1. qualify OKX tick-trade historical acquisition on a fixed 2024-Q1 five-day set (NFP, weekend, FOMC, weekday, CPI), metadata/schema first;
2. if qualified, repeat the unchanged 5s TFI predictive screen on those five OKX days using taker side from OKX trades;
3. only if same-venue predictive direction is supported, perform a full-day OKX L2 engineering/economic pilot on the same predeclared Q1 layer;
4. keep 2024-Q2 OKX trade/L2 data unopened as a same-venue confirmation layer until the Q1 same-venue candidate/execution model is frozen;
5. keep formal Validation (2024-07 onward) and Final unopened.

This sequence is more resource-efficient and more resistant to cross-venue false confidence than immediately buying the cost of full L2 processing.
