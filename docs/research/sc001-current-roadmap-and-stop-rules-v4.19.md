# SC001 Current Roadmap and Stop Rules v4.19

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — E009 POSTMORTEM COMPLETE / STRATEGY-PORTFOLIO SELECTION GATE OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.18.md`

## 1. Binding terminal states

E001-E008 remain terminal/closed. E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`.

E009 remains terminal:

`E009_GROSS_FEASIBILITY_FAIL`

Read-only diagnostic completed exact:

`E009_READONLY_POSTMORTEM_PASS`

Results are recorded in:

`docs/research/sc001-e009-readonly-postmortem-results-v0.1.md`

No E009 rescue, holdout, October Confirmation, August repurposing, L2, historical-spec promotion or net-PnL work is authorized.

## 2. E009 postmortem facts

- ranking: OP, DOGE, XRP, UNI, BCH, BTC, ETH, ORDI;
- best instrument OP ~= `+4.379879 bps`;
- worst instrument ORDI ~= `-6.633588 bps`;
- cross-instrument mean std ~= `4.069260 bps`;
- max event-weight ~= `0.173913`;
- max absolute gross-contribution share ~= `0.271617`;
- adequate sample = true;
- cross-market average headroom insufficient = true;
- cross-market breadth insufficient = true;
- pooled robust headroom insufficient = true;
- latency robustness insufficient = true;
- concentration failure = false.

The E009 terminal decision is unchanged.

## 3. New governance finding — strategy-selection concentration

Original SC001 intentionally targeted true/sub-minute scalping. This produced strong coverage of event/5-second/60-second microstructure and short-horizon families.

After E007R1 and E009, however, continuing directly into another candidate without reviewing the strategy universe would risk portfolio-level research concentration.

Binding new framework:

`docs/research/sc001-strategy-selection-time-horizon-and-mechanism-framework-v0.1.md`

This framework does not reopen any prior experiment. It explicitly separates original sub-minute SC001 evidence from a prospective expanded short-horizon search covering seconds through approximately 30 minutes.

## 4. Horizon bands for future candidate sampling

Future candidate cards must identify a horizon band:

- H0: micro / ultra-fast, holding generally <10 s;
- H1: very fast scalp, ~10-60 s;
- H2: fast scalp, ~1-5 min;
- H3: classic multi-minute scalp, ~5-15 min;
- H4: slow scalp / micro-intraday boundary, ~10-30 min.

Every protocol must separately freeze data resolution, signal lookback, decision cadence, latency, expected hold and hard maximum hold. A single “timeframe” label is insufficient.

## 5. Mechanism/execution diversification

Future research must also identify:

Mechanism family:

- M1 order-flow/microstructure prediction;
- M2 liquidity provision/spread capture;
- M3 overshoot/reversion/exhaustion;
- M4 continuation/breakout/short trend;
- M5 relative value/basis/paired convergence;
- M6 cross-asset information transfer;
- M7 event/forced-flow mechanisms.

Execution archetype:

- T1 directional taker;
- T2 passive maker;
- T3 paired/multi-leg;
- T4 hybrid.

Do not over-allocate consecutive research to one `H × M × T` cell.

## 6. Coverage gap after E009

Current evidence is comparatively dense in H0-H2 and M1/M2/M3/M4 short-horizon variants.

Under-covered areas include:

- H3: 1-5 minute signal / 5-15 minute hold;
- H4: 5-10 minute signal / 10-30 minute hold;
- M5 broader multi-asset relative value;
- M6 cross-asset lead/lag;
- M7 forced-flow/exhaustion.

This gap is now part of candidate-selection governance.

## 7. Candidate slate — planning only

No alpha is authorized by this section.

Candidate families retained for non-alpha feasibility cards:

- C1: multi-asset spot/perpetual basis convergence (legacy E006R1 concept), M5/H2-H4/T3;
- C2: multi-minute deviation/VWAP-style mean reversion, M3/H3/T1;
- C3: 5-minute/10-minute continuation or volatility expansion, M4/H3-H4/T1;
- C4: BTC/ETH-to-alt lead/lag, M6/H1-H2/T1;
- C5: large-trade/liquidity-sweep/forced-flow exhaustion, M7+M3/H1-H2/T1;
- C6: cross-sectional short-horizon dispersion/reversion, M5/M6/H3-H4/T3/portfolio;
- C7: future wider-spread passive-maker family, M2/H0-H2/T2/T4, lower immediate priority.

These are candidates, not frozen strategies.

## 8. Change to previous immediate queue

Roadmap v4.18 automatically queued E006R1 after the E009 postmortem.

v4.19 changes only **research ordering governance**, not any observed strategy result:

- E006R1 remains a valid orthogonal candidate;
- it is no longer automatically next by inertia;
- its four-fill fee/legging/borrow complexity must be compared with cheaper under-covered H3/H4 candidates before heavy engineering;
- no future profitability outcome has been observed for any candidate in this new slate.

## 9. Candidate selection gates

Before selecting the next alpha experiment, create non-alpha feasibility cards that cover:

- economic mechanism;
- horizon/mechanism/execution cell;
- conservative fill-count and cost floor;
- plausible gross-move scale/headroom;
- expected event frequency/sample sufficiency;
- historical data availability and causal semantics;
- execution identifiability;
- cross-market breadth potential;
- clean chronology/holdout availability;
- capital/capacity feasibility;
- cheapest falsification path;
- relationship to prior experiments / no-rescue justification.

Do not inspect promotional PnL while preparing these cards.

## 10. Portfolio-level stop rules

- no more than two consecutive new promotional candidates from the same mechanism family;
- do not run another candidate in the same `H × M` cell before sampling an under-covered cell unless it was a pre-registered controlled A/B test;
- a rolling block of roughly 4-6 candidate families should span at least three horizon bands and three mechanism families;
- use cheap feasibility before expensive L2;
- any material parameter/timeframe change after outcome gets a new experiment ID and fresh evidence;
- never select symbols because they were winners in E007R1/E009.

## 11. Current hard gate

**NO NEW ALPHA RUN YET.**

Immediate work is strategy-universe planning only:

1. preserve E009 terminal/postmortem record;
2. prepare compact non-alpha feasibility cards for C1-C6;
3. compare research cost and structural cost headroom;
4. choose one next experiment under the diversification rules;
5. assign/freeze a new experiment ID, exact horizon fields, universe, chronology, cost/headroom gates and tuning budget;
6. only then authorize metadata/data acquisition and alpha stages.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`; nothing here changes their frozen rules or forward clocks.
