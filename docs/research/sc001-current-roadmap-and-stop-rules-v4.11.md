# SC001 Current Roadmap and Stop Rules v4.11

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — E007R1 SEMANTIC RULE CORRECTED / RE-RUN OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.10.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact `E008_DISCOVERY_FAIL`. No prior verdict is reopened.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. Frozen E007R1 scope remains unchanged

Discovery assets:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH.

Asset holdout remains closed:

SOL, FIL, LTC, SUI.

Discovery performance dates remain:

2024-07-01..2024-07-14 UTC.

2024-06-30 remains boundary/warm-up only.

August Confirmation remains unopened.

No E007R1 gross-feasibility output has yet been calculated.

## 3. Acquisition remains exact PASS

Binding parent:

`E007R1_TRADE_ACQUISITION_VERIFY_PASS`

- verified files = `128`;
- verified total bytes = `468108915`;
- asset holdout accessed = false;
- August Confirmation accessed = false;
- strategy signal/PnL calculated = false.

## 4. First semantic run stopped fail-closed

Observed failure before any strategy/economic output:

`DOGE-USDT-SWAP 2024-06-30: 1439/1440 UTC minute buckets`

The runner exited nonzero. This was a data-quality gate stop, not a network failure and not a strategy result.

## 5. Methodology review finding

The v0.1 semantic protocol incorrectly treated `1440/1440 minute buckets observed` as a universal multi-asset integrity requirement.

That rule had been inherited from BTC Q006R diagnostics, where every minute happened to contain trades. In a multi-asset setting, a minute with zero trades is not evidence of missing data when:

- timestamps remain causally ordered;
- trade IDs remain strictly increasing;
- reconstructed UTC trade-ID gaps are zero;
- no duplicate/backward rows occur;
- instrument and row semantics remain valid.

Therefore the old rule conflated **market inactivity** with **data loss**.

## 6. Corrected binding semantic protocol

Current protocol:

`docs/research/sc001-e007r1-trade-semantic-integrity-protocol-v0.2.md`

Runner:

`research/sc001/sc001_e007r1_trade_semantic_integrity.py`

The strategy, dates, assets, threshold, horizon and economics are unchanged.

Hard integrity still requires:

- CRC/member/header validity;
- exact instrument;
- valid side/price/size/timestamp/trade ID;
- nondecreasing timestamps;
- strictly increasing trade IDs;
- zero reconstructed trade-ID gaps;
- no duplicate/backward rows;
- both buy/sell sides;
- nonempty target day.

Minute coverage is now diagnostic:

- `COMPLETE_1440`, or
- `SPARSE_BUT_ID_CONTINUOUS`.

Sparse days must record missing minute indexes and maximum inter-trade gap. The later E007 engine must continue to treat any 5-second VWAP window without trades as invalid; no price/trade forward-fill is permitted.

## 7. Why this is not rescue tuning

The correction was made before any E007R1 trigger, response, gross return, fee, execution PnL, holdout result or Confirmation result was calculated.

It changes only the interpretation of trade-tape completeness and replaces an activity proxy with direct continuity evidence.

## 8. Current hard gate

Re-run semantic preflight and full semantic qualification under v0.2.

Required exact terminal:

`E007R1_TRADE_SEMANTIC_INTEGRITY_PASS`

Expected summary:

- source files qualified = `128 / 128`;
- reconstructed UTC days qualified = `120 / 120`;
- sparse-but-ID-continuous day count reported;
- asset holdout accessed = false;
- August Confirmation accessed = false;
- strategy signal/PnL calculated = false.

## 9. Stop rules

Do not:

- calculate E007R1 gross-feasibility before semantic PASS;
- access asset-holdout bodies;
- access August Confirmation;
- access L2;
- fabricate trades/prices for sparse windows;
- relax trade-ID continuity or causal-ordering rules;
- use unresolved historical execution specs for executable PnL;
- reopen prior terminal experiments.

## 10. After semantic PASS

Only after exact PASS may the predeclared cheap E007R1 gross-feasibility screen run on the 8 Discovery assets.

That stage remains signal/gross analysis only and may not claim executable PnL before historical spec/fee and real execution validation gates are completed.
