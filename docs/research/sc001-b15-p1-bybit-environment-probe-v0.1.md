# SC001 — B15-P1 Bybit Credential Environment Probe v0.1

Date: 2026-09-20
Status: **DIAGNOSTIC ONLY / NO PRICE OUTCOME**

Purpose:

Safely determine whether the stored Bybit read-only credential belongs to mainnet, mainnet-demo or testnet after the mainnet capability call returned retCode 10003.

Probe only:

`GET /v5/user/query-api`

Domains:

- mainnet: `https://api.bybit.com`;
- mainnet-demo: `https://api-demo.bybit.com`;
- testnet: `https://api-testnet.bybit.com`.

Transport:

IPv4 only.

The probe does not print:

- API key;
- API secret;
- UID;
- IP values;
- signatures.

It does not call price, order, transfer or withdrawal endpoints.

Interpretation:

- exactly one retCode=0 => credential environment identified;
- all 10003 => stored API key is likely not the intended key, or the key/account environment requires manual review;
- 10004 => key recognized but secret/signature pair mismatch;
- 10010 => IP whitelist mismatch.
