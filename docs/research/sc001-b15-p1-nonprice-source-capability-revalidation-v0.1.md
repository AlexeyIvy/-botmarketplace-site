# SC001 — B15-P1 Collector Live Read-Only Source Capability Revalidation v0.1

Date: 2026-09-24  
Status: **PRE-LAUNCH CAPABILITY GATE / COLLECTOR LAUNCH NOT AUTHORIZED**

## 1. Purpose

Revalidate the dedicated B15 exchange credentials and source-only REST access after the frozen non-price collector implementation v0.1.2 passed its offline compile/self-test chain.

This gate may perform authenticated read-only REST calls.

It does **not** launch the collector.

## 2. Frozen implementation anchors

Runner:

`research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_2.py`

Runner SHA256:

`157b1e7e77a9d4299c06ac60ce56e1544335d7435d9f25a6212d7f417b312b3d`

Implementation freeze SHA256:

`fc4d7496870896ff7b8036ce9c17a3d5059142be2e18dd2c21eb646f8c32fabf`

Final route graph SHA256:

`06a9edd309a002aa5dc8408d992cff7b774604fc1cfb04f90fd7f56333f27928`

Service candidate SHA256:

`c71818e0b53cb087c5023361a50a19fbce918d87272f712178e92355bb184544`

Offline self-test manifest SHA256:

`d54b4ee0711dfe39ae1b606ae2f7caa25115d70106f405960cfddab87b85f0ef`

## 3. Credential source

Use only:

`/home/botmarket/.config/sc001/b15-p1.env`

Required mode:

`0600`

Required variables:

- `SC001_B15_BYBIT_API_KEY`
- `SC001_B15_BYBIT_API_SECRET`
- `SC001_B15_BYBIT_BASE_URL`
- `SC001_B15_OKX_API_KEY`
- `SC001_B15_OKX_API_SECRET`
- `SC001_B15_OKX_PASSPHRASE`
- `SC001_B15_OKX_BASE_URL`

Never print raw secret values, signatures or authentication headers.

## 4. Permission requirements

### Bybit

Require:

- `readOnly = 1`;
- Wallet permission must not contain `Withdraw`;
- API key IP binding must be present.

### OKX

Require:

- permission set exactly `read_only`;
- API key IP binding must be present.

Any mismatch => REVIEW.

## 5. Allowed live endpoints

### Public non-price metadata/time

Bybit:
- `GET /v5/market/time`
- `GET /v5/market/instruments-info?category=spot`

OKX:
- `GET /api/v5/public/time`
- `GET /api/v5/public/instruments?instType=SPOT`

These calls are metadata/time only. No ticker/orderbook/candle endpoint is allowed.

### Authenticated read-only capability/source

Bybit:
- `GET /v5/user/query-api`
- `GET /v5/asset/coin/query-info`
- one exact spot pair probe through `GET /v5/account/fee-rate`

OKX:
- `GET /api/v5/account/config`
- `GET /api/v5/asset/currencies`
- one exact spot pair probe through `GET /api/v5/account/trade-fee`

Forbidden:
- order placement;
- cancel/modify order;
- transfer;
- withdrawal;
- price ticker/orderbook/candle data.

## 6. Source-schema requirements

Bybit coin-info must expose the fields required by the frozen collector, including:

- chain identity;
- deposit/withdraw state;
- fixed withdrawal fee;
- percentage withdrawal fee;
- min deposit/withdrawal;
- confirmation metadata.

OKX currencies must expose the collector source fields, including:

- chain identity;
- deposit/withdraw state;
- fixed fee;
- fee currency;
- burning fee rate;
- min deposit/withdrawal;
- withdrawal precision;
- confirmation metadata.

Empty values are allowed where the venue legitimately returns empty metadata; missing required schema keys are not.

## 7. Exact USDT spot pair qualification

The frozen identity universe is **not** modified by pair qualification.

Start from the 192 frozen admitted assets.

Read live public spot-instrument metadata and create per-venue exact pair lists:

Bybit:
- quoteCoin = USDT;
- status = Trading.

OKX:
- quoteCcy = USDT;
- state = live.

For every frozen admitted asset, record whether an exact USDT spot pair is currently qualified on each venue.

Pair absence does not remove the asset from the frozen identity universe.

It means later economic admission for that venue/pair is unavailable until a future capability/version gate establishes otherwise.

Do not infer pair existence from ticker concatenation alone.

## 8. Account/pair fee probe

Choose one asset with a qualified USDT spot pair on both venues, preferring BTC when available.

Probe the authenticated exact pair fee endpoint on each venue.

Require a valid exact response with taker/maker fee fields.

Do not use the returned fee to tune research thresholds.

This only proves the slow fee lane can access account/pair fee metadata.

## 9. Clock and transport

Use process-local IPv4-only DNS resolution, matching the prior B15 credential/IP-whitelist configuration.

Maximum allowed absolute exchange/server clock skew:

`10,000 ms`

No system-wide routing change is allowed.

## 10. Capability snapshot

On PASS, write:

`~/sc001_data/SC001_B15P1_TRANSFERABILITY/source_capability_snapshot.json`

Snapshot must be secret-free and contain:

- PASS status;
- exact implementation anchors;
- read-only permission proof;
- source endpoint PASS;
- base URLs;
- clock skew;
- pair qualification lists/counts;
- safe fee-endpoint probe summary;
- generation timestamp.

The collector `--mode run` validates this snapshot before any exchange call.

## 11. PASS

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS`

PASS authorizes only the next pre-launch work:

- install/verify the frozen systemd candidate;
- prepare an exact launch-authorization record.

PASS does **not** itself start the collector.

## 12. REVIEW

Any permission mismatch, IP-binding failure, auth failure, source schema drift, clock-skew failure, empty common pair set, frozen-anchor mismatch or forbidden endpoint detection:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_REVIEW`

Then STOP.

## 13. Price firewall

Throughout this gate:

- price_data_used = false;
- pnl_data_used = false;
- collector_launch_authorized = false;
- live_execution_authorized = false.
