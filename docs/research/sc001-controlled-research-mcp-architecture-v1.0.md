# SC001 / BotMarketplace — Controlled Research MCP Architecture v1.0

Date: 2026-09-21
Status: **IMPLEMENTATION BASELINE FROZEN**

## Goal

Remove routine manual VPS operation from the research loop while preserving least privilege.

Target workflow:

1. assistant designs/updates a research script;
2. code is versioned and frozen;
3. an allowlisted job is requested;
4. VPS executes the immutable job under resource limits;
5. assistant reads logs/results directly from VPS;
6. assistant analyzes results and prepares the next step.

No raw datasets need to be copied to GitHub.

## Security domains

### Reader MCP
- read-only;
- no arbitrary filesystem paths;
- logical roots only;
- no credentials;
- no SSH keys;
- no shell;
- no writes.

### Runner MCP
- controlled actions only;
- no arbitrary shell/command;
- accepts only registered job IDs + schema-validated arguments;
- cannot directly access secrets;
- delegates execution to a minimal root-owned broker.

### Job executor
- Unix identity: `botmarket-runner`;
- immutable root-owned job bundles;
- per-run isolated directory;
- systemd/cgroup resource limits;
- network disabled by default;
- protected collectors excluded from authority.

## Linux identities

- `botmarket-mcp` — Reader MCP.
- `botmarket-runner-api` — Runner MCP/API only.
- `botmarket-runner` — job executor only.

All use `/usr/sbin/nologin`, no sudo membership.

## Filesystem layout

- `/opt/botmarket-research/app` — MCP/broker application code.
- `/opt/botmarket-research/venv` — Python environment.
- `/opt/botmarket-research/jobs` — immutable root-owned job bundles.
- `/etc/botmarket-research` — root-owned configuration/policies.
- `/var/lib/botmarket-research/runs` — per-run state/results.
- `/var/lib/botmarket-research/published` — data exposed to Reader MCP.
- `/var/log/botmarket-research/audit` — append-only operational audit.
- `/run/botmarket-research/broker.sock` — local broker socket.

Existing `/home/botmarket/sc001_data` is NOT treated as a security boundary and its historical permissions are not globally modified.

## Code identity

Jobs are never executed directly from a mutable Git working tree.

Every job manifest freezes:
- job ID;
- executable/interpreter;
- immutable script hash;
- argument schema;
- input roots;
- outputs;
- runtime limit;
- CPU/memory/task limits;
- network policy;
- optional credential profile.

Hash mismatch => execution refused.

## Run provenance

Each run gets an immutable run ID and directory containing:
- request metadata;
- job manifest snapshot;
- stdout/stderr;
- status;
- output files;
- hashes.

## Transport

Primary OpenAI path:
- private local MCP service;
- OpenAI Secure MCP Tunnel;
- no inbound MCP firewall port.

Vendor-neutral public edge may be added later for other MCP clients without changing the local Reader/Runner design.

## Current ChatGPT compatibility

Current OpenAI product support may allow only read/fetch custom MCP actions on some personal plans, while full write/action MCP is available on supported workspace plans.

Therefore the server architecture supports two controlled execution triggers:

1. **Runner MCP action path** — used by clients that support MCP actions.
2. **GitHub control-plane queue fallback** — small signed/versioned job requests only; VPS broker polls and validates them. Research datasets/results remain on VPS.

The GitHub fallback exists specifically so routine execution can still be automated without copying datasets to GitHub or granting arbitrary shell access.

## Forbidden capabilities

- arbitrary shell;
- arbitrary executable/path;
- root shell;
- sudo from MCP;
- unrestricted systemd;
- trading/withdrawal actions;
- direct secret reads;
- arbitrary filesystem access;
- execution from mutable Git checkout;
- unrestricted outbound network;
- retroactive modification of protected B13-C/B14-A rules or data.

## Kill switches

- execution-only kill switch;
- global MCP kill switch.

## Audit

Record:
- UTC;
- client/control path;
- tool/job ID;
- argument hash;
- code hash;
- input hashes;
- start/end;
- exit code;
- output hashes;
- publish result.

Secrets are excluded from logs.

## Implementation order

1. clean temporary ACL experiments;
2. create final FHS layout and `botmarket-runner-api`;
3. install isolated Python venv + MCP SDK;
4. implement Reader MCP;
5. systemd sandbox Reader;
6. connect Secure MCP Tunnel and validate read path;
7. implement immutable job registry/bundles;
8. implement broker + executor sandbox;
9. implement Runner MCP;
10. implement GitHub control-plane fallback;
11. negative security tests;
12. final operational PASS.
