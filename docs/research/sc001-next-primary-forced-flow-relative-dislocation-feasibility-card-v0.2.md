# SC001 — Next Primary Forced-Flow Relative Dislocation Feasibility Card v0.2

Date: 2026-09-29
Status: PREFREEZE READY / STRATEGY-USER HOLD / NO S0 AUTHORIZATION
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01
Family: VENUE_LOCAL_FORCED_FLOW_RELATIVE_DISLOCATION

Supersedes:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-feasibility-card-v0.1.md

Authority:
docs/research/sc001-strategy-manager-portfolio-review-v0.1.md at 5bab788cb32dcf99f3d2ff4fc869d9f833ae5686.

## Mechanism and scope

Disposition: RELATED_BUT_MATERIALLY_DIFFERENT_ARCHITECTURE.
Adaptive flag: ADAPTIVE_DISCOVERY_GENERATED.

Economic payer: non-discretionary Bybit forced deleveraging can temporarily consume local liquidity and move the forced venue away from independently trading same-underlying price discovery; later re-anchoring is the prospective payer.

Lineage:
- B13-C/RB021: event/state semantics only;
- RB011: strict-coactive 1-second cross-venue clock;
- RB012: causal local cross-venue basis reference;
- C8B: nearest relative-basis measurement lineage, but not the same monetization architecture.

Frozen symbols:
BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, ORDIUSDT, FILUSDT, UNIUSDT, XRPUSDT, LTCUSDT, OPUSDT, BCHUSDT, SUIUSDT.

Sources:
- frozen B13-C Bybit linear-USDT-perpetual liquidation semantics;
- Bybit public linear-perpetual trades for the affected contract;
- OKX public same-underlying USDT perpetual trades, reference only;
- official instrument metadata for full economic identity.

Fail closed before any ratio if asset class, underlying identity, economic unit, contract type, quote/settlement or timestamp semantics are unresolved. S0 excludes L1/L2, mark/premium/index substitutes, funding as alpha input, spot, external hedge trades, later returns and PnL.

## Event freeze

Unchanged from RB021/B13-C:
- deterministic liquidation fingerprints;
- per symbol;
- inter-event gap <=5 seconds;
- >=3 distinct events;
- all events same liquidation side;
- source-gap censoring +/-5 seconds around cluster;
- no liquidation magnitude threshold.

No size/count/gap/entry-delay/horizon/symbol/sign search.

## Fresh boundary

2026-09-30T00:00:00Z <= event_time < 2026-10-07T00:00:00Z.

This is the first seven complete UTC days after the 2026-09-29 prefreeze commit. The window is not movable because of later source inconvenience or outcomes.

The B13-C protected outcome interval is not promotional/design evidence for this candidate.

Operational continuity qualification:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-operational-source-continuity-qualification-v0.1.md.

Current continuity state:
B13C_FRESH_WINDOW_CONTINUITY_NOT_ESTABLISHED_READONLY.

Therefore no S0 execution is authorized.

## Edge-to-Fill

Architecture:
- trade Bybit only;
- OKX is observation-only reference;
- one entry + one exit = 2 structural fills;
- no maker rebate credit.

Binding fee qualification:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-fee-qualification-v0.1.md.

Freeze a conservative common regular-user product/zone taker fee:
11 bps/fill.

Two-fill fee floor = 22 bps.

Prospective reserves:
- spread/depth = 10 bps;
- execution/model = 10 bps;
- funding/borrow = 0 bps in S0 because S0 opens no position/hold/PnL.

two_fill_structural_burden_bps = 22 + 10 + 10 = 42.

H = max(30, 42 + 10) = 52 bps.

Required statement:
expected_information_scale_bps / structural_burden_bps = UNKNOWN_PRE_OUTCOME / 42.

Classification: UNKNOWN_NEEDS_NON_ALPHA_DATA.

The ordinary low-single-digit SC001 prior is below this burden, but the candidate has an explicit mandatory-flow payer and event-conditioned state. No outcome has been opened to estimate actual scale, so the cost card alone does not establish REJECT_STRUCTURAL_BEFORE_OUTCOME.

## Cheapest S0 question

At the first actionable strict-coactive second after each eligible cluster, test only whether signed venue-relative dislocation has structural headroom versus H=52 bps. No later convergence price is opened.

Exact formulas and stop rules are frozen in:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-s0-protocol-v0.2.md.

## Handoff

PREFREEZE_READY_FOR_STRATEGY/USER_GATE

This state is HOLD, not execution PASS.

No S0 outcome is authorized until:
1. source-semantic/economic-identity qualification passes;
2. binding implementation handshake passes;
3. fresh-window B13-C operational continuity is established read-only;
4. Strategy/User explicitly authorizes the frozen S0.

No C-series ID is assigned here.
