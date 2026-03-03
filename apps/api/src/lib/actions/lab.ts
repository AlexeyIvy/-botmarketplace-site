/**
 * Stage 18b — Lab service functions.
 * Extracted from labRoutes so /ai/execute can reuse the same logic.
 */

import { prisma } from "../prisma.js";
import { ActionNotFoundError, ActionValidationError } from "./strategies.js";
import { fetchCandles } from "../bybitCandles.js";
import { runBacktest } from "../backtest.js";

export { ActionNotFoundError, ActionValidationError };

const VALID_INTERVALS = ["1", "5", "15", "60"] as const;
const MAX_CANDLES = 2000;

export interface RunBacktestResult {
  backtestId: string;
  status: string;
}

// ---------------------------------------------------------------------------
// RUN_BACKTEST
// ---------------------------------------------------------------------------

export async function runBacktestAction(
  workspaceId: string,
  input: Record<string, unknown>,
): Promise<RunBacktestResult> {
  const { strategyId, symbol: bodySymbol, interval: bodyInterval, fromTs, toTs } = input;

  if (!strategyId || typeof strategyId !== "string") {
    throw new ActionValidationError("strategyId is required");
  }
  if (!fromTs || typeof fromTs !== "string") {
    throw new ActionValidationError("fromTs is required (ISO date)");
  }
  if (!toTs || typeof toTs !== "string") {
    throw new ActionValidationError("toTs is required (ISO date)");
  }
  if (bodyInterval !== undefined && !VALID_INTERVALS.includes(bodyInterval as typeof VALID_INTERVALS[number])) {
    throw new ActionValidationError(`interval must be one of: ${VALID_INTERVALS.join(", ")}`);
  }

  const fromDate = new Date(fromTs);
  const toDate = new Date(toTs);
  if (isNaN(fromDate.getTime()) || isNaN(toDate.getTime())) {
    throw new ActionValidationError("fromTs and toTs must be valid ISO dates");
  }
  if (fromDate >= toDate) {
    throw new ActionValidationError("fromTs must be before toTs");
  }

  // Cross-workspace check
  const strategy = await prisma.strategy.findUnique({ where: { id: strategyId } });
  if (!strategy || strategy.workspaceId !== workspaceId) {
    throw new ActionNotFoundError("Strategy not found");
  }

  const symbol = (typeof bodySymbol === "string" && bodySymbol) ? bodySymbol : strategy.symbol;
  const interval = (typeof bodyInterval === "string" && bodyInterval) ? bodyInterval : intervalFromTimeframe(strategy.timeframe);

  const bt = await prisma.backtestResult.create({
    data: {
      workspaceId,
      strategyId: strategy.id,
      symbol,
      interval,
      fromTs: fromDate,
      toTs: toDate,
      status: "PENDING",
    },
  });

  // Fire-and-forget
  runBacktestAsync(bt.id, symbol, interval, fromDate, toDate).catch(() => undefined);

  return { backtestId: bt.id, status: "PENDING" };
}

// ---------------------------------------------------------------------------
// Async runner (same as in labRoutes)
// ---------------------------------------------------------------------------

async function runBacktestAsync(
  btId: string,
  symbol: string,
  interval: string,
  fromDate: Date,
  toDate: Date,
): Promise<void> {
  try {
    await prisma.backtestResult.update({ where: { id: btId }, data: { status: "RUNNING" } });

    const bt = await prisma.backtestResult.findUnique({ where: { id: btId } });
    const strategy = bt
      ? await prisma.strategy.findUnique({
          where: { id: bt.strategyId },
          include: { versions: { orderBy: { version: "desc" }, take: 1 } },
        })
      : null;

    const riskPct = extractRiskPct(strategy?.versions[0]?.dslJson);
    const candles = await fetchCandles(symbol, interval, fromDate.getTime(), toDate.getTime(), MAX_CANDLES);
    const report = runBacktest(candles, riskPct);

    await prisma.backtestResult.update({
      where: { id: btId },
      data: { status: "DONE", reportJson: report as unknown as object },
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    await prisma.backtestResult.update({
      where: { id: btId },
      data: { status: "FAILED", errorMessage: msg },
    }).catch(() => undefined);
  }
}

function extractRiskPct(dslJson: unknown): number {
  if (!dslJson || typeof dslJson !== "object") return 1.0;
  const dsl = dslJson as Record<string, unknown>;
  const risk = dsl["risk"];
  if (!risk || typeof risk !== "object") return 1.0;
  const r = risk as Record<string, unknown>;
  const pct = Number(r["riskPerTradePct"]);
  return Number.isFinite(pct) && pct > 0 ? pct : 1.0;
}

function intervalFromTimeframe(tf: string): string {
  switch (tf) {
    case "M1":  return "1";
    case "M5":  return "5";
    case "M15": return "15";
    case "H1":  return "60";
    default:    return "15";
  }
}
