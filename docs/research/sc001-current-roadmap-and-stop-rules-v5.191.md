# SC001 Current Roadmap and Stop Rules v5.191

Date: 2026-09-28
Status: **B15-P2 GENERIC HYDRATION MAPPER V0.4 STABILIZED / EXACT-STAGE BOUNDARY FROZEN**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.190.md`

## Engineering conclusion

The user correctly flagged that the implementation process was becoming too iterative.

The research hypothesis itself is not looping:
- the 94-event evidence set remains frozen;
- no price outcome has been opened;
- no semantic result has yet been used for tuning.

The repeated failures were in transport/source-extraction/host-launch plumbing.

Therefore the engineering approach is now consolidated rather than patched line-by-line.

## Proven layers now treated as fixed

### Evidence identity
- exact frozen 94-event set;
- event-set SHA256:
  `1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2`.

### Transport
`CURL_HTML_WORKS_URLLIB_HTML_FAILS`

Use:
- curl;
- IPv4;
- HTTP/1.1;
- browser-like UA;
- no proxy;
- HTTPS only;
- same-host redirects.

### Source structure
DOGUSDT and TONUSDT:
`NEXT_HYDRATION_SCRIPT_CONTAINS_TITLE`

Visible DOM is not the body source.
Do not lower the 120-character integrity gate.

## v0.3 host failure

v0.3 never reached self-test or network.

It stopped at:

`probe_not_readable_by_botmarket`

because the wrapper assumed the unprivileged runtime user could directly read the GitHub-Control repo.

Canonical diagnostic:

`docs/research/sc001-b15p2-next-data-structure-v03-host-preflight-permission-failure-diagnostic-v0.1.json`

## v0.4 architectural correction

### Probe

`scripts/research/probe-b15p2-next-data-structure-probe-v0.4.py`

SHA256:

`5517ec5304e44e1ea5ebbaef043223a1f09067256da10d20ddf9837d7513181f`

### Host wrapper

`scripts/research/run-b15p2-next-data-structure-probe-v0.4.sh`

SHA256:

`42eac9cc82f6a5649f5bacb0c459563f52ea44b8ead36876f23510f0df9f2bc1`

### Contract

`docs/research/sc001-b15p2-next-data-structure-probe-contract-v0.4.json`

### Approval code

`BM-42EAC9CC82F6`

## Exact staging model

The host wrapper, running as root only for preparation:

1. verifies SHA256 of:
   - v0.4 probe;
   - frozen source result;
   - frozen event-set freeze;
2. deletes/recreates a dedicated v0.4 staging tree;
3. copies exactly those three files;
4. verifies staged SHA256 again;
5. makes staged files `root:botmarket 0440`;
6. confirms `botmarket` can read but cannot write them;
7. confirms exactly three staged files and no symlinks;
8. runs the self-test as `botmarket` from staged bytes;
9. only if PASS, starts the live mapper as `botmarket` from the same staged bytes.

The live job has no dependency on direct access to GitHub-Control repo.

## Generic mapper scope

v0.4 deliberately does not assume that the title/body is inside `__NEXT_DATA__`.

It:
- inspects all parseable hydration JSON scripts;
- identifies `__NEXT_DATA__` separately;
- distinguishes exact-title equality from mere substring containment;
- detects title outside `__NEXT_DATA__`;
- prevents non-NEXT JSON script-role collisions with indexed identities;
- supports string, dict/list and JSON-string bodies;
- maps up to five ancestor levels;
- includes large unknown-key fallbacks;
- derives cross-event consensus by `script role + JSON path`;
- records path depth so equally strong candidates can favor more specific paths.

No article body text is persisted.

## Stop rule

This is the last hydration-structure diagnostic iteration.

If DOGUSDT and TONUSDT yield at least one stable high-confidence common body identity:
- freeze the generic body-selection rule;
- implement the final hydration extractor;
- offline-test once;
- run DOG/TON extraction smoke;
- return to the full 94-page semantic audit.

If no stable high-confidence common body identity exists:
- stop hydration parser work;
- select another official extraction route;
- do not add another ad-hoc hydration probe.

## Firewalls

Still closed:
- article text persistence in diagnostics;
- semantic classification;
- price;
- external-reference price;
- index values;
- basis/spread;
- returns;
- PnL;
- trading.

## Strategy Manager

No trigger yet.

No terminal semantic evidence exists.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P2_GENERIC_HYDRATION_MAPPER_V04_BM-42EAC9CC82F6`
