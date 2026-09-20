# SC001 — B15-P1 Bybit Signature Diagnostic Result v0.1

Date: 2026-09-20
Status: **BYBIT SIGNATURE REVIEW / PUBLIC KEY RECOGNIZED / NO PRICE OUTCOME**

Observed:

- OKX = PASS;
- Bybit retCode changed from 10003 to 10004 after credential update;
- active Bybit key is HMAC;
- Bybit response reports signature-generation error.

Interpretation:

The new Bybit public API key is now recognized by the exchange.

The remaining blocker is signature validation.

The frozen B15 runner uses the current Bybit V5 GET signing rule:

`timestamp + api_key + recv_window + queryString`

with HMAC-SHA256 lowercase hex.

Primary next action:

re-enter the API secret belonging to the exact active HMAC read-only key.

If the exact secret is no longer available, delete that dedicated key and create a fresh HMAC read-only key, immediately preserving the new key+secret pair, then update only Bybit credentials on VPS.

No price/order/transfer/withdraw work is authorized.
