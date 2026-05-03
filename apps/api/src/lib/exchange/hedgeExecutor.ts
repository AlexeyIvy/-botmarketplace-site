/**
 * Funding-arb hedge execution (docs/55-T2).
 *
 * Places real Bybit orders for the spot + perp legs of a hedge, sequentially,
 * with compensating unwind on partial failure. Used synchronously by the
 * `/hedges/:id/execute` and `/hedges/:id/exit` REST routes.
 *
 * Sequencing:
 *   - Entry: spot Buy first, then perp Sell. Spot leads because spot market
 *     orders historically take longer to fill on Bybit; if spot fails, the
 *     perp side is never opened so no orphan position can result. If spot
 *     ok but perp fails, a compensating market sell is attempted on the
 *     spot leg (best-effort, swallowed errors → manual unwind alert).
 *   - Exit: spot Sell first, then perp Buy-to-close. Spot leads for the
 *     same reason. If perp close fails AFTER spot sell, no compensating
 *     reverse is attempted (re-buying spot would contradict the operator's
 *     intent to exit) — outcome is PARTIAL_ERROR with structured reason.
 *
 * Each leg uses bybitPlaceOrder (Market + IOC) and then polls
 * bybitGetOrderStatus a small fixed number of times to obtain avgPrice +
 * cumExecQty for the LegExecution row. Non-terminal status after the poll
 * budget is treated as a leg failure.
 *
 * Scope boundary: this module imports `bybitOrder.ts` but does NOT modify
 * it. The processIntents pipeline that the async hedgeBotWorker emits to
 * is unchanged — that path is still scoped to linear and will be wired up
 * separately.
 */

import {
  bybitPlaceOrder,
  bybitGetOrderStatus,
  sanitizeBybitError,
} from "../bybitOrder.js";
import { logger } from "../logger.js";

const log = logger.child({ module: "hedgeExecutor" });

// ---------------------------------------------------------------------------
// Polling config — env-overridable so tests can disable real timers.
// ---------------------------------------------------------------------------

function getPollAttempts(): number {
  const raw = parseInt(process.env.HEDGE_LEG_POLL_ATTEMPTS ?? "", 10);
  return Number.isFinite(raw) && raw > 0 ? raw : 5;
}

function getPollDelayMs(): number {
  const raw = parseInt(process.env.HEDGE_LEG_POLL_DELAY_MS ?? "", 10);
  return Number.isFinite(raw) && raw >= 0 ? raw : 200;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface LegCreds {
  apiKey: string;
  /** Plaintext secret — caller is responsible for decrypting. */
  secret: string;
}

export interface PlaceLegInput {
  category: "linear" | "spot";
  symbol: string;
  side: "Buy" | "Sell";
  qty: string;
}

export interface PlacedLegResult {
  orderId: string;
  /** Average fill price as number (parsed from Bybit string response). */
  avgPrice: number;
  /** Cumulative executed quantity as number. */
  cumExecQty: number;
}

export type HedgeLegSide = "SPOT_BUY" | "PERP_SHORT" | "SPOT_SELL" | "PERP_CLOSE";

export interface HedgeLegRow {
  side: HedgeLegSide;
  price: number;
  quantity: number;
  /** Bybit order response does not include exec fee on this path; populated
   *  from the order-status reconciler in a later pass. Default 0 keeps the
   *  LegExecution row writable today. */
  fee: number;
  orderId: string;
}

export type HedgeExecutionOutcome = "FILLED" | "FAILED" | "PARTIAL_ERROR";

export interface HedgeExecutionResult {
  outcome: HedgeExecutionOutcome;
  /** Successfully placed legs (one or two depending on outcome). */
  legs: HedgeLegRow[];
  /** Set when outcome is FAILED or PARTIAL_ERROR. */
  reason?: string;
  /** True iff a compensating action was attempted (PARTIAL_ERROR entry path). */
  compensatingUnwindAttempted?: boolean;
  /** True iff that compensating action itself succeeded. */
  compensatingUnwindSucceeded?: boolean;
}

export interface HedgeExecutionInput {
  spotCreds: LegCreds;
  perpCreds: LegCreds;
  symbol: string;
  /** Quantity as string (Bybit requires string representation). */
  qty: string;
  /** For structured logging only. */
  hedgeId: string;
}

// ---------------------------------------------------------------------------
// Single-leg placement + status poll
// ---------------------------------------------------------------------------

/** Place a Market+IOC order and poll bybitGetOrderStatus until terminal.
 *  Throws on Cancelled / Rejected / Deactivated terminal state, or on
 *  polling timeout (treated as a leg failure by the orchestrator above).
 *  Filled with cumExecQty=0 is reported as failure for safety — Bybit
 *  occasionally reports zero-fill Filled responses on rate-limited paths,
 *  and treating that as success would create a phantom LegExecution. */
export async function placeMarketLeg(
  creds: LegCreds,
  input: PlaceLegInput,
): Promise<PlacedLegResult> {
  const placed = await bybitPlaceOrder(creds.apiKey, creds.secret, {
    category: input.category,
    symbol: input.symbol,
    side: input.side,
    orderType: "Market",
    qty: input.qty,
  });

  const attempts = getPollAttempts();
  const delayMs = getPollDelayMs();

  for (let i = 0; i < attempts; i++) {
    const status = await bybitGetOrderStatus(
      creds.apiKey,
      creds.secret,
      placed.orderId,
      input.symbol,
      input.category,
    );

    if (status.orderStatus === "Filled") {
      const cumExecQty = parseFloat(status.cumExecQty);
      const avgPrice = parseFloat(status.avgPrice);
      if (!Number.isFinite(cumExecQty) || cumExecQty <= 0) {
        throw new Error(
          `Bybit reported Filled with non-positive cumExecQty (${status.cumExecQty}) for ${placed.orderId}`,
        );
      }
      if (!Number.isFinite(avgPrice) || avgPrice <= 0) {
        throw new Error(
          `Bybit reported Filled with non-positive avgPrice (${status.avgPrice}) for ${placed.orderId}`,
        );
      }
      return { orderId: placed.orderId, avgPrice, cumExecQty };
    }

    if (
      status.orderStatus === "Cancelled" ||
      status.orderStatus === "Rejected" ||
      status.orderStatus === "Deactivated"
    ) {
      throw new Error(
        `Order ${placed.orderId} reached terminal non-Filled state: ${status.orderStatus}`,
      );
    }

    if (i < attempts - 1 && delayMs > 0) {
      await sleep(delayMs);
    }
  }

  throw new Error(
    `Order ${placed.orderId} did not reach Filled within ${attempts} polls`,
  );
}

// ---------------------------------------------------------------------------
// Two-leg orchestration: entry + exit
// ---------------------------------------------------------------------------

/** Sequential entry: spot Buy first, then perp Sell. On spot failure the
 *  perp side is never opened; on perp failure after spot ok a compensating
 *  spot sell is attempted (best-effort). */
export async function executeHedgeEntry(
  input: HedgeExecutionInput,
): Promise<HedgeExecutionResult> {
  let spotLeg: PlacedLegResult;
  try {
    spotLeg = await placeMarketLeg(input.spotCreds, {
      category: "spot",
      symbol: input.symbol,
      side: "Buy",
      qty: input.qty,
    });
  } catch (err) {
    const reason = sanitizeBybitError(err);
    log.error(
      { hedgeId: input.hedgeId, leg: "SPOT_BUY", reason },
      "spot entry leg failed — abort before perp call",
    );
    return { outcome: "FAILED", legs: [], reason: `spot leg failed: ${reason}` };
  }

  let perpLeg: PlacedLegResult;
  try {
    perpLeg = await placeMarketLeg(input.perpCreds, {
      category: "linear",
      symbol: input.symbol,
      side: "Sell",
      qty: input.qty,
    });
  } catch (perpErr) {
    const perpReason = sanitizeBybitError(perpErr);
    log.error(
      { hedgeId: input.hedgeId, leg: "PERP_SHORT", reason: perpReason },
      "perp entry leg failed after spot fill — attempting compensating spot sell",
    );

    let compensatingSucceeded = false;
    try {
      await placeMarketLeg(input.spotCreds, {
        category: "spot",
        symbol: input.symbol,
        side: "Sell",
        qty: input.qty,
      });
      compensatingSucceeded = true;
      log.warn({ hedgeId: input.hedgeId }, "compensating spot sell succeeded");
    } catch (sellErr) {
      log.error(
        { hedgeId: input.hedgeId, reason: sanitizeBybitError(sellErr) },
        "compensating spot sell FAILED — manual unwind required",
      );
    }

    return {
      outcome: "PARTIAL_ERROR",
      legs: [
        {
          side: "SPOT_BUY",
          price: spotLeg.avgPrice,
          quantity: spotLeg.cumExecQty,
          fee: 0,
          orderId: spotLeg.orderId,
        },
      ],
      reason: `perp leg failed: ${perpReason}`,
      compensatingUnwindAttempted: true,
      compensatingUnwindSucceeded: compensatingSucceeded,
    };
  }

  return {
    outcome: "FILLED",
    legs: [
      {
        side: "SPOT_BUY",
        price: spotLeg.avgPrice,
        quantity: spotLeg.cumExecQty,
        fee: 0,
        orderId: spotLeg.orderId,
      },
      {
        side: "PERP_SHORT",
        price: perpLeg.avgPrice,
        quantity: perpLeg.cumExecQty,
        fee: 0,
        orderId: perpLeg.orderId,
      },
    ],
  };
}

/** Sequential exit: spot Sell first, then perp Buy-to-close. No compensating
 *  reverse on partial failure — re-buying spot would contradict the operator's
 *  intent to exit. PARTIAL_ERROR signals manual unwind required. */
export async function executeHedgeExit(
  input: HedgeExecutionInput,
): Promise<HedgeExecutionResult> {
  let spotLeg: PlacedLegResult;
  try {
    spotLeg = await placeMarketLeg(input.spotCreds, {
      category: "spot",
      symbol: input.symbol,
      side: "Sell",
      qty: input.qty,
    });
  } catch (err) {
    const reason = sanitizeBybitError(err);
    log.error(
      { hedgeId: input.hedgeId, leg: "SPOT_SELL", reason },
      "spot exit leg failed — abort before perp close",
    );
    return { outcome: "FAILED", legs: [], reason: `spot exit leg failed: ${reason}` };
  }

  let perpLeg: PlacedLegResult;
  try {
    perpLeg = await placeMarketLeg(input.perpCreds, {
      category: "linear",
      symbol: input.symbol,
      side: "Buy",
      qty: input.qty,
    });
  } catch (perpErr) {
    const perpReason = sanitizeBybitError(perpErr);
    log.error(
      { hedgeId: input.hedgeId, leg: "PERP_CLOSE", reason: perpReason },
      "perp close leg failed after spot sell — manual unwind alert",
    );
    return {
      outcome: "PARTIAL_ERROR",
      legs: [
        {
          side: "SPOT_SELL",
          price: spotLeg.avgPrice,
          quantity: spotLeg.cumExecQty,
          fee: 0,
          orderId: spotLeg.orderId,
        },
      ],
      reason: `perp close leg failed: ${perpReason}`,
    };
  }

  return {
    outcome: "FILLED",
    legs: [
      {
        side: "SPOT_SELL",
        price: spotLeg.avgPrice,
        quantity: spotLeg.cumExecQty,
        fee: 0,
        orderId: spotLeg.orderId,
      },
      {
        side: "PERP_CLOSE",
        price: perpLeg.avgPrice,
        quantity: perpLeg.cumExecQty,
        fee: 0,
        orderId: perpLeg.orderId,
      },
    ],
  };
}
