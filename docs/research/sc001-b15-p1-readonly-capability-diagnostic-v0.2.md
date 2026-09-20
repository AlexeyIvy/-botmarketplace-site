# SC001 — B15-P1 Read-Only Capability Diagnostic v0.2

Date: 2026-09-20
Status: **DIAGNOSTIC ONLY / NO PRICE OUTCOME / SECRETS REDACTED**

Purpose: diagnose venue-by-venue capability failures after v0.1 returned an undifferentiated HTTP error.

Rules:
- run OKX and Bybit checks independently;
- continue to Bybit even if OKX fails;
- expose only HTTP status and safe exchange error fields;
- never print API key, secret, passphrase, UID, bound IP values, signature or auth headers;
- keep all v0.1 price/order/transfer/withdraw firewalls unchanged.

PASS remains:
`B15_P1_READONLY_CAPABILITY_PASS`

Any venue failure:
`B15_P1_READONLY_CAPABILITY_REVIEW`
