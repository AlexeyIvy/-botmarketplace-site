/**
 * Strategy Preset routes (docs/51-T2).
 *
 * Public catalog of immutable JSON templates that the Lab Library renders
 * as cards and that POST /presets/:slug/instantiate (51-T3) materialises
 * into Strategy + StrategyVersion + Bot triples.
 *
 * Endpoints:
 *   POST /presets         — admin-only; create a preset (validates DSL)
 *   GET  /presets         — list (PUBLIC only for anon; all for admin)
 *   GET  /presets/:slug   — single preset with dslJson
 *
 * No PATCH / DELETE: presets are intentionally immutable. To replace,
 * create a new slug.
 */

import type { FastifyInstance } from "fastify";
import { Prisma, PresetVisibility } from "@prisma/client";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { validateDsl } from "../lib/dslValidator.js";
import { isAdminRequest } from "../lib/adminGuard.js";

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
  visibility?: "PRIVATE" | "PUBLIC";
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

  if (b.visibility !== undefined && b.visibility !== "PRIVATE" && b.visibility !== "PUBLIC") {
    errors.push({ field: "visibility", message: "visibility must be PRIVATE or PUBLIC" });
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

  // GET /presets — public (PUBLIC only) or admin (all)
  app.get<{ Querystring: { category?: string; visibility?: string } }>(
    "/presets",
    async (request, reply) => {
      const admin = isAdminRequest(request);
      const where: Prisma.StrategyPresetWhereInput = {};

      // Visibility scoping
      if (!admin) {
        where.visibility = PresetVisibility.PUBLIC;
      } else if (request.query?.visibility === "PRIVATE" || request.query?.visibility === "PUBLIC") {
        where.visibility = request.query.visibility as PresetVisibility;
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

  // GET /presets/:slug — full record
  app.get<{ Params: { slug: string } }>("/presets/:slug", async (request, reply) => {
    const admin = isAdminRequest(request);
    const preset = await prisma.strategyPreset.findUnique({
      where: { slug: request.params.slug },
    });

    // 404 (not 403) on PRIVATE without admin so existence is not revealed.
    if (!preset || (preset.visibility === PresetVisibility.PRIVATE && !admin)) {
      return problem(reply, 404, "Not Found", "Preset not found");
    }

    return reply.send(preset);
  });
}
