# SC001-E009 — Terminal Gross Feasibility Results v0.1

Date: 2026-09-17  
Status: **TERMINAL E009 v0.1 GROSS FAIL**

## 1. Exact terminal state

Observed frozen one-shot result:

`E009_GROSS_FEASIBILITY_FAIL`

Exit code: `2`.

E009 v0.1 is terminal. No rescue-tuning is authorized.

## 2. Frozen-output summary

- active assets = `8 / 8`;
- pooled completed events = `322`;
- equal-weight instrument mean gross edge ~= `-0.8931 bps`;
- median instrument mean gross edge ~= `-0.7971 bps`;
- positive instruments = `4 / 8`;
- pooled 10% trimmed mean ~= `4.8823 bps`;
- pooled median ~= `8.1922 bps`;
- 1000 ms equal-weight mean ~= `-0.6272 bps`;
- 2000 ms equal-weight mean ~= `-0.3090 bps`;
- top instrument absolute gross-contribution share ~= `0.27162`;
- discrete contract PnL calculated = false;
- asset holdout accessed = false;
- October Confirmation accessed = false;
- August repurposed = false.

## 3. Failed frozen gates

The terminal run failed:

- `equal_weight_mean_gte20`;
- `median_instrument_mean_gte15`;
- `positive_instruments_gte5`;
- `pooled_trimmed_mean_gte15`;
- `pooled_median_gte10`;
- `lat1000_equal_weight_gte15`;
- `lat2000_equal_weight_gte10`.

Sample/activity and top-instrument concentration were not the primary failure modes.

## 4. Binding interpretation

The volatility-normalized E009 mechanism generated enough events to test the hypothesis, but the fresh September evidence did not show economically adequate or cross-market portable gross headroom.

Compared with the motivation for E009, normalization by trailing robust short-horizon volatility did **not** solve the portability problem observed in E007R1. Cross-market equal-weight economics were approximately flat-to-negative, the median instrument was negative, and only half of the Discovery instruments had positive means.

The pooled event-level distribution retained some positive central tendency, but it was below the frozen hurdles and did not translate into robust instrument-level breadth.

This is a strategy-family conclusion, not an executable/net-PnL conclusion. The gross screen failed before historical exact contract specs, L2 execution, fees or net PnL were promoted.

## 5. Firewalls after FAIL

Do not:

- change `Z=3.0`, the 30-minute MAD window, target, hold, cooldown, latency or cap and rerun as E009;
- select only profitable E009 symbols;
- open SOL/FIL/LTC/SUI holdout to search for better results;
- open October Confirmation;
- repurpose August;
- spend E009 resources on historical execution-spec/L2/net-PnL engineering;
- call a tuned continuation `E009R2` without a genuinely new experiment family and untouched evidence.

## 6. Allowed diagnostic work

One read-only postmortem is allowed using only the existing terminal report. It may summarize per-instrument heterogeneity, direction asymmetry, event/day breadth, normalized-trigger diagnostics and concentration. It must not rerun the strategy or read any new market body.

After the postmortem, return to the next-generation framework. The queued orthogonal program is E006R1 multi-asset same-venue spot/perpetual basis convergence, subject to a new predeclared multi-leg/economics protocol.
