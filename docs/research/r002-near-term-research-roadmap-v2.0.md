# R002 Near-Term Research Roadmap v2.0

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Research posture:** falsification-first, no result chasing, no hidden parameter optimization  
**Primary frozen strategy:** R002 v1.0 SMA120, long/cash, daily bars, signal at close t applied to t+1  
**Co-finalist / challenger:** Donchian 100/50, long/cash, daily bars  
**Forward status:** frozen BTC SMA120 forward validation continues independently and must not be reset by research branches

---

## 1. Executive status

The original near-term roadmap (v1.0) has largely been executed. We have moved from candidate discovery into finalist validation.

Current state:

- **R001 options / convexity:** paused in REDESIGN. Crisis convexity exists, but robust positive economics were not validated.
- **R002 SMA120:** remains the frozen primary/control candidate.
- **R002.1 SMA120 + ADX20:** not promoted. It reduced drawdown in places but cut return materially and did not justify the extra rule.
- **R002.2 volatility targeting 15-30%:** not promoted. It reduced risk strongly but reduced participation and absolute return too much on the tested crypto universe.
- **Donchian 100/50:** promoted to co-finalist/challenger after an independent trend-formulation test.
- **Ensembles (50/50, AND, OR):** tested diagnostically. No ensemble has yet justified replacing the two simple finalists.
- **Next critical test:** wide-universe point-in-time validation on the complete Binance archive-defined universe.

The research objective is now narrower and stronger:

> Determine whether SMA120 and Donchian 100/50 survive a much broader point-in-time historical universe without relying on current survivors, a hand-picked subset, or a small number of large successful assets.

---

## 2. Completed evidence chain

### 2.1 R002 BTC historical screen

Frozen family initially tested:

- close > SMA100;
- close > SMA200;
- 252-day momentum > 0;
- SMA50 > SMA200.

Signal was shifted one day; no same-close look-ahead. Cost assumption: 10 bps on exposure changes.

Key result: SMA100/SMA120 area was strong enough to justify further robustness work.

### 2.2 SMA robustness plateau

A broad plateau was observed around roughly SMA110-130. SMA120 was selected instead of the best in-sample SMA110 because it sat in the middle of the stable region and had lower turnover.

This choice remains frozen. Do not retune SMA length unless a future strategy version is explicitly created and its forward clock reset.

### 2.3 Frozen BTC SMA120 historical reference

Historical fully-closed-data reference through 2026-09-07:

- SMA120 CAGR roughly 55.8%;
- Max DD roughly -32.3%;
- BTC buy-and-hold CAGR roughly 42.5%;
- BTC buy-and-hold Max DD roughly -76.7%;
- exposure roughly 57.8%;
- 59 switches.

These are development statistics, not forward results.

### 2.4 Seven-asset cross-asset test

Panel:

- BTCUSDT;
- ETHUSDT;
- SOLUSDT;
- XRPUSDT;
- LTCUSDT;
- ADAUSDT;
- BNBUSDT.

Same SMA120 for every asset, no asset-specific tuning.

Maximum-history result: SMA120 improved both CAGR and Max DD for 5/7 assets. Common-period equal-weight portfolio also improved both return and drawdown versus equal-weight buy-and-hold.

Verdict: **PARTIAL PASS**.

### 2.5 R002.1 SMA120 + ADX20

Pre-specified thresholds: ADX14 > 15 / 20 / 25.

ADX20 was the best portfolio-level compromise in the initial cross-asset experiment, but later finalist comparison showed it did not justify replacing plain SMA120.

Current status: **DO NOT PROMOTE**. Keep only as research history.

### 2.6 Historical/non-survivor subset

A fixed historical subset was built before strategy evaluation using Binance archive history, plus seven current control assets.

Initial collected subset:

- 22 historical/non-survivor candidates;
- 7 current controls;
- 29 total symbols;
- 37,821 daily rows;
- 0 missing / 0 failed downloads.

Important data correction: some Binance archives contain dead post-delisting tails with unchanged price and zero volume. Histories were therefore trimmed after the final positive-volume day.

This revealed that trend following often exits deteriorating tokens much earlier than buy-and-hold.

### 2.7 Point-in-time subset portfolio

The strategy was then tested as a portfolio using only information available at each date:

- symbol becomes eligible only after enough historical observations;
- signal is formed on t and applied to t+1;
- no future delisting information is used;
- inactive sleeves remain in cash;
- disappearing long sleeves can be penalized;
- transaction costs are charged on target-weight changes.

At 10 bps fee and no additional disappearance penalty:

- SMA120 portfolio CAGR roughly 52.25%;
- SMA120 Max DD roughly -51.21%;
- buy-and-hold CAGR roughly 37.83%;
- buy-and-hold Max DD roughly -86.85%.

Even very harsh disappearance penalties did not erase the historical advantage on this subset.

Verdict: **PASS WITH CAVEATS**.

### 2.8 R002.2 volatility targeting

Frozen SMA120 signal with RV20-based no-leverage scaling was tested at 15%, 20%, 25%, and 30% annualized volatility targets.

Baseline stress scenario: 10 bps cost, 25% disappearance penalty.

Approximate results:

- SMA120: CAGR 50.19%, Max DD -51.85%;
- VT15: CAGR 9.52%, Max DD -9.33%;
- VT20: CAGR 12.75%, Max DD -12.29%;
- VT25: CAGR 15.94%, Max DD -15.17%;
- VT30: CAGR 18.98%, Max DD -17.85%.

Conclusion: risk was reduced dramatically, but participation was cut too aggressively. No broad superiority over plain SMA120.

Verdict: **REDESIGN / DO NOT PROMOTE**.

### 2.9 Independent Donchian trend test

Pre-specified family:

- 50/25;
- 100/50;
- 200/100.

Common 200-day warmup, prior-day breakout channels, next-day return application, equal sleeves, 10 bps baseline transaction costs, 25% disappearance penalty.

Common-period reference 2020-07-19 -> 2026-08-31:

- SMA120 CAGR roughly 46.86%, Max DD roughly -54.53%;
- Donchian 100/50 CAGR roughly 46.77%, Max DD roughly -39.78%;
- Buy & Hold CAGR roughly 24.84%, Max DD roughly -89.47%.

Donchian 100/50 also had far lower turnover, roughly 14.7 vs 86.9 for SMA120.

At 50 bps transaction cost:

- Donchian 100/50 CAGR roughly 45.37%;
- SMA120 CAGR roughly 38.75%.

Verdict:

- **Independent trend thesis: PASS**
- **Donchian 100/50: PROMOTE TO CO-FINALIST / CHALLENGER**

### 2.10 Finalist tournament

Unified comparison under the same conditions:

| Candidate | CAGR | Max DD | Worst year | Turnover |
|---|---:|---:|---:|---:|
| SMA120 | ~46.86% | ~-54.53% | ~-28.55% | ~86.94 |
| SMA120 + ADX20 | ~35.80% | ~-40.85% | ~-22.54% | ~89.20 |
| Donchian 100/50 | ~46.77% | ~-39.78% | ~-16.04% | ~14.73 |
| SMA120 + VT30 | ~20.84% | ~-18.56% | ~-10.40% | ~57.18 |

Current finalist roles:

- **Primary/control:** SMA120
- **Co-finalist/challenger:** Donchian 100/50

ADX20 and VT30 are not current finalists.

### 2.11 Finalist ensemble diagnostic

Tested:

- standalone SMA120;
- standalone Donchian 100/50;
- 50/50 capital blend;
- AND;
- OR.

Approximate full-period results:

| Variant | CAGR | Max DD | Turnover |
|---|---:|---:|---:|
| SMA120 | 46.86% | -54.53% | 86.94 |
| Donchian 100/50 | 46.77% | -39.78% | 14.73 |
| 50/50 blend | 47.39% | -46.88% | 50.79 |
| AND | 39.24% | -44.28% | 39.84 |
| OR | 54.45% | -50.72% | 61.83 |

Signal agreement was roughly 80.9% of eligible symbol-days; daily strategy return correlation was roughly 0.934.

Interpretation: both finalists largely express the same medium/long-term trend factor. The 50/50 blend mostly averages their properties; AND cuts participation; OR raises exposure and headline CAGR but does not clearly improve robustness.

Current ensemble verdict:

- 50/50: diagnostic only;
- AND: reject;
- OR: do not promote;
- keep the two simple finalists separate until wide-universe validation is complete.

### 2.12 Important subgroup caveat

On the selected 29-symbol subset, the seven current control assets were very strong, but historical/non-survivor-only aggregate performance was much weaker.

Approximate historical/non-survivor-only CAGR:

- SMA120: about -4.3%;
- Donchian 100/50: about -1.3%;
- 50/50 blend: about -1.4%.

This does not negate the downside-protection evidence on individual dying assets, but it means the high aggregate CAGR of the 29-symbol subset is materially supported by current large assets.

This caveat is the direct reason for the next test: a much wider archive-defined point-in-time universe.

---

## 3. Full Binance archive-defined universe dataset — COMPLETE

### 3.1 Manifest

Binance USD-M monthly 1d archive manifest:

- manifest symbols: **864**;
- monthly archives: **21,383**;
- latest archive month: **2026-08**.

No current-survivor filter was used.

### 3.2 Full daily dataset

Final combined dataset:

- symbols: **864 / 864**;
- rows: **637,705**;
- date range: **2020-01-01 -> 2026-08-31**;
- duplicate `symbol + timestamp`: **0**;
- duplicate `symbol + date`: **0**;
- missing core OHLCV fields: **0**;
- negative volume rows: **0**;
- invalid OHLC relationships: **0**;
- non-positive prices: **0**.

Final file:

`r002_binance_full_universe_daily.csv`

Final state:

`r002_binance_full_universe_state.json`

State version: `unicode-repair-0.2`.

### 3.3 Unicode repair

Four symbols with Chinese Unicode names were initially missing because Python `urllib/http.client` attempted to send non-ASCII URL paths directly.

Missing instruments:

- `币安人生USDT`;
- `我踏马来了USDT`;
- `牛来USDT`;
- `龙虾USDT`.

Repair:

- Unicode URL paths were percent-encoded before HTTP request;
- repair shards were saved under ASCII-safe hashed filenames;
- original symbol names were preserved inside the CSV.

After repair:

- combined symbols: **864 / 864**;
- missing: **0**;
- failed repair targets: **0**.

Trading-day counts for the four repaired symbols:

- `币安人生USDT`: ~316 trading days -> eligible under 200-day warmup;
- `我踏马来了USDT`: ~223 trading days -> eligible;
- `龙虾USDT`: ~174 trading days -> not eligible;
- `牛来USDT`: ~2 trading days -> not eligible.

Therefore the repair was methodologically necessary: two of the four missing instruments can actually enter the wide-universe strategy test.

### 3.4 Expected eligible universe

Using a common 200 genuinely observed trading-day warmup, approximately **641 symbols** are expected to become eligible at some point.

This is not a pre-filter: eligibility must be determined point-in-time inside the backtest.

### 3.5 Data verdict

**FULL-UNIVERSE DATASET: PASS**

The data are now considered sufficient for the next major falsification test.

---

## 4. NEXT STEP — Wide-universe point-in-time finalist validation

**Priority:** immediate / highest.

### 4.1 Research question

Do SMA120 and Donchian 100/50 still show economically meaningful trend-following behavior when tested across the complete Binance archive-defined universe rather than the 29-symbol subset?

### 4.2 Universe construction

Use all 864 archive-defined symbols as input.

For each symbol:

- use only dates that actually exist at that historical time;
- trim any dead zero-volume post-delisting tail after the final positive-volume day;
- require a common **200 observed trading-day warmup** before eligibility;
- do not use future `months_count`, future survival status, final lifetime, later liquidity, or future delisting information to decide eligibility;
- remove the symbol only when real data disappear / trading ends;
- no manual exclusion of poor performers;
- no current-survivor filter.

The 200-day warmup is intentionally common to both finalists so neither gets an earlier start advantage.

### 4.3 Finalists to test

Only:

1. **SMA120**
   - long when close > SMA120;
   - otherwise cash.

2. **Donchian 100/50**
   - long after breakout above prior 100-day high;
   - remain long until close falls below prior 50-day low;
   - breakout channels use only prior data.

No new technical indicator is allowed in this stage.

### 4.4 Timing convention

For both finalists:

- all signals calculated from data known at close t;
- portfolio exposure applied to return t+1;
- no same-close execution assumption;
- no future delisting information.

### 4.5 Portfolio construction

Primary diagnostic:

- equal sleeve across all currently eligible assets;
- signal-off sleeves stay in cash;
- portfolio weights recalculated from the prior close state.

Do not introduce risk parity, volatility weighting, market-cap weighting, or liquidity weighting in the primary test.

Those can only become separate future branches after the basic full-universe result is known.

### 4.6 Transaction-cost stress

Pre-specified grid:

- 5 bps;
- 10 bps baseline;
- 25 bps;
- 50 bps.

Charge costs on absolute portfolio target-weight changes.

### 4.7 Disappearance / delisting stress

Pre-specified penalties on a disappearing long sleeve:

- 0%;
- 25% baseline;
- 50%;
- 100% extreme stress.

Do not choose a penalty after seeing which result looks best.

### 4.8 Required full-period metrics

For each finalist:

- CAGR;
- Max Drawdown;
- annualized volatility;
- Calmar;
- ending multiple;
- total turnover;
- average gross exposure;
- worst calendar year;
- worst calendar quarter;
- worst month;
- worst rolling 12-month return;
- longest drawdown / recovery time if practical;
- average / median number of eligible assets;
- average / median number of active long assets;
- average cash fraction.

### 4.9 Required robustness slices

At minimum:

1. **Full period**.
2. **Late period from 2023-01-01**.
3. **Current-survivor vs historical/non-survivor contribution**, defined using archive presence only for diagnostic attribution, never for portfolio eligibility.
4. **Per-calendar-year returns**.
5. **Cost stress**.
6. **Delisting/disappearance stress**.
7. **Breadth over time** — eligible and active symbol counts.
8. **Concentration diagnostic** — identify whether a small number of assets drive most portfolio P&L.

### 4.10 Decision rule

A finalist advances only if the wide-universe result is economically sensible without depending on a small set of current large winners.

**Strong PASS characteristics:**

- result remains positive / useful on the broader universe;
- drawdown is materially better than broad buy-and-hold or an equivalent eligible-universe passive comparator;
- result survives moderate transaction-cost and disappearance stress;
- late-period behavior is not catastrophically worse;
- contribution is not dominated by only a handful of assets;
- no hidden universe-selection rule is required.

**FAIL / REDESIGN characteristics:**

- advantage disappears when the universe expands;
- result is driven almost entirely by a few current successful assets;
- historical/non-survivor contribution destroys portfolio economics;
- moderate costs erase the effect;
- extreme sensitivity to delisting assumptions;
- implementation requires new filters invented after seeing this result.

### 4.11 Comparator

A point-in-time equal-sleeve passive comparator should be included when technically meaningful:

- every eligible asset receives its sleeve regardless of trend signal;
- same point-in-time eligibility;
- same disappearance assumptions;
- same cost accounting convention where applicable.

This comparator is not a recommendation to hold the universe passively; it is a research control.

---

## 5. What happens after the wide-universe test

### Case A — Both finalists pass

Then:

1. freeze Donchian 100/50 formally for forward tracking;
2. keep SMA120 frozen forward record intact;
3. compare the two finalists on execution realism;
4. decide whether to run both independently or use a very simple capital blend;
5. do not introduce AND/OR unless new independent evidence justifies reopening ensemble research.

### Case B — Only one finalist passes

Promote the surviving strategy and stop spending time trying to rescue the other with extra filters.

### Case C — Neither passes

Do not tune parameters on the same data. Reassess the economic hypothesis and universe construction. Possible next research directions would require a genuinely new hypothesis or new dataset.

---

## 6. Execution realism after signal validation

Only after the wide-universe test is passed should we move into production realism.

### 6.1 Perpetual-futures execution questions

Need to model / collect:

- funding history;
- actual maker/taker fees;
- realistic slippage;
- minimum order / precision rules;
- contract availability through time;
- exchange outages / operational gaps;
- liquidation / margin mechanics if leverage is ever introduced later.

Current finalists remain **unlevered** in research.

### 6.2 Spot execution questions

Need to model:

- independent spot-history cross-check;
- spot trading fees;
- delisting mechanics;
- cash / stablecoin return assumptions;
- stablecoin credit / depeg risk if relevant.

### 6.3 BotMarketplace platform gap analysis

Only after strategy validation:

- verify daily signal engine can express SMA120 and Donchian 100/50 exactly;
- verify no look-ahead in production scheduling;
- verify portfolio-level equal-sleeve allocation;
- verify cost / slippage model;
- verify handling of listing/delisting and missing market data;
- verify forward tracker / paper execution persistence;
- only then implement production integration.

---

## 7. Forward validation rules

### 7.1 SMA120

The existing frozen BTC SMA120 forward clock continues. Do not reset it because of Donchian or full-universe research.

Track:

- previous fully closed daily close;
- SMA120;
- signal;
- paper exposure;
- theoretical / realized execution difference;
- fees and slippage;
- strategy equity;
- BTC buy-and-hold comparator;
- anomalies.

### 7.2 Donchian 100/50

Do **not** start a formal forward clock until the wide-universe validation result is reviewed.

If it passes, freeze the exact 100/50 rule and start its own independent forward record.

---

## 8. Anti-overfitting rules still in force

Do not add now:

- RSI;
- MACD;
- more moving-average filters;
- more ADX conditions;
- fine SMA tuning;
- fine Donchian tuning;
- per-asset parameters;
- machine learning;
- neural networks;
- optimizer-selected thresholds;
- leverage;
- shorting;
- options overlay;
- intraday alpha;
- order-book features;
- social sentiment;
- on-chain filters.

Reason: the next unknown is broad-universe robustness, not signal complexity.

---

## 9. Current decision hierarchy

1. **SMA120** — frozen primary/control; continue forward validation.
2. **Donchian 100/50** — co-finalist/challenger; must pass full-universe PTI validation before formal forward freeze.
3. **50/50 SMA/Donchian blend** — diagnostic only, not current production candidate.
4. **ADX20 branch** — not promoted.
5. **Vol-target branch 15-30%** — redesign only, not promoted.
6. **R001 options** — paused in redesign.
7. **New technical indicators** — explicitly postponed.

---

## 10. Immediate execution order from the next chat

1. Load / inspect `r002_binance_full_universe_daily.csv` and `r002_binance_full_universe_state.json`.
2. Confirm full-universe dataset invariants: 864 symbols, 637,705 rows, no duplicate symbol-date, no core OHLCV corruption.
3. Implement / run a single reproducible **wide-universe point-in-time finalist engine**.
4. Use common 200-day point-in-time warmup.
5. Compare SMA120, Donchian 100/50, and point-in-time passive comparator.
6. Run baseline: 10 bps cost + 25% disappearance penalty.
7. Run cost stress: 5/10/25/50 bps.
8. Run disappearance stress: 0/25/50/100%.
9. Report full-period and post-2023 metrics.
10. Report breadth and concentration diagnostics.
11. Make a strict PASS / FAIL / REDESIGN decision for each finalist.
12. Update this roadmap after that decision.

---

## 11. Plain-language summary

We are no longer trying to discover a better indicator.

We have two simple trend-following finalists that looked strong on BTC, multiple large crypto assets, and a smaller historical/non-survivor subset. Their signals are highly correlated, so combining them does not yet appear to create a genuinely new source of edge.

The remaining important uncertainty is whether those good historical results survive a much broader market universe that includes hundreds of contracts, including weak, short-lived, and historical ones.

The complete Binance archive-defined dataset is now ready. The next test should therefore try to **break** SMA120 and Donchian 100/50 on that wider universe. If they survive, we can justify moving from signal research toward forward validation and execution realism. If they fail, we should not rescue them by adding more indicators.