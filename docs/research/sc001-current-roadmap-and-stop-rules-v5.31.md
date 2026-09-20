# SC001 Current Roadmap and Stop Rules v5.31

Date: 2026-09-20
Status: **CURRENT SC001 ROADMAP — B15-P1 CAPABILITY REVIEW / OKX IP + BYBIT ENVIRONMENT FIX NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.30.md`

## 1. Background branches

B13-C and B14-A remain protected under systemd.

## 2. B15-P1 capability diagnostic

Binding result:

`docs/research/sc001-b15-p1-readonly-capability-diagnostic-result-v0.1.md`

Current state:

`B15_P1_READONLY_CAPABILITY_REVIEW`

## 3. OKX blocker

`50110`

VPS request used IPv6 that was not included in the dedicated API key IP whitelist.

Required:

bind stable VPS IPv4 + IPv6.

## 4. Bybit blocker

`10003`

API key is invalid for the current environment/domain or the entered key does not match the production credential pair.

Required:

verify Production/Mainnet key and matching key+secret pair.

Mainnet default remains:

`https://api.bybit.com`

## 5. Security

No secrets are to be pasted into chat or Git.

Keep:

- OKX Read only;
- Bybit readOnly;
- no Trade/Withdraw authority.

## 6. Next action

Correct account/IP/environment configuration, then rerun:

`sc001_b15_p1_readonly_capability_preflight_v0_2.py`

Do not modify research logic or open prices.
