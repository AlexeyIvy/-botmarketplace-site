# SC001 Current Roadmap and Stop Rules v5.194

Date: 2026-09-28
Status: **B15-P2 SEMANTIC REVIEW PARTITIONED / ALL-18 ART-GENERATION SCHEMA CENSUS READY**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.193.md`

## Terminal semantic REVIEW

The full frozen 94-event semantic audit completed.

Resolved:
- 76 / 94 events;
- exact announced-time match: 76 / 76 resolved;
- automatic close explicit: 76 / 76;
- active-order auto-cancel explicit: 76 / 76;
- trading-stop explicit: 76 / 76;
- closing-price basis: `AVERAGE_INDEX_PRICE_WINDOW` for 76 / 76;
- stated window: 30 minutes for 76 / 76;
- funding-mentioned: 0;
- revision/postponement wording: 0.

Unresolved:
- 18 / 94;
- all fail before semantic classification with `HYDRATION_PRIMARY_BODY_PATH`.

Canonical REVIEW:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-v015-review-result-v0.1.json`

Worker Result Manifest:

`docs/research/worker-results/sc001-b15p2-semantic-v015-review-manifest-v0.1.json`

Strategy Watch is now eligible to review this boundary.

## Structural partition

The source-integrity failures are perfectly partitioned by official Bybit URL generation:

- 76 resolved pages: `...-blt...`;
- 18 unresolved pages: `...--art...`.

The resolved BLT generation runs from frozen deliveries 2026-01-02 through 2026-06-26.

The unresolved ART generation runs from frozen deliveries 2026-07-10 through 2026-09-18.

This pattern supports a CMS/schema-generation change hypothesis.

It does **not** authorize generalizing the 76 resolved semantics to the 18 unresolved events.

## Recovery iteration accounting

Recovery iteration 1 / 5 is consumed.

It successfully fixed the host launcher and produced the terminal 94-event REVIEW.

Recovery iteration 2 / 5 is prepared, not yet consumed.

## All-18 ART schema census

Probe:

`scripts/research/probe-b15p2-art-generation-schema-census-v0.1.py`

SHA256:

`7ee2057a3c66e0b4a3f08b0f23a16df295abc3a4e7fcf88a71e29543b2f06de0`

Wrapper:

`scripts/research/run-b15p2-art-generation-schema-census-v0.1.sh`

SHA256:

`5c86181cc072b393b9ed274bbb4505522286896deed0916bcad0cdb4a7984b17`

Contract:

`docs/research/sc001-b15p2-art-generation-schema-census-contract-v0.1.json`

The census selects all 18 pages directly from the frozen 94-event source by URL-generation rule. It does not use the semantic error list as its selector.

It maps:
- all parseable hydration JSON scripts;
- exact-title identities;
- title ancestor structure;
- body-like structural candidates;
- candidate coverage across all 18;
- whether a candidate belongs to the title-containing JSON document.

No article body text is persisted.

## Decision rule

If one stable structurally credible body identity is present across all 18 ART-generation events:
- freeze it as ART `SCHEMA_B`;
- keep existing BLT path as `SCHEMA_A`;
- route deterministically by frozen structural generation;
- rerun semantic resolution only, without prices.

If the 18 ART pages are not structurally homogeneous:
- stop;
- do not add per-symbol fallbacks;
- select another official source route.

## Firewalls

Still closed:
- price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking;
- trading.

## Next state

`RUN_RECOVERY_ITERATION_2_ALL_18_ART_GENERATION_SCHEMA_CENSUS`
