# SC001 — B15-P1 Read-Only Credential Security Contract v0.1

Date: 2026-09-19
Status: **SECURITY CONTRACT BEFORE CREDENTIAL CREATION**

## 1. Purpose

Allow authenticated transfer-status observation without giving the B15 research collector trading or withdrawal authority.

## 2. Dedicated credentials

Create dedicated API credentials for B15 source collection.

Do not reuse a key that has trading or withdrawal permissions when a read-only key can be used.

### OKX

Required permission:

`Read`

Forbidden:

- Trade;
- Withdraw.

Preferred:

- bind to the VPS public IP.

Required values are stored only on VPS:

- API key;
- secret key;
- passphrase;
- correct regional API domain.

### Bybit

Required:

`readOnly = 1`

Do not enable withdrawal authority.

Preferred:

- bind to VPS IP if available/account-compatible.

Required values are stored only on VPS:

- API key;
- API secret;
- correct regional API domain.

## 3. Secret location

Preferred local path:

`/home/botmarket/.config/sc001/b15-p1.env`

Required filesystem mode:

`0600`

The file must not be added to Git.

## 4. Variable names

Use:

- `SC001_B15_OKX_API_KEY`;
- `SC001_B15_OKX_API_SECRET`;
- `SC001_B15_OKX_PASSPHRASE`;
- `SC001_B15_OKX_BASE_URL`;
- `SC001_B15_BYBIT_API_KEY`;
- `SC001_B15_BYBIT_API_SECRET`;
- `SC001_B15_BYBIT_BASE_URL`.

## 5. Logging

Never print:

- raw API key;
- raw secret;
- OKX passphrase;
- request signature;
- complete authentication headers.

Capability-preflight output may print only:

- venue;
- HTTP/API success state;
- key read-only/permission verification when the venue exposes it;
- number of returned currencies/chains;
- schema presence flags.

## 6. Research firewall

Credential installation does not authorize:

- order placement;
- transfer;
- withdrawal;
- price outcome analysis;
- PnL.

The collector remains source-state-only.
