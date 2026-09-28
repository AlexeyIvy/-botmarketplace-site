# SC001 Current Roadmap and Stop Rules v5.195

Date: 2026-09-28
Status: **B15-P2 DUAL HYDRATION SCHEMA FROZEN / RECOVERY ITERATION 3 READY**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.194.md`

## ART-generation census result

The all-18 census completed successfully.

Runtime result SHA256:

`581ecec49653fc9230c18c05e1baa1371e268cba8899a170d1494861f8c4e943`

All 18 frozen `--art...` pages have:
- one exact title identity:
  `__NEXT_DATA__::$.props.pageProps.articleDetail.title`;
- one parseable `__NEXT_DATA__` document;
- one common concrete body string:
  `$.props.pageProps.articleDetail.content_html`;
- body-string structural length range: 1671–1719 characters;
- body-path coverage: 18 / 18;
- title-document coupling: 18 / 18.

Therefore the later ART generation is structurally homogeneous.

Canonical result:

`docs/research/sc001-b15p2-art-generation-schema-census-result-v0.1.json`

## Frozen dual schema routing

### SCHEMA_A — BLT_RICHTEXT
Frozen event count: 76.

URL generation:
`-blt...`

Body:
`$.props.pageProps.articleDetail.content.json.children`

Extraction:
deterministic descendant text leaves.

### SCHEMA_B — DOUBLE_DASH_ART_HTML
Frozen event count: 18.

URL generation:
`--art...`

Body:
`$.props.pageProps.articleDetail.content_html`

Extraction:
parse only that HTML fragment, require at least 2 HTML tags, exclude script/style/head/noscript/svg, and normalize visible text.

Common title:
`$.props.pageProps.articleDetail.title`

Routing is determined only from the frozen requested announcement URL.

No semantic-result, price, or outcome-driven routing is allowed.

Freeze:

`docs/research/sc001-b15p2-hydration-dual-schema-routing-freeze-v0.1.json`

## Recovery iteration accounting

- iteration 1 / 5: consumed — fixed post-smoke launcher;
- iteration 2 / 5: consumed successfully — identified and validated ART SCHEMA_B across all 18 pages;
- iteration 3 / 5: prepared, not yet consumed — unified dual-schema 94-event semantic rerun.

## v0.1.6 implementation

Implementation:

`research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_6.py`

SHA256:

\`1bc02d6e13ad919dbfa405f92b12f80d8c36271b294ed6845968c9dcac96315c\`

Static review confirmed unchanged from v0.1.5:
- semantic classifier;
- announced-time parser;
- frozen input validation;
- curl transport;
- PASS/REVIEW semantics.

Only the body extractor/router changed.

## Simplified host execution

Wrapper:

`scripts/research/run-b15p2-dual-schema-semantic-audit-v0.1.sh`

SHA256:

\`24e8cb382e026852178d26da9c9006c784dd437291e6836b426f0104ed321cbd\`

Contract:

`docs/research/sc001-b15p2-dual-schema-semantic-audit-contract-v0.1.json`

No systemd and no generated helper are used.

One synchronous command performs:
1. preflight;
2. exact read-only stage;
3. offline self-test;
4. 4-page dual-schema smoke;
5. full 94-event semantic audit;
6. terminal validation;
7. automatic runtime-inbox publication.

Large event-by-event output is written to a persistent log rather than printed to the terminal.

## Strategy state

The earlier 76/94 terminal REVIEW remains a valid strategy-relevant evidence boundary and already has a Worker Result Manifest.

It must not be interpreted as an economic rejection.

The dual-schema rerun is intended only to resolve the 18-event source-integrity gap.

## Firewalls

Still closed:
- affected-contract price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- event outcome ranking;
- trading.

## Next state

`RUN_RECOVERY_ITERATION_3_DUAL_SCHEMA_FULL_94_SEMANTIC_AUDIT`
