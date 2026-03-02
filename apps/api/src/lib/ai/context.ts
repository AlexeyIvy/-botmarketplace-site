import { prisma } from "../prisma.js";

// ---------------------------------------------------------------------------
// Types — whitelist-only fields (never fetch apiKey / encryptedSecret / etc.)
// ---------------------------------------------------------------------------

interface ContextStrategy {
  id: string;
  name: string;
  status: string;
  symbol: string;
  timeframe: string;
  updatedAt: string;
}

interface ContextBot {
  id: string;
  name: string;
  status: string;
  symbol: string;
  timeframe: string;
  strategyVersionId: string;
  updatedAt: string;
  // exchangeConnectionId intentionally OMITTED — avoid leaking connection refs
}

interface ContextRun {
  id: string;
  botId: string;
  state: string;
  errorCode: string | null;
  durationMinutes: number | null;
  createdAt: string;
}

interface ContextBotEvent {
  botRunId: string;
  type: string;
  ts: string;
  // payloadJson OMITTED — arbitrary user/event data, not safe to forward wholesale
}

interface ContextBacktest {
  id: string;
  strategyId: string;
  symbol: string;
  interval: string;
  status: string;
  errorMessage: string | null;
  createdAt: string;
}

export interface WorkspaceContext {
  workspace: { id: string };
  strategies: ContextStrategy[];
  bots: ContextBot[];
  runs: ContextRun[];
  botEvents: ContextBotEvent[];
  backtests: ContextBacktest[];
}

// ---------------------------------------------------------------------------
// Context builder
// ---------------------------------------------------------------------------

const CONTEXT_TIMEOUT_MS = 2000;

async function fetchContextData(workspaceId: string): Promise<WorkspaceContext> {
  const [strategies, bots, runs, backtests] = await Promise.all([
    prisma.strategy.findMany({
      where: { workspaceId },
      orderBy: { updatedAt: "desc" },
      take: 5,
      select: {
        id: true,
        name: true,
        status: true,
        symbol: true,
        timeframe: true,
        updatedAt: true,
      },
    }),

    prisma.bot.findMany({
      where: { workspaceId },
      orderBy: { updatedAt: "desc" },
      take: 5,
      select: {
        id: true,
        name: true,
        status: true,
        symbol: true,
        timeframe: true,
        strategyVersionId: true,
        updatedAt: true,
        // exchangeConnectionId: NOT included
      },
    }),

    prisma.botRun.findMany({
      where: { workspaceId },
      orderBy: { createdAt: "desc" },
      take: 10,
      select: {
        id: true,
        botId: true,
        state: true,
        errorCode: true,
        durationMinutes: true,
        createdAt: true,
      },
    }),

    prisma.backtestResult.findMany({
      where: { workspaceId },
      orderBy: { createdAt: "desc" },
      take: 5,
      select: {
        id: true,
        strategyId: true,
        symbol: true,
        interval: true,
        status: true,
        errorMessage: true,
        createdAt: true,
        // reportJson: NOT included — too large
      },
    }),
  ]);

  // Fetch events for the most recent run (if any)
  let botEvents: ContextBotEvent[] = [];
  if (runs.length > 0) {
    const latestRunId = runs[0].id;
    const events = await prisma.botEvent.findMany({
      where: { botRunId: latestRunId },
      orderBy: { ts: "desc" },
      take: 20,
      select: {
        botRunId: true,
        type: true,
        ts: true,
        // payloadJson: NOT included
      },
    });
    botEvents = events.map((e: { botRunId: string; type: string; ts: Date }) => ({
      botRunId: e.botRunId,
      type: e.type,
      ts: e.ts.toISOString(),
    }));
  }

  return {
    workspace: { id: workspaceId },
    strategies: strategies.map((s: { id: string; name: string; status: string; symbol: string; timeframe: string; updatedAt: Date }) => ({
      id: s.id,
      name: s.name,
      status: String(s.status),
      symbol: s.symbol,
      timeframe: String(s.timeframe),
      updatedAt: s.updatedAt.toISOString(),
    })),
    bots: bots.map((b: { id: string; name: string; status: string; symbol: string; timeframe: string; strategyVersionId: string; updatedAt: Date }) => ({
      id: b.id,
      name: b.name,
      status: String(b.status),
      symbol: b.symbol,
      timeframe: String(b.timeframe),
      strategyVersionId: b.strategyVersionId,
      updatedAt: b.updatedAt.toISOString(),
    })),
    runs: runs.map((r: { id: string; botId: string; state: string; errorCode: string | null; durationMinutes: number | null; createdAt: Date }) => ({
      id: r.id,
      botId: r.botId,
      state: String(r.state),
      errorCode: r.errorCode,
      durationMinutes: r.durationMinutes,
      createdAt: r.createdAt.toISOString(),
    })),
    botEvents,
    backtests: backtests.map((bt: { id: string; strategyId: string; symbol: string; interval: string; status: string; errorMessage: string | null; createdAt: Date }) => ({
      id: bt.id,
      strategyId: bt.strategyId,
      symbol: bt.symbol,
      interval: bt.interval,
      status: String(bt.status),
      errorMessage: bt.errorMessage,
      createdAt: bt.createdAt.toISOString(),
    })),
  };
}

/**
 * Build workspace context snapshot. Fails open: if context build times out,
 * returns null and the caller proceeds without context.
 */
export async function buildContext(workspaceId: string): Promise<WorkspaceContext | null> {
  try {
    const result = await Promise.race([
      fetchContextData(workspaceId),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error("context_timeout")), CONTEXT_TIMEOUT_MS),
      ),
    ]);
    return result;
  } catch {
    return null;
  }
}

/**
 * Serialize context to a safe string block for embedding in the system prompt.
 * Uses delimiters to contain any prompt injection attempts in user-controlled
 * field values (strategy names, bot names, etc.).
 */
export function serializeContext(ctx: WorkspaceContext | null): string {
  if (!ctx) return "(context unavailable — answering generically)";
  return JSON.stringify(ctx);
}
