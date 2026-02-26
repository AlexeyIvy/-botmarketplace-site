# Stage 13 — Observability & Ops Baseline

## Scope

Add foundational observability primitives to the API and botWorker:

- **Correlation IDs** on every request/response via `X-Request-Id` header
- **Enhanced `/healthz`** endpoint with `uptime` and `timestamp` fields
- **Structured logging** in botWorker (replaces `console.log`/`console.error` with pino)
- **Global error handler** for unhandled exceptions
- **Smoke tests** (4 new, total 83)

No new DB migrations. No new npm dependencies (`pino` already in deps; `node:crypto` built-in).

---

## What Was Implemented

### 1. `apps/api/src/app.ts`

- Import `randomUUID` from `node:crypto`
- `genReqId` on Fastify constructor: reuses `X-Request-Id` if client sends one, else generates UUID
- `onSend` hook: echoes `X-Request-Id` back on every response
- `setErrorHandler`: global catch-all — logs structured error, returns RFC 9457 Problem Details JSON

### 2. `apps/api/src/routes/healthz.ts`

- Response now includes `uptime` (`process.uptime()`) and `timestamp` (ISO string)

### 3. `apps/api/src/lib/botWorker.ts`

- Added `pino` logger instance (`workerLog`, `name: "botWorker"`)
- All `console.log` → `workerLog.info({ ...fields }, message)`
- All `console.error` → `workerLog.error({ err, ...fields }, message)`
- Error objects passed as structured `err` field, not string-concatenated

### 4. `deploy/smoke-test.sh`

Section 13 (4 tests):
1. `GET /healthz → has uptime`
2. `GET /healthz → has timestamp`
3. `GET /healthz → X-Request-Id header present`
4. `GET /healthz with X-Request-Id → echoed back`

---

## Verification Commands

```bash
# Enhanced healthz
curl -s https://botmarketplace.store/api/v1/healthz | jq .
# Expected: { "status": "ok", "uptime": <number>, "timestamp": "<ISO>" }

# X-Request-Id on every response
curl -sI https://botmarketplace.store/api/v1/healthz | grep -i x-request-id
# Expected: x-request-id: <uuid>

# Client-provided ID echoed back
curl -sI https://botmarketplace.store/api/v1/healthz -H "X-Request-Id: my-trace-42"
# Expected header: x-request-id: my-trace-42

# Full smoke suite (83 tests)
bash deploy/smoke-test.sh
```

---

## Runbook

### How to trace a request

Every HTTP response includes an `X-Request-Id` header. To trace a specific
request through the logs:

```bash
# Capture the ID from a live request
REQ_ID=$(curl -sI https://botmarketplace.store/api/v1/healthz | grep -i x-request-id | awk '{print $2}' | tr -d '\r')

# Search API logs for that ID
sudo journalctl -u botmarket-api --since "1 hour ago" | grep "$REQ_ID"
```

To inject your own trace ID (useful when debugging from a client):
```bash
curl -H "X-Request-Id: my-trace-42" https://botmarketplace.store/api/v1/healthz
```
The same ID will appear in the response header and in the API logs.

### What to check when the API returns 500

1. **Get the `X-Request-Id`** from the response headers.
2. **Search logs** for that ID:
   ```bash
   sudo journalctl -u botmarket-api -n 500 | grep "<req-id>"
   ```
3. Look for a log entry with `"Unhandled error"` — it will contain:
   - `err.message` and `err.stack`
   - `reqId` matching your request ID
4. In development (`NODE_ENV != production`) the `detail` field in the 500
   response body also contains the raw error message.

### How to read botWorker logs

botWorker logs are emitted via pino under the `botWorker` name, mixed into
the `botmarket-api` service output:

```bash
# Stream live worker logs
sudo journalctl -u botmarket-api -f | grep botWorker

# Filter for errors only
sudo journalctl -u botmarket-api --since "1 hour ago" | grep '"level":50'

# Pretty-print in dev (pino-pretty must be installed)
NODE_ENV=development node dist/server.js | pino-pretty
```

Key log fields:
- `workerId` — process ID of the worker instance
- `runId` — the BotRun being processed
- `intentId` — the BotIntent being executed
- `err` — structured error object (message + stack)
