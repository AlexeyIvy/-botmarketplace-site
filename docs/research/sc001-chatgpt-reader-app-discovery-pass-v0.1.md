# SC001 ChatGPT Reader App Discovery PASS v0.1

Date: 2026-09-21
Status: **CHATGPT_READER_APP_DISCOVERY_PASS**

Observed in ChatGPT developer-mode app settings:
- app name: BotMarketplace VPS Reader;
- connection: Secure MCP Tunnel-backed private Reader;
- authentication used: none;
- development status active;
- discovered actions are read-only;
- tool surface visible in ChatGPT:
  - list_roots
  - list_files
  - read_text
- no write/modify action is exposed.

Next stage:
**REMOTE_READER_INVOCATION_PASS**

Validation sequence:
1. attach/select the BotMarketplace VPS Reader app for a chat message;
2. call list_roots;
3. call list_files for the B15 logical root;
4. call read_text for the published run_manifest.json;
5. verify returned data originates from VPS-published data and no write surface exists.
