# SC001 OpenAI Secure MCP Tunnel PASS v0.1

Date: 2026-09-21
Status: **OPENAI_SECURE_MCP_TUNNEL_SERVICE_PASS**

Observed production state:
- `botmarket-openai-tunnel.service` started successfully;
- `OPENAI_TUNNEL_READY` emitted;
- local readiness endpoint returned `ready`;
- tunnel metadata fetched for `botmarket-reader-v1`;
- control-plane poller started;
- local MCP target remains `http://127.0.0.1:8765/mcp`;
- service completed with `OPENAI SECURE MCP TUNNEL SERVICE PASS`.

Non-blocking observation:
- runtime logged an OAuth discovery warning against the local MCP endpoint.
- The Reader MCP intentionally does not advertise OAuth metadata.
- Runtime nevertheless reached `ready`; this is treated as an optional OAuth-discovery failure, not a tunnel readiness failure.
- Do not add OAuth to the Reader solely to silence this warning unless product requirements later require MCP-side authentication.

Next stage:
**CHATGPT_TUNNEL_APP_CONNECTION_AND_REMOTE_READER_VALIDATION**

Validation sequence:
1. create/select a ChatGPT developer-mode app using Connection = Tunnel;
2. select `botmarket-reader-v1` (or paste the tunnel id);
3. confirm tool discovery exposes only `list_roots`, `list_files`, `read_text`;
4. run remote read validation against the published B15 dataset;
5. verify no write/action tools are exposed.
