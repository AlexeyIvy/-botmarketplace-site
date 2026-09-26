# SC001 Current Roadmap and Stop Rules v5.101

Date: 2026-09-26  
Status: **B15-P1 final launch v0.2.0 offline preflight PASS / real VPS launch next**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.100.md`

## Confirmed baseline

Recovery v0.1.2 host PASS remains the required clean baseline:
- archived source-invalid evidence files = 134;
- active collector state/manifest absent;
- stable service inactive/not-found;
- runtime unit absent;
- runtime authorization absent.

Current capability v0.2.2 snapshot SHA256:

`01cfa63b6001ec972c4ed87daba5bbd9fba932233b9e8323a49a6a5355e89647`

Collector v0.1.4 remains 32/32 offline PASS.

Bybit sentinel compatibility remains confirmed:
- real withdrawMax=-1 rows = 1007;
- normalized UNLIMITED rows = 1007.

Qualified assets remain:
- Bybit = 192;
- OKX = 192;
- both venues = 192.

## Final launch wrapper v0.2.0

Path:

`scripts/research/run-b15p1-final-collector-deployment-launch-v0.2.0.sh`

SHA256:

`25387c527fcd77b59bac96a1c88316029e093edc99848e60842e6436d90424ad`

Canonical runtime authorization payload SHA256:

`7c6a0296dc47f91a47d4747a0d29174338599a805b797427f19aa2e0c9d3b01c`

## Offline preflight result

Exact sealed bundle:
- bundle ID: `bundle_20260926T122142Z_bf51bc5e`
- bundle SHA256: `b334eb37fc66bc6f97a85313a6b53a4b156c1e882a014c593b3ea501021b005c`
- approval code: `BM-B334EB37FC66`

Executed Runner job:

`job_20260926T125951Z_ec46c508`

Result:

`B15P1_FINAL_LAUNCH_V020_OFFLINE_PREFLIGHT_PASS`

Evidence:
- package integrity = PASS;
- exit code = 0;
- stderr empty;
- source dependencies = 23;
- runtime deploy dependencies = 19;
- embedded Python blocks = 6 and compile PASS;
- Bash syntax PASS;
- collector v0.1.4 authorization validator PASS;
- ERR-trap fixture PASS;
- rollback-only `set +e` PASS;
- tri-state fixtures PASS: NOT_READY=10, PASS=0, HARD_FAIL=20;
- forbidden network/mutation patterns absent;
- collector start performed = false;
- credentials available = false;
- exchange calls performed = false;
- systemd mutation performed = false;
- runtime authorization created = false;
- price/PnL/live execution remain closed.

Result artifact:
`docs/research/sc001-b15-p1-final-launch-v0.2.0-offline-preflight-result-v0.1.json`

## Read-only VPS source check

The exposed B15 inventory root still contains run `20260920T210446Z`.

Its `run_manifest.json` reports:
- status = `B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_PASS`;
- Bybit readOnly = 1;
- OKX permission = read_only;
- price endpoints called = false;
- order endpoints called = false;
- withdraw endpoints called = false;
- transfer endpoints called = false;
- secret values printed = false.

This is supporting read-only evidence only. The real launch wrapper still revalidates the actual host runtime state fail-closed immediately before mutation.

## Real launch contract

The next operation is the real host execution of the exact v0.2.0 wrapper.

The wrapper itself revalidates before mutation:
- exact capability snapshot SHA;
- recovery report and recovery host evidence;
- credentials file ownership/mode without printing secrets;
- absence of runtime authorization/state/manifest/launch report;
- absence of v0.1.3/v0.1.4 collector processes;
- stable service inactive/not-found;
- runtime unit absent;
- storage capacity;
- all 23 source hashes;
- staged collector v0.1.4 self-test and authorization validation.

Only after those checks PASS does it atomically deploy the 19 runtime files, install the exact service unit and authorization, start the service once, and verify:
- service active/enabled/running;
- zero restarts;
- >=2 completed 15-second polls;
- >=1 fully valid Bybit+OKX poll;
- fresh heartbeat;
- monotonic 15-second slot phase;
- raw-object SHA integrity;
- price/PnL firewalls closed.

On any hard failure it executes transactional rollback and returns REVIEW.

## Stop rules

1. Do not use old final launch v0.1/v0.1.1 or recovery v0.1/v0.1.1.
2. Do not alter frozen research semantics, 15-second cadence, or price/PnL/live-execution firewalls without demonstrated necessity.
3. Do not rescue-tune merely to obtain a PASS.
4. If real v0.2.0 launch returns PASS, freeze collector infrastructure except for demonstrated correctness/data-integrity/safety defects.
5. After host PASS, move the main effort from collector engineering to accumulation and analysis of B15-P1 research data.

## Next state

`RUN_REAL_FINAL_LAUNCH_V020_ON_VPS`
