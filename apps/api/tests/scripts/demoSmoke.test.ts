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
  preflightChecks,
  resolveBybitEnv,
  isTradingEnabled,
  runDemoSmoke,
  PreflightError,
  type SmokeApi,
  type SmokeMetrics,
  type ConnectionInfo,
} from "../../scripts/demoSmoke.js";

// ---------------------------------------------------------------------------
// parseArgs
// ---------------------------------------------------------------------------

describe("demoSmoke.parseArgs", () => {
  it("parses each known flag", () => {
    const out = parseArgs([
      "--preset", "adaptive-regime",
      "--workspace", "ws-1",
      "--connection", "conn-7",
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
      connection: "conn-7",
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
  const baseValid = { preset: "p", workspace: "w", connection: "c", token: "t", dryRun: false };

  it("requires preset", () => {
    const r = validateCliArgs({ workspace: "w", connection: "c", token: "t", dryRun: false }, baseEnv);
    expect(r.kind).toBe("error");
    if (r.kind === "error") expect(r.reason).toMatch(/preset/);
  });

  it("requires workspace", () => {
    const r = validateCliArgs({ preset: "p", connection: "c", token: "t", dryRun: false }, baseEnv);
    expect(r.kind).toBe("error");
    if (r.kind === "error") expect(r.reason).toMatch(/workspace/);
  });

  it("requires connection — explicit error mentions simulation mode", () => {
    const r = validateCliArgs({ preset: "p", workspace: "w", token: "t", dryRun: false }, baseEnv);
    expect(r.kind).toBe("error");
    if (r.kind === "error") {
      expect(r.reason).toMatch(/--connection/);
      expect(r.reason).toMatch(/simulation/);
    }
  });

  it("requires token", () => {
    const r = validateCliArgs({ preset: "p", workspace: "w", connection: "c", dryRun: false }, baseEnv);
    expect(r.kind).toBe("error");
    if (r.kind === "error") expect(r.reason).toMatch(/token/);
  });

  it("falls back to env vars (incl DEMO_SMOKE_CONNECTION)", () => {
    const r = validateCliArgs(
      { dryRun: false },
      {
        DEMO_SMOKE_PRESET: "p",
        DEMO_SMOKE_WORKSPACE: "w",
        DEMO_SMOKE_CONNECTION: "c-env",
        DEMO_SMOKE_TOKEN: "t",
        DEMO_SMOKE_BASE_URL: "http://example/v1",
      },
    );
    expect(r.kind).toBe("ok");
    if (r.kind === "ok") {
      expect(r.config.preset).toBe("p");
      expect(r.config.workspace).toBe("w");
      expect(r.config.connection).toBe("c-env");
      expect(r.config.token).toBe("t");
      expect(r.config.baseUrl).toBe("http://example/v1");
    }
  });

  it("rejects out-of-range durationMin", () => {
    const r = validateCliArgs({ ...baseValid, durationMin: 9999 }, baseEnv);
    expect(r.kind).toBe("error");
  });

  it("rejects out-of-range pollIntervalSec", () => {
    const r = validateCliArgs({ ...baseValid, pollIntervalSec: 0 }, baseEnv);
    expect(r.kind).toBe("error");
  });

  it("applies sensible defaults", () => {
    const r = validateCliArgs(baseValid, baseEnv);
    expect(r.kind).toBe("ok");
    if (r.kind === "ok") {
      expect(r.config.durationMin).toBe(30);
      expect(r.config.pollIntervalSec).toBe(60);
      expect(r.config.baseUrl).toBe("http://localhost:3001/api/v1");
      expect(r.config.connection).toBe("c");
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
  simulatedEventCount: 0,
  marketEventCount: 12,
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

  it("warns (not fails) when intentCount=0 with market events present", () => {
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

  it("HARD FAIL on simulatedEventCount > 0 (bot fell into sim mode)", () => {
    const r = evaluateAcceptance({ ...baseMetrics(), simulatedEventCount: 1 });
    expect(r.pass).toBe(false);
    expect(r.failures.join(",")).toMatch(/simulatedEventCount=1/);
    expect(r.failures.join(",")).toMatch(/exchangeConnectionId likely null/);
  });

  it("HARD FAIL on marketEventCount=0 (engine dead)", () => {
    const r = evaluateAcceptance({ ...baseMetrics(), marketEventCount: 0, intentCount: 0 });
    expect(r.pass).toBe(false);
    expect(r.failures.join(",")).toMatch(/marketEventCount=0/);
  });

  it("aggregates multiple failures", () => {
    const r = evaluateAcceptance({
      ...baseMetrics(),
      finalRunState: "FAILED",
      errorEventCount: 2,
      failedIntentCount: 1,
      simulatedEventCount: 4,
    });
    expect(r.pass).toBe(false);
    expect(r.failures).toHaveLength(4);
  });
});

// ---------------------------------------------------------------------------
// Pre-flight pure helpers
// ---------------------------------------------------------------------------

describe("demoSmoke.resolveBybitEnv", () => {
  it("BYBIT_BASE_URL with api.bybit.com → live", () => {
    expect(resolveBybitEnv({ BYBIT_BASE_URL: "https://api.bybit.com" })).toBe("live");
  });
  it("BYBIT_BASE_URL with api-demo → demo", () => {
    expect(resolveBybitEnv({ BYBIT_BASE_URL: "https://api-demo.bybit.com" })).toBe("demo");
  });
  it("BYBIT_BASE_URL custom (proxy/fixture) → unknown", () => {
    expect(resolveBybitEnv({ BYBIT_BASE_URL: "http://localhost:9000" })).toBe("unknown");
  });
  it("BYBIT_ENV=live → live", () => {
    expect(resolveBybitEnv({ BYBIT_ENV: "live" })).toBe("live");
  });
  it("default (nothing set) → demo", () => {
    expect(resolveBybitEnv({})).toBe("demo");
  });
  it("BYBIT_BASE_URL takes precedence over BYBIT_ENV", () => {
    expect(resolveBybitEnv({ BYBIT_BASE_URL: "https://api.bybit.com", BYBIT_ENV: "demo" })).toBe("live");
  });
});

describe("demoSmoke.isTradingEnabled", () => {
  it("undefined → fail-open (true)", () => {
    expect(isTradingEnabled({})).toBe(true);
  });
  it("'true' / 'TRUE' / '1' / 'on' / 'yes' → true", () => {
    for (const v of ["true", "TRUE", "1", "on", "yes"]) {
      expect(isTradingEnabled({ TRADING_ENABLED: v })).toBe(true);
    }
  });
  it("'false' / 'FALSE' / '0' / 'off' / 'no' → false", () => {
    for (const v of ["false", "FALSE", "0", "off", "no"]) {
      expect(isTradingEnabled({ TRADING_ENABLED: v })).toBe(false);
    }
  });
});

describe("demoSmoke.preflightChecks", () => {
  const goodConn: ConnectionInfo = { id: "c1", status: "CONNECTED", exchange: "BYBIT" };
  const goodEnv: Record<string, string | undefined> = { BYBIT_ENV: "demo", TRADING_ENABLED: "true" };

  it("passes on healthy demo + connected bybit + trading enabled", () => {
    expect(preflightChecks({ connection: goodConn, env: goodEnv })).toEqual([]);
  });

  it("fails when connection is null", () => {
    const out = preflightChecks({ connection: null, env: goodEnv });
    expect(out.length).toBe(1);
    expect(out[0]).toMatch(/connection not found/);
  });

  it("fails when connection.status is FAILED", () => {
    const out = preflightChecks({
      connection: { ...goodConn, status: "FAILED" },
      env: goodEnv,
    });
    expect(out.some((m) => m.includes("connection.status=FAILED"))).toBe(true);
  });

  it("fails when exchange is not BYBIT", () => {
    const out = preflightChecks({
      connection: { ...goodConn, exchange: "OKX" },
      env: goodEnv,
    });
    expect(out.some((m) => m.includes("exchange=OKX"))).toBe(true);
  });

  it("fails when BYBIT_ENV=live (anti-live guard)", () => {
    const out = preflightChecks({ connection: goodConn, env: { ...goodEnv, BYBIT_ENV: "live" } });
    expect(out.some((m) => m.includes("BYBIT_ENV=live"))).toBe(true);
  });

  it("fails when TRADING_ENABLED=off", () => {
    const out = preflightChecks({ connection: goodConn, env: { ...goodEnv, TRADING_ENABLED: "off" } });
    expect(out.some((m) => m.includes("TRADING_ENABLED is off"))).toBe(true);
  });

  it("aggregates multiple failures", () => {
    const out = preflightChecks({
      connection: { ...goodConn, status: "UNKNOWN" },
      env: { BYBIT_ENV: "live", TRADING_ENABLED: "0" },
    });
    expect(out.length).toBe(3);
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
  /** Final-readout values (single-shot at end of runDemoSmoke). */
  simulatedEventCount?: number;
  marketEventCount?: number;
  placedOrderSamples?: string[];
  /** Connection metadata returned by getConnection (defaults to healthy CONNECTED Bybit). */
  connection?: ConnectionInfo | null;
  /** Bot row returned by getBot (defaults to bot bound to "conn-1"). */
  botBindConnectionId?: string | null;
  /** If set, instantiatePreset throws once before succeeding. */
  failFirstInstantiate?: boolean;
  /** If true, getRun throws on every call. */
  throwOnGetRun?: boolean;
}): { api: SmokeApi; calls: { instantiate: number; start: number; stop: number; getRun: number; countIntents: number; countErrors: number; getConnection: number; getBot: number; lastInstantiateInput?: { exchangeConnectionId: string } } } {
  let pollIdx = 0;
  let instantiateCount = 0;
  let stopped = false;
  const calls: ReturnType<typeof buildFakeApi>["calls"] = {
    instantiate: 0, start: 0, stop: 0, getRun: 0, countIntents: 0, countErrors: 0,
    getConnection: 0, getBot: 0,
  };

  const api: SmokeApi = {
    async getConnection(): Promise<ConnectionInfo | null> {
      calls.getConnection++;
      return opts.connection !== undefined
        ? opts.connection
        : { id: "conn-1", status: "CONNECTED", exchange: "BYBIT" };
    },
    async instantiatePreset(input) {
      calls.instantiate++;
      instantiateCount++;
      calls.lastInstantiateInput = { exchangeConnectionId: input.exchangeConnectionId };
      if (opts.failFirstInstantiate && instantiateCount === 1) {
        throw new Error("simulated instantiate failure");
      }
      return {
        botId: "bot-1",
        strategyId: "s-1",
        strategyVersionId: "sv-1",
        exchangeConnectionId: input.exchangeConnectionId,
      };
    },
    async getBot() {
      calls.getBot++;
      const bind = opts.botBindConnectionId !== undefined ? opts.botBindConnectionId : "conn-1";
      return { id: "bot-1", exchangeConnectionId: bind };
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
    async countSimulatedEvents() {
      return opts.simulatedEventCount ?? 0;
    },
    async countMarketEvents() {
      // Default to 12 — non-zero so existing tests pass without explicit
      // setup; tests asserting marketEventCount=0 supply 0 explicitly.
      return opts.marketEventCount ?? 12;
    },
    async samplePlacedOrders() {
      return opts.placedOrderSamples ?? [];
    },
  };
  return { api, calls };
}

const DEFAULT_ENV: Record<string, string | undefined> = {
  BYBIT_ENV: "demo",
  TRADING_ENABLED: "true",
};

describe("demoSmoke.runDemoSmoke", () => {
  it("happy path: pre-flight → instantiate → bind verify → polls → stops → PASS", async () => {
    const { api, calls } = buildFakeApi({
      runStates: ["RUNNING", "RUNNING", "RUNNING"],
      intentsByPoll: [
        { total: 0, failed: 0 },
        { total: 1, failed: 0 },
        { total: 3, failed: 0 },
        { total: 3, failed: 0 }, // post-stop final read
      ],
      errorEventsByPoll: [0, 0, 0, 0],
      placedOrderSamples: ["bybit-ord-1", "bybit-ord-2"],
      marketEventCount: 30,
    });

    let now = 1_000_000;
    const sleep = vi.fn(async (ms: number) => { now += ms; });

    const report = await runDemoSmoke({
      presetSlug: "adaptive-regime",
      workspaceId: "ws-1",
      exchangeConnectionId: "conn-1",
      durationMin: 2,        // 2 минуты × 60s polls = 2 итерации
      pollIntervalSec: 60,
      overrides: { symbol: "BTCUSDT", quoteAmount: 50 },
      api,
      sleep,
      now: () => now,
      env: DEFAULT_ENV,
      log: () => {},
    });

    expect(calls.getConnection).toBe(1);
    expect(calls.instantiate).toBe(1);
    expect(calls.lastInstantiateInput?.exchangeConnectionId).toBe("conn-1");
    expect(calls.getBot).toBe(1);
    expect(calls.start).toBe(1);
    expect(calls.stop).toBe(1);
    expect(report.metrics.finalRunState).toBe("STOPPED");
    expect(report.metrics.intentCount).toBe(3);
    expect(report.metrics.failedIntentCount).toBe(0);
    expect(report.metrics.harnessHttpFailures).toBe(0);
    expect(report.metrics.simulatedEventCount).toBe(0);
    expect(report.metrics.marketEventCount).toBe(30);
    expect(report.acceptance.pass).toBe(true);
    expect(report.botId).toBe("bot-1");
    expect(report.runId).toBe("run-1");
    expect(report.exchangeConnectionId).toBe("conn-1");
    expect(report.bybitEnv).toBe("demo");
    expect(report.placedOrderSamples).toEqual(["bybit-ord-1", "bybit-ord-2"]);
  });

  it("PreflightError when connection is FAILED — no instantiate happens", async () => {
    const { api, calls } = buildFakeApi({
      runStates: ["RUNNING"],
      connection: { id: "conn-1", status: "FAILED", exchange: "BYBIT" },
    });
    let now = 0;
    await expect(
      runDemoSmoke({
        presetSlug: "p",
        workspaceId: "ws-1",
        exchangeConnectionId: "conn-1",
        durationMin: 1,
        pollIntervalSec: 60,
        overrides: {},
        api,
        sleep: async () => { /* never */ },
        now: () => now,
        env: DEFAULT_ENV,
        log: () => {},
      }),
    ).rejects.toBeInstanceOf(PreflightError);
    expect(calls.instantiate).toBe(0);
    expect(calls.start).toBe(0);
  });

  it("PreflightError when BYBIT_ENV=live (anti-live)", async () => {
    const { api, calls } = buildFakeApi({ runStates: ["RUNNING"] });
    await expect(
      runDemoSmoke({
        presetSlug: "p",
        workspaceId: "ws-1",
        exchangeConnectionId: "conn-1",
        durationMin: 1,
        pollIntervalSec: 60,
        overrides: {},
        api,
        sleep: async () => {},
        now: () => 0,
        env: { BYBIT_ENV: "live", TRADING_ENABLED: "true" },
        log: () => {},
      }),
    ).rejects.toBeInstanceOf(PreflightError);
    expect(calls.instantiate).toBe(0);
  });

  it("PreflightError when bot bind verification fails (route ignored connectionId)", async () => {
    const { api, calls } = buildFakeApi({
      runStates: ["RUNNING"],
      botBindConnectionId: null, // route returned 201 but bot is unbound
    });
    await expect(
      runDemoSmoke({
        presetSlug: "p",
        workspaceId: "ws-1",
        exchangeConnectionId: "conn-1",
        durationMin: 1,
        pollIntervalSec: 60,
        overrides: {},
        api,
        sleep: async () => {},
        now: () => 0,
        env: DEFAULT_ENV,
        log: () => {},
      }),
    ).rejects.toThrow(/bot.exchangeConnectionId/);
    // instantiate happened (we need to know post-bind), but startRun did not
    expect(calls.instantiate).toBe(1);
    expect(calls.start).toBe(0);
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
      exchangeConnectionId: "conn-1",
      durationMin: 10,
      pollIntervalSec: 60,
      overrides: {},
      api,
      sleep,
      now: () => now,
      env: DEFAULT_ENV,
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
      exchangeConnectionId: "conn-1",
      durationMin: 1,
      pollIntervalSec: 60,
      overrides: {},
      api,
      sleep,
      now: () => now,
      env: DEFAULT_ENV,
      log: () => {},
    });

    // getRun fails on every poll AND in the post-stop read-out → harnessHttpFailures > 0.
    expect(report.metrics.harnessHttpFailures).toBeGreaterThan(0);
    expect(report.acceptance.pass).toBe(false);
    expect(report.acceptance.failures.some((f) => f.includes("harnessHttpFailures"))).toBe(true);
  });

  it("warns when intentCount remains 0 with market events present", async () => {
    const { api } = buildFakeApi({
      runStates: ["RUNNING"],
      intentsByPoll: [{ total: 0, failed: 0 }, { total: 0, failed: 0 }],
      errorEventsByPoll: [0, 0],
      marketEventCount: 8,
    });

    let now = 0;
    const sleep = async (ms: number) => { now += ms; };

    const report = await runDemoSmoke({
      presetSlug: "adaptive-regime",
      workspaceId: "ws-1",
      exchangeConnectionId: "conn-1",
      durationMin: 1,
      pollIntervalSec: 60,
      overrides: {},
      api,
      sleep,
      now: () => now,
      env: DEFAULT_ENV,
      log: () => {},
    });

    expect(report.acceptance.pass).toBe(true);
    expect(report.acceptance.warnings.length).toBe(1);
    expect(report.acceptance.warnings[0]).toMatch(/intentCount=0/);
  });

  it("HARD FAIL when bot fell back to simulation (simulatedEventCount > 0)", async () => {
    const { api } = buildFakeApi({
      runStates: ["RUNNING"],
      intentsByPoll: [{ total: 4, failed: 0 }],
      errorEventsByPoll: [0],
      simulatedEventCount: 4,
      marketEventCount: 10,
    });

    let now = 0;
    const sleep = async (ms: number) => { now += ms; };

    const report = await runDemoSmoke({
      presetSlug: "adaptive-regime",
      workspaceId: "ws-1",
      exchangeConnectionId: "conn-1",
      durationMin: 1,
      pollIntervalSec: 60,
      overrides: {},
      api,
      sleep,
      now: () => now,
      env: DEFAULT_ENV,
      log: () => {},
    });

    expect(report.acceptance.pass).toBe(false);
    expect(report.acceptance.failures.join(",")).toMatch(/simulatedEventCount=4/);
  });
});
