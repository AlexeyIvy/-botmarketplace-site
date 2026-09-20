# SC001 — B15-P1 Bybit-Only Credential Updater v0.1

Date: 2026-09-20
Status: **OPERATIONAL SECURITY HELPER**

Purpose:

Replace only the stored Bybit API key/secret pair while preserving the already validated OKX credentials unchanged.

Target:

`/home/botmarket/.config/sc001/b15-p1.env`

Security:

- secret input uses hidden getpass entry;
- no secret values are printed;
- output mode remains 0600;
- OKX key, secret, passphrase and base URL are preserved byte-for-value;
- no network/API calls are made by this helper.

Use after the previously stored Bybit API key was identified as stale/deleted.
