# BotMarketplace MCP Stack — recovery/runbook v1.0

Date: 2026-09-23

## Purpose

This document records the known-good BotMarketplace MCP topology after GitHub read/write control was completed and verified end-to-end.

It is intended to reduce recovery/migration time when moving to a new VPS or restoring after a server failure.

No secret values are stored in this document.

## Current verified topology

### Local MCP services

| Component | Service | Local endpoint | User/group | Purpose |
|---|---|---|---|---|
| Research Reader MCP | `botmarket-reader-mcp.service` | `127.0.0.1:8765` | `botmarket-mcp:botmarket-reader` | Read-only research/VPS data access |
| Runner Probe MCP | `botmarket-runner-probe.service` | `127.0.0.1:8766` | `botmarket-runner-probe:botmarket-runner-probe` | Controlled Runner inspection/control surface |
| Research Runner MCP v1.0.5 | `botmarket-runner.service` | `127.0.0.1:8767` | `botmarket-runner:botmarket-runner` | Offline sealed-bundle research execution |
| GitHub Control MCP | `botmarket-github-control.service` | `127.0.0.1:8768` | `botmarket-github:botmarket-github` | Dedicated GitHub read/write control plane |

### OpenAI tunnel services

| Tunnel service | Local health port | Upstream MCP |
|---|---:|---|
| `botmarket-openai-tunnel.service` | `127.0.0.1:8080` | Reader MCP |
| `botmarket-runner-tunnel.service` | `127.0.0.1:8081` | Runner Probe / Runner control surface |
| `botmarket-github-tunnel.service` | `127.0.0.1:8082` | GitHub Control MCP `http://127.0.0.1:8768/mcp` |

## GitHub Control MCP

Repository:

`git@github.com:AlexeyIvy/-botmarketplace-site.git`

Branch:

`main`

Dedicated clone:

`/var/lib/botmarket-github-control/repo`

Dedicated SSH deploy key:

`/var/lib/botmarket-github-control/ssh/id_ed25519`

Public key:

`/var/lib/botmarket-github-control/ssh/id_ed25519.pub`

GitHub deploy key must have **Allow write access** enabled.

### GitHub Control code/config

- server: `/opt/botmarket-github-control/server.py`
- env: `/etc/botmarket-github-control/env`
- systemd unit: `/etc/systemd/system/botmarket-github-control.service`

### Exposed tools

- `get_github_control_info`
- `get_repo_status`
- `refresh_repo`
- `list_files`
- `read_text`
- `show_diff`
- `write_text_file`
- `commit_and_push`

### Safety properties

- no arbitrary shell,
- no force push,
- no GitHub Actions workflow writes,
- dedicated clean clone,
- expected HEAD concurrency check,
- expected file SHA256 check,
- remote-moved check before commit,
- explicit write and commit/push separation,
- private keys/API tokens are not returned by MCP tools.

## GitHub tunnel

Current tunnel ID at time of this document:

`tunnel_6ab41289ddd48191a3cbf6f03b774479`

Treat tunnel IDs as environment-specific identifiers. They are not a replacement for runtime credentials.

Runtime API key values must never be committed to GitHub.

GitHub tunnel config:

- env: `/etc/botmarket-research/github-tunnel.env`
- service: `/etc/systemd/system/botmarket-github-tunnel.service`
- health: `http://127.0.0.1:8082`
- upstream: `http://127.0.0.1:8768/mcp`

## Known-good installation scripts

- `scripts/mcp/install-botmarket-github-control-v1.sh`
- `scripts/mcp/install-botmarket-github-tunnel-v1.sh`

The first script may intentionally stop after generating a deploy public key if GitHub has not authorized it yet. Add that public key in repository Settings -> Deploy keys with **Allow write access**, then rerun the same script.

The second script expects a valid OpenAI tunnel ID. It can reuse the existing runtime API key from `/etc/botmarket-research/runner-tunnel.env`, or use a runtime API key supplied through the environment on a fresh host.

## Health verification

Run:

```bash
systemctl is-active botmarket-reader-mcp.service
systemctl is-active botmarket-runner-probe.service
systemctl is-active botmarket-runner.service
systemctl is-active botmarket-github-control.service
systemctl is-active botmarket-openai-tunnel.service
systemctl is-active botmarket-runner-tunnel.service
systemctl is-active botmarket-github-tunnel.service

ss -ltnp | grep -E ':(8080|8081|8082|8765|8766|8767|8768)\b'

curl -sS http://127.0.0.1:8082/readyz
curl -sS http://127.0.0.1:8082/health/mcp
```

Expected GitHub tunnel readiness:

- `/readyz` -> HTTP 200
- `botmarket-github-control.service` -> active
- `botmarket-github-tunnel.service` -> active

A plain GET to a StreamableHTTP MCP endpoint may remain open as `text/event-stream`; a curl timeout after an HTTP 200 does not by itself indicate MCP failure.

## Restore sequence on a replacement VPS

1. Restore the normal non-secret backup archive.
2. Restore/install the base Python environment and `tunnel-client-runtime`.
3. Restore Reader/Runner code/config/systemd units from the backup.
4. Verify Reader and Runner locally before exposing tunnels.
5. Run `scripts/mcp/install-botmarket-github-control-v1.sh`.
6. Add/authorize the generated GitHub deploy public key if needed.
7. Create/reuse an OpenAI tunnel for GitHub Control.
8. Run `scripts/mcp/install-botmarket-github-tunnel-v1.sh <tunnel_id>`.
9. Reconnect the ChatGPT MCP app.
10. Test the complete GitHub cycle:
    - info/status,
    - refresh,
    - read,
    - write a safe test file,
    - diff,
    - commit/push,
    - reread,
    - confirm clean worktree.
11. Only after a successful restore drill declare the recovery complete.

## Backup policy

### CHECKPOINT_BACKUP_AFTER_IDENTITY_ROUTE_V02_FREEZE

Create a portable checkpoint immediately after identity/route v0.2 is frozen and before price/economic research begins.

### FULL_DISASTER_RECOVERY_BACKUP_AFTER_B15_STAGE

Create a full recovery package after B15.

The normal backup should include:

- repository/worktree state,
- research docs,
- SC001 data,
- Runner bundles/jobs/artifacts,
- GitHub Control code/config without secret values,
- tunnel-client profiles/config without secret values,
- relevant `/opt` code,
- relevant `/etc` configs,
- systemd units,
- environment/package manifests,
- SHA256 manifest,
- restore script,
- restore verification procedure.

Secrets must be stored only in a separate encrypted archive:

- exchange API secrets,
- GitHub private SSH keys,
- OpenAI runtime API keys,
- any other credentials.

Never put plaintext secrets into the normal Dropbox/computer backup or Git repository.

## Important infrastructure lessons

- Runner research jobs remain offline.
- Do not merge GitHub write capability into the Research Runner.
- Keep GitHub Control as a separate control-plane MCP.
- External declared Runner inputs materialize under `/work/run/input/<dest>`.
- Immutable bundle files live under `/work/run/package/`.
- Keep Runner `run_key` short; an overly long key caused `INVALID_ARGUMENT` before job creation.
- StreamableHTTP GET may stay open as SSE; use service state and tunnel `/readyz` as authoritative health checks.
