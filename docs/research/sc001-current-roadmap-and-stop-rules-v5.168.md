# SC001 Current Roadmap and Stop Rules v5.168

Date: 2026-09-27
Status: **B15-P2 SEMANTIC SELFTEST V0.1 SYNTHETIC FAILURE / V0.1.1 CORRECTION FROZEN**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.167.md`

## V0.1 offline self-test result

Exact sealed bundle:

`bundle_20260927T195054Z_1de54b89`

Job:

`job_20260927T195253Z_77823c65`

Package integrity:

`PASS`

Exit code:

`2`

Observed token:

`B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V01_SELF_TEST_REVIEW`

Observed error:

`RuntimeError: visible body unexpectedly short`

No network access occurred.

No real announcement body, price, basis, return or PnL was accessed.

## Root-cause treatment

The whole-page visible-text minimum was an unnecessarily brittle integrity criterion.

Semantic evidence is not the total amount of visible page text.

The correct fail-closed unit is the exact announcement article region beginning at the exact contract-specific title.

V0.1.1 therefore:

- rejects an empty visible page;
- retains exact-title article-region extraction;
- retains a 120-character minimum on the article region;
- retains page-chrome exclusion;
- adds stage-specific self-test diagnostics;
- changes no semantic classification rule;
- changes no PASS/REVIEW research criterion.

## Frozen v0.1.1 implementation

`research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_1.py`

SHA256:

`a7ba9da9b5eb0786476b9360f39cc182277fc8e7cf26657747ac0d64d5550a5c`

Implementation freeze:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-implementation-freeze-v0.1.1.json`

Offline self-test spec:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-offline-selftest-spec-v0.1.1.json`

## Firewalls

Still closed:

- network during offline self-test;
- real announcement pages;
- price;
- external-reference price;
- index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking.

## Strategy Manager

No strategy trigger occurred.

This was a synthetic engineering failure before any semantic evidence was opened.

## Next state

`PREPARE_AND_SEAL_B15P2_SEMANTIC_AUDIT_V011_OFFLINE_SELFTEST_NO_EXECUTION`
