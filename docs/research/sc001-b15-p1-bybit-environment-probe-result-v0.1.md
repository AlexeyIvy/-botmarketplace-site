# SC001 — B15-P1 Bybit Environment Probe Result v0.1

Date: 2026-09-20
Status: **BYBIT CREDENTIAL IDENTITY REVIEW / NO PRICE OUTCOME**

Observed:

- MAINNET -> retCode 10003;
- DEMO -> retCode 10003;
- TESTNET -> retCode 10003;
- environment = UNRESOLVED.

Interpretation:

The stored Bybit public API key is not recognized in the three standard environments tested.

This makes a simple mainnet/demo/testnet domain mismatch unlikely.

Primary next checks:

1. compare the stored public API key identifier with the currently active key shown in Bybit API Management;
2. verify the stored key belongs to the newly created read-only credential rather than an older/deleted key;
3. verify the key type is system-generated HMAC if using the current HMAC preflight;
4. only if the public key matches, investigate account/region-specific routing or recreate the dedicated key.

No secret value is to be printed or copied into research logs.
