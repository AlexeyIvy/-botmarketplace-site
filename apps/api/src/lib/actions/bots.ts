/**
 * Stage 18c — Bot service functions.
 * Extracted so /ai/execute can reuse the same logic without internal HTTP calls.
 */

import { prisma } from "../prisma.js";
import { ActionValidationError, ActionConflictError, ActionNotFoundError } from "./strategies.js";

export { ActionValidationError, ActionConflictError, ActionNotFoundError };

const VALID_TIMEFRAMES = ["M1", "M5", "M15", "H1"] as const;

// ---------------------------------------------------------------------------
// Result types
// ---------------------------------------------------------------------------

export interface CreateBotResult {
  botId: string;
  name: string;
  status: string;
}

// ---------------------------------------------------------------------------
// CREATE_BOT
// ---------------------------------------------------------------------------

export async function createBot(
  workspaceId: string,
  input: Record<string, unknown>,
): Promise<CreateBotResult> {
  const { name, strategyVersionId, symbol, timeframe, exchangeConnectionId } = input;

  if (!name || typeof name !== "string") throw new ActionValidationError("name is required");
  if (!strategyVersionId || typeof strategyVersionId !== "string") {
    throw new ActionValidationError("strategyVersionId is required");
  }
  if (!symbol || typeof symbol !== "string") throw new ActionValidationError("symbol is required");
  if (!timeframe || !VALID_TIMEFRAMES.includes(timeframe as typeof VALID_TIMEFRAMES[number])) {
    throw new ActionValidationError(`timeframe must be one of: ${VALID_TIMEFRAMES.join(", ")}`);
  }

  // Cross-workspace check for strategyVersionId
  const sv = await prisma.strategyVersion.findUnique({
    where: { id: strategyVersionId },
    include: { strategy: { select: { workspaceId: true } } },
  });
  if (!sv || sv.strategy.workspaceId !== workspaceId) {
    throw new ActionNotFoundError("strategyVersionId not found in this workspace");
  }

  // Cross-workspace check for exchangeConnectionId if provided
  if (exchangeConnectionId !== undefined && exchangeConnectionId !== null && typeof exchangeConnectionId === "string") {
    const conn = await prisma.exchangeConnection.findUnique({ where: { id: exchangeConnectionId } });
    if (!conn || conn.workspaceId !== workspaceId) {
      throw new ActionNotFoundError("exchangeConnectionId not found in this workspace");
    }
  }

  // Unique name check
  const existing = await prisma.bot.findUnique({
    where: { workspaceId_name: { workspaceId, name } },
  });
  if (existing) {
    throw new ActionConflictError(`Bot "${name}" already exists in this workspace`);
  }

  const bot = await prisma.bot.create({
    data: {
      workspaceId,
      name,
      strategyVersionId,
      exchangeConnectionId: typeof exchangeConnectionId === "string" ? exchangeConnectionId : null,
      symbol: symbol as string,
      timeframe: timeframe as typeof VALID_TIMEFRAMES[number],
      status: "DRAFT",
    },
  });

  return { botId: bot.id, name: bot.name, status: bot.status };
}
