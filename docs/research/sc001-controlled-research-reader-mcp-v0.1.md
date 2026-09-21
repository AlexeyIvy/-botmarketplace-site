# BotMarketplace Reader MCP v0.1

Date: 2026-09-21
Status: LOCAL READER IMPLEMENTATION

Files:
- `ops/mcp/reader_server_v0_1.py`
- `ops/mcp/reader_smoke_test_v0_1.py`

Properties:
- MCP SDK 2.2.0;
- MCPServer + Streamable HTTP;
- localhost only (`127.0.0.1:8765/mcp`);
- stateless HTTP + JSON responses;
- logical roots only;
- absolute paths rejected;
- resolved-path containment enforced;
- symlink escape not surfaced as readable data;
- bounded reads (max 1 MiB);
- text-like extension allowlist;
- ToolAnnotations: read-only, closed-world;
- no write tools;
- no shell;
- no network tools.

Initial smoke test is in-process and includes a negative path-traversal test.
