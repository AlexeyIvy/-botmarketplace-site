# SC001 Current Roadmap and Stop Rules v2.5

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v2.4.md`

## 1. Terminal history unchanged

- E001: terminal `FAIL`.
- E002 standalone: terminal `TAKER_ECONOMICS_FAIL`; TFI retained only as future auxiliary knowledge.
- E003: terminal `E003_DISCOVERY_FAIL`.
- E004: terminal `E004_DISCOVERY_FAIL`.
- E005: closed.
- E006: terminal `E006_DISCOVERY_FAIL`.
- E007: terminal `E007_DISCOVERY_FAIL`.

SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Q2 / formal Validation / Final remain closed.

## 2. Active candidate: SC001-E008

Candidate family:

**conservative passive maker spread capture on OKX BTC-USDT-SWAP with explicit pessimistic queue/adverse-selection modeling.**

Planning document:

`docs/research/sc001-e008-passive-maker-spread-capture-research-plan-v0.1.md`

No E008 hypothetical fill, spread-capture, inventory P&L or profitability output is authorized yet.

Base E008 excludes TFI/FLOW_IMPULSE/E004 compression/E006 basis/E007 displacement.

## 3. Data inventory result

The no-alpha/no-P&L inventory stage returned:

`E008_DATA_INVENTORY_PASS`

All four engineering days have:

- qualified Q009 parent/day PASS status;
- local exact-size L2 archive body;
- corresponding transaction tape present.

Engineering days:

- 2024-01-14;
- 2024-01-31;
- 2024-02-12;
- 2024-02-13.

These dates are contaminated by prior E002 infrastructure/research use and therefore may be used only for data-model/simulator engineering, not as sole promotional E008 Discovery evidence.

## 4. Current hard gate: conservative queue-model feasibility audit

Frozen protocol:

`docs/research/sc001-e008-queue-model-feasibility-audit-protocol-v0.1.md`

Frozen implementation identity:

`docs/research/sc001-e008-queue-model-feasibility-implementation-freeze-v0.1.md`

Executables:

- `research/sc001/sc001_e008_queue_audit_lib.py`;
- `research/sc001/sc001_e008_queue_model_feasibility.py`.

This audit may only determine whether qualified L2/trade data support a pessimistic queue model.

It must not calculate:

- hypothetical fills;
- fill rate;
- spread capture;
- inventory;
- hypothetical post-fill markout;
- maker fees/rebates;
- maker P&L;
- profitability.

## 5. Frozen conservative queue principle

If the feasibility audit PASSes, any later simulator must start from these lower-bound rules:

1. existing displayed quantity is ahead of our order;
2. cancellation / quote disappearance gives zero queue progress;
3. only causally observed compatible transaction volume may reduce queue-ahead;
4. exact FIFO is not claimed because exact order IDs are absent;
5. same-millisecond L2/trade ordering is ambiguous and cannot be resolved optimistically;
6. partial fills must be explicit;
7. generous fill assumptions are forbidden.

## 6. Feasibility PASS gates

Every engineering day must preserve qualified source integrity and satisfy the frozen structural gates, including:

- full trade UTC-day reconstruction;
- valid initial L2 snapshot and noncrossed/nonempty replay;
- >=99.9% strictly-prior valid-book availability for non-same-ms trades;
- >=99.5% prior-book age <=5 s;
- >=95% side/price compatibility among <=5 s aligned trades;
- >=99.99% usable best-book states with positive displayed size and aggregate order count;
- both buy and sell trades present.

Terminal states:

- `E008_QUEUE_MODEL_FEASIBILITY_PASS`;
- `E008_QUEUE_MODEL_FEASIBILITY_REVIEW`.

A REVIEW does not authorize weakening the model after seeing results.

## 7. After feasibility PASS

A PASS still does **not** authorize maker profitability.

Next steps would be:

1. freeze queue-simulator state machine and synthetic fixtures;
2. validate mechanics on these four contaminated engineering days without treating their P&L as promotional evidence;
3. preselect untouched additional Q1 Discovery dates before opening/downloading their L2 bodies for E008 profitability;
4. freeze quoting width/order size/cancel/inventory/fee/economics gates before first promotional E008 P&L;
5. run exactly one E008 Discovery;
6. only full PASS may open separately frozen untouched Confirmation dates.

## 8. Immediate next action

On the qualified VPS:

1. `git pull --ff-only`;
2. Python syntax-check both E008 queue-audit files;
3. run only `sc001_e008_queue_model_feasibility.py`;
4. inspect terminal PASS/REVIEW and structural diagnostics;
5. do not run any maker fill/P&L simulator yet.
