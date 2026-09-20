# SC001 — B15-P1 Read-Only Capability Diagnostic Result v0.1

Date: 2026-09-20
Status: **CAPABILITY REVIEW / TWO CONFIGURATION BLOCKERS IDENTIFIED / NO PRICE OUTCOME**

## 1. Security state

- credential file exists with mode 0600;
- secret values were not printed;
- no price/order/transfer/withdraw endpoints were called.

## 2. OKX

Result:

`REVIEW`

Safe exchange error:

`50110 — request source IP is not included in API key IP whitelist`

Observed diagnostic interpretation:

- request reached OKX;
- authentication layer recognized the API key context;
- VPS egress used IPv6;
- the currently bound API whitelist did not include that IPv6.

Do not store the actual VPS IPv6 or API-key identifier in Git.

Required correction:

- bind both stable VPS IPv4 and VPS IPv6 to the dedicated OKX B15 read-only key;
- retain Read permission only.

## 3. Bybit

Result:

`REVIEW`

Safe exchange error:

`10003 — API key is invalid / key-domain environment mismatch`

Official Bybit semantics distinguish:

- mainnet;
- mainnet-demo;
- testnet;
- testnet-demo.

This is not the Bybit unmatched-IP code (10010) and not signature-error code (10004).

Required correction:

1. verify the newly created B15 key is a Production/Mainnet key, not Demo/Testnet;
2. verify API key and secret belong to the same newly created credential pair;
3. if Production/Mainnet, retain base URL `https://api.bybit.com`;
4. if key was created in Demo Trading, it is not suitable for the intended production status collector; create a production read-only key instead;
5. bind stable VPS IPv4 and IPv6 where Bybit whitelist permits.

## 4. Research disposition

No source-feasibility or strategy verdict changes.

Current gate remains:

`B15_P1_READONLY_CAPABILITY_REVIEW`

Next action:

correct exchange credential/IP configuration and rerun diagnostic v0.2.

No price outcome is authorized.
