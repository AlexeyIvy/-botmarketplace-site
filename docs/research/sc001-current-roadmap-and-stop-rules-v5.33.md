# SC001 Current Roadmap and Stop Rules v5.33

Date: 2026-09-20
Status: **CURRENT SC001 ROADMAP — BYBIT STORED KEY IDENTITY CHECK NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.32.md`

## Current capability state

- OKX = PASS;
- Bybit = REVIEW;
- Bybit standard environment probe = 10003 on mainnet/demo/testnet.

## Next action

Compare only the stored Bybit PUBLIC API key fingerprint/suffix with the active key in Bybit API Management.

Do not print or compare the API secret in chat/logs.

If public key mismatches: rerun credential installer with the correct current key+secret pair.

If public key matches: review key type/account routing before recreating credentials.

No price outcome is authorized.
