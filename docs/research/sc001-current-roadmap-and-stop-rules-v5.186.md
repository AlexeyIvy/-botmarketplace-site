# SC001 Current Roadmap and Stop Rules v5.186

Date: 2026-09-28
Status: **B15-P2 CURL SEMANTIC NETWORK BOUNDARY V0.3 FROZEN / AWAITING APPROVAL**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.185.md`

## Offline prerequisite

The v0.1.4 semantic implementation passed exact sealed offline validation:

- job: `job_20260928T140518Z_694b33e5`
- implementation SHA256:
  `ca96be6b0cb8cae3a37fedb1a22fa2b426f5286ca3decdf7c272bf7cd29feceb`
- exact PASS:
  `B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V014_SELF_TEST_PASS`

## Transport basis

The valid v0.3 transport probe is binding:

- result SHA256:
  `97498ed8f60ab119d5a547a449d1e449366c4226d55442ed8d7abb0d1ba39e6f`
- observed:
  `CURL_HTML_WORKS_URLLIB_HTML_FAILS`

Selected acquisition path:

- curl;
- IPv4;
- HTTP/1.1;
- browser-like User-Agent;
- no proxy;
- HTTPS only;
- same-host redirects.

## Frozen network wrapper

`scripts/research/run-b15p2-announcement-body-semantic-audit-v0.3.sh`

SHA256:

`90b028b3cf4c1d12e364b7b5e147c7a44b366ddbb9b95c095cf4f49425b2513b`

Launch contract:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-networked-launch-contract-v0.3.json`

Approval code:

`BM-90B028B3CF4C`

No network execution is authorized by this roadmap update.

## Fail-closed execution sequence

After explicit approval:

1. no-network SHA/schema/firewall preflight;
2. stage exactly six frozen files;
3. rerun staged v0.1.4 offline self-test;
4. run real DOGUSDT + TONUSDT transport smoke;
5. verify smoke result structurally and verify all firewalls;
6. only on smoke PASS create the launch marker;
7. start the 94-page full semantic audit asynchronously;
8. return the Termux prompt for same-session status polling.

If smoke fails, the full 94-page run cannot start.

## Smoke is not semantic evidence

The smoke verifies only acquisition/body integrity:
- HTTP body;
- final official host;
- exact title;
- article-region extraction;
- hashes.

It explicitly does not classify settlement semantics.

Therefore a smoke PASS or failure does not trigger the Strategy Manager.

## Full terminal result

The full 94-page PASS/REVIEW is strategy-relevant.

After it terminates:

1. freeze the canonical result;
2. create `sc001.worker_result_manifest.v0.1`;
3. trigger Strategy Watch / Research Strategy Manager;
4. keep all price outcomes closed until the manager completes the mandatory pre-price mechanism gate.

## Firewalls

Still closed:
- affected-contract price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking;
- trading.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P2_SEMANTIC_NETWORK_V03_BM-90B028B3CF4C`
