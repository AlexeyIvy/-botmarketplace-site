# SC001 — Next Primary Forced-Flow Relative Dislocation Feasibility Card v0.1

Date: 2026-09-29
Status: PREFREEZE READY / NO OUTCOME ACCESS AUTHORIZED
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01
Family: VENUE_LOCAL_FORCED_FLOW_RELATIVE_DISLOCATION

Authority: docs/research/sc001-strategy-manager-portfolio-review-v0.1.md at 5bab788cb32dcf99f3d2ff4fc869d9f833ae5686.

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
- inter-event gap <=5s;
- >=3 distinct events;
- all events same liquidation side;
- source-gap censoring +/-5s around cluster;
- no liquidation magnitude threshold.

No size/count/gap/entry-delay/horizon/symbol/sign search.

## Fresh boundary

Because this package is committed on 2026-09-29 UTC, first evidence is frozen to:

2026-09-30T00:00:00Z <= event_time < 2026-10-07T00:00:00Z.

This is the first seven complete UTC days after the prefreeze commit. If the final commit date differs, re-freeze the mechanically implied first seven complete UTC days before any outcome access; outcomes may not select the replacement.

The B13-C protected outcome interval is not promotional/design evidence for this candidate.

## Edge-to-Fill

Architecture:
- trade Bybit only;
- OKX is observation-only reference;
- one entry + one exit = 2 structural fills;
- no maker rebate credit.

Current canonical Bybit perpetual/futures VIP0 taker reference in SC001: 5.5 bps/fill; two-fill fee floor = 11 bps.

Prospective conservative reserves:
- spread/depth = 10 bps;
- execution/model = 10 bps;
- funding/borrow = 0 bps in S0 because S0 opens no position/hold/PnL. A later convergence stage must freeze any economically relevant funding treatment separately.

two_fill_structural_burden_bps = 11 + 10 + 10 = 31.

H = max(30, 31 + 10) = 41 bps.

Required statement:
expected_information_scale_bps / structural_burden_bps = UNKNOWN_PRE_OUTCOME / 31.

Classification: UNKNOWN_NEEDS_NON_ALPHA_DATA.

The ordinary low-single-digit SC001 prior is below this burden, but the candidate has an explicit mandatory-flow payer and event-conditioned state. No outcome has been opened to estimate actual scale, so the pre-outcome card does not justify REJECT_STRUCTURAL_BEFORE_OUTCOME.

Qualitative capital-time profile: many/day, seconds-to-tens-of-seconds occupancy, broad liquid universe, and no expected USD 1,000 capacity constraint if later execution qualifies. Stressed liquidation liquidity can only raise later cost assumptions.

## Cheapest S0 question

At the first actionable strict-coactive second after each eligible cluster, test only whether signed venue-relative dislocation has structural headroom versus H=41 bps. No later convergence price is opened.

Exact formulas, sample gates and terminal tokens are frozen in:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-s0-protocol-v0.1.md.

## Handoff

PREFREEZE_READY_FOR_STRATEGY/USER_GATE

This authorizes no Runner bundle, networked job, outcome sentinel, PnL or trading. A later S0 outcome run requires separate explicit authorization after source-semantic qualification and the binding implementation handshake. No C-series ID is assigned here.
