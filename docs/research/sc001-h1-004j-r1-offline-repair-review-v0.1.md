# SC001-H1-004J-R1: bounded offline safety repair

Status: OFFLINE_SAFETY_REPAIR_VALIDATION_PASS. Final independent and Strategy acceptance are recorded in the result manifest. H1 remains BLOCKED.

## Authorization and immutable lineage

This is one user-authorized offline repair cycle, not automatic shared-library repair or host authorization. Research Strategy ratified the exact five-file contract before executable edits or tests. The four-hour window is 2026-10-13 10:44–14:44 UTC. No second changed-code execution cycle is allowed.

- Main: `e1de40ede4f9126078cbd84cd87c85f234b2f458`
- Unmerged repair base, PR #470: `422af98fdce33499e3f9c067fecd0c012a84ab76`
- Parent design, PR #467: `7b4cbe7fa3e021aac5ae9ce60f2a1bb2e78bb81c`
- Freeze commit, persisted/read back before edits: `27e90b67a9e51dfa318114c59513a42b67f5b667`
- Freeze SHA256: `ddfdd1946de45f39bcc85b2a9528b482d566f35db71bb0c2a52baab97c5d9315`
- [Original blocking review](https://github.com/AlexeyIvy/-botmarketplace-site/pull/470#issuecomment-6106787307)

Only five new additive files are permitted: the task freeze, v0.2 deployer, v0.2 tests, this report, and the final result manifest. All original files and the v0.1 package are preserved. The new draft has no READY trigger, merge or lifecycle rights.

## Diagnosis and coherent repair set

The predecessor was statically reviewed, not installed or tested. Three blocking implementation defects have deterministic root causes:

1. The only apply receipt was written after service start. A start failure made the documented rollback entrypoint unusable. The adjacent reload failure, interrupted target replacement, receipt persistence and backup validation paths were inspected together.
2. The generated launcher resolved the grant pathname before checking whether it was a symlink, erasing the leaf-symlink evidence. It also omitted root ownership and group/world-writability checks. The permission check and subsequent open could otherwise race.
3. Dataset and peak cap fields defaulted to zero and were checked only for an excessive upper bound. Integer coercion also admitted invalid representations. The shared grant path serves every privileged cache role.

No source, evidence role, symbol, horizon, threshold or research formula was changed. No data or protected outcome was accessed.

## Actual repaired paths

### Durable recovery

The additive v0.2 deployer's actual `apply` function builds an exact-hash plan from the frozen installer-derived artifacts, writes all backups and the plan durably, and then writes a PREPARED receipt before the first service or target mutation. Only a successful start advances it to APPLIED. Authority directories must satisfy the same ownership/non-writability assumptions before apply can mutate service or targets. Atomic writes set ownership before the final mode, then flush their file and parent directory. Failure while writing a newly-created temporary file cleans up that owned temporary file; a preexisting temporary file is refused and preserved.

The actual `rollback` function now requires the externally reviewed expected plan SHA256 as well as the receipt path and separate exact T3 acknowledgement/reference. It checks the receipt/task/schema/state, exact receipt/backup paths, canonical plan hash, exact four-file allowlist, root-owned non-group/world-writable authority artifacts, every current before-or-after target hash, and every backup hash before any service action or restore. It restores the original bytes and recorded mode/uid/gid. Original-or-patched hashes permit recovery from the tested caught partial-apply failures while refusing unknown bytes. Every preexisting target temporary-file collision is rejected before the first apply/rollback mutation. An uncatchable process kill that strands a temporary file still requires separate operator handling; crash recovery is not claimed. Shared cache and grants are preserved.

This changes the future rollback CLI: `--expected-plan-sha256` is mandatory. v0.1 receipts are not silently accepted by v0.2. No installer CLI or real service command was invoked during this repair.

### Grant descriptor and caps

The actual generated launcher keeps the unresolved grant leaf, pins a nonsymlink grant directory descriptor, checks its root ownership and write bits, then opens the token-named leaf relative to that descriptor with O_NOFOLLOW and O_NONBLOCK. It checks regular-file type, root ownership, and absence of either group or world write permission through fstat, and reads JSON from that same descriptor. Bounded non-object/malformed payloads fail closed before any subprocess launch. Replacing the pathname after open cannot change the checked descriptor's content.

All three grant caps are mandatory exact JSON integers, excluding booleans, strings and floats. Bounds are inclusive: timeout 1–900 seconds, dataset 1–5 GiB, peak increment 1–15 GiB. Requested timeout must not exceed the grant timeout. The existing requested-timeout coercion in the base launcher/server was not broadened into this repair; strict typing is claimed for grant caps, not all preexisting inputs.

## Offline validation boundary

The harness parses exact frozen installer heredocs as text and applies the real policy/runner/launcher/server patchers. It never runs the shell installer. Installer fixtures use real temporary byte I/O and the real apply/rollback functions, with root identity, service subprocesses and every chmod/chown/fchmod/fchown syscall mocked. Generated launcher tests execute its actual code with only five fixed path constants redirected to temporary fixtures; grant validation, role checks and sandbox-command construction remain unchanged. Subprocess creation and sockets are blocked or explicitly mocked. Root ownership/mode values are synthetic; no host permissions were changed.

Intended coverage includes failed start/reload/stop, partial apply, initial/final receipt-write failure, byte-identical recovery, missing/tampered receipt/plan/backups/targets, stale temp files, hostile tokens, in-directory/outside/dangling symlinks, symlinked grant directory, FIFO/nonregular grants, individual unsafe uid/write-bit cases, descriptor replacement, every cap's missing/invalid/boundary cases, requested-timeout limits, ordinary NONE isolation, read-only roles, acquisition binding refusal, and preserved scope/expiry/network gates.

Validation completed on 2026-10-13 at 11:03 UTC using Python 3.12.14:

- Deployer and tests syntax/compile: PASS.
- Frozen task and pre-reviewed implementation identity checks: PASS.
- Targeted regressions: 9 tests PASS.
- Full task-local synthetic preflight: 51 tests PASS.
- Separate isolated Python process with a fresh temporary root: the same 51 tests PASS.
- Exact source/test hashes before and after validation: unchanged.
- Temporary fixture cleanup, artifact size limits and output firewall: PASS; no research outputs emitted.
- One repaired implementation identity executed; one authorized repair cycle consumed. No failed test or changed-code retry occurred.

Commands: `python -I -B tests/research/test_sc001_h1_shared_cache_capability_v0_2.py` for the full suite, repeated in a separate process with a fresh TMPDIR. The targeted run names the nine rollback/grant/cap regression methods. The synthetic suite also compiles the actual generated runner, launcher and server and parses patched policy.

Exact SHA256 identities:

- v0.1 source preserved: `4fd60e29f4baaeeb417518ff659585c60e08f6145ac63256fdb2f27122a6e687`
- v0.1 tests preserved: `4d7d4a4172868f98ef5669fa6f12f3df43d6d199eeef3686be91b0b86532d6be`
- v0.2 deployer: `1149a73122cd9baa2149493cc80e01f145ecab0b5c1823aed52f063223270aab`
- v0.2 tests: `79047512ee6dda156f195a81e7b27a0078156f7d4c3f33628910f3388f09d5f4`
- Frozen canonical installer: `0e9afe9b9a3e12beb7aa451a7608eda3ffa30a46ba9b07faf0a869bfda518968`
- Static log: `31b5747a453ae8549418e6d9a430f9168142120275bf75d88fd8b54af5e572ee`
- Targeted log: `3adfbe6145d74e768da1455c968b8c4177cae703a8c498e8b2b8cd08412e8294`
- Full log: `af5eacab0b1c7e5279d24522a99550da16eed3cec2b30fc6e8f62e7959de42ca`
- Clean repeat log: `6f19b8163e2c9bdbcb081b3177da0943f39bcfab6684dae0addb4c36cf59fba2`

A separate reviewer inspected actual implementation and fixture paths before execution. Its static findings were consolidated before the sole validation cycle: authority-directory trust symmetry, ownership-before-mode ordering, receipt-specific permission negatives, missing-artifact cases, and atomic-write failure/temp-collision recovery. No production assertion was weakened. Final read-only adversarial review uses these same implementation identities and captured logs; the manifest records its verdict and the actual strategist's separate narrow acceptance.

## Remaining gates and limits

This is only an offline control-plane safety repair. It does not demonstrate installed service behavior, live root permissions, kernel/systemd sandbox isolation, filesystem durability under power loss, successful acquisition, or research value. Real host/T3 review remains separate. No actual grant is created or activated. No live smoke, VPS/Runner/Test Executor access, dataset or protected outcome access, merge or successor dispatch occurs.

The exact RESOURCE_ID, acquisition SHA256, 900-second job limit, 5 GiB dataset cap, 15 GiB peak increment and 25 GiB free-start gate remain unchanged. The frozen prospective resource's budget/900-second feasibility and H1's limited economic value remain unresolved. H1 remains BLOCKED even if narrow offline safety acceptance passes.

Repository-wide CI is observed on the final commit. Any inherited dependency/security-audit failure is reported separately and is not repaired within this bounded scope.
