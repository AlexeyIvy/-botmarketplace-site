/**
 * Funding Scanner API routes (Phase 11.2)
 *
 * GET /terminal/funding/scanner — ranked funding arbitrage candidates
 * GET /terminal/funding/:symbol/history — historical funding snapshots
 */

import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { scanFundingCandidates } from "../lib/funding/scanner.js";
import type { FundingSnapshot, SpreadSnapshot } from "../lib/funding/types.js";

// ---------------------------------------------------------------------------
// GET /terminal/funding/scanner
// ---------------------------------------------------------------------------

interface ScannerQuery {
  minYield?: string;
  maxBasis?: string;
  minStreak?: string;
  limit?: string;
}

// ---------------------------------------------------------------------------
// GET /terminal/funding/:symbol/history
// ---------------------------------------------------------------------------

interface HistoryParams {
  symbol: string;
}

interface HistoryQuery {
  from?: string;
  to?: string;
  limit?: string;
}

// ---------------------------------------------------------------------------
// Route plugin
// ---------------------------------------------------------------------------

export async function fundingRoutes(app: FastifyInstance) {
  /**
   * GET /terminal/funding/scanner
   *
   * Scans FundingSnapshot records from the last 7 days, groups by symbol,
   * fetches latest SpreadSnapshot per symbol, and runs scanFundingCandidates.
   */
  app.get<{ Querystring: ScannerQuery }>(
    "/terminal/funding/scanner",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const minYield = parseFloat(request.query.minYield ?? "5");
      const maxBasis = parseFloat(request.query.maxBasis ?? "50");
      const minStreak = parseInt(request.query.minStreak ?? "3", 10);
      const topN = parseInt(request.query.limit ?? "10", 10);

      if ([minYield, maxBasis, minStreak, topN].some((v) => isNaN(v) || v < 0)) {
        return problem(reply, 400, "Bad Request", "Invalid query parameters");
      }

      const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

      // Fetch funding snapshots from last 7 days
      const fundingRows = await prisma.fundingSnapshot.findMany({
        where: { timestamp: { gte: sevenDaysAgo } },
        orderBy: { timestamp: "asc" },
      });

      // Group by symbol
      const symbolMap = new Map<string, {
        snapshots: FundingSnapshot[];
        spread: SpreadSnapshot | null;
      }>();

      for (const row of fundingRows) {
        const symbol = row.symbol;
        if (!symbolMap.has(symbol)) {
          symbolMap.set(symbol, { snapshots: [], spread: null });
        }
        symbolMap.get(symbol)!.snapshots.push({
          symbol: row.symbol,
          fundingRate: row.fundingRate,
          nextFundingAt: row.nextFundingAt.getTime(),
          timestamp: row.timestamp.getTime(),
        });
      }

      // Fetch latest SpreadSnapshot per symbol
      const symbols = [...symbolMap.keys()];
      if (symbols.length > 0) {
        const spreadRows = await prisma.spreadSnapshot.findMany({
          where: { symbol: { in: symbols } },
          orderBy: { timestamp: "desc" },
          distinct: ["symbol"],
        });

        for (const row of spreadRows) {
          const entry = symbolMap.get(row.symbol);
          if (entry) {
            entry.spread = {
              symbol: row.symbol,
              spotPrice: row.spotPrice,
              perpPrice: row.perpPrice,
              basisBps: row.basisBps,
              timestamp: row.timestamp.getTime(),
            };
          }
        }
      }

      const candidates = scanFundingCandidates(symbolMap, {
        minAnnualizedYieldPct: minYield,
        maxBasisBps: maxBasis,
        minStreak,
        topN,
      });

      return reply.send({
        candidates,
        updatedAt: new Date().toISOString(),
      });
    },
  );

  /**
   * GET /terminal/funding/:symbol/history
   *
   * Returns funding snapshots for a specific symbol within a date range.
   */
  app.get<{ Params: HistoryParams; Querystring: HistoryQuery }>(
    "/terminal/funding/:symbol/history",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const { symbol } = request.params;
      const limit = Math.min(parseInt(request.query.limit ?? "100", 10), 1000);

      if (isNaN(limit) || limit < 1) {
        return problem(reply, 400, "Bad Request", "Invalid limit parameter");
      }

      const where: Record<string, unknown> = { symbol };
      const timestampFilter: Record<string, Date> = {};

      if (request.query.from) {
        const from = new Date(request.query.from);
        if (isNaN(from.getTime())) {
          return problem(reply, 400, "Bad Request", "Invalid 'from' date");
        }
        timestampFilter.gte = from;
      }

      if (request.query.to) {
        const to = new Date(request.query.to);
        if (isNaN(to.getTime())) {
          return problem(reply, 400, "Bad Request", "Invalid 'to' date");
        }
        timestampFilter.lte = to;
      }

      if (Object.keys(timestampFilter).length > 0) {
        where.timestamp = timestampFilter;
      }

      const snapshots = await prisma.fundingSnapshot.findMany({
        where,
        orderBy: { timestamp: "asc" },
        take: limit,
      });

      return reply.send({
        snapshots: snapshots.map((row) => ({
          symbol: row.symbol,
          fundingRate: row.fundingRate,
          nextFundingAt: row.nextFundingAt.toISOString(),
          timestamp: row.timestamp.toISOString(),
        })),
      });
    },
  );
}
