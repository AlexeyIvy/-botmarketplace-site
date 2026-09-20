# SC001 Current Roadmap and Stop Rules v5.35

Date: 2026-09-20
Status: **CURRENT SC001 ROADMAP — BYBIT BASE URL REPAIR BEFORE SIGNATURE RETEST**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.34.md`

Observed current issue:

`SC001_B15_BYBIT_BASE_URL` accidentally contains the VPS IPv4 rather than the Bybit REST URL.

This caused:

`ValueError: unknown url type`

and prevented the new Bybit key/secret pair from being tested at all.

Next action:

1. repair only the Bybit base URL to `https://api.bybit.com`;
2. preserve all credentials;
3. rerun capability preflight v0.3.

No price outcome is authorized.
