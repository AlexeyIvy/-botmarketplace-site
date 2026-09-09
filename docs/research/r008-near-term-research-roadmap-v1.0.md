# R008 Near-Term Research Roadmap v1.0

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** E001 promising; E002 independent long-history validation next  
**Research posture:** antifragility-first, falsification-first, no hidden tuning

---

## 1. Current strategic decision

R002 broad-universe SMA120 and Donchian 100/50 are FINAL REDESIGN / NOT PASS for naive complete archive-defined deployment. Do not rescue them with new technical indicators or filters on the same sample.

The frozen BTC SMA120 forward record continues independently as a control.

R001 options remains paused/redesign: true crisis convexity was observed, but tested static/filtered option implementations suffered premium drag and weak late-period validation.

R008 is now the primary active research branch.

---

## 2. R008-E001 result

Frozen architecture:

- 10% permanent BTC;
- 10% dry powder;
- 2.5% tranches at -20/-35/-50/-65% drawdown;
- tranches stay deployed until new closing ATH;
- no leverage, shorts, or technical filters.

E001 Binance 2020-2026 sanity screen:

- R008 full CAGR ~9.01%;
- Max DD ~-17.66%;
- Calmar ~0.51;
- post-2023 CAGR ~10.30%;
- post-2023 Max DD ~-8.38%;
- all eight detected crisis episodes showed positive incremental benefit vs STATIC10;
- completed Level-1 mean Benefit10 ~+0.81%;
- completed Level-3 mean Benefit10 ~+5.53%;
- completed Level-4 Benefit10 ~+9.41%;
- fee stress through 50 bps does not materially change the result.

Formal E001 status:

**PROMISING / ADVANCE TO LONGER-DATA VALIDATION.**

Not historical PASS because the sample is short/event-poor and initial path state is truncated at 2020.

Canonical result:

`docs/research/r008-e001-results-v0.1.md`

---

## 3. Immediate next step — R008-E002

Run the exact unchanged R008 v0.1 architecture on an independent long-history Bitcoin USD reference series.

Frozen E002 source:

- Blockchain.com Charts API `market-price` history;
- all available history;
- sampling disabled;
- UTC daily reference observations.

State initializes from earliest valid source observation, solving the E001 truncated-ATH initialization caveat.

Primary new evidence:

- `PRE_2020_NEW`: 2013-01-01 through 2019-12-31.

Also report:

- FULL_AVAILABLE;
- PRIMARY_LONG from 2013-01-01;
- REPLAY_2020 from 2020 onward;
- POST_2023.

Prospectively add STATIC15 as a fixed midpoint benchmark while retaining CASH, STATIC10, STATIC20 and BTC100.

Protocol:

`docs/research/r008-e002-long-history-validation-protocol-v0.1.md`

Implementation freeze:

`docs/research/r008-e002-implementation-freeze-v0.1.md`

Frozen engine commit:

`aa84072c2e35ac53442d57a6bf57a51966df68b4`

---

## 4. Decision after E002

### If HISTORICAL PASS

Do not go directly to forward/live.

Create R008-E003 implementation-realism experiment:

- real spot holdings and natural weight drift;
- explicit rebalance policy;
- actual turnover;
- realistic spread/slippage;
- cash/stablecoin/custody assumptions;
- venue-specific execution;
- perpetual funding only if a perp implementation is considered.

Then require forward paper testing.

### If REDESIGN

Do not tune the -20/-35/-50/-65 schedule inside v0.1.

Decide whether a genuinely new economic mechanism is justified, such as:

- trend + dry powder as a separately specified architecture;
- carry-funded crisis reserve;
- true option convexity layered on a validated cash-heavy base.

Any such branch requires a new version/protocol before testing.

### If FAIL

Close R008 v0.1. Do not search nearby thresholds or tranche sizes on the same history.

Return to the broader antifragility candidate queue, with priority on economically distinct mechanisms rather than technical-indicator combinations.

---

## 5. Anti-overfitting freeze

Until E002 decision, do not change:

- 10% base BTC;
- 10% opportunity reserve;
- 2.5% tranche size;
- -20/-35/-50/-65 triggers;
- ATH-only reset;
- cash return assumption;
- no leverage/shorts;
- no SMA/Donchian/RSI/MACD/ADX/volatility filter;
- no event-specific discretionary rules.

No new R002 rescue work is active.

---

## 6. Research priority hierarchy

1. **R008-E002 independent long-history validation** — immediate.
2. **BTC SMA120 frozen forward record** — continues independently as control.
3. **R008-E003 implementation realism** — only after E002 historical PASS.
4. **True convexity / carry-financed convexity** — later branch requiring better option/carry data.
5. **R002 broad-universe trend** — closed as FINAL REDESIGN for current implementation.
6. **R001 tested option implementations** — paused/redesign.
7. **New technical-indicator combinations** — not a current priority.
