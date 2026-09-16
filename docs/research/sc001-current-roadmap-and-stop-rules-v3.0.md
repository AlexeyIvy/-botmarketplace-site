# SC001 Current Roadmap and Stop Rules v3.0

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v2.9.md`

## 1. Terminal history

E001-E007 remain terminal/closed exactly as previously recorded. SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Q2 / formal Validation / Final remain closed.

## 2. E008 engineering gates complete

- `E008_DATA_INVENTORY_PASS`.
- historical queue-feasibility v0.1 remains `E008_QUEUE_MODEL_FEASIBILITY_REVIEW` and is never relabeled.
- Feb-13 forensic: `CONCENTRATED_SOURCE_GAPS`.
- stale-latch v0.2: `E008_STALE_LATCH_MODEL_PASS` on 4/4 engineering days.
- synthetic queue mechanics: `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`, 22/22.
- non-promotional real-data mechanics: `E008_QUEUE_SIMULATOR_MECHANICAL_PASS`, 4/4.

No promotional maker P&L has yet been calculated.

## 3. Frozen promotional chronology

Date freeze:
`docs/research/sc001-e008-discovery-date-freeze-v1.0.md`

Discovery dates:
- 2024-01-06
- 2024-01-13
- 2024-01-19
- 2024-01-24
- 2024-02-06
- 2024-02-11
- 2024-02-21
- 2024-02-23

Confirmation dates, unopened until Discovery PASS:
- 2024-01-08
- 2024-01-28
- 2024-02-10
- 2024-02-20

Selection is deterministic calendar-bin + SHA256, not outcome-driven.

## 4. Frozen E008 strategy protocol

Canonical protocol:
`docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`

Key rules:
- BTC-USDT-SWAP only;
- flat state quotes one 1-contract order at best bid and one at best ask;
- inventory bounded to +/-1 contract;
- 250 ms placement/cancel latency primary; 500 ms stress;
- 30 s quote TTL;
- 60 s max inventory hold;
- forced taker exit only as fail-safe after max hold;
- maker fee 2 bps/fill; taker fee 5 bps/fill; no VIP/rebate rescue;
- no cycle around funding boundaries;
- all conservative queue/stale rules preserved;
- base strategy uses no TFI or prior SC001 feature.

## 5. Discovery gates

All frozen gates in protocol v1.0 are mandatory. Core economic gates include:
- >=100 completed cycles across all 8 days;
- 8/8 active days;
- unresolved inventory = 0;
- forced taker exit share <=10%;
- mean net edge >=1.0 bps/cycle;
- trimmed mean >=0.5 bps;
- median >=0;
- positive days >=6/8;
- median daily mean >0;
- day-block bootstrap 95% LCB >0;
- concentration limits;
- both long-first and short-first breadth;
- 500 ms latency stress mean >=0 and total net >0;
- 2x initial queue-ahead stress mean >=0 and unresolved inventory=0.

Any failure => terminal `E008_DISCOVERY_FAIL` and blocks Confirmation.

## 6. Current hard gate: promotional metadata preflight

Runner:
`research/sc001/sc001_e008_discovery_metadata_preflight.py`

This stage may access only metadata/HEAD for the eight frozen Discovery L2 files and exact+D+1 trade archive labels.

It must not download/open promotional market-data bodies and must not calculate fills, spread capture, fees, inventory P&L or profitability.

Allowed terminal states:
- `E008_DISCOVERY_METADATA_PREFLIGHT_PASS`
- `E008_DISCOVERY_METADATA_PREFLIGHT_REVIEW`

## 7. Stop rules

Do not:
- substitute dates after seeing metadata or outcomes unless a new protocol version is frozen for an objective source-availability failure;
- open Confirmation L2 bodies before Discovery PASS;
- weaken queue/stale rules;
- reduce frozen fees or assume VIP/rebates;
- tune quote width/order size/TTL/latency/max hold from Discovery outcomes;
- add TFI or prior features;
- open Q2/Validation/Final.

## 8. Immediate next action

On VPS:
1. git pull --ff-only;
2. syntax-check `sc001_e008_discovery_metadata_preflight.py`;
3. run metadata-only preflight;
4. inspect exact terminal token and expected bytes/disk reserve;
5. do not download promotional bodies until PASS and a separate staged acquisition protocol is frozen.
