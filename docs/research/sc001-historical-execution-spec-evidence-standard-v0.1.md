# SC001 — Historical Execution-Spec Evidence Standard v0.1

Date: 2026-09-16  
Status: **BINDING EVIDENCE STANDARD BEFORE REAL HISTORICAL EXECUTION/PnL**

## 1. Purpose

Prevent current exchange metadata from being silently treated as historical execution truth.

For every frozen instrument and historical execution window, SC001 must resolve or explicitly mark unresolved:

- contract type;
- settlement/quote currency;
- `tickSz`;
- `lotSz`;
- `minSz`;
- `ctVal` / multiplier;
- relevant listing/spec changes;
- historical maker/taker fee basis used by the simulation;
- funding schedule/rules if positions may cross funding.

## 2. Evidence hierarchy

Preferred evidence, strongest first:

1. official historical exchange instrument/spec snapshot covering the tested date;
2. official dated exchange announcement/change log plus an authoritative baseline that brackets the tested date;
3. exchange-hosted historical data whose discrete prices/sizes can corroborate, but not by itself fully prove, the spec;
4. current metadata only as a diagnostic/reference, never as historical proof.

Third-party historical metadata may be used only as corroboration unless a separate protocol explicitly justifies it.

## 3. Fail-closed rule

If exact historical execution specs cannot be resolved with sufficient evidence, the instrument/date may still be used for signal-only or coarse feasibility analysis where those fields are irrelevant, but it may not be used for promoted discrete execution/PnL that depends on them.

No silent carry-back of current `tickSz`, `lotSz`, `minSz`, `ctVal` or fee schedule is permitted.

## 4. Spec-change intervals

If a field changed during a research window:

- create dated intervals;
- normalize raw prices/sizes using the interval active at each event timestamp;
- preserve the exact source/evidence for every interval;
- reject events that cannot be assigned unambiguously.

## 5. Fee evidence

Historical fee assumptions must be separated from instrument mechanics. The exact fee rule used in a promotional run must be frozen before opening strategy outcomes.

If only a conservative upper-bound fee can be justified, it may be used as a predeclared stress/feasibility assumption, but the report must not label it an exact historical fee.

## 6. Funding evidence

Funding may be ignored only when the frozen strategy guarantees no funding-boundary crossing. Otherwise the historical schedule/rate source and accounting rule must be frozen separately.

## 7. Output requirement

Every real-data execution manifest must carry, per instrument/date interval:

- spec evidence source IDs/URLs or repository artifacts;
- resolved values;
- evidence classification;
- unresolved fields, if any;
- exact hash of the frozen spec map.

A promotional execution runner must refuse to start when a required field is unresolved.
