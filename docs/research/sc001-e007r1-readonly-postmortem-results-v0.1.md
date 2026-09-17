# SC001-E007R1 — Read-Only Postmortem Results v0.1

Date: 2026-09-17  
Status: **TERMINAL DIAGNOSTIC — E007R1 VERDICT UNCHANGED**

## Result

Exact diagnostic token:

`E007R1_READONLY_POSTMORTEM_PASS`

Parent remains terminal:

`E007R1_GROSS_FEASIBILITY_FAIL`

No strategy rerun, no asset-holdout access, no August Confirmation access and no discrete/net PnL calculation occurred.

## Key numbers

- pooled mean gross edge: `2.1824 bps`;
- equal-weight instrument mean: `5.5936 bps`;
- median instrument mean: `3.5978 bps`;
- pooled completed events: `161`;
- positive instruments: `4 / 8`;
- best instrument: `BTC`, mean about `31.4808 bps`;
- worst instrument: `ETH`, mean about `-11.5128 bps`;
- mean ranking: `BTC, DOGE, UNI, XRP, ORDI, BCH, OP, ETH`;
- cross-instrument mean standard deviation: about `15.7888 bps`;
- maximum event-count weight of one instrument: about `0.2671`;
- maximum absolute gross-contribution share: about `0.1818`.

## Binding interpretation

The E007 absolute 80-bps displacement-reversal mechanism has a genuine event-level effect in part of the sample, but it is not broadly portable across markets and does not provide sufficient equal-weight gross headroom or latency-robust breadth.

The primary failure is not sample scarcity and not single-market concentration. The primary failure is cross-market heterogeneity/headroom/breadth.

The divergence between a positive pooled median/trimmed statistic and weak equal-weight market statistics is a general methodological lesson: pooled event statistics can look attractive while the underlying mechanism fails to transfer across instruments.

## Stop rule

Do not rescue E007R1 by selecting BTC or any profitable subset, changing the 80-bps threshold, adding a post-hoc volatility/regime filter, changing target/hold/latency, opening the asset holdout, or opening August Confirmation.

Any scale-normalized, market-relative, regime-conditioned or otherwise materially changed reversal idea is a new experiment family with a new ID and untouched evidence.
