# SC001 Current Roadmap and Stop Rules v4.17

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — E009 SEMANTIC PASS / GROSS IMPLEMENTATION FROZEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.16.md`

## 1. Binding terminal states

E001-E008 remain terminal/closed. E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL` with read-only postmortem complete. E009 is a new family and does not reopen earlier experiments.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. E009 governance

Discovery assets: BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH.

Asset holdout remains CLOSED: SOL, FIL, LTC, SUI.

Discovery performance dates: `2024-09-01..2024-09-14` UTC.

October Confirmation remains CLOSED. August remains untouched/non-promotional and is not repurposed.

## 3. E009 data qualification complete

Acquisition remains exact PASS:

- `E009_TRADE_ACQUISITION_VERIFY_PASS`;
- verified files = `128`;
- verified total bytes = `419552195`.

Semantic qualification now exact PASS:

- `E009_TRADE_SEMANTIC_INTEGRITY_PASS`;
- source files qualified = `128 / 128`;
- reconstructed UTC days qualified = `120 / 120`;
- sparse-but-ID-continuous days = `44`;
- asset holdout accessed = false;
- October Confirmation accessed = false;
- August repurposed = false;
- strategy signal/PnL calculated = false;
- semantic exit code = `0`.

The corrected multi-asset continuity rule remains binding: minute activity is diagnostic; exact trade-ID continuity, chronology, schema/instrument validity and UTC stitch are hard gates. Sparse future 5-second strategy buckets are never forward-filled.

## 4. Frozen E009 gross protocol

Binding protocol created before September market-body access:

`docs/research/sc001-e009-gross-feasibility-executable-protocol-v0.1.md`

Frozen economic/breadth gates are unchanged from before body access. They may not be relaxed after output.

## 5. Gross implementation identity freeze

Runner:

`research/sc001/sc001_e009_gross_feasibility.py`

Identity manifest:

`docs/research/sc001-e009-gross-feasibility-implementation-freeze-v1.0.json`

Before first gross output the runner must pass exact:

`E009_GROSS_FEASIBILITY_IMPLEMENTATION_PREFLIGHT_PASS`

The implementation freezes:

- 5s VWAP grid;
- 60s log displacement using current `[t-5s,t)` and anchor `[t-65s,t-60s)`;
- robust MAD volatility normalization;
- prior 30-minute volatility sample ending at `t-60s`, thereby excluding the current 60-second displacement interval;
- 360 possible 5s return slots, >=240 valid required;
- `sigma60 = 1.4826 * MAD5 * sqrt(12)`;
- strict `|Z|=3.0` crossing;
- invalid normalized points break the crossing chain;
- no forward fill;
- reversal direction;
- 50% arithmetic retracement;
- 500ms primary and 1000/2000ms stress latency;
- 5s proxy tolerance;
- 10-minute max hold;
- 4 decisions/day/instrument;
- 10-minute cooldown;
- no new decision after 23:49 UTC;
- all 8 instruments retained in equal-weight denominators; zero-completion instrument mean = 0 bps.

## 6. Current hard gate — one frozen E009 gross-feasibility run

Only one terminal gross run is authorized after exact implementation preflight.

Possible exact terminals:

- `E009_GROSS_FEASIBILITY_PASS`;
- `E009_GROSS_FEASIBILITY_FAIL`.

PASS only permits further engineering; it is not executable profitability proof.

FAIL is terminal for E009 v0.1 and blocks asset holdout, October Confirmation, historical execution-spec/L2/net-PnL engineering. No rescue tuning is permitted.

## 7. Firewalls

Do not:

- alter z-threshold, volatility lookback/MAD semantics, target, hold, latency, cooldown or cap after output;
- select only favorable instruments;
- open SOL/FIL/LTC/SUI before E009 Discovery gross PASS;
- open October Confirmation before later gates;
- repurpose August;
- access L2 in gross feasibility;
- use unresolved historical contract specs or fees for promoted execution/PnL;
- add TFI, flow, compression, basis or any other auxiliary feature to E009 v0.1.

## 8. Immediate VPS action

1. `git pull --ff-only`;
2. py-compile `research/sc001/sc001_e009_gross_feasibility.py`;
3. run `preflight` and require exact `E009_GROSS_FEASIBILITY_IMPLEMENTATION_PREFLIGHT_PASS`;
4. only then launch one `run` in tmux;
5. review exact PASS/FAIL and frozen gates before any further E009 action.
