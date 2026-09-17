# SC001 — Strategy Selection, Time-Horizon & Mechanism Diversification Framework v0.1

Date: 2026-09-17  
Status: **WORKING GOVERNANCE FRAMEWORK — FREEZE BEFORE NEXT ALPHA FAMILY**  
Scope: `SCALPING RESEARCH / SC001`

## 1. Why this framework is needed

SC001 originally asked a deliberately narrow question: whether a credible **true/sub-minute BTC scalping edge** exists. That narrow scope explains why much of E002-E009 concentrated on trade/L2 microstructure, five-second grids, sub-minute signals, sixty-second displacements, short inventory windows and latency-sensitive execution.

That was not an error at project inception. However, after E007R1 and E009, continuing to choose candidates one-by-one without an explicit portfolio-level sampling rule creates a new risk: **research concentration**. We can be rigorous inside each experiment while still spending too much total effort on neighboring strategy families.

Therefore SC001 now separates two questions:

1. **Original sub-minute SC001 evidence** — immutable historical record; terminal decisions stay terminal.
2. **Expanded short-horizon search** — a prospective extension covering seconds through approximately 30 minutes, without pretending that this broader mandate was the original one.

The expansion is governance, not rescue. No old FAIL is reopened.

## 2. “Timeframe” is not one number

A strategy must never be classified only as “5-second”, “5-minute” or “10-minute”. At least six time dimensions must be frozen separately:

1. **market-data resolution** — event/tick, 100 ms, 1 s, 5 s, 1 min, etc.;
2. **signal aggregation/lookback** — how much history defines the signal;
3. **decision cadence** — how often a new decision can be made;
4. **entry latency budget** — time from causal decision to executable order arrival;
5. **expected holding horizon** — where the economic mechanism is expected to resolve;
6. **hard maximum hold** — forced strategy exit horizon.

Example: a strategy may use a 5-minute volatility estimate, make decisions every 5 seconds, and hold for 90 seconds. Calling it simply a “5-minute strategy” would be misleading.

Every future SC001 candidate card/protocol must state all six dimensions before outcome-bearing data are inspected.

## 3. Prospective horizon bands

The expanded SC001 search should cover distinct holding/signal horizons rather than repeatedly sampling one band.

### H0 — micro / ultra-fast

Typical signal information: event-level to ~5 s.  
Typical holding horizon: sub-second to ~10 s.  
Examples of mechanism classes: microprice/order-flow imbalance, cross-venue lead/lag, immediate liquidity sweep response.

Execution dominates economics. Taker fees, spread, latency and queue state can easily exceed alpha.

### H1 — very fast scalp

Typical signal aggregation: ~1-30 s.  
Typical holding horizon: ~10-60 s.

Examples: aggressive-flow continuation/exhaustion, passive spread capture, post-sweep reversal.

### H2 — fast scalp

Typical signal aggregation: ~15 s-2 min.  
Typical holding horizon: ~1-5 min.

Examples: displacement/reversal, short-lived basis convergence, liquidation aftershock, short momentum bursts.

### H3 — classic multi-minute scalp

Typical signal aggregation: ~1-5 min.  
Typical holding horizon: ~5-15 min.

Examples: VWAP/median deviation mean reversion, multi-minute momentum/breakout, volume-shock continuation/reversal.

### H4 — slow scalp / micro-intraday boundary

Typical signal aggregation: ~5-10 min.  
Typical holding horizon: ~10-30 min.

Examples: 5/10-minute trend/breakout, cross-sectional dispersion/reversion, slower relative-value convergence.

H4 must be labeled **expanded short-horizon** rather than silently redefined as original sub-minute SC001. Positions expected to persist materially beyond ~30 minutes belong in another intraday research program, not in core scalping.

## 4. Mechanism families to diversify across

Time diversification alone is insufficient. Two strategies on different bar lengths can still be the same economic bet. Future candidate sampling should also rotate across mechanism families.

### M1 — order-flow / microstructure prediction

Examples: taker imbalance, microprice, signed flow, order-book imbalance, lead/lag.

### M2 — liquidity provision / spread capture

Examples: passive maker, queue-aware quoting, adverse-selection-controlled market making.

### M3 — overshoot / mean reversion / exhaustion

Examples: displacement reversal, sweep exhaustion, VWAP deviation reversion, liquidation aftershock.

### M4 — continuation / breakout / short trend

Examples: flow impulse continuation, volatility expansion, range/compression breakout, multi-minute trend continuation.

### M5 — relative value / basis / paired convergence

Examples: spot-perpetual basis, cross-perpetual dispersion, venue spread convergence. Requires explicit multi-leg/legging/borrow/funding economics.

### M6 — cross-asset information transfer

Examples: BTC/ETH impulse leading selected alt perpetuals, market-index residual moves, leader/follower relationships.

### M7 — event/forced-flow mechanisms

Examples: liquidation bursts, large trade/sweep events, funding/settlement micro-events when causally observable. Event definitions must be prospective and not hand-picked from profitable days.

A mechanism may map to more than one horizon, but repeated experiments in the same `H × M` cell should not crowd out unexplored cells.

## 5. Execution archetypes are a third diversification axis

Future research should deliberately include different execution structures:

- **T1 directional taker** — usually two taker fills per round trip;
- **T2 passive/maker** — lower explicit fee potential but queue/adverse-selection uncertainty;
- **T3 paired/multi-leg** — relative-value exposure but typically four or more fills and leg risk;
- **T4 hybrid** — e.g. maker entry/taker risk exit, only when economically justified prospectively.

A strategy that requires four taker fills faces a structurally different cost hurdle from a two-fill directional scalp. Research priority must account for this before expensive implementation.

## 6. What the completed experiments reveal about coverage

### E001

Hourly mean-reversion failed. It is useful historical evidence but lies outside the original true/sub-minute objective and does not fill the 1-15 minute scalping gap.

### E002

5 s flow / 5 s horizon microstructure prediction. Strong evidence that M1/H0-H1 was examined; standalone taker economics failed.

### E003 / E004 / E005

Short-horizon continuation/breakout-related families were explored and failed their frozen gates. They add M4 evidence but do not provide a systematic survey of 5-minute/10-minute strategies.

### E006

Spot/perpetual basis convergence introduced M5, but BTC evidence suffered from event scarcity/economic headroom. Multi-asset replication remains conceptually useful but is cost-heavy because paired taker execution can require four fills.

### E007 / E007R1

A 60-second displacement reversal with up-to-10-minute resolution/hold logic produced an event-level effect but inadequate cross-market breadth/headroom.

### E008

Passive-maker/spread capture covered M2/H1 and showed that BTC spread economics were poor while also teaching important execution-model lessons.

### E009

A volatility-normalized 60-second reversal provided a disciplined new M3 normalization test but terminally failed on fresh September evidence.

### Coverage conclusion

The program has **good coverage of sub-minute microstructure and short event-driven strategies**, but comparatively weak systematic coverage of:

- H3: 1-5 minute signal / 5-15 minute hold;
- H4: 5-10 minute signal / 10-30 minute hold;
- cross-asset information transfer (M6);
- broader multi-asset relative-value structures (M5 beyond BTC);
- forced-flow/event-exhaustion mechanisms (M7).

This is now an explicit research gap.

## 7. Candidate selection gates before spending compute

A candidate should not enter promotional testing merely because it sounds plausible. Before alpha, create a candidate card and check the following.

### G1 — economic mechanism

State why the edge could exist and who/what economically pays for it: inventory pressure, forced flow, delayed information transmission, liquidity demand, behavioral overshoot, basis dislocation, etc.

If the story is merely “indicator X crossed Y”, priority is low unless an economic mechanism is independently stated.

### G2 — cost headroom plausibility

Before detailed L2 work, estimate the unavoidable cost structure:

- number of fills;
- maker/taker fee floor;
- spread/depth exposure;
- borrow/funding where applicable;
- expected latency sensitivity;
- likely move scale at the intended horizon.

The strategy must have a plausible route to an edge materially larger than cost/model uncertainty. Do not spend weeks building a simulator for a mechanism whose typical move is smaller than the fee floor.

### G3 — sample sufficiency

Estimate event frequency before profitability. Candidate should plausibly produce enough independent instrument-day/calendar-day evidence for a meaningful test.

Rare-event strategies are allowed, but then they require a longer/multi-asset chronology rather than pretending a handful of events is sufficient.

### G4 — causal observability

Every signal input must be historically observable at decision time. Required timestamp semantics and feeds must exist.

### G5 — execution identifiability

Choose the simplest valid kernel for the mechanism. If profitability depends on unobservable FIFO/hidden-liquidity assumptions, execution-model uncertainty must be explicit and may lower priority.

### G6 — breadth potential

Prefer mechanisms that have a plausible reason to transfer across several contemporaneously liquid instruments. Asset-specific hypotheses are allowed, but must be labeled asset-specific rather than generalized from one winner.

### G7 — untouched evidence availability

A fresh chronology and, when appropriate, asset holdout must exist before promotional testing.

### G8 — research orthogonality

Measure whether the candidate adds a new `H × M × T` cell or mostly repeats a recently tested one. A second candidate in the same cell should require a strong scientific reason.

### G9 — capital/capacity feasibility

Apply the existing cross-strategy capital/scalability requirements: lot granularity, minimum notional, depth, margin, borrow and capacity cannot be deferred indefinitely.

## 8. Research-portfolio rules

To avoid tunnel vision, future candidate selection should obey these portfolio rules prospectively:

1. **No more than two consecutive promotional experiments in the same mechanism family.**
2. **Do not run a second new candidate in the same `H × M` cell until at least one materially different under-covered cell has been evaluated**, unless the second experiment was pre-registered as a controlled A/B mechanism test.
3. In any rolling block of approximately 4-6 new candidate families, cover at least **three horizon bands** and **three mechanism families**.
4. Across that block include, where data allow, at least one directional/taker candidate, one relative-value or market-neutral candidate, and one liquidity/microstructure candidate.
5. Prefer cheap gross/mechanism falsification before full L2/spec engineering.
6. A FAILED strategy is not replaced by a parameter neighborhood. A materially changed timeframe/mechanism gets a new experiment ID and fresh evidence.
7. Do not choose the next strategy because one instrument looked profitable in the previous strategy.

These rules are portfolio-level protection against research overfitting.

## 9. Proposed candidate universe after E009

The following is a **candidate slate**, not authorization to trade or alpha protocols. Exact formulas/thresholds/dates remain unfrozen until the relevant experiment is selected.

### C1 — multi-asset spot/perpetual basis convergence (legacy E006R1 concept)

Primary cells: M5, H2-H4, T3.  
Strength: economically distinct, market-neutral intent, existing groundwork.  
Weakness: four-fill fee hurdle, leg risk, borrow/funding complexity, prior event scarcity on BTC.  
Action: retain, but do **not** automatically make it next solely because it was already queued.

### C2 — multi-minute deviation / VWAP-style mean reversion

Primary cells: M3, H3, T1.  
Intent: test whether reversion has better cost headroom when the signal is built over minutes rather than a 60-second shock.  
Must be a genuinely new frozen family, not E007/E009 rescue tuning.

### C3 — 5-minute / 10-minute continuation or volatility-expansion strategy

Primary cells: M4, H3-H4, T1.  
Intent: cover the currently under-sampled multi-minute trend/breakout region.  
Prior E004 failure is relevant skepticism; any future version needs a new ID and fresh evidence rather than reinterpretation of E004.

### C4 — BTC/ETH-to-alt lead/lag

Primary cells: M6, H1-H2, T1.  
Intent: test delayed information transmission rather than same-asset reversal/continuation.  
Requires strict causal synchronization and cross-asset timestamp semantics.

### C5 — large-trade / liquidity-sweep / forced-flow exhaustion

Primary cells: M7+M3, H1-H2, T1.  
Intent: condition on an economically meaningful forced-liquidity event, then test short reversal/exhaustion.  
Requires objective event definition and likely L2/trade semantic work; should receive a cheap frequency/headroom preflight first.

### C6 — cross-sectional short-horizon dispersion/reversion

Primary cells: M5/M6, H3-H4, T3 or portfolio execution.  
Intent: trade relative moves across a frozen liquid universe instead of predicting absolute market direction.  
Requires explicit multi-leg fee/turnover and common-shock controls.

### C7 — future passive-maker on objectively wider-spread eligible markets

Primary cells: M2, H0-H2, T2/T4.  
This is not an E008 rescue. It would require a new prospectively selected universe using spread/fee feasibility before queue simulation. Low immediate priority until the simpler under-covered horizon cells are sampled.

## 10. Candidate ordering principle

Do not hard-code a single next strategy before candidate cards are completed. The next candidate should be selected by **information value per research cost**, subject to diversification rules.

A practical ordering preference is:

1. first fill an under-covered H3/H4 cell with a cheap gross screen if data can support it;
2. preserve E006R1 as the leading orthogonal relative-value candidate, but subject it to a cheap four-fill cost/headroom preflight before multi-leg engineering;
3. then rotate to a cross-asset/event mechanism rather than another same-asset reversal normalization.

This ordering may be finalized only after non-alpha feasibility cards are written. It must not use future profitability outcomes.

## 11. Time-horizon-specific economics

Shorter is not automatically better for scalping.

- H0/H1 can offer many observations but fees/spread/latency dominate and effective capacity may be small.
- H2 often balances event frequency and move size but remains fee-sensitive.
- H3/H4 generally permit larger raw moves and lower latency sensitivity, but fewer independent trades and more exposure to market drift/regime risk.

Therefore PASS gates should not be identical in raw bps across all horizon bands. Each candidate must freeze a **cost-relative economic hurdle** before outcomes while retaining common breadth/concentration/statistical requirements.

## 12. Required candidate card for every future experiment

Before data-body alpha access record:

- experiment ID;
- economic mechanism;
- horizon band;
- mechanism family;
- execution archetype;
- data resolution;
- signal lookback;
- decision cadence;
- primary/stress latency;
- expected hold;
- maximum hold;
- number/type of expected fills;
- conservative cost floor;
- gross headroom requirement;
- expected event frequency;
- universe rule;
- chronology/contamination roles;
- data requirements;
- cheapest falsification stage;
- promotion/stop rules;
- tuning budget;
- relationship to prior experiments and why it is not rescue tuning.

No candidate should move to heavy engineering without this card.

## 13. Immediate governance conclusion

E009 is closed. E006R1 remains a valid candidate but is **no longer automatically next by inertia**.

Before the next alpha run:

1. treat original sub-minute SC001 evidence as immutable;
2. adopt this expanded horizon/mechanism sampling framework;
3. prepare non-alpha feasibility cards for a small balanced slate spanning H2/H3/H4 and M3/M4/M5/M6/M7;
4. select the next experiment from that slate based on mechanism plausibility, cost headroom, data feasibility, sample sufficiency, orthogonality and research cost — not historical winner selection;
5. freeze the selected experiment under a new ID before any promotional outcome.
