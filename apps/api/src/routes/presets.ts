/**
 * Strategy Preset routes (docs/51-T2 + 51-T3).
 *
 * Public catalog of immutable JSON templates. The Lab Library renders the
 * list as cards and POST /presets/:slug/instantiate materialises them into
 * Strategy + StrategyVersion + Bot triples in a single Prisma transaction.
 *
 * Endpoints:
 *   POST /presets                       — admin-only; create a preset (validates DSL)
 *   GET  /presets                       — list (PUBLIC only for anon; all for admin)
 *   GET  /presets/:slug                 — single preset with dslJson
 *   POST /presets/:slug/instantiate     — workspace user; create Strategy + Version + Bot
 *
 * No PATCH / DELETE: presets are intentionally immutable. To replace,
 * create a new slug.
 */

import { randomBytes } from "node:crypto";
import type { FastifyInstance, FastifyRequest } from "fastify";
import { Prisma, PresetVisibility, BotMode } from "@prisma/client";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { validateDsl } from "../lib/dslValidator.js";
import { isAdminRequest } from "../lib/adminGuard.js";
import { resolveWorkspace } from "../lib/workspace.js";

// ---------------------------------------------------------------------------
// Visibility helpers
// ---------------------------------------------------------------------------

/**
 * Soft authentication for endpoints that have public + authenticated tiers
 * (docs/55-T6 §A4). Unlike `app.authenticate`, this never sends a 401: it
 * simply reports whether a valid Bearer token was supplied so the handler
 * can scope its visibility filter accordingly.
 */
async function tryAuthenticate(request: FastifyRequest): Promise<boolean> {
  try {
    await request.jwtVerify();
    return true;
  } catch {
    return false;
  }
}

interface ViewerScope {
  admin: boolean;
  authed: boolean;
}

/**
 * Three-tier visibility check: PRIVATE → admin only, BETA → authed users
 * (admin always passes), PUBLIC → everyone. The funding-arb preset lives
 * at BETA per docs/55-T6 — visible to authenticated users with an explicit
 * "experimental, multi-leg" badge in the UI, but kept off the anonymous
 * landing page until promoted to PUBLIC.
 */
function canViewPreset(visibility: PresetVisibility, scope: ViewerScope): boolean {
  if (scope.admin) return true;
  if (visibility === PresetVisibility.PUBLIC) return true;
  if (visibility === PresetVisibility.BETA) return scope.authed;
  return false; // PRIVATE — admin-only, already short-circuited above
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SLUG_REGEX = /^[a-z0-9-]{3,64}$/;
const VALID_CATEGORIES = ["trend", "dca", "scalping", "smc", "arb"] as const;
const VALID_TIMEFRAMES = ["M1", "M5", "M15", "H1"] as const;

type Category = typeof VALID_CATEGORIES[number];
type Timeframe = typeof VALID_TIMEFRAMES[number];

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DefaultBotConfig {
  symbol: string;
  timeframe: Timeframe;
  quoteAmount: number;
  maxOpenPositions: number;
  [k: string]: unknown;
}

interface CreatePresetBody {
  slug: string;
  name: string;
  description: string;
  category: Category;
  dslJson: unknown;
  defaultBotConfigJson: DefaultBotConfig;
  datasetBundleHintJson?: Record<string, unknown> | null;
  visibility?: "PRIVATE" | "BETA" | "PUBLIC";
}

interface InstantiateBody {
  overrides?: Partial<{
    symbol: string;
    timeframe: Timeframe;
    quoteAmount: number;
    maxOpenPositions: number;
    name: string;
  }>;
}

interface ResolvedConfig {
  symbol: string;
  timeframe: Timeframe;
  quoteAmount: number;
  maxOpenPositions: number;
  baseName: string;
  /** Runtime dispatch mode (docs/55-T4). Comes from
   *  `defaultBotConfigJson.mode` when present (e.g. funding-arb preset
   *  ships `"mode": "FUNDING_ARB"`); otherwise falls back to DSL. The
   *  override block intentionally cannot set this — it is a preset-level
   *  property, not a per-instantiation tweak. */
  mode: BotMode;
}

function resolveConfig(
  preset: { name: string; defaultBotConfigJson: Prisma.JsonValue },
  overrides: InstantiateBody["overrides"],
): { config?: ResolvedConfig; errors: Array<{ field: string; message: string }> } {
  const errors: Array<{ field: string; message: string }> = [];
  const cfg = preset.defaultBotConfigJson as Record<string, unknown> | null;
  if (!cfg || typeof cfg !== "object" || Array.isArray(cfg)) {
    errors.push({ field: "preset.defaultBotConfigJson", message: "preset has no usable default config" });
    return { errors };
  }

  const symbol = (overrides?.symbol ?? cfg.symbol) as unknown;
  const timeframe = (overrides?.timeframe ?? cfg.timeframe) as unknown;
  const quoteAmount = (overrides?.quoteAmount ?? cfg.quoteAmount) as unknown;
  const maxOpenPositions = (overrides?.maxOpenPositions ?? cfg.maxOpenPositions) as unknown;
  const baseName = (overrides?.name ?? preset.name) as unknown;
  const modeRaw = cfg.mode as unknown;

  if (typeof symbol !== "string" || symbol.length === 0) {
    errors.push({ field: "symbol", message: "symbol must be a non-empty string" });
  }
  if (typeof timeframe !== "string" || !VALID_TIMEFRAMES.includes(timeframe as Timeframe)) {
    errors.push({
      field: "timeframe",
      message: `timeframe must be one of: ${VALID_TIMEFRAMES.join(", ")}`,
    });
  }
  if (typeof quoteAmount !== "number" || !(quoteAmount > 0)) {
    errors.push({ field: "quoteAmount", message: "quoteAmount must be > 0" });
  }
  if (
    typeof maxOpenPositions !== "number" ||
    !Number.isInteger(maxOpenPositions) ||
    maxOpenPositions < 1
  ) {
    errors.push({ field: "maxOpenPositions", message: "maxOpenPositions must be a positive integer" });
  }
  if (typeof baseName !== "string" || baseName.length === 0 || baseName.length > 120) {
    errors.push({ field: "name", message: "name must be 1..120 chars" });
  }

  // Mode (docs/55-T4). Absent ⇒ DSL. Present must match the BotMode enum.
  let mode: BotMode = BotMode.DSL;
  if (modeRaw !== undefined && modeRaw !== null) {
    if (typeof modeRaw !== "string" || !(Object.values(BotMode) as string[]).includes(modeRaw)) {
      errors.push({
        field: "mode",
        message: `mode must be one of: ${(Object.values(BotMode) as string[]).join(", ")}`,
      });
    } else {
      mode = modeRaw as BotMode;
    }
  }

  if (errors.length > 0) return { errors };

  return {
    errors: [],
    config: {
      symbol: symbol as string,
      timeframe: timeframe as Timeframe,
      quoteAmount: quoteAmount as number,
      maxOpenPositions: maxOpenPositions as number,
      baseName: baseName as string,
      mode,
    },
  };
}

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

function validateCreateBody(
  body: Partial<CreatePresetBody> | null | undefined,
): { errors: Array<{ field: string; message: string }>; data?: CreatePresetBody } {
  const errors: Array<{ field: string; message: string }> = [];
  const b = body ?? {};

  if (typeof b.slug !== "string" || !SLUG_REGEX.test(b.slug)) {
    errors.push({ field: "slug", message: "slug must match /^[a-z0-9-]{3,64}$/" });
  }
  if (typeof b.name !== "string" || b.name.length < 1 || b.name.length > 120) {
    errors.push({ field: "name", message: "name must be 1..120 chars" });
  }
  if (typeof b.description !== "string" || b.description.length < 1 || b.description.length > 500) {
    errors.push({ field: "description", message: "description must be 1..500 chars" });
  }
  if (typeof b.category !== "string" || !VALID_CATEGORIES.includes(b.category as Category)) {
    errors.push({
      field: "category",
      message: `category must be one of: ${VALID_CATEGORIES.join(", ")}`,
    });
  }
  if (b.dslJson === undefined || b.dslJson === null) {
    errors.push({ field: "dslJson", message: "dslJson is required" });
  }

  const cfg = b.defaultBotConfigJson;
  if (!cfg || typeof cfg !== "object" || Array.isArray(cfg)) {
    errors.push({ field: "defaultBotConfigJson", message: "defaultBotConfigJson is required" });
  } else {
    if (typeof cfg.symbol !== "string" || cfg.symbol.length === 0) {
      errors.push({ field: "defaultBotConfigJson.symbol", message: "symbol is required" });
    }
    if (typeof cfg.timeframe !== "string" || !VALID_TIMEFRAMES.includes(cfg.timeframe as Timeframe)) {
      errors.push({
        field: "defaultBotConfigJson.timeframe",
        message: `timeframe must be one of: ${VALID_TIMEFRAMES.join(", ")}`,
      });
    }
    if (typeof cfg.quoteAmount !== "number" || !(cfg.quoteAmount > 0)) {
      errors.push({ field: "defaultBotConfigJson.quoteAmount", message: "quoteAmount must be > 0" });
    }
    if (typeof cfg.maxOpenPositions !== "number" || !Number.isInteger(cfg.maxOpenPositions) || cfg.maxOpenPositions < 1) {
      errors.push({
        field: "defaultBotConfigJson.maxOpenPositions",
        message: "maxOpenPositions must be a positive integer",
      });
    }
  }

  if (b.datasetBundleHintJson !== undefined && b.datasetBundleHintJson !== null) {
    if (typeof b.datasetBundleHintJson !== "object" || Array.isArray(b.datasetBundleHintJson)) {
      errors.push({
        field: "datasetBundleHintJson",
        message: "datasetBundleHintJson must be an object or null",
      });
    }
  }

  if (
    b.visibility !== undefined &&
    b.visibility !== "PRIVATE" &&
    b.visibility !== "BETA" &&
    b.visibility !== "PUBLIC"
  ) {
    errors.push({ field: "visibility", message: "visibility must be PRIVATE, BETA, or PUBLIC" });
  }

  if (errors.length > 0) return { errors };
  return { errors: [], data: b as CreatePresetBody };
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function presetRoutes(app: FastifyInstance) {
  // POST /presets — admin only
  app.post<{ Body: CreatePresetBody }>("/presets", async (request, reply) => {
    if (!isAdminRequest(request)) {
      return problem(reply, 401, "Unauthorized", "Admin token required");
    }

    const { errors, data } = validateCreateBody(request.body);
    if (!data) {
      return problem(reply, 400, "Validation Error", "Invalid preset payload", { errors });
    }

    const dslErrors = validateDsl(data.dslJson);
    if (dslErrors) {
      return problem(reply, 400, "Validation Error", "DSL validation failed", { errors: dslErrors });
    }

    try {
      const created = await prisma.strategyPreset.create({
        data: {
          slug: data.slug,
          name: data.name,
          description: data.description,
          category: data.category,
          dslJson: data.dslJson as Prisma.InputJsonValue,
          defaultBotConfigJson: data.defaultBotConfigJson as unknown as Prisma.InputJsonValue,
          datasetBundleHintJson:
            data.datasetBundleHintJson === undefined || data.datasetBundleHintJson === null
              ? Prisma.JsonNull
              : (data.datasetBundleHintJson as Prisma.InputJsonValue),
          visibility: data.visibility ?? PresetVisibility.PRIVATE,
        },
      });
      return reply.status(201).send(created);
    } catch (err) {
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2002") {
        return problem(reply, 409, "Conflict", `Preset "${data.slug}" already exists`);
      }
      throw err;
    }
  });

  // GET /presets — three-tier visibility scoping (docs/55-T6 §A4):
  //   • anon         → PUBLIC only
  //   • authed user  → PUBLIC + BETA (BETA gates experimental presets like funding-arb
  //                    behind login while still keeping them off the anonymous landing)
  //   • admin        → all (or filtered by ?visibility=…)
  app.get<{ Querystring: { category?: string; visibility?: string } }>(
    "/presets",
    async (request, reply) => {
      const admin = isAdminRequest(request);
      const authed = await tryAuthenticate(request);
      const where: Prisma.StrategyPresetWhereInput = {};

      // Visibility scoping
      if (admin) {
        if (
          request.query?.visibility === "PRIVATE" ||
          request.query?.visibility === "BETA" ||
          request.query?.visibility === "PUBLIC"
        ) {
          where.visibility = request.query.visibility as PresetVisibility;
        }
        // else: admin sees everything regardless of visibility
      } else if (authed) {
        where.visibility = { in: [PresetVisibility.PUBLIC, PresetVisibility.BETA] };
      } else {
        where.visibility = PresetVisibility.PUBLIC;
      }

      // Category filter
      const categoryFilter = request.query?.category;
      if (typeof categoryFilter === "string" && VALID_CATEGORIES.includes(categoryFilter as Category)) {
        where.category = categoryFilter;
      }

      const rows = await prisma.strategyPreset.findMany({
        where,
        orderBy: { updatedAt: "desc" },
        select: {
          slug: true,
          name: true,
          description: true,
          category: true,
          defaultBotConfigJson: true,
          datasetBundleHintJson: true,
          visibility: true,
          createdAt: true,
          updatedAt: true,
        },
      });
      return reply.send(rows);
    },
  );

  // GET /presets/:slug — full record. Visibility rules mirror the list endpoint
  // (docs/55-T6 §A4): PRIVATE is admin-only; BETA requires authentication; PUBLIC
  // is open. 404 (not 403) on hidden so existence is not revealed.
  app.get<{ Params: { slug: string } }>("/presets/:slug", async (request, reply) => {
    const admin = isAdminRequest(request);
    const authed = admin ? true : await tryAuthenticate(request);
    const preset = await prisma.strategyPreset.findUnique({
      where: { slug: request.params.slug },
    });

    if (!preset || !canViewPreset(preset.visibility, { admin, authed })) {
      return problem(reply, 404, "Not Found", "Preset not found");
    }

    return reply.send(preset);
  });

  // POST /presets/:slug/instantiate — workspace user creates Strategy + Version + Bot
  //
  // Workspace is taken from the X-Workspace-Id header (same convention as the
  // rest of the API), not the body. The docs/51-T3 spec sketches `workspaceId`
  // in the body, but using the header keeps membership enforcement uniform via
  // resolveWorkspace().
  app.post<{ Params: { slug: string }; Body: InstantiateBody }>(
    "/presets/:slug/instantiate",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const workspace = await resolveWorkspace(request, reply);
      if (!workspace) return;

      const admin = isAdminRequest(request);
      const preset = await prisma.strategyPreset.findUnique({
        where: { slug: request.params.slug },
      });
      // Endpoint runs under app.authenticate, so authed=true by construction.
      // Mirror GET semantics so PRIVATE is admin-only and BETA visible to authed.
      if (!preset || !canViewPreset(preset.visibility, { admin, authed: true })) {
        return problem(reply, 404, "Not Found", "Preset not found");
      }

      const overrides = request.body?.overrides;
      const { config, errors } = resolveConfig(preset, overrides);
      if (!config) {
        return problem(reply, 400, "Validation Error", "Invalid instantiate payload", { errors });
      }

      // Generate a unique-per-workspace suffix for both Strategy and Bot names
      // so repeated instantiate calls do not collide on the (workspaceId, name)
      // unique index. Six hex chars = 24 bits of entropy — plenty for human
      // disambiguation, retry-free.
      const suffix = randomBytes(3).toString("hex");
      const strategyName = `${config.baseName} (${suffix})`;
      const botName = `${config.baseName} (${suffix})`;

      try {
        const result = await prisma.$transaction(async (tx) => {
          const strategy = await tx.strategy.create({
            data: {
              workspaceId: workspace.id,
              name: strategyName,
              symbol: config.symbol,
              timeframe: config.timeframe,
              status: "DRAFT",
              templateSlug: preset.slug,
            },
          });

          const version = await tx.strategyVersion.create({
            data: {
              strategyId: strategy.id,
              version: 1,
              dslJson: preset.dslJson as Prisma.InputJsonValue,
              executionPlanJson: {
                kind: "preset",
                presetSlug: preset.slug,
                createdAt: new Date().toISOString(),
              } as Prisma.InputJsonValue,
            },
          });

          const bot = await tx.bot.create({
            data: {
              workspaceId: workspace.id,
              name: botName,
              strategyVersionId: version.id,
              symbol: config.symbol,
              timeframe: config.timeframe,
              status: "DRAFT",
              templateSlug: preset.slug,
              mode: config.mode,
            },
          });

          return { strategy, version, bot };
        });

        return reply.status(201).send({
          botId: result.bot.id,
          strategyId: result.strategy.id,
          strategyVersionId: result.version.id,
        });
      } catch (err) {
        if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2002") {
          // Astronomically unlikely with 24-bit suffix, but handle the
          // (workspaceId, name) clash explicitly so the client gets a clean
          // signal to retry.
          return problem(reply, 409, "Conflict", "Generated name collided; please retry");
        }
        throw err;
      }
    },
  );
}
