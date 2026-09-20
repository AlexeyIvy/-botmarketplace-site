# SC001 Current Roadmap and Stop Rules v5.30

Date: 2026-09-20
Status: **CURRENT SC001 ROADMAP — B15-P1 KEYS READY / READ-ONLY CAPABILITY PREFLIGHT NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.29.md`

## 1. Background branches

B13-C and B14-A remain protected under systemd.

## 2. B15-P1 state

User has created dedicated API credentials for:

- OKX;
- Bybit.

No secrets are stored in Git or chat.

## 3. Account region/domain posture

User KYC/registration context:

Russian Federation.

Default capability domains:

- OKX Global: `https://openapi.okx.com`;
- Bybit mainnet: `https://api.bybit.com`.

Capability preflight may reveal a domain mismatch; if so, adjust only the configured base URL, not research logic.

## 4. Security install

Credential installer:

`ops/b15/b15_p1_install_credentials.py`

Target file:

`/home/botmarket/.config/sc001/b15-p1.env`

Required mode:

`0600`

Secrets must not be pasted into chat.

## 5. Capability preflight

Protocol:

`docs/research/sc001-b15-p1-readonly-capability-preflight-v0.1.md`

Runner:

`research/sc001/sc001_b15_p1_readonly_capability_preflight_v0_1.py`

Freeze:

`docs/research/sc001-b15-p1-readonly-capability-implementation-freeze-v0.1.json`

## 6. PASS requirements

OKX:

- authenticated account/config works;
- API permission is exactly `read_only`;
- currencies endpoint returns chain-level transferability fields.

Bybit:

- query-api works;
- `readOnly=1`;
- coin-info returns chain-level deposit/withdraw status.

Both venue clocks:

- absolute skew <=10 seconds.

## 7. Firewalls

No:

- market prices;
- spread/basis;
- orders;
- transfers;
- withdrawals;
- PnL.

## 8. Next action

1. install secrets locally on VPS;
2. run one-shot capability preflight;
3. only after PASS freeze canonical route/universe identity and build prospective 15-second status collector.
