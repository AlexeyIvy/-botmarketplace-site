# SC001 Current Roadmap and Stop Rules v5.184

Date: 2026-09-28
Status: **B15-P2 CURL-TRANSPORT SEMANTIC V0.1.4 OFFLINE SELFTEST SEALED / AWAITING APPROVAL**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.183.md`

## Valid transport evidence

The corrected v0.3 transport probe established:

`CURL_HTML_WORKS_URLLIB_HTML_FAILS`

The selected acquisition path is:

- curl;
- forced IPv4;
- forced HTTP/1.1;
- browser-like User-Agent;
- proxy disabled;
- HTTPS only;
- same-host redirects only;
- bounded timeouts and body size.

## Semantic invariants

The v0.1.4 semantic implementation changes only the transport layer.

Verified unchanged from v0.1.3:

- `classify_text`;
- `article_region`;
- `validate_frozen_input`;
- exact 94-event set;
- semantic PASS/REVIEW rules.

## Automatic pre-94 smoke

The same implementation now provides a dedicated network smoke mode for:

- DOGUSDT;
- TONUSDT.

Smoke checks body acquisition and article-region extraction only.

It does not emit semantic classifications.

A future full 94-event wrapper must require this smoke to PASS before starting the full audit.

## Exact sealed offline self-test

Bundle:

`bundle_20260928T140229Z_8e07e478`

Bundle SHA256:

`7f3cfce3c732cd7184da27c9c6aab7103a59f7bf933dfbb647d59563ea6699c4`

Approval code:

`BM-7F3CFCE3C732`

Expected PASS:

`B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V014_SELF_TEST_PASS`

The bundle has no network, no real announcement bodies and no price/basis/returns/PnL.

## Strategy Manager

No trigger yet.

Transport is resolved, but terminal semantic evidence still does not exist.

## Next state

`AWAIT_EXPLICIT_APPROVAL_TO_RUN_B15P2_SEMANTIC_AUDIT_V014_OFFLINE_SELFTEST_BM-7F3CFCE3C732`
