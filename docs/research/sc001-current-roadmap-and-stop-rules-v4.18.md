# SC001 Current Roadmap and Stop Rules v4.18

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — E009 TERMINAL GROSS FAIL / READ-ONLY POSTMORTEM OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.17.md`

## 1. Binding terminal states

E001-E008 remain terminal/closed. E007R1 remains terminal `E007R1_GROSS_FEASIBILITY_FAIL` with postmortem complete.

E009 v0.1 now has exact terminal state:

`E009_GROSS_FEASIBILITY_FAIL`

No rescue-tuning, holdout opening, October Confirmation, L2, historical execution-spec promotion or net-PnL engineering is authorized for E009 v0.1.

## 2. E009 terminal summary

Observed frozen run:

- active assets = `8 / 8`;
- pooled completed = `322`;
- equal-weight instrument mean ~= `-0.8931 bps`;
- median instrument mean ~= `-0.7971 bps`;
- positive instruments = `4 / 8`;
- pooled trimmed mean ~= `4.8823 bps`;
- pooled median ~= `8.1922 bps`;
- 1000 ms equal-weight mean ~= `-0.6272 bps`;
- 2000 ms equal-weight mean ~= `-0.3090 bps`;
- top instrument absolute gross-contribution share ~= `0.27162`;
- discrete contract PnL = false;
- holdout accessed = false;
- October Confirmation accessed = false;
- August repurposed = false.

Failed frozen gates:

- `equal_weight_mean_gte20`;
- `median_instrument_mean_gte15`;
- `positive_instruments_gte5`;
- `pooled_trimmed_mean_gte15`;
- `pooled_median_gte10`;
- `lat1000_equal_weight_gte15`;
- `lat2000_equal_weight_gte10`.

## 3. Binding interpretation

The volatility-normalized displacement-reversal hypothesis did not produce adequate gross headroom or cross-market breadth on fresh September Discovery evidence. Sample/activity and concentration were sufficient to make the negative conclusion informative.

Normalization did not resolve the portability problem that motivated E009.

## 4. Current allowed work

Read-only postmortem only.

Protocol:

`docs/research/sc001-e009-readonly-postmortem-protocol-v0.1.md`

Runner:

`research/sc001/sc001_e009_readonly_postmortem.py`

Required token:

`E009_READONLY_POSTMORTEM_PASS`

The postmortem reads only the existing terminal JSON and cannot change the terminal decision.

## 5. Firewalls

Do not:

- rerun E009 with changed Z/lookback/MAD/target/hold/latency/cooldown/cap;
- select only favorable symbols;
- open SOL/FIL/LTC/SUI holdout;
- open October Confirmation;
- repurpose August;
- access L2 or promoted historical execution specs for E009;
- calculate discrete/net PnL for E009;
- create E009R2 automatically.

## 6. Next program after postmortem

Return to the next-generation multi-asset framework and begin the queued orthogonal program:

**E006R1 — multi-asset same-venue spot/perpetual basis-dislocation -> convergence.**

Before any new alpha output, E006R1 requires a new frozen protocol for:

- historical spot + perp universe/pair eligibility;
- synchronized causal basis construction;
- four-leg taker economics hurdle;
- multi-leg execution/legging model;
- spot borrow/short feasibility where applicable;
- funding and contract accounting;
- gross-first stop gate before expensive L2 work;
- fresh uncontaminated chronology and holdouts.

## 7. Immediate action

Run the E009 read-only postmortem once. After exact PASS, use its diagnostics only as lessons and open E006R1 planning; do not rescue E009.
