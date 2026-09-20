# SC001 Current Roadmap and Stop Rules v5.32

Date: 2026-09-20
Status: **CURRENT SC001 ROADMAP — B15-P1 IPV4-ONLY AUTH TRANSPORT / RECHECK NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.31.md`

## 1. Background branches

B13-C and B14-A remain unchanged under systemd.

## 2. B15-P1 transport correction

Observed:

- OKX previously used VPS IPv6 and failed IP whitelist;
- Bybit UI accepted the stable VPS IPv4 and rejected the supplied IPv6.

Decision:

`B15_AUTH_REST_TRANSPORT = IPV4_ONLY`

This is process-local to B15. No system-wide routing change.

## 3. Whitelist policy

Use the stable VPS IPv4 on both dedicated B15 read-only API keys.

Do not require IPv6 for B15 authenticated REST.

## 4. Diagnostic

Use:

`research/sc001/sc001_b15_p1_readonly_capability_preflight_v0_3.py`

If OKX IPv4 is correctly bound, the prior IPv6 whitelist error should disappear.

If Bybit still returns 10003, investigate Production/Mainnet environment or key-pair mismatch, not IP formatting.

## 5. No-price firewall

No B15 price/spread/return/PnL work yet.
