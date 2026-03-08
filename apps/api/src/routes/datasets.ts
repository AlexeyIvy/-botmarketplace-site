/**
 * Dataset routes — Stage 19a + Phase 2A
 *
 * POST /lab/datasets      — create (or retrieve existing) frozen market dataset
 * GET  /lab/datasets      — list workspace datasets (Phase 2A)
 * GET  /lab/datasets/:id  — retrieve dataset metadata + qualityJson
 *
 * Rate limits:
 *   POST  10 req/min
 *   GET   60 req/min
 */

import type { FastifyInstance } from "fastify";
import type { CandleInterval } from "@prisma/client";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { fetchCandles } from "../lib/bybitCandles.js";
import { computeDatasetHash } from "../lib/datasetHash.js";
import { computeDataQuality } from "../lib/dataQuality.js";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_RANGE_MS = 365 * 24 * 60 * 60 * 1000; // 365 days
const MAX_CANDLES = 100_000;
const CHUNK_SIZE = 1_000;

/** Maps CandleInterval → Bybit API interval string + duration in ms */
const INTERVAL_META: Record<string, { bybitInterval: string; intervalMs: number }> = {
  M1:  { bybitInterval: "1",   intervalMs: 60_000 },
  M5:  { bybitInterval: "5",   intervalMs: 300_000 },
  M15: { bybitInterval: "15",  intervalMs: 900_000 },
  M30: { bybitInterval: "30",  intervalMs: 1_800_000 },
  H1:  { bybitInterval: "60",  intervalMs: 3_600_000 },
  H4:  { bybitInterval: "240", intervalMs: 14_400_000 },
  D1:  { bybitInterval: "D",   intervalMs: 86_400_000 },
};

const VALID_INTERVALS = Object.keys(INTERVAL_META) as CandleInterval[];

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

interface CreateDatasetBody {
  exchange: string;
  symbol: string;
  interval: string;
  /** Optional display name for this dataset */
  name?: string;
  /** ISO date string (alternative to fromTsMs) */
  fromTs?: string;
  /** ISO date string (alternative to toTsMs) */
  toTs?: string;
  fromTsMs?: number;
  toTsMs?: number;
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function datasetRoutes(app: FastifyInstance) {
  // ── POST /lab/datasets ─────────────────────────────────────────────────────
  app.post<{ Body: CreateDatasetBody }>("/lab/datasets", {
    config: { rateLimit: { max: 10, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const {
      exchange,
      symbol,
      interval,
      name,
      fromTs,
      toTs,
      fromTsMs: bodyFromMs,
      toTsMs: bodyToMs,
    } = request.body ?? {};

    // ── Validation ────────────────────────────────────────────────────────────
    const errors: Array<{ field: string; message: string }> = [];
    if (!exchange) errors.push({ field: "exchange", message: "exchange is required" });
    if (!symbol)   errors.push({ field: "symbol",   message: "symbol is required" });
    if (!interval) {
      errors.push({ field: "interval", message: "interval is required" });
    } else if (!VALID_INTERVALS.includes(interval as CandleInterval)) {
      errors.push({
        field: "interval",
        message: `interval must be one of: ${VALID_INTERVALS.join(", ")}`,
      });
    }
    if (bodyFromMs == null && !fromTs) {
      errors.push({ field: "fromTs", message: "fromTs (ISO) or fromTsMs (ms) is required" });
    }
    if (bodyToMs == null && !toTs) {
      errors.push({ field: "toTs", message: "toTs (ISO) or toTsMs (ms) is required" });
    }
    if (errors.length > 0) {
      return problem(reply, 400, "Validation Error", "Invalid dataset request", { errors });
    }

    const fromMs = bodyFromMs ?? new Date(fromTs!).getTime();
    const toMs   = bodyToMs   ?? new Date(toTs!).getTime();

    if (!Number.isFinite(fromMs) || !Number.isFinite(toMs)) {
      return problem(reply, 400, "Validation Error", "fromTs / toTs must be valid ISO dates");
    }
    if (fromMs >= toMs) {
      return problem(reply, 400, "Validation Error", "fromTs must be before toTs");
    }

    const rangeMs = toMs - fromMs;
    if (rangeMs > MAX_RANGE_MS) {
      return problem(reply, 400, "Range Too Large", "Date range must not exceed 365 days");
    }

    const meta = INTERVAL_META[interval]!;
    const estimatedCandles = Math.ceil(rangeMs / meta.intervalMs);
    if (estimatedCandles > MAX_CANDLES) {
      return problem(
        reply, 400, "Too Many Candles",
        `Requested range would produce ~${estimatedCandles} candles, exceeding the 100,000 limit`,
      );
    }

    const exchangeUpper = exchange.toUpperCase();

    // ── Fetch from exchange ───────────────────────────────────────────────────
    let fetched: Awaited<ReturnType<typeof fetchCandles>>;
    try {
      fetched = await fetchCandles(symbol, meta.bybitInterval, fromMs, toMs, MAX_CANDLES);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return problem(reply, 502, "Bad Gateway", `Failed to fetch candles: ${msg}`);
    }

    const engineVersion = process.env.COMMIT_SHA ?? "unknown";

    // ── Transactional upsert (30 s timeout) ──────────────────────────────────
    const dataset = await prisma.$transaction(async (tx) => {
      // Chunked createMany (skipDuplicates = ON CONFLICT DO NOTHING)
      let totalCreated = 0;
      for (let i = 0; i < fetched.length; i += CHUNK_SIZE) {
        const chunk = fetched.slice(i, i + CHUNK_SIZE);
        const result = await tx.marketCandle.createMany({
          data: chunk.map((c) => ({
            exchange:   exchangeUpper,
            symbol,
            interval:   interval as CandleInterval,
            openTimeMs: BigInt(c.openTime),
            open:       c.open,
            high:       c.high,
            low:        c.low,
            close:      c.close,
            volume:     c.volume,
          })),
          skipDuplicates: true,
        });
        totalCreated += result.count;
      }

      const dupeAttempts = fetched.length - totalCreated;

      // Query candles from DB in exact range (source of truth for hash + quality)
      const dbCandles = await tx.marketCandle.findMany({
        where: {
          exchange:   exchangeUpper,
          symbol,
          interval:   interval as CandleInterval,
          openTimeMs: { gte: BigInt(fromMs), lte: BigInt(toMs) },
        },
        orderBy: { openTimeMs: "asc" },
      });

      // Compute quality + hash strictly from DB Decimal values
      const { qualityJson, status } = computeDataQuality(dbCandles, meta.intervalMs, dupeAttempts);
      const datasetHash = computeDatasetHash(dbCandles);

      // Upsert MarketDataset by unique(workspaceId, exchange, symbol, interval, fromTsMs, toTsMs)
      return tx.marketDataset.upsert({
        where: {
          workspaceId_exchange_symbol_interval_fromTsMs_toTsMs: {
            workspaceId: workspace.id,
            exchange:    exchangeUpper,
            symbol,
            interval:    interval as CandleInterval,
            fromTsMs:    BigInt(fromMs),
            toTsMs:      BigInt(toMs),
          },
        },
        create: {
          workspaceId:   workspace.id,
          exchange:      exchangeUpper,
          symbol,
          interval:      interval as CandleInterval,
          fromTsMs:      BigInt(fromMs),
          toTsMs:        BigInt(toMs),
          fetchedAt:     new Date(),
          datasetHash,
          candleCount:   dbCandles.length,
          qualityJson:   qualityJson as unknown as object,
          engineVersion,
          status,
          name:          name?.trim() || null,
        },
        update: {
          fetchedAt:     new Date(),
          datasetHash,
          candleCount:   dbCandles.length,
          qualityJson:   qualityJson as unknown as object,
          engineVersion,
          status,
          // preserve existing name on re-fetch unless a new one is provided
          ...(name?.trim() ? { name: name.trim() } : {}),
        },
      });
    }, { timeout: 30_000 });

    return reply.status(201).send({
      datasetId:     dataset.id,
      name:          dataset.name,
      datasetHash:   dataset.datasetHash,
      status:        dataset.status,
      qualityJson:   dataset.qualityJson,
      candleCount:   dataset.candleCount,
      fetchedAt:     dataset.fetchedAt,
      engineVersion: dataset.engineVersion,
    });
  });

  // ── GET /lab/datasets ──────────────────────────────────────────────────────
  app.get("/lab/datasets", {
    config: { rateLimit: { max: 60, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const datasets = await prisma.marketDataset.findMany({
      where: { workspaceId: workspace.id },
      orderBy: { createdAt: "desc" },
      take: 100,
      select: {
        id: true,
        exchange: true,
        symbol: true,
        interval: true,
        fromTsMs: true,
        toTsMs: true,
        candleCount: true,
        status: true,
        name: true,
        datasetHash: true,
        fetchedAt: true,
        createdAt: true,
      },
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return reply.send(
      (datasets as any[]).map((ds) => ({
        datasetId:   ds.id,
        exchange:    ds.exchange,
        symbol:      ds.symbol,
        interval:    ds.interval,
        fromTsMs:    ds.fromTsMs.toString(),
        toTsMs:      ds.toTsMs.toString(),
        candleCount: ds.candleCount,
        status:      ds.status,
        name:        ds.name,
        datasetHash: ds.datasetHash,
        fetchedAt:   ds.fetchedAt,
        createdAt:   ds.createdAt,
      }))
    );
  });

  // ── GET /lab/datasets/:id ──────────────────────────────────────────────────
  app.get<{ Params: { id: string } }>("/lab/datasets/:id", {
    config: { rateLimit: { max: 60, timeWindow: "1 minute" } },
    onRequest: [app.authenticate],
  }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const ds = await prisma.marketDataset.findUnique({ where: { id: request.params.id } });
    if (!ds) {
      return problem(reply, 404, "Not Found", "Dataset not found");
    }
    if (ds.workspaceId !== workspace.id) {
      return problem(reply, 403, "Forbidden", "Dataset belongs to another workspace");
    }

    return reply.send({
      datasetId:     ds.id,
      workspaceId:   ds.workspaceId,
      exchange:      ds.exchange,
      symbol:        ds.symbol,
      interval:      ds.interval,
      fromTsMs:      ds.fromTsMs.toString(),
      toTsMs:        ds.toTsMs.toString(),
      fetchedAt:     ds.fetchedAt,
      datasetHash:   ds.datasetHash,
      candleCount:   ds.candleCount,
      qualityJson:   ds.qualityJson,
      engineVersion: ds.engineVersion,
      status:        ds.status,
      name:          ds.name,
      createdAt:     ds.createdAt,
    });
  });
}
