# SC001 — B13-C S0 Source-Ingestion Amendment v0.1

Date: 2026-09-26  
Status: **FROZEN BEFORE B13-C PRICE OUTCOME / RESEARCH RULES UNCHANGED**

Parent:

`docs/research/sc001-b13c-s0-simple-post-liquidation-reversal-sentinel-protocol-v0.1.md`

## Purpose

Clarify the phrase "all required daily public trade archives" without changing any S0 signal, horizon, threshold, universe or result gate.

## Binding definition of required price archive

A daily Bybit price archive is required iff, after applying the already frozen **source-only** event rules:

- the symbol has at least one eligible S0 cluster; and
- the archive UTC date intersects either frozen price bucket:
  - `[cluster_end+1s, cluster_end+2s)`; or
  - `[cluster_end+31s, cluster_end+32s)`.

If a one-second bucket crosses midnight, both touched UTC dates are required.

A symbol-date with no eligible frozen cluster is not downloaded merely for completeness.

## Why this is not outcome selection

The exact required-file set is derived only from:
- explicit liquidation timestamps;
- frozen symbol identity;
- frozen 5-second clustering;
- frozen minimum 3 events;
- frozen pure-side condition;
- frozen source-gap censoring;
- frozen price anchor timestamps.

No price, return, spread, execution or PnL is consulted.

## Hard rules unchanged

Unchanged:
- all 12 symbols remain eligible;
- no size threshold;
- no size weighting;
- 5-second cluster gap;
- >=3 distinct fingerprints;
- pure-side clusters;
- gap censoring;
- entry E+1s;
- exit E+31s;
- 30-second reversal hypothesis;
- >=100 valid clusters;
- median >=30 bps;
- positive share >=55%;
- >=4/6 positive complete-day medians;
- no per-symbol winner selection;
- no rescue tuning.

## Consequence

Run an immutable source-only cluster census before downloading any B13-C price body.

The census may report aggregate cluster/sample sufficiency and the exact required symbol-date archive identities.

It must not report predictive returns or per-symbol performance.
