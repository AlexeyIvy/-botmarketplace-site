import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mock Prisma (required because notify.ts imports prisma.ts) ───────────────

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    workspaceMember: { findFirst: vi.fn().mockResolvedValue(null) },
    userPreference: { findUnique: vi.fn().mockResolvedValue(null) },
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  },
}));

import {
  sendTelegramMessage,
  notify,
  parseNotifyConfig,
  type TelegramConfig,
  type NotifyConfig,
  type NotifyPayload,
} from "../../src/lib/notify.js";

// ── Mock fetch ───────────────────────────────────────────────────────────────

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

// ── parseNotifyConfig ────────────────────────────────────────────────────────

describe("parseNotifyConfig", () => {
  it("returns null for null/undefined input", () => {
    expect(parseNotifyConfig(null)).toBeNull();
    expect(parseNotifyConfig(undefined)).toBeNull();
    expect(parseNotifyConfig("")).toBeNull();
  });

  it("returns null for object without telegram field", () => {
    expect(parseNotifyConfig({ foo: "bar" })).toBeNull();
  });

  it("returns null when telegram is missing botToken", () => {
    expect(parseNotifyConfig({ telegram: { chatId: "123" } })).toBeNull();
  });

  it("returns null when telegram is missing chatId", () => {
    expect(parseNotifyConfig({ telegram: { botToken: "abc" } })).toBeNull();
  });

  it("parses valid telegram config", () => {
    const result = parseNotifyConfig({
      telegram: { botToken: "123:ABC", chatId: "456", enabled: true },
    });
    expect(result).toEqual({
      telegram: { botToken: "123:ABC", chatId: "456", enabled: true },
    });
  });

  it("defaults enabled to true when omitted", () => {
    const result = parseNotifyConfig({
      telegram: { botToken: "123:ABC", chatId: "456" },
    });
    expect(result?.telegram?.enabled).toBe(true);
  });

  it("respects enabled: false", () => {
    const result = parseNotifyConfig({
      telegram: { botToken: "123:ABC", chatId: "456", enabled: false },
    });
    expect(result?.telegram?.enabled).toBe(false);
  });
});

// ── sendTelegramMessage ──────────────────────────────────────────────────────

describe("sendTelegramMessage", () => {
  const config: TelegramConfig = {
    botToken: "123:ABC",
    chatId: "456",
    enabled: true,
  };

  it("returns false when disabled", async () => {
    const result = await sendTelegramMessage({ ...config, enabled: false }, "test");
    expect(result).toBe(false);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("returns false when botToken is empty", async () => {
    const result = await sendTelegramMessage({ ...config, botToken: "" }, "test");
    expect(result).toBe(false);
  });

  it("calls Telegram API with correct parameters", async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ ok: true }) });

    const result = await sendTelegramMessage(config, "Hello test");
    expect(result).toBe(true);
    expect(mockFetch).toHaveBeenCalledOnce();

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe("https://api.telegram.org/bot123:ABC/sendMessage");
    expect(opts.method).toBe("POST");

    const body = JSON.parse(opts.body);
    expect(body.chat_id).toBe("456");
    expect(body.text).toBe("Hello test");
    expect(body.parse_mode).toBe("HTML");
  });

  it("returns false on HTTP error", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 400,
      text: () => Promise.resolve("Bad Request"),
    });

    const result = await sendTelegramMessage(config, "test");
    expect(result).toBe(false);
  });

  it("returns false on network error", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));

    const result = await sendTelegramMessage(config, "test");
    expect(result).toBe(false);
  });
});

// ── notify ───────────────────────────────────────────────────────────────────

describe("notify", () => {
  const payload: NotifyPayload = {
    eventType: "RUN_FAILED",
    runId: "run-123",
    symbol: "BTCUSDT",
    message: "Test failure message",
  };

  it("does nothing when config is null", async () => {
    await notify(null, payload);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("does nothing when telegram is disabled", async () => {
    const config: NotifyConfig = {
      telegram: { botToken: "abc", chatId: "123", enabled: false },
    };
    await notify(config, payload);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("sends formatted message when enabled", async () => {
    mockFetch.mockResolvedValue({ ok: true });

    const config: NotifyConfig = {
      telegram: { botToken: "test:TOKEN", chatId: "999", enabled: true },
    };
    await notify(config, payload);

    expect(mockFetch).toHaveBeenCalledOnce();
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.text).toContain("RUN_FAILED");
    expect(body.text).toContain("BTCUSDT");
    expect(body.text).toContain("Test failure message");
  });
});
