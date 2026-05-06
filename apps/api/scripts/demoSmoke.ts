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
 *     --token "$DEMO_JWT" \
 *     --base-url http://localhost:3001/api/v1 \
 *     --duration-min 30 \
 *     --symbol BTCUSDT \
 *     --quote-amount 50
 *
 * Результат: JSON-отчёт в `apps/api/scripts/.smoke-output/<timestamp>-<slug>.json`
 * + summary в stdout. Exit code 0 = PASS, 1 = FAIL, 2 = INPUT_ERROR.
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
  token?: string;
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
    else if (arg === "--token") out.token = argv[++i];
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
  /** Сколько HTTP запросов harness'а получили статус >= 400 (auth issues / rate limits). */
  harnessHttpFailures: number;
  /** Реальная длительность run'а в минутах. */
  actualDurationMin: number;
}

export interface SmokeAcceptance {
  pass: boolean;
  /** Warning (не fail) если intentCount === 0 — может быть legit flat market. */
  warnings: string[];
  /** Конкретные причины fail (пусто если pass). */
  failures: string[];
}

/**
 * Acceptance критерии из docs/53-T3:
 *   1. finalRunState !== "FAILED" / "TIMED_OUT"  → fail если нарушено.
 *   2. errorEventCount === 0                      → fail если > 0.
 *   3. harnessHttpFailures === 0                  → fail если > 0
 *      (sustained 401/403/429 от Bybit или /api).
 *   4. failedIntentCount === 0                    → fail если > 0.
 *   5. intentCount > 0                            → warning если 0
 *      (рынок может быть flat — operator решает rerun или принять).
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
}

export interface RunResponse {
  id: string;
  state: string;
}

export interface SmokeApi {
  /** POST /presets/:slug/instantiate. */
  instantiatePreset(input: {
    slug: string;
    workspaceId: string;
    overrides?: { symbol?: string; quoteAmount?: number; name?: string };
  }): Promise<InstantiateResponse>;

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
}

// ---------------------------------------------------------------------------
// Core orchestration — signature suitable for unit testing
// ---------------------------------------------------------------------------

export interface RunDemoSmokeArgs {
  presetSlug: string;
  workspaceId: string;
  durationMin: number;
  pollIntervalSec: number;
  overrides: { symbol?: string; quoteAmount?: number };
  api: SmokeApi;
  /** Inject sleep so tests advance virtual time without real waits. */
  sleep: (ms: number) => Promise<void>;
  /** Inject clock so tests can fix `actualDurationMin`. */
  now: () => number;
  /** Optional sink for progress lines. */
  log?: (line: string) => void;
}

export interface SmokeReport {
  presetSlug: string;
  workspaceId: string;
  startedAt: string;
  finishedAt: string;
  botId: string;
  runId: string;
  metrics: SmokeMetrics;
  acceptance: SmokeAcceptance;
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

  log(`[demoSmoke] preset=${args.presetSlug} workspace=${args.workspaceId} duration=${args.durationMin}min`);

  const created = await args.api.instantiatePreset({
    slug: args.presetSlug,
    workspaceId: args.workspaceId,
    overrides: args.overrides,
  });
  log(`[demoSmoke] instantiated bot=${created.botId} strategy=${created.strategyId}`);

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

  // Final read-out — capture state after stop completed.
  lastIntents = await safeCall(() => args.api.countIntents(run.id), lastIntents);
  lastErrorEvents = await safeCall(() => args.api.countErrorEvents(run.id), lastErrorEvents);

  const finishedAt = args.now();
  const metrics: SmokeMetrics = {
    finalRunState: lastState,
    pollCount,
    intentCount: lastIntents.total,
    failedIntentCount: lastIntents.failed,
    errorEventCount: lastErrorEvents,
    harnessHttpFailures,
    actualDurationMin: (finishedAt - startedAt) / 60_000,
  };
  const acceptance = evaluateAcceptance(metrics);

  return {
    presetSlug: args.presetSlug,
    workspaceId: args.workspaceId,
    startedAt: new Date(startedAt).toISOString(),
    finishedAt: new Date(finishedAt).toISOString(),
    botId: created.botId,
    runId: run.id,
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
  prisma: PrismaClient;
}

export function buildDefaultApi(input: BuildApiInput): SmokeApi {
  const headers = {
    "content-type": "application/json",
    authorization: `Bearer ${input.token}`,
  };

  async function postJson<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${input.baseUrl}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`POST ${path} -> ${res.status} ${res.statusText}: ${text.slice(0, 200)}`);
    }
    return (await res.json()) as T;
  }

  return {
    async instantiatePreset({ slug, workspaceId, overrides }) {
      return postJson<InstantiateResponse>(
        `/presets/${encodeURIComponent(slug)}/instantiate`,
        { workspaceId, overrides },
      );
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
  token: string;
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
  const token = parsed.token ?? env.DEMO_SMOKE_TOKEN;
  const baseUrl = parsed.baseUrl ?? env.DEMO_SMOKE_BASE_URL ?? "http://localhost:3001/api/v1";

  if (!preset) return { kind: "error", reason: "--preset <slug> is required (or DEMO_SMOKE_PRESET)" };
  if (!workspace) return { kind: "error", reason: "--workspace <id> is required (or DEMO_SMOKE_WORKSPACE)" };
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
      token,
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
    console.log(JSON.stringify({ ...cfg, token: "<redacted>" }, null, 2));
    return 0;
  }

  const prisma = new PrismaClient();
  const api = buildDefaultApi({ baseUrl: cfg.baseUrl, token: cfg.token, prisma });

  try {
    const report = await runDemoSmoke({
      presetSlug: cfg.preset,
      workspaceId: cfg.workspace,
      durationMin: cfg.durationMin,
      pollIntervalSec: cfg.pollIntervalSec,
      overrides: { symbol: cfg.symbol, quoteAmount: cfg.quoteAmount },
      api,
      sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
      now: () => Date.now(),
    });

    await mkdir(cfg.outputDir, { recursive: true });
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const outPath = join(cfg.outputDir, `${ts}-${cfg.preset}.json`);
    await writeFile(outPath, JSON.stringify(report, null, 2), "utf-8");

    console.log("\n=== demoSmoke summary ===");
    console.log(`preset:        ${report.presetSlug}`);
    console.log(`run:           ${report.runId}`);
    console.log(`finalState:    ${report.metrics.finalRunState}`);
    console.log(`intents:       ${report.metrics.intentCount} (failed=${report.metrics.failedIntentCount})`);
    console.log(`errorEvents:   ${report.metrics.errorEventCount}`);
    console.log(`httpFailures:  ${report.metrics.harnessHttpFailures}`);
    console.log(`durationMin:   ${report.metrics.actualDurationMin.toFixed(2)}`);
    console.log(`acceptance:    ${report.acceptance.pass ? "PASS" : "FAIL"}`);
    if (report.acceptance.warnings.length) {
      console.log(`warnings:      ${report.acceptance.warnings.join("; ")}`);
    }
    if (report.acceptance.failures.length) {
      console.log(`failures:      ${report.acceptance.failures.join("; ")}`);
    }
    console.log(`report:        ${outPath}`);

    return report.acceptance.pass ? 0 : 1;
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
