# SC001 Current Roadmap and Stop Rules v4.6

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — ACCOUNTING 20/20 PASS / SYNTHETIC TAKER KERNEL VALIDATION OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.5.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact `E008_DISCOVERY_FAIL`.

No prior verdict is reopened. SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. Governance state

Frozen first-generation universe:

BTC, ETH, SOL, DOGE, ORDI, FIL, UNI, XRP, LTC, OP, BCH, SUI — OKX linear USDT SWAPs.

Frozen evidence roles:

- Discovery assets: BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH;
- asset holdout: SOL, FIL, LTC, SUI;
- Discovery time: 2024-07-01..14;
- chronological Confirmation: all 12 on 2024-08-01..14;
- 2024-07-16..30 intentionally unopened/unassigned.

No July/August strategy body has yet been opened.

## 3. Common accounting gate complete

Observed exact:

`SC001_COMMON_ACCOUNTING_CORE_VALIDATION_PASS`

Observed:

- tests passed = `20 / 20`;
- real market-data body accessed = false;
- strategy signal calculated = false;
- promotional PnL calculated = false;
- July/August reserved bodies accessed = false.

The validated accounting layer is now the canonical independent fill->cash/position/PnL calculator for future linear-USDT synthetic/real executions, subject to historical spec resolution.

## 4. Historical execution-spec evidence remains fail-closed

Binding standard:

`docs/research/sc001-historical-execution-spec-evidence-standard-v0.1.md`

Current instrument metadata is not historical proof of 2024 `tickSz/lotSz/minSz/ctVal` or fees.

Real promotional discrete execution/PnL remains blocked until required historical fields are resolved and frozen by date interval.

Synthetic engine validation may continue using fixture specs only.

## 5. Current hard gate — normalized schema + taker kernel synthetic validation

Protocol:

`docs/research/sc001-normalized-market-schema-and-taker-kernel-validation-protocol-v0.1.md`

Core files:

- `research/sc001/sc001_normalized_market_schema.py`;
- `research/sc001/sc001_taker_execution_kernel.py`;
- `research/sc001/sc001_taker_execution_validation.py`.

Purpose:

- separate source/observed/decision/send/activation times;
- prevent strategy future visibility;
- execute BUY against asks and SELL against bids;
- sweep visible depth level-by-level;
- expose partial/unresolved remainder instead of fabricating fills;
- generate immutable `Fill` ledger records consumed by the already-validated accounting layer;
- prove deterministic execution on synthetic fixtures.

Required exact PASS:

`SC001_TAKER_KERNEL_SYNTHETIC_VALIDATION_PASS`

Required:

- `tests_passed = 24 / 24`;
- no real market body;
- no strategy signal;
- no promotional PnL;
- no July/August body access;
- historical exact execution specs still false/unresolved.

## 6. After PASS

1. perform historical execution-spec/fee evidence reconstruction for the frozen 12 and chronology;
2. build/validate raw->normalized real-data converters without strategy PnL;
3. validate taker kernel on controlled/engineering real-data samples with differential/accounting checks;
4. run a cheap predeclared E007 economic-feasibility audit;
5. only if economically warranted, freeze a new-ID strict E007 multi-asset implementation;
6. open July Discovery bodies only under a one-shot identity manifest.

## 7. Stop rules

Do not:

- open July/August strategy bodies during synthetic validation;
- use current exchange specs as proven 2024 execution specs;
- use public trade prints as canonical taker fill prices once L2 execution is required;
- let strategy logic access execution-only future venue state;
- fabricate completion beyond visible depth;
- calculate strategy PnL before historical spec/fee handling and real-data execution validation are frozen;
- reopen E001-E008.

## 8. Immediate VPS action

Pull latest code, py-compile the normalized schema, taker kernel and validation runner, then execute the synthetic validation once. Review the exact 24/24 result before any real-data execution work.
