/**
 * Stage 20e: Public demo endpoint — no auth, no workspace required.
 * POST /demo/backtest runs a deterministic backtest on a server-side preset
 * and returns the report in-memory without writing to the database.
 */

import type { FastifyInstance } from "fastify";
import { problem } from "../lib/problem.js";
import { runBacktest } from "../lib/backtest.js";
import { fetchCandles } from "../lib/bybitCandles.js";

// ---------------------------------------------------------------------------
// Preset definitions
// ---------------------------------------------------------------------------

interface DemoPreset {
  symbol: string;
  /** Bybit interval string: "15", "60", "D", etc. */
  interval: string;
  /** How many days back from now to use */
  daysBack: number;
  /** Risk per trade in % */
  riskPct: number;
  description: string;
}

const DEMO_PRESETS: Record<string, DemoPreset> = {
  "btc-breakout-demo": {
    symbol: "BTCUSDT",
    interval: "60",
    daysBack: 90,
    riskPct: 1,
    description: "BTC/USDT 1h breakout strategy (90-day window)",
  },
  "eth-mean-reversion-demo": {
    symbol: "ETHUSDT",
    interval: "15",
    daysBack: 45,
    riskPct: 1,
    description: "ETH/USDT 15m breakout strategy (45-day window)",
  },
};

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

interface DemoBacktestBody {
  presetId: string;
}

export async function demoRoutes(app: FastifyInstance) {
  // Rate-limit demo endpoint more conservatively (no auth guard)
  app.post<{ Body: DemoBacktestBody }>(
    "/demo/backtest",
    {
      config: { rateLimit: { max: 10, timeWindow: "1 minute" } },
    },
    async (request, reply) => {
      const { presetId } = request.body ?? {};

      if (!presetId || typeof presetId !== "string") {
        return problem(reply, 400, "Bad Request", "presetId is required");
      }

      const preset = DEMO_PRESETS[presetId];
      if (!preset) {
        return problem(reply, 400, "Bad Request", `Unknown presetId: "${presetId}". Valid: ${Object.keys(DEMO_PRESETS).join(", ")}`);
      }

      const nowMs = Date.now();
      const fromMs = nowMs - preset.daysBack * 24 * 60 * 60 * 1000;

      let candles;
      try {
        candles = await fetchCandles(preset.symbol, preset.interval, fromMs, nowMs, 2000);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        return problem(reply, 502, "Bad Gateway", `Failed to fetch market data: ${msg}`);
      }

      const report = runBacktest(candles, preset.riskPct);

      return reply.status(200).send({
        presetId,
        description: preset.description,
        symbol: preset.symbol,
        interval: preset.interval,
        summary: {
          trades: report.trades,
          wins: report.wins,
          winrate: report.winrate,
          totalPnlPct: report.totalPnlPct,
          maxDrawdownPct: report.maxDrawdownPct,
          candles: report.candles,
        },
        trades: report.tradeLog,
      });
    },
  );
}
