# SC001 Current Roadmap and Stop Rules v5.183

Date: 2026-09-28
Status: **B15-P2 CURL IPv4 HTTP1.1 SEMANTIC ADAPTER FROZEN / OFFLINE SELFTEST PENDING**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.182.md`

## Transport decision is now implemented

The valid transport probe established:

`CURL_HTML_WORKS_URLLIB_HTML_FAILS`

The semantic audit implementation now changes only acquisition transport.

Frozen v0.1.4:

`research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_4.py`

SHA256:

`ca96be6b0cb8cae3a37fedb1a22fa2b426f5286ca3decdf7c272bf7cd29feceb`

Implementation freeze:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-implementation-freeze-v0.1.4.json`

Offline self-test spec:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-offline-selftest-spec-v0.1.4.json`

## Semantic invariants

Compared with v0.1.3, the following blocks were checked byte-for-byte unchanged:

- `classify_text`;
- `article_region`;
- `validate_frozen_input`.

The exact 94-event set and PASS/REVIEW rules remain unchanged.

## New acquisition adapter

Every exact announcement page is fetched with:

- curl;
- IPv4 forced;
- HTTP/1.1 forced;
- browser-like User-Agent;
- proxy disabled;
- HTTPS-only protocol;
- same-host redirect checks;
- connect timeout 5 s;
- total timeout 15 s;
- at most two attempts;
- 2 MB body cap.

No search engine or alternate semantic source is introduced.

## Mandatory automatic smoke

Before any full 94-event run, the exact same staged implementation must fetch:

- DOGUSDT;
- TONUSDT.

The smoke does NOT classify semantics.

It verifies:
- HTTP success;
- official final hostname;
- nonempty bounded body;
- exact title;
- article-region extraction.

The full run is permitted only after both smoke events pass.

## Firewalls

Still closed:
- price;
- external-reference price;
- index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking;
- trading.

## Strategy Manager

No trigger yet.

This is transport repair; no terminal semantic evidence exists yet.

## Next state

`PREPARE_AND_SEAL_B15P2_SEMANTIC_AUDIT_V014_OFFLINE_SELFTEST_NO_EXECUTION`
