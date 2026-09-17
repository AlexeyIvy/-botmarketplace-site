# SC001 Current Roadmap and Stop Rules v4.15

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — E009 METADATA PREFLIGHT PASS / STAGED TRADE ACQUISITION OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.14.md`

## 1. Binding terminal states

E001-E008 remain terminal/closed. E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL`. No rescue-tuning or reopening is allowed.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. E009 remains the active new family

Planning document remains:

`docs/research/sc001-e009-volatility-normalized-displacement-reversal-research-plan-v0.1.md`

Frozen E009 Discovery assets:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH.

Frozen Discovery performance:

`2024-09-01..2024-09-14` UTC.

Asset holdout remains CLOSED:

SOL, FIL, LTC, SUI.

October chronological Confirmation remains CLOSED.

August remains unrepurposed except archive label `2024-08-31` as the required D-1 source neighbor for reconstructing September 1 UTC.

## 3. Metadata preflight passed

Observed exact:

`E009_TRADE_METADATA_PREFLIGHT_PASS`

Observed:

- expected files = `128`;
- resolved files = `128`;
- expected total bytes = `419552195`;
- trade body downloaded = false;
- asset holdout accessed = false;
- October Confirmation accessed = false;
- August repurposed = false;
- strategy signal/PnL calculated = false.

Therefore controlled Discovery-body acquisition is now authorized under the staged protocol only.

## 4. Current hard gate — E009 staged trade acquisition

Protocol:

`docs/research/sc001-e009-trade-staged-acquisition-protocol-v0.1.md`

Runner:

`research/sc001/sc001_e009_trade_staged_acquisition.py`

Frozen batches:

- A = BTC + ETH;
- B = DOGE + ORDI;
- C = UNI + XRP;
- D = OP + BCH.

Required exact batch PASS tokens:

- `E009_TRADE_ACQUISITION_BATCH_A_PASS`
- `E009_TRADE_ACQUISITION_BATCH_B_PASS`
- `E009_TRADE_ACQUISITION_BATCH_C_PASS`
- `E009_TRADE_ACQUISITION_BATCH_D_PASS`

Required final verify:

`E009_TRADE_ACQUISITION_VERIFY_PASS`

Required final counts:

- verified files = `128`;
- verified total bytes = `419552195`.

## 5. Firewalls

During acquisition do not:

- access SOL/FIL/LTC/SUI;
- access October;
- access September 16+;
- calculate E009 signal/returns/PnL;
- access L2;
- infer historical execution specs from trade bodies;
- alter E009 parameters.

## 6. After acquisition verify PASS

Only after full local verification PASS:

1. create/freeze E009 trade semantic-integrity protocol using the corrected multi-asset rule from E007R1 v0.2;
2. qualify all 128 source archives and reconstructed September UTC days;
3. no 1440/1440 mandatory-minute rule; sparse-but-ID-continuous coverage remains diagnostic;
4. only after semantic PASS may the frozen E009 gross-feasibility implementation be run;
5. holdout and October remain closed.

## 7. Immediate VPS action

1. cancel any partially typed shell line if necessary;
2. `git pull --ff-only`;
3. syntax-check `research/sc001/sc001_e009_trade_staged_acquisition.py`;
4. launch A -> B -> C -> D -> verify in one tmux session with fail-closed chaining;
5. review exact verify PASS before semantic work.
