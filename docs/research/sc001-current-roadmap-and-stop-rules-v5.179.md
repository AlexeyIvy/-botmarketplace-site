# SC001 Current Roadmap and Stop Rules v5.179

Date: 2026-09-28
Status: **B15-P2 ANNOUNCEMENT HTML TRANSPORT FAILURE / MINIMAL TRANSPORT PROBE FROZEN**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.177.md`

## Stopped async semantic attempt

The approved async 94-page semantic audit was manually stopped after the transport failure became decisive.

Observed at stop:

- events started: **71 / 94**
- events completed successfully: **0 / 94**
- transport errors: **70**
- representative completed-event elapsed time: approximately **61.1 s**
- representative error:
  `NETWORK_ERROR:TimeoutError:The read operation timed out`
- systemd after manual stop:
  `Result=signal`, `ExecMainStatus=15`

Canonical diagnostic:

`docs/research/sc001-b15p2-announcement-html-transport-failure-diagnostic-v0.1.json`

This is **not** a semantic REVIEW and not a mechanism/economic result.

No terminal semantic report exists.

## Interpretation

The current VPS -> `announcements.bybit.com` HTML path through Python `urllib` is not usable.

With zero successful pages among seventy completed attempts, continuing the remaining frozen URLs would only consume time and cannot satisfy the frozen 94/94 semantic PASS criterion.

No semantic parser tuning is justified from this failure.

## Next diagnostic

A minimal transport-capability probe is frozen.

Script:

`scripts/research/probe-b15p2-announcement-html-transport-v0.1.sh`

SHA256:

`5eaccea53adb8f2529ccf326dfddd5d064e94155c7de97162dce090260150a36`

Contract:

`docs/research/sc001-b15p2-announcement-html-transport-probe-contract-v0.1.json`

Approval code:

`BM-5EACCEA53ADB`

The probe uses only:

- exact frozen DOGUSDT announcement URL;
- exact frozen TONUSDT announcement URL;
- official public Bybit Announcement API as a control.

It compares:

- DNS A / AAAA visibility;
- curl IPv4;
- curl IPv6;
- browser-like User-Agent;
- BotMarketplace User-Agent;
- a second exact page;
- Python urllib reproduction;
- Announcement API control reachability.

The probe does not perform semantic classification and accesses no market price endpoint.

## Decision tree after probe

If announcement HTML succeeds over curl IPv4 while urllib fails:
use a frozen curl-IPv4 acquisition transport and keep semantic rules unchanged.

If IPv4 works but IPv6 fails:
treat the failure as an address-family transport problem and freeze IPv4 acquisition.

If both curl IPv4 and urllib fail but the Announcement API control succeeds:
evaluate, under a separate frozen source-integrity review, whether the API description is sufficient evidence for the required semantic fields. Do **not** silently substitute it for full page body.

If both announcement HTML and Announcement API controls fail:
treat this VPS egress/path as unsuitable for this source and choose a new authorized acquisition route before any semantic inference.

## Firewalls

Still closed:

- price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- event outcome ranking;
- trading.

## Strategy Manager

No strategy-review trigger occurred.

The failure is transport-only and no terminal semantic evidence was produced.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P2_ANNOUNCEMENT_HTML_TRANSPORT_PROBE_BM-5EACCEA53ADB`
