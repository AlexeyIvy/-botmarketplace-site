# SC001 Current Roadmap and Stop Rules v5.180

Date: 2026-09-28
Status: **B15-P2 ROBUST ANNOUNCEMENT TRANSPORT PROBE V0.2 FROZEN + APPROVED / AWAITING HOST EXECUTION**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.179.md`

## Why v0.1 is not being run

Before execution, the transport-probe v0.1 received a full programmer-expert audit.

Several prospective failure modes were found:

- `getent ahostsv6` under `set -euo pipefail` could abort merely because AAAA is absent;
- curl/urllib could inherit proxy environment unlike the original clean systemd job;
- shell-built JSON was unnecessarily fragile;
- redirect scope was not enforced by hostname;
- Python address-family behavior was not isolated;
- missing curl could be misclassified as remote transport failure;
- repeated execution could overwrite the same report.

Therefore v0.1 is superseded before execution.

## Frozen v0.2 probe

Script:

`scripts/research/probe-b15p2-announcement-html-transport-v0.2.py`

SHA256:

`11516abea2fd3e46297d05e1ae29066918b78926ace7ef69a0a103085e96014f`

Contract:

`docs/research/sc001-b15p2-announcement-html-transport-probe-contract-v0.2.json`

Approval code:

`BM-11516ABEA2FD`

The user explicitly authorized execution of the finalized probe after this expert review.

## Safety and reproducibility

The execution sequence is:

1. local no-network self-test;
2. only if PASS, bounded live transport probe.

The self-test validates:
- exact allowed URL policy;
- cross-host/http rejection;
- decision-pattern classification;
- curl-unavailable classification;
- curl metrics parser.

The live probe uses only:
- frozen DOGUSDT announcement URL;
- frozen TONUSDT announcement URL;
- official public Announcement API control.

It performs no semantic classification and opens no price endpoint.

All network paths are bounded:
- curl connect timeout: 4 s;
- curl hop timeout: 10 s;
- urllib timeout: 10 s;
- maximum same-host redirect hops: 3;
- no automatic request retries.

## Diagnostic value

The probe is designed to distinguish:

- IPv4 vs IPv6;
- curl vs urllib;
- browser-like vs BotMarketplace User-Agent;
- default curl protocol vs forced HTTP/1.1;
- page-specific failure vs host-wide HTML failure;
- announcement HTML vs Announcement API control.

## Firewalls

Still closed:
- semantic classification;
- price;
- external-reference price;
- index values;
- basis/spread;
- returns;
- PnL;
- trading.

## Strategy Manager

No strategy-review trigger.

This remains transport diagnostics only.

## Next state

`EXECUTE_APPROVED_B15P2_ANNOUNCEMENT_TRANSPORT_PROBE_V02_BM-11516ABEA2FD`
