# SC001 Current Roadmap and Stop Rules v3.1

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v3.0.md`

## 1. Terminal history / independence

E001-E007 remain terminal/closed exactly as previously recorded. SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Q2 / formal Validation / Final remain closed.

## 2. E008 completed engineering gates

- `E008_DATA_INVENTORY_PASS`.
- historical queue-feasibility v0.1 remains `E008_QUEUE_MODEL_FEASIBILITY_REVIEW` and is never relabeled.
- Feb-13 forensic: `CONCENTRATED_SOURCE_GAPS`.
- stale-latch v0.2: `E008_STALE_LATCH_MODEL_PASS` on 4/4 engineering days.
- synthetic queue mechanics: `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`, 22/22.
- non-promotional real-data mechanics: `E008_QUEUE_SIMULATOR_MECHANICAL_PASS`, 4/4.

## 3. Promotional chronology frozen

Discovery dates:
- 2024-01-06
- 2024-01-13
- 2024-01-19
- 2024-01-24
- 2024-02-06
- 2024-02-11
- 2024-02-21
- 2024-02-23

Confirmation dates remain unopened:
- 2024-01-08
- 2024-01-28
- 2024-02-10
- 2024-02-20

Date selection and strategy protocol remain frozen from v3.0.

## 4. Metadata preflight result

Exact terminal result:
`E008_DISCOVERY_METADATA_PREFLIGHT_PASS`

Observed frozen Discovery metadata totals:
- 8/8 L2 dates PASS;
- expected L2 compressed bytes: 3,724,622,435;
- expected unique trade compressed bytes: 76,647,648;
- disk reserve gate: PASS;
- no promotional market-data body had been downloaded at the time of preflight;
- no fills/spread capture/fees/inventory P&L/profitability calculated.

## 5. Current hard gate: staged data-only acquisition

Protocol:
`docs/research/sc001-e008-discovery-staged-acquisition-protocol-v1.0.md`

Implementation freeze:
`docs/research/sc001-e008-discovery-staged-acquisition-implementation-freeze-v1.0.md`

Runner:
`research/sc001/sc001_e008_discovery_staged_acquisition.py`

Frozen stages:
1. `trades`
2. `l2-a`: 2024-01-06 + 2024-01-13
3. `l2-b`: 2024-01-19 + 2024-01-24
4. `l2-c`: 2024-02-06 + 2024-02-11
5. `l2-d`: 2024-02-21 + 2024-02-23
6. `verify`

All stages are data engineering only and must preserve the 10 GB free-space reserve.

## 6. Acquisition stop rules

Do not:
- rediscover/substitute another source URL automatically if a frozen URL changes;
- change Discovery dates/batches after body access;
- open Confirmation bodies;
- calculate E008 maker fills/P&L before all acquisition stages and a separate full semantic replay/integrity qualification PASS;
- weaken queue/stale semantics;
- reduce fees or assume VIP/rebates;
- add TFI or prior features;
- open Q2/Validation/Final.

## 7. Immediate next action

On VPS:
1. `git pull --ff-only`;
2. syntax-check `research/sc001/sc001_e008_discovery_staged_acquisition.py`;
3. run acquisition `preflight` only;
4. if exact preflight PASS, run `trades` stage;
5. report result before starting L2 Batch A.

Do not launch the maker Discovery engine yet.
