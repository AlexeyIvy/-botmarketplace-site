# BotMarketplace Test Executor MCP v1.0

Date: 2026-09-29  
Status: **APP CONNECTED / RETENTION + REDEPLOY HARDENING PREPARED / INSTALLATION FREEZE v1.0.5 READY**

## Purpose

Create a separate MCP execution plane for ordinary software/research testing on the VPS so ChatGPT can:

- refresh an exact committed GitHub HEAD;
- launch bounded Python/Bash tests without asking the user to paste every command into Termux;
- inspect job status/logs/output files directly;
- perform up to a small fixed number of autonomous test runs;
- use either fully offline execution or public-research network execution;
- never obtain trading/account credentials or host-administration powers.

This component does **not** replace or weaken the hardened offline Research Runner.

## Topology

Planned local MCP endpoint:

`127.0.0.1:8769/mcp`

Planned OpenAI tunnel health endpoint:

`127.0.0.1:8083`

Services:

- `botmarket-test-executor.service`
- `botmarket-test-executor-tunnel.service`

Unix identities:

- control/MCP: `botmarket-testctl:botmarket-testctl`
- isolated worker: `botmarket-testjob:botmarket-test-jobs`
- shared staging/output group: `botmarket-test-jobs`

State:

`/var/lib/botmarket-test-executor`

Dedicated Git clone:

`/var/lib/botmarket-test-executor/repo`

The clone uses its own GitHub deploy key. The deploy key must be **read-only**.

The installer explicitly performs a dry-run push from the dedicated clone and refuses installation if write access appears to be available.

## Execution model

The MCP service never exposes an arbitrary shell tool.

A test can be launched only from an exact committed repository HEAD and only when:

- local Test Executor clone is clean;
- local HEAD equals `origin/main`;
- caller supplies that exact HEAD;
- entrypoint is under an allowed prefix;
- entrypoint suffix is allowed.

Allowed entrypoint prefixes in v1:

- `research/`
- `scripts/research/`
- `tests/`

Allowed executable types:

- `.py`
- `.sh`

The Test Executor snapshots the exact Git commit into a per-job package. The job never executes from the writable Git clone.

Each job receives:

- read-only package;
- dedicated writable output directory;
- clean environment;
- no stdin;
- no exchange API keys;
- no GitHub write key;
- no OpenAI control-plane key.

## MCP tool surface

Planned tools:

- `get_test_executor_info`
- `refresh_repo`
- `run_repo_test`
- `get_job_status`
- `list_recent_jobs`
- `read_job_log`
- `list_job_files`
- `read_job_text`
- `cancel_job`

There is no:

- arbitrary shell command tool;
- arbitrary host file reader;
- arbitrary host file writer;
- package installer tool;
- systemd mutation tool;
- Git write/commit/push tool;
- credential reader;
- order/trading tool.

## Network profiles

### offline

Systemd boundary:

- `PrivateNetwork=yes`
- `RestrictAddressFamilies=AF_UNIX`

No Internet or host network is available.

This is the preferred profile for:

- unit tests;
- parser tests;
- compile/lint;
- synthetic fixtures;
- offline replay;
- deterministic self-tests.

### public_research

Allows public Internet access for research/test scripts, but not access to host-local or private networks.

Blocked:

- `127.0.0.0/8`
- `::1/128`
- RFC1918 IPv4 private ranges;
- IPv4 link-local;
- IPv6 unique-local/link-local;
- multicast.

A dedicated resolver file contains only global DNS servers. If the host exposes only a loopback/private resolver, the installer falls back to public resolvers.

The installer runs a real sandbox smoke that must prove both:

1. public HTTPS access works;
2. local GitHub Control MCP on `127.0.0.1:8768` is unreachable from the test job.

Important: v1 is a **public Internet** profile, not a domain allowlist. The security boundary against trading is credential isolation + host isolation, not URL filtering.

## Trading/account boundary

Test jobs are intentionally unable to obtain account authority.

They do not receive:

- Bybit secret/API credential environment;
- OKX secret/API credential environment;
- private SSH keys;
- GitHub write deploy key;
- OpenAI runtime API key.

Sensitive host locations are hidden from jobs, including:

- `/etc/botmarket-research`
- `/etc/botmarket-github-control`
- `/etc/botmarket-test-executor`
- GitHub Control state;
- Test Executor repo/SSH key directories;
- Runner/Runner Probe state;
- tunnel state;
- systemd/dbus control sockets;
- Docker/containerd sockets where present.

A job runs as the unprivileged `botmarket-testjob` user with:

- `NoNewPrivileges=yes`
- empty capability sets;
- private devices/tmp;
- protected system/home/kernel/control groups;
- hidden process information;
- namespace restrictions.

The future Trading Executor, if ever created, remains a separate component and separate authorization boundary.

## Restricted root bridge

The Test Executor control MCP may use exactly three root-owned helpers:

- `/usr/local/sbin/botmarket-test-launch`
- `/usr/local/sbin/botmarket-test-cancel`
- `/usr/local/sbin/botmarket-test-prune`

The `botmarket-testctl` sudoers policy grants passwordless root execution **only** for these three exact command paths. The prune helper has no arbitrary path argument: it accepts only a canonical Test Executor job ID under the fixed jobs root, independently verifies completion/retention eligibility and refuses active, fresh, symlinked, escaped or incomplete jobs.

Important systemd distinction:

- the **control MCP service** must be allowed to traverse this exact sudo/setuid bridge;
- the **test jobs themselves** keep `NoNewPrivileges=yes`, empty capability sets, and the full sandbox restrictions.

Therefore do **not** add `NoNewPrivileges=true` or an empty `CapabilityBoundingSet=` to `botmarket-test-executor.service` unless the root broker architecture is redesigned. Doing so prevents the service from using the restricted sudo bridge.

The MCP server performs self-tests for all three root helpers through sudo during its own startup. If any launch/cancel/prune bridge is unavailable from the real systemd sandbox, the service fails closed and does not become operational. `get_test_executor_info` reports the three helper checks together.

The installer also verifies:

- launcher escalation works;
- cancel-helper escalation works;
- retention-prune escalation works;
- a synthetic old completed job containing a worker-owned `0700` directory and `0600` file can be pruned;
- an unrelated root command (`/usr/bin/id -u`) is denied.

## First-bootstrap validation finding

The first deployment attempt on 2026-09-29 correctly passed:

- GitHub read access;
- GitHub write denial;
- policy/runner/helper installation.

It then stopped at:

`TEST_LAUNCH_REVIEW:ROOT_REQUIRED`

Root cause: installer self-tests used `sudo -u botmarket-testctl <root-helper>`, which deliberately ran the helper *as* the unprivileged user. The intended production path is:

`root installer -> runuser botmarket-testctl -> sudo NOPASSWD -> exact root helper`

All occurrences of the incorrect self-test path were replaced with one shared `as_testctl_root` helper. The offline and public-network installation smokes now use the same privilege path as the MCP server.

A follow-up review also found that the MCP service's original `NoNewPrivileges=true` / empty capability bounding set would have blocked the same restricted sudo bridge at runtime. The control-service sandbox was corrected, while the worker-job sandbox remains unchanged and strict.

Targeted post-fix audit result:

**PASS.**

## Resource limits

v1 policy:

- max one concurrent job;
- max 3 launches per rolling hour;
- max 10 launches per UTC day;
- max job timeout: 900 seconds;
- default timeout: 180 seconds;
- memory: 1 GiB;
- CPU: 200%;
- tasks: 64;
- individual file-size limit: 64 MiB;
- repository snapshot: max 128 MiB / 6000 files.

Completed job retention:

- 7 days;
- max 100 completed jobs retained.

These rate limits are stored in root-owned policy and cannot be changed through the MCP tool surface.

## Exact package safety

Repository snapshot rejects:

- symlinks;
- hardlinks;
- device/special files;
- absolute/path-escape members;
- `.git` internals;
- tracked secret-like paths such as private keys and non-example `.env` files.

Package directories use the setgid job group so nested files remain readable by the worker.

Git executable semantics are preserved as read/execute only:

- executable tracked files -> `0550`;
- non-executable tracked files -> `0440`.

The worker cannot modify the package.

## Three programmer-expert review rounds

### Round 1 — architecture/security

Found and corrected:

1. top-level state `0700` prevented job-user traversal;
2. read-only deploy-key probe was executed from the wrong directory and could give a false PASS;
3. entrypoint restrictions existed only in MCP server, not root launcher;
4. public profile DNS could conflict with private/loopback network denial.

Result:

**PASS after correction.**

### Round 2 — Unix/runtime/systemd

Found and corrected:

1. service `UMask=0027` reduced output directory group-write permission;
2. repo snapshot discarded executable bits;
3. root launcher did not repeat argument-size/count and credential-boundary checks;
4. Python bytecode writes were not explicitly disabled.

Result:

**PASS after correction.**

### Round 3 — operations/observability

Found and corrected:

1. nested package directories could lose setgid/group inheritance;
2. public resolver could itself be in a blocked private range;
3. `refresh_repo(expected_head)` checked the wrong side of the fetch boundary;
4. completed jobs had no retention policy;
5. installer did not prove the public network sandbox end-to-end.

Result:

**PASS after correction.**

## Consolidation audit

After all three rounds, the final installer was checked for simultaneous presence of:

- distinct control/job users;
- private repo/SSH paths;
- read-only GitHub key enforcement;
- dual entrypoint validation in MCP and root launcher;
- setgid package/output permissions;
- executable-bit preservation;
- clean credential-free environment;
- offline/public network profiles;
- public DNS isolation;
- localhost/private-network denial;
- offline install job smoke;
- public-network install job smoke;
- system resource limits;
- autonomous run-rate limits;
- retention policy;
- no arbitrary shell tool;
- no repo write;
- separate tunnel ports.

Consolidation result:

**PASS.**

## Installation files

Current installation freeze:

`docs/infrastructure/botmarket-test-executor-installation-freeze-v1.0.5.json`

Main installer:

`scripts/mcp/install-botmarket-test-executor-v1.sh`

Tunnel installer:

`scripts/mcp/install-botmarket-test-executor-tunnel-v1.sh`

## Local deployment result

The v1.0.2 installer completed successfully on 2026-09-29.

Observed PASS conditions:

- GitHub repository read: PASS;
- GitHub repository write: DENIED AS REQUIRED;
- arbitrary root sudo: DENIED AS REQUIRED;
- MCP server compile: PASS;
- control-service restricted sudo bridge self-test: PASS;
- isolated offline worker self-test: PASS;
- public-research network sandbox self-test: PASS;
- local MCP active at `http://127.0.0.1:8769/mcp`.

Canonical deployment state:

`docs/infrastructure/botmarket-test-executor-deployment-state-v1.0.json`

The Test Executor is locally operational. Remote ChatGPT access remains pending until the dedicated OpenAI tunnel and app/plugin connection are completed.

## First deployment sequence

1. Run the main installer as root.
2. If it prints `TEST_EXECUTOR_DEPLOY_KEY_NOT_AUTHORIZED_YET`, copy the printed public key into GitHub repository Deploy Keys.
3. **Do not enable Allow write access.**
4. Rerun the same installer.
5. Installer must finish with:
   - GitHub read PASS;
   - GitHub write DENIED_AS_REQUIRED;
   - isolated offline job self-test PASS;
   - public-research network sandbox self-test PASS;
   - local MCP active on 8769.
6. Create a new OpenAI tunnel for Test Executor.
7. Run the tunnel installer with that tunnel ID.
8. Connect the resulting Test Executor app/plugin in ChatGPT.
9. From ChatGPT, call:
   - `get_test_executor_info`;
   - `refresh_repo`;
   - one harmless offline committed test.
10. Only after end-to-end PASS declare Test Executor operational.

## Operational rule after deployment

For new research code:

`STATIC REVIEW -> TEST EXECUTOR OFFLINE RUN -> FIX IF NEEDED -> OPTIONAL PUBLIC-RESEARCH SMOKE -> FREEZE -> RESEARCH EXECUTION`

The user should not be used as the normal command runner for software debugging.

## VPS namespace compatibility result

The first isolated worker-job bootstrap exposed one host-specific systemd incompatibility:

`InaccessiblePaths=/run/systemd`

The compatibility diagnostic proved:

- all worker identity/resource controls PASS;
- `NoNewPrivileges`, private tmp/devices and system/kernel/proc restrictions PASS;
- empty capabilities PASS;
- read-only/read-write mount rules PASS;
- all BotMarketplace secret/config/state masks PASS through `/var/lib/botmarket-tunnel`;
- `InaccessiblePaths=/run/systemd` alone causes `226/NAMESPACE`;
- targeted `InaccessiblePaths=/run/systemd/private` PASS;
- `/run/dbus` mask PASS;
- offline network namespace PASS;
- AF_UNIX-only offline profile PASS;
- the real installed `job_runner.py` PASS in the intended `jobs/<job_id>` layout;
- the complete `public_research` systemd property set PASS.

The final public-network smoke reached the external Bybit announcements site and received HTTP 403. This is considered transport success for the compatibility gate because DNS/TCP/TLS/HTTP completed successfully; the installer still separately requires localhost MCP access to be denied.

Installer v1.0.2 therefore:

- replaces the broad `/run/systemd` mask with the narrow `/run/systemd/private` socket mask when present;
- treats curl transport success plus any valid HTTP status 100–599 as public HTTPS egress PASS;
- retains every other passing sandbox property.

Canonical compatibility result:

`docs/infrastructure/botmarket-test-executor-compatibility-v2-result-v0.1.json`

## First MCP end-to-end run finding

After the tunnel/app connection, ChatGPT successfully called:

- `get_test_executor_info`;
- `refresh_repo`.

The Test Executor clone advanced from the installer-era commit to the then-current canonical GitHub HEAD and remained clean.

The first two `run_repo_test` attempts failed before a new `job.json` appeared.

Static reconstruction of the exact committed tree ruled out snapshot safety gates:

- 2713 total Git-tree entries;
- 2521 blobs;
- 0 symlinks;
- 0 submodules;
- 0 tracked secret-like filenames;
- about 19.5 MB of blob content;
- all below configured snapshot limits.

The deterministic control-service conflict was runtime directory creation:

- `botmarket-test-executor.service` correctly keeps `RestrictSUIDSGID=true`;
- server code attempted `chmod(02750/02770)` while creating jobs/packages/output;
- that setgid operation is forbidden by the control-service sandbox and happens before manifest creation.

v1.0.3 fixes the implementation without weakening the policy:

- no runtime setgid chmod/mkdir in the MCP service;
- all job/package/snapshot/manifest paths receive group `botmarket-test-jobs` explicitly;
- worker-readable package files remain `0440/0550`;
- output remains group-writable `0770`;
- worker sandbox retains `RestrictSUIDSGID`, `NoNewPrivileges`, empty capabilities and all previously validated namespace protections;
- manifestless orphan job directories older than one hour are pruned;
- the MCP service performs a filesystem-boundary self-test at startup from its actual systemd sandbox and refuses to start if group/layout permissions are not usable.

Canonical diagnostic:

`docs/infrastructure/botmarket-test-executor-first-mcp-run-diagnostic-v0.1.json`


## Retention cleanup permission finding (2026-10-08)

A later `run_repo_test` regression appeared only after completed jobs crossed the 7-day retention boundary.

Live journal traceback localized the failure before new job creation:

- `run_repo_test -> prune_completed_jobs -> shutil.rmtree(job)`;
- `PermissionError` occurred on worker-owned nested output files from completed historical jobs;
- MCP service health, restricted sudo bridge, filesystem-boundary self-test, repo freshness, run-rate counters and snapshot safety gates all remained PASS.

Root cause:

- the control service runs as `botmarket-testctl`;
- isolated jobs create some nested output paths as `botmarket-testjob`;
- retention cleanup attempted recursive deletion directly as the control user;
- nested worker-owned directories can intentionally lack group-write permission, so direct `shutil.rmtree` is not a valid retention mechanism.

v1.0.4 fixes the retention permission defect without weakening the worker sandbox:

- add root-owned `/usr/local/sbin/botmarket-test-prune`;
- sudo remains restricted to the exact helper path;
- helper accepts only canonical job IDs under the fixed Test Executor jobs root;
- symlink/path escape, missing manifest/result, manifest/job-id mismatch and active jobs fail closed;
- helper independently checks retention eligibility from the job-id timestamp and root-owned policy before deletion;
- `prune_completed_jobs` delegates only eligible completed-job removal to the helper;
- installer includes a synthetic ownership smoke with a worker-owned `0700` nested output directory and `0600` file.

No research semantics, network profile, credentials boundary, collector state, Worker `NoNewPrivileges`, capability set or protected-data boundary changes.

### v1.0.5 redeploy hardening

A three-pass programmer review after the v1.0.4 repair found additional operational failure modes that could otherwise force repeated manual Termux cycles:

- a transient `git ls-remote` failure was previously mislabeled as an unauthorized deploy key;
- the dry-run push check previously treated any network failure as proof of read-only GitHub access;
- `systemctl enable --now` did not prove that an already-active MCP process restarted onto the newly installed server code;
- startup health checked only the launch bridge, not the new prune bridge required by `run_repo_test`;
- the installer public-network smoke had no bounded retry;
- relative-path operator commands were vulnerable to the current working directory.

v1.0.5 therefore:

- retries GitHub read/fetch/clone checks with bounded backoff;
- reports deploy-key authorization only for explicit authentication/repository-denial signatures;
- accepts read-only status only from an explicit GitHub write-permission rejection; transport failures are indeterminate and fail closed;
- explicitly restarts the MCP service after installation;
- performs a bounded rollback of the prior server/unit/env/policy/sudoers if the new service cannot restart;
- requires all launch/cancel/prune sudo bridges to self-test at service startup;
- retries the public HTTPS transport smoke;
- adds `scripts/mcp/redeploy-botmarket-test-executor-v1.0.5.sh`, which resolves paths from its own location, checks a clean exact `origin/main` worktree, verifies the frozen installer SHA256, runs `bash -n` before sudo, verifies a real process restart, and rechecks all three helpers afterward.

The verified redeploy wrapper is the preferred update path for an existing installation. It is deliberately CWD-independent once invoked by absolute path.


## Residual limitations

- The v1 `public_research` profile is not a hostname/domain allowlist.
- Test Executor intentionally cannot mutate system packages/services.
- Test Executor intentionally cannot read arbitrary VPS research directories.
- Production collector and account/trading actions remain outside this component.
- If a test genuinely requires protected VPS data, a separate read-only input-export mechanism must be designed rather than broadening host filesystem access.
