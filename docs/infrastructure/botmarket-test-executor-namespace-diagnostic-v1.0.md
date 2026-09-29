# BotMarketplace Test Executor — namespace compatibility diagnostic v1.0

Date: 2026-09-29  
Status: **READY FOR ONE-SHOT HOST DIAGNOSTIC**

## Trigger

During the second bootstrap attempt, the Test Executor installation reached:

- read-only GitHub deploy key verification PASS;
- restricted sudo policy PASS;
- arbitrary root sudo denied PASS;
- MCP server compile PASS;
- MCP service installation/start PASS.

The first isolated offline worker job then failed before Python execution with:

`status=226/NAMESPACE`

This is a systemd sandbox/namespace setup failure.

It is not evidence of:
- Python runner failure;
- research-code failure;
- network failure;
- trading/account access.

## Diagnostic strategy

Do not disable hardening properties by guesswork.

Run one harmless host probe that:

1. executes only `/usr/bin/true`;
2. starts with a minimal transient service;
3. adds the real worker hardening properties one at a time;
4. includes:
   - identity/resource controls;
   - `NoNewPrivileges`;
   - private tmp/devices;
   - system/home/kernel/control protection;
   - hostname/proc/namespace restrictions;
   - empty capabilities;
   - read-only/read-write path mounts;
   - each existing `InaccessiblePaths` mask;
   - offline private network;
   - AF_UNIX restriction;
5. stops at the first cumulative failure;
6. reruns the first failing property in an isolated confirmation boundary;
7. saves systemd exit state and journal tail;
8. writes one JSON result into GitHub runtime inbox.

No project code is executed and no network calls are made by the diagnostic.

## Diagnostic script

`scripts/mcp/diagnose-botmarket-test-executor-namespace-v1.sh`

SHA256:

`b70d64b03e5b131e032a5a446df8ec65daf6f8fde8b9d33fb9a8f17fe5d23827`

Runtime result:

`docs/research/runtime-inbox/botmarket-test-executor-namespace-diagnostic-v1.json`

## Decision rule

After the result is published:

- if one property fails by itself, adapt/remove only that unsupported hardening primitive and preserve the rest;
- if the property passes alone but fails cumulatively, identify the interaction and redesign the smallest conflicting combination;
- if all cumulative properties pass, investigate the production-only path/ownership/mount combination next.

Do not weaken the entire sandbox merely to bypass `226/NAMESPACE`.
