# SC001 — Strategy Landscape v0.1

Date: 2026-09-17  
Status: **CURRENT COVERAGE MAP / NON-ALPHA GOVERNANCE ARTIFACT**

## 1. Purpose

This document maps completed and prospective SC001 research across:

- Signal Horizon;
- Position Horizon;
- mechanism family;
- execution archetype;
- coarse risk signature;
- evidence status.

The map is descriptive. It does not rank strategies by expected profitability.

## 2. Completed evidence map

### E001 — hourly mean reversion

- signal horizon: outside core S0-S4 scalp map / roughly hourly;
- position horizon: outside core <=30m boundary;
- mechanism: M3 mean reversion;
- execution: T1 directional;
- evidence: terminal FAIL;
- legacy action: no direct retest.

### E002 — taker-flow imbalance

- signal horizon: S0-S1;
- position horizon: P0-P1;
- mechanism: M1 order-flow/microstructure prediction;
- execution: T1 directional taker;
- risk signature: directional, high fee/spread/latency sensitivity;
- evidence: predictive feature survived replication, standalone taker economics failed;
- legacy action: no standalone retest; auxiliary use only under new ID.

### E003 — flow impulse continuation

- signal horizon: S0-S1;
- position horizon: P0-P2;
- mechanism: M4 continuation;
- execution: T1;
- evidence: terminal gross/mechanism failure;
- legacy action: no direct retest.

### E004/E005 — compression / breakout

- signal horizon: primarily S1-S2;
- position horizon: P1-P2;
- mechanism: M4 continuation/breakout;
- execution: T1;
- evidence: E004 terminal FAIL; E005 closed by prerequisite;
- legacy action: no direct retest; future H3/H4 trend candidate must be new family.

### E006 — same-venue spot/perp basis convergence

- signal horizon: S1-S3 depending on basis state window;
- position horizon: up to P4 (~30m max hold in old protocol);
- mechanism: M5 relative value/basis;
- execution: T3 multi-leg;
- risk signature: low intended market beta, four-fill cost, legging/funding/borrow complexity;
- evidence: BTC terminal FAIL with event-scarcity / headroom limitations;
- legacy action: strict multi-asset E006R1 replication scientifically justified, subject to cheap feasibility card first.

### E007 / E007R1 — displacement reversal

- signal horizon: S2 (~60s displacement);
- position horizon: P2-P3;
- mechanism: M3 overshoot/reversal;
- execution: T1;
- risk signature: directional, event-driven, latency-sensitive but less than H0/H1;
- evidence: E007 terminal; E007R1 strict multi-asset replication terminal FAIL despite adequate activity;
- legacy action: no further direct retest.

### E008 — passive maker / spread capture

- signal horizon: S0-S1 / state-driven quoting;
- position horizon: P1;
- mechanism: M2 liquidity provision;
- execution: T2 passive maker with taker fail-safe;
- risk signature: queue/adverse-selection/inventory risk;
- evidence: terminal FAIL; BTC spread economics poor; queue model also overly adversarial;
- legacy action: no BTC same-rule retest; a new wider-spread market universe may support a new family.

### E009 — volatility-normalized displacement reversal

- signal horizon: S2 with S3-scale volatility context;
- position horizon: P2-P3;
- mechanism: M3 overshoot/reversal;
- execution: T1;
- evidence: fresh multi-asset terminal FAIL with adequate sample; no concentration failure;
- legacy action: no direct retest.

## 3. Coverage diagnosis

Relatively well covered:

- S0-S2 microstructure/event-driven horizons;
- M1 order flow;
- M2 maker/spread capture on BTC;
- M3 short displacement reversal;
- M4 short continuation/breakout variants;
- T1 directional taker research infrastructure.

Under-covered:

- S3-S4 signals (1-10 minute construction);
- P3-P4 holds (5-30 minutes);
- M5 multi-asset relative value beyond one BTC basis study;
- M6 cross-asset information transfer;
- M7 forced-flow/liquidation/sweep events;
- multi-leg execution research beyond coarse legacy E006;
- cross-sectional/portfolio relative-value strategies;
- risk signatures with low directional beta and longer micro-intraday convergence.

## 4. Prospective candidate slate

### C1 — E006R1 multi-asset spot/perp basis convergence

- signal/position: S2-S4 / P2-P4;
- mechanism/execution: M5 / T3;
- role: strict legacy replication candidate;
- first task: pair eligibility + event-frequency + four-fill-cost feasibility, no heavy multi-leg engineering yet.

### C2 — multi-minute deviation / VWAP-style mean reversion

- signal/position: S3 / P3;
- mechanism/execution: M3 / T1;
- role: new H3 candidate, not E007 rescue;
- first task: define economic mechanism and cheap move-vs-cost sentinel.

### C3 — 5m/10m continuation or volatility expansion

- signal/position: S3-S4 / P3-P4;
- mechanism/execution: M4 / T1;
- role: new under-covered trend/breakout candidate, not E004 rescue;
- first task: distinguish structural rule from E004 and define bar-causal sentinel.

### C4 — BTC/ETH -> alt lead/lag

- signal/position: S1-S2 / P1-P2;
- mechanism/execution: M6 / T1;
- role: new information-transfer mechanism;
- first task: causal synchronization + common-market control feasibility.

### C5 — large-trade / sweep / forced-flow exhaustion

- signal/position: S0-S2 / P1-P2;
- mechanism/execution: M7 + M3 / T1;
- role: event-driven forced-flow candidate;
- first task: objective event definition, event frequency and move-vs-cost sentinel.

### C6 — cross-sectional short-horizon dispersion/reversion

- signal/position: S3-S4 / P3-P4;
- mechanism/execution: M5/M6 / T3 or portfolio execution;
- role: low-beta multi-asset relative-value candidate;
- first task: universe/common-factor definition + turnover/fill-count feasibility.

### C7 — new wider-spread maker family

- signal/position: S0-S2 / P0-P2;
- mechanism/execution: M2 / T2-T4;
- role: lower immediate priority;
- first task: prospectively selected spread/fee-eligible market universe before queue modeling.

## 5. Immediate landscape implication

No single candidate is automatically next.

The next step is to complete non-alpha candidate cards for C1-C6, apply structural feasibility gates, and form a small Pareto-efficient research batch spanning materially different mechanism/time/risk cells.

Promotional alpha remains closed until that batch is frozen.
