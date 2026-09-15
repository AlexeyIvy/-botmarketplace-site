# SC001-E002 OKX Q1 Taker Economics — Implementation Repair v0.2

Date: 2026-09-15  
Status: **PRE-OUTPUT IMPLEMENTATION REPAIR / FINANCIAL RULES UNCHANGED**

## 1. Trigger

The first implementation preflight of `sc001_e002_okx_q1_taker_economics.py` failed before any economics output because the engine still referenced metadata/funding artifact filenames from preflight v0.2, while the successful parser-repaired metadata preflight wrote v0.3 artifacts.

Observed failure class: missing required metadata file.  
No taker-economics day worker was launched and no execution P&L / net-edge result was observed.

## 2. Additional code audit before first economics output

Because the run had not started, the implementation was re-audited before repair. One conservative state-management defect was identified:

- when an entry had filled but the frozen exit book state could not fully fill the required quantity, the v0.1 engine counted the trade as unfilled but later allowed new entries after the exit timestamp;
- under the frozen one-position rule, that is inconsistent because the existing position was never fully closed;
- correct conservative behavior is to block all later candidates for that scenario/day once a filled entry cannot be fully exited at its frozen exit execution state.

This repair only makes the implementation conform to the already-frozen position-state rule. It cannot improve a failed economics result after observation because no economics result existed before the repair.

## 3. Authoritative implementation

Use:

`research/sc001/sc001_e002_okx_q1_taker_economics_v0_2.py`

This adapter loads the v0.1 parent engine and changes only:

1. metadata path to `sc001_e002_okx_q1_execution_metadata_preflight_v0_3.json`;
2. funding path to `sc001_e002_okx_q1_funding_rates_v0_3.json`;
3. validates that both successful artifacts are version `0.3` and that the funding source is the official `market-data-history module=3` archive path;
4. after a filled entry, if the frozen exit cannot fully fill visible adjusted depth, the scenario remains open and all later candidates that day are skipped;
5. implementation identity SHA256 is calculated over both the parent engine and the v0.2 adapter so stale v0.1 checkpoints cannot be reused as v0.2.

## 4. Financial/statistical freeze unchanged

No change to:

- four Q1 dates;
- E002 TFI definition;
- rolling 720 causal threshold history;
- q90 / q95 / q97.5 grid;
- q95 primary status;
- 5-second horizon;
- 100 / 250 / 500 ms latency grid;
- 0 / 25 / 50% depth haircuts;
- 1k / 10k / 50k target notionals;
- 0.01 BTC contract value;
- Q1 1-contract min/step;
- 0.1 tick;
- 5 bps taker fee per fill;
- conservative absolute funding treatment;
- visible-book VWAP rules;
- no-pyramiding / one-position rule;
- Base / Stress A / Stress B gates;
- PASS / WEAK / FAIL semantics;
- Q2 / Validation / Final firewall;
- no-rescue rule.

## 5. Run rule

Before any economics run, execute the v0.2 adapter in `preflight` mode and require:

`TAKER_ECONOMICS_IMPLEMENTATION_PREFLIGHT_PASS`

Only then may the same v0.2 adapter be run in `run` mode.

Do not use the v0.1 economics engine for the official Q1 result.
