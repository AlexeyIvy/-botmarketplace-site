# SC001 Current Roadmap and Stop Rules v5.182

Date: 2026-09-28
Status: **B15-P2 TRANSPORT PATH RESOLVED / CURL IPv4 HTTP1.1 ACQUISITION ADAPTER NEXT**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.181.md`

## Transport probe v0.3

The corrected v0.3 transport probe produced a valid terminal result:

`CURL_HTML_WORKS_URLLIB_HTML_FAILS`

Canonical summary:

`docs/research/sc001-b15p2-announcement-html-transport-probe-v03-result-v0.1.json`

## What is established

### Working paths

DOGUSDT exact frozen page:
- curl IPv4 + browser-like UA + HTTP/2: HTTP 200;
- curl IPv4 + browser-like UA + forced HTTP/1.1: HTTP 200.

TONUSDT exact frozen page:
- curl IPv4 + browser-like UA: HTTP 200.

Official Announcement API control:
- curl IPv4: HTTP 200.

### Non-working / unavailable paths

- DNS exposes no IPv6 addresses for the tested Bybit hosts.
- Python urllib default: read timeout.
- Python urllib forced IPv4: read timeout.
- Python urllib forced IPv6: no IPv6 addresses.
- curl IPv4 + BotMarketplace UA over HTTP/2: curl 92 INTERNAL_ERROR.

The last observation does not by itself prove a pure User-Agent effect because bot-UA + HTTP/1.1 was not tested.

## Minimal transport decision

Do not change semantic rules.

Replace only page acquisition with:

- curl;
- forced IPv4;
- forced HTTP/1.1;
- browser-like User-Agent;
- no proxy;
- HTTPS only;
- same-host redirects only;
- bounded connect/total timeout;
- body-size cap.

This exact combination has a direct successful frozen-page observation and avoids both known failing paths.

## Mandatory two-page smoke before 94

Before a full semantic retry, the new acquisition adapter must fetch only:

- frozen DOGUSDT page;
- frozen TONUSDT page.

For each it must prove:
- HTTP 200;
- final host remains `announcements.bybit.com`;
- nonempty body under size cap;
- exact contract title is present;
- exact article region can be extracted;
- no semantic classification is emitted.

Only if both pass may the same exact transport bytes proceed to all 94 frozen URLs.

## Firewalls

Still closed:
- price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking;
- trading.

## Strategy Manager

No strategy-review trigger.

The transport path has been resolved, but no terminal semantic evidence has yet been produced.

## Next state

`BUILD_FREEZE_AND_OFFLINE_VALIDATE_CURL_IPV4_HTTP11_SEMANTIC_ACQUISITION_ADAPTER`
