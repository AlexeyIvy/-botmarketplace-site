# SC001 Current Roadmap and Stop Rules v3.4

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP SNAPSHOT — MAKER DISCOVERY OPEN ONCE**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v3.3.md`

## 1. Independence / terminal history

E001-E007 remain terminal/closed exactly as previously recorded. SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Q2 / formal Validation / Final remain closed.

## 2. E008 data and mechanics gates complete

Completed and preserved:
- `E008_DATA_INVENTORY_PASS`;
- `E008_STALE_LATCH_MODEL_PASS`;
- `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`, 22/22;
- `E008_QUEUE_SIMULATOR_MECHANICAL_PASS`, 4/4;
- `E008_DISCOVERY_METADATA_PREFLIGHT_PASS`;
- `E008_DISCOVERY_ACQUISITION_PREFLIGHT_PASS`;
- `E008_DISCOVERY_TRADES_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_A_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_B_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_C_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_D_ACQUISITION_PASS`;
- `E008_DISCOVERY_ACQUISITION_VERIFY_PASS`, 24 verified files;
- `E008_DISCOVERY_SEMANTIC_PREFLIGHT_PASS`;
- `E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS`, 8/8 DAY_PASS.

No maker economics were calculated by the semantic stage.

## 3. Frozen Discovery chronology

Discovery dates remain exactly:
- 2024-01-06
- 2024-01-13
- 2024-01-19
- 2024-01-24
- 2024-02-06
- 2024-02-11
- 2024-02-21
- 2024-02-23

Confirmation dates remain frozen and unopened:
- 2024-01-08
- 2024-01-28
- 2024-02-10
- 2024-02-20

No date substitution is permitted.

## 4. Frozen maker implementation

Canonical strategy protocol:
`docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`

Implementation protocol:
`docs/research/sc001-e008-maker-discovery-implementation-protocol-v1.0.md`

Implementation freeze manifest:
`docs/research/sc001-e008-maker-discovery-implementation-freeze-v1.0.json`

Runner:
`research/sc001/sc001_e008_maker_discovery.py`

No strategy parameter, date, fee, queue rule, stale rule, TTL, latency, max hold, order quantity, funding window, stress definition or promotion gate may be changed from Discovery outcomes.

## 5. Maker implementation gate passed

Observed exact PASS on VPS after pulling frozen implementation:
- `E008_MAKER_DISCOVERY_IMPLEMENTATION_PREFLIGHT_PASS`;
- `E008_MAKER_DISCOVERY_IDENTITY_GATE_PASS`;
- verified frozen implementation files = 8;
- verified market source files = 24;
- maker orders/fills/spread capture/fees/inventory PnL/profitability calculated = False;
- Confirmation/Q2/Validation/Final = CLOSED.

Therefore the no-alpha maker implementation preflight + identity gate is complete.

## 6. Current hard gate: one frozen promotional E008 Discovery run

Exactly one promotional Discovery run is now authorized using only the frozen implementation and frozen eight Discovery days.

Run only:
`python3 -u research/sc001/sc001_e008_maker_discovery.py run`

Prefer tmux and preserve the complete terminal log.

The run evaluates only the predeclared frozen scenarios:
- primary: 250 ms placement/cancel/taker-proxy latency, 1x initial queue-ahead;
- latency stress: 500 ms, 1x initial queue-ahead;
- queue stress: 250 ms, 2x initial queue-ahead.

The run must not access Confirmation bodies, Q2, formal Validation or Final.

## 7. Terminal outcomes

If any mandatory Discovery gate fails, terminal state is:
`E008_DISCOVERY_FAIL`

Then:
- E008 is terminal failed;
- no rescue tuning;
- do not alter dates, queue/stale rules, fees, TTL, latency, max hold, order size or gates;
- do not open Confirmation/Q2/Validation/Final.

Only exact:
`E008_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`

may open the already-frozen Confirmation stage once. Even then, do not alter Discovery parameters from the observed result.

## 8. Immediate next action

On VPS in `~/botmarketplace-site`:
1. `git pull --ff-only`;
2. confirm no duplicate maker Discovery tmux session exists;
3. start exactly one `research/sc001/sc001_e008_maker_discovery.py run` inside a dedicated tmux session with output tee'd to a persistent log;
4. wait for the terminal token;
5. do not rerun if a valid complete Discovery report already exists;
6. report the terminal token and failed gates or PASS metrics before any further action.
