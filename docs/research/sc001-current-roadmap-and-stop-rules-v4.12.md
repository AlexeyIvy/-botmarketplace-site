# SC001 Current Roadmap and Stop Rules v4.12

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — E007R1 SEMANTIC PASS / GROSS-FEASIBILITY IMPLEMENTATION FROZEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.11.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact `E008_DISCOVERY_FAIL`. Nothing in E007R1 reopens E007.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. E007R1 Discovery data state

Acquisition remains exact PASS:

- `E007R1_TRADE_ACQUISITION_VERIFY_PASS`;
- verified files = `128`;
- verified total bytes = `468108915`.

Semantic v0.2 now exact PASS:

- `E007R1_TRADE_SEMANTIC_INTEGRITY_PASS`;
- source files qualified = `128 / 128`;
- reconstructed UTC days qualified = `120 / 120`;
- sparse-but-ID-continuous days = `27`;
- asset holdout accessed = false;
- August Confirmation accessed = false;
- strategy signal/PnL calculated = false;
- semantic v0.2 exit code = `0`.

The prior v0.1 semantic failure on DOGE 2024-06-30 (`1439/1440` active minutes) is retained as an audit trail and classified as a data-quality-rule defect, not a strategy result. Minute completeness is diagnostic; zero trade-ID gaps, no duplicate/backward IDs, valid UTC stitch and valid rows are the binding continuity evidence.

## 3. Gross-feasibility protocol remains frozen

Binding protocol created before July trade-body access:

`docs/research/sc001-e007r1-multiasset-gross-feasibility-protocol-v0.1.md`

Discovery assets only:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH.

Performance dates remain `2024-07-01..2024-07-14` UTC.

Asset holdout remains CLOSED: SOL, FIL, LTC, SUI.

August chronological Confirmation remains CLOSED.

## 4. Gross-feasibility implementation freeze

Runner:

`research/sc001/sc001_e007r1_gross_feasibility.py`

Identity freeze:

`docs/research/sc001-e007r1-gross-feasibility-implementation-freeze-v1.0.json`

Before any gross output the runner must pass exact no-alpha/identity preflight:

`E007R1_GROSS_FEASIBILITY_IMPLEMENTATION_PREFLIGHT_PASS`

The implementation preserves the old E007 mechanism exactly:

- 5s grid;
- [t-5s,t) current VWAP;
- [t-65s,t-60s) anchor VWAP;
- strict 80 bps crossing trigger;
- reversal direction;
- 50% frozen arithmetic retracement;
- primary latency 500 ms;
- stress 1000/2000 ms;
- 5s proxy tolerance;
- 10-minute max hold;
- 4 decisions/day;
- 10-minute cooldown;
- no new decision after 23:49 UTC;
- no per-asset retuning.

Sparse 5-second buckets remain invalid; no forward-fill is permitted.

## 5. Cross-asset anti-selection rule

For cross-instrument equal-weight/median aggregates, all 8 Discovery assets remain in the denominator.

If an instrument has zero completed events, its aggregate instrument mean is treated as `0 bps` rather than silently dropping the instrument. Pooled trade-level metrics use completed events only.

This rule is frozen before first gross output.

## 6. Gross feasibility terminal states

Exact PASS:

`E007R1_GROSS_FEASIBILITY_PASS`

Exact FAIL:

`E007R1_GROSS_FEASIBILITY_FAIL`

All gates in protocol v0.1 remain mandatory. FAIL blocks further E007R1 historical-spec/L2/executable-PnL engineering.

PASS is only permission to continue engineering; it is not Confirmation or executable profitability proof.

## 7. Firewalls

Gross feasibility must not:

- access SOL/FIL/LTC/SUI bodies;
- access August Confirmation;
- access July 16..30;
- access L2;
- use unresolved historical execution specs;
- calculate discrete contract PnL;
- calculate net PnL or claim exact historical fees;
- change E007/E007R1 parameters after output.

## 8. Immediate action

1. `git pull --ff-only`;
2. syntax-check `sc001_e007r1_gross_feasibility.py`;
3. run `preflight` and require exact implementation PASS;
4. only then run one gross-feasibility `run` in tmux;
5. review exact PASS/FAIL and gates before any further E007R1 engineering.
