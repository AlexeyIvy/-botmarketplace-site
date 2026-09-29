# SC001 — Next Primary Forced-Flow Relative Dislocation S0 Protocol v0.1

Date: 2026-09-29
Status: PREFROZEN CHEAPEST SENTINEL / NO EXECUTION AUTHORIZATION
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01

## Purpose and chronology

S0 measures only the signed venue-relative dislocation at the first actionable strict-coactive second after a frozen liquidation cluster. It does not test later convergence, return or PnL.

Fresh window:
2026-09-30T00:00:00Z <= event_time < 2026-10-07T00:00:00Z.

This is the first seven complete UTC days after the 2026-09-29 prefreeze commit. If the final commit date differs, re-freeze the mechanically implied first seven complete UTC days before outcome access. The B13-C protected outcome interval is not promotional/design evidence.

Frozen symbols:
BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, ORDIUSDT, FILUSDT, UNIUSDT, XRPUSDT, LTCUSDT, OPUSDT, BCHUSDT, SUIUSDT.

## Event definition

Unchanged RB021/B13-C semantics:
- deterministic fingerprints;
- per symbol;
- inter-event gap <=5s;
- >=3 distinct events;
- all events same liquidation side;
- source-gap censoring +/-5s;
- no liquidation magnitude threshold.

## Price/reference clock

Only Bybit public linear-perpetual trades and OKX public same-underlying USDT perpetual trades after the separate source-semantic gate PASSES.

Use STRICT_COACTIVE_1S_NO_CARRY_FORWARD.

For each exact UTC second, use the chronologically last valid trade price from each venue only when both trade in that same second. No carry-forward/interpolation/substitute source.

raw_basis_bps(t) = 10000 * ln(P_Bybit(t) / P_OKX(t)).

Use strict-coactive observations in [t-300s,t), current second excluded, minimum 120:

local_basis_ref_bps(t) = median(prior raw_basis_bps).

relative_dev_bps(t) = raw_basis_bps(t) - local_basis_ref_bps(t).

Pressure sign:
- LONG_LIQUIDATED = -1;
- SHORT_LIQUIDATED = +1.

forced_flow_dislocation_bps = pressure_sign * relative_dev_bps(t).

Observation bucket = first strict-coactive 1-second bucket starting >= cluster_end+1s and < cluster_end+2s. If absent, event is source/latency-ineligible. No later bucket and no later price may be opened.

## Edge-to-Fill hurdle

Frozen:
- two-fill Bybit regular-user fee floor = 11 bps;
- spread/depth reference = 10 bps;
- execution/model reserve = 10 bps;
- S0 funding/borrow reference = 0 bps because S0 has no position/hold.

two_fill_structural_burden_bps = 31.

H = max(30, 31+10) = 41 bps.

No maker rebate credit and no post-outcome lowering.

## Source/sample gate

Require all:
- valid clusters >=300;
- >=8/12 frozen symbols represented;
- >=5 distinct UTC days represented;
- every included event passes source-gap censoring;
- every included cross-venue observation passes semantic/economic identity.

Failure: DEFER_SOURCE_OR_SAMPLE.

## Headroom gate

After source/sample PASS, SURVIVE only if all:
- pooled median forced_flow_dislocation_bps >= 41;
- >=6 frozen symbols have positive median dislocation;
- >=5 of the seven UTC-day medians are positive.

All pass: SURVIVE_HEADROOM.
Otherwise: REJECT_FORCED_FLOW_RELATIVE_HEADROOM.

Report cluster count, symbol/day breadth, pooled median, per-symbol median-sign breadth and all seven day medians. Clusters are not assumed IID.

## Firewalls / stop rules

Forbidden:
- B13-C protected outcome tuning;
- liquidation-size/event-count/cluster-gap search;
- alternate entry delay or observation bucket;
- horizon grid;
- symbol subset selection;
- sign flip;
- lower headroom threshold;
- stale carry-forward;
- mark/premium/index/spot substitution;
- L1/L2 or execution simulation;
- returns/PnL/trading;
- Candidate 2/3 parallel outcome research.

DEFER_SOURCE_OR_SAMPLE: stop; resolve source/sample prospectively without relaxing rules.
REJECT_FORCED_FLOW_RELATIVE_HEADROOM: terminal for this exact S0; no same-evidence rescue; run reusable-block extraction.
SURVIVE_HEADROOM: authorizes only preparation of a separately prospectively frozen 10-second convergence sentinel. It does not authorize that run, PnL, Confirmation, promotion or trading.

No Runner bundle, networked research job, Test Executor research job or collector mutation is authorized by this protocol.
