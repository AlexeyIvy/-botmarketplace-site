import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";

const VALID_TIMEFRAMES = ["M1", "M5", "M15", "H1"] as const;

// ---------------------------------------------------------------------------
// Minimal DSL validation
// ---------------------------------------------------------------------------

function validateDslJson(dslJson: unknown): string | null {
  if (dslJson === null || dslJson === undefined) return "dslJson is required";
  if (typeof dslJson !== "object" || Array.isArray(dslJson)) return "dslJson must be a JSON object";
  return null;
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

interface CreateStrategyBody {
  name: string;
  symbol: string;
  timeframe: string;
}

interface CreateVersionBody {
  dslJson: unknown;
}

interface ValidateBody {
  dslJson: unknown;
}

export async function strategyRoutes(app: FastifyInstance) {
  // GET /strategies — list strategies for workspace
  app.get("/strategies", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const strategies = await prisma.strategy.findMany({
      where: { workspaceId: workspace.id },
      orderBy: { createdAt: "desc" },
    });
    return reply.send(strategies);
  });

  // POST /strategies — create a new strategy (DRAFT)
  app.post<{ Body: CreateStrategyBody }>("/strategies", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { name, symbol, timeframe } = request.body ?? {};

    const errors: Array<{ field: string; message: string }> = [];
    if (!name || typeof name !== "string") errors.push({ field: "name", message: "name is required" });
    if (!symbol || typeof symbol !== "string") errors.push({ field: "symbol", message: "symbol is required" });
    if (!timeframe || !VALID_TIMEFRAMES.includes(timeframe as typeof VALID_TIMEFRAMES[number])) {
      errors.push({ field: "timeframe", message: `timeframe must be one of: ${VALID_TIMEFRAMES.join(", ")}` });
    }
    if (errors.length > 0) {
      return problem(reply, 400, "Validation Error", "Invalid strategy payload", { errors });
    }

    // Check unique (workspaceId, name)
    const existing = await prisma.strategy.findUnique({
      where: { workspaceId_name: { workspaceId: workspace.id, name } },
    });
    if (existing) {
      return problem(reply, 409, "Conflict", `Strategy "${name}" already exists in this workspace`);
    }

    const strategy = await prisma.strategy.create({
      data: {
        workspaceId: workspace.id,
        name,
        symbol,
        timeframe: timeframe as typeof VALID_TIMEFRAMES[number],
        status: "DRAFT",
      },
    });
    return reply.status(201).send(strategy);
  });

  // GET /strategies/:id — get single strategy (must belong to workspace)
  app.get<{ Params: { id: string } }>("/strategies/:id", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const strategy = await prisma.strategy.findUnique({
      where: { id: request.params.id },
      include: { versions: { orderBy: { version: "desc" } } },
    });
    if (!strategy || strategy.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Strategy not found");
    }
    return reply.send(strategy);
  });

  // POST /strategies/:id/versions — create a new version
  app.post<{ Params: { id: string }; Body: CreateVersionBody }>("/strategies/:id/versions", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const strategy = await prisma.strategy.findUnique({ where: { id: request.params.id } });
    if (!strategy || strategy.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Strategy not found");
    }

    const { dslJson } = request.body ?? {};
    const dslError = validateDslJson(dslJson);
    if (dslError) {
      return problem(reply, 400, "Validation Error", dslError);
    }

    // Determine next version number
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
    return reply.status(201).send(version);
  });

  // POST /strategies/validate — validate DSL JSON
  app.post<{ Body: ValidateBody }>("/strategies/validate", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const { dslJson } = request.body ?? {};
    const dslError = validateDslJson(dslJson);
    if (dslError) {
      return problem(reply, 400, "Validation Error", dslError);
    }
    return reply.send({ ok: true });
  });
}
