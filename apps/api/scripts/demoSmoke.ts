#!/usr/bin/env tsx
/**
 * Demo connectivity smoke harness — 30-минутный (по умолчанию) run одного
 * preset-бота на Bybit demo с проверкой acceptance условий из docs/53-T3.
 *
 * Назначение:
 *  - Подтвердить, что preset → бот → polling-loop → intents работает
 *    end-to-end на реальном demo-эндпоинте Bybit.
 *  - Дать operators воспроизводимый runbook для acceptance gate
 *    (docs/53-T3 / docs/54-T1..T3 / docs/55-T6 sub-gate funding-arb).
 *
 * Что harness НЕ делает:
 *  - Не оценивает торговую прибыль (это walk-forward в docs/53-T2 / 54-T1..T3).
 *  - Не переключает visibility (это `publishPreset.ts`).
 *  - Не работает с live trading (BYBIT_ALLOW_LIVE остаётся off — гарантия в
 *    bybitPlaceOrder, не в этом скрипте).
 *
 * Использование (требует demo creds + локально запущенный API):
 *
 *   pnpm --filter @botmarketplace/api exec tsx scripts/demoSmoke.ts \
 *     --preset adaptive-regime \
 *     --workspace ws_xyz \
 *     --connection conn_xyz \
 *     --token "$DEMO_JWT" \
 *     --admin-token "$ADMIN_API_TOKEN" \
 *     --base-url http://localhost:3001/api/v1 \
 *     --duration-min 30 \
 *     --symbol BTCUSDT \
 *     --quote-amount 50
 *
 * `--admin-token` обязателен пока target preset PRIVATE (все 5 флагманов
 * до publishPreset.ts флипа). Без него `/presets/:slug/instantiate`
 * вернёт 404 ("Preset not found" — намеренно скрывает существование).
 * Опускайте флаг только когда preset уже флипнут в BETA / PUBLIC.
 *
 * `--connection` обязателен. Без exchangeConnectionId на боте
 * `intentExecutor` (apps/api/src/lib/worker/intentExecutor.ts:93)
 * автосимулирует все intents без вызова Bybit — gate проходит «зелёным»,
 * но реально ничего не торгуется. Harness отказывается стартовать без
 * connection чтобы исключить эту иллюзию.
 *
 * Pre-flight (fail-fast перед instantiate):
 *  - connection.status === "CONNECTED" (свежий /test пройден)
 *  - BYBIT_ENV !== "live" (anti-live guard, демо-only)
 *  - TRADING_ENABLED не выключен (kill switch off → все intents в FAILED)
 *  - после instantiate bot.exchangeConnectionId === requested (catches DB rollback)
 *
 * Результат: JSON-отчёт в `apps/api/scripts/.smoke-output/<timestamp>-<slug>.json`
 * + summary в stdout. Exit codes: 0 = PASS, 1 = FAIL, 2 = INPUT_ERROR
 * (CLI/env валидация), 3 = PREFLIGHT_FAIL (connection/env/post-bind).
 */

import { mkdir, writeFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { PrismaClient } from "@prisma/client";

// ---------------------------------------------------------------------------
// CLI argument parsing — exported pure for tests
// ---------------------------------------------------------------------------

export interface ParsedSmokeArgs {
  preset?: string;
  workspace?: string;
  /** Required at validation step; carried separately so parseArgs stays a
   *  thin tokenizer. */
  connection?: string;
  token?: string;
  /**
   * X-Admin-Token shared secret. Required when the target preset has
   * visibility PRIVATE (true for every flagship until publishPreset.ts
   * flips it post-acceptance) — without it `/presets/:slug/instantiate`
   * returns 404 "Preset not found" by design (404 not 403 to avoid leaking
   * existence). Optional: omit when the preset is already BETA / PUBLIC.
   */
  adminToken?: string;
  baseUrl?: string;
  durationMin?: number;
  pollIntervalSec?: number;
  symbol?: string;
  quoteAmount?: number;
  outputDir?: string;
  dryRun: boolean;
}

export function parseArgs(argv: readonly string[]): ParsedSmokeArgs {
  const out: ParsedSmokeArgs = { dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--preset") out.preset = argv[++i];
    else if (arg === "--workspace") out.workspace = argv[++i];
    else if (arg === "--connection") out.connection = argv[++i];
    else if (arg === "--token") out.token = argv[++i];
    else if (arg === "--admin-token") out.adminToken = argv[++i];
    else if (arg === "--base-url") out.baseUrl = argv[++i];
    else if (arg === "--duration-min") out.durationMin = Number(argv[++i]);
    else if (arg === "--poll-interval-sec") out.pollIntervalSec = Number(argv[++i]);
    else if (arg === "--symbol") out.symbol = argv[++i];
    else if (arg === "--quote-amount") out.quoteAmount = Number(argv[++i]);
    else if (arg === "--output-dir") out.outputDir = argv[++i];
    else if (arg === "--dry-run") out.dryRun = true;
  }
  return out;
}

// ---------------------------------------------------------------------------
// Acceptance evaluation — pure function, easy to unit test
// ---------------------------------------------------------------------------

export interface SmokeMetrics {
  /** BotRunState на момент завершения скрипта (после stop). */
  finalRunState: string;
  /** Сколько polls было сделано (информативно). */
  pollCount: number;
  /** Общее число BotIntent для этого run'а. */
  intentCount: number;
  /** Число BotIntent с state="FAILED". */
  failedIntentCount: number;
  /** Число BotEvent, у которых type содержит "error" / "fail" (case-insensitive). */
  errorEventCount: number;
  /**
   * Число BotEvent с type="intent_simulated" — индикатор что бот скатился
   * в demo simulation mode (intentExecutor:93). Для acceptance gate это
   * HARD FAIL: simulation означает что Bybit не получил ни одного ордера,
   * gate бессмысленный.
   */
  simulatedEventCount: number;
  /**
   * Число BotEvent рыночных категорий (`market_*`, `candle_*`, `tick_*`,
   * `signal_*`, `regime_*`). Если 0 — engine не получает данные / poll-loop
   * мёртвый, отсутствие intents объясняется не flat market'ом, а сломанной
   * data-pipeline.
   */
  marketEventCount: number;
  /** Сколько HTTP запросов harness'а получили статус >= 400 (auth issues / rate limits). */
  harnessHttpFailures: number;
  /** Реальная длительность run'а в минутах. */
  actualDurationMin: number;
}

export interface SmokeAcceptance {
  pass: boolean;
  /** Warning (не fail). Например intentCount=0 при наличии market events
   *  и duration ≥ 15 мин — легитимный flat market. */
  warnings: string[];
  /** Конкретные причины fail (пусто если pass). */
  failures: string[];
}

/**
 * Acceptance критерии (docs/53-T3, расширено в #PR-после-effa475):
 *   1. finalRunState !== "FAILED" / "TIMED_OUT"  → fail.
 *   2. errorEventCount === 0                      → fail.
 *   3. harnessHttpFailures === 0                  → fail.
 *   4. failedIntentCount === 0                    → fail.
 *   5. simulatedEventCount === 0                  → fail (бот в sim-режиме).
 *   6. marketEventCount > 0                       → fail (engine не получает данные).
 *   7. intentCount > 0                            → graded warning:
 *        - duration < 15 min          → warning (короткий run, ок что 0)
 *        - market events ≥ 1 + ≥15min → warning (legit flat market)
 *
 * Pure function — все границы тестируются без сети.
 */
export function evaluateAcceptance(metrics: SmokeMetrics): SmokeAcceptance {
  const failures: string[] = [];
  const warnings: string[] = [];

  if (metrics.finalRunState === "FAILED" || metrics.finalRunState === "TIMED_OUT") {
    failures.push(`finalRunState=${metrics.finalRunState} (expected STOPPED)`);
  }
  if (metrics.errorEventCount > 0) {
    failures.push(`errorEventCount=${metrics.errorEventCount} (expected 0)`);
  }
  if (metrics.harnessHttpFailures > 0) {
    failures.push(`harnessHttpFailures=${metrics.harnessHttpFailures} (expected 0)`);
  }
  if (metrics.failedIntentCount > 0) {
    failures.push(`failedIntentCount=${metrics.failedIntentCount} (expected 0)`);
  }
  if (metrics.simulatedEventCount > 0) {
    failures.push(
      `simulatedEventCount=${metrics.simulatedEventCount} (expected 0 — bot fell back to ` +
      `demo simulation mode, exchangeConnectionId likely null)`,
    );
  }
  if (metrics.marketEventCount === 0) {
    failures.push(
      "marketEventCount=0 — strategy never received market data (engine / poll-loop broken)",
    );
  }
  if (metrics.intentCount === 0) {
    warnings.push(
      "intentCount=0 — strategy did not emit any intents; may be flat market or DSL bug, " +
      "operator should review logs and rerun if needed",
    );
  }
  return { pass: failures.length === 0, warnings, failures };
}

// ---------------------------------------------------------------------------
// HTTP / DB seam — interface so tests can swap with in-memory fakes
// ---------------------------------------------------------------------------

export interface InstantiateResponse {
  botId: string;
  strategyId: string;
  strategyVersionId: string;
  /** Echo of the connection bound to the new bot, or null when none was
   *  passed. Harness uses this for fail-fast bind verification. */
  exchangeConnectionId: string | null;
}

export interface RunResponse {
  id: string;
  state: string;
}

export interface ConnectionInfo {
  id: string;
  status: string;
  exchange: string;
}

export interface BotInfo {
  id: string;
  exchangeConnectionId: string | null;
}

export interface SmokeApi {
  /** GET /exchanges/:id (or Prisma-direct) — pre-flight pre-instantiate. */
  getConnection(id: string): Promise<ConnectionInfo | null>;

  /**
   * POST /presets/:slug/instantiate. `exchangeConnectionId` is forwarded
   * to the route, which validates cross-workspace + binds it to the new
   * bot.
   */
  instantiatePreset(input: {
    slug: string;
    workspaceId: string;
    exchangeConnectionId: string;
    overrides?: { symbol?: string; quoteAmount?: number; name?: string };
  }): Promise<InstantiateResponse>;

  /** Re-fetch bot after instantiate to verify the connection actually bound
   *  (catches DB rollback / silent route bypass). */
  getBot(botId: string): Promise<BotInfo | null>;

  /** POST /bots/:botId/runs. */
  startRun(input: { botId: string; durationMinutes: number }): Promise<RunResponse>;

  /** POST /bots/:botId/runs/:runId/stop. */
  stopRun(input: { botId: string; runId: string }): Promise<RunResponse>;

  /** GET BotRun row by id (через Prisma — поллим состояние). */
  getRun(runId: string): Promise<{ state: string; errorCode: string | null } | null>;

  /** Aggregate intent counts for a run (через Prisma). */
  countIntents(runId: string): Promise<{ total: number; failed: number }>;

  /** Aggregate error-flavoured BotEvent for a run (через Prisma). */
  countErrorEvents(runId: string): Promise<number>;

  /** Count BotEvent with type='intent_simulated' — proof bot fell into
   *  demo simulation mode (intentExecutor:93). Should be 0 for a real run. */
  countSimulatedEvents(runId: string): Promise<number>;

  /** Count BotEvent of market data category — non-zero proves the engine
   *  is alive, even when intentCount=0 (legit flat market). */
  countMarketEvents(runId: string): Promise<number>;

  /** First N orderId values from BotIntent (FILLED or PLACED). Lets the
   *  operator cross-check on bybit.com/demo/orders. */
  samplePlacedOrders(runId: string, limit: number): Promise<string[]>;
}

// ---------------------------------------------------------------------------
// Core orchestration — signature suitable for unit testing
// ---------------------------------------------------------------------------

export interface RunDemoSmokeArgs {
  presetSlug: string;
  workspaceId: string;
  exchangeConnectionId: string;
  durationMin: number;
  pollIntervalSec: number;
  overrides: { symbol?: string; quoteAmount?: number };
  api: SmokeApi;
  /** Inject sleep so tests advance virtual time without real waits. */
  sleep: (ms: number) => Promise<void>;
  /** Inject clock so tests can fix `actualDurationMin`. */
  now: () => number;
  /**
   * Snapshot of `process.env` at script invocation, captured by the
   * caller. Injected so unit tests can supply controlled values for the
   * BYBIT_ENV / TRADING_ENABLED pre-flight without mutating real env.
   */
  env: Record<string, string | undefined>;
  /** Optional sink for progress lines. */
  log?: (line: string) => void;
}

/** A pre-flight check failed — harness aborts before instantiate so the
 *  operator does not waste a 30-min run on a misconfigured environment. */
export class PreflightError extends Error {
  constructor(public readonly checks: string[]) {
    super(`demoSmoke pre-flight failed: ${checks.join("; ")}`);
    this.name = "PreflightError";
  }
}

export interface SmokeReport {
  presetSlug: string;
  workspaceId: string;
  exchangeConnectionId: string;
  /** "demo" / "live" / "unknown" — derived from BYBIT_ENV / BYBIT_BASE_URL
   *  at run start. Pre-flight rejects "live" outright, so successful
   *  reports are always "demo". Recorded for audit. */
  bybitEnv: "demo" | "live" | "unknown";
  startedAt: string;
  finishedAt: string;
  botId: string;
  runId: string;
  /** Up to 5 orderIds from this run — the operator pastes them into
   *  bybit.com/demo/orders to verify real exchange-side activity. */
  placedOrderSamples: string[];
  metrics: SmokeMetrics;
  acceptance: SmokeAcceptance;
}

/**
 * Resolve which Bybit environment is currently configured. Mirrors the
 * priority used by `apps/api/src/lib/bybitOrder.ts:getBybitBaseUrl` so
 * the report matches what the running api process actually talks to.
 */
export function resolveBybitEnv(env: Record<string, string | undefined>): "demo" | "live" | "unknown" {
  const baseUrl = env.BYBIT_BASE_URL;
  if (baseUrl) {
    if (baseUrl.includes("api.bybit.com")) return "live";
    if (baseUrl.includes("api-demo.bybit.com") || baseUrl.includes("api-testnet")) return "demo";
    return "unknown";
  }
  if (env.BYBIT_ENV === "live") return "live";
  return "demo"; // matches getBybitBaseUrl default
}

/**
 * Read the kill switch the same way `apps/api/src/lib/tradingKillSwitch.ts`
 * does — fail-open default, falsy aliases off.
 */
export function isTradingEnabled(env: Record<string, string | undefined>): boolean {
  const raw = env.TRADING_ENABLED;
  if (raw === undefined) return true; // fail-open
  const norm = raw.toLowerCase().trim();
  return !(norm === "false" || norm === "0" || norm === "off" || norm === "no");
}

/**
 * Pre-flight bundle. Pure: takes already-fetched connection plus env, returns
 * the list of failed checks (empty = OK).
 */
export function preflightChecks(input: {
  connection: ConnectionInfo | null;
  env: Record<string, string | undefined>;
}): string[] {
  const failures: string[] = [];

  if (!input.connection) {
    failures.push("connection not found in workspace (verify --connection id)");
  } else {
    if (input.connection.exchange !== "BYBIT") {
      failures.push(`connection.exchange=${input.connection.exchange} (expected BYBIT)`);
    }
    if (input.connection.status !== "CONNECTED") {
      failures.push(
        `connection.status=${input.connection.status} (expected CONNECTED — run /test endpoint first)`,
      );
    }
  }

  const bybitEnv = resolveBybitEnv(input.env);
  if (bybitEnv === "live") {
    failures.push("BYBIT_ENV=live (refuse — demoSmoke is demo-only by design)");
  }

  if (!isTradingEnabled(input.env)) {
    failures.push(
      "TRADING_ENABLED is off (every intent would land in FAILED state — fix env first)",
    );
  }

  return failures;
}

export async function runDemoSmoke(args: RunDemoSmokeArgs): Promise<SmokeReport> {
  const log = args.log ?? ((line: string) => console.log(line));
  const startedAt = args.now();
  let harnessHttpFailures = 0;

  // Helper that wraps each api call so a thrown error increments the
  // failure counter instead of bubbling out — we want the harness to
  // continue collecting metrics even after a transient network blip.
  const safeCall = async <T>(fn: () => Promise<T>, fallback: T): Promise<T> => {
    try {
      return await fn();
    } catch (err) {
      harnessHttpFailures++;
      log(`[demoSmoke] api call failed (#${harnessHttpFailures}): ${(err as Error).message}`);
      return fallback;
    }
  };

  log(
    `[demoSmoke] preset=${args.presetSlug} workspace=${args.workspaceId} ` +
    `connection=${args.exchangeConnectionId} duration=${args.durationMin}min`,
  );

  // ── Pre-flight: bail out before instantiate when env / connection are
  //    obviously misconfigured. Failures here throw `PreflightError` so
  //    `main()` can map to a distinct exit code (3) and the operator does
  //    not get a 30-minute "FAIL" report for a 1-second config issue.
  const connection = await args.api.getConnection(args.exchangeConnectionId);
  const preflightFailures = preflightChecks({ connection, env: args.env });
  if (preflightFailures.length > 0) {
    throw new PreflightError(preflightFailures);
  }
  const bybitEnv = resolveBybitEnv(args.env);
  log(`[demoSmoke] pre-flight OK · bybitEnv=${bybitEnv} · connection.status=CONNECTED`);

  const created = await args.api.instantiatePreset({
    slug: args.presetSlug,
    workspaceId: args.workspaceId,
    exchangeConnectionId: args.exchangeConnectionId,
    overrides: args.overrides,
  });
  log(`[demoSmoke] instantiated bot=${created.botId} strategy=${created.strategyId}`);

  // Post-instantiate verification: the route echoes back the bound
  // connection but a stale code path or DB rollback could have produced a
  // bot with `exchangeConnectionId: null` and we would silently slip into
  // simulation mode. Re-read the bot row to confirm.
  const bot = await args.api.getBot(created.botId);
  if (!bot || bot.exchangeConnectionId !== args.exchangeConnectionId) {
    throw new PreflightError([
      `bot.exchangeConnectionId=${bot?.exchangeConnectionId ?? "null"} ` +
      `(expected ${args.exchangeConnectionId} — instantiate likely ignored the field)`,
    ]);
  }
  log(`[demoSmoke] bot bind verified · exchangeConnectionId=${bot.exchangeConnectionId}`);

  const run = await args.api.startRun({ botId: created.botId, durationMinutes: args.durationMin });
  log(`[demoSmoke] started run=${run.id} state=${run.state}`);

  const totalMs = args.durationMin * 60_000;
  const pollMs = args.pollIntervalSec * 1000;
  const deadline = startedAt + totalMs;
  let pollCount = 0;
  let lastIntents = { total: 0, failed: 0 };
  let lastErrorEvents = 0;
  let lastState = run.state;

  while (args.now() < deadline) {
    pollCount++;
    await args.sleep(pollMs);

    const fresh = await safeCall(() => args.api.getRun(run.id), null);
    if (fresh) lastState = fresh.state;
    lastIntents = await safeCall(() => args.api.countIntents(run.id), lastIntents);
    lastErrorEvents = await safeCall(() => args.api.countErrorEvents(run.id), lastErrorEvents);

    log(
      `[demoSmoke] poll=${pollCount} state=${lastState} ` +
      `intents=${lastIntents.total} (failed=${lastIntents.failed}) errorEvents=${lastErrorEvents}`,
    );

    // Early-exit: если run уже в terminal state — нет смысла продолжать поллить.
    if (lastState === "FAILED" || lastState === "TIMED_OUT" || lastState === "STOPPED") {
      log(`[demoSmoke] run reached terminal state ${lastState}, exiting poll loop`);
      break;
    }
  }

  // Try to stop the run gracefully — но не считаем ошибку остановки за
  // failure если run уже в terminal state.
  if (lastState !== "FAILED" && lastState !== "TIMED_OUT" && lastState !== "STOPPED") {
    await safeCall(() => args.api.stopRun({ botId: created.botId, runId: run.id }), { id: run.id, state: lastState });
    const final = await safeCall(() => args.api.getRun(run.id), null);
    if (final) lastState = final.state;
  }

  // Final read-out — capture state after stop completed. The simulation /
  // market-event / placedOrders read happen exactly once at the end so the
  // harness's per-poll overhead is unchanged (existing CI baselines).
  lastIntents = await safeCall(() => args.api.countIntents(run.id), lastIntents);
  lastErrorEvents = await safeCall(() => args.api.countErrorEvents(run.id), lastErrorEvents);
  const simulatedEventCount = await safeCall(() => args.api.countSimulatedEvents(run.id), 0);
  const marketEventCount = await safeCall(() => args.api.countMarketEvents(run.id), 0);
  const placedOrderSamples = await safeCall(() => args.api.samplePlacedOrders(run.id, 5), []);

  const finishedAt = args.now();
  const metrics: SmokeMetrics = {
    finalRunState: lastState,
    pollCount,
    intentCount: lastIntents.total,
    failedIntentCount: lastIntents.failed,
    errorEventCount: lastErrorEvents,
    simulatedEventCount,
    marketEventCount,
    harnessHttpFailures,
    actualDurationMin: (finishedAt - startedAt) / 60_000,
  };
  const acceptance = evaluateAcceptance(metrics);

  return {
    presetSlug: args.presetSlug,
    workspaceId: args.workspaceId,
    exchangeConnectionId: args.exchangeConnectionId,
    bybitEnv,
    startedAt: new Date(startedAt).toISOString(),
    finishedAt: new Date(finishedAt).toISOString(),
    botId: created.botId,
    runId: run.id,
    placedOrderSamples,
    metrics,
    acceptance,
  };
}

// ---------------------------------------------------------------------------
// Default API implementation: HTTP for write paths, Prisma for read paths
// ---------------------------------------------------------------------------

interface BuildApiInput {
  baseUrl: string;
  token: string;
  /**
   * Workspace id for the `X-Workspace-Id` header. Every authed write route
   * resolves the active workspace from this header (`resolveWorkspace` in
   * `apps/api/src/lib/workspace.ts`); the body's `workspaceId` is ignored.
   * Without this header, `/presets/:slug/instantiate` returns 400 long
   * before pre-flight or auth checks have a chance to surface a clearer
   * message — the unit-test mocks bypass `resolveWorkspace`, so the gap
   * is invisible until a real run hits the route.
   */
  workspaceId: string;
  /**
   * Optional X-Admin-Token shared secret. When omitted the harness can
   * only target BETA / PUBLIC presets — `/presets/:slug/instantiate`
   * returns 404 for PRIVATE presets without admin (intentional 404-not-403
   * info-leak protection in `presets.ts:canViewPreset`). Every flagship
   * starts PRIVATE pre-acceptance, so demoSmoke runs against them require
   * this token. Routes that don't gate on admin (bots/runs) ignore the
   * header — including it in default headers when set is harmless.
   */
  adminToken?: string;
  prisma: PrismaClient;
}

export function buildDefaultApi(input: BuildApiInput): SmokeApi {
  const headers: Record<string, string> = {
    "content-type": "application/json",
    authorization: `Bearer ${input.token}`,
    "x-workspace-id": input.workspaceId,
  };
  if (input.adminToken) {
    headers["x-admin-token"] = input.adminToken;
  }

  async function postJson<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${input.baseUrl}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      // Operator-friendly hint: 404 on /presets/*/instantiate without admin
      // token is almost always a PRIVATE-visibility issue, not a missing
      // preset. Surface that interpretation so the operator does not chase
      // a phantom seed problem.
      let hint = "";
      if (
        res.status === 404 &&
        path.startsWith("/presets/") &&
        path.endsWith("/instantiate") &&
        !input.adminToken
      ) {
        hint =
          " | hint: target preset may be PRIVATE — every flagship is PRIVATE pre-acceptance. " +
          "Re-run with --admin-token \"$ADMIN_API_TOKEN\" (or set DEMO_SMOKE_ADMIN_TOKEN env var). " +
          "See docs/53-baseline-results.md §2 pre-flight checklist.";
      }
      throw new Error(`POST ${path} -> ${res.status} ${res.statusText}: ${text.slice(0, 200)}${hint}`);
    }
    return (await res.json()) as T;
  }

  return {
    async getConnection(id) {
      const row = await input.prisma.exchangeConnection.findUnique({
        where: { id },
        select: { id: true, status: true, exchange: true },
      });
      return row;
    },

    async instantiatePreset({ slug, workspaceId, exchangeConnectionId, overrides }) {
      return postJson<InstantiateResponse>(
        `/presets/${encodeURIComponent(slug)}/instantiate`,
        { workspaceId, exchangeConnectionId, overrides },
      );
    },

    async getBot(botId) {
      const row = await input.prisma.bot.findUnique({
        where: { id: botId },
        select: { id: true, exchangeConnectionId: true },
      });
      return row;
    },

    async startRun({ botId, durationMinutes }) {
      return postJson<RunResponse>(
        `/bots/${encodeURIComponent(botId)}/runs`,
        { durationMinutes },
      );
    },

    async stopRun({ botId, runId }) {
      return postJson<RunResponse>(
        `/bots/${encodeURIComponent(botId)}/runs/${encodeURIComponent(runId)}/stop`,
        {},
      );
    },

    async getRun(runId) {
      const row = await input.prisma.botRun.findUnique({
        where: { id: runId },
        select: { state: true, errorCode: true },
      });
      return row;
    },

    async countIntents(runId) {
      const [total, failed] = await Promise.all([
        input.prisma.botIntent.count({ where: { botRunId: runId } }),
        input.prisma.botIntent.count({ where: { botRunId: runId, state: "FAILED" } }),
      ]);
      return { total, failed };
    },

    async countErrorEvents(runId) {
      const events = await input.prisma.botEvent.findMany({
        where: { botRunId: runId },
        select: { type: true, payloadJson: true },
      });
      return events.filter((e) => isErrorEvent(e.type, e.payloadJson)).length;
    },

    async countSimulatedEvents(runId) {
      return input.prisma.botEvent.count({
        where: { botRunId: runId, type: "intent_simulated" },
      });
    },

    async countMarketEvents(runId) {
      // Match the categories listed in SmokeMetrics.marketEventCount JSDoc.
      // Bybit-side evaluator emits e.g. "regime_check", "signal_entry",
      // "candle_close" — proof the engine is alive even on flat market.
      return input.prisma.botEvent.count({
        where: {
          botRunId: runId,
          OR: [
            { type: { startsWith: "market_" } },
            { type: { startsWith: "candle_" } },
            { type: { startsWith: "tick_" } },
            { type: { startsWith: "signal_" } },
            { type: { startsWith: "regime_" } },
          ],
        },
      });
    },

    async samplePlacedOrders(runId, limit) {
      const rows = await input.prisma.botIntent.findMany({
        where: {
          botRunId: runId,
          orderId: { not: null },
        },
        select: { orderId: true },
        orderBy: { createdAt: "asc" },
        take: limit,
      });
      return rows.map((r) => r.orderId).filter((id): id is string => !!id);
    },
  };
}

/**
 * Heuristic для error-event detection. Берём:
 *   - явные RUN_FAILED / RUN_RECONCILED_FAILED / *_ERROR types,
 *   - либо payload содержит `error` / `failed` ключ верхнего уровня.
 * Намеренно простая логика — операторы сами читают smokeOutput JSON
 * для разбора root cause.
 */
export function isErrorEvent(type: string, payload: unknown): boolean {
  const t = type.toLowerCase();
  if (t.includes("fail") || t.includes("error")) return true;
  if (payload && typeof payload === "object") {
    const obj = payload as Record<string, unknown>;
    if ("error" in obj && obj.error != null) return true;
    if ("failed" in obj && obj.failed === true) return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Process entry point
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);

const isDirectInvocation = (() => {
  if (typeof process === "undefined" || !process.argv[1]) return false;
  const entry = process.argv[1];
  return entry.endsWith("demoSmoke.ts") || entry.endsWith("demoSmoke.js");
})();

export interface ValidatedSmokeConfig {
  preset: string;
  workspace: string;
  connection: string;
  token: string;
  /** Optional X-Admin-Token; required when preset visibility is PRIVATE. */
  adminToken?: string;
  baseUrl: string;
  durationMin: number;
  pollIntervalSec: number;
  symbol?: string;
  quoteAmount?: number;
  outputDir: string;
  dryRun: boolean;
}

export type ValidationResult =
  | { kind: "ok"; config: ValidatedSmokeConfig }
  | { kind: "error"; reason: string };

/** Валидирует CLI-аргументы / env. Pure, чтобы тесты могли проверить
 *  все error-paths без spawn'а процесса. */
export function validateCliArgs(parsed: ParsedSmokeArgs, env: Record<string, string | undefined>): ValidationResult {
  const preset = parsed.preset ?? env.DEMO_SMOKE_PRESET;
  const workspace = parsed.workspace ?? env.DEMO_SMOKE_WORKSPACE;
  const connection = parsed.connection ?? env.DEMO_SMOKE_CONNECTION;
  const token = parsed.token ?? env.DEMO_SMOKE_TOKEN;
  const adminToken = parsed.adminToken ?? env.DEMO_SMOKE_ADMIN_TOKEN;
  const baseUrl = parsed.baseUrl ?? env.DEMO_SMOKE_BASE_URL ?? "http://localhost:3001/api/v1";

  if (!preset) return { kind: "error", reason: "--preset <slug> is required (or DEMO_SMOKE_PRESET)" };
  if (!workspace) return { kind: "error", reason: "--workspace <id> is required (or DEMO_SMOKE_WORKSPACE)" };
  if (!connection) {
    return {
      kind: "error",
      reason:
        "--connection <id> is required (or DEMO_SMOKE_CONNECTION). Without it the bot stays in " +
        "demo simulation mode (intentExecutor:93) and the run does not exercise Bybit at all. " +
        "Get the id from /exchanges UI or `pnpm --filter @botmarketplace/api exec prisma studio` " +
        "→ ExchangeConnection table.",
    };
  }
  if (!token) return { kind: "error", reason: "--token <jwt> is required (or DEMO_SMOKE_TOKEN)" };

  const durationMin = parsed.durationMin ?? 30;
  if (!Number.isFinite(durationMin) || durationMin < 1 || durationMin > 1440) {
    return { kind: "error", reason: `--duration-min must be 1..1440 (got ${parsed.durationMin})` };
  }

  const pollIntervalSec = parsed.pollIntervalSec ?? 60;
  if (!Number.isFinite(pollIntervalSec) || pollIntervalSec < 1 || pollIntervalSec > 600) {
    return { kind: "error", reason: `--poll-interval-sec must be 1..600 (got ${parsed.pollIntervalSec})` };
  }

  const outputDir = parsed.outputDir ?? join(dirname(__filename), ".smoke-output");

  return {
    kind: "ok",
    config: {
      preset,
      workspace,
      connection,
      token,
      adminToken,
      baseUrl,
      durationMin,
      pollIntervalSec,
      symbol: parsed.symbol,
      quoteAmount: parsed.quoteAmount,
      outputDir,
      dryRun: parsed.dryRun,
    },
  };
}

async function main(): Promise<number> {
  const cli = parseArgs(process.argv.slice(2));
  const validated = validateCliArgs(cli, process.env);
  if (validated.kind === "error") {
    console.error(`error: ${validated.reason}`);
    return 2;
  }

  const cfg = validated.config;

  if (cfg.dryRun) {
    console.log("[demoSmoke] dry-run — config validated, no run executed:");
    console.log(JSON.stringify({
      ...cfg,
      token: "<redacted>",
      adminToken: cfg.adminToken ? "<redacted>" : undefined,
    }, null, 2));
    return 0;
  }

  const prisma = new PrismaClient();
  const api = buildDefaultApi({
    baseUrl: cfg.baseUrl,
    token: cfg.token,
    workspaceId: cfg.workspace,
    adminToken: cfg.adminToken,
    prisma,
  });

  try {
    const report = await runDemoSmoke({
      presetSlug: cfg.preset,
      workspaceId: cfg.workspace,
      exchangeConnectionId: cfg.connection,
      durationMin: cfg.durationMin,
      pollIntervalSec: cfg.pollIntervalSec,
      overrides: { symbol: cfg.symbol, quoteAmount: cfg.quoteAmount },
      api,
      sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
      now: () => Date.now(),
      env: process.env,
    });

    await mkdir(cfg.outputDir, { recursive: true });
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const outPath = join(cfg.outputDir, `${ts}-${cfg.preset}.json`);
    await writeFile(outPath, JSON.stringify(report, null, 2), "utf-8");

    console.log("\n=== demoSmoke summary ===");
    console.log(`preset:        ${report.presetSlug}`);
    console.log(`run:           ${report.runId}`);
    console.log(`bybitEnv:      ${report.bybitEnv}`);
    console.log(`connection:    ${report.exchangeConnectionId}`);
    console.log(`finalState:    ${report.metrics.finalRunState}`);
    console.log(`intents:       ${report.metrics.intentCount} (failed=${report.metrics.failedIntentCount})`);
    console.log(`marketEvents:  ${report.metrics.marketEventCount}`);
    console.log(`simulated:     ${report.metrics.simulatedEventCount}`);
    console.log(`errorEvents:   ${report.metrics.errorEventCount}`);
    console.log(`httpFailures:  ${report.metrics.harnessHttpFailures}`);
    console.log(`durationMin:   ${report.metrics.actualDurationMin.toFixed(2)}`);
    console.log(`orderSamples:  ${report.placedOrderSamples.length ? report.placedOrderSamples.join(", ") : "(none)"}`);
    console.log(`acceptance:    ${report.acceptance.pass ? "PASS" : "FAIL"}`);
    if (report.acceptance.warnings.length) {
      console.log(`warnings:      ${report.acceptance.warnings.join("; ")}`);
    }
    if (report.acceptance.failures.length) {
      console.log(`failures:      ${report.acceptance.failures.join("; ")}`);
    }
    console.log(`report:        ${outPath}`);

    return report.acceptance.pass ? 0 : 1;
  } catch (err) {
    if (err instanceof PreflightError) {
      console.error("\n[demoSmoke] pre-flight FAILED — aborting before instantiate:");
      for (const c of err.checks) console.error(`  ✗ ${c}`);
      console.error(
        "\nFix the underlying environment / connection state and rerun. " +
        "No bot was created; no run was started.",
      );
      return 3;
    }
    throw err;
  } finally {
    await prisma.$disconnect();
  }
}

if (isDirectInvocation) {
  main()
    .then((code) => process.exit(code))
    .catch((err) => {
      console.error("[demoSmoke] fatal error:", err);
      process.exit(1);
    });
}
