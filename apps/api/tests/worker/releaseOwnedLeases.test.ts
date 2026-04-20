import { describe, it, expect, vi, beforeEach } from "vitest";

const updateMany = vi.fn();

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    botRun: { updateMany: (...args: unknown[]) => updateMany(...args) },
  },
  getPoolMetrics: vi.fn().mockResolvedValue(null),
  startPoolMetricsLogging: vi.fn(),
  stopPoolMetricsLogging: vi.fn(),
}));

describe("releaseOwnedLeases", () => {
  beforeEach(() => {
    updateMany.mockReset();
  });

  it("updates only RUNNING runs owned by this worker, setting leaseUntil to now", async () => {
    updateMany.mockResolvedValue({ count: 3 });

    const { releaseOwnedLeases } = await import("../../src/lib/botWorker.js");
    const released = await releaseOwnedLeases();

    expect(released).toBe(3);
    expect(updateMany).toHaveBeenCalledTimes(1);

    const call = updateMany.mock.calls[0][0] as {
      where: { leaseOwner: string; state: string };
      data: { leaseUntil: Date };
    };
    expect(call.where.state).toBe("RUNNING");
    expect(call.where.leaseOwner).toMatch(/^worker-\d+$/);
    expect(call.data.leaseUntil).toBeInstanceOf(Date);

    // leaseUntil should be now (±5s)
    const skew = Math.abs(Date.now() - call.data.leaseUntil.getTime());
    expect(skew).toBeLessThan(5000);
  });

  it("returns 0 when no leases match", async () => {
    updateMany.mockResolvedValue({ count: 0 });

    const { releaseOwnedLeases } = await import("../../src/lib/botWorker.js");
    expect(await releaseOwnedLeases()).toBe(0);
  });
});
