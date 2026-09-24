# SC001 Current Roadmap and Stop Rules v5.74

Date: 2026-09-24  
Status: **B15-P1 LIVE READ-ONLY CAPABILITY RETRY v0.2.1 READY / EXPLICIT APPROVAL REQUIRED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.73.md`

## Combined offline validation

Full PASS remains frozen:

- bundle: `bundle_20260924T163807Z_a5599568`
- job: `job_20260924T170906Z_810905df`
- status: `B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_PASS`
- collector v0.1.3: 28/28 mandatory + 8/8 extra PASS
- capability v0.2.1: compile+self-test PASS
- exchange calls: false
- credentials used: false
- collector launch: false
- price/PnL: false

## Live-wrapper offline preflight

Sealed bundle:

`bundle_20260924T171540Z_9f83d965`

Job:

`job_20260924T172500Z_45b04565`

Result:

`B15P1_SOURCE_CAPABILITY_LIVE_WRAPPER_V02_OFFLINE_PREFLIGHT_PASS`

Verified:
- package integrity PASS;
- exit code 0;
- bash syntax PASS;
- two embedded Python blocks compile;
- all 10 staged dependencies match pinned SHA256;
- exactly one capability `--mode run` invocation;
- no direct network client commands in wrapper;
- no systemd service start/enable/restart;
- no collector launch-authorization creation;
- no plaintext exchange credential variable names;
- no GitHub Control permission mutation;
- `rm -rf` scoped only to the staging root;
- credentials unavailable in preflight;
- exchange calls performed = false;
- collector launch = false;
- price/PnL = false;
- live execution = false.

Preflight result manifest SHA256:

`192df55653161fe88d27e49eed03b7238dc617917f2074407e659a8a8ff66f70`

Result document SHA256 will be frozen in the next commit.

## Live wrapper candidate

Path:

`scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.2.sh`

SHA256:

`0bc379933be07fb7b31e2efe4a2f06b4b7b99ad2fdc4db403dbffbe63ebc556e`

Target:
- capability v0.2.1;
- collector v0.1.3;
- exact frozen identity/route universe;
- read-only/non-price endpoints only.

The wrapper:
- preserves GitHub Control isolation;
- verifies source and staged dependency SHA256;
- requires credential env mode 0600;
- stages only 10 exact non-secret dependencies;
- rechecks successful combined offline prerequisite;
- runs probe as `botmarket`;
- writes a secret-free capability snapshot;
- revalidates anchors, permissions and security after completion;
- does not start the collector;
- does not create launch authorization;
- does not request price endpoints, orders, transfers or withdrawals.

## Stop rule

The next action is a real authenticated read-only capability revalidation against Bybit/OKX.

Do not execute it without a separate explicit user approval.

Do not reuse live wrapper v0.1.

Collector launch remains a later independent gate even if the live capability retry passes.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P1_LIVE_READ_ONLY_CAPABILITY_REVALIDATION_V021`
