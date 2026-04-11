/**
 * PATCH /exchanges/:id — apiKey validation (Roadmap V3, Task #17)
 *
 * Verifies that PATCH rejects empty/null apiKey the same way POST does.
 */

import { describe, it, expect, vi } from "vitest";

// Mock Prisma before any import that touches it
vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  })),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

const mockFindUnique = vi.fn();
const mockUpdate = vi.fn();

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    exchangeConnection: {
      findUnique: (...args: unknown[]) => mockFindUnique(...args),
      findMany: vi.fn().mockResolvedValue([]),
      create: vi.fn(),
      update: (...args: unknown[]) => mockUpdate(...args),
      delete: vi.fn(),
    },
    $connect: vi.fn(),
    $disconnect: vi.fn(),
    $queryRaw: vi.fn().mockResolvedValue([{ "?column?": 1 }]),
  },
}));

vi.mock("../../src/lib/workspace.js", () => ({
  resolveWorkspace: vi.fn().mockResolvedValue({ id: "ws-1", name: "test" }),
}));

vi.mock("../../src/lib/crypto.js", () => ({
  getEncryptionKey: vi.fn().mockReturnValue(Buffer.alloc(32)),
  encrypt: vi.fn().mockReturnValue("iv:tag:cipher"),
  decrypt: vi.fn().mockReturnValue("decrypted"),
}));

import { buildApp } from "../../src/app.js";

async function getApp() {
  const app = await buildApp();
  // Generate a valid JWT for auth
  const token = app.jwt.sign({ sub: "user-1", workspaceId: "ws-1" });
  return { app, token };
}

describe("PATCH /exchanges/:id — apiKey validation", () => {
  const CONN_ID = "conn-123";
  const EXISTING_CONN = {
    id: CONN_ID,
    workspaceId: "ws-1",
    exchange: "BYBIT",
    name: "My Bybit",
    apiKey: "valid-key",
    encryptedSecret: "iv:tag:cipher",
    status: "CONNECTED",
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  it("rejects apiKey: '' (empty string)", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "" },
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(body.detail).toContain("apiKey must be a non-empty string");

    await app.close();
  });

  it("rejects apiKey: '   ' (whitespace only)", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "   " },
    });

    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("accepts valid apiKey string", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);
    mockUpdate.mockResolvedValue({ ...EXISTING_CONN, apiKey: "new-valid-key", status: "UNKNOWN" });

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "new-valid-key" },
    });

    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("allows PATCH with only name (no apiKey)", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);
    mockUpdate.mockResolvedValue({ ...EXISTING_CONN, name: "Renamed" });

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { name: "Renamed" },
    });

    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("rejects apiKey exceeding max length", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "a".repeat(257) },
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(body.detail).toContain("256");
    await app.close();
  });

  it("rejects apiKey with invalid characters", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "key with spaces!" },
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(body.detail).toContain("invalid characters");
    await app.close();
  });

  it("accepts apiKey with alphanumeric, dash, underscore", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);
    mockUpdate.mockResolvedValue({ ...EXISTING_CONN, apiKey: "My-Key_123", status: "UNKNOWN" });

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "My-Key_123" },
    });

    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("returns 401 without auth token", async () => {
    const { app } = await getApp();

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      payload: { apiKey: "test" },
    });

    expect(res.statusCode).toBe(401);
    await app.close();
  });
});
