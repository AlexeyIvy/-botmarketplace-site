# SC001-E003 Discovery Results v0.1

Date: 2026-09-15  
Status: **TERMINAL DISCOVERY FAIL**

Parent protocol: `docs/research/sc001-e003-flow-impulse-continuation-protocol-v0.2.md`

## 1. Terminal verdict

The frozen SC001-E003 DEV-DISCOVERY run completed with:

`E003_DISCOVERY_FAIL`

Per the frozen stop rule, DEV-CONFIRMATION remains unopened. L2, 2024-Q2 raw market data, formal Validation and Final remain closed.

## 2. Frozen primary result

Primary scenario: `q99.5 / 250 ms / 60 s`.

Observed diagnostics:

- completed trades: `1640`;
- completion rate: `1.0`;
- pooled mean gross edge: about `-0.11795 bps`;
- pooled median gross edge: about `-0.11690 bps`;
- median daily mean gross edge: about `-0.04735 bps`;
- positive daily mean days: `9 / 20`.

The coarse economics hurdle was predeclared at pooled mean gross edge `>= 12 bps`; the observed primary mean was slightly negative and therefore failed by a very large margin.

## 3. Frozen 500 ms stress

Observed diagnostics for `q99.5 / 500 ms / 60 s`:

- completed trades: `1640`;
- completion rate: `1.0`;
- pooled mean gross edge: about `-0.09440 bps`;
- median daily mean gross edge: about `-0.02994 bps`;
- positive daily mean days: `10 / 20`.

The predeclared stress gate required pooled mean gross edge `>= 10 bps`; it failed.

## 4. Gate ledger

Passed:

- all required days had trades;
- completed-trade-count gate;
- completion rate >= 99%.

Failed:

- pooled mean gross edge >= 12 bps;
- median daily mean gross edge >= 8 bps;
- pooled median gross edge > 0;
- positive daily mean days >= 14/20;
- 500 ms stress mean >= 10 bps.

## 5. Interpretation

This is not an execution-cost failure like E002. E003 failed before L2 and before fees because the frozen rare-flow-impulse continuation hypothesis did not produce a positive gross continuation edge on the 60-second horizon in DEV-DISCOVERY.

The result therefore falsifies this specific frozen standalone continuation formulation. It does not falsify all possible short-horizon flow-based mechanisms.

Read-only inspection of already-computed diagnostic scenarios (q99/q99.75, 1000 ms, 30 s, 120 s) is allowed for scientific postmortem, but none may replace the failed primary rule or reopen confirmation.

## 6. Stop rule

Unchanged:

- do not run DEV-CONFIRMATION for E003;
- do not acquire E003 L2;
- do not open Q2 / Validation / Final;
- do not rescue via diagnostic threshold, latency, horizon, one-sided selection, event/day filters, maker assumptions, lower fees, or E002 TFI filtering;
- any materially different hypothesis must receive a new experiment identifier/version and be frozen before evaluation.
