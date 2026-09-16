# SC001 — Fresh Chronology & Asset-Holdout Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN BEFORE NEW MULTI-ASSET STRATEGY BODY ACCESS**  
Scope: **SCALPING RESEARCH / SC001**

## 1. Purpose

Define fresh, non-overlapping evidence roles for the first-generation frozen multi-asset universe without reopening E001-E008 or consuming previously protected Q2/formal Validation/Final data.

Parent universe:
`docs/research/sc001-first-generation-multi-asset-universe-freeze-v1.0.json`

No strategy signal/PnL has been used to choose these dates or the asset partition.

## 2. Engineering/calibration policy

Execution-kernel engineering must use already contaminated/engineering data whenever possible, primarily previously qualified BTC March-2024 / E008 engineering material.

Do not consume fresh Q3 bodies merely to debug the kernel.

## 3. Frozen asset partition

The 12 ranked instruments are split deterministically before any new strategy outcome.

Asset-holdout ranks are every third rank:
`3, 6, 9, 12`.

Therefore:

### Discovery-development assets — 8
- BTC-USDT-SWAP
- ETH-USDT-SWAP
- DOGE-USDT-SWAP
- ORDI-USDT-SWAP
- UNI-USDT-SWAP
- XRP-USDT-SWAP
- OP-USDT-SWAP
- BCH-USDT-SWAP

### Asset holdout — 4
- SOL-USDT-SWAP
- FIL-USDT-SWAP
- LTC-USDT-SWAP
- SUI-USDT-SWAP

The holdout assets must remain unopened for strategy-performance analysis until the discovery implementation, parameters, execution semantics, cost assumptions and gates are frozen.

No asset may migrate between groups after outcomes.

## 4. Frozen chronology

### Discovery performance block
`2024-07-01` through `2024-07-14` UTC inclusive.

Non-performance boundary/warm-up labels if needed by archive stitching:
- `2024-06-30` — warm-up / D-1 only;
- `2024-07-15` — D+1/boundary only.

### Asset-holdout performance block
The same calendar performance block `2024-07-01..2024-07-14`, but only on the four frozen holdout assets.

This is **cross-asset replication**, not chronological Confirmation.

### Chronological Confirmation block
`2024-08-01` through `2024-08-14` UTC inclusive on all 12 frozen instruments.

Non-performance boundary/warm-up labels if needed:
- `2024-07-31` — warm-up / D-1 only;
- `2024-08-15` — D+1/boundary only.

The gap `2024-07-16..2024-07-30` remains unopened/unassigned by this protocol and must not be mined opportunistically.

## 5. Access order

1. Build and validate common data/accounting + appropriate execution kernel using contaminated engineering data.
2. Freeze strategy-specific protocol and implementation identity.
3. Open Discovery bodies for the eight Discovery assets only.
4. If Discovery terminally satisfies its frozen gates, open the four asset-holdout bodies for the same July block with no retuning.
5. Only if Discovery + asset-holdout satisfy their predeclared gates may August chronological Confirmation bodies be opened.
6. Confirmation is one shot. No tuning after body access.

## 6. Statistical interpretation

July Discovery and July asset-holdout share calendar regime shocks. They provide different-instrument generalization, not independent time evidence.

August Confirmation provides the independent time axis.

Primary inference must include instrument-day/day-block structure and equal-weight market summaries, not only pooled cycles.

## 7. Contamination rules

After body access:
- Discovery dates become outcome-contaminated for the accessed Discovery assets;
- holdout dates become outcome-contaminated for holdout assets only after holdout access;
- Confirmation dates remain fresh until exact access authorization and first run;
- boundary days are engineering/boundary only and never performance evidence.

## 8. Firewalls

This chronology does not authorize immediate strategy simulation.

Before any promotional execution/PnL:
- historical execution-spec handling must be resolved/frozen;
- common normalized data/accounting infrastructure must pass verification;
- relevant execution kernel must pass golden/property/fault/determinism/accounting tests;
- strategy-specific economic-feasibility gate must be frozen and passed where applicable;
- one-shot run manifest and duplicate-run protection must exist.

E001-E008 terminal decisions remain immutable.
