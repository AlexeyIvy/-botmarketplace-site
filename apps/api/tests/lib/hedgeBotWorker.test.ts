/**
 * hedgeBotWorker — unit coverage (docs/55-T4).
 *
 * Mocks `prisma` + `errorClassifier` so the state machine can be
 * exercised without a database. Each test fixes a `HedgePosition`
 * status + a small set of `BotIntent` rows, calls `advanceHedge`,
 * and asserts on the return value AND the prisma writes the worker
 * issued.
 *
 * Coverage:
 *   1. PENDING + fundingWindowOpen ⇒ ENTRY_PLACED  (two BotIntents created
 *      with category="spot" + "linear", HedgeStatus → OPENING).
 *   2. PENDING + window closed     ⇒ no-op (hedge stays PLANNED).
 *   3. ENTRY_PLACED + both FILLED  ⇒ ACTIVE (status → OPEN).
 *   4. ENTRY_PLACED + one FAILED   ⇒ ERRORED (status → FAILED).
 *   5. ACTIVE + funding payment    ⇒ EXIT_PLACED (two BotIntents, status → CLOSING).
 *   6. EXIT_PLACED + both FILLED   ⇒ CLOSED (status → CLOSED + closedAt set).
 *   7. tickHedgeBotWorker isolates a per-hedge throw (other hedges still advance).
 *   8. startHedgeBotWorker honours ENABLE_HEDGE_WORKER off-by-default.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mocks (must come before importing the module under test)
// ---------------------------------------------------------------------------

interface FakeHedge {
  id: string;
  botRunId: string;
  symbol: string;
  status: "PLANNED" | "OPENING" | "OPEN" | "CLOSING" | "CLOSED" | "FAILED";
}

interface FakeIntent {
  botRunId: string;
  type: "ENTRY" | "EXIT";
  state: "PENDING" | "PLACED" | "PARTIALLY_FILLED" | "FILLED" | "CANCELLED" | "FAILED";
  metaJson: { hedgeId: string; legSide: string; category: string };
  intentId: string;
}

const hedgesById = new Map<string, FakeHedge>();
const intents: FakeIntent[] = [];
const connectionsByBotRunId = new Map<string, {
  apiKey: string;
  encryptedSecret: string;
  spotApiKey: string | null;
  spotEncryptedSecret: string | null;
} | null>();
const created: Array<Partial<FakeIntent> & { qty?: number; orderLinkId?: string; side?: string }> = [];
const updates: Array<{ id: string; data: Record<string, unknown> }> = [];

function resetState() {
  hedgesById.clear();
  intents.length = 0;
  connectionsByBotRunId.clear();
  created.length = 0;
  updates.length = 0;
}

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    hedgePosition: {
      findUnique: vi.fn(async ({ where }: { where: { id: string } }) => {
        return hedgesById.get(where.id) ?? null;
      }),
      findMany: vi.fn(async ({ where }: { where: { botRunId?: string; status: { in: string[] } } }) => {
        const statuses = new Set(where.status.in);
        return [...hedgesById.values()]
          .filter((h) => statuses.has(h.status))
          .filter((h) => where.botRunId === undefined || h.botRunId === where.botRunId)
          .map((h) => ({ id: h.id, symbol: h.symbol, botRunId: h.botRunId }));
      }),
      update: vi.fn(async ({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
        const h = hedgesById.get(where.id);
        if (h) {
          if (typeof data.status === "string") h.status = data.status as FakeHedge["status"];
        }
        updates.push({ id: where.id, data });
        return h;
      }),
    },
    botRun: {
      findUnique: vi.fn(async ({ where }: { where: { id: string } }) => {
        // The real query goes BotRun → Bot → ExchangeConnection. We
        // collapse it to a single map keyed by botRunId for tests; the
        // hedgeBotWorker only reads `run?.bot?.exchangeConnection`.
        const conn = connectionsByBotRunId.get(where.id);
        if (conn === undefined) return null;
        return { bot: { exchangeConnection: conn } };
      }),
    },
    fundingSnapshot: {
      // Default: no snapshot → windowDetector returns { open: false,
      // paymentReceived: false }, which keeps existing tests' "closed
      // window" assumption intact. Tests that need to open the window
      // can override this mock per-case.
      findFirst: vi.fn(async () => null),
    },
    botIntent: {
      create: vi.fn(async ({ data }: { data: Record<string, unknown> }) => {
        created.push(data as never);
        // Reflect into the intent store so subsequent findMany sees it
        intents.push({
          botRunId: data.botRunId as string,
          type: data.type as FakeIntent["type"],
          state: data.state as FakeIntent["state"],
          metaJson: data.metaJson as FakeIntent["metaJson"],
          intentId: data.intentId as string,
        });
        return data;
      }),
      findMany: vi.fn(async ({ where }: { where: { botRunId: string; type: string } }) => {
        return intents
          .filter((i) => i.botRunId === where.botRunId && i.type === where.type)
          .map((i) => ({ state: i.state, metaJson: i.metaJson, intentId: i.intentId }));
      }),
    },
    $transaction: vi.fn(async (ops: unknown[]) => {
      // Each op is already a Promise (the .create / .update calls have
      // executed eagerly because our mocks resolve the data immediately).
      return Promise.all(ops as Promise<unknown>[]);
    }),
  },
}));

const reconcileBalancesMock = vi.fn();
vi.mock("../../src/lib/exchange/balanceReconciler.js", () => ({
  reconcileBalances: (...args: unknown[]) => reconcileBalancesMock(...args),
}));

vi.mock("../../src/lib/logger.js", () => ({
  logger: {
    child: () => ({
      info: vi.fn(),
      warn: vi.fn(),
      error: vi.fn(),
      debug: vi.fn(),
    }),
  },
}));

vi.mock("../../src/lib/errorClassifier.js", () => ({
  classifyExecutionError: () => ({ errorClass: "unknown", retryable: false, reason: "test-stub" }),
}));

import {
  advanceHedge,
  startHedgeBotWorker,
  tickHedgeBotWorker,
  tickHedgeBotWorkerForBotRun,
  type HedgeStage,
} from "../../src/lib/hedgeBotWorker.js";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function seedHedge(overrides: Partial<FakeHedge> & { id: string }): FakeHedge {
  const h: FakeHedge = {
    id: overrides.id,
    botRunId: overrides.botRunId ?? `run-${overrides.id}`,
    symbol: overrides.symbol ?? "BTCUSDT",
    status: overrides.status ?? "PLANNED",
  };
  hedgesById.set(h.id, h);
  return h;
}

function seedIntent(args: {
  hedgeId: string;
  botRunId: string;
  type: "ENTRY" | "EXIT";
  legSide: string;
  category: "spot" | "linear";
  state: FakeIntent["state"];
}): void {
  intents.push({
    botRunId: args.botRunId,
    type: args.type,
    state: args.state,
    metaJson: { hedgeId: args.hedgeId, legSide: args.legSide, category: args.category },
    intentId: `seed-${args.hedgeId}-${args.legSide}-${args.type}`,
  });
}

beforeEach(() => {
  resetState();
});

afterEach(() => {
  delete process.env.ENABLE_HEDGE_WORKER;
});

// ---------------------------------------------------------------------------
// 1. PENDING → ENTRY_PLACED on funding window
// ---------------------------------------------------------------------------

describe("PENDING → ENTRY_PLACED", () => {
  it("emits two BotIntents (spot + linear) and bumps status to OPENING", async () => {
    seedHedge({ id: "h1" });

    const res = await advanceHedge("h1", { fundingWindowOpen: true, entryQty: 1.0 });

    expect(res).toMatchObject({
      hedgeId: "h1",
      fromStage: "PENDING",
      toStage: "ENTRY_PLACED",
      changed: true,
    });

    expect(created).toHaveLength(2);
    const categories = created.map((c) => (c.metaJson as { category: string }).category).sort();
    expect(categories).toEqual(["linear", "spot"]);

    // Both intents are ENTRY type, qty = 1.0
    expect(created.every((c) => c.type === "ENTRY")).toBe(true);
    expect(created.every((c) => c.qty === 1.0)).toBe(true);

    // Spot leg buys, perp leg sells
    const spotLeg = created.find((c) => (c.metaJson as { category: string }).category === "spot")!;
    const perpLeg = created.find((c) => (c.metaJson as { category: string }).category === "linear")!;
    expect(spotLeg.side).toBe("BUY");
    expect(perpLeg.side).toBe("SELL");

    // HedgeStatus advanced
    expect(hedgesById.get("h1")?.status).toBe("OPENING");
    expect(updates.some((u) => u.id === "h1" && u.data.status === "OPENING")).toBe(true);
  });

  it("no-ops when funding window is closed", async () => {
    seedHedge({ id: "h2" });

    const res = await advanceHedge("h2", { fundingWindowOpen: false, entryQty: 1.0 });

    expect(res).toMatchObject({ fromStage: "PENDING", toStage: "PENDING", changed: false });
    expect(created).toHaveLength(0);
    expect(hedgesById.get("h2")?.status).toBe("PLANNED");
  });

  it("no-ops when entryQty is missing or non-positive", async () => {
    seedHedge({ id: "h3" });

    const res = await advanceHedge("h3", { fundingWindowOpen: true, entryQty: 0 });

    expect(res.changed).toBe(false);
    expect(created).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// 1b. PENDING balance gate (55-T5 wiring)
// ---------------------------------------------------------------------------

describe("PENDING → ENTRY_PLACED — balance gating", () => {
  it("flat symbol → reconciler called, intents emitted, status → OPENING", async () => {
    seedHedge({ id: "g1" });
    const reconcile = vi.fn(async () => ({
      hedgeStatus: [{ symbol: "BTCUSDT", status: "flat" }],
    }));

    const res = await advanceHedge("g1", {
      fundingWindowOpen: true,
      entryQty: 1.0,
      reconcileBeforeEntry: reconcile,
    });

    expect(reconcile).toHaveBeenCalledOnce();
    expect(res.toStage).toBe<HedgeStage>("ENTRY_PLACED");
    expect(hedgesById.get("g1")?.status).toBe("OPENING");
  });

  it.each(["perp_only", "spot_only", "balanced", "imbalanced"])(
    "non-flat status (%s) refuses entry, no intents emitted, hedge stays PLANNED",
    async (status) => {
      seedHedge({ id: `g-${status}` });
      const reconcile = vi.fn(async () => ({
        hedgeStatus: [{ symbol: "BTCUSDT", status }],
      }));

      const res = await advanceHedge(`g-${status}`, {
        fundingWindowOpen: true,
        entryQty: 1.0,
        reconcileBeforeEntry: reconcile,
      });

      expect(reconcile).toHaveBeenCalledOnce();
      expect(res.changed).toBe(false);
      expect(res.toStage).toBe<HedgeStage>("PENDING");
      expect(created).toHaveLength(0);
      expect(hedgesById.get(`g-${status}`)?.status).toBe("PLANNED");
    },
  );

  it("reconciler throws → entry deferred to next tick, no state change", async () => {
    seedHedge({ id: "g-err" });
    const reconcile = vi.fn(async () => {
      throw new Error("Bybit reconciler HTTP 503");
    });

    const res = await advanceHedge("g-err", {
      fundingWindowOpen: true,
      entryQty: 1.0,
      reconcileBeforeEntry: reconcile,
    });

    expect(reconcile).toHaveBeenCalledOnce();
    expect(res.changed).toBe(false);
    expect(res.toStage).toBe<HedgeStage>("PENDING");
    expect(created).toHaveLength(0);
  });

  it("no reconciler supplied → balance check skipped (legacy unit-test path)", async () => {
    seedHedge({ id: "g-skip" });

    const res = await advanceHedge("g-skip", {
      fundingWindowOpen: true,
      entryQty: 1.0,
      // reconcileBeforeEntry intentionally omitted
    });

    expect(res.toStage).toBe<HedgeStage>("ENTRY_PLACED");
    expect(hedgesById.get("g-skip")?.status).toBe("OPENING");
  });
});

// ---------------------------------------------------------------------------
// 2. ENTRY_PLACED → ACTIVE / ERRORED
// ---------------------------------------------------------------------------

describe("ENTRY_PLACED → ACTIVE / ERRORED", () => {
  it("transitions ENTRY_PLACED → ACTIVE when both entry intents are FILLED", async () => {
    seedHedge({ id: "h4", status: "OPENING" });
    seedIntent({ hedgeId: "h4", botRunId: "run-h4", type: "ENTRY", legSide: "SPOT_BUY",   category: "spot",   state: "FILLED" });
    seedIntent({ hedgeId: "h4", botRunId: "run-h4", type: "ENTRY", legSide: "PERP_SHORT", category: "linear", state: "FILLED" });

    const res = await advanceHedge("h4");

    expect(res.toStage).toBe<HedgeStage>("ACTIVE");
    expect(hedgesById.get("h4")?.status).toBe("OPEN");
  });

  it("escalates ENTRY_PLACED → ERRORED when one leg is FAILED (partial fill)", async () => {
    seedHedge({ id: "h5", status: "OPENING" });
    seedIntent({ hedgeId: "h5", botRunId: "run-h5", type: "ENTRY", legSide: "SPOT_BUY",   category: "spot",   state: "FILLED" });
    seedIntent({ hedgeId: "h5", botRunId: "run-h5", type: "ENTRY", legSide: "PERP_SHORT", category: "linear", state: "FAILED" });

    const res = await advanceHedge("h5");

    expect(res.toStage).toBe<HedgeStage>("ERRORED");
    expect(hedgesById.get("h5")?.status).toBe("FAILED");
  });

  it("stays in ENTRY_PLACED while a leg is still PENDING", async () => {
    seedHedge({ id: "h6", status: "OPENING" });
    seedIntent({ hedgeId: "h6", botRunId: "run-h6", type: "ENTRY", legSide: "SPOT_BUY",   category: "spot",   state: "FILLED" });
    seedIntent({ hedgeId: "h6", botRunId: "run-h6", type: "ENTRY", legSide: "PERP_SHORT", category: "linear", state: "PENDING" });

    const res = await advanceHedge("h6");

    expect(res.changed).toBe(false);
    expect(res.toStage).toBe<HedgeStage>("ENTRY_PLACED");
    expect(hedgesById.get("h6")?.status).toBe("OPENING");
  });
});

// ---------------------------------------------------------------------------
// 3. ACTIVE → EXIT_PLACED
// ---------------------------------------------------------------------------

describe("ACTIVE → EXIT_PLACED", () => {
  it("emits exit BotIntents and sets HedgeStatus to CLOSING when funding payment is received", async () => {
    seedHedge({ id: "h7", status: "OPEN" });

    const res = await advanceHedge("h7", { fundingPaymentReceived: true, exitQty: 0.5 });

    expect(res.toStage).toBe<HedgeStage>("EXIT_PLACED");
    expect(hedgesById.get("h7")?.status).toBe("CLOSING");

    expect(created).toHaveLength(2);
    expect(created.every((c) => c.type === "EXIT")).toBe(true);
    const spotLeg = created.find((c) => (c.metaJson as { category: string }).category === "spot")!;
    const perpLeg = created.find((c) => (c.metaJson as { category: string }).category === "linear")!;
    expect(spotLeg.side).toBe("SELL");
    expect(perpLeg.side).toBe("BUY");
    expect(spotLeg.qty).toBe(0.5);
  });
});

// ---------------------------------------------------------------------------
// 4. EXIT_PLACED → CLOSED
// ---------------------------------------------------------------------------

describe("EXIT_PLACED → CLOSED", () => {
  it("transitions to CLOSED + closedAt when both exit legs FILLED", async () => {
    seedHedge({ id: "h8", status: "CLOSING" });
    seedIntent({ hedgeId: "h8", botRunId: "run-h8", type: "EXIT", legSide: "SPOT_SELL",  category: "spot",   state: "FILLED" });
    seedIntent({ hedgeId: "h8", botRunId: "run-h8", type: "EXIT", legSide: "PERP_CLOSE", category: "linear", state: "FILLED" });

    const res = await advanceHedge("h8");

    expect(res.toStage).toBe<HedgeStage>("CLOSED");
    expect(hedgesById.get("h8")?.status).toBe("CLOSED");
    const closedUpdate = updates.find((u) => u.id === "h8" && u.data.status === "CLOSED");
    expect(closedUpdate?.data.closedAt).toBeInstanceOf(Date);
  });
});

// ---------------------------------------------------------------------------
// 5. tick — error isolation across hedges
// ---------------------------------------------------------------------------

describe("tickHedgeBotWorker", () => {
  it("isolates a per-hedge throw — other hedges still advance", async () => {
    seedHedge({ id: "good", status: "PLANNED" });
    seedHedge({ id: "bad",  status: "PLANNED" });

    const res = await tickHedgeBotWorker((hedgeId) => {
      if (hedgeId === "bad") {
        throw new Error("synthetic");
      }
      return { fundingWindowOpen: true, entryQty: 1.0 };
    });

    // Only the good hedge produced a result; the bad one was swallowed.
    expect(res).toHaveLength(1);
    expect(res[0]).toMatchObject({ hedgeId: "good", toStage: "ENTRY_PLACED" });

    // good advanced; bad stayed PLANNED.
    expect(hedgesById.get("good")?.status).toBe("OPENING");
    expect(hedgesById.get("bad")?.status).toBe("PLANNED");
  });

  it("returns empty when there are no eligible hedges", async () => {
    seedHedge({ id: "terminal", status: "CLOSED" });
    const res = await tickHedgeBotWorker();
    expect(res).toEqual([]);
  });

  // -------------------------------------------------------------------------
  // Default-path orchestration: load creds → wire reconcileBalances callback
  //
  // The default path produces input { reconcileBeforeEntry: <wired> } only —
  // it does NOT set fundingWindowOpen, because that signal is owned by the
  // upstream funding scanner (out of scope here). So in these tests the
  // PENDING gate short-circuits on the closed-window check before the
  // reconciler is ever consulted. We instead pin:
  //   * loadHedgeCreds runs (BotRun.findUnique called with the right id),
  //   * advance returns no-change at the closed-window branch,
  //   * the reconciler is NEVER called when the window is closed even
  //     though the wiring is in place.
  //
  // Once the funding-scanner layer lands, a fresh test here will cover
  // the open-window path end-to-end.
  // -------------------------------------------------------------------------

  it("default path: loads ExchangeConnection via BotRun.findUnique", async () => {
    seedHedge({ id: "tick-1", status: "PLANNED", symbol: "BTCUSDT", botRunId: "run-tick-1" });
    connectionsByBotRunId.set("run-tick-1", {
      apiKey: "k", encryptedSecret: "enc:s",
      spotApiKey: "sk", spotEncryptedSecret: "enc:ss",
    });

    const { prisma } = await import("../../src/lib/prisma.js");

    await tickHedgeBotWorker();

    expect((prisma.botRun.findUnique as ReturnType<typeof vi.fn>)).toHaveBeenCalledWith(
      expect.objectContaining({ where: { id: "run-tick-1" } }),
    );
    // Closed window ⇒ no reconciler call, but wiring was prepared.
    expect(reconcileBalancesMock).not.toHaveBeenCalled();
    expect(hedgesById.get("tick-1")?.status).toBe("PLANNED");
  });

  it("default path: hedge without linked ExchangeConnection — reconciler not wired, no error", async () => {
    seedHedge({ id: "tick-2", status: "PLANNED", symbol: "BTCUSDT", botRunId: "run-tick-2" });
    // No connectionsByBotRunId entry for run-tick-2 → loadHedgeCreds returns null.

    const res = await tickHedgeBotWorker();

    expect(res[0]).toMatchObject({ hedgeId: "tick-2", toStage: "PENDING", changed: false });
    expect(reconcileBalancesMock).not.toHaveBeenCalled();
    expect(hedgesById.get("tick-2")?.status).toBe("PLANNED");
  });
});

// ---------------------------------------------------------------------------
// 5b. tickHedgeBotWorkerForBotRun — bot-scoped delegation (docs/55-T4)
// ---------------------------------------------------------------------------

describe("tickHedgeBotWorkerForBotRun", () => {
  it("only advances hedges whose botRunId matches the scope", async () => {
    seedHedge({ id: "scoped-a", status: "PLANNED", botRunId: "run-A" });
    seedHedge({ id: "scoped-b", status: "PLANNED", botRunId: "run-B" });

    const res = await tickHedgeBotWorkerForBotRun("run-A", () => ({
      fundingWindowOpen: true,
      entryQty: 1.0,
    }));

    expect(res).toHaveLength(1);
    expect(res[0]).toMatchObject({ hedgeId: "scoped-a", toStage: "ENTRY_PLACED" });
    expect(hedgesById.get("scoped-a")?.status).toBe("OPENING");
    // Cross-tenant isolation: the other run's hedge stays untouched.
    expect(hedgesById.get("scoped-b")?.status).toBe("PLANNED");
  });

  it("returns empty when the scoped run has no eligible hedges", async () => {
    seedHedge({ id: "other", status: "PLANNED", botRunId: "run-other" });
    const res = await tickHedgeBotWorkerForBotRun("run-empty");
    expect(res).toEqual([]);
  });

  it("filters by status: terminal hedges in scope are skipped", async () => {
    seedHedge({ id: "scope-closed", status: "CLOSED", botRunId: "run-X" });
    seedHedge({ id: "scope-open",   status: "OPENING", botRunId: "run-X" });

    const res = await tickHedgeBotWorkerForBotRun("run-X", () => ({}));

    // Only OPENING gets a tick; the CLOSED hedge is excluded by the
    // status filter (same as the global tick).
    expect(res).toHaveLength(1);
    expect(res[0].hedgeId).toBe("scope-open");
  });

  it("isolates a per-hedge throw within the scoped run", async () => {
    seedHedge({ id: "ok",  status: "PLANNED", botRunId: "run-iso" });
    seedHedge({ id: "bad", status: "PLANNED", botRunId: "run-iso" });

    const res = await tickHedgeBotWorkerForBotRun("run-iso", (hedgeId) => {
      if (hedgeId === "bad") throw new Error("synthetic");
      return { fundingWindowOpen: true, entryQty: 1.0 };
    });

    expect(res).toHaveLength(1);
    expect(res[0]).toMatchObject({ hedgeId: "ok", toStage: "ENTRY_PLACED" });
    expect(hedgesById.get("ok")?.status).toBe("OPENING");
    expect(hedgesById.get("bad")?.status).toBe("PLANNED");
  });
});

// ---------------------------------------------------------------------------
// 6. startHedgeBotWorker — env gating
// ---------------------------------------------------------------------------

describe("startHedgeBotWorker", () => {
  it("returns a no-op handle when ENABLE_HEDGE_WORKER is not set", async () => {
    delete process.env.ENABLE_HEDGE_WORKER;
    const handle = startHedgeBotWorker();
    expect(handle).toBeDefined();
    await handle.stop();
    // No tick should have run — no candidates queried.
    // We can't assert the timer count directly; the absence of a tick
    // means no hedges were created.
    expect(created).toHaveLength(0);
  });
});
