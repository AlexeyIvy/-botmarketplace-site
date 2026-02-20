/**
 * Bot Run State Machine
 *
 * Enforces valid state transitions and atomically logs each transition
 * as a BotEvent. All state changes MUST go through `transition()`.
 */

import type { BotRunState } from "@prisma/client";
import { prisma as defaultPrisma } from "./prisma.js";

// ---------------------------------------------------------------------------
// Transition graph
// ---------------------------------------------------------------------------

const TRANSITIONS: Record<BotRunState, readonly BotRunState[]> = {
  CREATED:   ["QUEUED"],
  QUEUED:    ["STARTING", "FAILED"],
  STARTING:  ["SYNCING", "STOPPING", "FAILED", "TIMED_OUT"],
  SYNCING:   ["RUNNING", "STOPPING", "FAILED", "TIMED_OUT"],
  RUNNING:   ["STOPPING", "FAILED", "TIMED_OUT"],
  STOPPING:  ["STOPPED", "FAILED"],
  STOPPED:   [],
  FAILED:    [],
  TIMED_OUT: [],
};

export const TERMINAL_STATES: ReadonlySet<BotRunState> = new Set([
  "STOPPED",
  "FAILED",
  "TIMED_OUT",
]);

export function isTerminalState(state: BotRunState): boolean {
  return TERMINAL_STATES.has(state);
}

export function isValidTransition(from: BotRunState, to: BotRunState): boolean {
  return (TRANSITIONS[from] as readonly BotRunState[]).includes(to);
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class InvalidTransitionError extends Error {
  constructor(
    public readonly from: BotRunState,
    public readonly to: BotRunState,
  ) {
    super(`Invalid state transition: ${from} → ${to}`);
    this.name = "InvalidTransitionError";
  }
}

export class RunNotFoundError extends Error {
  constructor(public readonly runId: string) {
    super(`BotRun not found: ${runId}`);
    this.name = "RunNotFoundError";
  }
}

// ---------------------------------------------------------------------------
// Transition function
// ---------------------------------------------------------------------------

export interface TransitionOptions {
  /** Short label for the BotEvent.type field, e.g. "RUN_STARTING" */
  eventType?: string;
  /** Human-readable message for BotEvent.payloadJson.message */
  message?: string;
  /** Extra fields merged into BotEvent.payloadJson */
  meta?: Record<string, unknown>;
  /** If provided, also set stoppedAt on terminal transitions */
  stoppedAt?: Date;
  /** If provided, also set startedAt when transitioning to RUNNING */
  startedAt?: Date;
  /** If provided, set errorCode on FAILED/TIMED_OUT */
  errorCode?: string;
}

export interface TransitionResult {
  id: string;
  state: BotRunState;
  stoppedAt: Date | null;
  startedAt: Date | null;
  errorCode: string | null;
  updatedAt: Date;
}

/**
 * Atomically transition a BotRun to a new state and record the event.
 *
 * @throws {RunNotFoundError}       if runId doesn't exist
 * @throws {InvalidTransitionError} if the transition is not allowed
 */
export async function transition(
  runId: string,
  to: BotRunState,
  options: TransitionOptions = {},
): Promise<TransitionResult> {
  const run = await defaultPrisma.botRun.findUnique({ where: { id: runId } });
  if (!run) throw new RunNotFoundError(runId);

  const from = run.state;
  if (!isValidTransition(from, to)) {
    throw new InvalidTransitionError(from, to);
  }

  const now = new Date();
  const eventType = options.eventType ?? `RUN_${to}`;
  const payload: Record<string, unknown> = {
    from,
    to,
    message: options.message ?? `State transition: ${from} → ${to}`,
    at: now.toISOString(),
    ...(options.meta ?? {}),
  };

  const updateData: Record<string, unknown> = { state: to };
  if (to === "RUNNING" && options.startedAt) updateData.startedAt = options.startedAt;
  if (isTerminalState(to)) {
    updateData.stoppedAt = options.stoppedAt ?? now;
    if (options.errorCode) updateData.errorCode = options.errorCode;
  }

  const updated = await defaultPrisma.$transaction(async (tx) => {
    const result = await tx.botRun.update({
      where: { id: runId },
      data: updateData,
      select: {
        id: true,
        state: true,
        stoppedAt: true,
        startedAt: true,
        errorCode: true,
        updatedAt: true,
      },
    });

    await tx.botEvent.create({
      data: {
        botRunId: runId,
        type: eventType,
        payloadJson: payload,
      },
    });

    return result;
  });

  return updated as TransitionResult;
}
