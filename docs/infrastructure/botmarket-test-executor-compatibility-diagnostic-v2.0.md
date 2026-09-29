# BotMarketplace Test Executor — compatibility diagnostic v2.0

Date: 2026-09-29  
Status: **READY FOR ONE-SHOT HOST VALIDATION**

## Input from v1 diagnostic

Canonical v1 result:

`docs/infrastructure/botmarket-test-executor-namespace-diagnostic-v1-result-v0.1.json`

Runtime evidence:

`docs/research/runtime-inbox/botmarket-test-executor-namespace-diagnostic-v1.json`

Localized incompatibility:

`InaccessiblePaths=/run/systemd`

Observed:

- all prior hardening stages PASS;
- `ReadOnlyPaths` PASS;
- `ReadWritePaths` PASS;
- BotMarketplace secret/config/state masks PASS;
- last passing mask: `/var/lib/botmarket-tunnel`;
- first failing property: `InaccessiblePaths=/run/systemd`;
- exit status: `226/NAMESPACE`;
- isolated confirmation: `FAIL_PROPERTY_ALONE`.

Conclusion:

Masking the entire `/run/systemd` hierarchy is incompatible with transient-service namespace setup on this VPS.

## v2 purpose

Do not modify the installer yet.

Validate the complete remaining host-specific sandbox after replacing the broad systemd hierarchy mask with the narrow control socket:

`InaccessiblePaths=/run/systemd/private`

when that socket exists.

The v2 diagnostic then checks:

1. known-good base without broad `/run/systemd`;
2. targeted `/run/systemd/private` mask;
3. `/run/dbus` mask;
4. Docker socket mask when present;
5. containerd mask when present;
6. offline `PrivateNetwork=yes`;
7. offline `RestrictAddressFamilies=AF_UNIX`;
8. the real installed `job_runner.py` using a harmless fixture in the real `jobs/<job_id>/package|output` layout;
9. full public-research systemd property set;
10. public HTTPS access to the Bybit announcements site;
11. negative localhost MCP reachability check.

Any early failure is written to the runtime inbox before exit.

## Safety

The diagnostic:

- does not edit the installer;
- does not enable/disable persistent services;
- does not execute repository research code;
- uses only a generated harmless fixture;
- does not read secret files;
- does not receive trading/API credentials;
- uses public network only in the explicit public-network smoke;
- cleans up transient units and fixture files.

## Diagnostic script

`scripts/mcp/diagnose-botmarket-test-executor-compatibility-v2.sh`

SHA256:

`4d00dd930c579e7161539e0f5a8e7a7c6964f3567ba143ba7e65f5f9f1b02f40`

Runtime output:

`docs/research/runtime-inbox/botmarket-test-executor-compatibility-v2.json`

## Decision rule

Only after v2 produces full PASS should the main Test Executor installer be changed.

If v2 fails:

- use the first failing check from the published JSON;
- do not weaken unrelated hardening;
- preserve every previously proven passing property.
