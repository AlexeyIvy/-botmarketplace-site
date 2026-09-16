# SC001 Current Roadmap and Stop Rules v4.9

Date: 2026-09-16
Status: **CURRENT SC001 ROADMAP — E007R1 TRADE METADATA PASS / STAGED ACQUISITION OPEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.8.md`

## 1. Binding state

E001-E008 remain terminal/closed. E007R1 is a new strict-replication family and does not reopen E007.

Frozen universe/chronology remain unchanged. Asset holdout and August Confirmation remain closed.

## 2. Technical validation already complete

- common accounting synthetic validation: `20/20 PASS`;
- normalized schema + taker kernel synthetic validation: `24/24 PASS`;
- historical execution-spec inventory complete, but exact historical discrete specs remain unresolved and block promoted discrete execution/PnL.

## 3. E007R1 metadata preflight complete

Observed exact:

`E007R1_TRADE_METADATA_PREFLIGHT_PASS`

Observed:
- expected_files = 128;
- resolved_files = 128;
- expected_total_bytes = 468,108,915;
- trade body downloaded = false;
- asset holdout accessed = false;
- August Confirmation accessed = false;
- strategy signal/PnL calculated = false.

## 4. Current hard gate — staged Discovery trade acquisition

Protocol:
`docs/research/sc001-e007r1-trade-staged-acquisition-protocol-v0.1.md`

Runner:
`research/sc001/sc001_e007r1_trade_staged_acquisition.py`

Frozen batches:
- A: BTC + ETH;
- B: DOGE + ORDI;
- C: UNI + XRP;
- D: OP + BCH.

Each batch contains exactly 32 files and requires its exact PASS token.

After A/B/C/D PASS, require:

`E007R1_TRADE_ACQUISITION_VERIFY_PASS`

with `verified_files = 128` and aggregate bytes equal to the metadata-preflight total.

## 5. Firewall

Acquisition/verify must not:
- access SOL/FIL/LTC/SUI holdout bodies;
- access August Confirmation;
- acquire L2;
- calculate strategy signal/gross/PnL;
- infer unresolved historical specs;
- change E007 frozen mechanism.

## 6. After full acquisition verify PASS

1. perform semantic trade qualification for all 128 Discovery archives;
2. only after semantic PASS run one gross-only E007R1 feasibility screen on the 8 Discovery assets;
3. no asset-holdout or August access during Discovery feasibility;
4. if gross mechanism fails frozen feasibility gates, stop E007R1 without spending effort on full historical execution-spec reconstruction;
5. only if gross feasibility survives, finish exact historical spec/fee reconstruction and controlled real-data taker execution validation before any promoted net PnL.

## 7. Immediate VPS action

Pull latest code, syntax-check the staged acquisition runner, then run batches A→D and local verify inside one tmux session with fail-closed `&&` chaining.