/**
 * Stage 18b — Strategy service functions.
 * Extracted from strategyRoutes so /ai/execute can reuse the same logic
 * without making internal HTTP calls.
 */

import { prisma } from "../prisma.js";
import { validateDsl } from "../dslValidator.js";

const VALID_TIMEFRAMES = ["M1", "M5", "M15", "H1"] as const;

// ---------------------------------------------------------------------------
// Result types
// ---------------------------------------------------------------------------

export interface CreateStrategyResult {
  strategyId: string;
  name: string;
  status: string;
}

export interface ValidateDslResult {
  ok: boolean;
  errors?: Array<{ field: string; message: string }>;
}

export interface CreateStrategyVersionResult {
  versionId: string;
  version: number;
}

// ---------------------------------------------------------------------------
// Service errors
// ---------------------------------------------------------------------------

export class ActionValidationError extends Error {
  constructor(public readonly detail: string) {
    super(detail);
    this.name = "ActionValidationError";
  }
}

export class ActionConflictError extends Error {
  constructor(public readonly detail: string) {
    super(detail);
    this.name = "ActionConflictError";
  }
}

export class ActionNotFoundError extends Error {
  constructor(public readonly detail: string) {
    super(detail);
    this.name = "ActionNotFoundError";
  }
}

// ---------------------------------------------------------------------------
// CREATE_STRATEGY
// ---------------------------------------------------------------------------

export async function createStrategy(
  workspaceId: string,
  input: Record<string, unknown>,
): Promise<CreateStrategyResult> {
  const name = input.name;
  const symbol = input.symbol;
  const timeframe = input.timeframe;

  if (!name || typeof name !== "string") throw new ActionValidationError("name is required");
  if (!symbol || typeof symbol !== "string") throw new ActionValidationError("symbol is required");
  if (!timeframe || !VALID_TIMEFRAMES.includes(timeframe as typeof VALID_TIMEFRAMES[number])) {
    throw new ActionValidationError(`timeframe must be one of: ${VALID_TIMEFRAMES.join(", ")}`);
  }

  const existing = await prisma.strategy.findUnique({
    where: { workspaceId_name: { workspaceId, name } },
  });
  if (existing) {
    throw new ActionConflictError(`Strategy "${name}" already exists in this workspace`);
  }

  const strategy = await prisma.strategy.create({
    data: {
      workspaceId,
      name,
      symbol,
      timeframe: timeframe as typeof VALID_TIMEFRAMES[number],
      status: "DRAFT",
    },
  });

  return { strategyId: strategy.id, name: strategy.name, status: strategy.status };
}

// ---------------------------------------------------------------------------
// VALIDATE_DSL
// ---------------------------------------------------------------------------

export async function validateDslAction(
  _workspaceId: string,
  input: Record<string, unknown>,
): Promise<ValidateDslResult> {
  const { dslJson } = input;
  if (dslJson === "__USER_MUST_PROVIDE__" || dslJson === undefined || dslJson === null) {
    throw new ActionValidationError("dslJson must be provided by the user");
  }

  const errors = validateDsl(dslJson);
  if (errors) {
    return { ok: false, errors };
  }
  return { ok: true };
}

// ---------------------------------------------------------------------------
// CREATE_STRATEGY_VERSION
// ---------------------------------------------------------------------------

export async function createStrategyVersion(
  workspaceId: string,
  input: Record<string, unknown>,
): Promise<CreateStrategyVersionResult> {
  const { strategyId, dslJson } = input;

  if (!strategyId || typeof strategyId !== "string") {
    throw new ActionValidationError("strategyId is required");
  }
  if (dslJson === "__USER_MUST_PROVIDE__" || dslJson === undefined || dslJson === null) {
    throw new ActionValidationError("dslJson must be provided by the user");
  }

  // Cross-workspace check
  const strategy = await prisma.strategy.findUnique({ where: { id: strategyId } });
  if (!strategy || strategy.workspaceId !== workspaceId) {
    throw new ActionNotFoundError("Strategy not found");
  }

  const dslErrors = validateDsl(dslJson);
  if (dslErrors) {
    throw new ActionValidationError(`DSL validation failed: ${dslErrors.map((e) => e.message).join("; ")}`);
  }

  const latest = await prisma.strategyVersion.findFirst({
    where: { strategyId: strategy.id },
    orderBy: { version: "desc" },
  });
  const nextVersion = (latest?.version ?? 0) + 1;

  const version = await prisma.strategyVersion.create({
    data: {
      strategyId: strategy.id,
      version: nextVersion,
      dslJson: dslJson as object,
      executionPlanJson: { kind: "stub", createdAt: new Date().toISOString() },
    },
  });

  return { versionId: version.id, version: version.version };
}
