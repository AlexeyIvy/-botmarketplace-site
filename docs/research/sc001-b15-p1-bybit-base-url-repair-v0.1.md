# SC001 — B15-P1 Bybit Base-URL Repair v0.1

Date: 2026-09-20
Status: **OPERATIONAL REPAIR ONLY**

Observed issue:

`SC001_B15_BYBIT_BASE_URL` was accidentally set to a raw VPS IPv4 address.

Repair:

restore:

`https://api.bybit.com`

without changing:

- OKX credentials;
- Bybit API key;
- Bybit API secret;
- any research rule.

Credential file remains mode 0600.
