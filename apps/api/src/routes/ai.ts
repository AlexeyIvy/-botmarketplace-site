import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { buildContext, serializeContext } from "../lib/ai/context.js";
import { buildSystemPrompt } from "../lib/ai/prompt.js";
import { buildPlanContext, serializePlanContext } from "../lib/ai/planContext.js";
import { buildPlanSystemPrompt } from "../lib/ai/planPrompt.js";
import { parsePlanResponse, buildActionPlan, type ActionItem } from "../lib/ai/planParser.js";
import { createProvider, getConfiguredModel, ProviderError } from "../lib/ai/provider.js";
import {
  createStrategy,
  validateDslAction,
  createStrategyVersion,
  ActionValidationError,
  ActionConflictError,
  ActionNotFoundError,
} from "../lib/actions/strategies.js";
import { runBacktestAction } from "../lib/actions/lab.js";
import { createBot } from "../lib/actions/bots.js";
import { startRun, stopRun } from "../lib/actions/runs.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatBody {
  messages: ChatMessage[];
  contextMode?: "auto" | "none";
}

interface PlanBody {
  message: string;
  contextMode?: "auto" | "none";
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MAX_HISTORY = 12;
const MAX_TOKENS = parseInt(process.env.AI_MAX_TOKENS ?? "1024", 10);

/**
 * Map provider HTTP status to our API status.
 * Hides internal provider details from clients.
 */
function providerStatusToHttp(providerStatus: number): {
  status: number;
  title: string;
  detail: string;
} {
  if (providerStatus === 429) {
    return { status: 429, title: "Too Many Requests", detail: "AI rate limit reached, try again later" };
  }
  if (providerStatus >= 500) {
    return { status: 502, title: "Bad Gateway", detail: "AI provider error" };
  }
  if (providerStatus === 401 || providerStatus === 403) {
    return { status: 503, title: "Service Unavailable", detail: "AI configuration error" };
  }
  if (providerStatus === 502) {
    return { status: 502, title: "Bad Gateway", detail: "AI returned invalid response" };
  }
  return { status: 502, title: "Bad Gateway", detail: "AI provider error" };
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function aiRoutes(app: FastifyInstance) {
  // ── GET /ai/status ────────────────────────────────────────────────────────
  // Unauthenticated probe so the UI can hide the chat button when AI is not configured.
  app.get("/ai/status", async (_request, reply) => {
    const available = !!process.env.AI_API_KEY;
    if (!available) {
      return reply.send({ available: false });
    }
    return reply.send({
      available: true,
      provider: process.env.AI_PROVIDER ?? "openai",
      model: getConfiguredModel(),
    });
  });

  // ── POST /ai/chat ─────────────────────────────────────────────────────────
  app.post<{ Body: ChatBody }>(
    "/ai/chat",
    {
      config: { rateLimit: { max: 20, timeWindow: "1 minute" } },
      onRequest: [app.authenticate],
    },
    async (request, reply) => {
      const startTime = Date.now();

      // Guard: AI must be configured
      if (!process.env.AI_API_KEY) {
        return problem(reply, 503, "Service Unavailable", "AI not configured");
      }

      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const { messages = [], contextMode = "auto" } = request.body ?? {};

      // Validate input
      if (!Array.isArray(messages) || messages.length === 0) {
        return problem(reply, 400, "Bad Request", "messages array is required and must not be empty");
      }

      // Validate each message
      for (const msg of messages) {
        if (!msg.role || !["user", "assistant"].includes(msg.role)) {
          return problem(reply, 400, "Bad Request", "Each message must have role 'user' or 'assistant'");
        }
        if (typeof msg.content !== "string" || msg.content.length === 0) {
          return problem(reply, 400, "Bad Request", "Each message must have non-empty string content");
        }
        if (msg.content.length > 4096) {
          return problem(reply, 400, "Bad Request", "Message content exceeds 4096 character limit");
        }
      }

      // Slice to last MAX_HISTORY messages
      const recentMessages = messages.slice(-MAX_HISTORY);

      // Last message must be from user
      if (recentMessages.at(-1)?.role !== "user") {
        return problem(reply, 400, "Bad Request", "Last message must be from user");
      }

      const userId = (request.user as { sub?: string })?.sub ?? "unknown";

      // Build context (fail-open on timeout)
      const ctx = contextMode === "auto"
        ? await buildContext(workspace.id)
        : null;

      const contextIncluded = ctx !== null && contextMode === "auto";

      // Assemble system prompt
      const systemPrompt = buildSystemPrompt(serializeContext(ctx));

      // Call provider
      const provider = createProvider();
      let reply_text: string;

      try {
        reply_text = await provider.chat(recentMessages, systemPrompt, { maxTokens: MAX_TOKENS });
      } catch (err) {
        const latencyMs = Date.now() - startTime;

        if (err instanceof ProviderError) {
          request.log.warn(
            { reqId: request.id, workspaceId: workspace.id, userId, latencyMs, providerStatus: err.providerStatus },
            "ai.chat.provider_error",
          );
          const mapped = providerStatusToHttp(err.providerStatus);
          return problem(reply, mapped.status, mapped.title, mapped.detail);
        }

        // Network timeout (AbortSignal fires DOMException)
        const isTimeout =
          err instanceof Error &&
          (err.name === "TimeoutError" || err.name === "AbortError" || err.message.includes("timed out"));

        if (isTimeout) {
          request.log.warn(
            { reqId: request.id, workspaceId: workspace.id, userId, latencyMs },
            "ai.chat.timeout",
          );
          return problem(reply, 504, "Gateway Timeout", "AI request timed out");
        }

        request.log.error(
          { err, reqId: request.id, workspaceId: workspace.id, userId, latencyMs },
          "ai.chat.unexpected_error",
        );
        return problem(reply, 502, "Bad Gateway", "AI provider error");
      }

      const latencyMs = Date.now() - startTime;
      request.log.info(
        {
          reqId: request.id,
          workspaceId: workspace.id,
          userId,
          provider: process.env.AI_PROVIDER ?? "openai",
          model: getConfiguredModel(),
          latencyMs,
          contextMode,
          contextIncluded,
          messageCount: recentMessages.length,
          lastUserMessageLength: recentMessages.at(-1)?.content?.length ?? 0,
        },
        "ai.chat.complete",
      );

      return reply.send({ reply: reply_text, requestId: request.id });
    },
  );

  // ── POST /ai/plan ─────────────────────────────────────────────────────────
  // Stage 18a: generate a structured action plan from a user message.
  // Returns ActionPlan JSON. Execution is handled by /ai/execute (Stage 18b).
  app.post<{ Body: PlanBody }>(
    "/ai/plan",
    {
      config: { rateLimit: { max: 20, timeWindow: "1 minute" } },
      onRequest: [app.authenticate],
    },
    async (request, reply) => {
      const startTime = Date.now();

      if (!process.env.AI_API_KEY) {
        return problem(reply, 503, "Service Unavailable", "AI not configured");
      }

      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const { message, contextMode = "auto" } = request.body ?? {};

      if (typeof message !== "string" || message.trim().length === 0) {
        return problem(reply, 400, "Bad Request", "message is required and must not be empty");
      }
      if (message.length > 2000) {
        return problem(reply, 400, "Bad Request", "message exceeds 2000 character limit");
      }

      const userId = (request.user as { sub?: string })?.sub ?? "unknown";

      // Build plan-mode context (includes resource IDs)
      const ctx = contextMode === "auto" ? await buildPlanContext(workspace.id) : null;
      const contextBlock = serializePlanContext(ctx);
      const systemPrompt = buildPlanSystemPrompt(contextBlock);

      // Call provider in JSON mode
      const provider = createProvider();
      let rawPlan: string;

      try {
        rawPlan = await provider.chat(
          [{ role: "user", content: message }],
          systemPrompt,
          { maxTokens: 2048, jsonMode: true },
        );
      } catch (err) {
        const latencyMs = Date.now() - startTime;

        if (err instanceof ProviderError) {
          request.log.warn(
            { reqId: request.id, workspaceId: workspace.id, userId, latencyMs, providerStatus: err.providerStatus },
            "ai.plan.provider_error",
          );
          const mapped = providerStatusToHttp(err.providerStatus);
          return problem(reply, mapped.status, mapped.title, mapped.detail);
        }

        const isTimeout =
          err instanceof Error &&
          (err.name === "TimeoutError" || err.name === "AbortError" || err.message.includes("timed out"));

        if (isTimeout) {
          return problem(reply, 504, "Gateway Timeout", "AI request timed out");
        }

        request.log.error({ err, reqId: request.id, workspaceId: workspace.id, userId, latencyMs }, "ai.plan.unexpected_error");
        return problem(reply, 502, "Bad Gateway", "AI provider error");
      }

      // Parse and validate the plan
      const parseResult = parsePlanResponse(rawPlan);
      if (!parseResult.ok) {
        request.log.warn(
          { reqId: request.id, workspaceId: workspace.id, userId, reason: parseResult.reason },
          "ai.plan.parse_error",
        );
        return problem(reply, 502, "Bad Gateway", `AI returned invalid plan: ${parseResult.reason}`);
      }

      // Persist to DB — planId comes from the DB record
      const expiresAt = new Date(Date.now() + 30 * 60 * 1000);
      const planRecord = await prisma.aiPlan.create({
        data: {
          workspaceId: workspace.id,
          userId,
          expiresAt,
          planJson: {
            actions: parseResult.actions,
            note: parseResult.note ?? null,
          } as object,
          requestId: request.id,
        },
      });

      const plan = buildActionPlan(planRecord.id, parseResult.actions, parseResult.note);

      const latencyMs = Date.now() - startTime;
      request.log.info(
        {
          reqId: request.id,
          workspaceId: workspace.id,
          userId,
          planId: planRecord.id,
          actionCount: parseResult.actions.length,
          latencyMs,
        },
        "ai.plan.complete",
      );

      return reply.send(plan);
    },
  );

  // ── POST /ai/execute ──────────────────────────────────────────────────────
  // Stage 18b: execute a single confirmed action from a stored plan.
  app.post<{ Body: { planId: string; actionId: string } }>(
    "/ai/execute",
    {
      config: { rateLimit: { max: 15, timeWindow: "1 minute" } },
      onRequest: [app.authenticate],
    },
    async (request, reply) => {
      if (!process.env.AI_API_KEY) {
        return problem(reply, 503, "Service Unavailable", "AI not configured");
      }

      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const { planId, actionId } = request.body ?? {};
      if (!planId || typeof planId !== "string") {
        return problem(reply, 400, "Bad Request", "planId is required");
      }
      if (!actionId || typeof actionId !== "string") {
        return problem(reply, 400, "Bad Request", "actionId is required");
      }

      const userId = (request.user as { sub?: string })?.sub ?? "unknown";

      // 1. Load plan from DB
      const planRecord = await prisma.aiPlan.findUnique({ where: { id: planId } });
      if (!planRecord) {
        return problem(reply, 404, "Not Found", "Plan not found");
      }

      // 2. Verify ownership
      if (planRecord.workspaceId !== workspace.id) {
        return problem(reply, 403, "Forbidden", "Plan does not belong to this workspace");
      }

      // 3. Check TTL
      if (new Date() > planRecord.expiresAt) {
        return problem(reply, 410, "Gone", "Plan has expired — please create a new plan");
      }

      // 4. Find action in stored plan
      const planJson = planRecord.planJson as { actions: ActionItem[]; note?: string };
      const action = planJson.actions?.find((a: ActionItem) => a.actionId === actionId);
      if (!action) {
        return problem(reply, 404, "Not Found", "Action not found in plan");
      }

      // 5. Check only allowlisted types (belt-and-suspenders)
      const ALLOWED_ACTION_TYPES = new Set([
        "CREATE_STRATEGY", "VALIDATE_DSL", "CREATE_STRATEGY_VERSION", "RUN_BACKTEST",
        "CREATE_BOT", "START_RUN", "STOP_RUN",
      ]);
      if (!ALLOWED_ACTION_TYPES.has(action.type)) {
        return problem(reply, 400, "Bad Request", `Action type "${action.type}" is not supported in this version`);
      }

      // 6. Check existing audit record for this action — prevent double-execution
      const existingAudit = await prisma.aiActionAudit.findFirst({
        where: { planId, actionId },
      });
      if (existingAudit?.status === "EXECUTED") {
        return problem(reply, 409, "Conflict", "Action has already been executed");
      }
      if (existingAudit?.status === "CANCELLED") {
        return problem(reply, 409, "Conflict", "Action was cancelled");
      }

      // 7. Check dependsOn — all must be EXECUTED
      if (action.dependsOn && action.dependsOn.length > 0) {
        for (const depId of action.dependsOn) {
          const depAudit = await prisma.aiActionAudit.findFirst({
            where: { planId, actionId: depId, status: "EXECUTED" },
          });
          if (!depAudit) {
            const depAction = planJson.actions?.find((a: ActionItem) => a.actionId === depId);
            const depTitle = depAction?.title ?? depId.slice(0, 8);
            return problem(reply, 409, "Conflict", `Dependency "${depTitle}" must be executed first`);
          }
        }
      }

      // 8. Resolve __FROM:{actionId}:{field}__ placeholders in stored input
      const resolvedInput = await resolvePlaceholders(action.input, planId);

      // 8b. Secret-key scanner — belt-and-suspenders against prompt injection
      const leakedKey = findSecretKey(resolvedInput);
      if (leakedKey) {
        request.log.warn(
          { planId, actionId, actionType: action.type, workspaceId: workspace.id, leakedKey },
          "ai.execute.secret_key_detected",
        );
        return problem(reply, 400, "Bad Request", `Action input contains disallowed key: "${leakedKey}"`);
      }

      // 9. Create PROPOSED audit record (or reuse existing PROPOSED one)
      const auditRecord = existingAudit ?? await prisma.aiActionAudit.create({
        data: {
          planId,
          workspaceId: workspace.id,
          userId,
          actionId,
          actionType: action.type,
          inputJson: resolvedInput as object,
          requestId: request.id,
        },
      });

      // 10. Execute the action
      let result: Record<string, unknown>;
      try {
        result = await dispatchAction(action.type, workspace.id, resolvedInput);
      } catch (err) {
        const detail = err instanceof ActionValidationError || err instanceof ActionConflictError || err instanceof ActionNotFoundError
          ? err.detail
          : "Action execution failed";
        const httpStatus = err instanceof ActionNotFoundError ? 404
          : err instanceof ActionConflictError ? 409
          : 400;

        await prisma.aiActionAudit.update({
          where: { id: auditRecord.id },
          data: { status: "FAILED", resultJson: { error: detail } as object },
        });

        request.log.warn(
          { planId, actionId, actionType: action.type, workspaceId: workspace.id, err },
          "ai.execute.action_failed",
        );
        return problem(reply, httpStatus, "Action Failed", detail);
      }

      // 11. Mark EXECUTED in audit
      await prisma.aiActionAudit.update({
        where: { id: auditRecord.id },
        data: {
          status: "EXECUTED",
          resultJson: result as object,
          executedAt: new Date(),
        },
      });

      request.log.info(
        { planId, actionId, actionType: action.type, workspaceId: workspace.id, userId },
        "ai.execute.complete",
      );

      return reply.send({
        actionId,
        type: action.type,
        status: "EXECUTED",
        result,
        executedAt: new Date().toISOString(),
      });
    },
  );
}

// ---------------------------------------------------------------------------
// Execute dispatcher — routes action type to service function
// ---------------------------------------------------------------------------

const PLACEHOLDER_RE = /^__FROM:([0-9a-f-]+):([a-zA-Z_]+)__$/;

/** Return the first key that looks like a secret, or null if clean. */
const SECRET_KEY_RE = /api.?key|secret|password|token|encrypted/i;
function findSecretKey(input: Record<string, unknown>): string | null {
  for (const key of Object.keys(input)) {
    if (SECRET_KEY_RE.test(key)) return key;
  }
  return null;
}

/**
 * Replace __FROM:{actionId}:{field}__ placeholders in the action input
 * by looking up the result of the dependency's AiActionAudit record.
 */
async function resolvePlaceholders(
  input: Record<string, unknown>,
  planId: string,
): Promise<Record<string, unknown>> {
  const resolved: Record<string, unknown> = { ...input };
  for (const [key, value] of Object.entries(input)) {
    if (typeof value === "string") {
      const match = value.match(PLACEHOLDER_RE);
      if (match) {
        const [, depActionId, field] = match;
        const depAudit = await prisma.aiActionAudit.findFirst({
          where: { planId, actionId: depActionId, status: "EXECUTED" },
        });
        if (depAudit?.resultJson && typeof depAudit.resultJson === "object") {
          const depResult = depAudit.resultJson as Record<string, unknown>;
          resolved[key] = depResult[field] ?? value;
        }
      }
    }
  }
  return resolved;
}

async function dispatchAction(
  type: string,
  workspaceId: string,
  input: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  switch (type) {
    case "CREATE_STRATEGY":
      return createStrategy(workspaceId, input) as unknown as Record<string, unknown>;
    case "VALIDATE_DSL":
      return validateDslAction(workspaceId, input) as unknown as Record<string, unknown>;
    case "CREATE_STRATEGY_VERSION":
      return createStrategyVersion(workspaceId, input) as unknown as Record<string, unknown>;
    case "RUN_BACKTEST":
      return runBacktestAction(workspaceId, input) as unknown as Record<string, unknown>;
    case "CREATE_BOT":
      return createBot(workspaceId, input) as unknown as Record<string, unknown>;
    case "START_RUN":
      return startRun(workspaceId, input) as unknown as Record<string, unknown>;
    case "STOP_RUN":
      return stopRun(workspaceId, input) as unknown as Record<string, unknown>;
    default:
      throw new ActionValidationError(`Unsupported action type: ${type}`);
  }
}
