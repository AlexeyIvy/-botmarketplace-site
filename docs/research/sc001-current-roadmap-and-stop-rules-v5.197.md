# SC001 Current Roadmap and Stop Rules v5.197

Date: 2026-09-29
Status: **B15-P2 FINAL RECOVERY ITERATION 5 PREPARED**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.196.md`

## Iteration 4 result

The committed v0.1.7 / wrapper v0.2 boundary was executed.

The wrapper published an exact prelaunch diagnostic before any network activity:

`docs/research/runtime-inbox/sc001-b15p2-dual-schema-semantic-v0.1.7-prelaunch-diagnostic.json`

Observed:

`PRECHECK_FAILED:IMPL_ROUTE_PATH`

The implementation freeze v0.1.7 uses canonical reference keys:

- `canonical_routing`
- `canonical_art_census`

Wrapper v0.2 retained stale pre-normalization keys:

- `dual_schema_routing`
- `schema_b_census`

All referenced paths and SHA256 values were otherwise consistent.

No network smoke or 94-event semantic execution started.

Canonical diagnostic:

`docs/research/sc001-b15p2-v017-preflight-canonical-ref-mismatch-diagnostic-v0.1.json`

## Recovery iteration accounting

- iteration 1 / 5: consumed — post-smoke launcher repair;
- iteration 2 / 5: consumed successfully — all-18 ART schema census;
- iteration 3 / 5: consumed — overly specific offline self-test expectation;
- iteration 4 / 5: consumed — implementation-freeze reference-key mismatch in preflight;
- iteration 5 / 5: prepared, not yet consumed.

If iteration 5 fails, automatic repair stops. The next action must be a joint review with the user.

## Final wrapper v0.3

Implementation remains unchanged:

`research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_7.py`

SHA256:

`f83e34263fe8716c235a76be1c94ee2049c38a4c3fdc8a064f1d99ed327ef4cc`

Final recovery wrapper:

`scripts/research/run-b15p2-dual-schema-semantic-audit-v0.3.sh`

SHA256:

`135b4965cf1ca28d112cae2cc4e486236354f0e89da07a98952a78fe1edfc336`

Contract:

`docs/research/sc001-b15p2-dual-schema-semantic-audit-contract-v0.3.json`

## Preflight correction

Wrapper v0.3 reads:

- `canonical_routing`
- `canonical_art_census`

from the implementation freeze.

It does not duplicate the canonical path/SHA values in Python literals.

Instead, the wrapper passes its own exact:
- routing path;
- routing SHA;
- census path;
- census SHA

into the Python preflight, which requires the implementation freeze to match those values.

This removes the class of stale-reference mismatch observed in iteration 4.

## Full programmer-expert review before iteration 5

The final boundary was reviewed for:

- exact implementation/freeze/routing/census/source/event-freeze SHA bindings;
- canonical freeze reference keys;
- absence of stale reference-key names;
- corrected offline self-test;
- seven-file root-owned read-only staging;
- preflight failure relay;
- self-test failure relay;
- 4-page dual-schema smoke;
- 76/18 schema partition validation;
- full 94-event terminal validation;
- smoke/result/log runtime-inbox relay;
- absence of systemd;
- absence of generated helper;
- absence of market endpoints;
- closed price/outcome firewalls.

No additional static defect was found.

## Research scope

Unchanged:
- frozen 94-event set;
- SCHEMA_A BLT_RICHTEXT = 76;
- SCHEMA_B DOUBLE_DASH_ART_HTML = 18;
- official Bybit announcement host only;
- semantic audit only.

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

`RUN_FINAL_RECOVERY_ITERATION_5_DUAL_SCHEMA_FULL_94_SEMANTIC_AUDIT_V017`
