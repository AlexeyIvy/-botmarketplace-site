# SC001 Current Roadmap and Stop Rules v4.27

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C1 SPOT BODY PASS / SHARED CAUSAL UTILITIES GOLDEN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.26.md`

## 1. Binding terminal strategy states

E001-E008 remain terminal/closed.  
E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`.  
E009 remains terminal `E009_GROSS_FEASIBILITY_FAIL`.  
E009 read-only postmortem remains complete.

No terminal strategy is reopened. No rescue-tuning is authorized.

## 2. C1 SPOT body integrity result

The frozen C1 SPOT body acquisition/integrity stage completed exact:

`C1_SPOT_BODY_INTEGRITY_PASS`

with:

- exit code `0`;
- archive files qualified `256/256`;
- reconstructed UTC asset-days qualified `240/240`;
- performance asset-days `224`;
- boundary warm-up asset-days `16`;
- downloaded files `256`;
- reused files `0`;
- qualified bytes `273358764`;
- strategy/sentinel/basis/returns/PnL false;
- promotional alpha false.

Result record:

`docs/research/sc001-c1-selection-spot-body-integrity-results-v0.1.md`

This PASS is data readiness only.

## 3. Shared causal utility layer frozen

Protocol:

`docs/research/sc001-shared-causal-trade-bar-return-utilities-protocol-v0.1.md`

Library:

`research/sc001/sc001_selection_causal_utils_v0_1.py`

Synthetic/golden runner:

`research/sc001/sc001_selection_causal_utils_golden_v0_1.py`

Implementation freeze:

`docs/research/sc001-selection-causal-utils-implementation-freeze-v0.1.json`

Frozen Git blob identities:

- protocol: `20afa656740c4785f6c1afb21a7f2dbb35ef5eb1`;
- library: `a7953274e5e47c7dd1280b20c16d479ca90badc4`;
- golden runner: `c0aade86aabfe4a241fca454004f3f07d5b33255`.

Exact required PASS token:

`SC001_SELECTION_CAUSAL_UTILS_GOLDEN_PASS`

## 4. Frozen utility semantics

The shared layer fixes:

- half-open bars `[T,T+W)`;
- a bar is available only at/after `bar.close_ms`;
- no same-bar look-ahead;
- causal trailing completed-bar windows;
- exact OHLC/VWAP/notional and signed aggressive notional;
- no fabricated empty bars;
- deterministic non-overlap;
- strict trade-id ordering;
- D + D+1 target-day filtering;
- reusable return and robust-z primitives.

It contains no candidate-specific alpha threshold or outcome-driven parameter.

## 5. Current hard gate

**NO C1-C6 SENTINEL OUTCOME BEFORE EXACT `SC001_SELECTION_CAUSAL_UTILS_GOLDEN_PASS`.**

The golden stage uses synthetic fixtures only and requires no market-data body.

Protected holdouts and Confirmation periods remain closed.

## 6. Sentinel budget unchanged

Frozen first-pass budget remains exactly **11 variants**:

- C1: 1;
- C2: 2;
- C3: 2;
- C4: 4;
- C5: 1;
- C6: 1.

No auxiliary indicator may be added after outcomes.

## 7. Current sequence

1. pull current GitHub state;
2. verify frozen protocol/library/golden identities;
3. syntax-check library and golden runner;
4. run synthetic/golden suite and require exact `SC001_SELECTION_CAUSAL_UTILS_GOLDEN_PASS`;
5. only after PASS implement six separate C1-C6 sentinel runners;
6. freeze runner/config identities before first sentinel outcome;
7. run all nonpromotional sentinels on contaminated sandbox;
8. assign selection dispositions;
9. perform MDE/block planning for survivors;
10. freeze diversified promotional research batch only after all dispositions are known.

Immediate next action: run the frozen shared causal utilities golden suite on VPS.
