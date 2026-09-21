# BotMarketplace OpenAI Secure MCP Tunnel service v0.1

Date: 2026-09-21

Runtime-only OpenAI tunnel-client v0.0.14.
Local MCP target: http://127.0.0.1:8765/mcp.
Health/admin surface: 127.0.0.1:8080 only.
Main channel only; MCP concurrency 2; control-plane prefetch queue 4.
No managed cloudflared companion for the base Reader tunnel.

Startup is gated by /readyz via ExecStartPost. Secrets are file-backed and excluded from argv.
