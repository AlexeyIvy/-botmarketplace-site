# SC001 — Next Primary Forced-Flow Relative Dislocation S0 Protocol v0.2

Date: 2026-09-29
Status: PREFROZEN CHEAPEST SENTINEL / STRATEGY-USER HOLD / NO EXECUTION AUTHORIZATION
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01

Supersedes:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-s0-protocol-v0.1.md

## Purpose and chronology

S0 measures only the signed venue-relative dislocation at the first actionable strict-coactive second after a frozen liquidation cluster. It does not test later convergence, return or PnL.

Fresh window:
2026-09-30T00:00:00Z <= event_time < 2026-10-07T00:00:00Z.

The seven frozen UTC dates are:
2026-09-30, 2026-10-01, 2026-10-02, 2026-10-03, 2026-10-04, 2026-10-05, 2026-10-06.

The window is fixed. It may not be moved, reconstructed or replaced because acquisition continuity is inconvenient.

Frozen symbols:
BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, ORDIUSDT, FILUSDT, UNIUSDT, XRPUSDT, LTCUSDT, OPUSDT, BCHUSDT, SUIUSDT.

## Event definition

Unchanged RB021/B13-C semantics:
- deterministic fingerprints;
- per symbol;
- inter-event gap <=5 seconds;
- >=3 distinct events;
- all events same liquidation side;
- source-gap censoring +/-5 seconds;
- no liquidation magnitude threshold.

## Price/reference clock

Only Bybit public linear-perpetual trades and OKX public same-underlying USDT perpetual trades after source-semantic/economic-identity qualification PASSES.

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

Binding fee qualification:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-fee-qualification-v0.1.md.

Frozen:
- common conservative regular-user Bybit taker fee = 11 bps/fill;
- two-fill fee floor = 22 bps;
- spread/depth reference = 10 bps;
- execution/model reserve = 10 bps;
- S0 funding/borrow reference = 0 bps because S0 has no position/hold.

two_fill_structural_burden_bps = 42.

H = max(30, 42+10) = 52 bps.

No maker rebate credit and no post-outcome lowering.

## Source/sample gate

Require all:
- valid clusters >=300;
- >=8/12 frozen symbols represented;
- >=5 distinct frozen UTC dates represented by at least one valid cluster;
- every included event passes source-gap censoring;
- every included cross-venue observation passes semantic/economic identity.

Failure: DEFER_SOURCE_OR_SAMPLE.

## Frozen breadth semantics

Day breadth denominator is always exactly all 7 frozen UTC dates.

For each frozen UTC date:
- if >=1 valid cluster exists, day_median = median forced_flow_dislocation_bps for valid clusters on that date;
- if zero valid clusters exist, day_median = null;
- day_median = null does not count positive.

positive_frozen_utc_dates is counted over the fixed denominator 7.

SURVIVE day breadth requires:
positive_frozen_utc_dates >= 5 / 7.

Symbol breadth denominator is always exactly all 12 frozen symbols.

For each frozen symbol:
- if >=1 valid cluster exists, symbol_median is calculated over its valid clusters;
- if no valid cluster exists, symbol_median = null;
- an unrepresented/null frozen symbol does not count positive.

positive_frozen_symbols is counted over the fixed denominator 12.

SURVIVE symbol breadth requires:
positive_frozen_symbols >= 6 / 12.

No reduced denominator is permitted for either day or symbol breadth.

## Headroom gate

After source/sample PASS, SURVIVE only if all:
- pooled median forced_flow_dislocation_bps >= 52;
- positive_frozen_symbols >= 6 / 12;
- positive_frozen_utc_dates >= 5 / 7.

All pass: SURVIVE_HEADROOM.
Otherwise: REJECT_FORCED_FLOW_RELATIVE_HEADROOM.

Report:
- valid cluster count;
- represented symbol count;
- represented frozen-date count;
- pooled median;
- all 12 symbol medians including nulls;
- all 7 frozen-date medians including nulls;
- positive_frozen_symbols / 12;
- positive_frozen_utc_dates / 7.

Clusters are not assumed IID.

## Preconditions before any S0 execution

All must pass before a separate execution authorization:
1. source-semantic/economic-identity qualification;
2. binding pre-outcome implementation handshake;
3. read-only operational continuity for the B13-C acquisition path across the frozen window boundary;
4. explicit Strategy/User S0 authorization.

Current operational continuity state:
B13C_FRESH_WINDOW_CONTINUITY_NOT_ESTABLISHED_READONLY.

Therefore S0 is not authorized.

## Firewalls / stop rules

Forbidden:
- B13-C protected outcome tuning;
- liquidation-size/event-count/cluster-gap search;
- alternate entry delay or observation bucket;
- horizon grid;
- symbol subset selection;
- sign flip;
- lower headroom threshold;
- reduced day/symbol breadth denominator;
- stale carry-forward;
- mark/premium/index/spot substitution;
- L1/L2 or execution simulation;
- returns/PnL/trading;
- Candidate 2/3 parallel outcome research;
- moving or reconstructing the fresh window.

DEFER_SOURCE_OR_SAMPLE: stop; resolve source/sample prospectively without relaxing rules.
REJECT_FORCED_FLOW_RELATIVE_HEADROOM: terminal for this exact S0; no same-evidence rescue; run reusable-block extraction.
SURVIVE_HEADROOM: authorizes only preparation of a separately prospectively frozen 10-second convergence sentinel. It does not authorize that run, PnL, Confirmation, promotion or trading.

No S0 run is authorized by this protocol.
