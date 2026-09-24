# SC001 Current Roadmap and Stop Rules v5.75

Date: 2026-09-24  
Status: **B15-P1 LIVE SOURCE CAPABILITY v0.2.1 PASS / COLLECTOR PRELAUNCH GATE NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.74.md`

## Live authenticated read-only source capability revalidation

Wrapper:

`scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.2.sh`

Wrapper SHA256:

`0bc379933be07fb7b31e2efe4a2f06b4b7b99ad2fdc4db403dbffbe63ebc556e`

Observed terminal status:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_V021_PASS`

Probe status:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS`

Snapshot:

`/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/source_capability_snapshot.json`

Snapshot SHA256:

`14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc`

## Verified live capability

Permissions:
- Bybit readOnly = 1;
- Bybit Withdraw token present = false;
- Bybit IP bound = true;
- OKX permission = read_only;
- OKX IP bound = true.

Source schemas:
- Bybit source chain rows = 1036;
- OKX source chain rows = 591.

Frozen pair coverage:
- admitted assets = 192;
- qualified Bybit USDT pairs = 192;
- qualified OKX USDT pairs = 192;
- qualified both-venue assets = 192.

Fee endpoint probe:
- asset = BTC;
- pass = true.

Security:
- price endpoints called = false;
- order/transfer/withdraw endpoints called = false;
- collector launch authorized = false;
- price data used = false;
- PnL data used = false;
- live execution authorized = false;
- security firewall = PASS.

The terminal returned normally to the shell prompt.

## Interpretation

The current Bybit/OKX API adapters and credentials are operationally compatible with the frozen B15-P1 source model across the full 192-asset admitted universe.

This is a source-capability PASS only. It does not establish:
- profitable transferability events;
- economic edge;
- executable price spreads;
- post-cost profitability;
- live trading readiness.

## Collector launch protocol gate

The frozen collector protocol requires, before collector start:

1. collector design preflight PASS — complete;
2. implementation freeze — complete;
3. offline parser/state-machine fixtures PASS — complete;
4. local output/write/restart fixtures PASS — complete;
5. live read-only source capability revalidation PASS — **complete**;
6. systemd unit / launch-readiness verification PASS — **next**;
7. explicit collector-launch authorization — not yet granted.

Collector authorization remains false.

## Next state

`PREPARE_B15P1_COLLECTOR_SYSTEMD_AND_LAUNCH_READINESS_PREFLIGHT`

Do not start or enable the collector yet.

Do not create the active runtime `collector_launch_authorization.json` until the prelaunch gate passes and the user gives a separate explicit collector-launch approval.

Price/PnL research remains unauthorized.
