# SC001 Current Roadmap and Stop Rules v5.170

Date: 2026-09-27
Status: **B15-P2 SEMANTIC SELFTEST V0.1.1 HTML-PARSER FAILURE / V0.1.2 CORRECTION FROZEN**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.169.md`

## V0.1.1 offline self-test

Bundle:

`bundle_20260927T195617Z_135de720`

Job:

`job_20260927T195919Z_b604441c`

Package integrity:

`PASS`

Observed:

`B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V011_SELF_TEST_REVIEW`

Stage:

`FIXTURE3_VISIBLE_REGION_CLASSIFY`

Error:

`RuntimeError: visible body empty`

No network or real announcement body access occurred.

## Root cause

The HTML parser used `head` in its start-tag skip set but omitted `head` from the corresponding end-tag skip set.

Therefore the skip state remained nonzero after `</head>` and suppressed the following body.

## V0.1.2 correction

The parser now defines one shared immutable `SKIP_TAGS` set and uses it symmetrically for both start-tag and end-tag transitions.

The head/script synthetic fixture additionally verifies:

- script content is excluded;
- body title remains visible after `</head>`.

No semantic classification, source, event-set or research gate changed.

Implementation:

`research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_2.py`

SHA256:

`a0fe50c52fcdcf3ce71ab0cb3a52c3be802f22426696a7f97e42b4d95a1dce78`

Failure diagnostic:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-v011-selftest-failure-diagnostic-v0.1.json`

Implementation freeze:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-implementation-freeze-v0.1.2.json`

Offline self-test spec:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-offline-selftest-spec-v0.1.2.json`

## Firewalls

Still closed:

- network during self-test;
- real announcement pages;
- price;
- external-reference price;
- index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking.

## Strategy Manager

No strategy review trigger occurred.

## Next state

`PREPARE_AND_SEAL_B15P2_SEMANTIC_AUDIT_V012_OFFLINE_SELFTEST_NO_EXECUTION`
