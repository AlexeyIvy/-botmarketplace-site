# SC001 Current Roadmap and Stop Rules v4.10

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — E007R1 TRADE ACQUISITION VERIFIED / SEMANTIC QUALIFICATION OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.9.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact `E008_DISCOVERY_FAIL`. No prior verdict is reopened.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. Frozen universe / chronology

First-generation universe remains frozen:

BTC, ETH, SOL, DOGE, ORDI, FIL, UNI, XRP, LTC, OP, BCH, SUI — OKX linear USDT SWAPs.

E007R1 Discovery assets only:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH.

Asset holdout remains closed:

SOL, FIL, LTC, SUI.

Discovery performance time remains:

2024-07-01..2024-07-14 UTC.

August 2024 chronological Confirmation remains unopened.

## 3. E007R1 trade acquisition complete

Observed exact terminal:

`E007R1_TRADE_ACQUISITION_VERIFY_PASS`

Observed:

- verified files = `128`;
- verified total bytes = `468108915`;
- asset holdout accessed = false;
- August Confirmation accessed = false;
- strategy signal/PnL calculated = false;
- acquisition exit code = `0`.

Trade archive body access is now limited to the 8 frozen Discovery assets and boundary source dates already acquired.

## 4. Current hard gate — trade semantic integrity

Protocol:

`docs/research/sc001-e007r1-trade-semantic-integrity-protocol-v0.1.md`

Runner:

`research/sc001/sc001_e007r1_trade_semantic_integrity.py`

The stage preserves previously qualified Q006R historical archive semantics:

`archive D + archive D+1 -> retain created_time in UTC [D,D+1)`.

Source archives:

- 8 Discovery assets;
- 2024-06-30 through 2024-07-15 inclusive;
- 128 exact local ZIP files.

Reconstructed UTC target days:

- 2024-06-30 boundary/warm-up only;
- 2024-07-01..14 Discovery performance;
- 120 instrument-days total.

Required preflight token:

`E007R1_TRADE_SEMANTIC_PREFLIGHT_PASS`

Required full PASS token:

`E007R1_TRADE_SEMANTIC_INTEGRITY_PASS`

Full PASS requires:

- source files qualified = `128 / 128`;
- reconstructed UTC days qualified = `120 / 120`;
- zero malformed/instrument-mismatch rows;
- nondecreasing timestamps;
- no duplicate/backward trade IDs;
- zero target-day trade-ID gaps;
- both buy/sell sides per target day;
- complete `1440/1440` UTC minute coverage per target day;
- asset holdout remains closed;
- August Confirmation remains closed;
- no E007 signal/PnL.

## 5. Stop rules

Do not:

- calculate the E007/E007R1 80-bps trigger before semantic PASS;
- calculate half-reversion targets or gross returns before semantic PASS;
- access SOL/FIL/LTC/SUI bodies;
- access August Confirmation;
- access L2;
- use unresolved historical execution specs for execution/PnL;
- alter E007R1 parameters from data-quality output;
- reopen prior terminal experiments.

## 6. After semantic PASS

Only after `E007R1_TRADE_SEMANTIC_INTEGRITY_PASS` may SC001 run the already-planned cheap E007R1 **gross-feasibility** screen on the 8 Discovery assets.

That screen remains pre-execution and must not claim executable PnL. Exact historical `tickSz/lotSz/minSz/ctVal` and fee evidence remain mandatory before any promoted discrete execution/PnL.

Asset holdout and chronological Confirmation remain closed until later gates explicitly open them.

## 7. Immediate VPS action

1. `git pull --ff-only`;
2. syntax-check `sc001_e007r1_trade_semantic_integrity.py`;
3. run `preflight` and require exact PASS;
4. only then start `run` inside tmux;
5. review the final semantic token before any E007R1 gross-feasibility calculation.
