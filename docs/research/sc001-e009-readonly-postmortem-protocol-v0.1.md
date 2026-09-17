# SC001-E009 — Read-Only Postmortem Protocol v0.1

Date: 2026-09-17  
Status: **FROZEN AFTER TERMINAL FAIL / NO STRATEGY RERUN**

## 1. Parent state

Required parent:

`E009_GROSS_FEASIBILITY_FAIL`

This protocol cannot change the terminal E009 decision.

## 2. Allowed input

Only:

`~/sc001_data/SC001_E009_GROSS_FEASIBILITY/sc001_e009_gross_feasibility_report.json`

No ZIP/trade/L2 body may be opened.

## 3. Allowed diagnostics

- per-instrument primary means/medians/trimmed means;
- candidate/decision/completed counts;
- long/short asymmetry already stored in the parent;
- stress-latency means already stored in the parent;
- event and absolute gross-contribution concentration;
- calendar-day breadth already stored in parent diagnostics;
- normalized-observation and trigger diagnostics already stored in parent, if present;
- ranking by frozen primary mean;
- comparison of pooled/event-level versus equal-weight instrument-level evidence.

## 4. Forbidden work

- no strategy rerun;
- no parameter alternatives;
- no threshold/lookback/target variants;
- no new market bodies;
- no holdout;
- no October;
- no August repurposing;
- no L2;
- no discrete/net PnL.

## 5. Required terminal token

`E009_READONLY_POSTMORTEM_PASS`

The report must explicitly state:

- `strategy rerun performed = False`;
- `E009 terminal decision changed = False`;
- `asset holdout accessed = False`;
- `October Confirmation accessed = False`;
- `August repurposed = False`;
- `discrete/net PnL calculated = False`.
