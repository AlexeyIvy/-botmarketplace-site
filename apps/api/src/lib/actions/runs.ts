/**
 * Stage 18c — Run service functions.
 * Extracted so /ai/execute can reuse the same logic without internal HTTP calls.
 */

import { prisma } from "../prisma.js";
import { ActionValidationError, ActionConflictError, ActionNotFoundError } from "./strategies.js";
import {
  transition,
  isTerminalState,
  isValidTransition,
  InvalidTransitionError,
} from "../stateMachine.js";

export { ActionValidationError, ActionConflictError, ActionNotFoundError };

// ---------------------------------------------------------------------------
// Result types
// ---------------------------------------------------------------------------

export interface StartRunResult {
  runId: string;
  state: string;
}

export interface StopRunResult {
  runId: string;
  state: string;
}

// ---------------------------------------------------------------------------
// START_RUN
// ---------------------------------------------------------------------------

export async function startRun(
  workspaceId: string,
  input: Record<string, unknown>,
): Promise<StartRunResult> {
  const { botId, durationMinutes } = input;

  if (!botId || typeof botId !== "string") throw new ActionValidationError("botId is required");
  if (durationMinutes !== undefined && durationMinutes !== null) {
    if (!Number.isInteger(durationMinutes) || (durationMinutes as number) < 1 || (durationMinutes as number) > 1440) {
      throw new ActionValidationError("durationMinutes must be an integer between 1 and 1440");
    }
  }

  // Cross-workspace check
  const bot = await prisma.bot.findUnique({ where: { id: botId } });
  if (!bot || bot.workspaceId !== workspaceId) {
    throw new ActionNotFoundError("Bot not found");
  }

  // Single-active-run invariant
  const activeRun = await prisma.botRun.findFirst({
    where: {
      botId: bot.id,
      state: { notIn: ["STOPPED", "FAILED", "TIMED_OUT"] },
    },
  });
  if (activeRun) {
    throw new ActionConflictError("An active run already exists for this bot");
  }

  let run;
  try {
    run = await prisma.$transaction(async (tx) => {
      const created = await tx.botRun.create({
        data: {
          botId: bot.id,
          workspaceId: bot.workspaceId,
          symbol: bot.symbol,
          state: "CREATED",
          durationMinutes: typeof durationMinutes === "number" ? durationMinutes : null,
        },
      });

      await tx.botEvent.create({
        data: {
          botRunId: created.id,
          type: "RUN_CREATED",
          payloadJson: {
            from: null,
            to: "CREATED",
            message: "Run created via AI action",
            durationMinutes: durationMinutes ?? null,
            at: new Date().toISOString(),
          },
        },
      });

      return created;
    });
  } catch (err) {
    if ((err as { code?: string })?.code === "P2002") {
      throw new ActionConflictError(`An active run for symbol ${bot.symbol} already exists in this workspace`);
    }
    throw err;
  }

  await transition(run.id, "QUEUED", {
    eventType: "RUN_QUEUED",
    message: "Run queued via AI action",
  });

  const fresh = await prisma.botRun.findUnique({ where: { id: run.id } });
  return { runId: fresh!.id, state: fresh!.state };
}

// ---------------------------------------------------------------------------
// STOP_RUN
// ---------------------------------------------------------------------------

export async function stopRun(
  workspaceId: string,
  input: Record<string, unknown>,
): Promise<StopRunResult> {
  const { botId, runId } = input;

  if (!botId || typeof botId !== "string") throw new ActionValidationError("botId is required");
  if (!runId || typeof runId !== "string") throw new ActionValidationError("runId is required");

  // Cross-workspace check for bot
  const bot = await prisma.bot.findUnique({ where: { id: botId } });
  if (!bot || bot.workspaceId !== workspaceId) {
    throw new ActionNotFoundError("Bot not found");
  }

  // Verify run belongs to this bot
  const run = await prisma.botRun.findUnique({ where: { id: runId } });
  if (!run || run.botId !== bot.id) {
    throw new ActionNotFoundError("Run not found");
  }

  if (isTerminalState(run.state)) {
    throw new ActionConflictError(`Run is already in terminal state: ${run.state}`);
  }

  try {
    let updated;
    if (isValidTransition(run.state, "STOPPING")) {
      await transition(run.id, "STOPPING", {
        eventType: "RUN_STOPPING",
        message: "Stop requested via AI action",
      });
      updated = await transition(run.id, "STOPPED", {
        eventType: "RUN_STOPPED",
        message: "Run stopped via AI action",
      });
    } else {
      updated = await transition(run.id, "STOPPED", {
        eventType: "RUN_STOPPED",
        message: "Run stopped via AI action",
      });
    }
    return { runId: updated.id, state: updated.state };
  } catch (err) {
    if (err instanceof InvalidTransitionError) {
      throw new ActionConflictError(err.message);
    }
    throw err;
  }
}
