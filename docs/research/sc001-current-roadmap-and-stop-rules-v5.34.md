# SC001 Current Roadmap and Stop Rules v5.34

Date: 2026-09-20
Status: **CURRENT SC001 ROADMAP — OKX PASS / BYBIT SIGNATURE SECRET-PAIR FIX NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.33.md`

## Capability state

- OKX = PASS;
- Bybit key identity/environment issue resolved;
- Bybit current blocker = retCode 10004 signature error.

## Next action

Update only the Bybit API secret/key pair using the Bybit-only credential updater.

If secret certainty is low, create a fresh dedicated HMAC read-only key and replace both Bybit key+secret together.

Then rerun capability preflight v0.3.

No B15 price outcome is authorized.
