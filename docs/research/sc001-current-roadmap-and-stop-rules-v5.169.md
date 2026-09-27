# SC001 Current Roadmap and Stop Rules v5.169

Date: 2026-09-27
Status: **B15-P2 SEMANTIC-AUDIT V0.1.1 OFFLINE SELFTEST SEALED / AWAITING EXPLICIT APPROVAL**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.168.md`

## Prior v0.1 self-test

The first sealed semantic-audit self-test returned:

`B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V01_SELF_TEST_REVIEW`

with:

`RuntimeError: visible body unexpectedly short`

Package integrity was PASS and no network access occurred.

## V0.1.1 correction

The whole-page visible-text length minimum was removed because whole-page text length is not a semantic integrity criterion.

The v0.1.1 implementation:

- rejects empty visible text;
- retains exact-title article-region extraction;
- retains a 120-character article-region minimum;
- retains head/script/style/noscript/svg exclusion;
- retains exact semantic classification rules;
- adds stage-specific self-test diagnostics.

No research/economic boundary changed.

## Exact sealed v0.1.1 self-test

Bundle:

`bundle_20260927T195617Z_135de720`

Bundle SHA256:

`7a4f3ee5720f7c9d15ce1fd7130982b929894e2ffe4c2ae807fa96146fc3566f`

Approval code:

`BM-7A4F3EE5720F`

Expected PASS:

`B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V011_SELF_TEST_PASS`

The bundle:
- has no external inputs;
- has no network;
- opens no real announcement body;
- opens no price/basis/return/PnL.

## Strategy Manager

No strategy review is triggered by the synthetic failure or its correction.

## Next state

`AWAIT_EXPLICIT_APPROVAL_TO_RUN_B15P2_SEMANTIC_AUDIT_V011_OFFLINE_SELFTEST_BM-7A4F3EE5720F`
