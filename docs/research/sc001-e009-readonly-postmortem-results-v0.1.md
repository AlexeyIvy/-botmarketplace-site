# SC001-E009 — Read-Only Postmortem Results v0.1

Date: 2026-09-17  
Status: **POSTMORTEM COMPLETE / E009 TERMINAL DECISION UNCHANGED**

## 1. Parent terminal state

E009 v0.1 remains exact:

`E009_GROSS_FEASIBILITY_FAIL`

Read-only postmortem completed with exact:

`E009_READONLY_POSTMORTEM_PASS`

No strategy rerun was performed and no new market body was accessed.

## 2. Observed postmortem summary

Frozen per-instrument ranking by primary mean:

1. OP
2. DOGE
3. XRP
4. UNI
5. BCH
6. BTC
7. ETH
8. ORDI

Key diagnostics:

- best instrument: OP ~= `+4.379879 bps`;
- worst instrument: ORDI ~= `-6.633588 bps`;
- cross-instrument mean standard deviation ~= `4.069260 bps`;
- maximum event-weight share ~= `0.173913`;
- maximum absolute gross-contribution share ~= `0.271617`.

Postmortem classifications:

- adequate sample = true;
- cross-market average headroom insufficient = true;
- cross-market breadth insufficient = true;
- pooled robust headroom insufficient = true;
- latency robustness insufficient = true;
- concentration failure = false.

## 3. Interpretation

The E009 failure is informative rather than a sample-starvation result. The strategy produced a large enough completed-event sample, activity was distributed across the eight Discovery markets, and no single instrument dominated enough to explain the failure.

The frozen volatility normalization did not deliver adequate cross-market gross headroom, robust pooled headroom or latency robustness on fresh September evidence.

Do not infer that volatility normalization itself universally worsens reversal performance by comparing E009 September results numerically with E007R1 July results: chronology differs, so that comparison is not a controlled same-sample A/B test. The defensible conclusion is narrower: **the prospectively frozen E009 v0.1 formulation failed its own fresh Discovery gates.**

## 4. Firewalls confirmed

- strategy rerun performed = false;
- E009 terminal decision changed = false;
- asset holdout accessed = false;
- October Confirmation accessed = false;
- August repurposed = false;
- L2 accessed = false;
- discrete/net PnL calculated = false.

## 5. Research lesson

E007R1 and E009 together show that repeated refinement inside one short-horizon reversal family can consume significant research effort without establishing broad portable economics. This does not invalidate disciplined follow-up hypotheses, but it motivates an explicit **strategy-portfolio selection framework** that diversifies not only assets and dates, but also signal horizon, holding horizon, mechanism and execution archetype before allocating further heavy compute.
