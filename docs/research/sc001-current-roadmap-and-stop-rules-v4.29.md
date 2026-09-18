# SC001 Current Roadmap and Stop Rules v4.29

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — MASTER PREFLIGHT PASS / ALL-SIX SENTINEL BATCH FROZEN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.28.md`

## 1. Binding terminal strategy states

E001-E008 remain terminal/closed.  
E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`.  
E009 remains terminal `E009_GROSS_FEASIBILITY_FAIL`.  
E009 read-only postmortem remains complete.

No terminal strategy is reopened. No rescue-tuning is authorized.

## 2. Shared causal utility gate remains PASS

Exact:

`SC001_SELECTION_CAUSAL_UTILS_GOLDEN_PASS`

with 11 synthetic/golden checks passed and no protected/promotional data accessed.

## 3. C1-C6 master implementation preflight result

Exact:

`SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT_PASS`

Observed:

- C1 preflight PASS;
- C2 preflight PASS;
- C3 preflight PASS;
- C4 preflight PASS;
- C5 preflight PASS;
- C6 preflight PASS;
- candidate preflights `6/6`;
- total strategy variants `11`;
- sentinel outcome calculated false;
- protected data accessed false;
- promotional alpha accessed false;
- master exit code `0`.

Result record:

`docs/research/sc001-c1-c6-sentinel-implementation-preflight-results-v0.1.md`

## 4. Frozen all-six batch execution

Batch protocol:

`docs/research/sc001-c1-c6-sentinel-batch-execution-protocol-v0.1.md`

Batch runner:

`research/sc001/sc001_c1c6_sentinel_batch_v0_1.py`

Batch freeze:

`docs/research/sc001-c1-c6-sentinel-batch-implementation-freeze-v0.1.json`

Frozen identities:

- batch protocol: `3579b646c1b2ad2022cf33e2dcbc8c539a422b81`;
- sentinel implementation freeze: `bbd850953ca8915c51706eee360ebb9689640eb1`;
- batch runner: `e1fb38353c721816380c45130a7e95b8861d8543`;
- batch implementation freeze blob: `978b876ecb006ac6179888d5bca298d7383458ee`.

## 5. Fixed execution order

The first-pass batch order is frozen:

1. C1;
2. C2;
3. C3;
4. C4;
5. C5;
6. C6.

The order has no ranking meaning.

Candidate outcome text is withheld from the interactive console until all six attempts finish. No human or LLM decision is inserted between candidates.

## 6. Sentinel budget remains exactly 11

- C1: 1;
- C2: 2;
- C3: 2;
- C4: 4;
- C5: 1;
- C6: 1.

No new threshold, horizon, indicator/filter, asset subset, event-day rule, or time-of-day rule may be introduced after outcome computation.

## 7. Batch failure semantics

Mechanical/runtime failure is:

`SC001_C1C6_SENTINEL_BATCH_EXECUTION_FAIL`

It is not a strategy REJECT and not research evidence.

A candidate SURVIVE/REJECT/DEFER does not stop the remaining candidates.

If all six attempts finish with recognized terminal reports, the batch status is:

`SC001_C1C6_SENTINEL_BATCH_COMPLETE`

This token means only batch execution completed, not that any strategy survived.

## 8. Current hard gate

Before any sentinel outcome, require exact batch preflight:

`SC001_C1C6_SENTINEL_BATCH_PREFLIGHT_PASS`

Only after this exact PASS may the frozen batch runner execute in `run` mode.

## 9. Protected periods remain closed

No access is authorized to:

- July SOL/FIL/LTC/SUI holdout;
- July 16-30 gap;
- August 1-30 protected period;
- September SOL/FIL/LTC/SUI holdout;
- October Confirmation;
- legacy E006 March 22-30 SPOT Confirmation.

All batch outcomes are permanently:

`SELECTION_CALIBRATION_ONLY`

## 10. Current sequence

1. pull current GitHub state;
2. verify batch freeze identity;
3. syntax-check batch runner;
4. run batch `preflight` only;
5. require exact `SC001_C1C6_SENTINEL_BATCH_PREFLIGHT_PASS`;
6. if PASS, launch frozen batch `run` in `tmux`;
7. do not adapt between C1-C6;
8. require `SC001_C1C6_SENTINEL_BATCH_COMPLETE` or classify any mechanical problem separately;
9. only after all six outcomes inspect full results;
10. assign dispositions and perform MDE/block planning for survivors;
11. freeze diversified promotional research batch only after all dispositions are known.

Immediate next action: run frozen batch preflight on VPS, then launch the all-six batch only if exact PASS.
