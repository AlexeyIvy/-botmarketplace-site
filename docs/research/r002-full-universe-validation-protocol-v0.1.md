# R002 Full-Universe Validation Protocol v0.1

**Project:** BotMarketplace strategy research  
**Objective:** validate the two R002 finalists on a much broader archive-defined Binance USD-M universe without introducing new signal parameters.  
**Finalists under test:**

1. **R002 v1.0 — SMA120**
2. **R003 challenger — Donchian 100/50**

This phase is not intended to discover a better indicator. It is intended to reduce uncertainty about whether the strong results seen on the earlier 29-asset subset survive a much wider historical universe.

---

## 1. Why this test is needed

The earlier finalist audit showed that aggregate performance on the 29-asset subset was materially helped by the seven current large/liquid control assets. Historical/non-survivor assets were much weaker as a group.

Therefore the next highest-value question is not whether another indicator can improve the backtest. The question is whether the two simple trend-following finalists remain economically useful when the tradable universe is made much broader and less hand-selected.

---

## 2. Universe definition

The download universe is defined mechanically from the previously collected Binance public USD-M monthly 1d archive manifest.

**Rule:** download every symbol that appears in the manifest.

No symbol is excluded because of:

- current listing status;
- future lifetime;
- number of months eventually survived;
- historical performance;
- whether it is a current large-cap asset;
- whether it was previously selected into the 29-asset research subset.

This avoids introducing a new full-history lifetime filter such as “at least 12 months,” which would itself use future information and could exclude contracts that survived just long enough to become strategy-eligible.

The manifest snapshot contains **864 symbols** and **21,383 symbol-month 1d archives**.

---

## 3. Important domain caveat

The archive-defined Binance USD-M universe contains more than traditional crypto tokens in later years, including tokenized or synthetic exposures linked to equities, indices, commodities, or other non-crypto underlyings.

Therefore:

- the first broad-universe result is an inference about the **archive-defined Binance USD-M tradable universe**;
- it should not automatically be described as a pure “crypto-only” universe;
- no manual ticker-by-ticker classification will be introduced before results are observed;
- if a crypto-only slice is later required, it must use an objective metadata source or a pre-specified classification rule rather than manual hindsight filtering.

---

## 4. Data collection rules

Source: Binance public data archive, USD-M futures, monthly `1d` klines.

The collector:

- reads `r002_binance_um_1d_manifest.csv`;
- downloads every manifest symbol;
- writes one atomic per-symbol shard;
- resumes safely after Android/Pydroid interruption;
- reuses compatible shards from the earlier 29-symbol subset when present;
- normalizes millisecond/microsecond timestamps defensively;
- deduplicates by `open_time_ms` within each symbol;
- produces one combined dataset plus a state/checkpoint file.

Expected outputs:

- `r002_binance_full_universe_daily.csv`
- `r002_binance_full_universe_state.json`

---

## 5. Point-in-time cleaning and eligibility

The strategy test must not use future listing or delisting information in signal formation.

For each symbol:

1. Sort by date and remove duplicate dates.
2. Require positive prices.
3. Treat zero-volume frozen archive tails after the last genuinely traded day as non-tradable artefacts and trim them.
4. A symbol becomes strategy-eligible only after **200 genuinely observed daily bars** are available. The 200-day common warmup is used so SMA120 and Donchian 100/50 are compared from the same eligibility clock.
5. Before eligibility, the symbol contributes nothing to the portfolio.
6. After the final real trading day, the symbol leaves the tradable universe without advance knowledge.
7. If a long position disappears between two dates, apply the pre-specified delisting stress assumption.

---

## 6. Frozen strategy specifications

### 6.1 SMA120

Signal formed on day `t`:

`long = close_t > SMA120_t`

Signal is applied to the next available day return. No same-close execution.

### 6.2 Donchian 100/50

Entry:

- long when close breaks above the highest high of the prior 100 days.

Exit:

- cash when close falls below the lowest low of the prior 50 days.

The breakout channels are shifted by one full day so the signal never uses the current day's high/low inside the channel.

No parameter changes are allowed in this phase.

---

## 7. Portfolio construction

Primary portfolio:

- each currently eligible symbol receives one equal capital sleeve `1/N`;
- if the strategy signal is long, that sleeve is invested;
- if the signal is off, that sleeve remains cash;
- no leverage;
- cash return = 0 in the signal-validation diagnostic.

This keeps universe construction and signal quality separate from later risk-budget optimization.

---

## 8. Execution stress assumptions

Primary cost:

- 10 bps per absolute portfolio weight change.

Cost stress:

- 25 bps;
- 50 bps.

Primary delisting penalty:

- 25% applied to any disappearing long sleeve.

Additional stress:

- 0%;
- 50%;
- 100%.

The purpose is not to estimate exact delisting recovery. The purpose is to test whether the result depends on optimistic treatment of disappearing contracts.

---

## 9. Required diagnostics

For both SMA120 and Donchian 100/50 report:

- CAGR;
- Max Drawdown;
- annualized volatility;
- Calmar ratio;
- worst calendar year;
- worst rolling 12-month return;
- worst month;
- worst quarter;
- turnover;
- average invested exposure;
- ending multiple;
- drawdown recovery time;
- number of eligible assets through time;
- number of active long assets through time;
- cash fraction through time;
- late-period performance from 2023-01-01;
- cost stress;
- delisting stress.

Also report concentration diagnostics:

- contribution by symbol;
- top 5 contributors as a fraction of total gains;
- bottom 5 contributors;
- performance excluding the top contributor;
- performance excluding the top 5 contributors.

This is necessary because a broad universe can still look strong if a small number of extreme winners dominate aggregate results.

---

## 10. Ensemble status

No new ensemble optimization is allowed during this broad-universe phase.

The earlier diagnostics showed:

- 50/50 blend is a reasonable compromise but not clearly superior;
- AND sacrifices too much participation;
- OR increases exposure and headline CAGR but does not provide a clearly better downside profile;
- SMA120 and Donchian are highly correlated because both capture the same underlying trend factor.

Therefore broad-universe validation is run on the **two finalists separately** first.

Only if both survive may a simple 50/50 blend be rechecked as a final implementation option.

---

## 11. Decision rules

### PASS

A finalist advances if:

- it remains economically positive on the broad point-in-time universe;
- downside is materially better than broad-universe buy-and-hold;
- the result survives 25–50 bps cost stress;
- delisting stress does not reverse the conclusion;
- late-period behavior remains economically sensible;
- results are not dominated by one or two assets;
- no hidden full-history universe filter is required.

### WEAK PASS / REDESIGN

Use this if:

- aggregate results remain positive but are highly concentrated;
- downside improvement survives but return advantage becomes weak;
- performance is highly sensitive to execution assumptions.

### FAIL

Reject the candidate for broad-universe use if:

- CAGR becomes economically unattractive or negative;
- drawdown advantage largely disappears;
- modest cost/delisting stress erases the edge;
- performance is explained mainly by a few hindsight winners;
- the late period materially contradicts the full sample.

---

## 12. Research freeze during this phase

Do not add:

- RSI;
- MACD;
- ADX changes;
- volatility-target changes;
- leverage;
- shorts;
- machine learning;
- asset-specific parameters;
- new breakout windows;
- optimized portfolio weights.

The purpose of this step is falsification of the two finalists, not improvement of their historical backtests.

---

## 13. Immediate execution sequence

1. Collect the full archive-defined daily universe using the crash-safe Android downloader.
2. Validate the resulting dataset: symbol count, row count, duplicate dates, timestamp consistency, OHLC validity, zero-volume tails, gaps, and coverage by year.
3. Build the common 200-day point-in-time eligibility panel.
4. Run SMA120 and Donchian 100/50 under identical assumptions.
5. Run cost and delisting stress.
6. Run late-period and contribution/concentration diagnostics.
7. Produce a final PASS / WEAK PASS / FAIL verdict for each finalist.
8. Only then decide whether to retain one finalist, both finalists, or a simple 50/50 blend for forward/paper execution.
