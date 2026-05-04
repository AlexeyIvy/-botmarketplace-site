import { prisma } from "../prisma.js";
import { sanitiseForPrompt } from "./sanitize.js";

// ---------------------------------------------------------------------------
// Plan context — extended workspace snapshot for /ai/plan
// Includes resource IDs so the AI can reference them in generated plans.
// Secrets (apiKey, encryptedSecret) are NEVER included.
// ---------------------------------------------------------------------------

export interface PlanContextStrategy {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  status: string;
  latestVersionId: string | null;
  latestVersion: number | null;
  updatedAt: string;
}

export interface PlanContextBot {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  status: string;
  strategyVersionId: string;
  updatedAt: string;
}

export interface PlanContextRun {
  id: string;
  botId: string;
  state: string;
  createdAt: string;
}

export interface PlanContextExchangeConnection {
  id: string;
  name: string;
  exchange: string;
  status: string;
}

export interface PlanContext {
  workspace: { id: string };
  strategies: PlanContextStrategy[];
  bots: PlanContextBot[];
  activeRuns: PlanContextRun[];
  exchangeConnections: PlanContextExchangeConnection[];
}

// ---------------------------------------------------------------------------
// Builder
// ---------------------------------------------------------------------------

const PLAN_CONTEXT_TIMEOUT_MS = 2000;

const TERMINAL_STATES = ["STOPPED", "FAILED", "TIMED_OUT"] as const;

async function fetchPlanContextData(workspaceId: string): Promise<PlanContext> {
  const [strategies, bots, activeRuns, exchangeConnections] = await Promise.all([
    // Strategies + their latest version (most recent by version number)
    prisma.strategy.findMany({
      where: { workspaceId },
      orderBy: { updatedAt: "desc" },
      take: 10,
      select: {
        id: true,
        name: true,
        symbol: true,
        timeframe: true,
        status: true,
        updatedAt: true,
        versions: {
          orderBy: { version: "desc" },
          take: 1,
          select: { id: true, version: true },
        },
      },
    }),

    // Bots — include ids so AI can reference them for START_RUN / STOP_RUN
    prisma.bot.findMany({
      where: { workspaceId },
      orderBy: { updatedAt: "desc" },
      take: 10,
      select: {
        id: true,
        name: true,
        symbol: true,
        timeframe: true,
        status: true,
        strategyVersionId: true,
        updatedAt: true,
        // exchangeConnectionId: intentionally excluded — not needed for plan generation
      },
    }),

    // Active runs only (AI needs runId to propose STOP_RUN)
    prisma.botRun.findMany({
      where: {
        workspaceId,
        state: { notIn: [...TERMINAL_STATES] },
      },
      orderBy: { createdAt: "desc" },
      take: 5,
      select: { id: true, botId: true, state: true, createdAt: true },
    }),

    // Exchange connections — id + name only, NO apiKey / encryptedSecret
    prisma.exchangeConnection.findMany({
      where: { workspaceId },
      select: {
        id: true,
        name: true,
        exchange: true,
        status: true,
      },
    }),
  ]);

  return {
    workspace: { id: workspaceId },
    strategies: strategies.map((s: {
      id: string; name: string; symbol: string; timeframe: string; status: string;
      updatedAt: Date; versions: Array<{ id: string; version: number }>;
    }) => ({
      id: s.id,
      // User-controlled — sanitise before forwarding to LLM (docs/34 §C2).
      name: sanitiseForPrompt(s.name),
      symbol: s.symbol,
      timeframe: String(s.timeframe),
      status: String(s.status),
      latestVersionId: s.versions[0]?.id ?? null,
      latestVersion: s.versions[0]?.version ?? null,
      updatedAt: s.updatedAt.toISOString(),
    })),
    bots: bots.map((b: {
      id: string; name: string; symbol: string; timeframe: string; status: string;
      strategyVersionId: string; updatedAt: Date;
    }) => ({
      id: b.id,
      name: sanitiseForPrompt(b.name),
      symbol: b.symbol,
      timeframe: String(b.timeframe),
      status: String(b.status),
      strategyVersionId: b.strategyVersionId,
      updatedAt: b.updatedAt.toISOString(),
    })),
    activeRuns: activeRuns.map((r: {
      id: string; botId: string; state: string; createdAt: Date;
    }) => ({
      id: r.id,
      botId: r.botId,
      state: String(r.state),
      createdAt: r.createdAt.toISOString(),
    })),
    exchangeConnections: exchangeConnections.map((ec: {
      id: string; name: string; exchange: string; status: string;
    }) => ({
      id: ec.id,
      name: sanitiseForPrompt(ec.name),
      exchange: ec.exchange,
      status: String(ec.status),
    })),
  };
}

/**
 * Build plan-mode workspace context. Fails open: returns null on timeout
 * and the caller proceeds with an empty context (AI will note it's unavailable).
 */
export async function buildPlanContext(workspaceId: string): Promise<PlanContext | null> {
  try {
    return await Promise.race([
      fetchPlanContextData(workspaceId),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error("plan_context_timeout")), PLAN_CONTEXT_TIMEOUT_MS),
      ),
    ]);
  } catch {
    return null;
  }
}

export function serializePlanContext(ctx: PlanContext | null): string {
  if (!ctx) return "(context unavailable — propose actions referencing no specific IDs)";
  return JSON.stringify(ctx);
}
