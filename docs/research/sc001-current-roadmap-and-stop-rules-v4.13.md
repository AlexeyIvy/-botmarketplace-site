# SC001 Current Roadmap and Stop Rules v4.13

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — E007R1 TERMINAL GROSS FAIL / READ-ONLY POSTMORTEM OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.12.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. Nothing in E007R1 reopens E007.

E007R1 now has exact terminal gross-screen state:

`E007R1_GROSS_FEASIBILITY_FAIL`

This FAIL blocks further E007R1 historical-spec reconstruction for execution, L2 engineering, executable/net-PnL testing, asset-holdout opening and August Confirmation.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. E007R1 terminal gross result

Observed frozen-output summary:

- active assets = `8 / 8`;
- pooled completed events = `161`;
- equal-weight mean instrument gross edge ~= `5.5936 bps`;
- median instrument mean gross edge ~= `3.5978 bps`;
- positive instruments = `4 / 8`;
- pooled 10% trimmed mean ~= `15.1079 bps`;
- pooled median ~= `30.8807 bps`;
- 1000 ms equal-weight mean ~= `5.3177 bps`;
- 2000 ms equal-weight mean ~= `5.0698 bps`;
- top-instrument absolute contribution share ~= `0.18183`;
- discrete contract PnL = false;
- asset holdout accessed = false;
- August Confirmation accessed = false.

Failed frozen gates:

- `equal_weight_mean_gte20`;
- `median_instrument_mean_gte15`;
- `positive_instruments_gte5`;
- `lat1000_equal_weight_gte15`;
- `lat2000_equal_weight_gte10`.

Sample/activity and concentration gates were not the principal failure.

## 3. Binding interpretation

The result contains a real event-level mean-reversion effect in part of the sample, evidenced by positive pooled median/trimmed statistics, but the effect is not sufficiently portable across markets and does not retain enough equal-weight latency-robust gross headroom.

Therefore:

- do not rescue E007R1 by selecting only profitable symbols;
- do not retune the 80 bps trigger, 50% target, hold, cooldown, latency or cap;
- do not open the asset holdout to search for better-looking symbols;
- do not open August Confirmation;
- do not spend more E007R1 resources on historical execution-spec/L2/net-PnL reconstruction.

## 4. Current allowed work — read-only postmortem only

Protocol:

`docs/research/sc001-e007r1-readonly-postmortem-protocol-v0.1.md`

Runner:

`research/sc001/sc001_e007r1_readonly_postmortem.py`

The postmortem may read only the existing terminal gross report. It must not rerun the strategy or read any new market body.

Purpose:

- explain pooled-vs-equal-weight divergence;
- identify cross-instrument heterogeneity;
- inspect event-count and contribution concentration;
- inspect long/short and calendar-day breadth already stored in the parent report;
- classify whether the main failure is breadth/headroom/latency/sample/concentration.

Exact successful diagnostic token:

`E007R1_READONLY_POSTMORTEM_PASS`

This token does not change the terminal E007R1 decision.

## 5. Data-quality lesson retained

Semantic v0.2 remains exact PASS:

- source files = `128 / 128`;
- reconstructed UTC days = `120 / 120`;
- sparse-but-ID-continuous days = `27`.

The earlier 1440/1440-minute rule defect is retained as a methodological lesson: absence of a trade in a minute is not by itself proof of missing data when trade-ID continuity and chronology remain intact.

## 6. Next program after postmortem

After the read-only postmortem, do not create E007R2 automatically.

Return to the next-generation research framework and choose the next candidate/mechanism using accumulated evidence from E001-E008 and E007R1. Any materially changed reversal idea, regime filter, cross-asset subset, threshold or execution design is a new experiment family/ID and requires untouched evidence.

Asset holdout and August Confirmation remain protected for future eligible new experiments unless/until separately re-governed.

## 7. Immediate VPS action

1. `git pull --ff-only`;
2. syntax-check `research/sc001/sc001_e007r1_readonly_postmortem.py`;
3. run it once;
4. review the exact read-only PASS and per-instrument diagnostics;
5. do not run any E007R1 strategy/execution stage afterward.
