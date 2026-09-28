# SC001 Current Roadmap and Stop Rules v5.181

Date: 2026-09-28
Status: **B15-P2 TRANSPORT PROBE V0.2 INVALID CURL SUBRESULTS / V0.3 CORRECTED BOUNDARY FROZEN**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.180.md`

## V0.2 result interpretation

The v0.2 probe completed and wrote a report, but its curl subprobes were invalid.

Observed curl failure:

`curl: (2) no URL specified`

Root cause:
the v0.2 curl command builder never appended the target URL to the command list.

Therefore the v0.2 derived pattern:

`ANNOUNCEMENT_HTML_AND_API_CONTROL_FAIL_FROM_VPS`

is NOT accepted.

### Trusted evidence retained from v0.2

- `announcements.bybit.com`: IPv4 addresses present, IPv6 addresses absent;
- `api.bybit.com`: IPv4 addresses present, IPv6 addresses absent;
- Python urllib default to DOGUSDT page: read timeout;
- Python urllib forced IPv4: read timeout;
- Python urllib forced IPv6: no IPv6 addresses.

### Discarded v0.2 evidence

All curl-based reachability, HTTP-version, User-Agent, second-page and Announcement-API-control conclusions are discarded.

Canonical diagnostic:

`docs/research/sc001-b15p2-announcement-transport-probe-v02-command-construction-failure-diagnostic-v0.1.json`

## Corrected v0.3 probe

Script:

`scripts/research/probe-b15p2-announcement-html-transport-v0.3.py`

SHA256:

`e3295d3c79d480e8efa17adf8fcec0f0b85cac32903b580b5535b0ef9963d42f`

Approval code:

`BM-E3295D3C79D4`

Key safeguards:

- explicit `--url <URL>` pair in every curl command;
- self-test verifies the URL pair exactly once;
- IPv4, IPv6 and HTTP/1.1 command builders tested offline;
- no-proxy, HTTPS-only and timeout options tested offline;
- same-host redirect policy retained;
- proxy-disabled urllib retained;
- unique `v0_3` result namespace;
- atomic writes and predictable output ownership.

## Execution sequence after fresh approval

1. `--mode self-test` — no network;
2. only on PASS, `--mode live`;
3. inspect the concise printed transport matrix;
4. choose one minimal semantic-acquisition transport correction.

## Firewalls

Still closed:
- semantic classification;
- price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- trading.

## Strategy Manager

No strategy-review trigger.

No terminal semantic evidence exists yet.

## Next state

`AWAIT_FRESH_EXPLICIT_APPROVAL_FOR_B15P2_TRANSPORT_PROBE_V03_BM-E3295D3C79D4`
