# SC001 Current Roadmap and Stop Rules v5.77

Date: 2026-09-25  
Status: **B15-P1 COLLECTOR PRELAUNCH READINESS OFFLINE PASS / HOST DEPLOYMENT-READINESS NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.76.md`

## Collector prelaunch readiness gate

Bundle:

`bundle_20260924T180410Z_997301cb`

Job:

`job_20260925T075008Z_6317d13c`

Result:

`B15P1_COLLECTOR_PRELAUNCH_READINESS_OFFLINE_PASS`

Package integrity = true.  
Exit code = 0.

Manifest SHA256:

`532f9cc7b1af9495e42e4c23f2ce633794e7b1c58c56d7320c0a06cf3d5218de`

## Verified gates

Collector/foundation:
- full collector v0.1.3 freeze handshake PASS;
- frozen mapping invariants PASS;
- base assets = 146;
- overlay assets = 46;
- asset common representations = 207;
- quote common representations = 12;
- quote one-sided representations = 14;
- implementation contract mandatory tests = 28;
- no-price endpoint static guard PASS.

Live prerequisite chain:
- combined offline PASS;
- live-wrapper offline preflight PASS;
- live capability v0.2.1 PASS;
- live snapshot SHA256 = `14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc`;
- full both-venue coverage = 192 assets.

Systemd contract:
- 20 required service fragments PASS;
- exactly one ExecStart;
- stable runtime unit = `sc001-b15p1-transferability.service`;
- status helper unit-name alignment PASS;
- no shell/GitHub Control permission mutation.

Collector gate ordering:
1. require_freeze;
2. load mapping;
3. mapping invariants;
4. load capability;
5. require launch authorization;
6. require credentials;
7. install IPv4-only transport;
8. create directories;
9. write collector manifest;
10. only later activate worker threads/network poll execution.

Thus launch authorization is fail-closed before credentials/network/writes.

## Launch-authorization mutation audit

The non-active candidate top-level object was rejected.

The nested proposed runtime payload was accepted only when all exact anchors matched.

Eight negative mutations all failed closed:
- wrong status;
- wrong token;
- runner SHA mismatch;
- implementation-freeze SHA mismatch;
- capability snapshot SHA mismatch;
- service SHA mismatch;
- price firewall enabled;
- live-execution firewall enabled.

Runtime authorization remains NOT created.

## Safety

During this gate:
- credentials available = false;
- exchange calls = false;
- collector start = false;
- systemd mutation = false;
- runtime authorization creation = false;
- price/PnL = false;
- live execution = false.

## Next gate

Prepare a separate **host systemd deployment-readiness wrapper**.

It must verify the actual VPS before any collector deployment/start, including:
- live capability snapshot bytes still hash to `14341c…`;
- credential env remains mode 0600 and readable only as intended;
- active runtime launch authorization remains absent;
- stable collector service is inactive and not enabled;
- exact versioned runner/library/freeze/service files can be staged and verified;
- systemd unit syntax/runtime paths are valid;
- collector self-test can run from exact staged bytes without network calls;
- no service start/enable occurs.

Only after host deployment-readiness PASS may we prepare the final deployment/authorization/start gate.

## Stop rule

Do not start or enable the collector.

Do not create `collector_launch_authorization.json`.

Do not enable price/PnL research.

## Next state

`PREPARE_B15P1_COLLECTOR_HOST_SYSTEMD_DEPLOYMENT_READINESS_WRAPPER`
