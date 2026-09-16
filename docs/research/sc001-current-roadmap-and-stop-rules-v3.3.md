# SC001 Current Roadmap and Stop Rules v3.3

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v3.2.md`

## 1. Independence / terminal history

E001-E007 remain terminal/closed exactly as previously recorded. SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Nothing in SC001 may alter their frozen rules, decisions or forward clocks.

Confirmation / Q2 / formal Validation / Final remain closed unless explicitly opened by a later exact promotion token.

## 2. E008 prerequisite stack complete

Engineering/data prerequisites remain:

- `E008_DATA_INVENTORY_PASS`;
- queue-feasibility v0.1 remains `E008_QUEUE_MODEL_FEASIBILITY_REVIEW` and is not relabeled;
- Feb-13 forensic = `CONCENTRATED_SOURCE_GAPS`;
- `E008_STALE_LATCH_MODEL_PASS`, 4/4;
- `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`, 22/22;
- `E008_QUEUE_SIMULATOR_MECHANICAL_PASS`, 4/4;
- `E008_DISCOVERY_METADATA_PREFLIGHT_PASS`;
- `E008_DISCOVERY_ACQUISITION_PREFLIGHT_PASS`;
- all staged trades/L2 acquisition PASS tokens;
- `E008_DISCOVERY_ACQUISITION_VERIFY_PASS`, exactly 24 verified files.

## 3. Full Discovery semantic integrity now PASS

The frozen semantic stage completed on all eight frozen Discovery dates with:

`E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS`

and:

`qualified_day_count = 8 / 8`

The semantic output firewall remained exact:

- maker orders/fills = not calculated;
- spread capture / markout = not calculated;
- fees = not calculated;
- inventory P&L / profitability = not calculated;
- TFI = not used;
- Confirmation/Q2/Validation/Final = closed.

Therefore semantic data qualification is complete and the separate maker-engine implementation stage may open. Semantic PASS itself did not authorize maker P&L.

## 4. Promotional chronology remains frozen

Discovery dates:

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

## 5. Maker Discovery implementation frozen before first P&L

Canonical strategy protocol remains:

`docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`

New implementation-level freeze:

- implementation protocol: `docs/research/sc001-e008-maker-discovery-implementation-protocol-v1.0.md`;
- implementation freeze manifest: `docs/research/sc001-e008-maker-discovery-implementation-freeze-v1.0.json`;
- runner: `research/sc001/sc001_e008_maker_discovery.py`.

Frozen Git identities at this roadmap snapshot:

- maker implementation protocol blob: `3c69ef62eb1757456adf808eb134f8ed95646c23`;
- maker runner blob: `db36513655f0df3af135a1651027d02b2c9ec6db`;
- implementation freeze manifest blob: `ea033a43e21839f804cb7c6a4d59c5fa567508ff`.

The manifest also pins inherited maker/semantic/queue/stale protocol and executable identities.

No strategy parameter, date, fee, queue rule, stale rule, TTL, latency, max hold, order quantity, funding window, stress definition or promotion gate may be altered from Discovery outcomes.

## 6. Current hard gate: no-alpha maker implementation preflight + identity gate

Before any promotional maker order/fill/P&L simulation, perform only:

1. pull the frozen implementation from GitHub;
2. syntax-check `research/sc001/sc001_e008_maker_discovery.py`;
3. run `python3 -u research/sc001/sc001_e008_maker_discovery.py preflight`;
4. require both exact terminal tokens:
   - `E008_MAKER_DISCOVERY_IMPLEMENTATION_PREFLIGHT_PASS`;
   - `E008_MAKER_DISCOVERY_IDENTITY_GATE_PASS`;
5. require 24 market source files verified against their frozen SHA256 identities;
6. require the preflight firewall to state that maker orders/fills/spread capture/fees/inventory P&L/profitability were not calculated.

If either exact token is absent, maker Discovery remains CLOSED.

The preflight must not create hypothetical maker orders or calculate fills/economics.

## 7. Promotional Discovery remains CLOSED until dual preflight PASS is reviewed

Do not run maker `run` in the same command block as the first preflight.

Only after the dual exact PASS has been observed and reviewed may one frozen promotional E008 Discovery run be launched, preferably inside tmux.

That one run evaluates only the predeclared frozen scenarios:

- primary: 250 ms placement/cancel/taker-proxy latency, 1x initial queue;
- latency stress: 500 ms, 1x initial queue;
- queue stress: 250 ms, 2x initial queue-ahead.

No post-outcome tuning or rerun with changed parameters is permitted.

## 8. Discovery terminal rules remain unchanged

Any failed mandatory Discovery gate => exact terminal:

`E008_DISCOVERY_FAIL`

and E008 becomes terminal at Discovery; Confirmation/Q2/Validation/Final remain closed. Do not rescue-tune.

Only all mandatory gates PASS => exact terminal:

`E008_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE`

Even then, stop first, freeze/report the Discovery outcome, and only then open the already-frozen Confirmation chronology exactly once under a separately controlled stage.

## 9. Immediate next action on VPS

In `~/botmarketplace-site`:

1. `git pull --ff-only`;
2. `python3 -m py_compile research/sc001/sc001_e008_maker_discovery.py`;
3. run maker `preflight` only;
4. require exact dual PASS + 24 verified source files;
5. report the result;
6. do **not** run maker `run` yet.

Confirmation / Q2 / Validation / Final remain CLOSED.
