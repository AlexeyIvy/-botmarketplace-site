import { describe, it, expect, vi, beforeEach } from "vitest";

const findMany = vi.fn();
const updateMany = vi.fn();
const eventCreate = vi.fn();

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn(), InputJsonValue: null },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    botIntent: {
      findMany: (...a: unknown[]) => findMany(...a),
      updateMany: (...a: unknown[]) => updateMany(...a),
    },
    botEvent: { create: (...a: unknown[]) => eventCreate(...a) },
  },
}));

describe("periodicReconciler.sweepStalePendingIntents", () => {
  beforeEach(() => {
    findMany.mockReset();
    updateMany.mockReset();
    eventCreate.mockReset();
  });

  it("returns 0 and does no writes when no stale intents exist", async () => {
    findMany.mockResolvedValue([]);
    const { sweepStalePendingIntents } = await import("../../src/lib/periodicReconciler.js");
    expect(await sweepStalePendingIntents()).toBe(0);
    expect(updateMany).not.toHaveBeenCalled();
    expect(eventCreate).not.toHaveBeenCalled();
  });

  it("queries only PENDING intents older than the cutoff, attached to RUNNING runs", async () => {
    findMany.mockResolvedValue([]);
    const { sweepStalePendingIntents, STALE_PENDING_MIN_AGE_MS } = await import(
      "../../src/lib/periodicReconciler.js"
    );
    const before = Date.now();
    await sweepStalePendingIntents();
    const after = Date.now();

    expect(findMany).toHaveBeenCalledTimes(1);
    const arg = findMany.mock.calls[0][0] as {
      where: { state: string; createdAt: { lt: Date }; botRun: { state: string } };
    };
    expect(arg.where.state).toBe("PENDING");
    expect(arg.where.botRun.state).toBe("RUNNING");
    const cutoffMs = arg.where.createdAt.lt.getTime();
    expect(cutoffMs).toBeGreaterThanOrEqual(before - STALE_PENDING_MIN_AGE_MS - 10);
    expect(cutoffMs).toBeLessThanOrEqual(after - STALE_PENDING_MIN_AGE_MS + 10);
  });

  it("cancels stale PENDING and creates one BotEvent per run", async () => {
    const now = Date.now();
    findMany.mockResolvedValue([
      { id: "i1", intentId: "int-1", botRunId: "runA", createdAt: new Date(now - 20 * 60_000) },
      { id: "i2", intentId: "int-2", botRunId: "runA", createdAt: new Date(now - 15 * 60_000) },
      { id: "i3", intentId: "int-3", botRunId: "runB", createdAt: new Date(now - 11 * 60_000) },
    ]);
    updateMany.mockResolvedValue({ count: 3 });

    const { sweepStalePendingIntents } = await import("../../src/lib/periodicReconciler.js");
    const cancelled = await sweepStalePendingIntents();

    expect(cancelled).toBe(3);
    expect(updateMany).toHaveBeenCalledTimes(1);
    const updArg = updateMany.mock.calls[0][0] as {
      where: { id: { in: string[] }; state: string };
      data: { state: string; metaJson: { reason: string } };
    };
    expect(updArg.where.id.in.sort()).toEqual(["i1", "i2", "i3"]);
    expect(updArg.where.state).toBe("PENDING");
    expect(updArg.data.state).toBe("CANCELLED");
    expect(updArg.data.metaJson.reason).toBe("periodic_reconciliation_stale_pending");

    // One event per distinct runId
    expect(eventCreate).toHaveBeenCalledTimes(2);
    const runIds = eventCreate.mock.calls.map(
      (c) => (c[0] as { data: { botRunId: string } }).data.botRunId,
    );
    expect(runIds.sort()).toEqual(["runA", "runB"]);
  });
});
