# SC001 Current Roadmap and Stop Rules v5.198

Date: 2026-09-29
Status: **B15-P2 RECOVERY BUDGET 5/5 EXHAUSTED / JOINT REVIEW REQUIRED**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.197.md`

## Final recovery iteration result

Recovery iteration 5 reached:

- host contract preflight: PASS;
- frozen partition: BLT 76 / ART 18;
- price/index/basis/returns/PnL firewalls: CLOSED;
- network start: NO;
- failure phase: offline self-test.

Failure:

`SCHEMA_B_SCRIPT_STYLE_EXCLUSION`

Error:

`NEXT_DATA_JSON: JSONDecodeError: Unterminated string`

Canonical diagnostic:

`docs/research/sc001-b15p2-final-recovery-v017-invalid-script-context-fixture-diagnostic-v0.1.json`

## Root cause

The failing test was intended to prove that `script/style` text inside SCHEMA_B `content_html` cannot contaminate semantic classification.

The synthetic fixture appended literal:

`<script>...</script><style>...</style>`

inside `content_html`, JSON-serialized the object, and embedded that JSON verbatim in an outer:

`<script id="__NEXT_DATA__" type="application/json"> ... </script>`

A literal `</script>` terminates the surrounding HTML script raw-text element even when it appears inside a JSON string.

Therefore the outer hydration JSON was truncated before `json.loads`.

This test never reached the inner `content_html` sanitizer.

## What this does NOT invalidate

The failure does not invalidate:

- frozen 94-event source;
- BLT SCHEMA_A;
- the all-18 ART schema census;
- ART SCHEMA_B body path `articleDetail.content_html`;
- the semantic classifier;
- the URL-generation routing rule.

The existing empirical source evidence remains:

- 76 BLT events already semantically resolved;
- 18 ART pages structurally homogeneous;
- ART body path coverage 18 / 18.

## Strategic engineering lesson

The central process error was not merely a bad assertion.

We allowed the user-triggered network-host wrapper to become the first dynamic execution environment for newly modified offline self-tests.

Static review was extensive, but static review cannot guarantee runtime behavior of synthetic HTML/JSON fixtures.

A second error was excessive layer coupling: one self-test tried to test:
1. outer HTML script parsing;
2. hydration JSON parsing;
3. inner HTML fragment filtering.

The innermost test failed in layer 1.

A third process issue observed earlier was concurrent/shared-worktree mutation of execution-boundary documents. Future exact execution boundaries must be single-writer/frozen before host handoff.

## Recovery budget

The user-approved automatic recovery budget is exhausted:

`5 / 5 consumed`

No sixth automatic repair or VPS execution is authorized.

## Recommended architecture before any further host attempt

If the user authorizes further work after joint review:

1. create a new version only after dynamic offline validation;
2. use script-context-safe JSON serialization for synthetic `__NEXT_DATA__` fixtures;
3. test `visible_text_fragment` directly for script/style exclusion as an independent layer;
4. retain an end-to-end SCHEMA_B test using escaped synthetic hydration JSON;
5. run the full self-test through the offline Research Runner before requesting any VPS execution;
6. after offline PASS, freeze exact bytes;
7. run a small network smoke;
8. only then permit a full frozen 94-event semantic rerun.

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

`JOINT_REVIEW_REQUIRED_BEFORE_ANY_FURTHER_EXECUTION`
