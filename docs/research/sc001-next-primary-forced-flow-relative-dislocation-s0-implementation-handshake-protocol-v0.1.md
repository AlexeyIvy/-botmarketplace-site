# SC001 — Forced-Flow Relative Dislocation S0 Implementation Handshake Protocol v0.1

Date: 2026-09-30
Status: FROZEN PRE-OUTCOME IMPLEMENTATION HANDSHAKE / SYNTHETIC ONLY / NO S0 AUTHORIZATION
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01
Family: VENUE_LOCAL_FORCED_FLOW_RELATIVE_DISLOCATION

## Purpose

Freeze and validate the deterministic S0 analyzer before any real fresh-window price/outcome access.

The handshake may use synthetic fixtures only.

No B13-C protected outcome interval, fresh-window price body, return, PnL or trading data may be opened by the handshake.

## Binding parents

- docs/research/sc001-next-primary-forced-flow-relative-dislocation-s0-protocol-v0.2.md
- docs/research/sc001-next-primary-forced-flow-relative-dislocation-fee-qualification-v0.1.md
- docs/research/sc001-next-primary-forced-flow-relative-dislocation-source-semantic-qualification-result-v0.1.json
- docs/research/sc001-next-primary-forced-flow-relative-dislocation-b13c-fresh-window-continuity-readonly-result-v0.1.json
- docs/research/sc001-contamination-registry-v0.40.json

The implementation freeze pins exact Git blobs for every parent and the runner.

## Frozen constants

Universe:
BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, ORDIUSDT, FILUSDT, UNIUSDT, XRPUSDT, LTCUSDT, OPUSDT, BCHUSDT, SUIUSDT.

Fresh window:
2026-09-30T00:00:00Z <= cluster_end < 2026-10-07T00:00:00Z.

Event semantics:
- distinct events >=3;
- max inter-event gap <=5000 ms;
- one liquidation side per cluster;
- source_gap_pass must be true;
- no liquidation magnitude threshold.

Observation:
- first strict-coactive second start >= cluster_end+1000 ms and < cluster_end+2000 ms;
- exact one-second bucket starts only;
- no carry-forward.

Basis:
raw_basis_bps = 10000 * ln(P_Bybit / P_OKX).

Causal local reference:
- [observation_second-300s, observation_second);
- strict-coactive rows only;
- current second excluded;
- minimum 120 observations;
- median raw basis.

Pressure sign:
- LONG_LIQUIDATED = -1;
- SHORT_LIQUIDATED = +1.

forced_flow_dislocation_bps = pressure_sign * (raw_basis_bps - local_basis_ref_bps).

H = 52 bps.

Source/sample gate:
- >=300 valid clusters;
- >=8/12 frozen symbols represented;
- >=5/7 frozen UTC dates represented.

Fixed breadth denominators:
- all 7 frozen dates always present; zero valid clusters => median null => not positive;
- all 12 frozen symbols always present; unrepresented => median null => not positive.

SURVIVE only if:
- pooled median >=52 bps;
- positive frozen symbols >=6/12;
- positive frozen UTC dates >=5/7.

## Input contracts for future authorized analyze mode

Cluster JSONL rows must contain:
- cluster_id;
- symbol;
- cluster_end_ms;
- liquidated_side;
- distinct_event_count;
- max_inter_event_gap_ms;
- source_gap_pass.

Coactive-price JSONL rows must contain:
- symbol;
- second_start_ms;
- bybit_price;
- okx_price;
- source_identity_pass.

A coactive row asserts both venues had a valid trade inside the exact same second. Duplicate symbol+second rows are forbidden.

The analyzer performs no network acquisition. A future acquisition/materialization stage must be separately frozen and authorized before real S0 inputs exist.

## Authorization interlock

Real analyze mode requires a committed authorization JSON supplied explicitly to the runner.

It must state:
- status = S0_EXECUTION_AUTHORIZED;
- task_id = SC001-NEXT-PRIMARY-PREFREEZE-01;
- exact implementation freeze path/blob;
- exact input provenance;
- outcome scope limited to S0.

Without that authorization file, analyze mode must fail closed before opening real input files.

No such authorization exists in this handshake stage.

Additionally, real analyze mode must fail closed before `2026-10-07T00:00:00Z`, because the frozen evidence window consists of seven complete UTC days. This time lock must be checked before opening real cluster or coactive-price inputs.

## Handshake requirements

Offline self-test must PASS:
- Python starts successfully;
- implementation freeze exists;
- freeze status equals expected;
- runner blob matches freeze;
- every parent path resolves and parent Git blob matches;
- universe count/order matches 12 frozen symbols;
- fresh-window timestamps match;
- H=52;
- synthetic pressure-sign test;
- synthetic causal 300-second baseline test;
- current-second exclusion;
- minimum-120 gate;
- exact observation-bucket test;
- fixed 7-day null denominator;
- fixed 12-symbol null denominator;
- malformed/duplicate input fixture rejection;
- analyze mode refuses missing authorization;
- analyze mode refuses any outcome access before 2026-10-07T00:00:00Z;
- output path collision check is active.

PASS token:

FORCED_FLOW_S0_IMPLEMENTATION_HANDSHAKE_PASS

Failure token:

FORCED_FLOW_S0_IMPLEMENTATION_HANDSHAKE_REVIEW

PASS does not authorize S0 execution.
