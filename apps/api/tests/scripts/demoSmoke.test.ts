/**
 * demoSmoke harness — unit coverage (docs/53-T3).
 *
 * Покрывает:
 *  1. parseArgs — все флаги.
 *  2. validateCliArgs — required-проверки + диапазоны + env fallback.
 *  3. evaluateAcceptance — все pass / fail / warning ветви.
 *  4. isErrorEvent — type-heuristic + payload-heuristic.
 *  5. runDemoSmoke — end-to-end оркестрация на mocked SmokeApi:
 *       happy path, terminal-state early exit, http failures
 *       аккумулируются, stop-after-deadline.
 *
 * Без сети, без БД, без real time — sleep / now инжектируются.
 */

import { describe, it, expect, vi } from "vitest";
import {
  parseArgs,
  validateCliArgs,
  evaluateAcceptance,
  isErrorEvent,
  runDemoSmoke,
  type SmokeApi,
  type SmokeMetrics,
} from "../../scripts/demoSmoke.js";

// ---------------------------------------------------------------------------
// parseArgs
// ---------------------------------------------------------------------------

describe("demoSmoke.parseArgs", () => {
  it("parses each known flag", () => {
    const out = parseArgs([
      "--preset", "adaptive-regime",
      "--workspace", "ws-1",
      "--token", "jwt",
      "--base-url", "http://api.test/v1",
      "--duration-min", "45",
      "--poll-interval-sec", "30",
      "--symbol", "ETHUSDT",
      "--quote-amount", "75",
      "--output-dir", "/tmp/x",
      "--dry-run",
    ]);
    expect(out).toEqual({
      preset: "adaptive-regime",
      workspace: "ws-1",
      token: "jwt",
      baseUrl: "http://api.test/v1",
      durationMin: 45,
      pollIntervalSec: 30,
      symbol: "ETHUSDT",
      quoteAmount: 75,
      outputDir: "/tmp/x",
      dryRun: true,
    });
  });

  it("returns dryRun=false and missing fields when nothing passed", () => {
    expect(parseArgs([])).toEqual({ dryRun: false });
  });
});

// ---------------------------------------------------------------------------
// validateCliArgs
// ---------------------------------------------------------------------------

describe("demoSmoke.validateCliArgs", () => {
  const baseEnv = {} as Record<string, string | undefined>;

  it("requires preset", () => {
    const r = validateCliArgs({ workspace: "w", token: "t", dryRun: false }, baseEnv);
    expect(r.kind).toBe("error");
    if (r.kind === "error") expect(r.reason).toMatch(/preset/);
  });

  it("requires workspace", () => {
    const r = validateCliArgs({ preset: "p", token: "t", dryRun: false }, baseEnv);
    expect(r.kind).toBe("error");
    if (r.kind === "error") expect(r.reason).toMatch(/workspace/);
  });

  it("requires token", () => {
    const r = validateCliArgs({ preset: "p", workspace: "w", dryRun: false }, baseEnv);
    expect(r.kind).toBe("error");
    if (r.kind === "error") expect(r.reason).toMatch(/token/);
  });

  it("falls back to env vars", () => {
    const r = validateCliArgs(
      { dryRun: false },
      {
        DEMO_SMOKE_PRESET: "p",
        DEMO_SMOKE_WORKSPACE: "w",
        DEMO_SMOKE_TOKEN: "t",
        DEMO_SMOKE_BASE_URL: "http://example/v1",
      },
    );
    expect(r.kind).toBe("ok");
    if (r.kind === "ok") {
      expect(r.config.preset).toBe("p");
      expect(r.config.workspace).toBe("w");
      expect(r.config.token).toBe("t");
      expect(r.config.baseUrl).toBe("http://example/v1");
    }
  });

  it("rejects out-of-range durationMin", () => {
    const r = validateCliArgs(
      { preset: "p", workspace: "w", token: "t", durationMin: 9999, dryRun: false },
      baseEnv,
    );
    expect(r.kind).toBe("error");
  });

  it("rejects out-of-range pollIntervalSec", () => {
    const r = validateCliArgs(
      { preset: "p", workspace: "w", token: "t", pollIntervalSec: 0, dryRun: false },
      baseEnv,
    );
    expect(r.kind).toBe("error");
  });

  it("applies sensible defaults", () => {
    const r = validateCliArgs(
      { preset: "p", workspace: "w", token: "t", dryRun: false },
      baseEnv,
    );
    expect(r.kind).toBe("ok");
    if (r.kind === "ok") {
      expect(r.config.durationMin).toBe(30);
      expect(r.config.pollIntervalSec).toBe(60);
      expect(r.config.baseUrl).toBe("http://localhost:3001/api/v1");
    }
  });
});

// ---------------------------------------------------------------------------
// evaluateAcceptance
// ---------------------------------------------------------------------------

const baseMetrics = (): SmokeMetrics => ({
  finalRunState: "STOPPED",
  pollCount: 30,
  intentCount: 5,
  failedIntentCount: 0,
  errorEventCount: 0,
  harnessHttpFailures: 0,
  actualDurationMin: 30,
});

describe("demoSmoke.evaluateAcceptance", () => {
  it("passes on clean run", () => {
    const r = evaluateAcceptance(baseMetrics());
    expect(r.pass).toBe(true);
    expect(r.failures).toEqual([]);
    expect(r.warnings).toEqual([]);
  });

  it("warns (not fails) when intentCount=0", () => {
    const r = evaluateAcceptance({ ...baseMetrics(), intentCount: 0 });
    expect(r.pass).toBe(true);
    expect(r.warnings.length).toBeGreaterThan(0);
    expect(r.warnings[0]).toMatch(/intentCount=0/);
  });

  it("fails on FAILED finalRunState", () => {
    const r = evaluateAcceptance({ ...baseMetrics(), finalRunState: "FAILED" });
    expect(r.pass).toBe(false);
    expect(r.failures.join(",")).toMatch(/finalRunState=FAILED/);
  });

  it("fails on TIMED_OUT finalRunState", () => {
    const r = evaluateAcceptance({ ...baseMetrics(), finalRunState: "TIMED_OUT" });
    expect(r.pass).toBe(false);
  });

  it("fails on errorEventCount > 0", () => {
    const r = evaluateAcceptance({ ...baseMetrics(), errorEventCount: 3 });
    expect(r.pass).toBe(false);
    expect(r.failures.join(",")).toMatch(/errorEventCount=3/);
  });

  it("fails on harnessHttpFailures > 0", () => {
    const r = evaluateAcceptance({ ...baseMetrics(), harnessHttpFailures: 2 });
    expect(r.pass).toBe(false);
    expect(r.failures.join(",")).toMatch(/harnessHttpFailures=2/);
  });

  it("fails on failedIntentCount > 0", () => {
    const r = evaluateAcceptance({ ...baseMetrics(), failedIntentCount: 1 });
    expect(r.pass).toBe(false);
    expect(r.failures.join(",")).toMatch(/failedIntentCount=1/);
  });

  it("aggregates multiple failures", () => {
    const r = evaluateAcceptance({
      ...baseMetrics(),
      finalRunState: "FAILED",
      errorEventCount: 2,
      failedIntentCount: 1,
    });
    expect(r.pass).toBe(false);
    expect(r.failures).toHaveLength(3);
  });
});

// ---------------------------------------------------------------------------
// isErrorEvent heuristic
// ---------------------------------------------------------------------------

describe("demoSmoke.isErrorEvent", () => {
  it("matches type containing 'fail'", () => {
    expect(isErrorEvent("RUN_RECONCILED_FAILED", null)).toBe(true);
  });

  it("matches type containing 'error'", () => {
    expect(isErrorEvent("ORDER_PLACEMENT_ERROR", null)).toBe(true);
  });

  it("ignores benign types", () => {
    expect(isErrorEvent("signal_entry", null)).toBe(false);
    expect(isErrorEvent("RUN_QUEUED", null)).toBe(false);
  });

  it("matches when payload has truthy `error` key", () => {
    expect(isErrorEvent("intent_done", { error: "rate-limit" })).toBe(true);
  });

  it("ignores payload with null error", () => {
    expect(isErrorEvent("intent_done", { error: null })).toBe(false);
  });

  it("matches when payload has failed=true", () => {
    expect(isErrorEvent("intent_done", { failed: true })).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// runDemoSmoke orchestration with mocked SmokeApi
// ---------------------------------------------------------------------------

interface FakeRunState {
  state: string;
  errorCode: string | null;
}

function buildFakeApi(opts: {
  /** Sequence of run states returned by getRun on each poll. Last one is also final state. */
  runStates: string[];
  intentsByPoll?: { total: number; failed: number }[];
  errorEventsByPoll?: number[];
  /** If set, instantiatePreset throws once before succeeding. */
  failFirstInstantiate?: boolean;
  /** If true, getRun throws on every call. */
  throwOnGetRun?: boolean;
}): { api: SmokeApi; calls: { instantiate: number; start: number; stop: number; getRun: number; countIntents: number; countErrors: number } } {
  let pollIdx = 0;
  let instantiateCount = 0;
  let stopped = false;
  const calls = { instantiate: 0, start: 0, stop: 0, getRun: 0, countIntents: 0, countErrors: 0 };

  const api: SmokeApi = {
    async instantiatePreset() {
      calls.instantiate++;
      instantiateCount++;
      if (opts.failFirstInstantiate && instantiateCount === 1) {
        throw new Error("simulated instantiate failure");
      }
      return { botId: "bot-1", strategyId: "s-1", strategyVersionId: "sv-1" };
    },
    async startRun() {
      calls.start++;
      return { id: "run-1", state: opts.runStates[0] ?? "RUNNING" };
    },
    async stopRun() {
      calls.stop++;
      stopped = true;
      return { id: "run-1", state: "STOPPED" };
    },
    async getRun(): Promise<FakeRunState | null> {
      calls.getRun++;
      if (opts.throwOnGetRun) throw new Error("simulated getRun failure");
      // Once stopRun was called, subsequent reads observe STOPPED — same
      // semantics as Postgres after the route's transition() runs.
      if (stopped) return { state: "STOPPED", errorCode: null };
      const state = opts.runStates[pollIdx] ?? opts.runStates[opts.runStates.length - 1] ?? "RUNNING";
      pollIdx = Math.min(pollIdx + 1, opts.runStates.length - 1);
      return { state, errorCode: null };
    },
    async countIntents() {
      calls.countIntents++;
      const i = Math.min(calls.countIntents - 1, (opts.intentsByPoll?.length ?? 1) - 1);
      return opts.intentsByPoll?.[i] ?? { total: 0, failed: 0 };
    },
    async countErrorEvents() {
      calls.countErrors++;
      const i = Math.min(calls.countErrors - 1, (opts.errorEventsByPoll?.length ?? 1) - 1);
      return opts.errorEventsByPoll?.[i] ?? 0;
    },
  };
  return { api, calls };
}

describe("demoSmoke.runDemoSmoke", () => {
  it("happy path: instantiates → starts → polls → stops → PASS", async () => {
    const { api, calls } = buildFakeApi({
      runStates: ["RUNNING", "RUNNING", "RUNNING"],
      intentsByPoll: [
        { total: 0, failed: 0 },
        { total: 1, failed: 0 },
        { total: 3, failed: 0 },
        { total: 3, failed: 0 }, // post-stop final read
      ],
      errorEventsByPoll: [0, 0, 0, 0],
    });

    let now = 1_000_000;
    const sleep = vi.fn(async (ms: number) => { now += ms; });

    const report = await runDemoSmoke({
      presetSlug: "adaptive-regime",
      workspaceId: "ws-1",
      durationMin: 2,        // 2 минуты × 60s polls = 2 итерации
      pollIntervalSec: 60,
      overrides: { symbol: "BTCUSDT", quoteAmount: 50 },
      api,
      sleep,
      now: () => now,
      log: () => {},
    });

    expect(calls.instantiate).toBe(1);
    expect(calls.start).toBe(1);
    expect(calls.stop).toBe(1);
    expect(report.metrics.finalRunState).toBe("STOPPED");
    expect(report.metrics.intentCount).toBe(3);
    expect(report.metrics.failedIntentCount).toBe(0);
    expect(report.metrics.harnessHttpFailures).toBe(0);
    expect(report.acceptance.pass).toBe(true);
    expect(report.botId).toBe("bot-1");
    expect(report.runId).toBe("run-1");
  });

  it("early-exits on terminal FAILED state and skips stop call", async () => {
    const { api, calls } = buildFakeApi({
      runStates: ["RUNNING", "FAILED"],
      intentsByPoll: [{ total: 0, failed: 0 }, { total: 0, failed: 0 }, { total: 0, failed: 0 }],
      errorEventsByPoll: [0, 1, 1],
    });

    let now = 0;
    const sleep = async (ms: number) => { now += ms; };

    const report = await runDemoSmoke({
      presetSlug: "adaptive-regime",
      workspaceId: "ws-1",
      durationMin: 10,
      pollIntervalSec: 60,
      overrides: {},
      api,
      sleep,
      now: () => now,
      log: () => {},
    });

    expect(calls.stop).toBe(0); // already terminal — no stop call
    expect(report.metrics.finalRunState).toBe("FAILED");
    expect(report.acceptance.pass).toBe(false);
  });

  it("counts harness http failures without aborting", async () => {
    const { api } = buildFakeApi({
      runStates: ["RUNNING"],
      intentsByPoll: [{ total: 1, failed: 0 }],
      errorEventsByPoll: [0],
      throwOnGetRun: true,
    });

    let now = 0;
    const sleep = async (ms: number) => { now += ms; };

    const report = await runDemoSmoke({
      presetSlug: "adaptive-regime",
      workspaceId: "ws-1",
      durationMin: 1,
      pollIntervalSec: 60,
      overrides: {},
      api,
      sleep,
      now: () => now,
      log: () => {},
    });

    // getRun fails on every poll AND in the post-stop read-out → harnessHttpFailures > 0.
    expect(report.metrics.harnessHttpFailures).toBeGreaterThan(0);
    expect(report.acceptance.pass).toBe(false);
    expect(report.acceptance.failures.some((f) => f.includes("harnessHttpFailures"))).toBe(true);
  });

  it("warns when intentCount remains 0", async () => {
    const { api } = buildFakeApi({
      runStates: ["RUNNING"],
      intentsByPoll: [{ total: 0, failed: 0 }, { total: 0, failed: 0 }],
      errorEventsByPoll: [0, 0],
    });

    let now = 0;
    const sleep = async (ms: number) => { now += ms; };

    const report = await runDemoSmoke({
      presetSlug: "adaptive-regime",
      workspaceId: "ws-1",
      durationMin: 1,
      pollIntervalSec: 60,
      overrides: {},
      api,
      sleep,
      now: () => now,
      log: () => {},
    });

    expect(report.acceptance.pass).toBe(true);
    expect(report.acceptance.warnings.length).toBe(1);
    expect(report.acceptance.warnings[0]).toMatch(/intentCount=0/);
  });
});
