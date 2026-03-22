/**
 * Position Manager — runtime state layer for bot positions.
 *
 * Provides first-class position lifecycle management:
 *   open → add → partial close → close
 *
 * Key responsibilities:
 * - VWAP average entry calculation
 * - Realised PnL tracking (per-close and cumulative)
 * - Immutable event log (PositionEvent) for auditability
 * - Active position read on bot startup (recovery/reconciliation)
 *
 * Designed for:
 * - long/short positions
 * - partial fills and DCA extensions
 * - future exchange reconciliation (#129)
 * - signal/exit engine integration (#128)
 *
 * Stage 3 — Issue #127
 */

import { Prisma } from "@prisma/client";
import { Decimal } from "@prisma/client/runtime/library";
import { prisma as defaultPrisma } from "./prisma.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type PositionSide = "LONG" | "SHORT";
export type PositionStatus = "OPEN" | "CLOSED";
export type PositionEventType = "OPEN" | "ADD" | "PARTIAL_CLOSE" | "CLOSE" | "SL_UPDATE" | "TP_UPDATE";

export interface OpenPositionInput {
  botId: string;
  botRunId: string;
  symbol: string;
  side: PositionSide;
  qty: number;
  price: number;
  slPrice?: number;
  tpPrice?: number;
  intentId?: string;
  meta?: Record<string, unknown>;
}

export interface AddToPositionInput {
  positionId: string;
  qty: number;
  price: number;
  intentId?: string;
  meta?: Record<string, unknown>;
}

export interface ClosePositionInput {
  positionId: string;
  qty: number;
  price: number;
  intentId?: string;
  meta?: Record<string, unknown>;
}

export interface UpdateSLTPInput {
  positionId: string;
  slPrice?: number | null;
  tpPrice?: number | null;
  meta?: Record<string, unknown>;
}

export interface PositionSnapshot {
  id: string;
  botId: string;
  botRunId: string;
  symbol: string;
  side: PositionSide;
  status: PositionStatus;
  entryQty: number;
  avgEntryPrice: number;
  costBasis: number;
  currentQty: number;
  realisedPnl: number;
  slPrice: number | null;
  tpPrice: number | null;
  openedAt: Date;
  closedAt: Date | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function toNum(d: Decimal | null | undefined): number | null {
  return d != null ? d.toNumber() : null;
}

function toSnapshot(pos: {
  id: string;
  botId: string;
  botRunId: string;
  symbol: string;
  side: string;
  status: string;
  entryQty: Decimal;
  avgEntryPrice: Decimal;
  costBasis: Decimal;
  currentQty: Decimal;
  realisedPnl: Decimal;
  slPrice: Decimal | null;
  tpPrice: Decimal | null;
  openedAt: Date;
  closedAt: Date | null;
}): PositionSnapshot {
  return {
    id: pos.id,
    botId: pos.botId,
    botRunId: pos.botRunId,
    symbol: pos.symbol,
    side: pos.side as PositionSide,
    status: pos.status as PositionStatus,
    entryQty: pos.entryQty.toNumber(),
    avgEntryPrice: pos.avgEntryPrice.toNumber(),
    costBasis: pos.costBasis.toNumber(),
    currentQty: pos.currentQty.toNumber(),
    realisedPnl: pos.realisedPnl.toNumber(),
    slPrice: toNum(pos.slPrice),
    tpPrice: toNum(pos.tpPrice),
    openedAt: pos.openedAt,
    closedAt: pos.closedAt,
  };
}

function makeSnapshotJson(pos: {
  avgEntryPrice: number | Decimal;
  currentQty: number | Decimal;
  costBasis: number | Decimal;
  realisedPnl: number | Decimal;
  slPrice: number | Decimal | null;
  tpPrice: number | Decimal | null;
}): Prisma.InputJsonValue {
  return {
    avgEntryPrice: Number(pos.avgEntryPrice),
    currentQty: Number(pos.currentQty),
    costBasis: Number(pos.costBasis),
    realisedPnl: Number(pos.realisedPnl),
    slPrice: pos.slPrice != null ? Number(pos.slPrice) : null,
    tpPrice: pos.tpPrice != null ? Number(pos.tpPrice) : null,
  } as Prisma.InputJsonValue;
}

// ---------------------------------------------------------------------------
// Position Manager
// ---------------------------------------------------------------------------

/**
 * Open a new position. Creates Position + OPEN event in a transaction.
 *
 * @throws if there is already an OPEN position for the same bot+symbol
 */
export async function openPosition(
  input: OpenPositionInput,
  tx?: Prisma.TransactionClient,
): Promise<PositionSnapshot> {
  const run = async (db: Prisma.TransactionClient) => {
    // Enforce one OPEN position per bot+symbol
    const existing = await db.position.findFirst({
      where: { botId: input.botId, symbol: input.symbol, status: "OPEN" },
    });
    if (existing) {
      throw new Error(
        `Bot ${input.botId} already has an open position on ${input.symbol} (${existing.id})`,
      );
    }

    const costBasis = input.qty * input.price;

    const position = await db.position.create({
      data: {
        botId: input.botId,
        botRunId: input.botRunId,
        symbol: input.symbol,
        side: input.side,
        status: "OPEN",
        entryQty: input.qty,
        avgEntryPrice: input.price,
        costBasis,
        currentQty: input.qty,
        realisedPnl: 0,
        slPrice: input.slPrice ?? null,
        tpPrice: input.tpPrice ?? null,
        metaJson: (input.meta as Prisma.InputJsonValue) ?? undefined,
      },
    });

    await db.positionEvent.create({
      data: {
        positionId: position.id,
        type: "OPEN",
        qty: input.qty,
        price: input.price,
        realisedPnl: 0,
        intentId: input.intentId ?? null,
        metaJson: (input.meta as Prisma.InputJsonValue) ?? undefined,
        snapshotJson: makeSnapshotJson({
          avgEntryPrice: input.price,
          currentQty: input.qty,
          costBasis,
          realisedPnl: 0,
          slPrice: input.slPrice ?? null,
          tpPrice: input.tpPrice ?? null,
        }),
      },
    });

    return toSnapshot(position);
  };

  return tx ? run(tx) : defaultPrisma.$transaction(run);
}

/**
 * Add to an existing OPEN position (DCA / averaging in).
 * Recalculates VWAP average entry and updates cost basis.
 *
 * @throws if position is not OPEN
 */
export async function addToPosition(
  input: AddToPositionInput,
  tx?: Prisma.TransactionClient,
): Promise<PositionSnapshot> {
  const run = async (db: Prisma.TransactionClient) => {
    const pos = await db.position.findUniqueOrThrow({ where: { id: input.positionId } });
    if (pos.status !== "OPEN") {
      throw new Error(`Cannot add to position ${input.positionId}: status is ${pos.status}`);
    }

    const oldQty = pos.entryQty.toNumber();
    const oldCostBasis = pos.costBasis.toNumber();
    const addCost = input.qty * input.price;

    const newEntryQty = oldQty + input.qty;
    const newCostBasis = oldCostBasis + addCost;
    const newAvgEntry = newCostBasis / newEntryQty;
    const newCurrentQty = pos.currentQty.toNumber() + input.qty;

    const updated = await db.position.update({
      where: { id: input.positionId },
      data: {
        entryQty: newEntryQty,
        avgEntryPrice: newAvgEntry,
        costBasis: newCostBasis,
        currentQty: newCurrentQty,
      },
    });

    await db.positionEvent.create({
      data: {
        positionId: input.positionId,
        type: "ADD",
        qty: input.qty,
        price: input.price,
        realisedPnl: 0,
        intentId: input.intentId ?? null,
        metaJson: (input.meta as Prisma.InputJsonValue) ?? undefined,
        snapshotJson: makeSnapshotJson({
          avgEntryPrice: newAvgEntry,
          currentQty: newCurrentQty,
          costBasis: newCostBasis,
          realisedPnl: updated.realisedPnl,
          slPrice: updated.slPrice,
          tpPrice: updated.tpPrice,
        }),
      },
    });

    return toSnapshot(updated);
  };

  return tx ? run(tx) : defaultPrisma.$transaction(run);
}

/**
 * Close (partially or fully) an OPEN position.
 * Calculates realised PnL for the closed quantity.
 * If closeQty >= currentQty, fully closes the position.
 *
 * Realised PnL formula:
 *   LONG:  (exitPrice - avgEntryPrice) × closeQty
 *   SHORT: (avgEntryPrice - exitPrice) × closeQty
 *
 * @throws if position is not OPEN or closeQty exceeds currentQty
 */
export async function closePosition(
  input: ClosePositionInput,
  tx?: Prisma.TransactionClient,
): Promise<PositionSnapshot> {
  const run = async (db: Prisma.TransactionClient) => {
    const pos = await db.position.findUniqueOrThrow({ where: { id: input.positionId } });
    if (pos.status !== "OPEN") {
      throw new Error(`Cannot close position ${input.positionId}: status is ${pos.status}`);
    }

    const currentQty = pos.currentQty.toNumber();
    const avgEntry = pos.avgEntryPrice.toNumber();

    if (input.qty > currentQty + 1e-12) {
      throw new Error(
        `Cannot close ${input.qty} from position ${input.positionId}: only ${currentQty} remaining`,
      );
    }

    // Determine if this is a full close (within floating point tolerance)
    const isFullClose = Math.abs(input.qty - currentQty) < 1e-12;
    const closeQty = isFullClose ? currentQty : input.qty;

    // Calculate realised PnL for this close
    const priceDiff = pos.side === "LONG"
      ? input.price - avgEntry
      : avgEntry - input.price;
    const eventPnl = priceDiff * closeQty;

    const newCurrentQty = isFullClose ? 0 : currentQty - closeQty;
    const newRealisedPnl = pos.realisedPnl.toNumber() + eventPnl;

    const updateData: Record<string, unknown> = {
      currentQty: newCurrentQty,
      realisedPnl: newRealisedPnl,
    };

    if (isFullClose) {
      updateData.status = "CLOSED";
      updateData.closedAt = new Date();
    }

    const updated = await db.position.update({
      where: { id: input.positionId },
      data: updateData,
    });

    await db.positionEvent.create({
      data: {
        positionId: input.positionId,
        type: isFullClose ? "CLOSE" : "PARTIAL_CLOSE",
        qty: closeQty,
        price: input.price,
        realisedPnl: eventPnl,
        intentId: input.intentId ?? null,
        metaJson: (input.meta as Prisma.InputJsonValue) ?? undefined,
        snapshotJson: makeSnapshotJson({
          avgEntryPrice: avgEntry,
          currentQty: newCurrentQty,
          costBasis: updated.costBasis,
          realisedPnl: newRealisedPnl,
          slPrice: updated.slPrice,
          tpPrice: updated.tpPrice,
        }),
      },
    });

    return toSnapshot(updated);
  };

  return tx ? run(tx) : defaultPrisma.$transaction(run);
}

/**
 * Update SL and/or TP on an OPEN position.
 * Pass `null` to clear a level; omit to leave unchanged.
 */
export async function updateSLTP(
  input: UpdateSLTPInput,
  tx?: Prisma.TransactionClient,
): Promise<PositionSnapshot> {
  const run = async (db: Prisma.TransactionClient) => {
    const pos = await db.position.findUniqueOrThrow({ where: { id: input.positionId } });
    if (pos.status !== "OPEN") {
      throw new Error(`Cannot update SL/TP on position ${input.positionId}: status is ${pos.status}`);
    }

    const updateData: Record<string, unknown> = {};
    if (input.slPrice !== undefined) updateData.slPrice = input.slPrice;
    if (input.tpPrice !== undefined) updateData.tpPrice = input.tpPrice;

    const updated = await db.position.update({
      where: { id: input.positionId },
      data: updateData,
    });

    // Log SL_UPDATE and/or TP_UPDATE events
    const events: Array<{ type: PositionEventType; price: number | null }> = [];
    if (input.slPrice !== undefined) events.push({ type: "SL_UPDATE", price: input.slPrice });
    if (input.tpPrice !== undefined) events.push({ type: "TP_UPDATE", price: input.tpPrice });

    for (const evt of events) {
      await db.positionEvent.create({
        data: {
          positionId: input.positionId,
          type: evt.type,
          price: evt.price,
          metaJson: (input.meta as Prisma.InputJsonValue) ?? undefined,
          snapshotJson: makeSnapshotJson({
            avgEntryPrice: updated.avgEntryPrice,
            currentQty: updated.currentQty,
            costBasis: updated.costBasis,
            realisedPnl: updated.realisedPnl,
            slPrice: updated.slPrice,
            tpPrice: updated.tpPrice,
          }),
        },
      });
    }

    return toSnapshot(updated);
  };

  return tx ? run(tx) : defaultPrisma.$transaction(run);
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/**
 * Get the active (OPEN) position for a bot run on a given symbol.
 * Returns null if no open position exists.
 */
export async function getActivePosition(
  botRunId: string,
  symbol: string,
  tx?: Prisma.TransactionClient,
): Promise<PositionSnapshot | null> {
  const db = tx ?? defaultPrisma;

  const pos = await db.position.findFirst({
    where: { botRunId, symbol, status: "OPEN" },
    orderBy: { openedAt: "desc" },
  });

  return pos ? toSnapshot(pos) : null;
}

/**
 * Get the active position for a bot (across all runs).
 * Useful for bot startup to find existing open positions.
 */
export async function getActiveBotPosition(
  botId: string,
  symbol: string,
  tx?: Prisma.TransactionClient,
): Promise<PositionSnapshot | null> {
  const db = tx ?? defaultPrisma;

  const pos = await db.position.findFirst({
    where: { botId, symbol, status: "OPEN" },
    orderBy: { openedAt: "desc" },
  });

  return pos ? toSnapshot(pos) : null;
}

/**
 * List all positions for a bot, ordered by most recent first.
 * Supports optional status filter and pagination.
 */
export async function listBotPositions(
  botId: string,
  opts?: { status?: PositionStatus; limit?: number; offset?: number },
  tx?: Prisma.TransactionClient,
): Promise<PositionSnapshot[]> {
  const db = tx ?? defaultPrisma;

  const positions = await db.position.findMany({
    where: {
      botId,
      ...(opts?.status ? { status: opts.status } : {}),
    },
    orderBy: { openedAt: "desc" },
    take: opts?.limit ?? 50,
    skip: opts?.offset ?? 0,
  });

  return positions.map(toSnapshot);
}

/**
 * Get position events for a position, ordered newest first.
 */
export async function getPositionEvents(
  positionId: string,
  opts?: { limit?: number },
  tx?: Prisma.TransactionClient,
) {
  const db = tx ?? defaultPrisma;

  return db.positionEvent.findMany({
    where: { positionId },
    orderBy: { ts: "desc" },
    take: opts?.limit ?? 100,
  });
}

/**
 * Calculate unrealised PnL for an open position at a given mark price.
 *
 * LONG:  (markPrice - avgEntryPrice) × currentQty
 * SHORT: (avgEntryPrice - markPrice) × currentQty
 */
export function calcUnrealisedPnl(position: PositionSnapshot, markPrice: number): number {
  if (position.status !== "OPEN" || position.currentQty === 0) return 0;

  const diff = position.side === "LONG"
    ? markPrice - position.avgEntryPrice
    : position.avgEntryPrice - markPrice;

  return diff * position.currentQty;
}
