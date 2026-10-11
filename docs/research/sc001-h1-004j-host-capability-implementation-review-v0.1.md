# SC001-H1-004J — shared-cache capability implementation review v0.1

Status: **H1_CAPABILITY_STATIC_PACKAGE_PREPARED_REVIEW_REQUIRED**  
TASK_ID: `SC001-H1-004J`  
WORKER_ID: `H1_HISTORICAL_INDICATORS`  
Authorization: `T0_OFFLINE_ENGINEERING_PACKAGE_ONLY`  
Dispatch/current-main binding: `e1de40ede4f9126078cbd84cd87c85f234b2f458`

## Decision

A minimal additive patch package is technically defensible for review, but it is neither installed nor authorized for host use. The package keeps the existing Test Executor and adds a fail-closed shared-cache capability behind a root-owned grant. It does not create a grant, run a job, access market bytes, inspect the live host, or authorize T1.

The package is:

- `scripts/research/deploy_sc001_h1_shared_cache_capability_v0_1.py`
- `tests/research/test_sc001_h1_shared_cache_capability_v0_1.py`

Both files are proposals for a separately approved T3 action. They were not executed, compiled, installed, or smoke-tested because this task has zero execution and host-mutation budget.

## Verified current static mismatch

The current installer SHA-256 is
`0e9afe9b9a3e12beb7aa451a7608eda3ffa30a46ba9b07faf0a869bfda518968`.

Its installed contracts currently:

1. set `SC001_DATA_ROOT` to each job's `output/data`;
2. export `BM_TEST_NETWORK_PROFILE`, but not `SC001_NETWORK_PROFILE`;
3. grant systemd write access only to job output;
4. retain completed job output for seven days;
5. limit a job to 900 seconds and one concurrent job.

The frozen H1 acquisition entrypoint SHA-256 is
`1eb597e3186023540a5ab9929f433f7f5a81b9d587f10386cf2e3e55f625c760`.
It requires `SC001_NETWORK_PROFILE=public_research`, the exact resource acknowledgement, and a durable `SC001_DATA_ROOT`.

Frozen `RESOURCE_ID`:
`b97ffeefed4dd1b4caa771df734b59b5a6dc2b6a9ada3b3c9b8ce0c6de6319bf`.

## Proposed additive boundary

The only persistent root is:

`/var/lib/botmarket-test-executor/shared-data/sc001`

The deployer patches four installed artifacts only:

- root-owned Test Executor policy;
- sandboxed job runner;
- root-only launcher;
- MCP server manifest builder.

It does not patch the canonical installer source, acquisition source, collector, roadmap, governance, credentials, systemd service unit, or any market-data file. It creates the fixed shared directory hierarchy, a root-only grant directory, exact-hash backups, and an apply receipt only during a future approved `apply`.

Ordinary jobs retain role `NONE`. The launcher explicitly masks the shared root for those jobs. The server's new optional fields do not themselves grant access.

## Roles and enforcement

### `ACQUIRE_WRITE`

The launcher admits this role only when all of the following are bound by a non-expired root-owned grant:

- exact task ID and grant token;
- exact frozen `RESOURCE_ID`;
- exact acquisition entrypoint SHA-256;
- `public_research` network profile;
- explicit T3 approval reference;
- separate T1 task-authorization reference;
- deterministic reservation reference;
- disk-preflight reference;
- collector-isolation reference;
- timeout at most 900 seconds;
- single-dataset declaration at most 5 GiB;
- peak workspace increment at most 15 GiB.

Only the exact resource directory and its exact quarantine directory are added to the transient job's systemd `ReadWritePaths`. There is no arbitrary host path, shell, sudo, new service, or collector path.

### `CONSUME_READ_ONLY`

A root-owned grant must additionally name the verified-dataset record and the task-specific evidence-access receipt. The fixed shared root is added read-only. Physical byte presence never grants evidence access.

### `SMOKE_WRITE` / `SMOKE_READ_ONLY`

These roles are offline-only and restricted to:

`SC001_DATA_ROOT/_capability_smoke/<fixed-token>`

No market namespace is mounted. The same namespace token is used for two sequential jobs; between them, an approved root action must replace the grant from write to read-only. The package never creates that grant automatically.

## Root-owned grant requirement

A grant is a separately reviewed JSON file under:

`/etc/botmarket-test-executor/sc001-shared-cache-grants/<token>.json`

Required base fields are:

- schema `sc001.shared_cache_grant.v0.1`;
- `status=AUTHORIZED`;
- task ID, role, resource ID, entrypoint SHA-256 and network profile;
- expiration time;
- maximum timeout, single-dataset bytes and peak increment;
- exact T3 approval reference.

Acquisition grants also require T1 authorization, reservation, disk-preflight, and collector-isolation references. Consumer grants require verified-dataset and evidence-access references.

The deployer intentionally has no command that installs a grant. Therefore deployment alone cannot turn tool presence into acquisition authority.

## Exact-hash plan/apply/rollback

A future approved operator must first run read-only `plan`. It:

1. verifies the canonical installer source hash;
2. checks every expected source anchor exactly once;
3. records SHA-256 and byte length for all four installed files;
4. constructs deterministic target bytes in memory;
5. returns a canonical plan SHA-256.

`apply` requires all of:

- root;
- exact acknowledgement `SC001-H1-004J-T3-HOST-MUTATION`;
- a non-empty exact approval reference;
- the exact previously reviewed plan SHA-256;
- unchanged current-file hashes.

It writes hash-addressed backups before stopping the service, atomically replaces only the four files, creates the fixed directories, restarts the existing service, and records target hashes. It creates zero grants.

`rollback` requires a separate exact T3 acknowledgement and approval reference. It refuses if any installed target hash or backup hash differs from the receipt, restores only the four backed-up files, and restarts the service. It deliberately does not delete the shared root, quarantine, grants, or any verified cache.

Operational review must consider that an unexpected systemd/start failure during apply can leave the existing service stopped; rollback remains available from the saved, hash-verified backup. This is one reason human T3 supervision is mandatory.

## Prospective two-job offline smoke

The focused test file has two future entrypoint phases:

1. writer: requires both network-profile variables to equal `offline`, exact `SMOKE_WRITE`, exact synthetic root, and separation from job output; proves a write outside the namespace is denied; writes a random-namespace sentinel through `.part` plus atomic rename and records its SHA-256;
2. reader: runs as a distinct job after the root-owned grant is changed to `SMOKE_READ_ONLY`; verifies the persisted sentinel SHA-256 and proves a new write inside the namespace is denied.

Acceptance also requires the pre-existing launcher/privilege/filesystem self-tests to remain PASS and the ordinary `NONE` role to receive `InaccessiblePaths` for the shared root. Cleanup may remove only the synthetic smoke namespace under separate approval. No market files or collector paths are involved.

## Hard remaining gates

This package cannot authorize H1 acquisition.

- Frozen coverage is 312 remote objects and permits up to 10 GiB total network bytes.
- Active delegated policy caps one dataset at 5 GiB and peak workspace increment at 15 GiB.
- Each job remains limited to 900 seconds.
- At least 25 GiB free before start remains binding, together with the shared-resource reserve formula.
- A protected collector on the same contention domain requires separately evidenced `RESOURCE_ISOLATION_PASS`.
- A deterministic GitHub reservation is required before any request.
- No current authorization permits creating an acquisition grant.

Because the frozen resource may exceed the 5 GiB single-dataset cap and no evidence proves completion inside 900 seconds, the next acquisition-facing work, if Strategy Manager still finds it worthwhile, is a separately frozen source-preserving chunk/resume resource contract. It may not change source, symbols, months, total request/byte caps, `RESOURCE_ID`, or evidence semantics.

## Economics and deprioritization

The 12-asset H1 panel is lexicographically determined and contains mostly speculative/small-cap instruments. Expected research value should not be inflated merely because infrastructure can be built. Reuse by an X1 BTC/ETH anchor is not yet proven. Strategy Manager should compare the supervised T3 installation and maintenance cost with a defer decision before spending host-change effort; this package creates an option, not a presumption to continue.

## Static review conclusion

`H1_CAPABILITY_STATIC_PACKAGE_PREPARED_REVIEW_REQUIRED`

The design is additive, fixed-path, hash-guarded, reversible, grant-gated, and preserves ordinary-job isolation. Programmer/Strategy Manager review is required before any T3 approval. No claim is made that the package is installed, executable on the live host, or sufficient for T1 acquisition.

`NO_ROADMAP_CHANGE_REQUIRED`  
`EVIDENCE_ACCESS_COUNT: 0`  
`MARKET_BODY_ACCESSED: false`  
`PROTECTED_OUTCOME_ACCESSED: false`  
`NETWORK_RUNS: 0`  
`EXECUTIONS: 0`  
`HOST_MUTATIONS: 0`
