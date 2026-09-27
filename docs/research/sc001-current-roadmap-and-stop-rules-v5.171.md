# SC001 Current Roadmap and Stop Rules v5.171

Date: 2026-09-27
Status: **B15-P2 SEMANTIC-AUDIT V0.1.2 OFFLINE SELFTEST SEALED / AWAITING EXPLICIT APPROVAL**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.170.md`

## Prior v0.1.1 self-test

Bundle:
`bundle_20260927T195617Z_135de720`

Job:
`job_20260927T195919Z_b604441c`

Package integrity:
`PASS`

Observed:
`B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V011_SELF_TEST_REVIEW`

Failure stage:
`FIXTURE3_VISIBLE_REGION_CLASSIFY`

Error:
`RuntimeError: visible body empty`

## Root cause

The HTML parser added `head` to the start-tag suppression set but not to the end-tag suppression set.

After `</head>`, the parser therefore remained in suppressed state and hid the real `<body>`.

## V0.1.2 correction

The parser now uses one shared immutable:

`SKIP_TAGS = {head, script, style, noscript, svg}`

for both start and end transitions.

The synthetic head/script fixture explicitly verifies that:
- script content is hidden;
- body content becomes visible after `</head>`.

No semantic classification rule, source scope, event-set identity or research gate changed.

## Exact sealed v0.1.2 self-test

Bundle:
`bundle_20260927T200214Z_b321091a`

Bundle SHA256:
`5015f01b988d41ea8b48bb8982b13369e7c4dc9d8daf5533972fbcfa5589dd67`

Approval code:
`BM-5015F01B988D`

Expected PASS:
`B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V012_SELF_TEST_PASS`

No network, real announcement bodies, price, basis, returns or PnL are included.

## Strategy Manager

No strategy-review trigger occurred.

Both v0.1 and v0.1.1 failures were synthetic engineering failures with no new market evidence.

## Next state

`AWAIT_EXPLICIT_APPROVAL_TO_RUN_B15P2_SEMANTIC_AUDIT_V012_OFFLINE_SELFTEST_BM-5015F01B988D`
