# SC001 Current Roadmap and Stop Rules v4.16

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — E009 ACQUISITION VERIFIED / SEMANTIC QUALIFICATION OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.15.md`

## 1. Binding terminal states

E001-E008 remain terminal/closed. E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL` with read-only postmortem complete. E009 is a new family and does not reopen earlier experiments.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. E009 governance

Discovery assets: BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH.

Asset holdout remains CLOSED: SOL, FIL, LTC, SUI.

Discovery performance dates: `2024-09-01..2024-09-14` UTC.

Boundary source labels: `2024-08-31` and `2024-09-15` only as required for causal UTC reconstruction.

October Confirmation remains CLOSED. August remains non-promotional and may not be repurposed as E009 evidence.

## 3. E009 acquisition complete

Observed exact:

- `E009_TRADE_METADATA_PREFLIGHT_PASS`;
- metadata files = `128 / 128`;
- expected total bytes = `419552195`;
- `E009_TRADE_ACQUISITION_VERIFY_PASS`;
- verified files = `128`;
- verified total bytes = `419552195`;
- holdout accessed = false;
- October Confirmation accessed = false;
- August repurposed = false;
- strategy signal/PnL calculated = false.

## 4. Current hard gate — E009 trade semantic integrity

Protocol:

`docs/research/sc001-e009-trade-semantic-integrity-protocol-v0.1.md`

Runner:

`research/sc001/sc001_e009_trade_semantic_integrity.py`

Use the qualified OKX UTC stitch:

`archive D + archive D+1 -> retain created_time in UTC [D,D+1)`.

The corrected multi-asset continuity rule from E007R1 v0.2 is binding:

- zero target-day trade-ID gaps;
- no duplicate/backward IDs;
- no timestamp reversal;
- exact schema/instrument/side/finite-positive price-size;
- both taker sides observed;
- minute coverage diagnostic only;
- sparse days may pass only as `SPARSE_BUT_ID_CONTINUOUS` when hard continuity remains intact;
- no forward-fill of empty future 5-second strategy buckets.

Required preflight token:

`E009_TRADE_SEMANTIC_PREFLIGHT_PASS`

Required full token:

`E009_TRADE_SEMANTIC_INTEGRITY_PASS`

Expected counts:

- source files = `128 / 128`;
- reconstructed UTC days = `120 / 120`.

## 5. Firewalls

Semantic qualification must not calculate E009 MAD volatility, Z-score, trigger, gross return, fees or PnL. It must not access holdout, October, L2, or historical execution specs.

## 6. After semantic PASS

Only after exact semantic PASS may the frozen E009 gross-feasibility implementation be finalized/identity-frozen and run once on the eight Discovery assets.

Any E009 gross FAIL is terminal for E009 v0.1 and blocks holdout/October/execution-PnL engineering. No rescue-tuning is permitted.

## 7. Immediate VPS action

Pull latest code, py-compile `sc001_e009_trade_semantic_integrity.py`, run `preflight`, require exact PASS, then launch `run` in tmux and review the final exact token before any E009 alpha calculation.
