# SC001 Current Roadmap and Stop Rules v5.76

Date: 2026-09-24  
Status: **B15-P1 COLLECTOR PRELAUNCH READINESS OFFLINE GATE SEALED / AWAITING APPROVAL**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.75.md`

## Completed prerequisite chain

### Combined offline adapter validation

PASS:
- collector v0.1.3: 28/28 mandatory + 8/8 extra;
- capability v0.2.1 compile+self-test PASS;
- no credentials/exchange calls/collector launch/price/PnL.

### Live wrapper offline preflight

PASS:
- bash syntax;
- embedded Python compile;
- exact dependency SHA closure;
- no direct network helper commands;
- no service mutation;
- no runtime launch authorization creation.

### Live authenticated source capability v0.2.1

PASS:
- snapshot SHA256: `14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc`;
- Bybit qualified: 192/192;
- OKX qualified: 192/192;
- both venues: 192/192;
- Bybit readOnly = 1;
- Bybit Withdraw permission absent;
- OKX permission = read_only;
- both keys IP-bound;
- security firewall = PASS;
- collector launch = false;
- price/PnL = false.

## New prelaunch readiness gate

Purpose:

Verify the exact collector v0.1.3 launch boundary before any host deployment/start.

The gate re-runs:
- collector full `require_freeze()` dependency handshake;
- frozen mapping invariants;
- no-price static endpoint guard;
- systemd candidate contract;
- stable runtime unit mapping:
  - versioned candidate: `sc001-b15p1-transferability-v0.1.3.service`;
  - stable runtime unit: `sc001-b15p1-transferability.service`;
- status-helper alignment;
- live capability result binding to snapshot SHA `14341c…`;
- collector launch authorization validator;
- negative mutation tests for wrong status/token/anchors and price/live-execution firewalls;
- AST gate ordering:
  capability -> launch authorization -> credentials/network;
- collector remains stopped.

## Launch authorization boundary

A non-active candidate exists:

`docs/research/sc001-b15-p1-collector-launch-authorization-candidate-v0.1.json`

Its top-level status is intentionally:

`CANDIDATE_NOT_ACTIVE`

Therefore it is not a valid runtime authorization.

The future runtime payload is nested only for offline validation and may not be materialized to:

`/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/collector_launch_authorization.json`

without a later separate explicit user approval.

## Sealed Runner bundle

- bundle ID: `bundle_20260924T180410Z_997301cb`
- SHA256: `e287545e7911aa160a12b0c0df89d84fb2f00fe15961704785e92291c3ebd370`
- approval code: `BM-E287545E7911`
- files: 26
- total bytes: 322419
- runtime: `offline-research-v1`
- inputs: none

This gate is fully offline and has NOT been run.

## Stop rule

Do not deploy/install/start/enable the collector yet.

Do not create the active runtime launch-authorization file.

After this offline gate PASS, the next step is a separate **host systemd deployment-readiness wrapper** that may verify/stage exact files and unit semantics while keeping the service inactive and disabled.

Collector start remains a later independent explicit approval.

## Next state

`RUN_B15P1_COLLECTOR_PRELAUNCH_READINESS_OFFLINE_AFTER_USER_APPROVAL`
