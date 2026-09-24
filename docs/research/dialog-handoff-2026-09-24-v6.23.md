# SC001 / B15-P1 — dialog handoff v6.23 — 2026-09-24

Current state:

`B15P1_LIVE_SOURCE_CAPABILITY_V021_PASS_PRELAUNCH_GATE_NEXT`

## Live capability PASS

The user executed the verified safe-staging wrapper:

`sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.2.sh`

Observed:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_V021_PASS`

Snapshot SHA256:

`14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc`

Coverage:
- Bybit = 192/192;
- OKX = 192/192;
- both venues = 192/192.

Source rows:
- Bybit = 1036;
- OKX = 591.

Permissions:
- Bybit readOnly = 1;
- Bybit Withdraw permission absent;
- Bybit IP-bound = true;
- OKX permission = read_only;
- OKX IP-bound = true.

Fee probe:
- BTC;
- PASS.

Security:
- price endpoints called = false;
- order/transfer/withdraw endpoints called = false;
- collector_launch_authorized = false;
- price/PnL = false;
- live_execution_authorized = false;
- security_firewall = PASS.

Live result document:

`docs/research/sc001-b15-p1-live-source-capability-revalidation-v0.2.1-result-v0.1.json`

## Research meaning

API/source compatibility is now validated live for the entire frozen admitted universe.

No inference about profitability is made from this PASS.

## Next gate

Prepare a separate systemd + launch-readiness preflight for collector v0.1.3.

Before collector start it must verify:
- exact runner/freeze/service hashes;
- live capability snapshot binding;
- service user/path/env/firewall semantics;
- launch authorization fail-closed semantics;
- no price/PnL endpoints;
- storage/heartbeat/restart safeguards;
- collector remains stopped before explicit launch approval.

Do not start or enable the collector automatically.

Do not create the active runtime launch-authorization file until explicit user approval after prelaunch PASS.

## Next state

`PREPARE_B15P1_COLLECTOR_SYSTEMD_AND_LAUNCH_READINESS_PREFLIGHT`
