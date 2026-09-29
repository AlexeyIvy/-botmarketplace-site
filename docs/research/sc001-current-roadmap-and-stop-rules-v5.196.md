# SC001 Current Roadmap and Stop Rules v5.196

Date: 2026-09-29
Status: **B15-P2 DUAL-SCHEMA SELFTEST CORRECTED / RECOVERY ITERATION 4 READY**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.195.md`

## What happened in iteration 3

The user executed the committed v0.1.6 synchronous dual-schema boundary.

No v0.1.6 smoke, terminal result, or log was published.

A full reconstruction of the committed wrapper preflight passed against:
- exact implementation/freeze SHAs;
- canonical dual-schema routing;
- canonical ART census;
- frozen 94-event source and event-set freeze.

The deterministic first failure is in the offline self-test stage:

`NO_CROSS_SCHEMA_FALLBACK`

The SCHEMA_A synthetic fixture intentionally contains:

`content_html=""`

When deliberately routed as SCHEMA_B, the extractor correctly rejects it as:

`SCHEMA_B_RAW_HTML_TOO_SHORT`

The self-test incorrectly required:

`SCHEMA_B_CONTENT_HTML_PATH`

Therefore the extractor behaved correctly and the test expectation was too narrow.

Canonical diagnostic:

`docs/research/sc001-b15p2-dual-schema-v016-selftest-failure-diagnostic-v0.1.json`

No network smoke or 94-event run was reached.

## Iteration accounting

- iteration 1 / 5: consumed — post-smoke launcher fix;
- iteration 2 / 5: consumed successfully — all-18 ART schema census;
- iteration 3 / 5: consumed — offline self-test expectation failure;
- iteration 4 / 5: prepared, not yet consumed.

## v0.1.7 implementation

Implementation:

`research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_7.py`

SHA256:

`f83e34263fe8716c235a76be1c94ee2049c38a4c3fdc8a064f1d99ed327ef4cc`

Static review confirms that compared with v0.1.6:
- semantic classifier is unchanged;
- announced-time parser is unchanged;
- frozen input validation is unchanged;
- curl transport is unchanged;
- dual-schema extractor/router is unchanged.

Only the incorrect self-test expectation and versioned output paths changed.

Additional self-test assertions now explicitly verify schema-specific null/non-null metadata.

## Recovery wrapper v0.2

Wrapper:

`scripts/research/run-b15p2-dual-schema-semantic-audit-v0.2.sh`

SHA256:

`bce2bb8733a3042df52c1b3a7a062610a4201dad9a8eec07c5371d4df70bcae9`

Contract:

`docs/research/sc001-b15p2-dual-schema-semantic-audit-contract-v0.2.json`

The wrapper remains synchronous, with no systemd and no generated helper.

It now also publishes a compact prelaunch diagnostic if:
- contract preflight fails;
- offline self-test exits non-zero;
- self-test PASS token is missing.

Diagnostic target:

`docs/research/runtime-inbox/sc001-b15p2-dual-schema-semantic-v0.1.7-prelaunch-diagnostic.json`

Therefore another early stop can be diagnosed through MCP without screenshots.

## Research scope

Unchanged:
- frozen event set: 94;
- SCHEMA_A BLT_RICHTEXT: 76;
- SCHEMA_B DOUBLE_DASH_ART_HTML: 18;
- official Bybit announcement host only.

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

`RUN_RECOVERY_ITERATION_4_DUAL_SCHEMA_FULL_94_SEMANTIC_AUDIT_V017`
