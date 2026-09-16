# SC001 Current Roadmap and Stop Rules v4.4

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — FIRST MULTI-ASSET UNIVERSE + FRESH Q3 ROLES FROZEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.3.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact `E008_DISCOVERY_FAIL`.

No prior verdict is reopened. SC001 remains fully independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. Historical-universe governance complete for first generation

Completed exact gates:

- `SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_PASS`;
- 66 both-anchor historical OKX candidates;
- `SC001_PREPERIOD_LIQUIDITY_CALIBRATION_PASS`;
- 50 liquidity-eligible candidates;
- `SC001_CONTRACT_STRUCTURE_SPEC_AVAILABILITY_AUDIT_PASS`;
- all proposed top-12 structurally comparable.

No strategy signal/PnL was used to select the universe.

## 3. Exact first-generation universe frozen

Canonical artifact:

`docs/research/sc001-first-generation-multi-asset-universe-freeze-v1.0.json`

Exact ranked instruments:

1. BTC-USDT-SWAP
2. ETH-USDT-SWAP
3. SOL-USDT-SWAP
4. DOGE-USDT-SWAP
5. ORDI-USDT-SWAP
6. FIL-USDT-SWAP
7. UNI-USDT-SWAP
8. XRP-USDT-SWAP
9. LTC-USDT-SWAP
10. OP-USDT-SWAP
11. BCH-USDT-SWAP
12. SUI-USDT-SWAP

No manual substitution is permitted from later strategy outcomes.

Historical exact execution specs remain intentionally unresolved. Current metadata must not be treated as historical proof.

## 4. Fresh chronology and asset holdout frozen

Protocol:

`docs/research/sc001-fresh-chronology-and-asset-holdout-protocol-v0.1.md`

### Discovery assets — 8
BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH.

Discovery performance dates:
`2024-07-01..2024-07-14` UTC.

### Asset holdout — 4
SOL, FIL, LTC, SUI.

Asset-holdout performance dates:
`2024-07-01..2024-07-14` UTC.

This is cross-asset replication, not chronological Confirmation.

### Chronological Confirmation
All 12 frozen instruments on:
`2024-08-01..2024-08-14` UTC.

Confirmation bodies remain protected/unopened until authorized by prior frozen gates.

### Boundary-only dates
- 2024-06-30
- 2024-07-15
- 2024-07-31
- 2024-08-15

### Unassigned gap
`2024-07-16..2024-07-30` remains unopened and must not be mined opportunistically.

## 5. Contamination registry updated

Current registry:

`docs/research/sc001-contamination-registry-v0.3.json`

The six pre-period liquidity calibration dates remain engineering contaminated.

July/August role reservations are now recorded as protected unopened evidence and may not migrate between roles after outcomes.

## 6. Current hard gate — no promotional strategy body access yet

Do **not** begin E007 or any other strategy simulation yet.

Before new promotional execution/PnL, complete:

1. historical execution-spec handling protocol for the frozen 12/chronology;
2. common normalized market-data schema + immutable event semantics;
3. independent fill/position/cash/accounting ledger infrastructure;
4. taker execution kernel for E007-class strategies;
5. golden hand-calculated fixtures;
6. causal future-access tests;
7. property/fuzz/fault injection where applicable;
8. deterministic replay;
9. independent accounting recomputation;
10. reference/differential validation;
11. one-shot run manifest + duplicate-run protection;
12. cheap E007 economic-feasibility audit before full multi-asset replay.

## 7. Engineering-data rule

Kernel/accounting engineering should preferentially reuse already contaminated BTC March-2024 / E008 engineering data rather than consuming fresh Q3 evidence.

Fresh July/August bodies are not debugging data.

## 8. Historical spec firewall

Current public instrument metadata may be used only for structural diagnostics.

It must not be silently treated as historical 2024 values for:

- tickSz;
- lotSz;
- minSz;
- ctVal;
- fee schedule;
- funding schedule.

Exact historical handling must be frozen before execution/PnL.

## 9. Legacy replication priority unchanged

First strict replication target remains the E007 displacement -> partial mean-reversion mechanism under a new experiment ID, because it retained material gross signal and uses the simpler taker kernel.

E006 follows after multi-leg execution is validated. E002 TFI remains auxiliary-only. Passive-maker research remains a separate later family and never reopens E008.

## 10. Immediate next action

Proceed to historical execution-spec reconstruction/handling and common normalized accounting infrastructure. No broad L2 acquisition and no July/August strategy body access yet.
