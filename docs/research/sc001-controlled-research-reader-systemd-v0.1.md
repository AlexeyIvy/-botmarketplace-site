# BotMarketplace Reader MCP systemd deployment v0.1

Date: 2026-09-21
Status: PRE-TUNNEL LOCAL DEPLOYMENT

Service:
- `botmarket-reader-mcp.service`
- user: `botmarket-mcp`
- group: `botmarket-reader`
- endpoint: `http://127.0.0.1:8765/mcp`
- transport: Streamable HTTP
- no public listener
- restart on failure

Hardening:
- no new privileges;
- empty capability bounding set;
- ProtectSystem=strict;
- ProtectHome=tmpfs;
- private tmp/devices;
- kernel/control-group protections;
- reader-only paths;
- run/control/audit trees inaccessible;
- localhost-only IP policy;
- memory/CPU/task limits.

Validation:
- systemd active;
- listener must be 127.0.0.1:8765 only;
- HTTP MCP Client smoke test;
- path traversal negative test;
- systemd security inspection before external tunnel.
