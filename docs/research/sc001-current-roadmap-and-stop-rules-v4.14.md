# SC001 Current Roadmap and Stop Rules v4.14

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — E007R1 POSTMORTEM COMPLETE / E009 HYPOTHESIS FROZEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.13.md`

## 1. Binding terminal states

E001-E008 remain terminal/closed.

E007R1 remains exact terminal:

`E007R1_GROSS_FEASIBILITY_FAIL`

Read-only diagnostic completed:

`E007R1_READONLY_POSTMORTEM_PASS`

No E007R1 rescue-tuning, asset-holdout opening, August Confirmation, historical-spec execution engineering, L2 or net-PnL work is authorized.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. E007R1 postmortem findings

Recorded in:

`docs/research/sc001-e007r1-readonly-postmortem-results-v0.1.md`

Key findings:

- pooled mean ~= `2.1824 bps`;
- equal-weight instrument mean ~= `5.5936 bps`;
- median instrument mean ~= `3.5978 bps`;
- best instrument BTC ~= `31.4808 bps`;
- worst instrument ETH ~= `-11.5128 bps`;
- cross-instrument mean std ~= `15.7888 bps`;
- 4/8 instruments positive;
- sample/activity failure = false;
- concentration failure = false;
- primary failure = cross-market breadth/headroom/latency robustness.

Binding lesson: attractive pooled event statistics can coexist with poor cross-market transferability.

## 3. New active candidate family — E009

Planning document:

`docs/research/sc001-e009-volatility-normalized-displacement-reversal-research-plan-v0.1.md`

E009 is a new experiment family, not E007R2 and not a reopening of E007/E007R1.

Hypothesis: a 60-second displacement normalized by each instrument's own causal robust recent volatility may define economically comparable extreme events across heterogeneous perpetual markets better than a fixed absolute 80-bps trigger.

Frozen core design before E009 market-body access:

- 5s VWAP grid;
- 60s displacement;
- prior 30-minute robust MAD-based 5s volatility scale;
- `sigma60 = 1.4826 * MAD5 * sqrt(12)`;
- normalized displacement `Z = r60 / sigma60`;
- strict crossing at `|Z| >= 3.0`;
- reversal direction;
- 50% arithmetic retracement;
- 500 ms primary proxy latency;
- 1000/2000 ms stress;
- 10-minute max hold;
- 4 decisions/day/instrument;
- 10-minute cooldown;
- no per-asset retuning.

## 4. E009 clean evidence roles

Discovery assets:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH.

Asset holdout remains:

SOL, FIL, LTC, SUI.

Fresh E009 chronology:

- Discovery performance: `2024-09-01..2024-09-14` UTC;
- asset holdout: same September block, CLOSED until Discovery PASS;
- chronological Confirmation: `2024-10-01..2024-10-14` UTC, CLOSED;
- August remains untouched and unrepurposed.

July E007R1 data are engineering-contaminated for E009 and must not be used as promotional evidence.

## 5. Why E009 is next

This is a low-cost, one-mechanism test of the specific portability failure identified by E007R1, using already validated trade-data infrastructure and untouched later data.

It is not permission for iterative reversal tuning. Only the single frozen v0.1 normalization is authorized.

E006R1 multi-asset basis convergence remains the next orthogonal program if E009 terminally fails. E006R1 requires spot accounting/multi-leg execution and a substantially higher four-taker-fill cost hurdle, so it remains queued rather than abandoned.

## 6. Current hard gate

Before any E009 trade body download or gross output:

1. create/freeze exact E009 gross-feasibility executable protocol and PASS/FAIL gates;
2. run metadata-only historical archive preflight for the eight Discovery assets and required September boundary labels;
3. review exact file count/bytes;
4. only then acquire bodies in staged batches;
5. semantic qualification using the v0.2 trade-continuity lesson;
6. no asset holdout or October access;
7. no exact executable/net PnL claim.

## 7. Stop rules

Do not:

- alter E007R1;
- use only BTC/DOGE/UNI/XRP because they looked better in E007R1;
- reuse July E007R1 performance as fresh E009 evidence;
- open SOL/FIL/LTC/SUI before E009 Discovery PASS;
- open October Confirmation before the appropriate prior gates;
- change E009 z-threshold/lookback/normalization/target/hold/latency after output;
- add TFI or any auxiliary feature to E009 v0.1;
- proceed to historical discrete execution/L2 if gross-feasibility fails.

## 8. Immediate next action

Freeze E009 gross-feasibility executable gates, then run a metadata-only September archive preflight. No market body should be downloaded before that preflight is reviewed.
