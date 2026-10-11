# SC001-P1-OPS-005 - Host-tool type diagnostic and v0.2 repair

Date: 2026-10-11
Status: STATIC PACKAGE READY / STRATEGY REVIEW REQUIRED
TASK_ID: SC001-P1-OPS-005
WORKER_ID: P1_PROSPECTIVE_EVENT

## Repair diagnostic

- Exact failure signature: `ACTION_FAIL:HOST_TOOL_TYPE`.
- Failing assertion identity: `require_fixed_tools()` rejected `/usr/bin/python3` before source, parent, package, or sudoers installation.
- Full traceback: not emitted by the fail-closed installer; the canonical host receipt records the terminal token and earliest-fail call order.
- First failing invariant: v0.1 applied `link_metadata.st_mode & 0o022` to a normal root-owned Linux symlink whose nominal mode is `0777`.
- Last known-good stage: root and required-user checks passed; the user-reported repository, installer, adapter, and static-validation identities matched the v0.1 freeze.
- Affected code path: only host-tool preflight for `/usr/bin/python3`.
- Affected contract: distinguish a trusted executable symlink from its resolved executable without treating symlink mode bits as target permissions.
- Offline reproducibility: yes, with injected fake `lstat` and `readlink` metadata; execution was not authorized here.
- Primary failure class: `TASK_LOCAL_ENVIRONMENT_CONFIGURATION_DEFECT`.
- Root-cause confidence: HIGH.
- Frozen research semantics: unchanged.

## Adjacent-defect sweep

The complete installer path was reviewed from arguments through root/user/tool checks, source identity, package staging, sudoers validation, rollback identity, and static validation. The embedded entrypoint and fixed sudoers content remain byte-identical to v0.1.

Covered risks: unsafe link or target ownership; dangling targets; relative/absolute escape; multi-hop cycles or excessive chains; non-regular, writable, or non-executable final targets; untrusted tool directories; preservation of regular-file behavior; and continued rejection of symlinked `/usr/sbin/visudo`. No generic bypass or silent fallback was added.

## Coherent repair set

The additive v0.2 installer permits symlink traversal only for exact `/usr/bin/python3`. Every traversed link must be root-owned, every lexical hop must remain below root-owned non-writable `/usr/bin`, and the final object must be a root-owned regular executable without group/world write bits. Linux symlink mode bits are not interpreted as target writability. `/usr/sbin/visudo` remains strict regular-file only.

Installed adapter, entrypoint, sudoers content, users, paths, modes, fixed command, collector scope, apply ordering, cleanup, rollback, and absence of live-read behavior remain unchanged.

## Artifact identities

- v0.1 installer immutable: `a9e330ffad08be27f48b8a749f5c7335be8244d752db03b9023168b7f6c559fa`
- v0.2 installer: `3e50ba2b4c537cbb039bf33850e80c5dd165e0e1d94b2a9d6603d690c4e98450`
- v0.2 regression specification: `45b9b4098727a055fd5afb8862dc4caebfa05e5c5d6f7f2563fcc3938eda6223`
- v0.2 freeze: `3e9dff667a287fd61a016c079b36729f614b28f71c9d8fdb64cf5902404c2730`
- adapter: `844949ec670c6cd1856d2a1ea016f3554b6c6e85b95b254b6e370907eb47d2c7`
- embedded entrypoint: `eadaf746e0ca31de040040a744b0d7ff2e72995f9fd6fe84a7fe33e63b3e4612`
- sudoers content: `794e6e9bd87f062cbde818e852affdb81ef6a83adb8349e5e788c52ac798f8ba`

## Validation ladder and safety receipt

- Static/source review: PASS.
- Targeted regression specification: PREPARED, NOT EXECUTED.
- Adjacent test set: PREPARED, NOT EXECUTED.
- Full preflight terminal token: `NOT_EXECUTED_BY_TASK_AUTHORIZATION`.
- Output firewall: PASS by static inspection; no execution or live read occurred.
- Repair cycles consumed: 0.
- Tests changed: additive regression only; no existing test weakened.
- Protected evidence / outcome / network access: false.
- Test Executor / Runner / VPS job: none.
- Host apply, rollback, sudo, chmod/chown, collector read, or mutation: none.

## Remaining risk and continuation gate

Tests are unexecuted by contract. Strategy Manager must review the diff and arrange authorized validation before acceptance. The prior approval applied only to frozen v0.1. Any v0.2 host apply requires a new exact T3 user approval; the first live read remains a separate later T3 gate.
