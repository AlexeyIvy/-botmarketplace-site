# Reader MCP differential diagnostic v0.1

Use when systemd reports the Reader active but the expected loopback listener is absent.

The diagnostic checks systemd state/journal, host and service network namespaces,
socket state, a bare unprivileged loopback bind, the systemd IP allow/deny policy,
and an eight-second direct launch of the exact Reader application outside the
systemd sandbox. The Reader service is restored afterward.

It does not read credentials and does not modify research data.
