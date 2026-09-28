# SC001 Current Roadmap and Stop Rules v5.190

Date: 2026-09-28
Status: **B15-P2 ENGINEERING STABILIZATION / GENERIC NEXT HYDRATION MAPPER V0.3 FROZEN**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.189.md`

## Why the process is being changed

The recent sequence exposed a process problem: transport, source extraction, synthetic fixtures and host-launching were being corrected in small successive iterations.

That produced useful evidence, but too many execution cycles.

The economic/research direction itself is not looping:
- the 94-event set remains frozen;
- no price outcome has been opened;
- each failure has been infrastructure/source-extraction only.

The engineering workflow, however, needed consolidation.

## Proven layers that are no longer being reconsidered

### Frozen evidence
- 94 exact Bybit USDT perpetual delisting events;
- event-set SHA256:
  `1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2`.

### Transport
Binding observation:
`CURL_HTML_WORKS_URLLIB_HTML_FAILS`.

The working transport remains:
- curl;
- IPv4;
- HTTP/1.1;
- browser-like User-Agent;
- no proxy;
- HTTPS only;
- same-host redirects.

### Source structure
DOGUSDT and TONUSDT both show:
`NEXT_HYDRATION_SCRIPT_CONTAINS_TITLE`.

Visible DOM is not the body source.
Do not lower the 120-character integrity gate.

## v0.2 self-test failure

v0.2 did not perform any live network request.

It stopped at:
`RuntimeError: PARENT_CONTENT_HTML`.

The synthetic test assumed closing HTML tags were counted, while its regex counted only opening tags.

Rather than patch that single assertion, v0.2 is retired.

Canonical diagnostic:

`docs/research/sc001-b15p2-next-data-structure-v02-selftest-failure-diagnostic-v0.1.json`

## Generic hydration mapper v0.3

Probe:

`scripts/research/probe-b15p2-next-data-structure-v0.3.py`

SHA256:

`b0a7cbb2aadb68ecf570865205cfb30ecc4b1f953c8a1e16cb839196b22b0bb9`

Host wrapper:

`scripts/research/run-b15p2-next-data-structure-probe-v0.3.sh`

SHA256:

`61314ae69307cd9ec8748d84868c8141e3102d0370e880e0ff2c45c28c2edb59`

Contract:

`docs/research/sc001-b15p2-next-data-structure-probe-contract-v0.3.json`

Approval code:

`BM-61314AE69307`

## Why v0.3 is materially stronger

It does not assume the body is one HTML string.

It maps:
- exact title nodes;
- up to five ancestor levels;
- sibling fields;
- nested dict/list content;
- long unhinted strings/containers;
- JSON-encoded strings;
- HTML structural counts;
- candidate hashes and sizes.

It then compares DOGUSDT and TONUSDT and produces:
- common exact-title paths;
- common candidate paths;
- high-confidence candidate paths present in both events.

No article body text is persisted.

## New pre-freeze engineering rule

Before a new executable candidate becomes a network boundary it must pass three checks:

1. **Synthetic contract checks**
   - string body;
   - nested object/list body;
   - JSON-string body;
   - list-backed title;
   - cross-event consensus;
   - raw-body non-persistence;
   - curl URL/transport policy.

2. **Static invariant audit**
   - probe/wrapper SHA match;
   - v0.3 namespaces only;
   - frozen source/freeze bindings;
   - no market endpoints;
   - firewalls;
   - status parser matches current schema.

3. **Host-launcher audit**
   - output directory exists before namespace;
   - `Type=exec`;
   - job runs as `botmarket`;
   - runtime bound active;
   - unique systemd unit;
   - self-test precedes network.

A line-level correction alone is no longer enough reason to create a fresh network cycle.

## What happens after v0.3

If both events expose at least one stable high-confidence common body candidate:
- freeze that generic path/selection rule;
- implement one hydration body extractor;
- offline-test it;
- run one DOG/TON extraction smoke;
- only then return to the 94-page semantic audit.

If no stable common candidate exists:
- stop the hydration approach and choose another official source route rather than adding more ad-hoc parsing.

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

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P2_GENERIC_NEXT_DATA_MAPPER_V03_BM-61314AE69307`
