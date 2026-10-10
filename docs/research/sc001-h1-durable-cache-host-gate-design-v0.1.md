# SC001 H1 durable shared-cache host gate design v0.1

Status: **T3_HOST_CAPABILITY_REQUIRED / NO T1 AUTHORIZATION**  
TASK_ID: `SC001-H1-004I`  
WORKER_ID: `H1_HISTORICAL_INDICATORS`  
Dispatch main: `e1de40ede4f9126078cbd84cd87c85f234b2f458`  
Architecture: `0.3`

## Scope and verified identities

This is a pre-outcome T0 design only. It does not install, execute, download, inspect a market body, access protected evidence, or authorize T1.

Verified current-main SHA-256 identities:

- H1 acquisition implementation: `1eb597e3186023540a5ab9929f433f7f5a81b9d587f10386cf2e3e55f625c760`
- Test Executor installer: `0e9afe9b9a3e12beb7aa451a7608eda3ffa30a46ba9b07faf0a869bfda518968`
- frozen H1 bodyset: `c0798987d86dfb32fdb38e4d7ca525d68850bf41391a0c15e7fa7ed91de2075a`
- frozen `RESOURCE_ID`: `b97ffeefed4dd1b4caa771df734b59b5a6dc2b6a9ada3b3c9b8ce0c6de6319bf`

The frozen scope remains 12 symbols × 13 months, 156 ZIP archives plus 156 checksum sidecars, at most 1,248 requests and 10 GiB of network bytes. No source, symbol, month, horizon, feature, or evidence-role change is proposed.

## Known verified static blockers

1. The current launcher contract gives each job `SC001_DATA_ROOT=BM_TEST_OUTPUT_DIR/data`. That path is job-local, while the shared-resource policy requires one persistent physical cache reusable across H1 and X1.
2. The launcher sets `BM_TEST_NETWORK_PROFILE`; the frozen acquisition implementation requires `SC001_NETWORK_PROFILE=public_research` before `--apply`.
3. The job sandbox permits writes only to its job output. Completed output is retained for seven days, which is not a durable immutable shared-cache contract.
4. The executor maximum is 900 seconds and one concurrent job. No current evidence proves that 312 remote objects, up to 10 GiB plus checksum and body validation, complete in one job.
5. Live disk headroom and protected-collector isolation are unproven. Static configuration must not be represented as deployed runtime evidence.
6. The referenced delegated authorization policy v0.2 is still marked proposed/pending ratification and its default single-dataset cap is 5 GiB. It cannot be used to infer authorization for this frozen resource of up to 10 GiB.

## One minimum viable least-privilege capability

Reuse the existing Test Executor; add no service and no alternate execution plane.

A separately approved T3 installation package may add exactly one persistent SC001 root beneath the existing Test Executor state:

`/var/lib/botmarket-test-executor/shared-data/sc001`

This host path becomes the exact `SC001_DATA_ROOT`. The frozen logical archive location is:

`SC001_DATA_ROOT/_raw_cache/binance/b97ffeefed4dd1b4caa771df734b59b5a6dc2b6a9ada3b3c9b8ce0c6de6319bf/<source_basename>`

Required executor changes are limited to:

- a root-owned policy allowlist binding the exact resource ID, root path, authorized implementation SHA-256, and access mode;
- a job-manifest capability field that fails closed unless the requested resource, entrypoint identity, network profile, and mode match that allowlist;
- bind the persistent root into an eligible job only; ordinary jobs retain the existing job-output-only write boundary;
- export both `BM_TEST_NETWORK_PROFILE` and `SC001_NETWORK_PROFILE` from the selected executor profile;
- set `SC001_DATA_ROOT` to the persistent root only for an eligible shared-resource job;
- permit `ACQUIRE_WRITE` only for a separately authorized acquisition reservation; permit later consumers only `CONSUME_READ_ONLY`;
- preserve all existing credential, network-isolation, package-read-only, rate, memory, CPU, timeout, and no-arbitrary-shell controls.

No generic host path, arbitrary bind mount, broad VPS reader, new root shell, or collector access is part of this option.

## Persistence, locking, immutability, and evidence separation

Before any later network request, the exact resource must have its own deterministic GitHub reservation record. The reservation is the cross-worker lock; the executor remains single-job.

During an authorized acquisition:

- only deterministic `.part` files under the exact resource directory may be written;
- only the reservation owner may resume them;
- checksum or identity mismatch is quarantined, never overwritten;
- a final basename is created only by atomic replacement after its checksum and frozen body-integrity checks pass;
- an existing final basename is never silently replaced;
- after the verified dataset receipt, all later task mounts are read-only.

Physical presence grants no evidence access. Every H1 or X1 task still requires its own access receipt, exact interval/assets, evidence role, and contamination classification. No strategy-specific raw copy is allowed.

## Disk, peak, collector, rate, and 900-second gates

Before T3 installation and again before any later T1 acquisition, a bounded host preflight must record the target filesystem total/free bytes and calculate:

`ESTIMATED_PEAK_INCREMENT = remaining download + largest active .part/validation workspace + expected derived output (zero for acquisition-only) + explicit safety margin`

The job may start only if:

`free_bytes - ESTIMATED_PEAK_INCREMENT >= max(10 GiB, 15% of filesystem total)`

and the frozen 25 GiB minimum-before-start is also satisfied. Neither reserve may be lowered. Storage allocation outside the stated root, or capacity expansion with cost, requires separate user approval.

The bodyset is HEAVY. If the persistent root shares a host or contention domain with a protected collector, acquisition remains deferred unless Strategy Manager has a separately evidenced `RESOURCE_ISOLATION_PASS`; this design does not inspect or restart a collector.

The 900-second limit and existing rate limits remain unchanged. If an exact pre-run bound cannot prove that all 312 objects and validation finish in one job, T1 must not start. The only next design action is a separately frozen T0 source-preserving chunk/resume review using the same ordered manifest, `RESOURCE_ID`, cumulative request/byte caps, reservation, and integrity rules. It may not rewrite coverage, budgets, or evidence semantics.

## Exact T3 human approval boundary

Explicit user approval is required before any of these actions:

1. create or permission the persistent host directory;
2. modify installer, policy, server, launcher, job manifest, systemd bind/write paths, or environment mapping;
3. redeploy/restart the Test Executor to activate those changes;
4. inspect live host mount/disk facts or establish collector isolation;
5. run the proposed offline host-capability smoke.

Approval of that package would authorize only the named host/runtime preparation and smoke. It would not authorize archive acquisition, market-body access, T1, protected evidence, collector mutation/restart, a larger disk budget, a source change, or trading.

## Prospective offline smoke and rollback

One acceptance procedure, executed only under the separate T3 approval, consists of two sequential offline phases under a synthetic non-market namespace:

1. writer phase verifies both network-profile variables equal `offline`, confirms `SC001_DATA_ROOT` is the approved persistent root and not job output, writes and atomically renames a random sentinel, and proves writes outside the synthetic namespace are denied;
2. after removal of the first job output, verifier phase reads the sentinel from a fresh job, proves persistence across jobs, proves the repository package remains read-only, then removes only the synthetic sentinel.

Acceptance requires exact path containment, no network, no market files, no credentials, no collector paths, and PASS of existing sandbox/privilege-boundary self-tests.

Rollback: stop the service; restore the installer-created backup of server/launcher/policy/unit/environment; remove only the synthetic smoke namespace; restart and re-run existing boundary self-tests. Never delete a verified cache or quarantine directory during rollback.

## Technical decision

**T3_HOST_CAPABILITY_REQUIRED.**

The existing Test Executor can remain the execution plane, but the minimum safe option requires host directory, permissions, sandbox bind/write policy, environment, and deployment changes. Those are not authorized by T0. Even after a future T3 capability PASS, T1 remains unapproved until disk/collector gates, the 900-second envelope (or a separately frozen chunk design), reservation, and the applicable data-size authorization are resolved.

`NO_ROADMAP_CHANGE_REQUIRED`  
`EVIDENCE_ACCESS_COUNT: 0`  
`MARKET_BODY_ACCESSED: false`  
`PROTECTED_OUTCOME_ACCESSED: false`
