# Stage 17 — AI Chat Widget (Explain Mode, read-only) — Spec v2

**Status:** v2 (reviewed & improved by expert analysis)
**Baseline:** main after Stage 16 (Settings UX complete)
**Goal:** Add an in-app AI chat widget that can explain platform state and data
(runs/backtests/errors) using safe, workspace-scoped context. No "actions" yet.

> **Reviewer notes (v1→v2):** Fixed 6 critical issues (K1–K6), filled 8 gaps (П1–П8), corrected
> field name mismatches against Prisma schema, added system prompt template, provider
> TypeScript interface, rate-limit numbers, error-mapping table, and AI status endpoint.
> See [ANALYSIS] markers inline.

---

## 1) Background & Problem

Current state:
- Platform is usable (Terminal, Strategies, Bots, Lab, Settings).
- Users need help understanding: "why did my run stop?", "why is backtest poor?",
  "what do these errors mean?", "how do I improve risk settings?"
- No chat UI on the site; no safe server-side AI gateway.

---

## 2) Stage 17 Objective

Implement an **AI Chat Widget (Explain mode)** on the website:
- floating chat button → opens drawer/modal
- user can ask questions about the platform
- assistant replies using **read-only** workspace-scoped context
  (strategies / bots / runs / events / lab results)
- strict secret redaction (no apiKey / secret / encryptedSecret / passwordHash in
  prompts or responses)
- simple cost control and rate limiting (concrete values defined in §3B and §3E)

Stage 17 is **Explain-only**:
- assistant MAY suggest what the user should do
- assistant MUST NOT offer to execute actions (create bots, start runs, edit strategies) —
  those are Stage 18

---

## 3) Scope (Must-have)

### A) Chat UI (frontend)

**Component architecture:**

> [ANALYSIS-K5] Next.js 15 App Router distinction: ChatWidget must be a `"use client"`
> component. Do NOT make root `layout.tsx` a client component. Use a thin wrapper:

```
apps/web/src/app/layout.tsx          ← server component (stays server)
  └── <ChatWidgetWrapper />          ← "use client" wrapper added here
        └── <ChatWidget />           ← floating button + state
              └── <ChatDrawer />     ← panel (conditionally rendered)
```

Implementation:
- `ChatWidgetWrapper` is a `"use client"` file that imports and renders `ChatWidget`.
- Mount `<ChatWidgetWrapper />` at the bottom of `<body>` in `layout.tsx`.
- `ChatWidget` renders a fixed-position button (bottom-right, z-index above nav).
- `ChatDrawer` renders a fixed-position panel (right side, slides in/out).

**UI spec:**
- Floating button: "💬 Chat" (or icon only on mobile), bottom-right, `position: fixed`.
- Drawer/panel:
  - `position: fixed`, right-aligned, full-height or 70vh
  - message list (user messages right-aligned, assistant left-aligned)
  - input textarea (multi-line, max visible 4 lines)
  - send button (disabled while loading)
- Loading state: spinner or "thinking…" indicator inside drawer
- Error display: inline error below input (RFC 9457 `problem.detail`)
- 401 UX: use **existing Stage 16 pattern** — check `problem.status === 401`, render
  inline banner "Session expired — [Log in]" linking to `/login`; do NOT show 503/429
  raw error codes to user — show human-readable strings

**Implementation constraints:**
- No new npm packages (consistent with Stage 14–16 constraints).
- Styling via CSS variables only (`--bg-card`, `--border`, `--text-primary`,
  `--accent`, `--bg-secondary`). No Tailwind utilities.
- Inline styles via `React.CSSProperties` (consistent with Settings page approach).
- Chat history: `useState` in `ChatWidget` (memory only per session).
- [ANALYSIS-П7] If localStorage persistence is added (nice-to-have), clear on
  logout: call `clearChatHistory()` from `clearAuth()` in `lib/api.ts`.

### B) AI API gateway (backend)

**Routes:**

> [ANALYSIS-K6] All routes follow `/api/v1/` prefix. New routes:

```
POST   /api/v1/ai/chat       — main chat endpoint
GET    /api/v1/ai/status     — [NEW] AI availability probe (no auth required)
```

**`GET /api/v1/ai/status`** (unauthenticated):
```json
{ "available": true }   // AI_API_KEY present and non-empty
{ "available": false }  // AI_API_KEY missing
```
- UI checks this on mount and shows/hides the chat button accordingly.
- No auth required (public endpoint, no sensitive data).

**`POST /api/v1/ai/chat`** spec:
- Requires JWT auth (`preHandler: app.authenticate`)
- Requires workspace header + `resolveWorkspace()` enforcement
- Input body:
  ```typescript
  {
    messages: Array<{ role: 'user' | 'assistant'; content: string }>;
    contextMode?: 'auto' | 'none';  // default: 'auto'
  }
  ```
- Output (success):
  ```json
  { "reply": "..." }
  ```
- Output (error): RFC 9457 Problem Details (existing pattern):
  ```json
  { "type": "about:blank", "title": "...", "status": 503, "detail": "..." }
  ```

**Input validation (Fastify JSON schema):**
```typescript
{
  messages: {
    type: 'array',
    minItems: 1,
    maxItems: 50,               // hard limit before slicing to last 12
    items: {
      type: 'object',
      required: ['role', 'content'],
      properties: {
        role: { type: 'string', enum: ['user', 'assistant'] },
        content: { type: 'string', maxLength: 4096 }
      }
    }
  },
  contextMode: { type: 'string', enum: ['auto', 'none'], default: 'auto' }
}
```

**Hard limits applied in handler (not just schema):**
- Slice messages to **last 12** before sending to provider (system message is NOT
  counted in this 12 — it is prepended separately).
- Validate that last message has `role: 'user'` (reject if not).
- Total context sent to model ≤ ~6000 tokens estimated (system + context + messages).
  No exact token count required; stay within limits via N caps and content truncation.

**Rate limiting:**

> [ANALYSIS-П1] Concrete rate limit required. Recommended given AI latency (2–5s/reply):

```typescript
// in chat route registration:
config: { rateLimit: { max: 20, timeWindow: '1 minute' } }
```
20 req/min per user. At 3s average latency, honest use yields ~4 req/min.
If AI_API_KEY missing, rate limit still applies (returns 503 quickly).

**Provider:**
- HTTP `fetch` to provider API. No SDK dependency.
- `AI_PROVIDER` env: `openai` | `anthropic` (default `openai`)
- `AI_API_KEY` env: provider API key
- `AI_MODEL` env: model name (defaults: `gpt-4o-mini` / `claude-haiku-4-5-20251001`)
- Non-streaming only (Stage 17): both fetch call and response to client.

**New env vars to document:**
```
AI_PROVIDER=openai           # or: anthropic
AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini         # or: claude-haiku-4-5-20251001
AI_MAX_TOKENS=1024           # max output tokens (default: 1024)
AI_CONTEXT_MODE=auto         # default contextMode if not in request
```

**Error handling — provider errors → HTTP status mapping:**

> [ANALYSIS-П3] Explicit mapping required:

| Provider response | HTTP to client | `detail` |
|---|---|---|
| `AI_API_KEY` missing | 503 | "AI not configured" |
| Provider 401/403 | 503 | "AI configuration error" |
| Provider 429 | 429 | "AI rate limit reached, try again later" |
| Provider 5xx | 502 | "AI provider error" |
| `fetch` timeout / network error | 504 | "AI request timed out" |
| Empty / malformed provider response | 502 | "AI returned invalid response" |

Do NOT propagate raw provider error messages to the client (they may contain internal details).

### C) Provider implementation (`lib/ai/provider.ts`)

**TypeScript interface (mandatory — defines the contract):**

> [ANALYSIS-П5] Provider interface must be specified to ensure consistent impl:

```typescript
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AIProvider {
  /**
   * Send messages to the model and return the assistant reply text.
   * system: prepended as system-role or equivalent before messages.
   * Throws on provider errors (handler maps to HTTP status).
   */
  chat(
    messages: ChatMessage[],
    system: string,
    options?: { maxTokens?: number }
  ): Promise<string>;
}
```

**OpenAI implementation notes:**
- Endpoint: `https://api.openai.com/v1/chat/completions`
- Headers: `Authorization: Bearer ${AI_API_KEY}`, `Content-Type: application/json`
- Body: `{ model, messages: [{role:'system',content:system}, ...messages], max_tokens, stream: false }`
- Response: `choices[0].message.content`

**Anthropic implementation notes:**
- Endpoint: `https://api.anthropic.com/v1/messages`
- Headers: `x-api-key: ${AI_API_KEY}`, `anthropic-version: 2023-06-01`, `Content-Type: application/json`
- Body: `{ model, system, messages, max_tokens, stream: false }`
- Response: `content[0].text`

**Factory:**
```typescript
export function createProvider(): AIProvider {
  const provider = process.env.AI_PROVIDER ?? 'openai';
  if (provider === 'anthropic') return new AnthropicProvider();
  return new OpenAIProvider();
}
```

### D) System prompt (mandatory — defines AI behaviour)

> [ANALYSIS-K2] The system prompt is the primary control mechanism. Without it the model
> has no platform context, may hallucinate features, and will not refuse action requests
> consistently. A template must be defined.

**System prompt template** (assembled in `lib/ai/context.ts`):

```
You are an AI assistant embedded in a trading bot platform. Your role is to EXPLAIN
and HELP UNDERSTAND the platform state, errors, and data. You do NOT take actions.

RULES:
1. You MUST NOT offer to create bots, start runs, edit strategies, place orders, or
   perform any write operations. If asked, explain that actions are not yet supported
   in this chat and direct the user to the relevant UI section.
2. You MUST NOT reveal, repeat, or acknowledge any API keys, secrets, passwords, or
   encrypted credentials — even if the user explicitly asks. Direct them to
   Settings → Exchange Connections.
3. Keep answers concise and focused on the platform context provided below.
4. If context is missing or insufficient, say so rather than guessing.
5. Refer to the platform as "the platform" or by feature name (Terminal, Lab, Factory).

PLATFORM CONTEXT (workspace snapshot, read-only):
{{CONTEXT_BLOCK}}

Current time (UTC): {{TIMESTAMP}}
```

The `{{CONTEXT_BLOCK}}` is replaced with the JSON context from §3E.
The `{{TIMESTAMP}}` is `new Date().toISOString()`.

### E) Context builder (read-only, workspace-scoped)

**File:** `apps/api/src/lib/ai/context.ts`

When `contextMode=auto`, backend composes a context snapshot using **parallel Prisma queries**
with a shared 2-second timeout (fail open — if timeout, return empty context and continue).

> [ANALYSIS-K3] Correct Prisma field names (from actual schema):

```typescript
export interface WorkspaceContext {
  user: { id: string; email: string };
  workspace: { id: string };
  strategies: Array<{ id: string; name: string; status: string; updatedAt: string }>;
  bots: Array<{
    id: string; name: string; status: string;
    strategyVersionId: string;
    // exchangeConnectionId intentionally OMITTED — avoid leaking connection reference
    // that could be combined with apiKey queries
  }>;
  runs: Array<{
    id: string; botId: string; state: string;
    createdAt: string; durationMinutes: number | null; errorCode: string | null;
  }>;
  botEvents: Array<{        // [ANALYSIS-K3] table is BotEvent, field is botRunId not runId
    botRunId: string;
    type: string;
    ts: string;             // field is `ts`, not `createdAt`
    // payloadJson: OMITTED — may contain arbitrary data; include only if sanitized
  }>;
  backtests: Array<{
    id: string; status: string; symbol: string; interval: string;
    fromTs: number; toTs: number;
    // reportJson: OMITTED — too large; include only summary fields if DONE
    errorMessage: string | null;
  }>;
}
```

**N values (bounded):**
- strategies: last 5 (by `updatedAt DESC`)
- bots: last 5 (by `updatedAt DESC`)
- runs: last 10 (by `createdAt DESC`, across all bots in workspace)
- botEvents: last 20 (by `ts DESC`, for the most recent run only)
- backtests: last 5 (by `createdAt DESC`)

**Redaction (whitelist approach — safer than blacklist):**

> [ANALYSIS-K4] Use whitelist: only explicitly listed fields are included. Never include:

```typescript
// Fields NEVER included in context (extend list as schema grows):
const REDACTED_FIELDS = new Set([
  'apiKey', 'secret', 'encryptedSecret', 'passwordHash',
  'dslJson', 'executionPlanJson',   // full DSL bodies too large and not useful for explain
  'payloadJson',                      // BotEvent payload — sanitize separately if needed
  'reportJson',                       // full backtest report — too large
  'leaseOwner', 'leaseUntil',        // internal worker fields
]);
```

Use whitelist field selection in Prisma `select: {}` — do not fetch then delete fields.

**Prompt injection defense:**

> [ANALYSIS-П8] Strategy names, bot names, and event data are user-controlled strings.
> Wrap context as a clearly delimited JSON block:

```typescript
function buildContextBlock(ctx: WorkspaceContext): string {
  return [
    '--- BEGIN PLATFORM DATA (JSON) ---',
    JSON.stringify(ctx, null, 0),  // compact to save tokens
    '--- END PLATFORM DATA ---',
  ].join('\n');
}
```

The clear delimiters reduce (but do not eliminate) prompt injection risk. For Stage 17
(explain only, no tool calls) the risk is low but the practice is correct.

**Context size budget:**
- Serialized context target: ≤ 2000 chars (~500 tokens).
- If over budget, drop categories in order: botEvents → backtests → runs → strategies/bots.
- Do not include `dslJson` or `reportJson` in any case.

### F) Secret redaction / safety (mandatory)

Never send to the model:
- `apiKey` — exchange API key (stored plaintext in DB; MUST be excluded from context)
- `secret` — raw exchange secret
- `encryptedSecret` — encrypted exchange secret
- `passwordHash` — user password hash
- Any JWT token value
- `AI_API_KEY`, `SECRET_ENCRYPTION_KEY`, `JWT_SECRET` — server env vars (never in context)
- Full `dslJson` / `executionPlanJson` bodies (may contain sensitive IP or oversized)
- Full `reportJson` (backtest results — oversized)

In responses:
- If user asks to show secrets → respond with refusal text: "API keys and secrets are
  never available in chat. To view or update exchange credentials, go to
  Settings → Exchange Connections."
- This refusal is enforced both by the system prompt (rule 2) and by context redaction
  (secrets never reach the model to be parroted back).

### G) Minimal observability

Log (server-side) per request (using existing Fastify `request.log`):
```typescript
request.log.info({
  requestId: request.id,              // from Stage 13 X-Request-Id
  workspaceId: workspace.id,
  userId: request.user.sub,
  provider: process.env.AI_PROVIDER,
  model: process.env.AI_MODEL,
  latencyMs: Date.now() - startTime,
  contextMode,
  contextIncluded: contextMode === 'auto',
  messageCount: messages.length,
  // message content: NOT logged (privacy)
  // user message length for cost tracking:
  lastUserMessageLength: messages.at(-1)?.content?.length ?? 0,
}, 'ai.chat.complete');
```

Do NOT log message content in production. Log lengths only for cost monitoring.

---

## 4) Out of scope (NOT in Stage 17)

- "Actions mode": creating strategies/bots, starting runs, editing DSL (Stage 18)
- Streaming responses (SSE/WebSocket)
- Storing chat history in DB
- Multi-model selector in UI
- Voice input/output
- UI library adoption
- Per-workspace or per-user token budget enforcement (Stage 18+)
- Full backtest `reportJson` in context (future: summarise in Stage 18)
- Real-time event subscription / push to chat

---

## 5) Expected files / components

**Frontend:**
```
apps/web/src/components/chat/ChatWidget.tsx      NEW — "use client", floating button + state
apps/web/src/components/chat/ChatDrawer.tsx      NEW — panel, message list, input
apps/web/src/app/layout.tsx                      MODIFIED — add <ChatWidgetWrapper />
```

**Backend:**
```
apps/api/src/routes/ai.ts                        NEW — GET /api/v1/ai/status, POST /api/v1/ai/chat
apps/api/src/lib/ai/provider.ts                  NEW — AIProvider interface + OpenAI/Anthropic impl
apps/api/src/lib/ai/context.ts                   NEW — context builder + redaction + system prompt
apps/api/src/app.ts                              MODIFIED — register aiRoutes
```

**Docs:**
```
docs/steps/17-stage-17-ai-chat-explain.md        THIS FILE
```

**Optional:**
- OpenAPI schema update for `/api/v1/ai/*` (if OpenAPI spec exists)

---

## 6) Test approach

> [ANALYSIS-K1] CRITICAL: There is currently NO test infrastructure (no Jest/Vitest/Mocha
> config) in this codebase. The phrase "smoke-suite stays green" from previous stages
> referred to manual curl checks documented in each stage doc, NOT automated tests.

**Stage 17 does NOT require setting up a test framework.** Manual API verification
(documented in §8) replaces automated smoke tests for this stage.

If automated tests are desired (future), add Vitest to `apps/api` in a separate
infrastructure PR before Stage 17. Do not mix infrastructure setup with feature work.

**Manual verification matrix (§8) covers:**
- Auth enforcement (401 without token)
- Workspace enforcement (403 cross-workspace)
- 200 response with stubbed/real AI key
- 503 without AI_API_KEY
- Secret redaction (inspect prompt content via debug log)

---

## 7) Implementation approach (recommended)

### Provider strategy
- If `AI_API_KEY` is missing or empty → return 503 with `"AI not configured"`.
- UI checks `GET /api/v1/ai/status` on mount → shows/hides chat button.
- Do NOT crash server startup if `AI_API_KEY` missing (provider is optional).

### Context build resilience

> [ANALYSIS-П6] Context build makes 5 parallel DB queries. Use Promise.all with a timeout:

```typescript
const CONTEXT_TIMEOUT_MS = 2000;

async function buildContext(workspaceId: string, userId: string): Promise<WorkspaceContext | null> {
  try {
    const result = await Promise.race([
      fetchAllContextData(workspaceId, userId),   // Promise.all of 5 Prisma queries
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('context_timeout')), CONTEXT_TIMEOUT_MS)
      ),
    ]);
    return result as WorkspaceContext;
  } catch (err) {
    request.log.warn({ err }, 'ai.context.build.failed — proceeding without context');
    return null;  // fail open: chat proceeds without workspace context
  }
}
```

### Message history truncation
```typescript
// System message is SEPARATE — does NOT count in the 12-message limit
const recentMessages = messages.slice(-12);

// Validate last message is from user
if (recentMessages.at(-1)?.role !== 'user') {
  return reply.status(400).send(problem(400, 'Bad Request', 'Last message must be from user'));
}
```

### AI_API_KEY guard (at route level, not startup)
```typescript
// In POST /api/v1/ai/chat handler, before anything else:
if (!process.env.AI_API_KEY) {
  return reply.status(503).send(problem(503, 'Service Unavailable', 'AI not configured'));
}
```

---

## 8) Acceptance Criteria

1. **Chat button** exists on all pages (authenticated), opens chat drawer.
2. **User can send message** and receive assistant reply (or graceful error).
3. **`POST /api/v1/ai/chat`** is protected:
   - without auth → 401 (RFC 9457)
   - with auth, wrong workspace → 403
4. **Workspace safety:** context built only for the current workspace (resolveWorkspace enforced).
5. **Secret redaction:** apiKey / secret / encryptedSecret / passwordHash never appear in
   prompts (verifiable via AI_API_KEY stub + debug log) or in UI responses.
6. **Graceful degradation:**
   - without `AI_API_KEY` → `GET /ai/status` returns `{ available: false }`,
     chat button hidden or disabled; `/ai/chat` returns 503.
7. **System prompt active:** model refuses "show me my API keys" with correct redirection message.
8. **No regressions:** `next build` passes; `tsc --noEmit` passes; existing routes unaffected.

---

## 9) Verification (manual)

### A) UI
```
1. Login → any page → chat button visible in bottom-right
2. Click → drawer opens
3. Type: "Why did my last run stop?" → assistant replies with context-aware answer
4. Type: "Show me my API key" → assistant refuses with guidance to Settings
```

### B) Security / Auth
```bash
# Without auth → 401
curl -X POST http://localhost:4000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hello"}]}'
# Expected: 401 Problem Details

# With valid auth, wrong workspace → 403
curl -X POST http://localhost:4000/api/v1/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: wrong-workspace-id" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hello"}]}'
# Expected: 403 Problem Details
```

### C) AI status endpoint
```bash
curl http://localhost:4000/api/v1/ai/status
# Without AI_API_KEY: { "available": false }
# With AI_API_KEY set: { "available": true }
```

### D) No AI key
```bash
# Run server without AI_API_KEY
curl -X POST http://localhost:4000/api/v1/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hello"}]}'
# Expected: 503 "AI not configured"
# UI: chat button hidden (ai/status returned false)
```

### E) Secret redaction (debug check)
```bash
# Temporarily set NODE_ENV=development and add debug logging to context builder
# Inspect log output — confirm no apiKey/secret fields in logged context
```

---

## 10) Suggested split (recommended for lower risk)

**Stage 17a** — Chat UI shell + `GET /ai/status` + `POST /ai/chat` stub (returns canned
response, no real AI call) + auth/workspace enforcement + 401/503 UX
*(Small PR — frontend + security layer, no external dependency)*

**Stage 17b** — Provider integration (OpenAI or Anthropic via fetch) + system prompt +
error mapping table + env vars + `AI_API_KEY` guard
*(Medium PR — external API integration, well-isolated in `lib/ai/provider.ts`)*

**Stage 17c** — Context builder + redaction + system prompt interpolation + prompt injection
mitigations + observability logging
*(Medium PR — Prisma queries + security, touches `lib/ai/context.ts` only)*

Split reduces risk: 17a is fully testable without an AI key; 17b can be verified with
a real key independently; 17c adds richness without breaking 17a/17b.

---

## 11) Deliverables

- PR(s) merged to main
- `docs/steps/17-stage-17-ai-chat-explain.md` finalized (this file)
- Short stage report:
  - PR link(s)
  - changed files list
  - verification steps completed (with curl output snippets)
  - deviations from spec (if any)
  - env vars added to `.env.example` (or deployment config)
- `.env.example` updated with `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`, `AI_MAX_TOKENS`

---

## 12) Change log (v1 → v2)

| # | Issue | Fix |
|---|-------|-----|
| K1 | Smoke-suite referenced but doesn't exist | Removed automated test requirement; clarified manual verification replaces it |
| K2 | System prompt absent | Added §3D with full system prompt template and injection rules |
| K3 | BotEvent field names wrong (`runId`/`details`/`createdAt`) | Corrected to `botRunId`/`ts`/`payloadJson` per Prisma schema |
| K4 | apiKey exclusion from ExchangeConnection context unclear | Explicit: `exchangeConnectionId` omitted from bot context; whitelist approach documented |
| K5 | Next.js App Router server/client boundary not addressed | Added `ChatWidgetWrapper` pattern, component tree documented |
| K6 | Route path `/chat` without `/api/v1/` prefix | Fixed to `POST /api/v1/ai/chat`, `GET /api/v1/ai/status` |
| П1 | Rate limit not specified | Added: 20 req/min per user on `/api/v1/ai/chat` |
| П2 | Token budget vague | Added: `AI_MAX_TOKENS=1024` default; concrete per-provider notes |
| П3 | Provider error → HTTP status mapping missing | Added error mapping table in §3B |
| П4 | No AI status endpoint | Added `GET /api/v1/ai/status` (unauthenticated) |
| П5 | Provider interface not defined | Added TypeScript `AIProvider` interface in §3C |
| П6 | Context build performance / timeout | Added `Promise.race` with 2s timeout, fail-open pattern |
| П7 | localStorage privacy note missing | Added: clear chat history on logout |
| П8 | Prompt injection via user-controlled DB data | Added delimiter wrapping in `buildContextBlock()` |
