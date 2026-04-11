import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock Prisma ───────────────────────────────────────────────────────────────

let mockUserPreference: Record<string, unknown> | null = null;
let lastStoredNotifyJson: Record<string, unknown> | null = null;
const mockWorkspaceMemberships: unknown[] = [];

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn(), JsonNull: "DbNull" },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    userPreference: {
      findUnique: vi.fn().mockImplementation(() => Promise.resolve(mockUserPreference)),
      upsert: vi.fn().mockImplementation(({ create, update }: { create: Record<string, unknown>; update: Record<string, unknown> }) => {
        const data = mockUserPreference
          ? { ...mockUserPreference, ...update }
          : { id: "pref-1", ...create };
        mockUserPreference = data;
        // Capture the notifyJson before response redaction mutates it
        lastStoredNotifyJson = structuredClone(data.notifyJson as Record<string, unknown>);
        return Promise.resolve(data);
      }),
    },
    workspaceMember: {
      findUnique: vi.fn().mockImplementation(() => {
        const m = mockWorkspaceMemberships[0] as Record<string, unknown> | undefined;
        if (!m) return Promise.resolve(null);
        return Promise.resolve({
          ...m,
          workspace: { id: m.workspaceId, name: "Test" },
        });
      }),
    },
    $queryRaw: vi.fn().mockResolvedValue([]),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  },
}));

// Mock crypto module for encryption/decryption
vi.mock("../../src/lib/crypto.js", () => ({
  getEncryptionKey: vi.fn().mockReturnValue(Buffer.alloc(32, 0xab)),
  getEncryptionKeyRaw: vi.fn().mockReturnValue(Buffer.alloc(32, 0xab)),
  encrypt: vi.fn().mockImplementation((plaintext: string) => `enc:${plaintext}`),
  decrypt: vi.fn().mockImplementation((payload: string) => {
    if (payload.startsWith("enc:")) return payload.slice(4);
    return payload;
  }),
}));

// Mock the notify module to avoid real Telegram calls
vi.mock("../../src/lib/notify.js", async () => {
  const actual = await vi.importActual("../../src/lib/notify.js");
  return {
    ...actual as object,
    sendTelegramMessage: vi.fn().mockResolvedValue(true),
  };
});

import { buildApp } from "../../src/app.js";
import type { FastifyInstance } from "fastify";

// ── Setup ────────────────────────────────────────────────────────────────────

let app: FastifyInstance;
let token: string;

beforeAll(async () => {
  app = await buildApp();
  token = app.jwt.sign({ sub: "test-user-id", email: "test@test.com" });
});

afterAll(async () => {
  await app.close();
});

beforeEach(() => {
  mockUserPreference = null;
  lastStoredNotifyJson = null;
  mockWorkspaceMemberships.length = 0;
});

// ── GET /user/notifications ──────────────────────────────────────────────────

describe("GET /api/v1/user/notifications", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/user/notifications",
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns null when no config exists", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/user/notifications",
      headers: { authorization: `Bearer ${token}` },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().notifyJson).toBeNull();
  });

  it("returns config with redacted token when exists (encrypted)", async () => {
    mockUserPreference = {
      id: "pref-1",
      userId: "test-user-id",
      notifyJson: {
        telegram: { botToken: "enc:123456:ABCDEFGHIJKLMNOP", chatId: "999", enabled: true, _tokenEncrypted: true },
      },
    };

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/user/notifications",
      headers: { authorization: `Bearer ${token}` },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.notifyJson.telegram.botToken).toBe("****MNOP");
    expect(body.notifyJson.telegram.chatId).toBe("999");
    expect(body.notifyJson.telegram.enabled).toBe(true);
    // _tokenEncrypted should not leak to client
    expect(body.notifyJson.telegram._tokenEncrypted).toBeUndefined();
  });

  it("returns config with redacted token for legacy plaintext storage", async () => {
    mockUserPreference = {
      id: "pref-1",
      userId: "test-user-id",
      notifyJson: {
        telegram: { botToken: "123456:ABCDEFGHIJKLMNOP", chatId: "999", enabled: true },
      },
    };

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/user/notifications",
      headers: { authorization: `Bearer ${token}` },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    // Legacy plaintext: redacts last 4 of the raw string
    expect(body.notifyJson.telegram.botToken).toBe("****MNOP");
  });
});

// ── PUT /user/notifications ──────────────────────────────────────────────────

describe("PUT /api/v1/user/notifications", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "PUT",
      url: "/api/v1/user/notifications",
      payload: { notifyJson: {} },
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns 400 when notifyJson is missing", async () => {
    const res = await app.inject({
      method: "PUT",
      url: "/api/v1/user/notifications",
      headers: { authorization: `Bearer ${token}` },
      payload: {},
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when telegram.botToken is not a string", async () => {
    const res = await app.inject({
      method: "PUT",
      url: "/api/v1/user/notifications",
      headers: { authorization: `Bearer ${token}` },
      payload: {
        notifyJson: { telegram: { botToken: 123, chatId: "456" } },
      },
    });
    expect(res.statusCode).toBe(400);
  });

  it("saves valid config with encrypted botToken", async () => {
    const res = await app.inject({
      method: "PUT",
      url: "/api/v1/user/notifications",
      headers: { authorization: `Bearer ${token}` },
      payload: {
        notifyJson: {
          telegram: { botToken: "123:ABCDEF", chatId: "999", enabled: true },
        },
      },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.notifyJson.telegram).toBeDefined();
    // The stored data should contain encrypted token (captured before response redaction)
    expect(lastStoredNotifyJson).toBeTruthy();
    const tg = (lastStoredNotifyJson as Record<string, unknown>).telegram as Record<string, unknown>;
    expect(tg.botToken).toBe("enc:123:ABCDEF");
    expect(tg._tokenEncrypted).toBe(true);
  });
});

// ── POST /user/notifications/test ────────────────────────────────────────────

describe("POST /api/v1/user/notifications/test", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/user/notifications/test",
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns 400 when no config exists", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/user/notifications/test",
      headers: { authorization: `Bearer ${token}` },
    });
    expect(res.statusCode).toBe(400);
  });

  it("sends test message when config exists", async () => {
    mockUserPreference = {
      id: "pref-1",
      userId: "test-user-id",
      notifyJson: {
        telegram: { botToken: "123:TOKEN", chatId: "999", enabled: true },
      },
    };

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/user/notifications/test",
      headers: { authorization: `Bearer ${token}` },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().success).toBe(true);
  });
});
