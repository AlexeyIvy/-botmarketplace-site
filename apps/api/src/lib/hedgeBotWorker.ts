/**
 * Funding-arbitrage runtime skeleton (docs/55-T4).
 *
 * A dedicated worker that runs alongside `botWorker.ts` (it does NOT replace
 * or compete with it) and progresses each `HedgePosition` through the
 * funding-arb state machine on a 60-second cadence.
 *
 * Stage names (this file)   ↔ persisted `HedgeStatus` (Prisma):
 *   PENDING       ↔ PLANNED   — hedge created, awaiting funding window.
 *   ENTRY_PLACED  ↔ OPENING   — entry BotIntents emitted, awaiting fills.
 *   BOTH_FILLED   ↔ OPEN      — both entry legs FILLED; transient → ACTIVE.
 *   ACTIVE        ↔ OPEN      — hedge live, awaiting funding payment.
 *   EXIT_PLACED   ↔ CLOSING   — exit BotIntents emitted, awaiting fills.
 *   CLOSED        ↔ CLOSED    — both exit legs FILLED.
 *   ERRORED       ↔ FAILED    — partial fill / unrecoverable error.
 *
 * What this skeleton DOES today:
 *   * Finds eligible hedges (status ∈ PLANNED/OPENING/OPEN/CLOSING).
 *   * Reads input signals (`fundingWindowOpen`, `fundingPaymentReceived`)
 *     from the caller and decides the next stage.
 *   * Emits `BotIntent` rows with `metaJson.category = "spot" | "linear"` —
 *     funding-arb's two-leg pattern, mirroring `routes/hedges.ts`.
 *   * Advances persisted `HedgeStatus` based on `BotIntent.state` of the
 *     emitted legs (FILLED on both ⇒ progress; CANCELLED/FAILED on either
 *     ⇒ ERRORED).
 *   * Isolates per-hedge errors: one bad hedge does not crash the loop.
 *   * Boots only when `ENABLE_HEDGE_WORKER === "true"` is set, so the
 *     mainline `botWorker.ts` runtime is unaffected by this skeleton.
 *
 * What this skeleton DOES NOT do (deferred to 55-T2):
 *   * Place actual Bybit orders. The fills used to drive the state machine
 *     come from `BotIntent.state` written by the existing `intentExecutor`
 *     pipeline — once 55-T2 wires `bybitOrder.ts` with category dispatch,
 *     the spot leg will execute end-to-end with no changes here.
 *   * Run a Bybit balance reconciliation. 55-T5 introduced
 *     `balanceReconciler.ts` for that; this skeleton intentionally does
 *     not call it yet to keep the diff minimal.
 *   * Resolve the funding window itself. Callers pass that signal in via
 *     `HedgeAdvanceInput`; the live wiring (Bybit funding scanner) lands
 *     with 55-T3 / 55-T4 follow-up.
 */

import { randomUUID } from "node:crypto";
import { prisma } from "./prisma.js";
import { logger } from "./logger.js";
import { classifyExecutionError } from "./errorClassifier.js";
import {
  reconcileBalances,
  type ExchangeConnectionCreds,
} from "./exchange/balanceReconciler.js";
import { detectFundingWindow } from "./funding/windowDetector.js";

const log = logger.child({ module: "hedgeBotWorker" });

const DEFAULT_TICK_INTERVAL_MS = 60_000;

function getTickIntervalMs(): number {
  const raw = parseInt(process.env.HEDGE_WORKER_TICK_MS ?? "", 10);
  return Number.isFinite(raw) && raw > 0 ? raw : DEFAULT_TICK_INTERVAL_MS;
}

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export type HedgeStage =
  | "PENDING"
  | "ENTRY_PLACED"
  | "BOTH_FILLED"
  | "ACTIVE"
  | "EXIT_PLACED"
  | "CLOSED"
  | "ERRORED";

/** `HedgeStatus` enum values — duplicated here to avoid importing the
 *  generated Prisma enum object (keeps the skeleton agnostic of the
 *  generator-output layout). */
export type PersistedHedgeStatus =
  | "PLANNED"
  | "OPENING"
  | "OPEN"
  | "CLOSING"
  | "CLOSED"
  | "FAILED";

const STAGE_TO_STATUS: Record<HedgeStage, PersistedHedgeStatus> = {
  PENDING: "PLANNED",
  ENTRY_PLACED: "OPENING",
  BOTH_FILLED: "OPEN",
  ACTIVE: "OPEN",
  EXIT_PLACED: "CLOSING",
  CLOSED: "CLOSED",
  ERRORED: "FAILED",
};

/** Inputs the caller (or test) supplies for one `advanceHedge` call. */
export interface HedgeAdvanceInput {
  /** True when the upstream funding scanner says we're inside the entry
   *  window for this hedge — drives PENDING → ENTRY_PLACED. */
  fundingWindowOpen?: boolean;
  /** True when the Bybit funding-payment ledger shows the payment landed —
   *  drives ACTIVE → EXIT_PLACED. */
  fundingPaymentReceived?: boolean;
  /** Quantity to size each leg with on entry (base units). */
  entryQty?: number;
  /** Quantity to size each leg with on exit (base units). Defaults to
   *  whatever was used on entry. */
  exitQty?: number;
  /**
   * Optional balance-reconcile callback invoked at the PENDING → ENTRY_PLACED
   * transition only (docs/55-T5 §3). When provided:
   *   - The hedge symbol's classification must be "flat" for entry to proceed.
   *     Any non-flat result (perp_only / spot_only / balanced / imbalanced)
   *     is treated as "position already exists" and entry is skipped to
   *     avoid double-position errors.
   *   - A thrown error is logged and treated as transient — the tick
   *     produces no state change so the next tick will retry. funding-arb
   *     errors must not crash the worker.
   *
   * When omitted, the balance check is skipped entirely. This keeps unit
   * tests that exercise the state machine in isolation simple, and lets
   * `tickHedgeBotWorker` decide per-hedge whether to load creds + wire a
   * real reconciler.
   */
  reconcileBeforeEntry?: () => Promise<{
    hedgeStatus: Array<{ symbol: string; status: string }>;
  }>;
}

export interface HedgeAdvanceResult {
  hedgeId: string;
  /** Stage the hedge was in BEFORE this tick. */
  fromStage: HedgeStage;
  /** Stage the hedge is in AFTER this tick. */
  toStage: HedgeStage;
  /** True if `toStage !== fromStage`. */
  changed: boolean;
}

// ---------------------------------------------------------------------------
// Stage helpers
// ---------------------------------------------------------------------------

/** Map persisted `HedgeStatus` → stage label.
 *
 *  `OPEN` maps to `ACTIVE` here — `BOTH_FILLED` is a transient intra-tick
 *  marker that callers see in the return value of a tick that just
 *  advanced from ENTRY_PLACED. */
function statusToStage(status: PersistedHedgeStatus): HedgeStage {
  switch (status) {
    case "PLANNED": return "PENDING";
    case "OPENING": return "ENTRY_PLACED";
    case "OPEN":    return "ACTIVE";
    case "CLOSING": return "EXIT_PLACED";
    case "CLOSED":  return "CLOSED";
    case "FAILED":  return "ERRORED";
  }
}

// ---------------------------------------------------------------------------
// Intent emission
// ---------------------------------------------------------------------------

interface EmitArgs {
  hedgeId: string;
  botRunId: string;
  symbol: string;
  qty: number;
  /** "ENTRY" emits perp short + spot long; "EXIT" emits perp close + spot sell. */
  type: "ENTRY" | "EXIT";
}

/** Persist two `BotIntent` rows + bump `HedgeStatus`. Mirrors the
 *  hedges-route `/execute` and `/exit` payload shape so 55-T2 can wire
 *  real execution without touching this code. */
async function emitHedgeIntents(args: EmitArgs): Promise<void> {
  const isEntry = args.type === "ENTRY";
  const spotIntentId = `hedge-${args.hedgeId}-spot-${isEntry ? "entry" : "exit"}`;
  const perpIntentId = `hedge-${args.hedgeId}-perp-${isEntry ? "entry" : "exit"}`;

  const nextStatus: PersistedHedgeStatus = isEntry ? "OPENING" : "CLOSING";

  await prisma.$transaction([
    prisma.botIntent.create({
      data: {
        botRunId: args.botRunId,
        intentId: spotIntentId,
        orderLinkId: randomUUID(),
        type: args.type,
        state: "PENDING",
        side: isEntry ? "BUY" : "SELL",
        qty: args.qty,
        metaJson: {
          hedgeId: args.hedgeId,
          legSide: isEntry ? "SPOT_BUY" : "SPOT_SELL",
          // TODO(55-T2): wire bybitOrder.ts with category dispatch — the
          // spot leg is the one this category routing unlocks.
          category: "spot",
        },
      },
    }),
    prisma.botIntent.create({
      data: {
        botRunId: args.botRunId,
        intentId: perpIntentId,
        orderLinkId: randomUUID(),
        type: args.type,
        state: "PENDING",
        side: isEntry ? "SELL" : "BUY",
        qty: args.qty,
        metaJson: {
          hedgeId: args.hedgeId,
          legSide: isEntry ? "PERP_SHORT" : "PERP_CLOSE",
          category: "linear",
        },
      },
    }),
    prisma.hedgePosition.update({
      where: { id: args.hedgeId },
      data: { status: nextStatus },
    }),
  ]);
}

// ---------------------------------------------------------------------------
// Intent state inspection
// ---------------------------------------------------------------------------

interface LegStateSummary {
  /** Both legs FILLED. */
  bothFilled: boolean;
  /** Any leg in a terminal failure state (CANCELLED | FAILED). */
  anyTerminalFailure: boolean;
  /** Total intents found for this hedge + stage. */
  count: number;
}

async function summariseLegStates(
  hedgeId: string,
  botRunId: string,
  type: "ENTRY" | "EXIT",
): Promise<LegStateSummary> {
  const intents = await prisma.botIntent.findMany({
    where: { botRunId, type },
    select: { state: true, metaJson: true, intentId: true },
  });
  // Filter to the two intents created for this hedge — `metaJson.hedgeId`
  // is the canonical link.
  const matching = intents.filter((i) => {
    const meta = i.metaJson as { hedgeId?: string } | null;
    return meta?.hedgeId === hedgeId;
  });
  const filled = matching.filter((i) => i.state === "FILLED").length;
  const failed = matching.filter((i) => i.state === "CANCELLED" || i.state === "FAILED").length;
  return {
    bothFilled: matching.length === 2 && filled === 2,
    anyTerminalFailure: failed > 0,
    count: matching.length,
  };
}

// ---------------------------------------------------------------------------
// Single-hedge advance
// ---------------------------------------------------------------------------

/**
 * Advance one hedge by at most one stage based on persisted state +
 * caller-provided signals. Pure-ish: every side-effect goes through
 * `prisma`, so tests mock that surface and exercise the state machine
 * without standing up a database.
 */
export async function advanceHedge(
  hedgeId: string,
  input: HedgeAdvanceInput = {},
): Promise<HedgeAdvanceResult> {
  const hedge = await prisma.hedgePosition.findUnique({
    where: { id: hedgeId },
  });
  if (!hedge) {
    log.warn({ hedgeId }, "advanceHedge: hedge not found");
    return { hedgeId, fromStage: "ERRORED", toStage: "ERRORED", changed: false };
  }

  const fromStage = statusToStage(hedge.status as PersistedHedgeStatus);

  switch (hedge.status as PersistedHedgeStatus) {
    case "PLANNED": {
      if (!input.fundingWindowOpen) {
        return { hedgeId, fromStage, toStage: fromStage, changed: false };
      }
      const qty = input.entryQty ?? 0;
      if (qty <= 0) {
        log.warn({ hedgeId, qty }, "PENDING → ENTRY_PLACED skipped: entryQty must be > 0");
        return { hedgeId, fromStage, toStage: fromStage, changed: false };
      }

      // Balance gate (docs/55-T5 §3). Optional: when no reconciler is
      // supplied the check is skipped — keeps unit tests minimal and
      // lets the caller (tickHedgeBotWorker) decide per-hedge whether
      // to load credentials.
      if (input.reconcileBeforeEntry) {
        let recon: Awaited<ReturnType<NonNullable<HedgeAdvanceInput["reconcileBeforeEntry"]>>>;
        try {
          recon = await input.reconcileBeforeEntry();
        } catch (err) {
          log.error(
            { err, hedgeId, symbol: hedge.symbol },
            "balance reconcile failed — deferring entry to next tick (transient)",
          );
          return { hedgeId, fromStage, toStage: fromStage, changed: false };
        }
        const symbolStatus = recon.hedgeStatus.find((s) => s.symbol === hedge.symbol);
        if (symbolStatus && symbolStatus.status !== "flat") {
          log.warn(
            { hedgeId, symbol: hedge.symbol, status: symbolStatus.status },
            "PENDING → ENTRY_PLACED refused: existing perp / spot position for symbol",
          );
          return { hedgeId, fromStage, toStage: fromStage, changed: false };
        }
      }

      await emitHedgeIntents({
        hedgeId,
        botRunId: hedge.botRunId,
        symbol: hedge.symbol,
        qty,
        type: "ENTRY",
      });
      log.info({ hedgeId, qty }, "PENDING → ENTRY_PLACED");
      return { hedgeId, fromStage, toStage: "ENTRY_PLACED", changed: true };
    }

    case "OPENING": {
      const summary = await summariseLegStates(hedgeId, hedge.botRunId, "ENTRY");
      if (summary.anyTerminalFailure) {
        await prisma.hedgePosition.update({
          where: { id: hedgeId },
          data: { status: STAGE_TO_STATUS.ERRORED },
        });
        log.error({ hedgeId, summary }, "ENTRY_PLACED → ERRORED (partial fill / failure)");
        return { hedgeId, fromStage, toStage: "ERRORED", changed: true };
      }
      if (summary.bothFilled) {
        await prisma.hedgePosition.update({
          where: { id: hedgeId },
          data: { status: STAGE_TO_STATUS.ACTIVE },
        });
        log.info({ hedgeId }, "ENTRY_PLACED → BOTH_FILLED → ACTIVE");
        return { hedgeId, fromStage, toStage: "ACTIVE", changed: true };
      }
      return { hedgeId, fromStage, toStage: fromStage, changed: false };
    }

    case "OPEN": {
      if (!input.fundingPaymentReceived) {
        return { hedgeId, fromStage, toStage: fromStage, changed: false };
      }
      const exitQty = input.exitQty ?? input.entryQty ?? 0;
      if (exitQty <= 0) {
        log.warn({ hedgeId, exitQty }, "ACTIVE → EXIT_PLACED skipped: exitQty must be > 0");
        return { hedgeId, fromStage, toStage: fromStage, changed: false };
      }
      await emitHedgeIntents({
        hedgeId,
        botRunId: hedge.botRunId,
        symbol: hedge.symbol,
        qty: exitQty,
        type: "EXIT",
      });
      log.info({ hedgeId, exitQty }, "ACTIVE → EXIT_PLACED");
      return { hedgeId, fromStage, toStage: "EXIT_PLACED", changed: true };
    }

    case "CLOSING": {
      const summary = await summariseLegStates(hedgeId, hedge.botRunId, "EXIT");
      if (summary.anyTerminalFailure) {
        await prisma.hedgePosition.update({
          where: { id: hedgeId },
          data: { status: STAGE_TO_STATUS.ERRORED },
        });
        log.error({ hedgeId, summary }, "EXIT_PLACED → ERRORED (exit fill failure)");
        return { hedgeId, fromStage, toStage: "ERRORED", changed: true };
      }
      if (summary.bothFilled) {
        await prisma.hedgePosition.update({
          where: { id: hedgeId },
          data: { status: STAGE_TO_STATUS.CLOSED, closedAt: new Date() },
        });
        log.info({ hedgeId }, "EXIT_PLACED → CLOSED");
        return { hedgeId, fromStage, toStage: "CLOSED", changed: true };
      }
      return { hedgeId, fromStage, toStage: fromStage, changed: false };
    }

    case "CLOSED":
    case "FAILED":
      return { hedgeId, fromStage, toStage: fromStage, changed: false };
  }
}

// ---------------------------------------------------------------------------
// Tick loop
// ---------------------------------------------------------------------------

/**
 * Load the exchange credentials linked to a hedge via its BotRun → Bot →
 * ExchangeConnection chain. Returns null if any link is missing — the
 * caller treats null as "skip the balance check" (safer than blocking
 * forever on a misconfigured bot).
 *
 * The select intentionally pulls only the four credential columns the
 * reconciler needs; nothing else from ExchangeConnection leaks to the
 * worker context.
 */
async function loadHedgeCreds(botRunId: string): Promise<ExchangeConnectionCreds | null> {
  const run = await prisma.botRun.findUnique({
    where: { id: botRunId },
    select: {
      bot: {
        select: {
          exchangeConnection: {
            select: {
              apiKey: true,
              encryptedSecret: true,
              spotApiKey: true,
              spotEncryptedSecret: true,
            },
          },
        },
      },
    },
  });
  return run?.bot?.exchangeConnection ?? null;
}

type HedgeCandidate = { id: string; symbol: string; botRunId: string };

const NON_TERMINAL_STATUSES = ["PLANNED", "OPENING", "OPEN", "CLOSING"] as const;

/** Shared advance loop. Per-hedge errors are logged + classified but NEVER
 *  bubble — funding-arb errors must not take down the worker. Used by both
 *  the global `tickHedgeBotWorker` and the bot-scoped
 *  `tickHedgeBotWorkerForBotRun` so the inputResolver / default-input
 *  semantics stay identical regardless of how candidates were sourced. */
async function advanceCandidates(
  candidates: HedgeCandidate[],
  inputResolver?: (hedgeId: string) => HedgeAdvanceInput | Promise<HedgeAdvanceInput>,
): Promise<HedgeAdvanceResult[]> {
  const out: HedgeAdvanceResult[] = [];
  for (const c of candidates) {
    try {
      const input = inputResolver
        ? await inputResolver(c.id)
        : await buildDefaultInput(c);
      const res = await advanceHedge(c.id, input);
      out.push(res);
    } catch (err) {
      const classification = classifyExecutionError(err);
      log.error({ err, hedgeId: c.id, classification }, "hedge advance failed (isolated)");
      // Swallow — funding-arb tick must keep ticking for other hedges.
    }
  }
  return out;
}

/** One pass: advance every non-terminal hedge across the whole installation.
 *
 *  Behaviour:
 *   - Default path (no `inputResolver` supplied): for each hedge, load
 *     creds via `loadHedgeCreds` and wire a `reconcileBeforeEntry`
 *     callback so the PENDING → ENTRY_PLACED gate consults the live
 *     Bybit wallet (docs/55-T5 §3). Hedges whose Bot has no linked
 *     ExchangeConnection skip the check (callback omitted) — no
 *     blocking, just a warning in the log.
 *   - Caller-supplied path (`inputResolver` provided): tests + advanced
 *     callers fully own the input shape. The default credential loader
 *     is NOT layered underneath — explicit beats implicit.
 *
 *  Funding-window / funding-payment signals must still be supplied by
 *  whichever upstream owns scanner / payment-ledger lookups (out of
 *  scope for this PR — currently absent, so PENDING / ACTIVE hedges
 *  no-op until that wiring lands).
 *
 *  Used by the env-gated `startHedgeBotWorker` daemon. Per-bot delegation
 *  from the mainline botWorker poll lives in `tickHedgeBotWorkerForBotRun`.
 */
export async function tickHedgeBotWorker(
  inputResolver?: (hedgeId: string) => HedgeAdvanceInput | Promise<HedgeAdvanceInput>,
): Promise<HedgeAdvanceResult[]> {
  const candidates = await prisma.hedgePosition.findMany({
    where: { status: { in: [...NON_TERMINAL_STATUSES] } },
    select: { id: true, symbol: true, botRunId: true },
  });
  return advanceCandidates(candidates, inputResolver);
}

/** Bot-scoped variant: advance only the non-terminal hedges that belong to
 *  one BotRun. Used by `botWorker.evaluateStrategies` to delegate
 *  FUNDING_ARB bots — the DSL evaluator already short-circuits on
 *  `bot.mode === "FUNDING_ARB"`, so this call replaces the no-op skip with
 *  a real per-bot tick that runs every botWorker poll (4s) instead of the
 *  60s global daemon cadence. Same advance semantics as the global tick,
 *  just narrower findMany. */
export async function tickHedgeBotWorkerForBotRun(
  botRunId: string,
  inputResolver?: (hedgeId: string) => HedgeAdvanceInput | Promise<HedgeAdvanceInput>,
): Promise<HedgeAdvanceResult[]> {
  const candidates = await prisma.hedgePosition.findMany({
    where: { botRunId, status: { in: [...NON_TERMINAL_STATUSES] } },
    select: { id: true, symbol: true, botRunId: true },
  });
  return advanceCandidates(candidates, inputResolver);
}

/**
 * Default `HedgeAdvanceInput` builder used when no `inputResolver` is
 * supplied. Wires the reconciler callback so production ticks consult
 * the live Bybit wallet at the entry gate, and derives funding-window
 * signals from the latest `FundingSnapshot.nextFundingAt` via
 * `detectFundingWindow`. Read-only; safe to call concurrently across
 * hedges within one tick.
 */
async function buildDefaultInput(
  hedge: { id: string; symbol: string; botRunId: string },
): Promise<HedgeAdvanceInput> {
  const window = await detectFundingWindow(hedge.symbol, Date.now());
  const creds = await loadHedgeCreds(hedge.botRunId);

  if (!creds) {
    log.warn(
      { hedgeId: hedge.id, symbol: hedge.symbol },
      "no ExchangeConnection linked — balance check skipped",
    );
    return {
      fundingWindowOpen: window.open,
      fundingPaymentReceived: window.paymentReceived,
    };
  }
  return {
    fundingWindowOpen: window.open,
    fundingPaymentReceived: window.paymentReceived,
    reconcileBeforeEntry: () => reconcileBalances(creds, [hedge.symbol]),
  };
}

// ---------------------------------------------------------------------------
// Boot — env-gated, intentionally NOT wired into server.ts yet
// ---------------------------------------------------------------------------

interface HedgeWorkerHandle {
  stop(): Promise<void>;
}

/**
 * Boot the funding-arb runtime. Only starts a tick timer when
 * `ENABLE_HEDGE_WORKER === "true"`; otherwise returns a no-op handle so
 * the call site is safe to add to `server.ts` without changing default
 * behaviour. The mainline `botWorker.ts` is untouched by this skeleton.
 */
export function startHedgeBotWorker(
  inputResolver?: (hedgeId: string) => HedgeAdvanceInput | Promise<HedgeAdvanceInput>,
): HedgeWorkerHandle {
  if (process.env.ENABLE_HEDGE_WORKER !== "true") {
    log.info("ENABLE_HEDGE_WORKER not set — hedgeBotWorker skipped (default off)");
    return { stop: async () => {} };
  }

  const tickMs = getTickIntervalMs();
  log.info({ tickMs }, "hedgeBotWorker started");

  let stopped = false;
  let inFlight: Promise<unknown> | null = null;

  async function wrappedTick() {
    if (stopped || inFlight) return;
    inFlight = tickHedgeBotWorker(inputResolver).catch((err) => {
      log.error({ err }, "tickHedgeBotWorker top-level failure");
    });
    await inFlight;
    inFlight = null;
  }

  const timer = setInterval(wrappedTick, tickMs);
  // Run once immediately so the first hedge doesn't wait a full tick.
  wrappedTick();

  return {
    stop: async () => {
      stopped = true;
      clearInterval(timer);
      if (inFlight) await inFlight;
      log.info("hedgeBotWorker stopped");
    },
  };
}
