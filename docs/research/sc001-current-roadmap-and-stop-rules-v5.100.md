# SC001 Current Roadmap and Stop Rules v5.100

Date: 2026-09-26  
Status: **B15-P1 controlled collector v0.1.4 launch v0.2.0 offline preflight sealed / awaiting approval**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.99.md`

## Current baseline

Recovery v0.1.2 host PASS established:
- archived evidence files = 134;
- active collector state/manifest absent;
- stable service inactive/not-found;
- runtime unit absent;
- runtime authorization absent.

Current capability v0.2.2 snapshot SHA256:

`01cfa63b6001ec972c4ed87daba5bbd9fba932233b9e8323a49a6a5355e89647`

Collector v0.1.4 remains 32/32 offline PASS.

## New launch authorization candidate v0.2

Candidate remains top-level non-authorizing.

Canonical runtime payload SHA256:

`7c6a0296dc47f91a47d4747a0d29174338599a805b797427f19aa2e0c9d3b01c`

It binds exactly to:
- runner v0.1.4;
- implementation freeze v0.1.4;
- current capability snapshot v0.2.2;
- service v0.1.4;
- price-economic research = false;
- live execution = false.

## Final launch wrapper v0.2.0

Path:

`scripts/research/run-b15p1-final-collector-deployment-launch-v0.2.0.sh`

SHA256:

`25387c527fcd77b59bac96a1c88316029e093edc99848e60842e6436d90424ad`

Structural audit:
- source dependencies = 23;
- runtime deploy files = 19;
- embedded Python blocks = 6;
- one staged collector self-test;
- zero direct collector --mode run;
- one systemctl enable;
- one systemctl start;
- one set +e confined to rollback;
- no stale v0.1.3 runtime path except defensive pgrep;
- transactional runtime-file rollback ledger;
- atomic runtime/service/authorization replacement;
- runtime prestart authorization validation;
- tri-state initial verifier;
- zero restart first-start contract.

Before mutation it revalidates:
- collector v0.1.4 32/32 offline PASS;
- current capability v0.2.2 result;
- exact current snapshot SHA;
- 1007/1007 Bybit sentinel mapping;
- recovery v0.1.2 host result;
- exact recovery-report SHA;
- all 134 archived files by size and SHA;
- safe-summary binding;
- price/PnL/live-execution firewalls.

## Sealed offline-preflight bundle

- bundle ID: `bundle_20260926T122142Z_bf51bc5e`
- SHA256: `b334eb37fc66bc6f97a85313a6b53a4b156c1e882a014c593b3ea501021b005c`
- approval code: `BM-B334EB37FC66`
- files: 28
- bytes: 381388
- runtime: offline-research-v1
- inputs: none

The bundle has NOT been run.

## Offline gate contents

The preflight will:
- verify exact 23-source/19-deploy closure;
- compile Bash and all 6 Python heredocs;
- call the actual collector v0.1.4 authorization validator on candidate v0.2;
- verify wrapper snapshot/auth/recovery anchors;
- verify rollback/systemd ordering;
- run synthetic NOT_READY/PASS/HARD_FAIL poll/raw-object fixtures;
- keep credentials/network/systemd/start/price/PnL completely closed.

## Stop rule

Do not run the real launch wrapper v0.2.0 until this offline gate returns full PASS and the user separately approves the real host launch.

## Next state

`RUN_FINAL_LAUNCH_V020_OFFLINE_PREFLIGHT_AFTER_EXPLICIT_APPROVAL`
