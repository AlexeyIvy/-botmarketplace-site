import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { buildContext, serializeContext } from "../lib/ai/context.js";
import { buildSystemPrompt } from "../lib/ai/prompt.js";
import { buildPlanContext, serializePlanContext } from "../lib/ai/planContext.js";
import { buildPlanSystemPrompt } from "../lib/ai/planPrompt.js";
import { parsePlanResponse, buildActionPlan } from "../lib/ai/planParser.js";
import { createProvider, getConfiguredModel, ProviderError } from "../lib/ai/provider.js";

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
}
