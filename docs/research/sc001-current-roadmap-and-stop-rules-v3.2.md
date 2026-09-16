# SC001 Current Roadmap and Stop Rules v3.2

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v3.1.md`

## 1. Independence / terminal history

E001-E007 remain terminal/closed exactly as previously recorded. SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Q2 / formal Validation / Final remain closed.

## 2. E008 engineering and simulator gates complete

- `E008_DATA_INVENTORY_PASS`.
- queue-feasibility v0.1 remains `E008_QUEUE_MODEL_FEASIBILITY_REVIEW` and is not relabeled.
- Feb-13 forensic = `CONCENTRATED_SOURCE_GAPS`.
- stale-latch v0.2 = `E008_STALE_LATCH_MODEL_PASS`, 4/4.
- synthetic queue mechanics = `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`, 22/22.
- non-promotional real-data mechanics = `E008_QUEUE_SIMULATOR_MECHANICAL_PASS`, 4/4.

## 3. Promotional chronology / strategy remain frozen

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

Canonical strategy protocol remains:
`docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`

No strategy parameter, fee, queue rule, TTL, latency, max hold or date may be changed from Discovery outcomes.

## 4. Discovery acquisition complete

All data-only acquisition stages passed:
- `E008_DISCOVERY_METADATA_PREFLIGHT_PASS`;
- `E008_DISCOVERY_ACQUISITION_PREFLIGHT_PASS`;
- `E008_DISCOVERY_TRADES_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_A_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_B_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_C_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_D_ACQUISITION_PASS`;
- `E008_DISCOVERY_ACQUISITION_VERIFY_PASS`.

Verified local file count: 24 = 16 trade archives + 8 L2 archives.

No promotional profitability has been calculated.

## 5. Current hard gate: full semantic integrity qualification

Protocol:
`docs/research/sc001-e008-discovery-semantic-integrity-protocol-v1.0.md`

Implementation freeze:
`docs/research/sc001-e008-discovery-semantic-integrity-implementation-freeze-v1.0.md`

Runner:
`research/sc001/sc001_e008_discovery_semantic_integrity.py`

Required sequence:
1. syntax check runner;
2. run `preflight` and require exact `E008_DISCOVERY_SEMANTIC_PREFLIGHT_PASS`;
3. run `run` in tmux;
4. require all 8 days exact `DAY_PASS` and terminal `E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS`.

This stage may calculate no hypothetical maker orders/fills, spread capture, markout, fees, inventory P&L or profitability.

L2 gaps >5 seconds are diagnostic only; the already-frozen stale-latch rule remains the execution safety response.

## 6. Stop rules

If semantic integrity returns REVIEW:
- do not run maker Discovery;
- do not substitute dates post hoc;
- do not weaken trade/L2 integrity rules;
- investigate only objective source/data-engineering defects;
- do not open Confirmation/Q2/Validation/Final.

If semantic integrity PASSes:
- still do not immediately calculate maker P&L;
- first implement/freeze the maker Discovery engine;
- pass a separate no-alpha implementation preflight + identity gate;
- only then allow one frozen E008 Discovery.

## 7. Immediate next action

On VPS in `~/botmarketplace-site`:
1. `git pull --ff-only`;
2. `python3 -m py_compile research/sc001/sc001_e008_discovery_semantic_integrity.py`;
3. `python3 -u research/sc001/sc001_e008_discovery_semantic_integrity.py preflight`;
4. only after exact preflight PASS, run `python3 -u research/sc001/sc001_e008_discovery_semantic_integrity.py run` inside tmux;
5. report the terminal token; do not launch maker Discovery.