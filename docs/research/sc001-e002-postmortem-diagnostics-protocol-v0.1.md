# SC001-E002 Postmortem Diagnostics Protocol v0.1

Date: 2026-09-15  
Status: **READ-ONLY POSTMORTEM — NO RESCUE TUNING**

Parent terminal result: `TAKER_ECONOMICS_FAIL`.

Purpose: extract additional lessons from the already-completed E002 taker-economics outputs without rerunning the market-data engine, changing any financial/statistical rule, or reopening E002.

## Hard boundary

This diagnostic stage must not:

- alter the terminal `TAKER_ECONOMICS_FAIL` verdict;
- promote q90/q97.5, 1k/50k, 500 ms, or any haircut scenario into a new primary rule;
- introduce maker assumptions, side filters, event filters, new horizons, new thresholds, or Q2 exploration;
- access formal Validation or Final;
- reinterpret partial checkpoints as new evidence.

E002 remains closed as a standalone taker strategy.

## Questions to answer from existing final outputs only

1. How do q90 / q95 / q97.5 compare at the frozen 10k, 100 ms, 0% haircut setting?
2. How do 1k / 10k / 50k compare at q95, 100 ms, 0% haircut?
3. How do 100 / 250 / 500 ms compare at q95, 10k, 0% haircut?
4. How do 0 / 25 / 50% depth haircuts compare at q95, 10k, 100 ms?
5. Are fills/capacity or fee burden the dominant bottleneck?
6. What are the long/short counts and whether one side dominates the completed sample?
7. What are execution-wait percentiles and whether stale/late execution looks material?
8. What is the break-even round-trip fee across the main diagnostics?
9. Among completed trades already stored by the frozen engine, how often is `abs(TFI)` exactly equal (within floating tolerance) to the causal threshold? This is a tie diagnostic only and must not be used to redefine the threshold.

## Interpretation rule

Any diagnostic pattern can be carried forward only as research knowledge or as a candidate feature/design constraint for a separately frozen future experiment (e.g. E003 or an ensemble/meta-model). It cannot retroactively rescue E002.

Q2 / Validation / Final remain closed throughout this postmortem.
