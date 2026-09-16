# SC001 Current Roadmap and Stop Rules v4.8

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — SPEC INVENTORY PASS / E007R1 GROSS-FEASIBILITY PREFLIGHT OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.7.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. No prior verdict is reopened.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. Synthetic infrastructure gates complete

Completed:

- `SC001_COMMON_ACCOUNTING_CORE_VALIDATION_PASS`, 20/20;
- `SC001_TAKER_KERNEL_SYNTHETIC_VALIDATION_PASS`, 24/24.

No July/August reserved market body was opened by those stages.

## 3. Historical execution-spec inventory complete

Observed exact:

`SC001_HISTORICAL_EXECUTION_SPEC_INVENTORY_PASS`

Observed:
- frozen instruments inventoried = 12 / 12;
- current metadata used as historical proof = false;
- July/August market-data body accessed = false;
- strategy signal/PnL calculated = false;
- exact historical execution specs remain unresolved/incomplete.

This is not a failure. It means the evidence inventory completed honestly without inventing historical values.

## 4. Research-order optimization

Binding doctrine remains **economics before engineering**.

Full exact `tickSz/lotSz/minSz/ctVal` reconstruction is still mandatory before promoted discrete execution/PnL.

However, before spending further engineering effort on those fields, SC001 opens a cheaper **gross-only E007R1 feasibility screen** that does not depend on contract discreteness, L2 fills or USDT PnL.

If the strict E007 mechanism lacks broad gross headroom across the frozen Discovery assets, further E007R1 execution-spec/L2 work stops.

## 5. E007R1 protocol frozen

Protocol:

`docs/research/sc001-e007r1-multiasset-gross-feasibility-protocol-v0.1.md`

Discovery assets only:

- BTC-USDT-SWAP
- ETH-USDT-SWAP
- DOGE-USDT-SWAP
- ORDI-USDT-SWAP
- UNI-USDT-SWAP
- XRP-USDT-SWAP
- OP-USDT-SWAP
- BCH-USDT-SWAP

Performance window: `2024-07-01..2024-07-14`.

Boundary-only archive dates: `2024-06-30` and `2024-07-15`.

Asset holdout remains closed: SOL, FIL, LTC, SUI.

August `2024-08-01..14` Confirmation remains closed.

July `2024-07-16..30` remains unopened/unassigned.

## 6. Current hard gate — metadata-only trade identity preflight

Runner:

`research/sc001/sc001_e007r1_trade_metadata_preflight.py`

Expected set:

8 Discovery instruments × 16 archive dates = `128` exact OKX daily trade archives.

Required exact terminal:

`E007R1_TRADE_METADATA_PREFLIGHT_PASS`

PASS requires:
- all 128 exact filenames uniquely resolved;
- trusted `static.okx.com` URL identity;
- positive HEAD content length for every file;
- total expected bytes within frozen cap;
- no trade body downloaded;
- no L2 body downloaded;
- no strategy signal/PnL;
- no asset-holdout access;
- no August Confirmation access.

## 7. After preflight PASS

1. review expected total download size;
2. freeze staged trade-only acquisition batches;
3. download/verify only the 8 Discovery-asset trade archives needed for July gross feasibility;
4. semantic/UTC qualification of those trade bodies;
5. run exactly one frozen E007R1 gross-feasibility screen;
6. if `E007R1_GROSS_FEASIBILITY_FAIL`, stop E007R1 before L2/spec engineering;
7. only if `E007R1_GROSS_FEASIBILITY_PASS`, resume exact historical execution-spec reconstruction + real-data taker execution work;
8. asset holdout remains unopened until Discovery gross feasibility is reviewed;
9. August Confirmation remains unopened until later protocol gates.

## 8. Stop rules

Do not:
- open SOL/FIL/LTC/SUI during current Discovery feasibility;
- open August Confirmation;
- open July 16..30;
- calculate promoted PnL before exact historical specs are resolved;
- change the old E007 trigger/target/hold/latency rules from outcomes;
- drop losing Discovery symbols from breadth denominators;
- reopen prior terminal experiments.
